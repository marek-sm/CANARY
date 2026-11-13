"""Corpus freeze manifest (W8-T2; SPEC.md Section 5 step 8, Section 11 Gate 3).

    python -m corpus.freeze          # write corpus/freeze.json
    python -m corpus.freeze --check  # fail if any frozen file changed since

Records the SHA-256 of every file the frozen corpus rests on, in two sets, and one
hash per set for `protocol/active.json`:

- `corpus_hash`: the evaluation base cases, their rendered fixtures and templates,
  the C2/C3/C4 adapters, the clean-twin and build code, the selection and intake
  code, and the committed `task_order`;
- `source_ledger_hash`: the candidate ledger and every candidate's source record.

Each set hash is SHA-256 over its sorted `path<TAB>sha256` lines. The release-safe
payload list stays outside both sets, as W8-T2's row asks, so W9-T3's sanitizer
input can change without reopening the freeze.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "corpus" / "freeze.json"

CORPUS_GLOBS = (
    "corpus/evaluation/eval-*.json",
    "fixtures/eval-*/content.template.txt",
    "fixtures/eval-*/rendered-hashes.json",
    "fixtures/eval-*/rendered/*",
    "channels/__init__.py",
    "channels/render.py",
    "corpus/render_fixtures.py",
    "corpus/build_evaluation.py",
    "corpus/select.py",
    "corpus/intake.py",
    "tasks/task_order.json",
)
LEDGER_GLOBS = (
    "corpus/candidates.jsonl",
    "corpus/evaluation/candidates/*.json",
)


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(globs) -> dict[str, str]:
    out = {}
    for pattern in globs:
        for path in sorted(ROOT.glob(pattern)):
            if path.is_file():
                out[path.relative_to(ROOT).as_posix()] = file_sha(path)
    return dict(sorted(out.items()))


def set_hash(entries: dict[str, str]) -> str:
    lines = "\n".join(f"{path}\t{sha}" for path, sha in sorted(entries.items()))
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def build() -> dict:
    corpus = files(CORPUS_GLOBS)
    ledger = files(LEDGER_GLOBS)
    bases = sorted(Path(p).stem for p in corpus if p.startswith("corpus/evaluation/eval-"))
    if not bases:
        raise ValueError("no evaluation base cases to freeze")
    return {
        "rule": "W8-T2 corpus freeze; SPEC.md Section 5 step 8 and Section 11",
        "base_case_ids": bases,
        "corpus_hash": set_hash(corpus),
        "source_ledger_hash": set_hash(ledger),
        "corpus_files": corpus,
        "source_ledger_files": ledger,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write or check the corpus freeze manifest.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    text = json.dumps(build(), indent=2) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("corpus/freeze.json is missing or a frozen file changed; a change after freeze follows SPEC.md Section 11", file=sys.stderr)
            return 1
        return 0
    OUT.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
