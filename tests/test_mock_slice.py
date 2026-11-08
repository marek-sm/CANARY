import json
import os
import re
import socket

import pytest
from jsonschema import ValidationError

from agent.loop import CONTINUATION_PROMPT, MAX_STEPS, run_loop
from demo.trace import UNKNOWN, WIDTH, render_trace
from runner import mock_slice
from runner.mock_provider import MockProvider

CREDENTIAL_PATTERN = re.compile(
    r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|ANTHROPIC|OPENAI|AWS_|AZURE_|GOOGLE_|GEMINI",
    re.IGNORECASE,
)
SENTINEL = "sentinel-credential-must-not-appear"
SECURITY_FIELDS = (
    "unauthorized_user_disclosure",
    "proposed_egress",
    "external_exfiltration",
    "unauthorized_action_requested",
    "unauthorized_action_dispatched",
    "unauthorized_action_effect",
    "model_violation",
    "system_compromise",
)


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def run_dir(tmp_path):
    return mock_slice.run_mock_trial(tmp_path / "run")


def test_slice_runs_to_final_answer(run_dir):
    events = lines(run_dir / mock_slice.EVENTS_FILE)
    (result,) = lines(run_dir / mock_slice.RESULTS_FILE)

    assert [e["event_type"] for e in events] == [
        "trial_started",
        "provider_attempt",
        "provider_attempt",
        "final_output",
        "trial_ended",
    ]
    assert [e["sequence"] for e in events] == list(range(1, len(events) + 1))
    assert result["configuration"] == "D0_BASELINE"
    assert result["status"] == "completed"
    assert result["termination_reason"] == "final_answer"
    assert result["final_output"].startswith("The fictional note lists two follow-ups")


def test_every_record_validates(run_dir):
    events = lines(run_dir / mock_slice.EVENTS_FILE)
    results = lines(run_dir / mock_slice.RESULTS_FILE)
    for event in events:
        mock_slice.validator("event").validate(event)
    for result in results:
        mock_slice.validator("result").validate(result)

    ids = [e["event_id"] for e in events]
    assert len(ids) == len(set(ids))
    (result,) = results
    for attempt in result["attempts"]:
        assert attempt["model_call_id"] == f"{result['logical_trial_id']}:step{attempt['step']}"
        assert attempt["attempt_id"] == f"{attempt['model_call_id']}:a{attempt['attempt_index']}"


def test_unknown_endpoints_stay_null(run_dir):
    (result,) = lines(run_dir / mock_slice.RESULTS_FILE)
    for field in SECURITY_FIELDS:
        assert result["security"][field] is None, field
    assert result["utility"]["pass"] is None
    assert result["display_label"] is None

    trace = render_trace(run_dir / mock_slice.EVENTS_FILE)
    assert trace.count(UNKNOWN) == 4
    assert "FALSE" not in trace


def test_three_valued_or():
    assert mock_slice.or3(None, None, None) is None
    assert mock_slice.or3(False, None, False) is None
    assert mock_slice.or3(False, False, False) is False
    assert mock_slice.or3(None, True, False) is True


def test_events_are_durable_before_next_step(tmp_path):
    events_path = tmp_path / "run" / mock_slice.EVENTS_FILE
    seen_before_call = []

    class Watching(MockProvider):
        def complete(self, *args, **kwargs):
            seen_before_call.append([e["event_type"] for e in lines(events_path)])
            return super().complete(*args, **kwargs)

    mock_slice.run_mock_trial(tmp_path / "run", provider=Watching())
    assert seen_before_call == [
        ["trial_started"],
        ["trial_started", "provider_attempt"],
    ]


def test_mock_trace_is_byte_identical_across_two_fixed_clock_runs(tmp_path):
    """BLOCKER1: the W5-T3 refactor makes six_cell reuse mock_slice's EventLog and
    assemble_result, so the mock trace itself must stay unchanged. With a fixed
    clock two independent runs produce byte-identical events.jsonl and
    results.jsonl, pinning the mock trace against a silent regression."""
    clock = lambda: "2020-01-01T00:00:00Z"  # noqa: E731 - deterministic test clock
    a = mock_slice.run_mock_trial(tmp_path / "a", clock=clock)
    b = mock_slice.run_mock_trial(tmp_path / "b", clock=clock)
    assert (a / mock_slice.EVENTS_FILE).read_bytes() == (b / mock_slice.EVENTS_FILE).read_bytes()
    assert (a / mock_slice.RESULTS_FILE).read_bytes() == (b / mock_slice.RESULTS_FILE).read_bytes()


