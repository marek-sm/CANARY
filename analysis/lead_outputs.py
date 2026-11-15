"""The project lead's generated outputs: decision 0012's two count tables and decision
0028 item 4's count-only diagnostics (decision 0036; decision 0012 item 7's wiring).

    python -m analysis.lead_outputs                              # the empty shells, paper/generated/lead_outputs.md
    python -m analysis.lead_outputs --check                      # fail if that file is stale
    python -m analysis.lead_outputs RECORDS --out PATH           # the tables over a final set of result records
    python -m analysis.lead_outputs RECORDS --events RUN [--events RUN ...] --out PATH

`make report` runs this after the estimand shells ([decision 0036](../docs/decisions/0036-lead-output-wiring.md)).
These outputs are generated here, additively, and change no existing output; the Gate 3
step freezes this file with the rest of `analysis/`.

RECORDS is a final set of result records: either a raw sweep run directory, which must
verify complete (`runner.sweep.verify_sweep`, every stored result recomputed from its raw
events), or a released JSONL file of result records, each validated against the result
schema. Choosing the final, non-superseded set is the caller's: the released bundle is the
final set, and a raw run holds one result per scheduled trial. Decision 0012's two tables
read only the result records. The count-only tables read only verified raw evidence, each
primary record's stored result and raw events from a complete raw run: a raw run as RECORDS
supplies its own, and `--events` adds verified raw runs (a sweep run and its repair runs, say),
whose stored result must agree with the final record it stands for on the cell, the ending,
every scored fact, and each tool event's dispositions and arguments. Raw evidence of a trial
outside the final set is ignored. Without the raw evidence of every primary record in the
final set, the count-only tables are rendered as needing it, never computed from part of it;
which records form the final set is the caller's.

Over evaluation records, the tables stay hidden during the sweep (`SPEC.md` Section 9).
The project lead runs this after Gate 4's integrity checks pass; the code enforces the raw
run's completeness, and the rest holds by rule.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

from analysis import diagnostics
from analysis.report_shells import STATUS, load_manifest
from analysis.request_effect import request_to_effect_counts, tool_name_only_ablation
from runner import sweep
from runner.mock_slice import validator

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "paper" / "generated" / "lead_outputs.md"
DIAGNOSTICS = "ReliabilityAndResourceDiagnostics"
CELL = ["Configuration", "Condition (attack / clean)", "Delivery channel / adapter"]
NOT_APPLICABLE = "Not applicable at this tier: D1_POLICY_GATE isn't retained (`SPEC.md` Section 10)."
NEEDS_RAW_EVENTS_TEXT = ("Not shown: this table needs the raw events (decision 0028 item 4) of every primary "
                         "record, and the run gave records without them.")


class _NeedsRawEvents:
    """The value of a count-only table when some primary record has no raw events."""

    def __repr__(self) -> str:
        return "NEEDS_RAW_EVENTS"


NEEDS_RAW_EVENTS = _NeedsRawEvents()


@dataclass(frozen=True)
class Table:
    output_id: str
    title: str
    columns: list[str]
    compute: Callable[[list], Optional[list[dict[str, str]]]]

    @property
    def key(self) -> str:
        return self.title if self.output_id == DIAGNOSTICS else self.output_id


def _manifest_entry(output_id: str) -> Mapping[str, Any]:
    return next(entry for entry in load_manifest()["estimands"] if entry["id"] == output_id)


def _records(trials: list) -> list[Mapping[str, Any]]:
    return [record for record, _ in trials]


def _ablation(trials: list) -> Optional[list[dict[str, str]]]:
    primary = [record for record in _records(trials)
               if record.get("split") == "evaluation" and record.get("analysis_role") == "primary_indirect"]
    if not any(record.get("configuration") == "D1_POLICY_GATE" for record in primary):
        return None
    return tool_name_only_ablation(_records(trials))


TABLES = [
    Table("RequestToEffectCounts", _manifest_entry("RequestToEffectCounts")["title"],
          _manifest_entry("RequestToEffectCounts")["columns"], lambda trials: request_to_effect_counts(_records(trials))),
    Table("ToolNameOnlyAblation", _manifest_entry("ToolNameOnlyAblation")["title"],
          _manifest_entry("ToolNameOnlyAblation")["columns"], _ablation),
    Table(DIAGNOSTICS, "Tool blocks in malformed_model_output replies",
          [*CELL, "Malformed trials", "Replies whose blocks can't be read", "Tool blocks",
           "Names an offered tool (true / false / null)", "Canary in arguments (true / false / null)",
           "Authorized recipient (true / false / null)"], diagnostics.malformed_tool_blocks),
    Table(DIAGNOSTICS, "Filtered pairs",
          ["Configuration pair", "Delivery channel / adapter", "Filtered side", "First exposure (filtered reply)",
           "Unrecorded tool block (filtered reply)", "Filtered pairs"], diagnostics.filtered_pairs),
    Table(DIAGNOSTICS, "Trials with no request", [*CELL, "Ending", "Trials with no request"],
          diagnostics.trials_without_request),
    Table(DIAGNOSTICS, "Canaries in tool arguments",
          [*CELL, "Requests", "Requests with a canary in their arguments", "Trials with such a request",
           "Requests whose raw `to` differs from the normalized one and holds a canary"],
          diagnostics.canary_in_arguments),
    Table(DIAGNOSTICS, "Required calls satisfied only by an unauthorized request",
          [*CELL, "Logical trials", "Required calls satisfied", "Satisfied only by a request with authorized = false",
           "Unknown: another request that could satisfy it has an unknown verdict or effect", "Trials with such a call"], diagnostics.required_calls_only_unauthorized),
]


def _primary_ids(records: list[Mapping[str, Any]]) -> list:
    return [record.get("logical_trial_id") for record in records
            if record.get("split") == "evaluation" and record.get("analysis_role") == "primary_indirect"]


def generate(records: Iterable[Mapping[str, Any]],
             raw: Optional[Mapping[str, tuple[Mapping[str, Any], Sequence[Mapping[str, Any]]]]] = None) -> dict[str, Any]:
    """Every table over a final set of result records. Decision 0012's tables read only the
    records; the ablation is `None` at a tier without D1_POLICY_GATE. The count-only tables
    read only `raw`: for each logical trial, a verified raw run's stored result and its raw
    events. They are `NEEDS_RAW_EVENTS` unless `raw` holds every primary record. Raw
    evidence of a trial outside `records` is ignored."""
    records = list(records)
    raw = raw or {}
    covered = all(trial_id in raw for trial_id in _primary_ids(records))
    final = [(record, ()) for record in records]
    stored = [raw.get(record.get("logical_trial_id"), (record, ())) for record in records]
    tables: dict[str, Any] = {}
    for table in TABLES:
        if table.output_id != DIAGNOSTICS:
            tables[table.key] = table.compute(final)
        elif covered:
            tables[table.key] = table.compute(stored)
        else:
            tables[table.key] = NEEDS_RAW_EVENTS
    return tables


def _row(values: Iterable[str]) -> str:
    return "| " + " | ".join(str(value).replace("|", "\\|") for value in values) + " |"


def render(tables: Optional[Mapping[str, Optional[list[dict[str, str]]]]]) -> str:
    """Deterministic Markdown. `None` renders the empty pre-results shells."""
    lines = [
        "# CANARY Generated Lead Outputs",
        "",
        "> Decision 0012's request-to-effect table and tool-name-only ablation, and decision 0028",
        "> item 4's count-only diagnostics in `ReliabilityAndResourceDiagnostics`. Counts only: no",
        "> rate, interval, or endpoint, and none of them is shown before the sweep completes and its",
        "> integrity checks pass (`SPEC.md` Sections 9 and 10; decision 0036).",
    ]
    if tables is None:
        lines += ["", f"> **{STATUS}.** Generated by `python -m analysis.lead_outputs` with no run."]
    for table in TABLES:
        lines += ["", f"### {table.title}", "", f"- **Output ID:** `{table.output_id}`", ""]
        if tables is None:
            lines += [_row(table.columns), _row("---" for _ in table.columns),
                      _row([STATUS, *(["—"] * (len(table.columns) - 1))])]
            continue
        rows = tables[table.key]
        if rows is NEEDS_RAW_EVENTS:
            lines.append(NEEDS_RAW_EVENTS_TEXT)
            continue
        if rows is None:
            lines.append(NOT_APPLICABLE)
            continue
        lines += [_row(table.columns), _row("---" for _ in table.columns)]
        for row in rows:
            if list(row) != table.columns:
                raise ValueError(f"{table.title}: row keys {list(row)} aren't the table's columns")
            lines.append(_row(row.values()))
        if not rows:
            lines.append(_row(["none", *(["—"] * (len(table.columns) - 1))]))
    lines.append("")
    return "\n".join(lines)


def load_run(run: Path) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    """Each trial directory's committed result and its raw events, in directory order."""
    trials = []
    for results in sorted(Path(run).glob(f"*/{sweep.RESULTS_FILE}")):
        lines = results.read_text(encoding="utf-8").split("\n")
        records = [json.loads(line) for line in lines if line]
        if len(records) != 1:
            raise ValueError(f"{results.parent.name}: expected one committed result, found {len(records)}")
        events_text = (results.parent / "events.jsonl").read_text(encoding="utf-8").split("\n")
        trials.append((records[0], [json.loads(line) for line in events_text if line]))
    return trials


