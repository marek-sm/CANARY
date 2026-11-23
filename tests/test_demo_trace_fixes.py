"""WT-11, WT-12, WT-13, N-66-1, N-66-2, and N-66-4: the stage trace reports what the record says.

Each test copies the staged mock trial into tmp_path and changes it schema-validly.
Nothing here reads results/ or any official run.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from demo import trace
from demo.trace import UNKNOWN, WIDTH, render_trace

ROOT = Path(__file__).resolve().parents[1]
STAGED_RUN = ROOT / "demo" / "recorded" / "w7-t5"
STAGED = STAGED_RUN / "t0000_dev-001_C2_attack_D0_BASELINE_r1"


def _lines(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")


@pytest.fixture
def trial(tmp_path):
    out = tmp_path / STAGED.name
    shutil.copytree(STAGED, out)
    return out


def _edit_events(trial: Path, edit) -> Path:
    path = trial / "events.jsonl"
    events = _lines(path)
    _write(path, edit(events))
    return path


def _edit_result(trial: Path, edit) -> None:
    path = trial / "results.jsonl"
    records = _lines(path)
    edit(records[-1])
    _write(path, records)


def _with_gate(events: list[dict], gate_decision) -> list[dict]:
    """Insert a D1 gate record, as runner/delivery.py writes it, after the tool request."""
    index = next(i for i, e in enumerate(events) if e["event_type"] == "tool_requested")
    request = events[index]
    gate = {
        **request,
        "event_id": request["event_id"] + "-gate",
        "event_type": "authorization_decision",
        "payload": {
            "call_id": request["payload"]["call_id"],
            "tool": request["payload"]["tool"],
            "step": request["payload"]["step"],
            "gate_action": "block" if gate_decision and not gate_decision["authorized"] else "dispatch",
            "gate_decision": gate_decision,
        },
        "raw_evidence": {"sha256": None, "artifact_ref": None},
    }
    events = events[: index + 1] + [gate] + events[index + 1 :]
    for sequence, event in enumerate(events, start=1):
        event["sequence"] = sequence
    return events


@pytest.mark.parametrize("authorized,label", [(False, "UNAUTHORIZED"), (True, "AUTHORIZED")])
def test_wt11_the_gate_decision_is_read_from_the_gate_record(trial, authorized, label):
    decision = {"authorized": authorized, "reason_codes": [], "evaluator_version": "v"}
    events = _edit_events(trial, lambda ev: _with_gate(ev, decision))
    text = render_trace(events)
    gate_line = next(line for line in text.splitlines() if "UNAUTHORIZED" in line or "AUTHORIZ" in line)
    assert label in gate_line and "UNKNOWN" not in gate_line


def test_wt11_a_gate_with_no_decision_stays_unknown(trial):
    events = _edit_events(trial, lambda ev: _with_gate(ev, None))
    assert "AUTHORIZATION: NO EVIDENCE / UNKNOWN" in render_trace(events)


def test_wt12_a_null_stop_reason_renders(trial):
    def edit(events):
        attempt = next(e for e in events if e["event_type"] == "provider_attempt")
        attempt["payload"]["raw_response"]["stop_reason"] = None
        return events

    assert "STOP: UNKNOWN" in render_trace(_edit_events(trial, edit))


def test_wt13_cut_off_replies_are_shown_when_disclosure_scans_them(trial):
    def edit(events):
        ended = next(e for e in events if e["event_type"] == "trial_ended")
        ended["payload"]["cut_off_text"] = "partial reply that names CANARY-feedfacefeedface"
        return events

    text = render_trace(_edit_events(trial, edit))
    assert "CUT-OFF REPLIES" in text
    assert "CANARY-feedfacefeedface" in text


def test_n66_1_the_provider_is_the_recorded_adapter(trial):
    text = render_trace(trial / "events.jsonl")
    assert "PROVIDER: MOCK (mock-provider-v0)" in text

    def edit(events):
        for event in events:
            event["component_versions"]["provider_adapter"] = "anthropic-messages-adapter-v0.1.2"
        return events

    text = render_trace(_edit_events(trial, edit))
    assert "PROVIDER: anthropic-messages-adapter-v0.1.2" in text
    assert "MOCK" not in text.split("CONFIGURATION:")[0].replace("MODEL REQUESTED", "")


@pytest.mark.parametrize(
    "split,role,label",
    [
        ("development", None, "DEVELOPMENT / EXCLUDED"),
        ("development", "demo_rehearsal", "DEMO / EXCLUDED"),
        ("evaluation", "primary_indirect", "EVALUATION"),
    ],
)
def test_n66_1_the_case_label_follows_the_record(trial, split, role, label):
    def edit(result):
        result["split"], result["analysis_role"] = split, role
        if split == "evaluation":
            result["protocol_version"] = "1.0.0"
            result["comparison_superblock_id"] = result["comparison_superblock_id"] or "sb"

    _edit_result(trial, edit)
    text = render_trace(trial / "events.jsonl")
    assert f"({label})" in text
    assert "dev-001:C2:attack" in text
    assert "CASE: MOCK / EXCLUDED" not in text


def test_n66_1_no_result_means_an_unknown_case(trial):
    (trial / "results.jsonl").unlink()
    assert f"CASE: {UNKNOWN}" in render_trace(trial / "events.jsonl")


def test_n66_2_the_trace_shows_its_code_and_configuration_hashes(trial):
    text = render_trace(trial / "events.jsonl")
    result = _lines(trial / "results.jsonl")[-1]
    metadata = result["run_metadata"]
    flat = text.replace("\n  ", "")
    assert metadata["code_commit"] in flat
    assert metadata["prompt_hash"][:12] in text
    assert metadata["corpus_hash"][:12] in text
    assert "DEFENSE: NOT RECORDED" in text  # null in the staged record


def test_every_line_fits_the_stage_width(trial):
    def edit(events):
        events = _with_gate(events, {"authorized": False, "reason_codes": [], "evaluator_version": "v"})
        ended = next(e for e in events if e["event_type"] == "trial_ended")
        ended["payload"]["cut_off_text"] = "word " * 40
        return events

    text = render_trace(_edit_events(trial, edit))
    assert all(len(line) <= WIDTH for line in text.splitlines()), [l for l in text.splitlines() if len(l) > WIDTH]


def test_n66_4_the_make_replay_path_renders_with_the_new_labels(capsys):
    """`make replay` runs `python3 -m demo.trace demo/recorded/w7-t5` (Makefile)."""
    assert trace.main([str(STAGED_RUN)]) == 0
    out = capsys.readouterr().out
    assert "PROVIDER: MOCK (mock-provider-v0)" in out
    assert "(DEVELOPMENT / EXCLUDED)" in out
    assert "CODE:" in out
