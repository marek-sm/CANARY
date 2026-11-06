"""The run-wide stop rule (decision 0029): a run that hits a failure every later trial
would also hit stops, and verification doesn't call it complete.

Two signals stop a run. A provider attempt that fails the same way for every trial
(an HTTP 4xx other than 408 and 429 that isn't a listed content-policy refusal, or a
connection error) stops it at once, before that trial ends, so a resume after the
fix continues the trial and loses nothing. Two trials in a row ending as
infrastructure failures, whatever the cause, stop it after the second.
"""

import json

import pytest

from runner import execute, grid_dev, paid_run
from runner import schedule as sched
from runner.mock_slice import EVENTS_FILE, RESULTS_FILE, read_jsonl

FIXED_CLOCK = lambda: "2020-01-01T00:00:00Z"  # noqa: E731
COMMIT = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"


@pytest.fixture(autouse=True)
def doubles_are_not_paid(monkeypatch):
    monkeypatch.setattr(paid_run, "is_paid", lambda provider: False)


def _answer(model_request, n):
    return {"outcome": "model_response", "provider_request_id": f"req-{n}", "model_requested": model_request["model"],
            "model_resolved": model_request["model"], "provider_fingerprint": None,
            "raw_response": {"stop_reason": "end_turn", "content": [{"type": "text", "text": "Done."}]}}


def _failure(model_request, error):
    return {"outcome": "no_model_content", "provider_request_id": None, "model_requested": model_request["model"],
            "model_resolved": None, "provider_fingerprint": None, "raw_response": None, "error": error}


class Scripted:
    """Stateless: each call takes the next item from ``errors`` while any remain (``None``
    answers), then answers, or fails with ``forever`` when it's set."""

    adapter_version = "test-scripted-v0"

    def __init__(self, errors=(), forever=None):
        self.errors, self.forever, self.calls = list(errors), forever, 0

    def complete(self, messages, tool_schemas, decoding, model_request):
        self.calls += 1
        if self.errors:
            error = self.errors.pop(0)
            return _answer(model_request, self.calls) if error is None else _failure(model_request, error)
        if self.forever is not None:
            return _failure(model_request, self.forever)
        return _answer(model_request, self.calls)


DEAD_KEY = {"type": "AuthenticationError", "status": 401, "provider_code": None, "provider_type": "authentication_error"}
NO_NETWORK = {"type": "APIConnectionError", "status": None}
TIMEOUT = {"type": "APITimeoutError", "status": None}
RATE_LIMIT = {"type": "RateLimitError", "status": 429, "provider_code": None, "provider_type": "rate_limit_error"}


def _schedule():
    return sched.generate_schedule(execute.default_dev_spec("exp-stop", seed="sd"))


def _run(out, schedule, provider, *, resume=False):
    tokens = iter(["a1a1a1a1", "b2b2b2b2"])
    return execute.run_schedule(out, schedule, clock=FIXED_CLOCK, provider_factory=lambda t, c: provider,
                                canary_factory=lambda: next(tokens), code_commit_value=COMMIT, resume=resume)


def _started(out, schedule):
    return [t for t in schedule if (out / execute.trial_slug(t)).exists()]


def _result(out, trial):
    path = out / execute.trial_slug(trial) / RESULTS_FILE
    return read_jsonl(path, "result")[0] if path.exists() else None


def _stops(out):
    lines = [json.loads(line) for line in (out / paid_run.PROVENANCE_FILE).read_text(encoding="utf-8").splitlines()]
    return [line["run_wide_stop"] for line in lines if line["phase"] == "stop"]


@pytest.mark.parametrize("error", [DEAD_KEY, NO_NETWORK], ids=["dead-key", "no-network"])
def test_a_run_wide_provider_failure_stops_before_the_trial_ends(tmp_path, error):
    out, schedule = tmp_path / "run", _schedule()
    with pytest.raises(execute.RunWideFailure):
        _run(out, schedule, Scripted(forever=error))
    (first,) = _started(out, schedule)  # nothing after the stop
    events = read_jsonl(out / execute.trial_slug(first) / EVENTS_FILE, "event")
    assert "trial_ended" not in [e["event_type"] for e in events]  # left open for the resume
    assert [e["payload"]["error"] for e in events if e["event_type"] == "provider_attempt"] == [error]
    assert _result(out, first) is None
    (stop,) = _stops(out)
    assert stop["logical_trial_id"] == first.logical_trial_id and stop["rule"] == "run_wide_provider_error"


def test_a_resume_after_the_fix_loses_no_trial(tmp_path):
    out, schedule = tmp_path / "run", _schedule()
    with pytest.raises(execute.RunWideFailure):
        _run(out, schedule, Scripted(forever=DEAD_KEY))
    _run(out, schedule, Scripted(), resume=True)
    assert all(_result(out, t)["status"] == "completed" for t in schedule)
    first = schedule[0]
    attempts = [e["payload"] for e in read_jsonl(out / execute.trial_slug(first) / EVENTS_FILE, "event")
                if e["event_type"] == "provider_attempt"]
    # The stopped attempt stays in the trace, and the resume made the step's first retry.
    assert [(a["attempt_index"], a["outcome"]) for a in attempts] == [(1, "no_model_content"), (2, "model_response")]
    assert _stops(out)[-1] is None


