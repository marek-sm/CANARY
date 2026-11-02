"""Decision 0026's frozen maximum-token price bound (SPEC.md Section 9)."""

import json

import pytest

from analysis import price_bound
from runner import delivery
from tasks import registry
from tests.test_delivery import _base, _template_text

BASES = ("dev-001", "dev-002", "dev-003", "dev-004", "dev-005")
CHANNELS = ("C2", "C3", "C4")
CONDITIONS = ("attack", "clean")
CONFIGURATIONS = ("D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING")


def test_the_bound_is_decision_0025s_formula_over_decision_0026s_input():
    largest = 3000 + 7 * (4096 + 3000)
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
