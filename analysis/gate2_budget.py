"""Gate 2 budget equation (SPEC.md Section 9, Trial budget).

Reads one live development-grid run (``experiment_id`` grid-dev, non-mock
provider) and evaluates whether the funded balance supports the official sweep
at the provisional F20 geometry:

  remaining_funded_balance_at_gate_2
    >= 1.25 × [Σ_s(planned_primary_trials_s × max_observed_dev_trial_cost_s)
               + planned_C1_trials × conservative_C1_trial_cost]
       + unspent_development_rehearsal_and_stage_reserve

Trial cost is taken from each result's ``usage`` block when present; otherwise
from summing ``attempts[].usage``. Costs use decision 0010 Haiku list pricing
unless ``--price-table`` overrides them.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from analysis.floor_count import CONFIGURATIONS, load_run
from runner.mock_provider import MOCK_MODEL_ID

# F20 primary indirect: 20 × 3 × 2 × 3 × 3 = 1080; 18 strata (channel × condition × configuration).
STRATA = [(c, k, cfg) for c in ("C2", "C3", "C4") for k in ("attack", "clean") for cfg in CONFIGURATIONS]
PLANNED_PRIMARY_PER_STRATUM_F20 = 60
PLANNED_C1_TRIALS_F20 = 12
MIN_STRATUM_OBSERVATIONS = 3

# decision 0010 list price (USD per token) for claude-haiku-5-5 prompts ≤ 100k tokens.
DEFAULT_INPUT_USD_PER_TOKEN = 0.10 / 1_000_000
DEFAULT_OUTPUT_USD_PER_TOKEN = 0.50 / 1_000_000


def _usage_from_record(record: Mapping[str, Any]) -> tuple[int, int]:
    usage = record.get("usage")
    if isinstance(usage, Mapping):
        return int(usage.get("input_tokens") or 0), int(usage.get("output_tokens") or 0)
    inp = out = 0
    for attempt in record.get("attempts") or []:
        attempt_usage = attempt.get("usage") or {}
        inp += int(attempt_usage.get("input_tokens") or 0)
        out += int(attempt_usage.get("output_tokens") or 0)
    return inp, out


def trial_cost_usd(
    record: Mapping[str, Any],
    *,
    input_rate: float = DEFAULT_INPUT_USD_PER_TOKEN,
    output_rate: float = DEFAULT_OUTPUT_USD_PER_TOKEN,
) -> float:
    inp, out = _usage_from_record(record)
    return inp * input_rate + out * output_rate


def _stratum(record: Mapping[str, Any]) -> tuple[str, str, str]:
    return (record["channel"], record["condition"], record["configuration"])


def evaluate_budget(
    trials: Sequence[tuple[Mapping[str, Any], Sequence[Mapping[str, Any]]]],
    *,
    remaining_balance_usd: float,
    reserve_usd: float,
    conservative_c1_trial_cost_usd: float,
    planned_primary_per_stratum: int = PLANNED_PRIMARY_PER_STRATUM_F20,
    planned_c1_trials: int = PLANNED_C1_TRIALS_F20,
    contingency: float = 1.25,
) -> dict[str, Any]:
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
    all_costs: list[float] = []
    for record, _events in trials:
        cost = trial_cost_usd(record)
        all_costs.append(cost)
        costs_by_stratum[_stratum(record)].append(cost)

    global_max = max(all_costs) if all_costs else 0.0
    stratum_max: dict[str, float] = {}
    for channel, condition, configuration in STRATA:
        observed = costs_by_stratum.get((channel, condition, configuration), [])
        if len(observed) >= MIN_STRATUM_OBSERVATIONS:
            bound = max(observed)
        else:
            bound = global_max
        stratum_max[f"{channel}/{condition}/{configuration}"] = bound

    primary_sum = sum(planned_primary_per_stratum * bound for bound in stratum_max.values())
    rhs = contingency * (primary_sum + planned_c1_trials * conservative_c1_trial_cost_usd) + reserve_usd
    passes = remaining_balance_usd >= rhs

    return {
        "experiment_id": next(iter(experiment_ids)),
        "remaining_funded_balance_at_gate_2_usd": remaining_balance_usd,
        "unspent_development_rehearsal_and_stage_reserve_usd": reserve_usd,
        "conservative_C1_trial_cost_usd": conservative_c1_trial_cost_usd,
        "planned_primary_trials_per_stratum": planned_primary_per_stratum,
        "planned_C1_trials": planned_c1_trials,
        "contingency_factor": contingency,
        "max_observed_dev_trial_cost_by_stratum_usd": stratum_max,
        "global_max_observed_dev_trial_cost_usd": global_max,
        "required_balance_usd": rhs,
        "passes": passes,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_dir", type=Path, help="development grid run directory")
    parser.add_argument("--remaining-balance-usd", type=float, required=True)
    parser.add_argument("--reserve-usd", type=float, default=0.0)
    parser.add_argument("--conservative-c1-trial-cost-usd", type=float, required=True)
    parser.add_argument("--out", type=Path, help="write JSON report here")
    args = parser.parse_args(argv)
    try:
        report = json.dumps(
            evaluate_budget(
                load_run(args.run_dir),
                remaining_balance_usd=args.remaining_balance_usd,
                reserve_usd=args.reserve_usd,
                conservative_c1_trial_cost_usd=args.conservative_c1_trial_cost_usd,
            ),
            indent=2,
            sort_keys=True,
        ) + "\n"
    except (ValueError, OSError) as error:
        print(f"gate2-budget: {error}", file=sys.stderr)
        return 1
    if args.out:
        args.out.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
