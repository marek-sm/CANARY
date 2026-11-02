"""Gate 2 budget equation over development-grid records (decisions 0025 and 0026)."""

import copy
import json

import pytest

from analysis import price_bound
from analysis import gate2_budget
from analysis.gate2_budget import TIERS, evaluate_budget, trial_cost_usd
from runner.mock_provider import MOCK_MODEL_ID
from tests.test_floor_count import MODEL, events, grid
from tests.test_status_consistency import SPEC, tier_table

BOUND = price_bound.PRICE_BOUND_USD
USED = 107


def _live_grid(input_tokens=1000, output_tokens=200):
    trials = grid()
    for record, ev in trials:
        record = copy.deepcopy(record)
        record["status"] = "completed"
        record["usage"] = {"input_tokens": input_tokens, "output_tokens": output_tokens}
        record["run_metadata"]["model_requested"] = MODEL
        record["run_metadata"]["model_resolved"] = MODEL
        yield record, ev


def _evaluate(trials=None, *, balance=1000.0, **kwargs):
    kwargs.setdefault("development_trials_used", USED)
    return evaluate_budget(list(trials if trials is not None else _live_grid()), remaining_balance_usd=balance, **kwargs)


def test_budget_equation_passes_with_generous_balance():
    report = _evaluate()
    assert report["passes"] is True
    assert report["required_balance_usd"] > 0


def test_budget_equation_fails_when_the_balance_is_short():
    assert _evaluate(balance=0.01)["passes"] is False


def test_budget_equation_refuses_mock_provider():
    record, ev = next(_live_grid())
    record["run_metadata"]["model_requested"] = MOCK_MODEL_ID
    with pytest.raises(ValueError, match="mock-provider"):
        evaluate_budget([(record, ev)], remaining_balance_usd=1.0, development_trials_used=USED)


def test_the_reserve_is_computed_from_the_bound_at_f20():
    report = _evaluate()
    assert report["reserve_trials"] == {"development": 13, "rehearsal": 30, "stage": 3}
    assert report["unspent_development_rehearsal_and_stage_reserve_usd"] == pytest.approx(46 * BOUND)


def test_the_c1_cost_is_never_below_the_bound():
    report = _evaluate()
    assert report["conservative_C1_trial_cost_usd"] == pytest.approx(BOUND)
    assert _evaluate(c1_pilot_cost_usd=BOUND * 2)["conservative_C1_trial_cost_usd"] == pytest.approx(BOUND * 2)


def test_a_thin_stratum_takes_the_larger_of_the_global_maximum_and_the_bound():
    cheap = [trial for trial in _live_grid() if trial[0]["channel"] == "C2"]
    report = _evaluate(cheap)
    assert report["max_observed_dev_trial_cost_by_stratum_usd"]["C3/attack/D0_BASELINE"] == pytest.approx(BOUND)
    costly = [trial for trial in _live_grid(output_tokens=2_000_000) if trial[0]["channel"] == "C2"]
    report = _evaluate(costly)
    assert report["global_max_observed_dev_trial_cost_usd"] > BOUND
    assert report["max_observed_dev_trial_cost_by_stratum_usd"]["C3/attack/D0_BASELINE"] == pytest.approx(
        report["global_max_observed_dev_trial_cost_usd"])


def _stratum_trials(count_failed, count_valid):
    """One stratum's cells, the first ``count_failed`` of them infrastructure failures."""
    cells = [t for t in _live_grid() if (t[0]["channel"], t[0]["condition"], t[0]["configuration"]) == ("C2", "attack", "D0_BASELINE")]
    assert len(cells) >= count_failed + count_valid
    others = [t for t in _live_grid() if (t[0]["channel"], t[0]["condition"], t[0]["configuration"]) != ("C2", "attack", "D0_BASELINE")]
    picked = []
    for index, (record, _) in enumerate(cells[:count_failed + count_valid]):
        record = copy.deepcopy(record)
        if index < count_failed:
            record["status"] = "infrastructure_failure"
            record["usage"] = {"input_tokens": None, "output_tokens": None}
            picked.append((record, events(record, stops=(None,))))
        else:
            picked.append((record, cells[index][1]))
    return picked + others


C2_ATTACK = "C2/attack/D0_BASELINE"


def test_a_stratum_of_infrastructure_failures_is_thin_and_never_priced_at_zero():
    report = _evaluate(_stratum_trials(5, 0))
    assert report["max_observed_dev_trial_cost_by_stratum_usd"][C2_ATTACK] == pytest.approx(BOUND)


def test_failures_don_t_count_toward_the_three_valid_observations():
    report = _evaluate(_stratum_trials(3, 2))
    assert report["max_observed_dev_trial_cost_by_stratum_usd"][C2_ATTACK] == pytest.approx(BOUND)


