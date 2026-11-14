"""The Gate 3 step's computed hashes (decision 0038 items 4 and 5).

    python -m analysis.gate3_hashes                                 # print the values the step passes to generate(...)
    python -m analysis.gate3_hashes --check protocol/active.json    # fail on any mismatch or null fallback hash

`analysis_hash` is the SHA-256 of a UTF-8 text with one line `<path> <lowercase sha256>`
for every git-tracked file under `analysis/` except `analysis/sanitizer.py`, plus
`paper/estimand_manifest.json`; the lines are sorted by path bytes and joined with LF, with
no trailing newline. The sanitizer is excluded because it crosses Gate 3 to `W9-T3`.

The engineering fallback's values: `validation_id` from `protocol/engineering_validation_plan.json`,
`source_ledger_hash` copied from `corpus/freeze.json`, and `validation_plan_hash`,
`validation_schema_hash`, and `report_generator_hash`, the SHA-256 of
`protocol/engineering_validation_plan.json`, `schemas/engineering_validation.schema.json`,
and `analysis/engineering_report.py`.

Every value is computed from a clean checkout's working-tree bytes: a covered file that
differs from the commit, or an untracked file under `analysis/`, is refused, because a
clean checkout has neither.

`--check` recomputes every value and compares it with `protocol/active.json`. Every
fallback field must be non-null and equal at every tier but `STOP`, which carries no
fallback and isn't checked here. `analysis_hash` must equal the recomputed value at an
empirical tier; at `ENGINEERING` it must be null with its own reason in
`empirical.null_reasons`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Optional

ROOT = Path(__file__).resolve().parents[1]
SANITIZER = "analysis/sanitizer.py"
MANIFEST = "paper/estimand_manifest.json"
CORPUS_FREEZE = "corpus/freeze.json"
VALIDATION_PLAN = "protocol/engineering_validation_plan.json"
VALIDATION_SCHEMA = "schemas/engineering_validation.schema.json"
REPORT_GENERATOR = "analysis/engineering_report.py"
FALLBACK_FIELDS = ("validation_id", "source_ledger_hash", "validation_plan_hash",
                   "validation_schema_hash", "report_generator_hash")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analysis_paths(root: Path = ROOT) -> list[str]:
    """The files `analysis_hash` covers, sorted by path bytes."""
    tracked = [path for path in _git(root, "ls-files", "-z", "--", "analysis").split("\0") if path]
    if MANIFEST not in _git(root, "ls-files", "-z", "--", MANIFEST).split("\0"):
        raise ValueError(f"{MANIFEST} isn't tracked")
    return sorted({*(path for path in tracked if path != SANITIZER), MANIFEST}, key=lambda path: path.encode("utf-8"))


def _clean_refusal(root: Path, paths: list[str]) -> Optional[str]:
    changed = [path for path in _git(root, "diff", "--name-only", "-z", "HEAD", "--", *paths).split("\0") if path]
    if changed:
        return f"not a clean checkout: {', '.join(sorted(changed))} differ from the commit"
    untracked = [path for path in _git(root, "ls-files", "-z", "--others", "--exclude-standard", "--", "analysis").split("\0")
                 if path]
    if untracked:
        return f"not a clean checkout: untracked {', '.join(sorted(untracked))} under analysis/"
    return None


def analysis_hash(root: Path = ROOT) -> str:
    paths = analysis_paths(root)
    text = "\n".join(f"{path} {_sha256(root / path)}" for path in paths)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fallback(root: Path = ROOT) -> dict[str, str]:
    validation_id = json.loads((root / VALIDATION_PLAN).read_text(encoding="utf-8")).get("validation_id")
    if not isinstance(validation_id, str) or not validation_id or validation_id.startswith("PENDING"):
        raise ValueError(f"{VALIDATION_PLAN}: validation_id isn't set ({validation_id!r})")
    ledger = json.loads((root / CORPUS_FREEZE).read_text(encoding="utf-8")).get("source_ledger_hash")
    if not isinstance(ledger, str) or len(ledger) != 64:
        raise ValueError(f"{CORPUS_FREEZE}: no source_ledger_hash")
    return {"validation_id": validation_id, "source_ledger_hash": ledger,
            "validation_plan_hash": _sha256(root / VALIDATION_PLAN),
            "validation_schema_hash": _sha256(root / VALIDATION_SCHEMA),
            "report_generator_hash": _sha256(root / REPORT_GENERATOR)}


def compute(root: Path = ROOT) -> dict[str, Any]:
    """Every value the step passes to `analysis.active_protocol.generate(...)`."""
    root = Path(root)
    covered = [*analysis_paths(root), CORPUS_FREEZE, VALIDATION_PLAN, VALIDATION_SCHEMA]
    refusal = _clean_refusal(root, covered)
    if refusal:
        raise ValueError(refusal)
    return {"analysis_hash": analysis_hash(root), "engineering_fallback": fallback(root)}


def check(active: Mapping[str, Any], computed: Mapping[str, Any]) -> list[str]:
    """Every way `active` disagrees with the recomputed values; empty when it agrees."""
    tier_class = active.get("tier_class")
    if tier_class == "STOP":
        return ["STOP carries no engineering fallback, so there is nothing for this check to compare"]
    problems = []
    stored = active.get("engineering_fallback") or {}
    for field in FALLBACK_FIELDS:
        value, expected = stored.get(field), computed["engineering_fallback"][field]
        if value is None:
            problems.append(f"engineering_fallback.{field} is null")
        elif value != expected:
            problems.append(f"engineering_fallback.{field} is {value}, recomputed {expected}")
    empirical = active.get("empirical") or {}
    value = empirical.get("analysis_hash")
    if tier_class == "ENGINEERING":
        reason = (empirical.get("null_reasons") or {}).get("analysis_hash")
        if value is not None:
            problems.append("empirical.analysis_hash must be null at ENGINEERING")
        elif not isinstance(reason, str) or not reason.strip():
            problems.append("empirical.analysis_hash is null without its own reason in empirical.null_reasons")
    elif value != computed["analysis_hash"]:
        problems.append(f"empirical.analysis_hash is {value}, recomputed {computed['analysis_hash']}")
    return problems


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", type=Path, default=None, metavar="ACTIVE_JSON")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        computed = compute(args.root)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"gate3_hashes: {exc}", file=sys.stderr)
        return 1
    if args.check is None:
        print(json.dumps(computed, indent=2, sort_keys=True))
        return 0
    active = json.loads(args.check.read_text(encoding="utf-8"))
    problems = check(active, computed)
    for problem in problems:
        print(f"gate3_hashes: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"gate3_hashes: {args.check} agrees with the recomputed hashes ({active.get('tier')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