def test_invalid_record_is_rejected_before_write(tmp_path):
    path = tmp_path / "events.jsonl"
    log = mock_slice.EventLog(path, mock_slice.utc_now)
    log.append("trial_started", {})
    with pytest.raises(ValidationError):
        log.append("final_output", {"text": "missing hash"})
    assert len(lines(path)) == 1


def test_refuses_to_overwrite_existing_run(run_dir):
    with pytest.raises(FileExistsError):
        mock_slice.run_mock_trial(run_dir)


@pytest.mark.parametrize("bad", ["D0", "D1", "D2", "d0_baseline"])
def test_configuration_enum_rejects_aliases(run_dir, bad):
    (result,) = lines(run_dir / mock_slice.RESULTS_FILE)
    result["configuration"] = bad
    with pytest.raises(ValidationError):
        mock_slice.validator("result").validate(result)


@pytest.mark.parametrize("bad", ["unknown", 0, "false"])
def test_security_fact_must_be_boolean_or_null(run_dir, bad):
    (result,) = lines(run_dir / mock_slice.RESULTS_FILE)
    result["security"]["proposed_egress"] = bad
    with pytest.raises(ValidationError):
        mock_slice.validator("result").validate(result)


def test_loop_stops_at_step_limit():
    script = [{"stop_reason": "max_tokens", "content": [{"type": "text", "text": "..."}]}] * (
        MAX_STEPS + 1
    )
    provider = MockProvider(script)
    steps = []
    outcome = run_loop(
        provider,
        [{"role": "user", "content": "x"}],
        tool_schemas=[],
        decoding={},
        model_request={"model": "mock"},
        on_attempt=lambda step, attempt, response: steps.append(step),
    )
    assert outcome.termination_reason == "max_steps"
    assert outcome.final_text is None
    assert steps == list(range(1, MAX_STEPS + 1))
    assert provider.calls == MAX_STEPS


class RecordingProvider(MockProvider):
    def __init__(self, script):
        super().__init__(script)
        self.seen = []

    def complete(self, messages, *args):
        self.seen.append([dict(m) for m in messages])
        return super().complete(messages, *args)


def test_output_limit_stop_continues_with_a_user_turn():
    # Some providers reject a conversation that ends with an assistant turn, so a
    # max_tokens stop is followed by a fixed user turn (decision 0010).
    provider = RecordingProvider([
        {"stop_reason": "max_tokens", "content": [{"type": "text", "text": "partial"}]},
        {"stop_reason": "max_tokens", "content": []},
        {"stop_reason": "end_turn", "content": [{"type": "text", "text": "done"}]},
    ])
    outcome = run_loop(provider, [{"role": "user", "content": "x"}], tool_schemas=[], decoding={},
                       model_request={"model": "mock"}, on_attempt=lambda *a: None)
    assert outcome.termination_reason == "final_answer" and outcome.final_text == "done"
    assert provider.seen[1] == [{"role": "user", "content": "x"}, {"role": "assistant", "content": "partial"},
                                {"role": "user", "content": CONTINUATION_PROMPT}]
    # An empty cut-off reply adds no empty assistant turn.
    assert provider.seen[2] == provider.seen[1] + [{"role": "user", "content": CONTINUATION_PROMPT}]


def test_trace_fits_width(run_dir):
    trace = render_trace(run_dir / mock_slice.EVENTS_FILE).splitlines()
    for line in trace:
        assert len(line) <= WIDTH, line
    start = trace.index("  TRACE:") + 1
    end = trace.index("  ILLUSTRATIVE — NOT STATISTICAL EVIDENCE")
    assert "".join(line.strip() for line in trace[start:end]) == mock_slice.LOGICAL_TRIAL_ID


def test_trace_has_accessible_evidence_regions(run_dir):
    trace = render_trace(run_dir / mock_slice.EVENTS_FILE)
    required_text = (
        "CANARY  |  RECORDED TRACE",
        "TIER: NOT SELECTED",
        f"MODEL REQUESTED: {mock_slice.MOCK_MODEL_ID}",
        f"MODEL RESOLVED: {mock_slice.MOCK_MODEL_ID}",
        "PROVIDER: MOCK",
        "CASE: MOCK / EXCLUDED",
        "CONFIGURATION: D0_BASELINE",
        "TRUSTED TASK",
        "UNTRUSTED DATA",
        "EVENT TIMELINE",
        "FINAL OUTPUT",
        "MODEL VIOLATION",
        "SYSTEM COMPROMISE",
        "UTILITY",
        "DISPLAY LABEL",
        "PROTOCOL: NOT FROZEN",
        "TRACE:",
        "ILLUSTRATIVE — NOT STATISTICAL EVIDENCE",
    )
    for text in required_text:
        assert text in trace

    assert "\N{ESCAPE}[" not in trace
    for unsupported_shortcut in ("SAFE", "SECURE", "ATTACK PREVENTED", "DEFENSE SUCCEEDED"):
        assert unsupported_shortcut not in trace


