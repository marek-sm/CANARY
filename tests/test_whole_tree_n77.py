"""The whole-tree review's blocking findings on #77 (the November 13 whole-tree review record):
N-77-4 (active.json lists against the Section 12 row), N-77-5 (ENGINEERING totals over the
plan's checks), N-77-6 (one C1 record per logical trial, one experiment)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from analysis import active_protocol, c1_table
from analysis.engineering_report import load_plan, render

ROOT = Path(__file__).resolve().parents[1]
COMMON = dict(protocol_id="p", protocol_version="1.24.0", active_contributor_count=6,
              selection_reason_category="headcount-ceiling", accountable_roles=["lead"], data_cutoff="2026-11-22")
BASES = [f"eval-{i:03d}" for i in range(1, 21)]


# --- N-77-4 ------------------------------------------------------------------------


def test_a_generated_f20_manifest_with_the_frozen_lists_validates():
    manifest = active_protocol.generate("F20", base_case_ids=BASES, **COMMON)
    active_protocol.validate(manifest)


@pytest.mark.parametrize("kwargs, reason", [
    ({"base_case_ids": BASES[:19]}, "base_case_ids"),
    ({"base_case_ids": BASES[:19] + [BASES[0]]}, "base_case_ids"),
    ({"base_case_ids": BASES, "run_indices": [1, 2]}, "run_indices"),
    ({"base_case_ids": BASES, "run_indices": [1, 2, 4]}, "run_indices"),
    ({"base_case_ids": BASES, "c1_control_ids": ["c1-003", "c1-002", "c1-001", "c1-004"]}, "c1_controls"),
])
def test_generate_refuses_lists_the_section_12_row_does_not_give(kwargs, reason):
    with pytest.raises(active_protocol.ArithmeticError_, match=reason):
        active_protocol.generate("F20", **{**COMMON, **kwargs})


@pytest.mark.parametrize("field, value, reason", [
    ("base_case_count", 7, "base_case_count"),
    ("channels", ["C2"], "channels"),
    ("channels", ["C3", "C2", "C4"], "channels"),
    ("configurations", ["D0_BASELINE", "D1_POLICY_GATE"], "configurations"),
    ("stage_configurations", ["D0_BASELINE"], "stage_configurations"),
    ("run_indices", [1, 2], "run_indices"),
    ("c1_controls", ["c1-002", "c1-003", "c1-001"], "c1_controls"),
])
def test_validate_refuses_an_edited_manifest_whose_lists_disagree_with_its_row(field, value, reason):
    manifest = active_protocol.generate("F20", base_case_ids=BASES, **COMMON)
    edited = {**copy.deepcopy(manifest), field: value}
    if field == "stage_configurations":
        edited["stage_configuration_count"] = len(value)
    with pytest.raises(active_protocol.ArithmeticError_, match=reason):
        active_protocol.validate(edited)


STOP_TIER = next(tier for tier, row in active_protocol.TIERS.items() if row["tier_class"] == "STOP")


@pytest.mark.parametrize("field, value", [("channels", ["C2"]), ("run_indices", [1]), ("c1_controls", ["c1-001"])])
def test_a_stop_manifest_with_any_list_is_refused(field, value):
    manifest = active_protocol.generate(STOP_TIER, **{**COMMON, "active_contributor_count": 0})
    active_protocol.validate(manifest)
    with pytest.raises(active_protocol.ArithmeticError_, match=field):
        active_protocol.validate({**manifest, field: value})


@pytest.mark.parametrize("field, value", [
    ("configurations", ["D0_BASELINE", "D2_DATAMARKING", "D1_POLICY_GATE"]),
    ("run_indices", [3, 2, 1]),
    ("stage_configurations", ["D0_BASELINE", "D2_DATAMARKING", "D1_POLICY_GATE"]),
])
def test_validate_refuses_a_reordered_list(field, value):
    manifest = active_protocol.generate("F20", base_case_ids=BASES, **COMMON)
    with pytest.raises(active_protocol.ArithmeticError_, match=field):
        active_protocol.validate({**copy.deepcopy(manifest), field: value})


# --- N-77-5 ------------------------------------------------------------------------


def test_engineering_totals_count_the_plans_checks_not_the_records():
    plan = load_plan()
    ids = [check["check_id"] for check in plan["checks"]]
    records = [{"check_id": cid, "passed": True} for cid in ids[:-1]]  # the last check has no record
    text = render(plan, records)
    assert f"- Passed: {len(ids) - 1}" in text
    assert "- Failed: 0" in text
    assert "- Indeterminate (incomplete evidence, not false): 1" in text


def test_an_engineering_record_for_a_check_outside_the_plan_is_refused():
    plan = load_plan()
    with pytest.raises(ValueError, match="not in the validation plan"):
        render(plan, [{"check_id": "stray-check", "passed": False}])


def test_two_engineering_records_for_one_check_are_refused():
    plan = load_plan()
    cid = plan["checks"][0]["check_id"]
    with pytest.raises(ValueError, match="more than one record"):
        render(plan, [{"check_id": cid, "passed": True}, {"check_id": cid, "passed": False}])


# --- N-77-6 ------------------------------------------------------------------------


FIXTURE = ROOT / "tests" / "fixtures" / "result" / "valid_c1_control.json"


def _record(cid="c1-001", run_index=1, experiment="exp-1"):
    record = json.loads(FIXTURE.read_text(encoding="utf-8"))
    record["base_case_id"] = cid
    record["run_index"] = run_index
    record["experiment_id"] = experiment
    record["logical_trial_id"] = f"{experiment}:p1:m:{cid}:C1:attack:D0_BASELINE:r{run_index}"
    record["comparison_superblock_id"] = f"{experiment}:p1:m:{cid}:r{run_index}"
    return record


def test_one_logical_trial_counted_twice_is_refused():
    with pytest.raises(ValueError, match="more than once"):
        c1_table.tabulate([_record(), _record()], ["c1-001"])


def test_c1_records_from_two_experiments_are_refused():
    with pytest.raises(ValueError, match="one experiment"):
        c1_table.tabulate([_record(), _record(run_index=2, experiment="exp-2")], ["c1-001"])


def test_c1_records_from_two_protocol_versions_are_refused():
    other = _record(run_index=2)
    other["protocol_version"] = "9.9.9"
    with pytest.raises(ValueError, match="one experiment"):
        c1_table.tabulate([_record(), other], ["c1-001"])


def test_distinct_repeats_of_one_experiment_are_counted():
    rows = c1_table.tabulate([_record(run_index=1), _record(run_index=2)], ["c1-001"])
    assert rows["c1-001"]["repeats"] == 2
