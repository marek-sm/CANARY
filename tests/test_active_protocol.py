"""W8-T3: tests for the protocol/active.json generator and its Section 12 arithmetic."""

from __future__ import annotations

import copy
import json

import pytest

from analysis.active_protocol import (
    TIERS,
    ArithmeticError_,
    compute_arithmetic,
    generate,
    load,
    retained_configurations,
    validate,
)

_COMMON = dict(
    protocol_id="p",
    protocol_version="0.1.0",
    active_contributor_count=6,
    selection_reason_category="headcount-ceiling",
    accountable_roles=["lead"],
    data_cutoff="2026-11-22",
)

# The Section 12 published official counts. The generator must recompute each.
_OFFICIAL = {
    "F20": 1092, "R15": 822, "M10-ALL": 369, "M10-ONE": 249, "M10-BASE": 129,
    "L8-ONE": 102, "L8-BASE": 54, "R6-ONE": 78, "R6-BASE": 42,
    "ENGINEERING": 0, "STOP": 0,
}


@pytest.mark.parametrize("tier", sorted(TIERS))
def test_every_tier_arithmetic_agrees_with_section_12(tier):
    arithmetic = compute_arithmetic(tier)
    assert arithmetic["computed_official_trial_count"] == _OFFICIAL[tier]


def test_f20_is_1080_primary_plus_12_c1():
    a = compute_arithmetic("F20")
    assert a["primary_trials"] == 1080
    assert a["c1_trials"] == 12
    assert a["computed_official_trial_count"] == 1092


def _fallback(**overrides):
    base = {
        "validation_id": "val-eng",
        "source_ledger_hash": "a" * 64,
        "validation_plan_hash": "b" * 64,
        "validation_schema_hash": "c" * 64,
        "report_generator_hash": "d" * 64,
    }
    base.update(overrides)
    return base


def test_f20_manifest_is_schema_valid_and_full_geometry():
    m = generate("F20", **_COMMON)
    assert m["official_trial_count"] == 1092
    assert m["configurations"] == ["D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING"]
    assert m["base_case_count"] == 20
    assert m["channels"] == ["C2", "C3", "C4"]
    # dormant fallback is null while an empirical tier is active
    assert m["engineering_fallback"]["validation_id"] is None


def test_engineering_manifest_has_empty_geometry_and_null_official_fields():
    m = generate("ENGINEERING", **{**_COMMON, "active_contributor_count": 1},
                 engineering_fallback=_fallback())
    assert m["official_trial_count"] == 0
    assert m["base_case_ids"] == [] and m["channels"] == [] and m["configurations"] == []
    assert m["empirical"]["experiment_id"] is None
    assert m["empirical"]["null_reasons"], "ENGINEERING must record a null reason"
    assert m["engineering_fallback"]["validation_id"] == "val-eng"


def test_one_tier_retains_baseline_plus_one_defense():
    assert retained_configurations("M10-ONE") == ["D0_BASELINE", "D1_POLICY_GATE"]
    assert retained_configurations("M10-ONE", "D2_DATAMARKING") == ["D0_BASELINE", "D2_DATAMARKING"]
    assert retained_configurations("M10-BASE") == ["D0_BASELINE"]
    assert retained_configurations("F20") == ["D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING"]


def test_tampered_official_count_is_rejected():
    m = generate("F20", **_COMMON)
    bad = copy.deepcopy(m)
    bad["official_trial_count"] = 9999
    with pytest.raises(ArithmeticError_):
        validate(bad)


def test_tampered_arithmetic_block_is_rejected():
    m = generate("R15", **_COMMON)
    bad = copy.deepcopy(m)
    bad["tier_arithmetic"]["primary_trials"] = 1
    with pytest.raises(ArithmeticError_):
        validate(bad)


def test_round_trip_through_disk(tmp_path):
    m = generate("M10-ALL", **_COMMON)
    path = tmp_path / "active.json"
    path.write_text(json.dumps(m), encoding="utf-8")
    loaded = load(path)
    assert loaded == m


def test_unknown_tier_rejected():
    with pytest.raises(ValueError):
        generate("NOT-A-TIER", **_COMMON)
