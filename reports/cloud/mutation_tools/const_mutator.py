"""Supplementary mutator for module-level and class-level constants.

mutmut 3 mutates only code inside functions and methods (it routes each call
through a trampoline), so a module constant such as ``FLOOR_THRESHOLD = 3`` or
the per-token prices in ``analysis/gate2_budget.py`` is never mutated. This
script mutates the literals in each top-level or class-level assignment of a
target file, one mutant at a time, in place in a scratch copy of the
repository, runs the given pytest selection, and restores the file.

It is a development tool for the mutation report, not project code.

Usage (from the scratch copy's root, as the non-root user):
  python const_mutator.py FILE --tests "tests/a.py tests/b.py" --out results.jsonl
"""

from __future__ import annotations

import argparse
import ast
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path


def _literal_mutations(node: ast.AST):
    """Yield (description, replacement source) for each literal inside ``node``."""
    in_fstring = {id(c) for j in ast.walk(node) if isinstance(j, ast.JoinedStr) for c in ast.walk(j)}
    for sub in ast.walk(node):
        if id(sub) in in_fstring:
            continue
        if isinstance(sub, ast.Constant):
            v = sub.value
            if isinstance(v, bool):
                yield sub, f"{v!r} -> {not v!r}", repr(not v)
            elif isinstance(v, int):
                for new in {v + 1, v - 1, 0} - {v}:
                    yield sub, f"{v!r} -> {new!r}", repr(new)
            elif isinstance(v, float):
                for new in {v * 2, v / 2, 0.0} - {v}:
                    yield sub, f"{v!r} -> {new!r}", repr(new)
            elif isinstance(v, str) and v:
                yield sub, f"{v[:40]!r} -> 'XX'+...", repr("XX" + v + "XX")
        elif isinstance(sub, (ast.Tuple, ast.List, ast.Set)) and len(sub.elts) > 1:
            for i, elt in enumerate(sub.elts):
                # Remove one element of a collection literal.
                yield ("drop", sub, i), f"drop element {i} ({ast.unparse(elt)[:40]})", None
        elif isinstance(sub, ast.Dict) and len(sub.keys) > 1:
            for i, key in enumerate(sub.keys):
                if key is not None:
                    yield ("dropkey", sub, i), f"drop key {ast.unparse(key)[:40]}", None


def _segments(source: str, node: ast.AST) -> tuple[int, int]:
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line.encode("utf-8")))
    data = source.encode("utf-8")
    start = offsets[node.lineno - 1] + node.col_offset
    end = offsets[node.end_lineno - 1] + node.end_col_offset
    return start, end, data


def mutants(source: str):
    tree = ast.parse(source)
    targets = []
    for stmt in tree.body:
        if isinstance(stmt, (ast.Assign, ast.AnnAssign)) and stmt.value is not None:
            targets.append(stmt)
        elif isinstance(stmt, ast.ClassDef):
            targets += [s for s in stmt.body if isinstance(s, (ast.Assign, ast.AnnAssign)) and s.value is not None]
    for stmt in targets:
        name = ast.unparse(stmt.targets[0] if isinstance(stmt, ast.Assign) else stmt.target)
        if name in {"__all__"} or name.endswith("VERSION"):
            # Version strings are recorded, not compared; skip them to keep the count meaningful.
            continue
        for item in _literal_mutations(stmt.value):
            where, desc, replacement = item
            data = source.encode("utf-8")
            if isinstance(where, tuple):
                kind, coll, i = where
                if kind == "drop":
                    elt = coll.elts[i]
                    s, e, _ = _segments(source, elt)
                    # Remove the element and one adjacent comma.
                    tail = data[e:]
                    stripped = tail.lstrip()
                    if stripped.startswith(b","):
                        e = e + (len(tail) - len(stripped)) + 1
                    new = data[:s] + data[e:]
                else:
                    key, val = coll.keys[i], coll.values[i]
                    s, _, _ = _segments(source, key)
                    _, e, _ = _segments(source, val)
                    tail = data[e:]
                    stripped = tail.lstrip()
                    if stripped.startswith(b","):
                        e = e + (len(tail) - len(stripped)) + 1
                    new = data[:s] + data[e:]
            else:
                s, e, _ = _segments(source, where)
                new = data[:s] + replacement.encode("utf-8") + data[e:]
            text = new.decode("utf-8")
            try:
                ast.parse(text)
            except SyntaxError:
                continue
            yield f"{name} line {stmt.lineno}: {desc}", stmt.lineno, text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--tests", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=int, default=900)
    args = ap.parse_args()
    path = Path(args.file)
    original = path.read_text(encoding="utf-8")
    out = Path(args.out).open("a", encoding="utf-8")
    try:
        for desc, line, text in mutants(original):
            path.write_text(text, encoding="utf-8")
            started = time.time()
            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", *shlex.split(args.tests)],
                    capture_output=True, text=True, timeout=args.timeout,
                )
                status = "killed" if proc.returncode != 0 else "survived"
            except subprocess.TimeoutExpired:
                status = "timeout"
            finally:
                path.write_text(original, encoding="utf-8")
            out.write(json.dumps({"file": args.file, "line": line, "mutant": desc, "status": status,
                                  "seconds": round(time.time() - started, 1)}) + "\n")
            out.flush()
    finally:
        path.write_text(original, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
