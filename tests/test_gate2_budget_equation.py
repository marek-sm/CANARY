"""The Gate 2 budget equation's arithmetic, term by term (SPEC.md Section 9,
"Trial budget"; decision 0010 list price).

Added from mutation testing (reports/cloud/mutation.md): the two existing
tests in test_gate2_budget.py pass with a generous balance, so a changed
price, contingency factor, planned count, stratum rule, or comparison went
unnoticed. These pin each term with exact values.
"""

import copy
import json

import pytest

from analysis import gate2_budget
from analysis.gate2_budget import (
    MIN_STRATUM_OBSERVATIONS,
    PLANNED_C1_TRIALS_F20,
    PLANNED_PRIMARY_PER_STRATUM_F20,
    STRATA,
    evaluate_budget,
    main,
    trial_cost_usd,
)
from runner.mock_provider import MOCK_MODEL_ID
from tests.test_floor_count import MODEL, events, grid, result

# Decision 0010: $0.10 per million input tokens, $0.50 per million output tokens.
IN_RATE = 0.10 / 1_000_000
OUT_RATE = 0.50 / 1_000_000


def _live(record, input_tokens, output_tokens):
    record = copy.deepcopy(record)
    record["usage"] = {"provider_requests": 1, "input_tokens": input_tokens, "output_tokens": output_tokens,
                       "latency_ms": None}
    record["run_metadata"]["model_requested"] = MODEL
    record["run_metadata"]["model_resolved"] = MODEL
    return record


def _uniform_grid(input_tokens=1000, output_tokens=200):
    return [(_live(r, input_tokens, output_tokens), ev) for r, ev in grid()]


def test_f20_geometry_constants():
    # F20: 20 bases x 3 channels x 2 conditions x 3 configurations = 1,080 primary trials
    # over 18 strata, plus 4 C1 controls x 3 configurations = 12.
    assert len(STRATA) == 18 == len(set(STRATA))
    assert {s[0] for s in STRATA} == {"C2", "C3", "C4"}
    assert {s[1] for s in STRATA} == {"attack", "clean"}
    assert {s[2] for s in STRATA} == {"D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING"}
    assert PLANNED_PRIMARY_PER_STRATUM_F20 * len(STRATA) == 1080
    assert PLANNED_C1_TRIALS_F20 == 12
    assert MIN_STRATUM_OBSERVATIONS == 3
    assert gate2_budget.DEFAULT_INPUT_USD_PER_TOKEN == IN_RATE
    assert gate2_budget.DEFAULT_OUTPUT_USD_PER_TOKEN == OUT_RATE


def test_trial_cost_uses_the_decision_0010_list_price():
    record = _live(grid()[0][0], 1_000_000, 1_000_000)
    assert trial_cost_usd(record) == pytest.approx(0.10 + 0.50)
    record = _live(grid()[0][0], 3_000_000, 0)
    assert trial_cost_usd(record) == pytest.approx(0.30)
    record = _live(grid()[0][0], 0, 2_000_000)
    assert trial_cost_usd(record) == pytest.approx(1.00)


def test_required_balance_is_the_spec_equation_exactly():
    trials = _uniform_grid(1000, 200)
    per_trial = 1000 * IN_RATE + 200 * OUT_RATE
    report = evaluate_budget(trials, remaining_balance_usd=0.0, reserve_usd=7.0, conservative_c1_trial_cost_usd=0.02)
    expected = 1.25 * (18 * 60 * per_trial + 12 * 0.02) + 7.0
    assert report["required_balance_usd"] == pytest.approx(expected)
    assert report["global_max_observed_dev_trial_cost_usd"] == pytest.approx(per_trial)
    assert set(report["max_observed_dev_trial_cost_by_stratum_usd"]) == {f"{c}/{k}/{g}" for c, k, g in STRATA}
    assert report["contingency_factor"] == 1.25
    assert report["planned_primary_trials_per_stratum"] == 60
    assert report["planned_C1_trials"] == 12
    assert report["remaining_funded_balance_at_gate_2_usd"] == 0.0
    assert report["unspent_development_rehearsal_and_stage_reserve_usd"] == 7.0
    assert report["conservative_C1_trial_cost_usd"] == 0.02
    assert report["experiment_id"] == "grid-dev"
    assert report["passes"] is False


def test_a_balance_equal_to_the_requirement_passes_and_one_cent_less_fails():
    trials = _uniform_grid(1000, 200)
    required = evaluate_budget(trials, remaining_balance_usd=0.0, reserve_usd=1.0,
                               conservative_c1_trial_cost_usd=0.05)["required_balance_usd"]
    at = evaluate_budget(trials, remaining_balance_usd=required, reserve_usd=1.0, conservative_c1_trial_cost_usd=0.05)
    assert at["passes"] is True
    below = evaluate_budget(trials, remaining_balance_usd=required - 0.01, reserve_usd=1.0,
                            conservative_c1_trial_cost_usd=0.05)
    assert below["passes"] is False


