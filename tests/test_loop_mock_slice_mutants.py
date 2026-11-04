"""Agent-loop and mock-trial behaviour that mutation testing found unpinned
(reports/cloud/mutation.md). Each test names the surviving mutants it kills.
Everything here uses the mock provider."""

import json

import pytest

from agent.loop import response_text, run_loop
from runner import mock_slice
from runner.mock_provider import MockProvider

TASK = [{"role": "user", "content": "task"}]


class Recording(MockProvider):
    def __init__(self, script):
        super().__init__(script)
        self.seen = []

    def complete(self, messages, tool_schemas, decoding, model_request):
        self.seen.append((tool_schemas, decoding))
        return super().complete(messages, tool_schemas, decoding, model_request)


def _tool_use(call_id="toolu_1", path="docs/a.txt"):
    return {"stop_reason": "tool_use", "content": [
        {"type": "tool_use", "id": call_id, "name": "read_file", "input": {"path": path}}]}


END = {"stop_reason": "end_turn", "content": [{"type": "text", "text": "done"}]}


def test_text_blocks_join_with_nothing_between_them():
    # Kills x_response_text__mutmut_2: the final output is the provider's text exactly.
    raw = {"content": [{"type": "text", "text": "a"}, {"type": "tool_use"}, {"type": "text", "text": "b"}]}
    assert response_text(raw) == "ab"


def test_the_loop_passes_the_runner_s_tool_schemas_and_decoding():
    # Kills x_run_loop__mutmut_28 (tool schemas dropped before the provider call).
    provider = Recording([END])
    schemas = [{"name": "read_file"}]
    run_loop(provider, TASK, tool_schemas=schemas, decoding={"temperature": 0}, model_request={"model": "m"},
             on_attempt=lambda *a: None)
    assert provider.seen == [(schemas, {"temperature": 0})]


@pytest.mark.parametrize("text", [None, 5, ["a"]])
def test_a_text_block_without_string_text_is_malformed_output(text):
    # Kills x_run_loop__mutmut_100..105 (the text-block check keyed on the wrong field).
    raw = {"stop_reason": "end_turn", "content": [{"type": "text", "text": text}]}
    outcome = run_loop(MockProvider([raw]), TASK, tool_schemas=[], decoding={}, model_request={"model": "m"},
                       on_attempt=lambda *a: None)
    assert (outcome.termination_reason, outcome.final_text, outcome.steps_used) == ("malformed_model_output", None, 1)


@pytest.mark.parametrize("missing", ["dispatch", "on_tool"])
def test_a_tool_call_needs_both_a_dispatcher_and_a_tool_recorder(missing):
    # Kills x_run_loop__mutmut_121 (`or` -> `and`).
    hooks = {"dispatch": lambda request: {"ok": True}, "on_tool": lambda *a: None}
    hooks[missing] = None
    outcome = run_loop(MockProvider([_tool_use(), END]), TASK, tool_schemas=[], decoding={},
                       model_request={"model": "m"}, on_attempt=lambda *a: None, **hooks)
    assert outcome.termination_reason == "malformed_model_output"


def test_a_tool_request_carries_the_trial_s_call_id_and_the_default_read_oracle():
    # Kills x_run_loop__mutmut_1/2/134 (call IDs built without the trial ID) and _274..277
    # (the default effect record).
    events = []
    outcome = run_loop(MockProvider([_tool_use(), END]), TASK, tool_schemas=[], decoding={},
                       model_request={"model": "m"}, on_attempt=lambda *a: None,
                       dispatch=lambda request: {"ok": True, "text": "x"},
                       on_tool=lambda kind, payload: events.append((kind, payload)))
    assert outcome.termination_reason == "final_answer"
    assert events[0][0] == "tool_requested" and events[0][1]["call_id"] == "mock:step1:call1"
    assert events[1] == ("effect_observation", {"call_id": "mock:step1:call1", "step": 1, "effect_observed": True,
                                                "effect_oracle_id": "read-returned-v0.1.0"})
    events.clear()
    run_loop(MockProvider([_tool_use(), END]), TASK, tool_schemas=[], decoding={}, model_request={"model": "m"},
             on_attempt=lambda *a: None, logical_trial_id="trial-9", dispatch=lambda request: {"ok": False},
             on_tool=lambda kind, payload: events.append((kind, payload)))
    assert events[0][1]["call_id"] == "trial-9:step1:call1"
    assert events[1][1]["effect_observed"] is False


