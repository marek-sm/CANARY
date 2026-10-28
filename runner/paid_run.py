"""The paid-run gate (decision 0023): no paid model call without the lead's record.

Every non-mock provider, on every runner path, passes ``require_paid_run``
before its first call. It refuses unless all of these hold:

* the run isn't in CI and no provider variable is set in the environment
  (keys come only from the env file the runner reads itself, decision 0010);
* every tool process runs in the sandbox (``tools.sandbox``), which refuses on
  an unsupported platform, a missing sandbox binary, or a root user;
* ``protocol/paid_run_record.json`` exists and validates against its schema;
* the running sandbox is the one the record's mock grid ran under, so the paid
  run uses the same platform and sandbox mode as its preflight;
* the code the paid run executes is the code the record pinned: no git-tracked
  file under the hashed directories has uncommitted changes, and every such
  file's SHA-256 equals the record's.

The one exception is the project lead's live smoke (``make live-smoke``, TASKS.md
paid-run condition), which still runs its read tool in the sandbox but needs no
record. Run paid steps from a clean checkout of the recorded commit, so a later
merge to ``main`` can't invalidate the record or a resume.

Usage (project lead, after the mock grid verifies on the paid-run machine):
  python -m runner.paid_run record MOCK_RUN --delivery PR --sandbox PR --request-to-effect PR
  python -m runner.paid_run check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional

from runner.mock_provider import MockProvider
from runner.mock_slice import EVENTS_FILE, REPO_ROOT, validator
from tools import sandbox

RECORD = REPO_ROOT / "protocol" / "paid_run_record.json"
# Everything a paid grid cell executes or reads: code, the corpus and its fixtures,
# schemas, the grid spec, and the locked dependencies.
HASHED_DIRS = (
    "agent", "channels", "defenses", "oracles", "runner", "tasks", "tools",
    "corpus", "fixtures", "schemas", "protocol/development_grid_spec.json", "uv.lock",
)
RECORD_SCHEMA = "paid_run_record"


class PaidRunRefused(ValueError):
    """A paid call was refused before it was made."""


def is_paid(provider: Any) -> bool:
    return provider is not None and not isinstance(provider, MockProvider)


def _git(*args: str, root: Path = REPO_ROOT) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=True,
        env={"PATH": os.defpath, "LANG": "C.UTF-8"},
    ).stdout


def tracked_files(root: Path = REPO_ROOT) -> list[str]:
    return sorted(p for p in _git("ls-files", "-z", "--", *HASHED_DIRS, root=root).split("\0") if p)


def code_hashes(root: Path = REPO_ROOT) -> dict[str, str]:
    """SHA-256 of every git-tracked file under the hashed directories."""
    return {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in tracked_files(root)}


def dirty_paths(root: Path = REPO_ROOT) -> list[str]:
    status = _git("status", "--porcelain", "--untracked-files=all", "--", *HASHED_DIRS, root=root)
    return [line[3:] for line in status.splitlines() if line.strip()]


def environment_refusal() -> Optional[str]:
    if "CI" in os.environ:
        return "CI is set; paid calls never run in CI"
    ambient = sorted(name for name in os.environ if name.startswith(("ANTHROPIC_", "OPENAI_")))
    if ambient:
        return "unset ambient provider variables first: " + ", ".join(ambient)
    return None


def load_record(path: Optional[Path] = None) -> dict[str, Any]:
    path = path or RECORD
    if not path.is_file():
        raise PaidRunRefused(f"no paid-run record at {path}; paid runs are closed until the project lead records one")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        validator(RECORD_SCHEMA).validate(record)
    except Exception as exc:
        raise PaidRunRefused(f"the paid-run record doesn't validate: {exc}") from exc
    return record


def paid_run_refusal(*, live_smoke: bool = False, record_path: Optional[Path] = None, root: Path = REPO_ROOT) -> Optional[str]:
    """Why a paid call can't run now, or ``None`` when it may."""
    reason = environment_refusal()
    if reason:
        return reason
    try:
        running = sandbox.describe()
    except sandbox.SandboxUnavailable as exc:
        return f"tool sandbox unavailable: {exc}"
    if live_smoke:
        return None
    try:
        record = load_record(record_path)
    except PaidRunRefused as exc:
        return str(exc)
    if record["sandbox"] != running:
        return f"this machine's tool sandbox {running!r} isn't the recorded mock grid's {record['sandbox']!r}"
    dirty = dirty_paths(root)
    if dirty:
        return "uncommitted changes in recorded code: " + ", ".join(dirty[:5])
    current = code_hashes(root)
    if current != record["code_sha256"]:
        changed = sorted(p for p in set(current) | set(record["code_sha256"]) if current.get(p) != record["code_sha256"].get(p))
        return "code differs from the paid-run record: " + ", ".join(changed[:5])
    return None


