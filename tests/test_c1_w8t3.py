"""W8-T3's C1 part (decision 0034 item 8): schedule rows, split guard, C1 table, active.json C1 list.

The official C1 executor is not built: a C1 control has no task template, so what is
authorized in a C1 trial needs a project-lead decision first. These tests pin that the runner
fails closed on a C1 run rather than scoring every C1 trial as an infrastructure failure.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from analysis import active_protocol, c1_table
from runner import execute, schedule

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "result" / "valid_c1_control.json"
C1_IDS = ["c1-002", "c1-003", "c1-001", "c1-004"]


def _c1_spec(**overrides):
    spec = schedule.c1_schedule_spec(C1_IDS, experiment_id="c1-test", model_id="mock-canned-v0",
                                     seed="s", protocol_sentinel="p1")
    spec.update(overrides)
    return spec


# --- schedule rows ---------------------------------------------------------------

def test_c1_schedule_is_controls_times_three_repeats_attack_d0():
    trials = schedule.generate_schedule(_c1_spec())
    assert len(trials) == 4 * 3
    assert {(t.channel, t.condition, t.configuration) for t in trials} == {("C1", "attack", "D0_BASELINE")}
    assert {t.base_case_id for t in trials} == set(C1_IDS)


def test_each_c1_repeat_is_its_own_superblock():
    trials = schedule.generate_schedule(_c1_spec())
    groups = schedule.superblock_groups(trials)
    assert len(groups) == 12  # one canary pair per (control, repeat), SPEC.md Section 9
    assert all(len(members) == 1 for members in groups.values())


@pytest.mark.parametrize("overrides", [
    {"channels": ["C1", "C2"]},
    {"conditions": ["attack", "clean"]},
    {"conditions": ["clean"]},
    {"configurations": ["D0_BASELINE", "D1_POLICY_GATE"]},
    {"configurations": ["D2_DATAMARKING"]},
    {"base_case_ids": ["dev-001"]},
    {"base_case_ids": ["eval-014"]},
])
def test_a_c1_spec_of_any_other_shape_is_refused(overrides):
    spec = {**_c1_spec(), **overrides}
    with pytest.raises(ValueError):
        schedule.generate_schedule(spec)


def test_indirect_specs_are_unchanged():
    spec = {"experiment_id": "e", "model_id": "m", "seed": "s", "base_case_ids": ["dev-001"],
            "channels": ["C2", "C3", "C4"], "conditions": ["attack", "clean"],
            "configurations": ["D0_BASELINE"], "repeats": 1}
    assert len(schedule.generate_schedule(spec)) == 6


def test_a_hand_built_c1_trial_of_the_wrong_shape_is_refused():
    trial = schedule.generate_schedule(_c1_spec())[0]
    bad = copy.copy(trial)
    object.__setattr__(bad, "configuration", "D1_POLICY_GATE")
    with pytest.raises(ValueError):
        schedule.validate_trial(bad)


# --- split guard -----------------------------------------------------------------

def _run(tmp_path, trials, **kwargs):
    return execute.run_schedule(tmp_path / "run", trials, **kwargs)


def test_c1_split_needs_a_protocol_version(tmp_path):
    with pytest.raises(ValueError, match="protocol_version"):
        _run(tmp_path, schedule.generate_schedule(_c1_spec()), split="c1_control", analysis_role="c1_control")


def test_c1_split_needs_the_c1_control_role(tmp_path):
    with pytest.raises(ValueError, match="analysis_role"):
        _run(tmp_path, schedule.generate_schedule(_c1_spec()), split="c1_control",
             protocol_version="1.23.0", analysis_role="primary_indirect")


def test_c1_split_ids_cannot_carry_the_unfrozen_sentinel(tmp_path):
    trials = schedule.generate_schedule(_c1_spec(protocol_sentinel=schedule.PROTOCOL_SENTINEL))
    with pytest.raises(ValueError, match="sentinel|unfrozen"):
        _run(tmp_path, trials, split="c1_control", protocol_version="1.23.0", analysis_role="c1_control")


def test_c1_is_never_an_evaluation_channel(tmp_path):
    with pytest.raises(ValueError, match="never an evaluation channel"):
        _run(tmp_path, schedule.generate_schedule(_c1_spec()), split="evaluation", protocol_version="1.23.0")


def test_a_well_formed_c1_run_fails_closed_before_writing_anything(tmp_path):
    """No official C1 trial body exists, so the runner refuses rather than scoring infrastructure failures."""
    with pytest.raises(execute.C1ExecutorUnavailable):
        _run(tmp_path, schedule.generate_schedule(_c1_spec()), split="c1_control",
             protocol_version="1.23.0", analysis_role="c1_control")
    assert not (tmp_path / "run").exists()


def test_unknown_split_is_refused(tmp_path):
    with pytest.raises(ValueError, match="split"):
        _run(tmp_path, schedule.generate_schedule(_c1_spec()), split="c1")


# --- active.json C1 list ---------------------------------------------------------

@pytest.mark.parametrize("tier, expected", [
    ("F20", C1_IDS), ("R15", C1_IDS),
    ("M10-ALL", C1_IDS[:3]), ("M10-ONE", C1_IDS[:3]), ("M10-BASE", C1_IDS[:3]),
    ("L8-ONE", C1_IDS[:2]), ("R6-BASE", C1_IDS[:2]),
    ("ENGINEERING", []), ("STOP", []),
])
def test_active_json_c1_list_is_the_committed_prefix(tier, expected):
    assert active_protocol.c1_control_ids_for(tier) == expected


def test_generated_manifest_carries_the_c1_list():
    manifest = active_protocol.generate(
        "F20", protocol_id="p", protocol_version="1.23.0", active_contributor_count=6,
        selection_reason_category="headcount-ceiling", accountable_roles=["lead"], data_cutoff="2026-11-22")
    assert manifest["c1_controls"] == C1_IDS
    assert manifest["tier_arithmetic"]["c1_trials"] == 12


def test_a_c1_prefix_that_disagrees_with_the_tier_row_is_refused(tmp_path):
    bad = json.loads((ROOT / "corpus" / "c1_controls" / "manifest.json").read_text(encoding="utf-8"))
    bad["tier_prefixes"]["F20"] = C1_IDS[:3]
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(active_protocol.ArithmeticError_):
        active_protocol.c1_control_ids_for("F20", path)


def test_a_given_c1_list_of_the_wrong_length_is_refused():
    with pytest.raises(active_protocol.ArithmeticError_):
        active_protocol.generate(
            "F20", protocol_id="p", protocol_version="1.23.0", active_contributor_count=6,
            selection_reason_category="x", accountable_roles=[], data_cutoff="d", c1_control_ids=C1_IDS[:2])


# --- C1 table --------------------------------------------------------------------

def _record(cid="c1-001", **security):
    record = json.loads(FIXTURE.read_text(encoding="utf-8"))
    record["base_case_id"] = cid
    record["security"].update(security)
    return record


def test_table_counts_true_false_null_per_control_and_outcome():
    records = [
        _record("c1-001", unauthorized_user_disclosure=True),
        _record("c1-001", unauthorized_user_disclosure=False),
        _record("c1-001", unauthorized_user_disclosure=None),
    ]
    rows = c1_table.tabulate(records, C1_IDS)
    disclosure = rows["c1-001"]["outcomes"]["unauthorized_user_disclosure"]
    assert rows["c1-001"]["repeats"] == 3
    assert (disclosure["true"], disclosure["false"], disclosure["null"]) == (1, 1, 1)
    assert rows["c1-002"]["repeats"] == 0


def test_table_counts_infrastructure_failures():
    failed = _record("c1-003")
    failed["status"] = "infrastructure_failure"
    failed["termination_reason"] = "infrastructure_failure"
    rows = c1_table.tabulate([failed, _record("c1-003")], C1_IDS)
    assert rows["c1-003"]["infrastructure_failures"] == 1


def test_table_ignores_non_c1_records_and_refuses_an_unknown_control():
    dev = _record()
    dev["split"] = "development"
    assert c1_table.tabulate([dev], C1_IDS)["c1-001"]["repeats"] == 0
    with pytest.raises(ValueError, match="outside"):
        c1_table.tabulate([_record("c1-099")], C1_IDS)


def test_rendered_table_has_no_rate_or_interval():
    text = c1_table.render(c1_table.tabulate([_record()], C1_IDS), has_records=True)
    assert "not an estimate" in text
    assert "%" not in text
    # "rate" and "interval" appear only in the disclaimer that the table has neither.
    body = "\n".join(line for line in text.splitlines() if line.startswith("|"))
    assert "rate" not in body.lower() and "interval" not in body.lower()
    # 4 controls x 9 outcomes data rows
    assert sum(1 for line in text.splitlines() if line.startswith("| c1-")) == 4 * len(c1_table.OUTCOMES)


def test_pre_results_shell_shows_no_values():
    text = c1_table.render(c1_table.tabulate([], C1_IDS), has_records=False)
    assert "PRE-RESULTS" in text
    assert "| c1-002 | 0 | unauthorized_user_disclosure | — | — | — | — |" in text
