"""W7-T3 review fixes (#49): each configuration runs its real defense path, the
preflight checks defense behavior rather than the stored label, and the live
grid refuses until paid runs open.

D1_POLICY_GATE is enforcement and D2_DATAMARKING is behavioral guidance, so a
grid that records a baseline run under either label measures nothing. The
grid therefore runs through tool-result delivery, where the gate decides before
every dispatch and the transform marks every tool result.
"""

import json
from pathlib import Path

import pytest

from defenses.interfaces import DATAMARK_MARKER
from runner import grid_dev
from runner.mock_slice import EVENTS_FILE, RESULTS_FILE, read_jsonl

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "protocol" / "development_grid_spec.json"
CORPUS = ROOT / "corpus" / "development"


def _spec():
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def grid_run(tmp_path_factory):
    out = tmp_path_factory.mktemp("grid") / "run"
    grid_dev.run_mock_grid(out, spec=_spec(), corpus_root=CORPUS)
    return out


def _trials(run_dir):
    for results_path in sorted(Path(run_dir).glob(f"*/{RESULTS_FILE}")):
        (record,) = read_jsonl(results_path, "result")
        yield record, read_jsonl(results_path.parent / EVENTS_FILE, "event")


def test_every_grid_cell_runs_through_tool_result_delivery(grid_run):
    trials = list(_trials(grid_run))
    assert len(trials) == grid_dev.EXPECTED_TRIALS
    for record, events in trials:
        assert "tool_result_delivery" in events[0]["component_versions"], record["logical_trial_id"]


def test_the_grid_uses_delivery_s_audit_so_security_facts_are_known(grid_run):
    for record, _ in _trials(grid_run):
        assert record["tool_events"], record["logical_trial_id"]
        for tool_event in record["tool_events"]:
            assert tool_event["audit_decision"]["evaluator_version"], record["logical_trial_id"]
            assert tool_event["authorized"] is not None, record["logical_trial_id"]
        assert None not in record["security"].values(), record["logical_trial_id"]


def test_the_gate_decides_every_d1_dispatch_and_no_other(grid_run):
    for record, events in _trials(grid_run):
        decided = {e["payload"]["call_id"] for e in events if e["event_type"] == "authorization_decision"}
        dispatched = {e["payload"]["call_id"] for e in events if e["event_type"] == "tool_dispatch"}
        gate = "d1_policy_gate" in events[0]["component_versions"]
        if record["configuration"] == "D1_POLICY_GATE":
            assert gate and dispatched and dispatched <= decided, record["logical_trial_id"]
            assert all(t["gate_audit_match"] is not None for t in record["tool_events"]), record["logical_trial_id"]
        else:
            assert not gate and not decided, record["logical_trial_id"]


def test_datamarking_transforms_only_d2_deliveries(grid_run):
    for record, events in _trials(grid_run):
        started = events[0]["payload"]
        transformed = started["delivered_sha256"] != started["rendered_sha256"]
        results = [e["payload"] for e in events if e["event_type"] == "tool_result"]
        marked = any(DATAMARK_MARKER in json.dumps(r["observation"], ensure_ascii=False) for r in results)
        hashed = [r.get("unmarked_observation_sha256") for r in results]
        if record["configuration"] == "D2_DATAMARKING":
            assert transformed and marked and all(hashed), record["logical_trial_id"]
        else:
            assert not transformed and not marked and not any(hashed), record["logical_trial_id"]


def test_verify_accepts_the_mock_grid(grid_run):
    assert grid_dev.verify_grid_run(grid_run, _spec())["complete"] is True


def _trial_dir(run_dir, configuration):
    for results_path in sorted(Path(run_dir).glob(f"*/{RESULTS_FILE}")):
        (record,) = read_jsonl(results_path, "result")
        if record["configuration"] == configuration:
            return results_path.parent
    raise AssertionError(configuration)


def test_verify_rejects_a_d1_label_without_gate_decisions(grid_run, tmp_path):
    import shutil

    copy = tmp_path / "run"
    shutil.copytree(grid_run, copy)
    path = _trial_dir(copy, "D1_POLICY_GATE") / EVENTS_FILE
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for event in events:
        if event["event_type"] == "authorization_decision":
            event["payload"]["call_id"] = "not-the-dispatched-call"
    path.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    with pytest.raises(ValueError, match="D1_POLICY_GATE"):
        grid_dev.verify_grid_run(copy, _spec())


def _tamper(grid_run, tmp_path, configuration, edit_events=None, edit_record=None):
    import shutil

    copy = tmp_path / "run"
    shutil.copytree(grid_run, copy)
    trial_dir = _trial_dir(copy, configuration)
    if edit_events:
        path = trial_dir / EVENTS_FILE
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        edit_events(events)
        path.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
    if edit_record:
        path = trial_dir / RESULTS_FILE
        (record,) = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        edit_record(record)
        path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    return copy


def test_verify_rejects_a_d2_tool_result_that_was_never_marked(grid_run, tmp_path):
    def unmark(events):
        for event in events:
            if event["event_type"] == "tool_result":
                event["payload"].pop("unmarked_observation_sha256", None)

    with pytest.raises(ValueError, match="D2_DATAMARKING"):
        grid_dev.verify_grid_run(_tamper(grid_run, tmp_path, "D2_DATAMARKING", edit_events=unmark), _spec())


def test_verify_rejects_datamarked_content_under_d0(grid_run, tmp_path):
    def mark(events):
        for event in events:
            if event["event_type"] == "tool_result" and isinstance(event["payload"]["observation"].get("text"), str):
                event["payload"]["observation"]["text"] += DATAMARK_MARKER

    with pytest.raises(ValueError, match="D0_BASELINE"):
        grid_dev.verify_grid_run(_tamper(grid_run, tmp_path, "D0_BASELINE", edit_events=mark), _spec())


def test_verify_rejects_a_tool_call_without_an_audit_decision(grid_run, tmp_path):
    def drop_audit(record):
        record["tool_events"][0]["audit_decision"] = None

    with pytest.raises(ValueError, match="audit decision"):
        grid_dev.verify_grid_run(_tamper(grid_run, tmp_path, "D0_BASELINE", edit_record=drop_audit), _spec())


def test_live_cli_refuses_with_the_ack_and_a_clean_environment(monkeypatch, tmp_path):
    for name in list(__import__("os").environ):
        if name == "CI" or name.startswith(("ANTHROPIC_", "OPENAI_")):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("CANARY_PAID_RUN_ACK", "1")
    env_file = tmp_path / "never-read.env"
    with pytest.raises(ValueError, match="paid"):
        grid_dev.run_live_grid(tmp_path / "out", spec=_spec(), env_file=env_file, corpus_root=CORPUS)
    assert not env_file.exists() and not (tmp_path / "out").exists()


def test_live_grid_refuses_even_with_the_ack_and_a_clean_environment(monkeypatch):
    for name in list(__import__("os").environ):
        if name == "CI" or name.startswith(("ANTHROPIC_", "OPENAI_")):
            monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("CANARY_PAID_RUN_ACK", "1")
    reason = grid_dev.live_run_refusal(CORPUS, _spec())
    assert reason is not None
    assert "paid" in reason
