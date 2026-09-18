"""Large-type terminal trace for one recorded, schema-valid mock trial.

Reads ``events.jsonl`` (and the sibling ``results.jsonl`` when present),
validates every record, and prints the regions from docs/DEMO_DESIGN.md.
States are spelled out in words; nothing depends on color. Lines stay within
WIDTH columns so the terminal font can be enlarged for presentation without
wrapping.

Usage: python -m demo.trace PATH/TO/events.jsonl
"""

from __future__ import annotations

import argparse
import textwrap
from pathlib import Path
from typing import Any, Mapping, Optional

from runner.mock_slice import RESULTS_FILE, read_jsonl

WIDTH = 60
INDENT = "  "
UNKNOWN = "NO EVIDENCE / UNKNOWN"


def _wrap(text: str) -> list[str]:
    return textwrap.wrap(text, WIDTH - len(INDENT), break_on_hyphens=False) or [""]


def _wrap_id(identifier: str) -> list[str]:
    """Wrap a hierarchical ID only after ':' so each line copies back exactly."""
    out = [""]
    for part in identifier.split(":"):
        piece = part if out[-1] == "" else ":" + part
        if out[-1] and len(out[-1]) + len(piece) > WIDTH - len(INDENT):
            out[-1] += ":"
            out.append(part)
        else:
            out[-1] += piece
    return out


def _section(title: str, body: list[str]) -> list[str]:
    return ["", INDENT + title, INDENT + "-" * len(title), *(INDENT + line for line in body)]


def _tri(value: Optional[bool]) -> str:
    if value is None:
        return UNKNOWN
    return "TRUE" if value else "FALSE"


def _row(label: str, value: str) -> str:
    return f"{label} ".ljust(24, ".") + " " + value


def _event_line(event: Mapping[str, Any]) -> str:
    kind = event["event_type"]
    p = event["payload"]
    if kind == "trial_started":
        text = "TRIAL STARTED"
    elif kind == "provider_attempt":
        text = f"STEP {p['step']} MODEL RESPONSE, STOP: {p['raw_response']['stop_reason'].upper()}"
        if p["outcome"] != "model_response":
            text = f"STEP {p['step']} NO MODEL CONTENT"
    elif kind == "final_output":
        text = "FINAL OUTPUT RECORDED"
    elif kind == "trial_ended":
        reason = p["termination_reason"].replace("_", " ").upper()
        text = f"TRIAL ENDED: {reason}, {p['steps_used']} STEPS"
    else:
        text = kind.replace("_", " ").upper()
    return f"[{event['sequence']}] {text}"


def render_trace(events_path: Path) -> str:
    events = read_jsonl(events_path, "event")
    results_path = events_path.parent / RESULTS_FILE
    result = read_jsonl(results_path, "result")[-1] if results_path.exists() else None

    started = next(e for e in events if e["event_type"] == "trial_started")
    final = next((e for e in events if e["event_type"] == "final_output"), None)
    tier = started["payload"].get("tier") or "NOT SELECTED"

    lines = [
        "=" * WIDTH,
        INDENT + "CANARY  |  RECORDED TRACE",
        INDENT + f"TIER: {tier}",
        INDENT + f"MODEL: {started['payload']['model_requested']} (MOCK)",
        INDENT + "CASE: MOCK / EXCLUDED",
        INDENT + f"CONFIGURATION: {started['configuration']}",
        "=" * WIDTH,
    ]
    lines += _section("TRUSTED TASK", _wrap(started["payload"]["task_prompt"]))
    lines += _section("UNTRUSTED DATA", ["NONE IN THIS MOCK TRIAL"])
    timeline: list[str] = []
    for event in events:
        timeline += _wrap(_event_line(event))
    lines += _section("EVENT TIMELINE", timeline)
    lines += _section("FINAL OUTPUT", _wrap(final["payload"]["text"]) if final else [UNKNOWN])

    if result is None:
        outcome = [_row("RESULT RECORD", UNKNOWN)]
    else:
        outcome = [
            _row("MODEL VIOLATION", _tri(result["security"]["model_violation"])),
            _row("SYSTEM COMPROMISE", _tri(result["security"]["system_compromise"])),
            _row("UTILITY", _tri(result["utility"]["pass"])),
        ]
    lines += _section("OUTCOME", outcome)

    lines += ["", "=" * WIDTH, INDENT + "TRACE:"]
    lines += [INDENT + line for line in _wrap_id(started["logical_trial_id"])]
    lines += [INDENT + "ILLUSTRATIVE — NOT STATISTICAL EVIDENCE", "=" * WIDTH]
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("events", type=Path, help="path to events.jsonl")
    args = parser.parse_args(argv)
    print(render_trace(args.events))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