def test_a_content_filtered_tool_call_is_recorded_with_its_trial_and_step():
    # Kills x_run_loop__mutmut_185/186.
    events, dispatched = [], []
    filtered = {"stop_reason": "content_filter", "content": [
        {"type": "text", "text": "partial"},
        {"type": "tool_use", "id": "toolu_9", "name": "read_file", "input": {"path": "docs/a.txt"}}]}
    cut_off = {"stop_reason": "max_tokens", "content": []}
    outcome = run_loop(MockProvider([cut_off, filtered]), TASK,
                       tool_schemas=[], decoding={}, model_request={"model": "m"}, on_attempt=lambda *a: None,
                       logical_trial_id="trial-3", dispatch=dispatched.append,
                       on_tool=lambda kind, payload: events.append((kind, payload)))
    assert (outcome.termination_reason, outcome.final_text, outcome.steps_used) == ("provider_content_filter", "partial", 2)
    assert dispatched == []
    assert [(kind, payload["call_id"], payload["step"]) for kind, payload in events] == [
        ("tool_requested", "trial-3:step2:call1", 2)]


# --- the mock trial's recorded run metadata -------------------------------------


@pytest.fixture
def mock_run(tmp_path):
    out = mock_slice.run_mock_trial(tmp_path / "run", clock=lambda: "2026-11-04T00:00:00Z")
    events = mock_slice.read_jsonl(out / mock_slice.EVENTS_FILE, "event")
    [record] = mock_slice.read_jsonl(out / mock_slice.RESULTS_FILE, "result")
    return out, events, record


def test_the_mock_result_records_its_decoding_prompt_and_output_hashes(mock_run):
    # Kills x_assemble_result__mutmut_147..162 (temperature, top_p) and _292
    # (final_output_sha256), and x_run_mock_trial__mutmut_20..42 (the prompt hash
    # over the messages actually sent).
    _, events, record = mock_run
    meta = record["run_metadata"]
    assert (meta["temperature"], meta["top_p"]) == (0, 1)
    messages = [{"role": "system", "content": mock_slice.SYSTEM_PROMPT},
                {"role": "user", "content": mock_slice.TASK_PROMPT}]
    assert meta["prompt_hash"] == mock_slice.sha256_json(messages)
    assert record["final_output_sha256"] == mock_slice.sha256_text(record["final_output"])
    started = events[0]["payload"]
    assert started["tier"] is None and "tier" in started


def test_each_attempt_records_the_hash_of_its_raw_response(mock_run):
    # Kills x_run_mock_trial__mutmut_54/95.
    _, events, record = mock_run
    attempts = [e for e in events if e["event_type"] == "provider_attempt"]
    assert attempts
    for event in attempts:
        assert event["payload"]["raw_response"] is not None
        assert event["raw_evidence"]["sha256"] == mock_slice.sha256_json(event["payload"]["raw_response"])
    assert [c["raw_response_sha256"] for c in record["model_calls"]] == [
        e["raw_evidence"]["sha256"] for e in attempts if e["payload"]["outcome"] == "model_response"]


def test_a_run_directory_must_be_new(mock_run):
    # Kills x_run_mock_trial__mutmut_9 (exist_ok=True).
    out, _, _ = mock_run
    with pytest.raises(FileExistsError):
        mock_slice.run_mock_trial(out)


def test_results_lines_are_sorted_compact_utf8_json(tmp_path):
    # Kills x_append_jsonl__mutmut_11..20: the stored line is the canonical serialization
    # a reader and a hash see.
    path = tmp_path / "events.jsonl"
    log = mock_slice.EventLog(path, lambda: "2026-11-04T00:00:00Z")
    log.append("trial_started", {"task_prompt": "café", "zeta": 1, "alpha": 2})
    line = path.read_bytes()
    record = json.loads(line)
    assert line == (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    assert "café".encode("utf-8") in line