def test_two_infrastructure_failures_in_a_row_stop_the_run(tmp_path):
    out, schedule = tmp_path / "run", _schedule()
    with pytest.raises(execute.RunWideFailure):
        _run(out, schedule, Scripted(forever=TIMEOUT))
    started = _started(out, schedule)
    assert started == schedule[:2]
    assert [_result(out, t)["status"] for t in started] == ["infrastructure_failure"] * 2
    (stop,) = _stops(out)
    assert stop["rule"] == "consecutive_infrastructure_failures"
    assert stop["logical_trial_ids"] == [t.logical_trial_id for t in started]
    _run(out, schedule, Scripted(), resume=True)
    assert [_result(out, t)["status"] for t in schedule] == ["infrastructure_failure"] * 2 + ["completed"] * 4


def test_a_retried_rate_limit_or_one_failed_trial_doesnt_stop_the_run(tmp_path):
    out, schedule = tmp_path / "run", _schedule()
    # The first trial's step: a 429, then an answer. The second trial: three timeouts, an
    # infrastructure failure. Every later trial answers, so no two failures are consecutive.
    _run(out, schedule, Scripted(errors=[RATE_LIMIT, None, TIMEOUT, TIMEOUT, TIMEOUT]))
    assert [_result(out, t)["status"] for t in schedule] == ["completed", "infrastructure_failure"] + ["completed"] * 4
    assert _stops(out) == [None]


def test_verify_doesnt_call_a_stopped_run_complete(tmp_path, monkeypatch):
    """The last trial's failure completes the schedule and stops the run: every trial
    has a result, and verify still says the run isn't complete until a resume ends
    without a stop."""
    out, schedule = tmp_path / "run", _schedule()
    _run(out, schedule[:4], Scripted())
    with pytest.raises(execute.RunWideFailure):
        _run(out, schedule, Scripted(forever=TIMEOUT), resume=True)
    assert all(_result(out, t) is not None for t in schedule)
    stops = grid_dev.run_wide_stops(out)
    assert [s["rule"] for s in stops] == ["consecutive_infrastructure_failures"]
    assert grid_dev.stopped_unresolved(out) is True
    _run(out, schedule, Scripted(), resume=True)
    assert grid_dev.stopped_unresolved(out) is False


def test_a_dead_key_doesnt_run_through_the_schedule(tmp_path):
    """The audit's finding, stated without the rule's names: a dead key used to run
    every trial into an infrastructure failure, each counting toward the ceiling."""
    out, schedule = tmp_path / "run", _schedule()
    try:
        _run(out, schedule, Scripted(forever=DEAD_KEY))
    except Exception:
        pass
    assert len(_started(out, schedule)) == 1
    assert _result(out, schedule[0]) is None


@pytest.mark.parametrize("response, stops", [
    (_failure({"model": "m"}, DEAD_KEY), True),
    (_failure({"model": "m"}, {"type": "BadRequestError", "status": 400}), True),
    (_failure({"model": "m"}, NO_NETWORK), True),
    (_failure({"model": "m"}, RATE_LIMIT), False),
    (_failure({"model": "m"}, {"type": "APIStatusError", "status": 408}), False),
    (_failure({"model": "m"}, {"type": "InternalServerError", "status": 500}), False),
    (_failure({"model": "m"}, {"type": "APIStatusError", "status": 529}), False),
    (_failure({"model": "m"}, TIMEOUT), False),
    (_failure({"model": "m"}, {"type": "APIConnectionError", "status": 401}), True),  # by its status
    (_failure({"model": "m"}, {"type": "APIConnectionError", "status": 503}), False),
    (_failure({"model": "m"}, None), False),
    # A listed content-policy refusal is a completed outcome, never a stop (decision 0008).
    ({**_failure({"model": "m"}, {"type": "BadRequestError", "status": 400}), "outcome": "provider_content_filter"}, False),
    (_answer({"model": "m"}, 1), False),
])
def test_which_attempts_stop_the_run_at_once(response, stops):
    assert (execute.run_wide_error(response) is not None) is stops


def test_a_failure_streak_resets_on_a_completed_trial(tmp_path):
    out, schedule = tmp_path / "run", _schedule()
    # Trials 1 and 3 fail (three timeouts each); trials 2, 4, 5, and 6 answer.
    _run(out, schedule, Scripted(errors=[TIMEOUT] * 3 + [None] + [TIMEOUT] * 3))
    assert [_result(out, t)["status"] for t in schedule] == (
        ["infrastructure_failure", "completed", "infrastructure_failure"] + ["completed"] * 3)
    assert _stops(out) == [None]


def test_a_torn_last_provenance_line_isnt_read():
    """A stop line a kill cut off never became durable, so it doesn't count."""
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / paid_run.PROVENANCE_FILE
        stop = {"rule": "consecutive_infrastructure_failures", "reason": "x", "logical_trial_ids": []}
        path.write_text(json.dumps({"phase": "stop", "run_wide_stop": None}) + "\n"
                        + json.dumps({"phase": "stop", "run_wide_stop": stop}), encoding="utf-8")
        assert grid_dev.run_wide_stops(Path(directory)) == [] and grid_dev.stopped_unresolved(Path(directory)) is False