# The fields that tie a raw run's stored result to the final record it stands for: the cell,
# the ending, every scored fact, and each tool event's scored dispositions and normalized
# arguments. The sanitizer's scored projection keeps all of them unchanged.
BOUND_FIELDS = ("split", "analysis_role", "configuration", "condition", "channel", "base_case_id",
                "case_id", "run_index", "termination_reason", "status", "security", "utility")
TOOL_EVENT_FIELDS = ("call_id", "step", "tool", "normalized_args", "request_evaluable", "authorized",
                     "blocked", "dispatched", "disposition_observed", "execution_succeeded",
                     "effect_observed", "sink_received", "gate_audit_match", "effect_oracle_id")


def _bound(record: Mapping[str, Any]) -> tuple:
    events = record.get("tool_events")
    tool_events = ([{key: event.get(key) for key in TOOL_EVENT_FIELDS} for event in events]
                   if isinstance(events, list) else events)
    return tuple(record.get(key) for key in BOUND_FIELDS), tool_events


def read_released(path: Path) -> list[dict[str, Any]]:
    """A released JSONL file of result records, each validated against the result schema."""
    schema = validator("result")
    records = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").split("\n"), start=1):
        if not line:
            continue
        try:
            record = json.loads(line)
            schema.validate(record)
        except Exception as exc:
            raise ValueError(f"{path}: line {number} isn't a valid result record ({exc.__class__.__name__})") from exc
        records.append(record)
    if not records:
        raise ValueError(f"{path}: no result records")
    return records


