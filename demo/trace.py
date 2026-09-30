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
    parts = identifier.split(":")
    for index, part in enumerate(parts):
        piece = part + (":" if index < len(parts) - 1 else "")
        if out[-1] and len(out[-1]) + len(piece) > WIDTH - len(INDENT):
            out.append(piece)
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
        text = f"STEP {p['step']} MODEL RESPONSE, STOP: {(p['raw_response'] or {}).get('stop_reason', 'unknown').upper()}"
        if p["outcome"] != "model_response":
            text = f"STEP {p['step']} NO MODEL CONTENT"
    elif kind == "tool_requested":
        text = "REQUESTED read_file"
    elif kind == "tool_dispatch":
        text = "DISPATCHED TO LOCAL FIXTURE"
    elif kind == "tool_result":
        text = "EXECUTION SUCCEEDED" if p["observation"]["ok"] else "TOOL ERROR: " + p["observation"]["error"]
    elif kind == "effect_observation":
        text = "EFFECT OBSERVED" if p["effect_observed"] else "NO EFFECT OBSERVED"
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
    attempts = [e for e in events if e["event_type"] == "provider_attempt"]
    final = next((e for e in events if e["event_type"] == "final_output"), None)
    tier = started["payload"].get("tier") or "NOT SELECTED"
    resolved_model = next(
        (
            event["payload"].get("model_resolved")
            for event in reversed(attempts)
            if event["payload"].get("model_resolved")
        ),
        None,
    )
    protocol_version = result["protocol_version"] if result else None

    lines = [
        "=" * WIDTH,
        INDENT + "CANARY  |  RECORDED TRACE",
        INDENT + f"TIER: {tier}",
        INDENT + f"MODEL REQUESTED: {started['payload']['model_requested']}",
        INDENT + f"MODEL RESOLVED: {resolved_model or UNKNOWN}",
        INDENT + "PROVIDER: MOCK",
        INDENT + "CASE: MOCK / EXCLUDED",
        INDENT + f"CONFIGURATION: {started['configuration']}",
        "=" * WIDTH,
    ]
    lines += _section("TRUSTED TASK", _wrap(started["payload"]["task_prompt"]))
    channel = result["channel"] if result else None
    observations = [e["payload"]["observation"]["text"] for e in events
                    if e["event_type"] == "tool_result" and e["payload"].get("observation", {}).get("ok")]
    if channel:
        untrusted = [f"CHANNEL {channel} / {result['condition'].upper()} CONDITION"]
        span = started["payload"].get("untrusted_span")
        if span:
            untrusted += _wrap(span)
        lines += _section("UNTRUSTED DATA", untrusted)
    elif observations:
        lines += _section("UNTRUSTED DATA", [line for text in observations for line in _wrap(text)])
    else:
        lines += _section("UNTRUSTED DATA", ["NONE RECORDED IN THIS MOCK TRIAL"])
    if result and result.get("measurement_limitation"):
        lines += _section("MEASUREMENT LIMITATION", _wrap(result["measurement_limitation"]))
    timeline: list[str] = []
    for event in events:
        timeline += _wrap(_event_line(event))
    lines += _section("EVENT TIMELINE", timeline)
    lines += _section("FINAL OUTPUT", _wrap(final["payload"]["text"]) if final else [UNKNOWN])

    security = result["security"] if result else {}
    utility = result["utility"] if result else {}
    outcome = [
        _row("MODEL VIOLATION", _tri(security.get("model_violation"))),
        _row("SYSTEM COMPROMISE", _tri(security.get("system_compromise"))),
        _row("UTILITY", _tri(utility.get("pass"))),
    ]
    if channel:
        outcome.insert(
            0,
            _row("USER DISCLOSURE", _tri(security.get("unauthorized_user_disclosure"))),
        )
    lines += _section("OUTCOME", outcome)

    lines += [
        "",
        "=" * WIDTH,
        INDENT + f"PROTOCOL: {protocol_version or 'NOT FROZEN'}",
        INDENT + "TRACE:",
    ]
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
