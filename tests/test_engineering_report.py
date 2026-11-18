"""W8-T3: tests for the dormant ENGINEERING fallback plan and report generator."""

from __future__ import annotations

import json

import pytest
from jsonschema import Draft202012Validator

from analysis.engineering_report import DEFAULT_OUTPUT, DEFAULT_PLAN, load_plan, render

ROOT = DEFAULT_PLAN.resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"


def test_plan_loads_and_declares_no_official_experiment():
    plan = load_plan()
    assert plan["official_empirical_experiment"] is False
    assert plan["checks"], "plan must list checks"


def test_dormant_report_claims_no_estimate():
    text = render(load_plan())
    assert "DORMANT" in text
    assert "no empirical estimate" in text.lower() or "no official model" in text.lower()
    # a dormant report shows the status marker, not pass/fail outcomes
    assert "DORMANT — NO ENGINEERING RUN" in text


def test_active_report_summarizes_counts_without_an_estimate():
    plan = load_plan()
    records = [
        {"check_id": plan["checks"][0]["check_id"], "passed": True},
        {"check_id": plan["checks"][1]["check_id"], "passed": False},
        {"check_id": plan["checks"][2]["check_id"], "passed": None},
    ]
    text = render(plan, records)
    assert "PASS" in text and "FAIL" in text and "INDETERMINATE" in text
    assert "Passed: 1" in text and "Failed: 1" in text
    assert "Indeterminate" in text
    # never an empirical estimate or defense-efficacy claim
    assert "efficacy" not in text.lower() or "no " in text.lower()


def test_generated_shell_is_current():
    """The committed shell must match the generator output (CI guard)."""
    expected = render(load_plan())
    assert DEFAULT_OUTPUT.exists(), "engineering report shell must be committed"
    assert DEFAULT_OUTPUT.read_text(encoding="utf-8") == expected


def test_engineering_validation_schema_is_well_formed_and_rejects_empirical_ids():
    schema = json.loads((SCHEMA_DIR / "engineering_validation.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    record = {
        "schema_version": "0.1.0",
        "validation_id": "v",
        "validation_record_id": "v:check-1",
        "check_id": "check-1",
        "check_category": "containment",
        "check_name": "safe tools fail closed",
        "input": "mock",
        "expected_result": True,
        "actual_result": True,
        "passed": True,
        "hashes": {
            "code_commit": None, "container_digest": None, "validation_plan": None,
            "fixture": None, "schema": None, "oracle_scorer": None, "prompt": None,
            "defense_prototype": None, "report_generator": None,
        },
        "started_at": "2026-11-01T00:00:00Z",
        "ended_at": "2026-11-01T00:00:01Z",
        "evidence_refs": ["events/sha256/x"],
        "reason_codes": [],
        "official_empirical_record": False,
    }
    validator.validate(record)  # valid

    # passed may be null (incomplete evidence), never coerced to false
    record_null = dict(record, passed=None, reason_codes=["evidence_incomplete"])
    validator.validate(record_null)

    # an empirical identifier must be rejected
    with pytest.raises(Exception):
        validator.validate(dict(record, experiment_id="final-2026"))