def test_a_failed_trials_recorded_spend_still_counts_toward_the_stratum_maximum():
    trials = _stratum_trials(2, 3)
    failed = next(record for record, _ in trials if record["status"] == "infrastructure_failure")
    failed["usage"] = {"input_tokens": 60_000, "output_tokens": 4_000}
    spend = 60_000 * price_bound.INPUT_USD_PER_TOKEN + 4_000 * price_bound.OUTPUT_USD_PER_TOKEN
    report = _evaluate(trials)
    assert report["max_observed_dev_trial_cost_by_stratum_usd"][C2_ATTACK] == pytest.approx(spend)


def test_three_valid_observations_use_the_strata_own_maximum():
    report = _evaluate(_stratum_trials(2, 3))
    own = 1000 * price_bound.INPUT_USD_PER_TOKEN + 200 * price_bound.OUTPUT_USD_PER_TOKEN
    assert report["max_observed_dev_trial_cost_by_stratum_usd"][C2_ATTACK] == pytest.approx(own)


def test_a_defense_on_a_row_without_one_to_choose_is_refused():
    with pytest.raises(ValueError, match="defense"):
        _evaluate(tier="M10-ALL", defense="D2_DATAMARKING")


def test_the_cli_reports_the_equation_on_a_run_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(gate2_budget, "load_run", lambda _path: list(_live_grid()))
    out = tmp_path / "budget.json"
    assert gate2_budget.main([str(tmp_path), "--remaining-balance-usd", "9.95", "--development-trials-used", "107", "--out", str(out)]) == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["tier"] == "F20" and report["reserve_trials"]["development"] == 13


def test_a_long_prompt_trial_whose_attempts_don_t_add_up_is_refused():
    record, _ = next(_live_grid(input_tokens=150_000, output_tokens=100))
    for attempts in (None, [], [{"event_type": "provider_attempt", "payload": {"outcome": "model_response", "usage": {"input_tokens": None, "output_tokens": None}}}]):
        with pytest.raises(ValueError, match="100,000"):
            trial_cost_usd(record, attempts)
    small, _ = next(_live_grid())
    attempt = {"event_type": "provider_attempt", "payload": {"outcome": "model_response", "usage": {"input_tokens": 150_000, "output_tokens": 100}}}
    with pytest.raises(ValueError, match="100,000"):
        trial_cost_usd(small, [attempt])


def test_required_balance_applies_the_contingency_to_primary_and_c1_but_not_the_reserve():
    report = _evaluate()
    primary = sum(report["max_observed_dev_trial_cost_by_stratum_usd"].values()) * report["planned_primary_trials_per_stratum"]
    expected = 1.25 * (primary + report["planned_C1_trials"] * report["conservative_C1_trial_cost_usd"])
    expected += report["unspent_development_rehearsal_and_stage_reserve_usd"]
    assert report["required_balance_usd"] == pytest.approx(expected)


@pytest.mark.parametrize("tier", sorted(TIERS))
def test_each_tier_row_matches_the_specs_official_trial_count(tier):
    row = TIERS[tier]
    planned = row["primary_per_stratum"] * len(row["channels"]) * 2 * row["configurations"] + row["c1_trials"]
    assert planned == tier_table(SPEC.read_text(encoding="utf-8"))[tier]


def test_a_lower_tier_prices_only_its_own_strata_and_stage_set():
    report = _evaluate(tier="L8-BASE")
    assert set(report["max_observed_dev_trial_cost_by_stratum_usd"]) == {"C2/attack/D0_BASELINE", "C2/clean/D0_BASELINE"}
    assert report["planned_primary_trials_per_stratum"] == 24 and report["planned_C1_trials"] == 6
    assert report["reserve_trials"] == {"development": 13, "rehearsal": 10, "stage": 1}


def test_a_one_row_needs_its_retained_defense():
    with pytest.raises(ValueError, match="defense"):
        _evaluate(tier="M10-ONE")
    report = _evaluate(tier="M10-ONE", defense="D2_DATAMARKING")
    assert not [s for s in report["max_observed_dev_trial_cost_by_stratum_usd"] if "D1_POLICY_GATE" in s]


def test_more_development_trials_than_the_ceiling_are_refused():
    with pytest.raises(ValueError, match="120"):
        _evaluate(development_trials_used=121)


def test_an_attempt_over_100000_input_tokens_is_priced_at_the_higher_rates():
    record, ev = next(_live_grid(input_tokens=150_000, output_tokens=100))
    attempt = {"event_type": "provider_attempt", "payload": {
        "outcome": "model_response", "usage": {"input_tokens": 150_000, "output_tokens": 100}}}
    assert trial_cost_usd(record, [attempt]) == pytest.approx(150_000 * 0.50e-6 + 100 * 2.50e-6)


def test_a_summed_trial_under_100000_per_attempt_stays_at_the_lower_rates():
    record, ev = next(_live_grid(input_tokens=150_000, output_tokens=200))
    attempts = [{"event_type": "provider_attempt", "payload": {
        "outcome": "model_response", "usage": {"input_tokens": 75_000, "output_tokens": 100}}} for _ in range(2)]
    assert trial_cost_usd(record, attempts) == pytest.approx(150_000 * 0.10e-6 + 200 * 0.50e-6)
