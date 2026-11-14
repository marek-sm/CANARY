"""The separate descriptive C1 direct-injection control table (W8-T3; decision 0034 item 8).

SPEC.md Section 10 (Interpretation rules, C1) and decision 0004 item 18 fix its content: one
row per C1 control and outcome, with that control's D0_BASELINE repeat count, exact
true/false/null counts of the six underlying security facts, the two unions, and
``utility_pass``, and its infrastructure-failure count. It is labelled "direct-injection
positive controls; outside the primary threat model; not an estimate", and it has NO rate,
macro-average, interval, or comparison with indirect cases. Its columns are the predeclared
``C1DirectInjectionControls`` shell in ``paper/estimand_manifest.json``.

It reads only result records with ``split`` ``c1_control`` (result schema 1.1.0), validates each,
and never infers a missing value: an absent or unknown fact counts as null, never as false.

Usage:
    python -m analysis.c1_table --tier F20 RUN_DIR [RUN_DIR ...]
    python -m analysis.c1_table --tier F20            # pre-results shell, no records
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from analysis.active_protocol import c1_control_ids_for
from runner.mock_slice import read_jsonl, validator

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "paper" / "estimand_manifest.json"
ESTIMAND_ID = "C1DirectInjectionControls"
LABEL = "direct-injection positive controls; outside the primary threat model; not an estimate"
STATUS = "PRE-RESULTS — NO DATA"

SECURITY_FACTS = (
    "unauthorized_user_disclosure",
    "proposed_egress",
    "external_exfiltration",
    "unauthorized_action_requested",
    "unauthorized_action_dispatched",
    "unauthorized_action_effect",
)
UNIONS = ("model_violation", "system_compromise")
OUTCOMES = (*SECURITY_FACTS, *UNIONS, "utility_pass")


def _outcome(record: Mapping[str, Any], name: str) -> Optional[bool]:
    if name == "utility_pass":
        return record["utility"]["pass"]
    return record["security"][name]


def c1_records(records: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """The schema-valid C1 control records among ``records``; every other split is left out."""
    selected = []
    for record in records:
        if record.get("split") != "c1_control":
            continue
        validator("result").validate(record)
        selected.append(record)
    return selected


def tabulate(records: Iterable[Mapping[str, Any]], control_ids: list[str]) -> dict[str, dict[str, Any]]:
    """Per control: repeat count, true/false/null counts per outcome, and infrastructure failures.

    Counts only. A record for a control outside ``control_ids`` is refused, so a stray or
    development-material C1 record can't enter the official table.
    """
    rows: dict[str, dict[str, Any]] = {
        cid: {"repeats": 0, "infrastructure_failures": 0, "outcomes": {o: Counter() for o in OUTCOMES}}
        for cid in control_ids
    }
    for record in c1_records(records):
        cid = record["base_case_id"]
        if cid not in rows:
            raise ValueError(f"C1 record for {cid!r} is outside this tier's controls {control_ids}")
        row = rows[cid]
        row["repeats"] += 1
        if record["status"] == "infrastructure_failure":
            row["infrastructure_failures"] += 1
        for name in OUTCOMES:
            value = _outcome(record, name)
            row["outcomes"][name][{True: "true", False: "false", None: "null"}[value]] += 1
    return rows


def _columns() -> list[str]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    entry = next(e for e in manifest["estimands"] if e["id"] == ESTIMAND_ID)
    return list(entry["columns"])


def render(rows: Mapping[str, Mapping[str, Any]], *, has_records: bool) -> str:
    """Deterministic Markdown: one row per control and outcome, counts only, no rate or interval."""
    columns = _columns()
    lines = [
        "# C1 direct-injection positive controls",
        "",
        f"> **{LABEL.capitalize()}.** One row per control and outcome. Counts only: no rate,",
        "> macro-average, interval, or comparison with indirect cases (SPEC.md Section 10).",
        "",
    ]
    if not has_records:
        lines += [f"> **{STATUS}.** Regenerate from the frozen sanitized bundle after the sweep.", ""]
    lines += ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for cid, row in rows.items():
        for name in OUTCOMES:
            counts = row["outcomes"][name]
            cells = [cid, str(row["repeats"]), name]
            if has_records:
                cells += [str(counts["true"]), str(counts["false"]), str(counts["null"])]
            else:
                cells += ["—", "—", "—"]
            cells.append(str(row["infrastructure_failures"]) if has_records else "—")
            lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    return "\n".join(lines)


def _records_from(run_dirs: Iterable[Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        for path in sorted(Path(run_dir).glob("*/results.jsonl")):
            records.extend(read_jsonl(path, "result"))
    return records


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tier", required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("run_dirs", nargs="*", type=Path)
    args = parser.parse_args(argv)
    control_ids = c1_control_ids_for(args.tier)
    records = _records_from(args.run_dirs)
    text = render(tabulate(records, control_ids), has_records=bool(c1_records(records)))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
