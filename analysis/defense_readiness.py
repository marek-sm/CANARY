"""The Gate 2 step's binary defense readiness checks (W7-T4).

SPEC.md Section 12, row-selection rule 3, defines both checks in advance:

* ``D1_POLICY_GATE`` is ready when every argument/grant golden test passes,
  the gate/audit differential tests agree, no blocked request dispatches, and
  its full development cells complete.
* ``D2_DATAMARKING`` is ready when every coverage, round-trip, and
  context-window test passes and its full development cells complete.

These are engineering checks, not evaluation outcomes. The script is outcome
blind: it reads only dispatch, decision, completion, and token facts, and never
``security``, ``utility``, ``model_violation``, or ``system_compromise``, so a
defense cannot be judged ready or not ready by whether an attack worked. The
project lead runs it over the live development grid's run directory in the
Gate 2 step, so readiness is a tier input and is never self-certified.

It makes no provider call. It refuses evaluation records, mock-provider
records, records from more than one run, and duplicate logical trials, the same
refusals as ``analysis.floor_count``. A check whose evidence is missing fails
and names what is missing; unknown evidence is never counted as passing.

Predeclared rules (changing one is a versioned change to this file):

D1 record checks, over every ``D1_POLICY_GATE`` trial:
  D1-CELLS      the 30 cells (5 bases x C2/C3/C4 x attack/clean) each have
                exactly one record, run 1, status ``completed``.
  D1-EXERCISED  at least one tool event carries a gate decision, so the gate
                ran rather than sat unused.
  D1-DECIDED    every tool event carries a gate decision. A null one is a gate
                that could not evaluate (POLICY_UNAVAILABLE) and fails.
  D1-NO-BLOCKED-DISPATCH  no tool event the gate denied was dispatched, every
                denied event is recorded ``blocked``, and no allowed event is.
  D1-AGREE      ``gate_audit_match`` is true on every tool event.
  D1-OBSERVED   ``disposition_observed`` is true on every tool event.
D1 code checks: the policy-gate golden tests and the gate/audit differential
tests pass with none skipped.

D2 record checks, over every ``D2_DATAMARKING`` trial:
  D2-CELLS      the same 30 cells.
  D2-USAGE      every trial records ``usage.input_tokens``.
  D2-NO-TRUNCATION  no provider attempt stopped at the output limit.
  D2-CONTEXT    the largest recorded ``input_tokens`` plus the output reserve
                fits the context window the lead supplies with ``--context-window``
                and ``--output-reserve``. With no window supplied the check fails:
                fit cannot be shown without it.
D2 code checks: the datamarking coverage, round-trip, and vector tests pass with
none skipped.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

from jsonschema import ValidationError

from analysis.floor_count import (
    CHANNELS,
    DEVELOPMENT_BASES,
    Trial,
    _hit_output_limit,
    _is_mock,
    load_run,
)

READINESS_VERSION = "defense-readiness-v0.1.0"
REPO_ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = ("attack", "clean")

D1 = "D1_POLICY_GATE"
D2 = "D2_DATAMARKING"
D1_TEST_FILES = ("tests/test_policy_gate.py", "tests/test_gate_audit_differential.py")
D2_TEST_FILES = ("tests/test_datamarking.py",)


def _check(check_id: str, passed: bool, detail: str, evidence: Optional[Sequence[str]] = None) -> dict[str, Any]:
    return {"check": check_id, "passed": bool(passed), "detail": detail, "evidence": list(evidence or [])}


def _decision(checks: Iterable[Mapping[str, Any]]) -> str:
    return "ready" if all(c["passed"] for c in checks) else "not_ready"


# --------------------------------------------------------------------------
# Refusals shared with the floor count.
# --------------------------------------------------------------------------


def _refuse_unusable(trials: Sequence[Trial]) -> None:
    experiments = {record["experiment_id"] for record, _ in trials}
    if len(experiments) != 1:
        raise ValueError(f"records come from {len(experiments)} runs ({sorted(experiments)}); expected exactly one")
    for record, events in trials:
        if record["split"] != "development":
            raise ValueError(f"{record['logical_trial_id']}: an evaluation record cannot feed a development readiness check")
        if _is_mock(record, events):
            raise ValueError(f"{record['logical_trial_id']}: mock-provider records never count toward readiness")
    ids = [record["logical_trial_id"] for record, _ in trials]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"duplicate logical trials: {duplicates}")


# --------------------------------------------------------------------------
# Cells.
# --------------------------------------------------------------------------


def expected_cells() -> set[tuple[str, str, str]]:
    return {(b, ch, cond) for b in DEVELOPMENT_BASES for ch in CHANNELS for cond in CONDITIONS}


def cells_check(check_id: str, configuration: str, trials: Sequence[Trial]) -> dict[str, Any]:
    wanted = expected_cells()
    seen: dict[tuple[str, str, str], list[Mapping[str, Any]]] = {}
    for record, _ in trials:
        if record["configuration"] != configuration:
            continue
        key = (record["base_case_id"], record["channel"], record["condition"])
        seen.setdefault(key, []).append(record)
    problems: list[str] = []
    for key in sorted(wanted):
        records = seen.get(key, [])
        label = ":".join(key)
        if not records:
            problems.append(f"{label} missing")
        elif len(records) > 1:
            problems.append(f"{label} has {len(records)} records")
        else:
            record = records[0]
            if record["run_index"] != 1:
                problems.append(f"{label} is run {record['run_index']}, not run 1")
            if record["status"] != "completed":
                problems.append(f"{label} status is {record['status']}")
    for key in sorted(set(seen) - wanted):
        problems.append(f"{':'.join(key)} is not a development-grid cell")
    return _check(
        check_id,
        not problems,
        f"{len(wanted) - sum(1 for p in problems if p.endswith('missing'))} of {len(wanted)} cells present"
        if problems
        else f"all {len(wanted)} cells have exactly one completed run-1 record",
        problems,
    )


# --------------------------------------------------------------------------
# D1 record checks.
# --------------------------------------------------------------------------


def _d1_events(trials: Sequence[Trial]) -> list[tuple[str, Mapping[str, Any]]]:
    return [
        (record["logical_trial_id"], event)
        for record, _ in trials
        if record["configuration"] == D1
        for event in record["tool_events"]
    ]


def d1_record_checks(trials: Sequence[Trial]) -> list[dict[str, Any]]:
    events = _d1_events(trials)
    decided = [(t, e) for t, e in events if e.get("gate_decision") is not None]

    undecided = [f"{t}:{e['call_id']}" for t, e in events if e.get("gate_decision") is None]

    leaks: list[str] = []
    for trial, event in decided:
        authorized = event["gate_decision"]["authorized"]
        ref = f"{trial}:{event['call_id']}"
        if authorized is False:
            if event.get("dispatched") is not False:
                leaks.append(f"{ref} was denied but dispatched={event.get('dispatched')}")
            if event.get("blocked") is not True:
                leaks.append(f"{ref} was denied but blocked={event.get('blocked')}")
        elif authorized is True:
            if event.get("blocked") is not False:
                leaks.append(f"{ref} was allowed but blocked={event.get('blocked')}")
        else:
            leaks.append(f"{ref} gate decision has authorized=null")

    disagree = [f"{t}:{e['call_id']} gate_audit_match={e.get('gate_audit_match')}" for t, e in events if e.get("gate_audit_match") is not True]
    unobserved = [f"{t}:{e['call_id']} disposition_observed={e.get('disposition_observed')}" for t, e in events if e.get("disposition_observed") is not True]

    return [
        cells_check("D1-CELLS", D1, trials),
        _check("D1-EXERCISED", bool(decided), f"{len(decided)} tool events carry a gate decision"),
        _check("D1-DECIDED", not undecided, f"{len(undecided)} tool events have no gate decision", undecided),
        _check("D1-NO-BLOCKED-DISPATCH", not leaks, f"{len(leaks)} disposition violations over {len(decided)} decided events", leaks),
        _check("D1-AGREE", not disagree, f"{len(disagree)} events without a true gate_audit_match", disagree),
        _check("D1-OBSERVED", not unobserved, f"{len(unobserved)} events without a true disposition_observed", unobserved),
    ]


# --------------------------------------------------------------------------
# D2 record checks.
# --------------------------------------------------------------------------


def d2_record_checks(
    trials: Sequence[Trial], context_window: Optional[int], output_reserve: Optional[int]
) -> list[dict[str, Any]]:
    d2 = [(record, events) for record, events in trials if record["configuration"] == D2]

    no_usage = [r["logical_trial_id"] for r, _ in d2 if r["usage"].get("input_tokens") is None]
    truncated = [r["logical_trial_id"] for r, ev in d2 if _hit_output_limit(ev)]

    inputs = [r["usage"]["input_tokens"] for r, _ in d2 if r["usage"].get("input_tokens") is not None]
    if context_window is None or output_reserve is None:
        context = _check(
            "D2-CONTEXT",
            False,
            "no --context-window and --output-reserve supplied, so fit cannot be shown",
        )
    elif not inputs:
        context = _check("D2-CONTEXT", False, "no D2 trial records input_tokens")
    else:
        largest = max(inputs)
        context = _check(
            "D2-CONTEXT",
            largest + output_reserve <= context_window,
            f"largest input {largest} + output reserve {output_reserve} = {largest + output_reserve} "
            f"against a {context_window}-token window",
        )

    return [
        cells_check("D2-CELLS", D2, trials),
        _check("D2-USAGE", not no_usage and bool(d2), f"{len(no_usage)} of {len(d2)} D2 trials lack input_tokens", no_usage),
        _check("D2-NO-TRUNCATION", not truncated, f"{len(truncated)} D2 trials hit the output limit", truncated),
        context,
    ]


# --------------------------------------------------------------------------
# Code checks: the committed tests, run as they are, with none skipped.
# --------------------------------------------------------------------------


def run_tests(check_id: str, files: Sequence[str]) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-rs", "-p", "no:cacheprovider", *files],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    output = proc.stdout + proc.stderr
    summary = output.strip().splitlines()[-1] if output.strip() else ""
    skipped = re.search(r"\b(\d+) skipped\b", output)
    passed = proc.returncode == 0 and not skipped and re.search(r"\b\d+ passed\b", output) is not None
    detail = summary if passed else (f"{summary}" + (" (tests were skipped; a skip is not a pass)" if skipped else ""))
    return _check(check_id, passed, detail, list(files))


def code_checks(defense: str) -> list[dict[str, Any]]:
    if defense == D1:
        return [run_tests("D1-TESTS", D1_TEST_FILES)]
    return [run_tests("D2-TESTS", D2_TEST_FILES)]


# --------------------------------------------------------------------------
# The report.
# --------------------------------------------------------------------------


def defense_readiness(
    trials: Sequence[Trial],
    *,
    context_window: Optional[int] = None,
    output_reserve: Optional[int] = None,
    run_code_checks: bool = True,
) -> dict[str, Any]:
    _refuse_unusable(trials)
    d1 = d1_record_checks(trials) + (code_checks(D1) if run_code_checks else [])
    d2 = d2_record_checks(trials, context_window, output_reserve) + (code_checks(D2) if run_code_checks else [])
    return {
        "readiness_version": READINESS_VERSION,
        "experiment_id": trials[0][0]["experiment_id"],
        "trials_read": len(trials),
        "code_checks_run": run_code_checks,
        "defenses": {
            D1: {"decision": _decision(d1), "checks": d1},
            D2: {"decision": _decision(d2), "checks": d2},
        },
        "note": "Binary engineering checks, never attack outcomes (SPEC.md Section 12). Outcome-blind by construction.",
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Binary D1_POLICY_GATE and D2_DATAMARKING readiness over a development-grid run.")
    parser.add_argument("run_dir", type=Path, help="directory holding the grid's per-trial results.jsonl and events.jsonl")
    parser.add_argument("--out", type=Path, help="write the report here instead of printing it")
    parser.add_argument("--context-window", type=int, help="the chosen model's context window in tokens")
    parser.add_argument("--output-reserve", type=int, help="tokens reserved for output and worst-case tool-loop headroom")
    args = parser.parse_args(argv)
    try:
        report = defense_readiness(load_run(args.run_dir), context_window=args.context_window, output_reserve=args.output_reserve)
    except (ValueError, OSError, ValidationError) as error:
        print(f"defense-readiness: {error}", file=sys.stderr)
        return 1
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
