"""Duplicate-ID and sequence checks on traces and records (audit C-08).

SPEC.md Section 11 requires "duplicate-ID rejection"; Section 8 makes
logical-trial, model-call, and attempt IDs globally unique; docs/DATA_CONTRACTS.md
says duplicate global IDs fail validation; and a resume must add no duplicate
(SPEC.md Section 9, Gate 2). A trace holds one logical trial, numbered from 1.
"""

import json

import pytest

from runner import execute
from runner import mock_slice
from runner.mock_slice import EVENTS_FILE, RESULTS_FILE

CLOCK = lambda: "2020-01-01T00:00:00Z"  # noqa: E731 - deterministic test clock


@pytest.fixture
def trace(tmp_path):
    run = mock_slice.run_mock_trial(tmp_path / "run", clock=CLOCK)
    return run, (run / EVENTS_FILE).read_text(encoding="utf-8").splitlines()


def _write(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _edited(tmp_path, lines):
    return {
        "a duplicated line": lines[:2] + [lines[1]] + lines[2:],
        "a missing line": lines[:1] + lines[2:],
        "lines out of order": [lines[1], lines[0]] + lines[2:],
    }


def test_a_committed_trace_reads_cleanly(trace):
    run, lines = trace
    events = mock_slice.read_jsonl(run / EVENTS_FILE, "event")
    assert [e["sequence"] for e in events] == list(range(1, len(lines) + 1))
    assert execute._durable_events(run / EVENTS_FILE, truncate=False) == events


@pytest.mark.parametrize("edit", ["a duplicated line", "a missing line", "lines out of order"])
def test_a_trace_with_a_duplicate_or_gap_is_refused(tmp_path, trace, edit):
    _, lines = trace
    path = _write(tmp_path / f"{edit}.jsonl", _edited(tmp_path, lines)[edit])
    with pytest.raises(ValueError):
        mock_slice.read_jsonl(path, "event")
    with pytest.raises(ValueError):
        execute._durable_events(path, truncate=False)


def _result(trace):
    run, _ = trace
    (result,) = mock_slice.read_jsonl(run / RESULTS_FILE, "result")
    return result


@pytest.mark.parametrize("field, key", [("attempts", "attempt_id"), ("model_calls", "model_call_id")])
def test_a_record_with_a_duplicate_id_is_refused(tmp_path, trace, field, key):
    result = _result(trace)
    result[field] = result[field] + [dict(result[field][0])]
    mock_slice.validator("result").validate(result)  # the schema alone can't see it
    with pytest.raises(ValueError, match=key):
        mock_slice.check_record_ids(result)
    with pytest.raises(ValueError):
        mock_slice.append_jsonl(tmp_path / "results.jsonl", result, "result")
    assert not (tmp_path / "results.jsonl").exists() or (tmp_path / "results.jsonl").read_text() == ""
    with pytest.raises(ValueError):
        execute._commit_result(tmp_path / "committed.jsonl", result)
    _write(tmp_path / "read.jsonl", [json.dumps(result)])
    with pytest.raises(ValueError):
        mock_slice.read_jsonl(tmp_path / "read.jsonl", "result")


def test_a_record_with_a_duplicate_tool_call_is_refused(trace):
    result = _result(trace)
    event = {
        "call_id": "c1", "step": 1, "tool": "read_file", "requested_args": {"path": "a"}, "normalized_args": {"path": "a"},
        "normalizer_version": "v", "request_evaluable": False, "authorized": None, "gate_decision": None,
        "audit_decision": None, "gate_audit_match": None, "blocked": None, "dispatched": None,
        "disposition_observed": None, "execution_succeeded": None, "effect_observed": None,
        "effect_oracle_id": "o", "sink_received": None, "evidence_refs": [],
    }
    result["tool_events"] = [event, dict(event)]
    with pytest.raises(ValueError, match="call_id"):
        mock_slice.check_record_ids(result)