def _with_stratum_costs(stratum, costs):
    """The grid with every trial at 1,000/200 tokens, except the first
    len(costs) trials of `stratum`, which get those input-token counts."""
    trials = []
    remaining = list(costs)
    for record, ev in grid():
        key = (record["channel"], record["condition"], record["configuration"])
        if key == stratum and remaining:
            trials.append((_live(record, remaining.pop(0), 0), ev))
        elif key == stratum:
            continue  # leave the stratum with exactly len(costs) observations
        else:
            trials.append((_live(record, 1000, 200), ev))
    return trials


def test_a_stratum_with_three_observations_uses_its_own_maximum():
    stratum = ("C2", "attack", "D0_BASELINE")
    trials = _with_stratum_costs(stratum, [10, 20, 30])
    report = evaluate_budget(trials, remaining_balance_usd=0.0, reserve_usd=0.0, conservative_c1_trial_cost_usd=0.0)
    bounds = report["max_observed_dev_trial_cost_by_stratum_usd"]
    assert bounds["C2/attack/D0_BASELINE"] == pytest.approx(30 * IN_RATE)
    other = 1000 * IN_RATE + 200 * OUT_RATE
    assert bounds["C3/attack/D0_BASELINE"] == pytest.approx(other)
    assert report["required_balance_usd"] == pytest.approx(1.25 * 60 * (17 * other + 30 * IN_RATE))


def test_a_stratum_with_two_observations_falls_back_to_the_global_maximum():
    stratum = ("C2", "attack", "D0_BASELINE")
    trials = _with_stratum_costs(stratum, [10, 20])
    report = evaluate_budget(trials, remaining_balance_usd=0.0, reserve_usd=0.0, conservative_c1_trial_cost_usd=0.0)
    other = 1000 * IN_RATE + 200 * OUT_RATE
    assert report["max_observed_dev_trial_cost_by_stratum_usd"]["C2/attack/D0_BASELINE"] == pytest.approx(other)


def test_the_stratum_bound_is_the_maximum_not_another_statistic():
    stratum = ("C4", "clean", "D2_DATAMARKING")
    trials = _with_stratum_costs(stratum, [50, 5000, 70, 60])
    report = evaluate_budget(trials, remaining_balance_usd=0.0, reserve_usd=0.0, conservative_c1_trial_cost_usd=0.0)
    assert report["max_observed_dev_trial_cost_by_stratum_usd"]["C4/clean/D2_DATAMARKING"] == pytest.approx(5000 * IN_RATE)
    # The global maximum is the largest trial anywhere.
    assert report["global_max_observed_dev_trial_cost_usd"] == pytest.approx(max(5000 * IN_RATE, 1000 * IN_RATE + 200 * OUT_RATE))


def test_unknown_usage_is_read_from_the_trials_events():
    record = _live(grid()[0][0], None, None)
    ev = events(record, stops=("tool_use", None, "end_turn"))
    ev[1]["payload"]["usage"] = {"input_tokens": 100, "output_tokens": 10}
    ev[3]["payload"]["usage"] = {"input_tokens": 300, "output_tokens": 30}
    # An attempt with no model content and no usage counts nothing.
    assert trial_cost_usd(record, ev) == pytest.approx(400 * IN_RATE + 40 * OUT_RATE)


def test_a_partly_known_result_total_is_not_trusted():
    record = _live(grid()[0][0], 500, None)
    ev = events(record, stops=("end_turn",))
    ev[1]["payload"]["usage"] = {"input_tokens": 700, "output_tokens": 70}
    assert trial_cost_usd(record, ev) == pytest.approx(700 * IN_RATE + 70 * OUT_RATE)


def test_a_model_response_without_usage_is_never_priced_at_zero():
    record = _live(grid()[0][0], None, None)
    ev = events(record, stops=("end_turn",))
    with pytest.raises(ValueError, match="without recorded usage"):
        trial_cost_usd(record, ev)
    ev[1]["payload"]["usage"] = {"input_tokens": 5, "output_tokens": None}
    with pytest.raises(ValueError, match="without recorded usage"):
        trial_cost_usd(record, ev)
    with pytest.raises(ValueError, match="pass the trial's events"):
        trial_cost_usd(record)


def test_boolean_token_counts_are_unknown_not_one():
    record = _live(grid()[0][0], True, True)
    ev = events(record, stops=("end_turn",))
    ev[1]["payload"]["usage"] = {"input_tokens": 9, "output_tokens": 1}
    assert trial_cost_usd(record, ev) == pytest.approx(9 * IN_RATE + 1 * OUT_RATE)


def test_one_run_only_and_never_empty():
    trials = _uniform_grid()
    other = copy.deepcopy(trials[0][0])
    other["experiment_id"] = "grid-dev-2"
    with pytest.raises(ValueError, match="one experiment_id"):
        evaluate_budget([*trials, (other, trials[0][1])], remaining_balance_usd=1.0, reserve_usd=0.0,
                        conservative_c1_trial_cost_usd=0.0)
    with pytest.raises(ValueError, match="no grid trials"):
        evaluate_budget([], remaining_balance_usd=1.0, reserve_usd=0.0, conservative_c1_trial_cost_usd=0.0)