def _verified_run(run: Path, corpus: list) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    verified = sweep.verify_sweep(run, *corpus)
    if verified.get("complete") is not True:
        raise SystemExit("these tables stay hidden during the sweep (SPEC.md Section 9): "
                         f"{run} isn't a complete, verified sweep run")
    return load_run(run)


def _add_events(raw: dict, trials: list, run: Path) -> None:
    for record, trial_events in trials:
        trial_id = record.get("logical_trial_id")
        if trial_id in raw:
            raise ValueError(f"{trial_id}: raw events in more than one raw run (last: {run})")
        raw[trial_id] = (record, trial_events)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("records", type=Path, nargs="?",
                        help="a final set of result records: a complete sweep run directory or a released JSONL file")
    parser.add_argument("--events", type=Path, action="append", default=[],
                        help="a complete raw run whose raw events the count-only tables read (repeatable)")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--check", action="store_true", help="fail if the committed empty shells are stale")
    parser.add_argument("--corpus-root", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.records is None:
        if args.events:
            raise SystemExit("--events needs the result records it explains")
        out = args.out or DEFAULT_OUTPUT
        rendered = render(None)
        if args.check:
            if not out.exists() or out.read_text(encoding="utf-8") != rendered:
                raise SystemExit(f"stale generated lead outputs: {out}")
            return 0
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
        return 0

    if args.check or args.out is None:
        raise SystemExit("records need --out, and --check applies only to the empty shells")
    corpus = [args.corpus_root] if args.corpus_root else []
    if args.records.is_dir():
        trials = _verified_run(args.records, corpus)
        records, events = [record for record, _ in trials], {}
        _add_events(events, trials, args.records)
    else:
        records, events = read_released(args.records), {}
    by_id = {record.get("logical_trial_id"): record for record in records}
    for run in args.events:
        trials = _verified_run(run, corpus)
        for record, _ in trials:
            final = by_id.get(record.get("logical_trial_id"))
            if final is not None and _bound(final) != _bound(record):
                raise ValueError(f"{record.get('logical_trial_id')}: {run}'s stored result disagrees with "
                                 "the final record it stands for")
        _add_events(events, trials, run)
    rendered = render(generate(records, events))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