def require_paid_run(provider: Any, *, live_smoke: bool = False, record_path: Optional[Path] = None) -> None:
    """Refuse a non-mock provider unless every paid-run condition holds."""
    if not is_paid(provider):
        return
    reason = paid_run_refusal(live_smoke=live_smoke, record_path=record_path)
    if reason:
        raise PaidRunRefused(reason)


def _mock_run_sandbox(run_dir: Path) -> str:
    modes = set()
    for events_path in run_dir.glob(f"*/{EVENTS_FILE}"):
        first = json.loads(events_path.read_text(encoding="utf-8").splitlines()[0])
        modes.add(first.get("component_versions", {}).get("tool_sandbox"))
    if len(modes) != 1 or None in modes:
        raise PaidRunRefused(f"the mock grid didn't run under one recorded tool sandbox: {sorted(map(str, modes))}")
    return modes.pop()


def build_record(mock_run: Path, *, delivery: str, sandbox_pr: str, request_to_effect: str,
                 recorded_by: str = "marek-sm", root: Path = REPO_ROOT) -> dict[str, Any]:
    from runner import grid_dev

    summary = grid_dev.verify_grid_run(mock_run, grid_dev.load_spec())
    if not summary["complete"]:
        raise PaidRunRefused("the mock grid isn't complete")
    unfinished = []
    for results_path in mock_run.glob("*/results.jsonl"):
        for line in results_path.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("status") != "completed":
                unfinished.append(results_path.parent.name)
    if unfinished:
        raise PaidRunRefused("mock grid trials didn't complete: " + ", ".join(sorted(unfinished)[:5]))
    mode = _mock_run_sandbox(mock_run)
    if mode != sandbox.describe():
        raise PaidRunRefused("record the paid run on the machine and sandbox the mock grid ran under")
    dirty = dirty_paths(root)
    if dirty:
        raise PaidRunRefused("commit or discard these changes before recording: " + ", ".join(dirty[:5]))
    return {
        "schema_version": "1.0.0",
        "recorded_on": date.today().isoformat(),
        "recorded_by": recorded_by,
        "recorded_commit": _git("rev-parse", "HEAD", root=root).strip(),
        "sandbox": mode,
        "conditions": {
            "tool_result_delivery": {"merged_in": delivery},
            "mock_grid": {
                "experiment_id": summary["experiment_id"],
                "trials": summary["trials_found"],
                "verify_complete": True,
                "tool_sandbox": mode,
            },
            "request_to_effect": {"merged_in": request_to_effect},
            "tool_sandbox": {"merged_in": sandbox_pr},
        },
        "code_sha256": code_hashes(root),
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    rec = sub.add_parser("record", help="write protocol/paid_run_record.json from a verified mock grid")
    rec.add_argument("mock_run", type=Path)
    rec.add_argument("--delivery", required=True)
    rec.add_argument("--sandbox", required=True)
    rec.add_argument("--request-to-effect", required=True)
    sub.add_parser("check", help="say whether a paid run may start here")
    args = parser.parse_args(argv)
    if args.command == "record":
        record = build_record(args.mock_run, delivery=args.delivery, sandbox_pr=args.sandbox,
                              request_to_effect=args.request_to_effect)
        validator(RECORD_SCHEMA).validate(record)
        RECORD.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {RECORD.relative_to(REPO_ROOT)}; commit it, then run paid steps from a clean checkout of it")
        return 0
    reason = paid_run_refusal()
    print(reason or "paid runs may start here")
    return 1 if reason else 0


if __name__ == "__main__":
    sys.exit(main())
