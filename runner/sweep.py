"""W9-T3: the official sweep, through the development grid's own runner path.

The sweep runs a committed schedule spec with ``split="evaluation"`` through
``execute.run_schedule`` and tool-result delivery, on the evaluation corpus, with the
real provider adapter. Nothing here changes how a trial runs or is scored: it is the
paid grid's path with the sweep's labels, so the code the paid-run record hashes is
the code the sweep runs. Every trial still passes ``runner.paid_run``'s gate, the
spend ledger, and the cap before its first call, and evaluation trials don't count
against SPEC.md Section 9's development ceiling. Raw records go only where Git can't
take them (decision 0025 item 5).

``verify`` checks completeness, schema, and that every stored result recomputes from
its events, replays against its stored model responses, and matches its stored
environment. It prints counts of trials and statuses only, never a security or
utility aggregate, so the blinded integrity checks can run it mid-sweep (SPEC.md
Section 9; decision 0028 item 8).

Usage:
  python -m runner.sweep live --spec SPEC.json --protocol-version V [--corpus-root DIR]
      [--out DIR] [--resume] [--analysis-role ROLE] [--env-file PATH] [--provider anthropic|openai]
  python -m runner.sweep verify RUN [--corpus-root DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Optional

from jsonschema import ValidationError

from runner import delivery, execute, grid_dev, paid_run
from runner.mock_slice import RESULTS_FILE, REPO_ROOT, read_jsonl, validator
from runner.provider_config import load_api_key
from runner.schedule import PROTOCOL_SENTINEL, generate_schedule

DEFAULT_CORPUS_ROOT = REPO_ROOT / "corpus" / "evaluation"
DEFAULT_OUT_ROOT = REPO_ROOT / "results" / "raw" / "sweep"


def _bases_refusal(corpus_root: Path, spec: Mapping[str, Any]) -> Optional[str]:
    for base_case_id in spec["base_case_ids"]:
        path = Path(corpus_root) / f"{base_case_id}.json"
        try:
            base = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return f"{corpus_root} holds no readable {base_case_id}.json"
        if base.get("split") != "evaluation" or base.get("base_case_id") != base_case_id:
            return f"{base_case_id} isn't an evaluation base; the sweep runs only the frozen evaluation corpus"
    return None


def _renders_refusal(corpus_root: Path, spec: Mapping[str, Any]) -> Optional[str]:
    """Every scheduled cell's pinned render exists, matches its pin, and round-trips, so
    a missing render refuses the sweep here instead of failing each of its cells."""
    cache: dict[str, Any] = {}
    for base_case_id in spec["base_case_ids"]:
        try:
            base, template = execute._load_base(cache, Path(corpus_root), base_case_id)
        except ValidationError as exc:  # its full text would print the record's payload
            return f"{base_case_id} can't be loaded for the render preflight: {exc.message}"
        except (OSError, ValueError, KeyError) as exc:
            return f"{base_case_id} can't be loaded for the render preflight: {exc}"
        for channel in spec["channels"]:
            for condition in spec["conditions"]:
                try:
                    delivery.pinned_render(base, channel, condition, template)
                except (OSError, ValueError, KeyError) as exc:
                    return f"{base_case_id} has no usable {channel} {condition} render: {exc}"
    return None


def live_refusal(spec: Mapping[str, Any], protocol_version: Optional[str], corpus_root: Path, out: Path) -> Optional[str]:
    """Fail closed before any key is read or any paid call is made."""
    if os.environ.get("CANARY_PAID_RUN_ACK") != "1":
        return "set CANARY_PAID_RUN_ACK=1 only after the Gate 3 record and the project lead's paid-run record for this commit"
    reason = grid_dev._provider_env_refusal()
    if reason:
        return reason
    problem = next(validator("schedule_spec").iter_errors(dict(spec)), None)
    if problem is not None:
        return f"the sweep spec isn't a valid schedule spec: {problem.message}"
    if not protocol_version:
        return "the sweep needs the frozen protocol_version (protocol/active.json)"
    if spec.get("protocol_sentinel", PROTOCOL_SENTINEL) == PROTOCOL_SENTINEL:
        return f"the sweep spec's protocol_sentinel must name the frozen protocol, not {PROTOCOL_SENTINEL!r}"
    reason = _bases_refusal(corpus_root, spec) or _renders_refusal(corpus_root, spec) or execute.raw_evidence_refusal(out)
    if reason:
        return reason
    return paid_run.paid_run_refusal(new_trials=0)  # evaluation trials don't count against the ceiling


def run_sweep(
    out: Path,
    *,
    spec: Mapping[str, Any],
    protocol_version: str,
    corpus_root: Path = DEFAULT_CORPUS_ROOT,
    env_file: Path,
    provider_name: str = "anthropic",
    analysis_role: Optional[str] = None,
    resume: bool = False,
) -> Path:
    reason = grid_dev.fallback_refusal(provider_name) or live_refusal(spec, protocol_version, corpus_root, out)
    if reason:
        raise paid_run.PaidRunRefused(reason)

    from runner import live_smoke

    config = live_smoke.PROVIDERS[provider_name]
    if spec.get("model_id") != config["model"]:
        raise ValueError(f"a {provider_name} sweep runs only {config['model']}, but the spec names {spec.get('model_id')}")
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
        out, generate_schedule(spec), corpus_root=corpus_root, resume=resume, spec=dict(spec), delivery=True,
        provider_factory=lambda _trial, _canaries: adapter, decoding=config["decoding"],
        split="evaluation", protocol_version=protocol_version, analysis_role=analysis_role,
    )


def verify_sweep(run: Path, corpus_root: Path = DEFAULT_CORPUS_ROOT) -> dict[str, Any]:
    """Completeness, schema, and recomputation only; no outcome aggregate."""
    run = Path(run)
    mode = json.loads((run / execute.MODE_FILE).read_text(encoding="utf-8"))
    if mode != {"delivery": True, "split": "evaluation"}:
        raise ValueError(f"{run.name}: not an evaluation run through tool-result delivery")
    schedule = execute.stored_schedule(run)
    pairs, statuses = [], Counter()
    for results in sorted(run.glob(f"*/{RESULTS_FILE}")):
        for record in read_jsonl(results, "result"):
            validator("result").validate(record)
            trial = schedule.get(record["logical_trial_id"])
            if trial is None:
                raise ValueError(f"{record['logical_trial_id']}: not in this run's stored schedule")
            pairs.append((trial, record))
            statuses[record["status"]] += 1
    found = [trial.logical_trial_id for trial, _ in pairs]
    if len(found) != len(set(found)):
        raise ValueError(f"{run.name}: a trial has more than one stored result")
    execute.check_stored_run(run, pairs, corpus_root=corpus_root)
    missing = len(set(schedule) - set(found))
    return {"trials_expected": len(schedule), "trials_found": len(found), "missing": missing,
            "status_counts": dict(sorted(statuses.items())), "protocol_versions": sorted({r["protocol_version"] for _, r in pairs}),
            # A sweep the run-wide stop rule stopped isn't complete until a resume runs it through (decision 0029).
            "run_wide_stops": grid_dev.run_wide_stops(run),
            "complete": missing == 0 and not grid_dev.stopped_unresolved(run)}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    live = sub.add_parser("live", help="run the sweep on a real provider (hand only; paid-run gate applies)")
    live.add_argument("--spec", type=Path, required=True)
    live.add_argument("--protocol-version", required=True)
    live.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS_ROOT)
    live.add_argument("--out", type=Path, default=None)
    live.add_argument("--resume", action="store_true")
    live.add_argument("--analysis-role", default=None)
    live.add_argument("--env-file", type=Path, default=REPO_ROOT / ".env")
    live.add_argument("--provider", choices=("anthropic", "openai"), default="anthropic")
    check = sub.add_parser("verify", help="completeness, schema, and recomputation of a sweep run")
    check.add_argument("run", type=Path)
    check.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS_ROOT)
    args = parser.parse_args(argv)
    try:
        if args.command == "live":
            spec = json.loads(args.spec.read_text(encoding="utf-8"))
            out = args.out or DEFAULT_OUT_ROOT / str(spec.get("experiment_id"))
            reason = grid_dev._existing_run_refusal(out, args.resume)
            if reason:
                print(f"refusing: {reason}", file=sys.stderr)
                return 2
            run_sweep(out, spec=spec, protocol_version=args.protocol_version, corpus_root=args.corpus_root,
                      env_file=args.env_file, provider_name=args.provider, analysis_role=args.analysis_role,
                      resume=args.resume)
            print(f"sweep run directory: {out}")
            return 0
        print(json.dumps(verify_sweep(args.run, args.corpus_root), indent=2, sort_keys=True))
        return 0
    except paid_run.PaidRunRefused as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 2
    except execute.RunWideFailure as exc:
        print(f"{exc}: rerun this command with --resume", file=sys.stderr)
        return 3
    except grid_dev.REFUSALS as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
