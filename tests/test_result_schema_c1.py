"""Decision 0034 (DEV-0005): official C1 direct-injection control records.

Every empirical Section 12 row runs C1 controls under D0_BASELINE, so the result
schema needs a lawful C1 record form: split ``c1_control``, channel ``C1``, the
attack condition, D0_BASELINE, its own superblock, role ``c1_control``, and a
``c1-`` base. A 1.0.0 record keeps exactly the 1.0.0 shape, so preserved
development records still validate and no new record can claim the old version.
"""
import copy
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from runner import mock_slice, spend_ledger
from runner.mock_slice import validator

FIXTURES = Path(__file__).parent / "fixtures" / "result"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def c1_record():
    return load("valid_c1_control.json")


def test_a_c1_control_record_validates():
    record = c1_record()
    assert (record["split"], record["channel"], record["schema_version"]) == ("c1_control", "C1", "1.1.0")
    validator("result").validate(record)


@pytest.mark.parametrize("field, value", [
    ("channel", "C2"),
    ("channel", None),
    ("condition", "clean"),
    ("condition", None),
    ("configuration", "D1_POLICY_GATE"),
    ("configuration", "D2_DATAMARKING"),
    ("comparison_superblock_id", None),
    ("comparison_superblock_id", ""),
    ("protocol_version", None),
    ("protocol_version", ""),
    ("analysis_role", "primary_indirect"),
    ("analysis_role", None),
    ("base_case_id", "dev-001"),
    ("base_case_id", "eval-014"),
    ("schema_version", "1.0.0"),
])
def test_a_c1_control_record_with_any_other_value_is_rejected(field, value):
    record = c1_record()
    record[field] = value
    with pytest.raises(ValidationError):
        validator("result").validate(record)


def test_channel_c1_is_never_an_evaluation_record():
    record = c1_record()
    record["split"] = "evaluation"
    record["analysis_role"] = "primary_indirect"
    with pytest.raises(ValidationError):
        validator("result").validate(record)


@pytest.mark.parametrize("change", [{"channel": "C1"}, {"split": "c1_control"}])
def test_a_1_0_0_record_keeps_the_1_0_0_shape(change):
    record = load("valid_development.json")
    record["schema_version"] = "1.0.0"
    record.update(change)
    with pytest.raises(ValidationError):
        validator("result").validate(record)


def test_a_preserved_1_0_0_record_still_validates():
    for name in ("valid_development.json", "valid_evaluation.json"):
        record = load(name)
        record["schema_version"] = "1.0.0"
        validator("result").validate(record)


def test_a_development_record_may_carry_channel_c1_for_a_pilot():
    # decision 0033: a C1-cost pilot uses development material only
    record = load("valid_development.json")
    record["channel"] = "C1"
    validator("result").validate(record)


def test_unknown_versions_are_rejected():
    record = c1_record()
    for version in ("1.2.0", "2.0.0"):
        record["schema_version"] = version
        with pytest.raises(ValidationError):
            validator("result").validate(record)


def test_the_runner_writes_the_current_result_version(tmp_path):
    assert mock_slice.RESULT_SCHEMA_VERSION == "1.1.0"
    out = mock_slice.run_mock_trial(tmp_path / "run", clock=lambda: "2026-11-12T00:00:00Z")
    [record] = mock_slice.read_jsonl(out / mock_slice.RESULTS_FILE, "result")
    assert record["schema_version"] == "1.1.0"
    schema = json.loads((Path(mock_slice.__file__).resolve().parents[1] / "schemas" / "result.schema.json").read_text())
    assert schema["$id"] == f"urn:CANARY:schema:result:{mock_slice.RESULT_SCHEMA_VERSION}"
    assert mock_slice.RESULT_SCHEMA_VERSION in schema["properties"]["schema_version"]["enum"]


class _Paid:
    adapter_version = "fake-paid-adapter-v0"


def test_the_ledger_writes_the_current_version():
    # conftest points the ledger at a temporary home; the real one is never reached
    spend_ledger.init()
    spend_ledger.start(_Paid(), "trial")
    lines = [json.loads(line) for line in spend_ledger.ledger_path().read_text(encoding="utf-8").splitlines()]
    assert [line["schema_version"] for line in lines] == ["1.1.0", "1.1.0"]


def test_a_c1_spend_ledger_start_validates_and_counts_in_dollars_only():
    line = {
        "schema_version": spend_ledger.LEDGER_SCHEMA_VERSION, "phase": "started", "recorded_at": "2026-11-20T00:00:00Z",
        "invocation_id": "x", "logical_trial_id": c1_record()["logical_trial_id"], "provider_adapter": "a",
        "split": "c1_control", "analysis_role": "c1_control", "new_trial": True, "bound_usd": 0.01, "cap_usd": 10.0,
    }
    validator("spend_ledger").validate(line)
    assert spend_ledger.counts_against_ceiling("c1_control", "c1_control") is False
    old = copy.deepcopy(line)
    old["schema_version"] = "1.0.0"
    with pytest.raises(ValidationError):
        validator("spend_ledger").validate(old)
    old["split"] = "development"
    validator("spend_ledger").validate(old)
