"""The SHA-256 manifest of a run's raw results and events files (decision 0025 item 5).

Raw records stay outside Git. What merges under ``docs/evidence/`` is this manifest:
relative paths and hashes, never a provider body, canary, or host path, so a reviewer
with access to the raw storage can check the files are the ones the summary came
from. It names each run's experiments and models, says whether the run was the mock
(mock runs never count), and repeats the code commits and paid-run record commit the
run itself recorded, so writing it later from another checkout changes nothing. Once
published, it is what anchors the raw files: nothing earlier can tell an edit made
consistently across a whole run directory. It makes no provider call and reads no key.

Usage:
  python -m runner.raw_manifest RUN [RUN ...] [--out FILE]
  python -m runner.raw_manifest RUN [RUN ...] --check FILE
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Optional, Sequence

from jsonschema import ValidationError

from runner import paid_run
from runner.mock_provider import MOCK_MODEL_ID
from runner.mock_slice import EVENTS_FILE, RESULTS_FILE, read_jsonl
from tasks import registry

VERSION = "raw-results-manifest-v0.1.0"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _files(run: Path) -> dict[str, str]:
    """Every raw results and events file one level down, by path relative to the run."""
    return {path.relative_to(run).as_posix(): _digest(path)
            for name in (RESULTS_FILE, EVENTS_FILE) for path in sorted(run.glob(f"*/{name}"))}


def _recorded_code(run: Path) -> dict[str, list[str]]:
    """What the run's own invocations recorded, each value once, oldest first."""
    path = run / paid_run.PROVENANCE_FILE
    lines = registry.jsonl_records(path.read_text(encoding="utf-8")) if path.is_file() else []
    return {f"{key}s": list(dict.fromkeys(line[key] for line in lines if line.get(key) is not None))
            for key in ("code_commit", "code_digest", "paid_run_record_commit")}


def build(runs: Sequence[Path]) -> dict[str, Any]:
    """The manifest over ``runs``; a trial directory missing either file is refused."""
    entries: dict[str, Any] = {}
    for run in map(Path, runs):
        if run.name in entries:
            raise ValueError(f"two runs share the same name: {run.name}")
        results = sorted(run.glob(f"*/{RESULTS_FILE}"))
        if not results:
            raise ValueError(f"{run}: no results files")
        unpaired = sorted({p.parent.name for p in results} ^ {p.parent.name for p in run.glob(f"*/{EVENTS_FILE}")})
        if unpaired:
            raise ValueError(f"{run}: trial directories without both files: {unpaired[:3]}")
        records = [record for path in results for record in read_jsonl(path, "result")]
        models = {r["run_metadata"][key] for r in records for key in ("model_requested", "model_resolved")} - {None}
        entries[run.name] = {
            "experiment_ids": sorted({r["experiment_id"] for r in records}),
            "models": sorted(models),
            "mock": MOCK_MODEL_ID in models,
            "trials": len(records),
            **_recorded_code(run),
            "files": _files(run),
        }
    return {"version": VERSION, "runs": entries}


def check(manifest: dict[str, Any], runs: Sequence[Path]) -> list[str]:
    """Each file that differs from ``manifest``, is missing, or was added; empty when all match."""
    problems = []
    runs = list(map(Path, runs))
    if sorted(run.name for run in runs) != sorted(manifest["runs"]):
        problems.append(f"the manifest names runs {sorted(manifest['runs'])}")
    for run in runs:
        recorded = manifest["runs"].get(run.name, {}).get("files", {})
        current = _files(run)
        for path in sorted(set(recorded) | set(current)):
            if recorded.get(path) != current.get(path):
                problems.append(f"{run.name}/{path}")
    return problems


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("runs", type=Path, nargs="+", help="run directories holding per-trial results and events files")
    parser.add_argument("--out", type=Path, help="write the manifest here instead of printing it")
    parser.add_argument("--check", type=Path, help="compare the runs with this manifest instead of writing one")
    args = parser.parse_args(argv)
    try:
        if args.check:
            problems = check(json.loads(args.check.read_text(encoding="utf-8")), args.runs)
            if problems:
                print("raw-manifest: differs: " + ", ".join(problems[:10]), file=sys.stderr)
                return 1
            print(f"ok: {len(args.runs)} run(s) match {args.check}")
            return 0
        text = json.dumps(build(args.runs), indent=2, sort_keys=True) + "\n"
    except (OSError, ValueError, ValidationError) as exc:
        print(f"raw-manifest: {exc}", file=sys.stderr)
        return 1
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