def test_trace_keeps_outcomes_separate_without_result_record(run_dir):
    (run_dir / mock_slice.RESULTS_FILE).unlink()

    trace = render_trace(run_dir / mock_slice.EVENTS_FILE)

    assert trace.count(UNKNOWN) == 4
    assert "MODEL VIOLATION" in trace
    assert "SYSTEM COMPROMISE" in trace
    assert "UTILITY" in trace


def test_mock_trace_needs_no_network(tmp_path, monkeypatch):
    def block_network(*args, **kwargs):
        raise AssertionError("mock trace attempted network access")

    monkeypatch.setattr(socket, "socket", block_network)
    monkeypatch.setattr(socket, "create_connection", block_network)

    out = mock_slice.run_mock_trial(tmp_path / "run")
    trace = render_trace(out / mock_slice.EVENTS_FILE)

    assert "RECORDED TRACE" in trace


class RecordingEnviron(dict):
    """Stand-in for os.environ that records every key looked up."""

    def __init__(self, data):
        super().__init__(data)
        self.accessed = set()

    def __getitem__(self, key):
        self.accessed.add(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        self.accessed.add(key)
        return super().get(key, default)

    def __contains__(self, key):
        self.accessed.add(key)
        return super().__contains__(key)

    def copy(self):
        self.accessed.add("<copy>")
        return dict(self)

    def items(self):
        self.accessed.add("<items>")
        return super().items()


def test_no_provider_credential_is_read(tmp_path, monkeypatch):
    fake = {
        "PATH": os.environ.get("PATH", ""),
        "ANTHROPIC_API_KEY": SENTINEL,
        "OPENAI_API_KEY": SENTINEL,
        "PROVIDER_TOKEN": SENTINEL,
    }
    env = RecordingEnviron(fake)
    monkeypatch.setattr(os, "environ", env)

    out = mock_slice.run_mock_trial(tmp_path / "run")
    trace = render_trace(out / mock_slice.EVENTS_FILE)

    credential_reads = {k for k in env.accessed if CREDENTIAL_PATTERN.search(k)}
    assert credential_reads == set()
    assert "<copy>" not in env.accessed and "<items>" not in env.accessed
    for path in out.iterdir():
        assert SENTINEL not in path.read_text(encoding="utf-8")
    assert SENTINEL not in trace


# Result derivation from stored attempts --------------------------------------


class Scripted(MockProvider):
    """Provider records shaped like the real adapters', with usage and latency.

    A test double, so it is a ``MockProvider``: the paid-run gate (decision 0023)
    refuses any provider that isn't one."""

    adapter_version = "scripted-test"

    def __init__(self, *records):
        self.records = list(records)
        self.calls = 0

    def complete(self, messages, tool_schemas, decoding, model_request):
        return dict(self.records.pop(0), model_requested=model_request["model"])


def reply(stop="end_turn", model="dev-model-2026-01", usage=(100, 10), latency=250):
    tokens = {"input_tokens": usage[0], "output_tokens": usage[1]} if usage else {"input_tokens": None, "output_tokens": None}
    return {"outcome": "model_response", "provider_request_id": "req", "model_resolved": model, "provider_fingerprint": None,
            "raw_response": {"stop_reason": stop, "content": [{"type": "text", "text": "{}"}]}, "usage": tokens,
            "provider_response": {"stub": True}, "requested_at": None, "completed_at": None, "latency_ms": latency, "error": None}


def no_content():
    return {"outcome": "no_model_content", "provider_request_id": None, "model_resolved": None, "provider_fingerprint": None,
            "raw_response": None, "usage": {"input_tokens": None, "output_tokens": None}, "provider_response": None,
            "requested_at": None, "completed_at": None, "latency_ms": 5, "error": {"type": "APITimeoutError", "status": None}}


def ticket_result(tmp_path, provider):
    from runner import ticket_slice

    out = ticket_slice.run(tmp_path / "run", provider, model="dev-model", decoding={}, experiment_id="dev-test")
    (result,) = lines(out / mock_slice.RESULTS_FILE)
    return result


def test_exhausted_retries_end_the_trial_as_an_infrastructure_failure(tmp_path):
    out = mock_slice.run_mock_trial(tmp_path / "run", provider=Scripted(no_content(), no_content(), no_content()))
    (result,) = lines(out / mock_slice.RESULTS_FILE)
    assert (result["status"], result["termination_reason"]) == ("infrastructure_failure", "infrastructure_failure")


def test_resolved_model_survives_an_outage_at_the_last_step(tmp_path):
    result = ticket_result(tmp_path, Scripted(reply("max_tokens"), no_content(), no_content(), no_content()))
    assert result["termination_reason"] == "infrastructure_failure"
    assert result["run_metadata"]["model_resolved"] == "dev-model-2026-01"


def test_conflicting_resolved_models_are_not_collapsed_to_one(tmp_path):
    result = ticket_result(tmp_path, Scripted(reply("max_tokens"), reply(model="dev-model-2026-02")))
    assert result["run_metadata"]["model_resolved"] is None
    assert [c["model_resolved"] for c in result["model_calls"]] == ["dev-model-2026-01", "dev-model-2026-02"]


def test_usage_is_summed_from_the_recorded_attempts(tmp_path):
    result = ticket_result(tmp_path, Scripted(reply("max_tokens", usage=(100, 10)), reply(usage=(200, 20))))
    assert result["usage"] == {"provider_requests": 2, "input_tokens": 300, "output_tokens": 30, "latency_ms": 500}


def test_usage_is_unknown_when_any_attempt_is(tmp_path):
    result = ticket_result(tmp_path, Scripted(no_content(), reply()))
    assert result["usage"] == {"provider_requests": 2, "input_tokens": None, "output_tokens": None, "latency_ms": 255}


# Append durability ------------------------------------------------------------


def final_output(text="x"):
    return {"text": text, "text_sha256": mock_slice.sha256_text(text)}


def test_a_failed_append_leaves_the_trace_unchanged_and_no_sequence_gap(tmp_path, monkeypatch):
    path = tmp_path / "events.jsonl"
    log = mock_slice.EventLog(path, mock_slice.utc_now)
    log.append("trial_started", {})
    before = path.read_bytes()
    real_fsync = os.fsync

    def disk_full(fd):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(mock_slice.os, "fsync", disk_full)
    with pytest.raises(OSError):
        log.append("final_output", final_output())
    assert path.read_bytes() == before
    monkeypatch.setattr(mock_slice.os, "fsync", real_fsync)
    log.append("final_output", final_output())
    assert [e["sequence"] for e in lines(path)] == [1, 2]


def test_a_partial_write_is_rolled_back(tmp_path, monkeypatch):
    path = tmp_path / "events.jsonl"
    log = mock_slice.EventLog(path, mock_slice.utc_now)
    log.append("trial_started", {})
    before = path.read_bytes()
    real_write = os.write

    def short_then_fail(fd, data):
        real_write(fd, bytes(data[:10]))
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(mock_slice.os, "write", short_then_fail)
    with pytest.raises(OSError):
        log.append("final_output", final_output())
    assert path.read_bytes() == before


def test_short_writes_still_append_the_whole_line(tmp_path, monkeypatch):
    path = tmp_path / "events.jsonl"
    real_write = os.write
    monkeypatch.setattr(mock_slice.os, "write", lambda fd, data: real_write(fd, bytes(data[:10])))
    log = mock_slice.EventLog(path, mock_slice.utc_now)
    log.append("trial_started", {})
    log.append("final_output", final_output())
    assert [e["sequence"] for e in lines(path)] == [1, 2]


def test_every_append_is_fsynced(tmp_path, monkeypatch):
    synced = []
    real_fsync = os.fsync
    monkeypatch.setattr(mock_slice.os, "fsync", lambda fd: (synced.append(fd), real_fsync(fd)))
    out = mock_slice.run_mock_trial(tmp_path / "run")
    appended = len(lines(out / mock_slice.EVENTS_FILE)) + len(lines(out / mock_slice.RESULTS_FILE))
    assert len(synced) == appended


def test_reading_a_trace_back_rejects_a_schema_invalid_line(run_dir):
    path = run_dir / mock_slice.EVENTS_FILE
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"event_type": "trial_ended"}) + "\n")
    with pytest.raises(ValidationError):
        mock_slice.read_jsonl(path, "event")
