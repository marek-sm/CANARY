"""Gate 3 step driver at F20 (decision 0039 item 5; run on November 15 under decision 0040).
It calls committed code only, with the input values decision 0039 item 5 fixed. Commit it
after decision 0040 merges, then run it with the project venv's python:
    python docs/evidence/gate3-2026-11-15/gate3_step.py --code-commit "$(git rev-parse HEAD)" --out protocol
It refuses unless --code-commit is HEAD, no tracked file differs from HEAD, and it runs in a
virtual environment. It writes protocol/active.json, protocol/sweep_spec.json, and
protocol/c1_spec.json only after checking the manifest against the recomputed hashes, both
schedule refusals, and the trial counts (1,080 + 12 = 1,092)."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from analysis import active_protocol, gate3_hashes  # noqa: E402
from runner import c1_trial, sweep  # noqa: E402
from runner.schedule import generate_schedule  # noqa: E402


def refuse(message):
    sys.exit(f"gate3_step: refused: {message}")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


p = argparse.ArgumentParser()
p.add_argument("--code-commit", required=True)
p.add_argument("--out", type=Path, required=True)
a = p.parse_args()

if sys.prefix == sys.base_prefix:
    refuse("not running in the project's virtual environment")
if a.code_commit != git("rev-parse", "HEAD"):
    refuse(f"--code-commit {a.code_commit} isn't HEAD {git('rev-parse', 'HEAD')}")
if git("status", "--porcelain", "--untracked-files=no"):
    refuse("a tracked file differs from HEAD")

corpus, defenses, tasks = load("corpus/freeze.json"), load("defenses/freeze.json"), load("tasks/freeze.json")
floor = load("docs/evidence/gate2-2026-11-10/floor-count.json")
computed = gate3_hashes.compute(ROOT)  # refuses an unclean checkout of a covered path
SENTINEL = "canary-2026-v1"
ran = floor["ran_on"]
if floor["ran_on_consistent"] is not True or not all(len(v) == 1 for v in ran.values()):
    refuse("the development grid didn't run on one model, endpoint, and effort")
manifest = active_protocol.generate(
    "F20", base_case_ids=list(corpus["base_case_ids"]),
    empirical={
        "experiment_id": "canary-2026-sweep", "model_requested": ran["model_requested"][0],
        "model_resolved": ran["model_resolved"][0], "model_endpoint": ran["endpoint"][0],
        "reasoning_effort": ran["effort"][0], "defense_hash": defenses["defense_hash"],
        "corpus_hash": corpus["corpus_hash"], "analysis_hash": computed["analysis_hash"],
        "schedule_seed": "CANARY-2026-sweep-20261114", "schedule_concurrency": 1,
        "development_floor": floor, "null_reasons": {}},
    protocol_id="CANARY-2026-F20", protocol_version="1.0.0", active_contributor_count=6,
    selection_reason_category="headcount ceiling",
    accountable_roles=["project lead: the lead inputs, the estimand report module, the Gate 3 step, and the sweep's and C1 run's execution",
                       "the owner of each W8–W13 slice in TASKS.md"],
    data_cutoff="2026-11-22", budget_cap_usd=10.0,
    common_hashes={**tasks["common_hashes"], "code_commit": a.code_commit, "container_digest": None},
    engineering_fallback=computed["engineering_fallback"], host_environment=computed["host_environment"])
problems = gate3_hashes.check(manifest, computed)
if problems:
    refuse(f"gate3_hashes.check: {problems}")

e, arithmetic = manifest["empirical"], manifest["tier_arithmetic"]
base = {"experiment_id": e["experiment_id"], "protocol_sentinel": SENTINEL, "model_id": e["model_requested"],
        "seed": e["schedule_seed"]}
sweep_spec = {**base, "base_case_ids": manifest["base_case_ids"], "channels": manifest["channels"],
              "conditions": ["attack", "clean"], "configurations": manifest["configurations"],
              "repeats": len(manifest["run_indices"])}
c1_spec = {**base, "base_case_ids": manifest["c1_controls"], "channels": ["C1"], "conditions": ["attack"],
           "configurations": ["D0_BASELINE"], "repeats": arithmetic["c1_repeats"]}
err = next(sweep.validator("schedule_spec").iter_errors(sweep_spec), None)
if err is not None:
    refuse(f"sweep_spec.json doesn't validate: {err.message}")
refusals = sweep._schedule_refusal(sweep_spec, manifest), c1_trial.schedule_refusal(c1_spec, manifest)
if refusals != (None, None):
    refuse(f"schedule refusals {refusals}")
n_sweep, n_c1 = len(generate_schedule(sweep_spec)), len(generate_schedule(c1_spec))
if (n_sweep, n_c1) != (arithmetic["primary_trials"], arithmetic["c1_trials"]):
    refuse(f"schedules have {n_sweep} + {n_c1} trials; tier_arithmetic says {arithmetic}")
if not n_sweep + n_c1 == manifest["official_trial_count"] == 1092:
    refuse(f"{n_sweep} + {n_c1} isn't official_trial_count {manifest['official_trial_count']} or 1,092")

a.out.mkdir(parents=True, exist_ok=True)
(a.out / "active.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
for name, spec in (("sweep_spec.json", sweep_spec), ("c1_spec.json", c1_spec)):
    (a.out / name).write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("active.json written:", manifest["tier"], manifest["official_trial_count"], "official trials")
print("schedule refusals:", refusals)
print("schedules:", n_sweep, "sweep trials +", n_c1, "C1 trials =", n_sweep + n_c1)
print("sweep_spec.json and c1_spec.json written")
