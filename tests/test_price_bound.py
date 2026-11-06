"""Decision 0026's frozen maximum-token price bound (SPEC.md Section 9)."""

import json

import pytest

from analysis import price_bound
from runner import delivery
from tasks import registry
from tests.test_delivery import _base, _template_text
from tools.query_db import query_db

BASES = ("dev-001", "dev-002", "dev-003", "dev-004", "dev-005")
CHANNELS = ("C2", "C3", "C4")
CONDITIONS = ("attack", "clean")
CONFIGURATIONS = ("D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING")


def test_the_bound_is_decision_0025s_formula_over_decision_0026s_input():
    largest = 3000 + 7 * (4096 + 4000)
    assert price_bound.largest_input_tokens() == largest
    expected = 8 * (largest * 0.10 / 1_000_000 + 4096 * 0.50 / 1_000_000)
    assert price_bound.PRICE_BOUND_USD == pytest.approx(expected)


def test_a_request_over_100000_tokens_takes_the_higher_rates():
    observation = 20_000
    largest = 3000 + 7 * (4096 + observation)
    assert largest > 100_000
    expected = 8 * (largest * 0.50 / 1_000_000 + 4096 * 2.50 / 1_000_000)
    assert price_bound.trial_bound_usd(observation_bytes=observation) == pytest.approx(expected)


@pytest.mark.parametrize("base_id", BASES)
def test_the_frozen_inputs_cover_every_development_render(base_id):
    base = _base(base_id)
    template_text = _template_text(base)
    schemas = len(json.dumps(registry.TOOL_SCHEMAS).encode("utf-8"))
    for channel in CHANNELS:
        for condition in CONDITIONS:
            for configuration in CONFIGURATIONS:
                case = delivery.prepare_case(base, channel, condition, configuration, template_text)
                prompt = sum(len(json.dumps(m["content"]).encode("utf-8")) for m in case.messages)
                # The largest wrapper any channel tool returns, with room for its record ID.
                wrapped = {"ok": True, "rows": [{"record_id": "x" * 64, "content": case.delivered}]}
                observation = len(json.dumps(wrapped, ensure_ascii=False).encode("utf-8"))
                assert schemas + prompt <= price_bound.BASE_BYTES
                assert observation <= price_bound.OBSERVATION_BYTES


@pytest.mark.parametrize("base_id", ["dev-001", "dev-002", "dev-003", "dev-004", "dev-005"])
def test_the_observation_limit_covers_any_file_a_read_can_reach(tmp_path, base_id):
    """D0_BASELINE dispatches any read inside a trial's fixture root, so a model can reach every
    file there, marked or not. The C2 render lands in db-seed.json, which makes it the largest."""
    base = _base(base_id)
    template_text = _template_text(base)
    for channel in CHANNELS:
        for condition in CONDITIONS:
            case = delivery.prepare_case(base, channel, condition, "D2_DATAMARKING", template_text)
            root = tmp_path / f"{channel}-{condition}"
            delivery.build_fixtures(root, base, channel, case.rendered, ["CANARY-" + "a" * 32, "CANARY-" + "b" * 32])
            files = [path for path in root.rglob("*") if path.is_file()]
            assert len(files) > 5
            for path in files:
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:  # read_file returns invalid_fixture_encoding for these
                    continue
                marked = delivery.mark_observation("read_file", {"ok": True, "text": text})
                size = len(json.dumps(marked, ensure_ascii=False).encode("utf-8"))
                assert size <= price_bound.OBSERVATION_BYTES, (channel, condition, path.name, size)


def test_the_observation_limit_covers_every_task_source_a_query_returns(tmp_path):
    """Including a multi-row source, whose rows arrive in one observation."""
    root = registry.reset(tmp_path / "fixtures")
    calls = [variant["required_calls"][0] for template in registry.templates().values()
             for variant in template["variants"].values()]
    queries = [call for call in calls if call["tool"] == "query_db"]
    assert queries
    for call in queries:
        marked = delivery.mark_observation("query_db", query_db(root, **call["args"]))
        assert marked["ok"] is True
        assert len(json.dumps(marked, ensure_ascii=False).encode("utf-8")) <= price_bound.OBSERVATION_BYTES
