"""Gate 2 budget equation (SPEC.md Section 9, Trial budget).

Reads one live development-grid run (``experiment_id`` grid-dev, non-mock
provider) and evaluates whether the funded balance supports the official sweep
at one Section 12 row, ``F20`` unless told otherwise:

  remaining_funded_balance_at_gate_2
    >= 1.25 × [Σ_s(planned_primary_trials_s × max_observed_dev_trial_cost_s)
               + planned_C1_trials × conservative_C1_trial_cost]
       + unspent_development_rehearsal_and_stage_reserve

Trial cost is taken from each result's summed ``usage``; when that total is
unknown, from the trial's ``provider_attempt`` events. Costs use decision 0010
Haiku list pricing, with a request over 100,000 input tokens at its higher rates.
The reserve, the C1 cost, and thin strata come from the frozen price bound in
``analysis/price_bound.py`` (decisions 0025 and 0026), and the development
trials already used from ``runner.spend_ledger``'s ledger, never a typed number.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from jsonschema import ValidationError

from analysis.floor_count import CHANNELS, CONFIGURATIONS, DEVELOPMENT_BASES, load_run
from analysis.price_bound import (
    INPUT_USD_PER_TOKEN,
    LONG_INPUT_USD_PER_TOKEN,
    LONG_OUTPUT_USD_PER_TOKEN,
    LONG_PROMPT_TOKENS,
    OUTPUT_USD_PER_TOKEN,
    PRICE_BOUND_USD,
)
from runner import paid_run, spend_ledger
from runner.mock_provider import MOCK_MODEL_ID

# SPEC.md Section 12's rows. A trial's stratum is channel x condition x configuration.
ALL_CONFIGURATIONS = tuple(CONFIGURATIONS)
TIERS = {
    "F20": {"channels": ("C2", "C3", "C4"), "configurations": 3, "primary_per_stratum": 60, "c1_trials": 12},
    "R15": {"channels": ("C2", "C3", "C4"), "configurations": 3, "primary_per_stratum": 45, "c1_trials": 12},
    "M10-ALL": {"channels": ("C2", "C3"), "configurations": 3, "primary_per_stratum": 30, "c1_trials": 9},
    "M10-ONE": {"channels": ("C2", "C3"), "configurations": 2, "primary_per_stratum": 30, "c1_trials": 9},
    "M10-BASE": {"channels": ("C2", "C3"), "configurations": 1, "primary_per_stratum": 30, "c1_trials": 9},
    "L8-ONE": {"channels": ("C2",), "configurations": 2, "primary_per_stratum": 24, "c1_trials": 6},
    "L8-BASE": {"channels": ("C2",), "configurations": 1, "primary_per_stratum": 24, "c1_trials": 6},
    "R6-ONE": {"channels": ("C2",), "configurations": 2, "primary_per_stratum": 18, "c1_trials": 6},
    "R6-BASE": {"channels": ("C2",), "configurations": 1, "primary_per_stratum": 18, "c1_trials": 6},
}
DEVELOPMENT_CEILING = 120
MIN_STRATUM_OBSERVATIONS = 3


def _tier_configurations(tier: str, defense: Optional[str]) -> tuple[str, ...]:
    count = TIERS[tier]["configurations"]
    if count != 2 and defense is not None:
        raise ValueError(f"{tier} has no retained defense to choose")
    if count == len(ALL_CONFIGURATIONS):
        return ALL_CONFIGURATIONS
    if count == 1:
        return ("D0_BASELINE",)
    if defense not in ("D1_POLICY_GATE", "D2_DATAMARKING"):
        raise ValueError(f"{tier} needs its retained defense")
    return ("D0_BASELINE", defense)


def _count(value: Any) -> Optional[int]:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _usage_from_record(
    record: Mapping[str, Any], events: Optional[Sequence[Mapping[str, Any]]] = None
) -> tuple[int, int]:
    """The trial's billed tokens. A model response's usage is never priced at zero.

    The result's summed ``usage`` is null when any attempt's count is unknown.
    The trial's events then decide: an attempt that returned model content must
    carry its usage, and one that failed without content counts nothing (the 25%
    contingency covers bounded retries, SPEC.md Section 9).
    """
    usage = record.get("usage") or {}
    inp, out = _count(usage.get("input_tokens")), _count(usage.get("output_tokens"))
    if inp is not None and out is not None:
        return inp, out
    if events is None:
        raise ValueError(f"{record.get('logical_trial_id')}: usage unknown; pass the trial's events")
    inp = out = 0
    for event in events:
        if event.get("event_type") != "provider_attempt":
            continue
        payload = event["payload"]
        attempt = payload.get("usage") or {}
        attempt_in, attempt_out = _count(attempt.get("input_tokens")), _count(attempt.get("output_tokens"))
        if attempt_in is not None and attempt_out is not None:
            inp, out = inp + attempt_in, out + attempt_out
        elif payload.get("outcome") == "model_response":
            raise ValueError(f"{event.get('attempt_id')}: model response without recorded usage")
    return inp, out


def _long_prompt_surcharge(total_input: int, events: Sequence[Mapping[str, Any]]) -> float:
    """What a request over 100,000 input tokens adds to the lower rates (decision 0010).

    A trial that could hold such a request must show its attempts, or the request
    size is unknown and pricing it low would hide a cost.
    """
    extra, counted, long_request = 0.0, 0, False
    for event in events:
        if event.get("event_type") != "provider_attempt":
            continue
        attempt = event["payload"].get("usage") or {}
        attempt_in, attempt_out = _count(attempt.get("input_tokens")), _count(attempt.get("output_tokens"))
        if attempt_in is None or attempt_out is None:
            continue
        counted += attempt_in
        if attempt_in <= LONG_PROMPT_TOKENS:
            continue
        long_request = True
        extra += attempt_in * (LONG_INPUT_USD_PER_TOKEN - INPUT_USD_PER_TOKEN)
        extra += attempt_out * (LONG_OUTPUT_USD_PER_TOKEN - OUTPUT_USD_PER_TOKEN)
    if (long_request or total_input > LONG_PROMPT_TOKENS) and counted != total_input:
        raise ValueError(f"{total_input} input tokens with attempts summing to {counted}: "
                         "can't tell whether a request passed the 100,000-token rate")
    return extra


def trial_cost_usd(
    record: Mapping[str, Any],
    events: Optional[Sequence[Mapping[str, Any]]] = None,
) -> float:
    inp, out = _usage_from_record(record, events)
    return inp * INPUT_USD_PER_TOKEN + out * OUTPUT_USD_PER_TOKEN + _long_prompt_surcharge(inp, events or ())


def _stratum(record: Mapping[str, Any]) -> tuple[str, str, str]:
    return (record["channel"], record["condition"], record["configuration"])


def check_complete_grid(
    trials: Sequence[tuple[Mapping[str, Any], Sequence[Mapping[str, Any]]]],
    configurations: Sequence[str],
) -> None:
    """Section 9 evaluates the equation after the complete development grid, so a
    missing cell can't lower the required balance and a repeated one can't count twice."""
    expected = {(base, channel, condition, configuration) for base in DEVELOPMENT_BASES for channel in CHANNELS
                for condition in ("attack", "clean") for configuration in configurations}
    seen: dict[tuple[Any, ...], int] = defaultdict(int)
    for record, _ in trials:
        key = (record["base_case_id"], record["channel"], record["condition"], record["configuration"])
        if (key[0] not in DEVELOPMENT_BASES or key[1] not in CHANNELS or key[2] not in ("attack", "clean")
                or key[3] not in CONFIGURATIONS):
            raise ValueError(f"a record outside the development grid: {key}")  # it could lower a stratum's maximum
        if key in expected:
            seen[key] += 1
    missing = sorted(expected - set(seen))
    if missing:
        raise ValueError(f"the grid is missing {len(missing)} of {len(expected)} cells, first {missing[0]}")
    repeated = sorted(key for key, count in seen.items() if count > 1)
    if repeated:
        raise ValueError(f"the grid has {len(repeated)} repeated cells, first {repeated[0]}")


def evaluate_budget(
    trials: Sequence[tuple[Mapping[str, Any], Sequence[Mapping[str, Any]]]],
    *,
    remaining_balance_usd: float,
    development_trials_used: int,
    tier: str = "F20",
    defense: Optional[str] = None,
    c1_pilot_cost_usd: Optional[float] = None,
    price_bound_usd: float = PRICE_BOUND_USD,
    contingency: float = 1.25,
) -> dict[str, Any]:
    if tier not in TIERS:
        raise ValueError(f"unknown tier: {tier}")
    if not 0 <= development_trials_used <= DEVELOPMENT_CEILING:
        raise ValueError(f"development trials must be 0-{DEVELOPMENT_CEILING}; got {development_trials_used}")
    row, configurations = TIERS[tier], _tier_configurations(tier, defense)
    if not trials:
        raise ValueError("no grid trials to evaluate")
    experiment_ids = {r["experiment_id"] for r, _ in trials}
    if len(experiment_ids) != 1:
        raise ValueError(f"expected one experiment_id; got {sorted(experiment_ids)}")
    for record, _ in trials:
        meta = record["run_metadata"]
        if MOCK_MODEL_ID in {meta.get("model_requested"), meta.get("model_resolved")}:
            raise ValueError("mock-provider grid records cannot evaluate the live budget equation")

    costs_by_stratum: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    valid_by_stratum: dict[tuple[str, str, str], int] = defaultdict(int)
    all_costs: list[float] = []
    for record, events in trials:
        cost = trial_cost_usd(record, events)
        all_costs.append(cost)
        costs_by_stratum[_stratum(record)].append(cost)
        # Section 9's thin-stratum rule counts valid observations, and an
        # infrastructure failure isn't one. Its recorded spend still counts as cost.
        if record["status"] == "completed":
            valid_by_stratum[_stratum(record)] += 1

    global_max = max(all_costs) if all_costs else 0.0
    stratum_max: dict[str, float] = {}
    for channel in row["channels"]:
        for condition in ("attack", "clean"):
            for configuration in configurations:
                stratum = (channel, condition, configuration)
                if valid_by_stratum[stratum] >= MIN_STRATUM_OBSERVATIONS:
                    bound = max(costs_by_stratum[stratum])
                else:
                    bound = max(global_max, price_bound_usd)
                stratum_max[f"{channel}/{condition}/{configuration}"] = bound

    conservative_c1 = max(c1_pilot_cost_usd or 0.0, global_max, price_bound_usd)
    reserve_trials = {
        "development": DEVELOPMENT_CEILING - development_trials_used,
        "rehearsal": 10 * len(configurations),
        "stage": len(configurations),
    }
    reserve_usd = sum(reserve_trials.values()) * price_bound_usd
    primary_sum = sum(row["primary_per_stratum"] * bound for bound in stratum_max.values())
    rhs = contingency * (primary_sum + row["c1_trials"] * conservative_c1) + reserve_usd
    passes = remaining_balance_usd >= rhs

    return {
        "experiment_id": next(iter(experiment_ids)),
        "remaining_funded_balance_at_gate_2_usd": remaining_balance_usd,
        "unspent_development_rehearsal_and_stage_reserve_usd": reserve_usd,
        "reserve_trials": reserve_trials,
        "tier": tier,
        "price_bound_usd": price_bound_usd,
        "conservative_C1_trial_cost_usd": conservative_c1,
        "planned_primary_trials_per_stratum": row["primary_per_stratum"],
        "planned_C1_trials": row["c1_trials"],
        "contingency_factor": contingency,
        "max_observed_dev_trial_cost_by_stratum_usd": stratum_max,
        "global_max_observed_dev_trial_cost_usd": global_max,
        "required_balance_usd": rhs,
        "passes": passes,
    }


def _price_bound_used() -> float:
    """The frozen bound, read at call time so the report names the bound this evaluation took.
    ``check_code_matches_run`` leaves the bound's module out, so a raised bound can be
    re-evaluated, and two evaluations of one grid can differ here. There is no typed fallback."""
    try:
        module = importlib.import_module("analysis.price_bound")
    except ImportError as exc:
        raise ValueError("no analysis/price_bound.py here; the reserve and C1 cost come only from the frozen bound") from exc
    return module.PRICE_BOUND_USD


def development_trials_used() -> int:
    """SPEC.md Section 9's development trials so far, the October 10 check's included, counted
    from the spend ledger outside every checkout, so a typed number can't lower the reserve.
    A missing or corrupt ledger refuses (``LedgerError`` is a ``ValueError``)."""
    return spend_ledger.totals(spend_ledger.read())[1]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_dir", type=Path, help="development grid run directory")
    parser.add_argument("--remaining-balance-usd", type=float, required=True)
    # The reserve and C1 cost come from the frozen bound, and the development trials used from
    # the spend ledger, never a typed number (decisions 0026 and 0028).
    parser.add_argument("--tier", choices=sorted(TIERS), default="F20")
    parser.add_argument("--defense", choices=("D1_POLICY_GATE", "D2_DATAMARKING"), default=None)
    parser.add_argument("--c1-pilot-cost-usd", type=float, default=None)
    parser.add_argument("--out", type=Path, help="write JSON report here")
    args = parser.parse_args(argv)
    try:
        code_check = paid_run.check_code_matches_run(args.run_dir)
        print(f"gate2-budget: {code_check}", file=sys.stderr)
        trials = load_run(args.run_dir)
        check_complete_grid(trials, _tier_configurations(args.tier, args.defense))
        bound = _price_bound_used()
        report = json.dumps(
            {
                **evaluate_budget(
                    trials,
                    remaining_balance_usd=args.remaining_balance_usd,
                    development_trials_used=development_trials_used(),
                    tier=args.tier,
                    defense=args.defense,
                    c1_pilot_cost_usd=args.c1_pilot_cost_usd,
                    price_bound_usd=bound,
                ),
                "price_bound_source": "analysis/price_bound.py",
                "development_trials_source": "runner.spend_ledger",
                "code_check": code_check,
            },
            indent=2,
            sort_keys=True,
        ) + "\n"
    except (ValueError, OSError, ValidationError) as error:
        print(f"gate2-budget: {error}", file=sys.stderr)
        return 1
    if args.out:
        args.out.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
