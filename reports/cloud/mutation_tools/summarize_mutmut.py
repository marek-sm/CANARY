"""Summarize mutmut 3 results from its ``mutants/**/*.py.meta`` files.

Prints per-module counts and writes every non-killed mutant name to a file.
Development tool for reports/cloud/mutation.md, not project code.

Usage: python summarize_mutmut.py MUTANTS_DIR [--survivors OUT]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

STATUS = {1: "killed", 3: "killed", 0: "survived", 5: "no tests", 33: "no tests", 34: "skipped",
          35: "suspicious", 36: "timeout", 37: "type check", -24: "timeout", 24: "timeout",
          152: "timeout", 255: "timeout", -11: "segfault", -9: "segfault", None: "not checked"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mutants_dir", type=Path)
    ap.add_argument("--survivors", type=Path)
    args = ap.parse_args()
    rows = []
    others = []
    for meta in sorted(args.mutants_dir.rglob("*.py.meta")):
        module = meta.relative_to(args.mutants_dir).as_posix()[: -len(".meta")]
        codes = json.loads(meta.read_text())["exit_code_by_key"]
        counts = Counter(STATUS.get(code, "suspicious") for code in codes.values())
        if not codes:
            continue
        rows.append((module, len(codes), counts))
        others += [(name, STATUS.get(code, "suspicious")) for name, code in codes.items()
                   if STATUS.get(code, "suspicious") != "killed"]
    header = ["module", "mutants", "killed", "survived", "no tests", "timeout", "suspicious", "not checked",
              "survival %"]
    print("| " + " | ".join(header) + " |")
    print("|" + "---|" * len(header))
    total = Counter()
    for module, n, c in rows:
        total.update(c)
        total["_n"] += n
        tested = n - c["not checked"]
        rate = 100 * (c["survived"] + c["no tests"]) / tested if tested else 0.0
        print(f"| `{module}` | {n} | {c['killed']} | {c['survived']} | {c['no tests']} | {c['timeout']} | "
              f"{c['suspicious'] + c['segfault']} | {c['not checked']} | {rate:.1f} |")
    tested = total["_n"] - total["not checked"]
    rate = 100 * (total["survived"] + total["no tests"]) / tested if tested else 0.0
    print(f"| **total** | {total['_n']} | {total['killed']} | {total['survived']} | {total['no tests']} | "
          f"{total['timeout']} | {total['suspicious'] + total['segfault']} | {total['not checked']} | {rate:.1f} |")
    if args.survivors:
        args.survivors.write_text("".join(f"{status}\t{name}\n" for name, status in others))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
