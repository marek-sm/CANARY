"""Reproducible W8-T1 component-freeze candidate; no Gate 3 attestation.

Generate with ``python -m tasks.freeze``; verify with ``--check``. A check
establishes byte consistency, never human review, environment selection, or
permission to run an official experiment (SPEC.md Section 11).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from corpus.freeze import set_hash

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tasks/freeze.json"

# Hash source and data, not __pycache__, local traces, mutable state, or this
# manifest itself. Every required pattern must match at least one regular file.
GROUPS = {
    "task_registry": ("tasks/registry.py", "tasks/templates/*.json", "tasks/task_order.*",
                      "tasks/coverage-smokes.json", "corpus/task_coverage/*.json"),
    "prompt_tool": ("tasks/registry.py", "runner/delivery.py", "tools/*.py",
                    "agent/task_requests.py", "corpus/c1_controls/*.json", "corpus/build_c1.py"),
    "fixtures": ("fixtures/w6-t1/**/*.json", "fixtures/w6-t1/**/*.txt",
                 "fixtures/task_coverage/*.txt"),
    "schema": ("schemas/*.json",),
    "oracle_scorer": ("oracles/utility/*.py", "tests/fixtures/task_suite/*.json",
                      "oracles/authorization/*.py", "oracles/authorization/golden/*.json",
                      "runner/execute.py", "defenses/*.py"),
    "sandbox": ("tools/sandbox.py", "tools/no_exec.py", "tools/worker.py", "uv.lock",
                "pyproject.toml"),
    "validators": ("tasks/freeze.py", "runner/coverage.py",
                   "tests/test_task_freeze.py", "tests/test_task_suite.py",
                   "tests/test_tool_sandbox.py",
                   "tests/test_sandbox_mutants.py"),
}


def sha(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"not a regular freeze input: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(root, patterns):
    result = {}
    for pattern in patterns:
        matches = sorted(root.glob(pattern))
        if not matches:
            raise ValueError(f"missing freeze input: {pattern}")
        for path in matches:
            result[path.relative_to(root).as_posix()] = sha(path)
    return dict(sorted(result.items()))


def build(root=ROOT):
    # Bind the existing W8-T2 freeze without changing its owners' selected pool,
    # payloads, embedded task prompts, source ledger, or pins.
    from corpus.freeze import CORPUS_GLOBS, LEDGER_GLOBS
    corpus = json.loads((root / "corpus/freeze.json").read_text())
    for key, patterns, hash_key in (("corpus_files", CORPUS_GLOBS, "corpus_hash"),
                                    ("source_ledger_files", LEDGER_GLOBS, "source_ledger_hash")):
        actual = collect(root, patterns)
        if actual != corpus[key] or set_hash(actual) != corpus[hash_key]:
            raise ValueError(f"existing W8-T2 {key} drift; do not silently re-pin")

    components = {name: {"sha256": set_hash(files), "files": files}
                  for name, patterns in GROUPS.items()
                  for files in [collect(root, patterns)]}
    templates = {path.stem: json.loads(path.read_text())
                 for path in sorted((root / "tasks/templates").glob("*.json"))}
    if len(templates) != 10:
        raise ValueError("expected the ten retained task templates")
    policies = {f"{tid}/{channel}": variant["policy"]
                for tid, task in templates.items() for channel, variant in task["variants"].items()}
    if any(set(task["variants"]) != {"C2", "C3", "C4"} for task in templates.values()):
        raise ValueError("every retained task needs all three channels")
    policy_bytes = json.dumps(policies, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    fixture_manifest = json.loads((root / "fixtures/w6-t1/manifest.json").read_text())
    actual_fixtures = {path.relative_to(root / "fixtures/w6-t1").as_posix(): sha(path)
                       for path in (root / "fixtures/w6-t1").rglob("*")
                       if path.is_file() and path.relative_to(root / "fixtures/w6-t1").as_posix()
                       not in {"manifest.json", "fixture.sqlite"}}
    if actual_fixtures != fixture_manifest["files"]:
        raise ValueError("task fixture manifest drift")
    return {
        "version": "w8-t1-component-candidate-v0.1.0",
        "status": "pending_lead_review",
        "rule": "W8-T1; SPEC.md Section 11; decision 0031 item 8",
        "scope": "ten tasks, three channels; component candidate, not protocol/active.json",
        "pending": ["Green exact-head CI and merge under repository review rules",
                    "Lead-side review and human disposition of findings before Gate 3",
                    "Lead-owned full protocol and execution-environment freeze"],
        "task_ids": sorted(templates),
        "corpus_hash": corpus["corpus_hash"],
        "source_ledger_hash": corpus["source_ledger_hash"],
        "authorization_policy_hash": hashlib.sha256(policy_bytes).hexdigest(),
        "common_hashes": {name: components[name]["sha256"]
                          for name in ("task_registry", "prompt_tool", "schema", "oracle_scorer")},
        "components": components,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        text = json.dumps(build(), indent=2) + "\n"
        if args.check:
            if not OUT.exists() or OUT.read_text() != text:
                raise ValueError("tasks/freeze.json missing or component drift; regenerate before review")
        else:
            OUT.write_text(text)
    except (ValueError, OSError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
