"""Stack-gaps item 4: JSON Schema contracts enforced where records are used.

A base case is refused at run time, not only in tests/test_corpus_records.py. The
schedule spec, ``protocol/active.json``, and the release manifest have unlocked
schemas built from SPEC.md's field lists.
"""

import copy
import json
import shutil
from pathlib import Path

import pytest
from jsonschema import ValidationError

from runner import execute, grid_dev
from runner.mock_slice import validator
from runner.schedule import generate_schedule

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpus" / "development"


def _corpus_without(tmp_path, field):
    corpus = shutil.copytree(CORPUS, tmp_path / "corpus")
    base = json.loads((corpus / "dev-001.json").read_text(encoding="utf-8"))
    del base[field]
    (corpus / "dev-001.json").write_text(json.dumps(base), encoding="utf-8")
    return corpus


def test_a_base_case_without_its_source_is_refused_before_any_trial(tmp_path):
    corpus = _corpus_without(tmp_path, "source")
    spec = {**execute.default_dev_spec("schema-refusal"), "base_case_ids": ["dev-001"]}
    with pytest.raises(ValidationError, match="source"):
        execute.run_schedule(tmp_path / "run", generate_schedule(spec), corpus_root=corpus, spec=spec, delivery=True)
    assert not list((tmp_path / "run").glob("*/events.jsonl"))


def test_load_base_refuses_a_record_the_schema_refuses(tmp_path):
    with pytest.raises(ValidationError):
        execute._load_base({}, _corpus_without(tmp_path, "notes"), "dev-001")


def test_every_development_base_still_loads():
    for path in sorted(CORPUS.glob("dev-*.json")):
        execute._load_base({}, CORPUS, path.stem)


# The schedule spec ----------------------------------------------------------


@pytest.mark.parametrize("name", ["development_grid_spec.json", "development_grid_spec_fallback.json"])
def test_the_committed_grid_specs_validate(name):
    validator("schedule_spec").validate(json.loads((ROOT / "protocol" / name).read_text(encoding="utf-8")))


def test_the_default_dev_spec_validates():
    validator("schedule_spec").validate(execute.default_dev_spec("x"))


@pytest.mark.parametrize("mutate", [
    lambda s: s.pop("seed"),
    lambda s: s.update(repeats=0),
    lambda s: s.update(channels=["C9"]),
    lambda s: s.update(configurations=["D0"]),
    lambda s: s.update(conditions=["attack", "attack"]),
    lambda s: s.update(base_case_ids=[]),
    lambda s: s.update(unexpected=True),
])
def test_the_schedule_schema_refuses_a_bad_spec(mutate):
    spec = grid_dev.load_spec()
    mutate(spec)
    with pytest.raises(ValidationError):
        validator("schedule_spec").validate(spec)


def test_validate_refuses_a_spec_the_schema_refuses(tmp_path, capsys):
    bad = {**grid_dev.load_spec(), "repeats": "1"}
    (tmp_path / "spec.json").write_text(json.dumps(bad), encoding="utf-8")
    assert grid_dev.main(["validate", "--spec", str(tmp_path / "spec.json")]) != 0


# active_protocol and manifest: SPEC.md Section 8's field lists ----------------


def _active():
    return json.loads((ROOT / "tests" / "fixtures" / "schemas" / "active_protocol.example.json").read_text(encoding="utf-8"))


def _manifest():
    return json.loads((ROOT / "tests" / "fixtures" / "schemas" / "manifest.example.json").read_text(encoding="utf-8"))


def test_the_example_active_protocol_and_manifest_validate():
    validator("active_protocol").validate(_active())
    validator("manifest").validate(_manifest())


@pytest.mark.parametrize("name", ["active_protocol", "manifest"])
def test_every_field_spec_lists_is_required(name):
    record = _active() if name == "active_protocol" else _manifest()
    for field in validator(name).schema["required"]:
        broken = copy.deepcopy(record)
        del broken[field]
        with pytest.raises(ValidationError):
            validator(name).validate(broken)


def test_an_active_protocol_names_one_of_the_tiers():
    with pytest.raises(ValidationError):
        validator("active_protocol").validate({**_active(), "tier": "F99"})


@pytest.mark.parametrize("name", ["schedule_spec", "active_protocol", "manifest"])
def test_the_new_schemas_are_unlocked_and_indexed(name):
    """0.x, so W8-T3, W9-T3, and W11-T3 may still revise them; not among the locked contract schemas."""
    from tests.test_contract_lock import CONTRACT_SCHEMAS, LOCKED

    schema = validator(name).schema
    assert schema["$id"] == f"urn:CANARY:schema:{name}:0.1.0" and name not in CONTRACT_SCHEMAS
    assert not schema["$id"].endswith(LOCKED)
    assert f"`{name}.schema.json`" in (ROOT / "docs" / "DATA_CONTRACTS.md").read_text(encoding="utf-8")


def test_the_sweep_refuses_a_spec_the_schema_refuses(monkeypatch):
    from runner import sweep

    monkeypatch.setenv("CANARY_PAID_RUN_ACK", "1")
    monkeypatch.delenv("CI", raising=False)
    for name in list(__import__("os").environ):
        if name.startswith(("ANTHROPIC_", "OPENAI_")):
            monkeypatch.delenv(name, raising=False)
    spec = {**grid_dev.load_spec(), "protocol_sentinel": "frozen-x", "repeats": 0}
    reason = sweep.live_refusal(spec, "v1", ROOT / "nowhere", ROOT / "nowhere-out")
    assert reason is not None and "schedule spec" in reason


def test_a_generated_task_coverage_record_loads_and_nothing_else_skips_the_schema(tmp_path):
    """runner.coverage's generated coverage-* records aren't corpus base cases (no candidate or
    source); only they skip base_case.schema.json, and a marked dev base is still refused."""
    from runner import coverage

    record, _template = coverage.expected_case(sorted(coverage.CANONICAL)[0])
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / f"{record['base_case_id']}.json").write_text(json.dumps(record), encoding="utf-8")
    execute._load_base({}, corpus, record["base_case_id"])
    base = json.loads((CORPUS / "dev-001.json").read_text(encoding="utf-8"))
    del base["source"]
    (corpus / "dev-001.json").write_text(json.dumps({**base, "fixture_mode": "native-task-coverage-v1"}), encoding="utf-8")
    with pytest.raises(ValidationError):
        execute._load_base({}, corpus, "dev-001")
