import json
import os
import re

import pytest
from jsonschema import ValidationError

from agent.loop import MAX_STEPS, run_loop
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
    assert trace.count(UNKNOWN) == 3
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


def test_trace_fits_width(run_dir):
    trace = render_trace(run_dir / mock_slice.EVENTS_FILE).splitlines()
    for line in trace:
        assert len(line) <= WIDTH, line
    start = trace.index("  TRACE:") + 1
    end = trace.index("  ILLUSTRATIVE — NOT STATISTICAL EVIDENCE")
    assert "".join(line.strip() for line in trace[start:end]) == mock_slice.LOGICAL_TRIAL_ID


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
