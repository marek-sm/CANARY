"""Tier 2: re-test mutmut survivors against tests tier 1 left out or couldn't map.

Tier 1 is ``mutmut run`` with the seven slowest grid tests deselected. For each
mutant tier 1 marked survived or "no tests", this runs, inside mutmut's
``mutants/`` copy with ``MUTANT_UNDER_TEST`` set:

* ``--slow``: the deselected slow tests that cover the mutant's function
  (from ``mutmut-stats.json``), or
* ``--tests``: an explicit test selection (used for "no tests" mutants, whose
  callers run in a subprocess that mutmut's stats can't see).

Writes one JSON line per mutant: killed, survived, or timeout.
Development tool for reports/cloud/mutation.md, not project code.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def function_of(mutant: str) -> str:
    return re.sub(r"__mutmut_\d+$", "", mutant)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mutants_dir", type=Path)
    ap.add_argument("names", type=Path, help="file with one mutant name per line")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--slow", type=Path, help="file listing the deselected slow tests")
    ap.add_argument("--tests", help="explicit pytest selection instead of --slow")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()

    stats = json.loads((args.mutants_dir / "mutmut-stats.json").read_text())
    by_function = stats["tests_by_mangled_function_name"]
    slow = args.slow.read_text().split() if args.slow else []
    names = [n.strip() for n in args.names.read_text().splitlines() if n.strip()]
    done = set()
    if args.out.exists():
        done = {json.loads(line)["mutant"] for line in args.out.read_text().splitlines() if line.strip()}

    def run(name: str) -> dict:
        if args.tests:
            selection = shlex.split(args.tests)
        else:
            covering = set(by_function.get(function_of(name), []))
            selection = [t for t in slow if t in covering]
        if not selection:
            return {"mutant": name, "status": "survived", "tests": [], "note": "no deselected test covers it"}
        env = dict(os.environ, MUTANT_UNDER_TEST=name)
        base = Path("/tmp/tier2") / name.replace("ǁ", "_")
        base.parent.mkdir(parents=True, exist_ok=True)
        started = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", "-p", "no:randomly",
                 f"--basetemp={base}", *selection],
                cwd=args.mutants_dir, env=env, capture_output=True, text=True, timeout=args.timeout,
            )
            status = {0: "survived", 1: "killed"}.get(proc.returncode, f"exit{proc.returncode}")
            tail = proc.stdout.strip().splitlines()[-1:] if proc.stdout else []
        except subprocess.TimeoutExpired:
            status, tail = "timeout", []
        subprocess.run(["rm", "-rf", str(base)])
        return {"mutant": name, "status": status, "tests": selection, "seconds": round(time.time() - started, 1),
                "summary": tail}

    todo = [n for n in names if n not in done]
    with args.out.open("a") as out, ThreadPoolExecutor(args.jobs) as pool:
        for row in pool.map(run, todo):
            out.write(json.dumps(row) + "\n")
            out.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
