"""Decision 0030 item 8: the Section 13 live-first rehearsal of the excluded demo case.

    python -m runner.rehearsal live --protocol-version V --env-file PATH [--out DIR] [--resume]
    python -m runner.rehearsal verify DIR

`live` runs the fixed demo case (`corpus/demo/demo-001.json`, excluded from every
estimate) on the rehearsed C2 fixture under attack, as ten dry runs across the `K`
stage configurations `protocol/active.json` lists. That is SPEC.md Section 13's
live-first gate: `10 × K` logical trials, the whole rehearsal allowance (Section 9's
table). Each trial keeps `split: development` and carries `analysis_role:
demo_rehearsal`, so it counts in dollars and never against the development ceiling
(decision 0028 item 1; `runner/spend_ledger.py`).

It runs through `execute.run_schedule`, so every trial passes `runner.paid_run`'s gate
before its first call: the paid-run record and the spend cap, and, once
`runner/lead_review.py` is on `main`, the attested lead-side review (decision 0031 item 6).
Before any key is read, it also refuses:

- without `CANARY_PAID_RUN_ACK=1`, a provider's environment, or the paid fallback's decision;
- without a committed, unchanged `protocol/active.json`, or when its `protocol_version`
  isn't `--protocol-version`, its tier is `ENGINEERING` or `STOP`, `K` is 0, a stage
  configuration isn't one the tier retains, or its model isn't the provider's;
- when a dry run would be redone: a fresh run whose trials the ledger already started, a
  resume whose started trial left no durable events in this output, or a trial started twice.
  An interruption after a trial's ledger start but before its first durable event therefore
  refuses every later resume of that run: it fails closed, and finishing the rehearsal then
  needs the project lead's visible decision;
- when the ledger's rehearsal trials plus these would pass `10 × K`;
- when the demo case's C2 attack render is missing or drifted, the output is inside Git,
  `--resume` names no earlier run, or the paid gate refuses this checkout now.

Every later rehearsal is replay-only (decision 0030 item 8). `verify` checks
each stored result against the run's stored schedule and recomputes it from its events,
then reports completeness, the missing trials, and each dry run's recorded outcomes only. Whether a run showed the
intended stage behavior, and so whether 9 of 10 passed, is read against Section 13's
script by the project lead and the demo operator; this module doesn't judge it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Optional

import subprocess

from runner import execute, grid_dev, paid_run, spend_ledger, sweep
from runner.mock_slice import RESULTS_FILE, REPO_ROOT, read_jsonl, validator
from runner.provider_config import load_api_key
from runner.schedule import generate_schedule

ROLE = "demo_rehearsal"
DEMO_CORPUS_ROOT = REPO_ROOT / "corpus" / "demo"
DEMO_BASE = "demo-001"
CHANNEL = "C2"  # Section 13's script: "the rehearsed C2 fixture"
DRY_RUNS = 10  # Section 13: at least 9 of 10 complete dry runs
ACTIVE = REPO_ROOT / "protocol" / "active.json"
RETAINED = ("D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING")
DEFAULT_OUT = REPO_ROOT / "results" / "raw" / "rehearsal"
# The recorded outcome flags verify shows per dry run, in the result schema's own words.
OUTCOME_FIELDS = ("unauthorized_action_requested", "unauthorized_action_dispatched", "unauthorized_action_effect",
                  "proposed_egress", "external_exfiltration", "unauthorized_user_disclosure", "model_violation",
                  "system_compromise")


def _active_committed_refusal() -> Optional[str]:
    """protocol/active.json sets K and so the allowance, and no hashed path covers it, so
    it counts only as a committed, unchanged file of this checkout."""
    try:
        relative = ACTIVE.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
        paid_run._git("ls-files", "--error-unmatch", "--", relative, root=REPO_ROOT)
        if paid_run._git("status", "--porcelain", "--", relative, root=REPO_ROOT).strip():
            return "protocol/active.json has uncommitted changes"
    except ValueError:
        return f"protocol/active.json must be a file in this checkout, not {ACTIVE}"
    except (OSError, subprocess.CalledProcessError):
        return "protocol/active.json isn't committed; the Gate 3 step commits it"
    return None


def _active(protocol_version: Optional[str], model: str) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    try:
        active = json.loads(ACTIVE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "no protocol/active.json: the Gate 3 step writes it, and the rehearsal runs on the frozen release"
    except (OSError, ValueError):
        return None, "protocol/active.json isn't readable JSON"
    if not isinstance(active, dict):
        return None, "protocol/active.json isn't a JSON object"
    reason = _active_committed_refusal()
    if reason:
        return None, reason
    if not protocol_version or active.get("protocol_version") != protocol_version:
        return None, f"--protocol-version {protocol_version!r} isn't protocol/active.json's {active.get('protocol_version')!r}"
    stage = active.get("stage_configurations")
    if not isinstance(stage, list) or not stage:
        return None, "protocol/active.json has no stage configurations (K = 0), so the demo is replay-first (SPEC.md Section 13)"
    if active.get("tier_class") in ("ENGINEERING", "STOP"):
        return None, f"the {active.get('tier_class')} tier is replay-first (SPEC.md Section 13)"
    retained = active.get("configurations")
    if not isinstance(retained, list):
        return None, "protocol/active.json lists no retained configurations"
    if len(set(stage)) != len(stage) or not set(stage) <= set(RETAINED) & set(retained):
        return None, f"protocol/active.json's stage_configurations {stage} aren't distinct retained configurations"
    if "stage_configuration_count" in active and active["stage_configuration_count"] != len(stage):
        return None, "protocol/active.json's stage_configuration_count isn't the length of its stage_configurations"
    frozen_model = (active.get("empirical") or {}).get("model_requested") if isinstance(active.get("empirical"), dict) else None
    if frozen_model != model:
        return None, f"the provider's model {model!r} isn't protocol/active.json's empirical.model_requested {frozen_model!r}"
    return active, None


def rehearsal_spec(active: Mapping[str, Any], model_id: str) -> dict[str, Any]:
    version = str(active["protocol_version"])
    sentinel = "v" + "".join(c if c.isalnum() else "-" for c in version)
    return {
        "experiment_id": "demo-rehearsal", "model_id": model_id, "seed": f"demo-rehearsal|{version}",
        "protocol_sentinel": sentinel, "base_case_ids": [DEMO_BASE], "channels": [CHANNEL],
        "conditions": ["attack"], "configurations": list(active["stage_configurations"]), "repeats": DRY_RUNS,
    }


def allowance(active: Mapping[str, Any]) -> int:
    return DRY_RUNS * len(active["stage_configurations"])


def _started_rehearsal_trials() -> Counter:
    """How many times the ledger started each rehearsal trial afresh."""
    return Counter(line["logical_trial_id"] for line in spend_ledger.read()
                   if line.get("phase") == "started" and line.get("new_trial") and line.get("analysis_role") == ROLE)


def allowance_refusal(spec: Mapping[str, Any], active: Mapping[str, Any], out: Path, *, resume: bool) -> Optional[str]:
    """A dry run is never redone, and the rehearsal never passes 10 × K logical trials."""
    schedule = generate_schedule(spec)
    planned = {trial.logical_trial_id for trial in schedule}
    try:
        counts = _started_rehearsal_trials()
    except spend_ledger.LedgerError as exc:
        return str(exc)
    twice = sorted(trial_id for trial_id, count in counts.items() if count > 1)
    if twice:
        return f"the ledger started {len(twice)} rehearsal trial(s) more than once; a dry run isn't redone"
    started = set(counts)
    if not resume and started & planned:
        return "these dry runs were already started; continue that run with --resume, since a dry run isn't redone"
    if resume:
        # A started trial resumes only from its own durable trace. An empty or recreated
        # events.jsonl would make execute.run_schedule start it afresh, a redone dry run.
        lost = [trial.logical_trial_id for trial in schedule if trial.logical_trial_id in started
                and not execute._durable_events(Path(out) / execute.trial_slug(trial) / execute.EVENTS_FILE,
                                                truncate=False)]
        if lost:
            return (f"{len(lost)} started rehearsal trial(s) have no durable events in {out}; resume only the run "
                    "that started them, with nothing deleted, since a dry run isn't redone")
    limit = allowance(active)
    if len(started | planned) > limit:
        return f"the rehearsal allowance is {limit} logical trials (10 × K); the ledger holds {len(started)} and this adds {len(planned - started)}"
    return None


def live_refusal(spec: Mapping[str, Any], active: Mapping[str, Any], out: Path, *, resume: bool,
                 provider_name: str) -> Optional[str]:
    if os.environ.get("CANARY_PAID_RUN_ACK") != "1":
        return "set CANARY_PAID_RUN_ACK=1 only after the Gate 3 record and the project lead's paid-run record for this commit"
    reason = grid_dev._provider_env_refusal() or grid_dev.fallback_refusal(provider_name)
    if reason:
        return reason
    base = json.loads((DEMO_CORPUS_ROOT / f"{DEMO_BASE}.json").read_text(encoding="utf-8"))
    if base.get("split") != "demo":
        return f"{DEMO_BASE} must be the excluded demo case (split 'demo'), not {base.get('split')!r}"
    if resume and not (Path(out) / execute.SPEC_FILE).is_file():
        return f"--resume needs an earlier rehearsal run in {out}"
    if not resume and Path(out).exists():
        return f"{out} already exists; pass a new --out, or --resume the run it holds"
    return (sweep._renders_refusal(DEMO_CORPUS_ROOT, spec) or allowance_refusal(spec, active, out, resume=resume)
            or execute.raw_evidence_refusal(out)
            or paid_run.paid_run_refusal(new_trials=0))  # rehearsal trials don't count against the ceiling


def run_rehearsal(out: Path, *, protocol_version: str, env_file: Path, provider_name: str = "anthropic",
                  resume: bool = False) -> Path:
    from runner import live_smoke

    config = live_smoke.PROVIDERS[provider_name]
    active, reason = _active(protocol_version, config["model"])
    if reason:
        raise paid_run.PaidRunRefused(reason)
    spec = rehearsal_spec(active, config["model"])
    try:
        generate_schedule(spec)
    except ValueError as exc:
        raise paid_run.PaidRunRefused(f"the rehearsal schedule isn't valid: {exc}") from None
    reason = live_refusal(spec, active, out, resume=resume, provider_name=provider_name)
    if reason:
        raise paid_run.PaidRunRefused(reason)
    config["check"](config["decoding"])
    try:
        key = load_api_key(Path(env_file), config["key"])
    except (OSError, ValueError) as exc:
        raise ValueError(f"{env_file} must hold exactly one {config['key']}= line") from exc
    if not key:
        raise ValueError(f"{config['key']} in {env_file} is empty")
    adapter = config["adapter"](config["module"].build_client(key))
    del key
    return execute.run_schedule(
        out, generate_schedule(spec), corpus_root=DEMO_CORPUS_ROOT, resume=resume, spec=spec, delivery=True,
        provider_factory=lambda _trial, _canaries: adapter, decoding=config["decoding"],
        split="development", protocol_version=protocol_version, analysis_role=ROLE,
    )


def verify_rehearsal(run: Path) -> dict[str, Any]:
    """Each stored result against the run's stored schedule, recomputed from its events,
    then completeness and each dry run's recorded outcome flags; no pass/fail judgment."""
    run = Path(run)
    mode = json.loads((run / execute.MODE_FILE).read_text(encoding="utf-8"))
    if mode != {"delivery": True}:  # execute.run_schedule records no split for development
        raise ValueError(f"{run.name}: not a development run through tool-result delivery")
    schedule = execute.stored_schedule(run)
    pairs = []
    for path in sorted(run.glob(f"*/{RESULTS_FILE}")):
        for record in read_jsonl(path, "result"):
            validator("result").validate(record)
            trial = schedule.get(record["logical_trial_id"])
            if trial is None:
                raise ValueError(f"{record['logical_trial_id']}: not in this run's stored schedule")
            if record.get("analysis_role") != ROLE or record.get("base_case_id") != DEMO_BASE:
                raise ValueError(f"{record['logical_trial_id']}: not a {ROLE} trial of {DEMO_BASE}")
            pairs.append((trial, record))
    found = [trial.logical_trial_id for trial, _ in pairs]
    if len(found) != len(set(found)):
        raise ValueError(f"{run.name}: a trial has more than one stored result")
    execute.check_stored_run(run, pairs, corpus_root=DEMO_CORPUS_ROOT)
    by_id = {trial.logical_trial_id: record for trial, record in pairs}
    # A trial the ledger started afresh more than once was redone, so its dry run never counts.
    twice = sorted(trial_id for trial_id, count in _started_rehearsal_trials().items() if count > 1 and trial_id in schedule)
    runs: dict[int, list[Any]] = {}
    for trial in schedule.values():
        runs.setdefault(trial.run_index, []).append(trial)
    dry_runs, complete = {}, 0
    for index, trials in sorted(runs.items()):
        rows = []
        for trial in sorted(trials, key=lambda t: t.configuration):
            record = by_id.get(trial.logical_trial_id)
            security = (record or {}).get("security") or {}
            rows.append({"configuration": trial.configuration, "status": record["status"] if record else "missing",
                         **{field: security.get(field) for field in OUTCOME_FIELDS},
                         "utility_pass": ((record or {}).get("utility") or {}).get("pass")})
        complete += all(row["status"] == "completed" for row in rows) and not any(
            trial.logical_trial_id in twice for trial in trials)
        dry_runs[str(index)] = rows
    return {
        "trials_expected": len(schedule), "trials_found": len(found),
        "missing": sorted(set(schedule) - set(found)),
        "status_counts": dict(sorted(Counter(record["status"] for _, record in pairs).items())),
        "protocol_versions": sorted({record["protocol_version"] for _, record in pairs}),
        "trials_started_more_than_once": twice, "complete_dry_runs": complete, "dry_runs": dry_runs,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    live = sub.add_parser("live", help="the Section 13 live-first rehearsal, on the project lead's Mac only")
    live.add_argument("--protocol-version", required=True)
    live.add_argument("--env-file", type=Path, required=True)
    live.add_argument("--out", type=Path, default=DEFAULT_OUT)
    live.add_argument("--resume", action="store_true")
    verify = sub.add_parser("verify", help="completeness and recorded outcomes of a rehearsal run")
    verify.add_argument("run", type=Path)
    args = parser.parse_args(argv)
    if args.command == "live":
        try:
            run_rehearsal(args.out, protocol_version=args.protocol_version, env_file=args.env_file, resume=args.resume)
        except paid_run.PaidRunRefused as exc:
            print(f"refusing: {exc}", file=sys.stderr)
            return 1
        print(f"wrote {args.out}; run python -m runner.rehearsal verify {args.out}")
        return 0
    print(json.dumps(verify_rehearsal(args.run), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