@pytest.mark.parametrize("field", ["model_requested", "model_resolved"])
def test_a_mock_model_in_either_field_is_refused(field):
    trials = _uniform_grid()
    record = copy.deepcopy(trials[5][0])
    record["run_metadata"][field] = MOCK_MODEL_ID
    with pytest.raises(ValueError, match="mock-provider"):
        evaluate_budget([*trials[:5], (record, trials[5][1]), *trials[6:]], remaining_balance_usd=1.0,
                        reserve_usd=0.0, conservative_c1_trial_cost_usd=0.0)


def test_the_command_line_requires_the_reserve_and_reports_the_equation(tmp_path, capsys):
    run = tmp_path / "run"
    for i, (record, ev) in enumerate(_uniform_grid()):
        trial_dir = run / f"t{i:04d}"
        trial_dir.mkdir(parents=True)
        (trial_dir / "results.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
        (trial_dir / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in ev), encoding="utf-8")
    with pytest.raises(SystemExit):
        main([str(run), "--remaining-balance-usd", "1", "--conservative-c1-trial-cost-usd", "0.01"])
    out = tmp_path / "report.json"
    assert main([str(run), "--remaining-balance-usd", "1000", "--reserve-usd", "2",
                 "--conservative-c1-trial-cost-usd", "0.01", "--out", str(out)]) == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    per_trial = 1000 * IN_RATE + 200 * OUT_RATE
    assert report["required_balance_usd"] == pytest.approx(1.25 * (1080 * per_trial + 12 * 0.01) + 2)
    assert report["passes"] is True
    assert main([str(tmp_path / "empty"), "--remaining-balance-usd", "1", "--reserve-usd", "0",
                 "--conservative-c1-trial-cost-usd", "0"]) == 1
    assert "gate2-budget:" in capsys.readouterr().err


def test_the_equation_prices_a_trial_with_unknown_usage_from_its_events():
    # Kills x_evaluate_budget__mutmut_31/33, which dropped the trial's events so an
    # unknown result total refused instead of being priced from its attempts.
    trials = _uniform_grid(1000, 200)
    record, ev = trials[0]
    record = copy.deepcopy(record)
    record["usage"] = {"provider_requests": 1, "input_tokens": None, "output_tokens": None, "latency_ms": None}
    ev = copy.deepcopy(ev)
    ev[1]["payload"]["usage"] = {"input_tokens": 9000, "output_tokens": 900}
    report = evaluate_budget([(record, ev), *trials[1:]], remaining_balance_usd=0.0, reserve_usd=0.0,
                             conservative_c1_trial_cost_usd=0.0)
    assert report["global_max_observed_dev_trial_cost_usd"] == pytest.approx(9000 * IN_RATE + 900 * OUT_RATE)


def test_a_stratum_with_no_records_falls_back_to_the_global_maximum():
    # Kills x_evaluate_budget__mutmut_45/47 (a missing stratum's default became None).
    trials = [(r, ev) for r, ev in _uniform_grid(1000, 200)
              if (r["channel"], r["condition"], r["configuration"]) != ("C3", "clean", "D1_POLICY_GATE")]
    report = evaluate_budget(trials, remaining_balance_usd=0.0, reserve_usd=0.0, conservative_c1_trial_cost_usd=0.0)
    per_trial = 1000 * IN_RATE + 200 * OUT_RATE
    assert report["max_observed_dev_trial_cost_by_stratum_usd"]["C3/clean/D1_POLICY_GATE"] == pytest.approx(per_trial)
    assert report["required_balance_usd"] == pytest.approx(1.25 * 1080 * per_trial)


@pytest.mark.parametrize("flag", ["--remaining-balance-usd", "--reserve-usd", "--conservative-c1-trial-cost-usd"])
def test_every_number_in_the_equation_is_a_required_flag(tmp_path, flag, capsys):
    # Kills the x_main mutants that made a flag optional: a missing input is a usage
    # error, never a None that reaches the comparison.
    argv = [str(tmp_path), "--remaining-balance-usd", "1", "--reserve-usd", "0", "--conservative-c1-trial-cost-usd", "0"]
    i = argv.index(flag)
    del argv[i:i + 2]
    with pytest.raises(SystemExit) as exit_info:
        main(argv)
    assert exit_info.value.code == 2
    assert flag in capsys.readouterr().err


def test_without_out_the_report_is_printed_as_json(tmp_path, capsys):
    run = tmp_path / "run"
    for i, (record, ev) in enumerate(_uniform_grid()):
        trial_dir = run / f"t{i:04d}"
        trial_dir.mkdir(parents=True)
        (trial_dir / "results.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
        (trial_dir / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in ev), encoding="utf-8")
    assert main([str(run), "--remaining-balance-usd", "0", "--reserve-usd", "0",
                 "--conservative-c1-trial-cost-usd", "0"]) == 0
    printed = capsys.readouterr().out
    assert printed.endswith("}\n")
    assert json.loads(printed)["passes"] is False
