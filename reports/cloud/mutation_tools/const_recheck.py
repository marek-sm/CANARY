"""Re-run constant-mutation survivors against a test selection (the new tests).

Reads const_mutator.py's JSONL, regenerates each surviving mutant of each
file by its description, applies it in place in a scratch copy, runs the
selection, and restores the file. Development tool for
reports/cloud/mutation.md, not project code.

Usage (from the scratch copy's root):
  python const_recheck.py RESULTS.jsonl --tests "tests/a.py ..." --out RECHECK.jsonl
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from const_mutator import mutants  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--tests", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    survivors = [json.loads(line) for line in Path(args.results).read_text().splitlines() if line.strip()]
    survivors = [r for r in survivors if r["status"] != "killed"]
    by_file: dict[str, set[str]] = {}
    for r in survivors:
        by_file.setdefault(r["file"], set()).add(r["mutant"])
    with open(args.out, "a", encoding="utf-8") as out:
        for file, wanted in by_file.items():
            path = Path(file)
            original = path.read_text(encoding="utf-8")
            try:
                for desc, line, text in mutants(original):
                    if desc not in wanted:
                        continue
                    path.write_text(text, encoding="utf-8")
                    try:
                        proc = subprocess.run(
                            [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider",
                             *shlex.split(args.tests)], capture_output=True, text=True, timeout=900)
                        status = "killed" if proc.returncode != 0 else "survived"
                    except subprocess.TimeoutExpired:
                        status = "timeout"
                    finally:
                        path.write_text(original, encoding="utf-8")
                    out.write(json.dumps({"file": file, "line": line, "mutant": desc, "status": status}) + "\n")
                    out.flush()
            finally:
                path.write_text(original, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
