"""Runner invariants from the #31 review (W6-T3 Part A).

One section per review item: every file operation stays inside the run
directory; resume continues from the last durable event and never replays a
completed tool dispatch or restarts after observable model behavior (SPEC.md
Section 9); an unwired defense configuration fails closed; tool-request
evidence survives a missing task policy; rendering and post-run failures leave
a durable record rather than a half-written trial; the canary map is durable;
and component versions name the provider actually used.
"""

import dataclasses
import json
import os
import shutil

import pytest

from runner import execute
from runner import schedule as sched
from runner.mock_slice import EVENTS_FILE, RESULTS_FILE, read_jsonl

FIXED_CLOCK = lambda: "2020-01-01T00:00:00Z"  # noqa: E731 - deterministic test clock
COMMIT = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
DEV_001 = execute.DEFAULT_CORPUS_ROOT / "dev-001.json"


class Killed(BaseException):
    """A forced termination: not an Exception, so no runner handler catches it."""


def _spec(**overrides):
    spec = execute.default_dev_spec("exp-fixed", seed="sd")
    spec.update(overrides)
    return spec


def _canaries():
    tokens = iter(["a1a1a1a1", "b2b2b2b2", "c3c3c3c3", "d4d4d4d4"])
    return lambda: next(tokens)


def _run(out, spec, **kwargs):
    schedule = sched.generate_schedule(spec)
    execute.run_schedule(
        out,
        schedule,
        clock=FIXED_CLOCK,
        canary_factory=kwargs.pop("canary_factory", _canaries()),
        code_commit_value=COMMIT,
        spec=spec,
        **kwargs,
    )
    return schedule


def _events(out, trial):
    return read_jsonl(out / execute.trial_slug(trial) / EVENTS_FILE, "event")


def _result(out, trial):
    (result,) = read_jsonl(out / execute.trial_slug(trial) / RESULTS_FILE, "result")
    return result


# --- 1. every file operation stays inside the run directory ---------------


@pytest.mark.parametrize(
    "overrides",
    [
        {"base_case_ids": ["x/../../escape"]},
        {"base_case_ids": [".."]},
        {"base_case_ids": ["dev:001"]},
        {"channels": ["C9"]},
        {"conditions": ["../attack"]},
        {"configurations": ["D9_UNKNOWN"]},
        {"experiment_id": "exp/../x"},
    ],
)
def test_schedule_rejects_unsafe_or_unknown_identifiers(overrides):
    with pytest.raises(ValueError):
        sched.generate_schedule(_spec(**overrides))


def test_resume_never_deletes_outside_the_run_directory(tmp_path):
    # A hand-built trial bypasses the schedule's validation; the executor must
    # still refuse it before touching the filesystem.
    corpus = tmp_path / "corpus" / "a" / "b"
    (corpus / "x").mkdir(parents=True)
    shutil.copy(DEV_001, tmp_path / "corpus" / "a" / "victim.json")
    out = tmp_path / "run"
    (out / "t0000_x").mkdir(parents=True)
    trial = dataclasses.replace(
        sched.generate_schedule(_spec())[0], base_case_id="x/../../victim", schedule_index=0
    )
    victim = tmp_path / (
        f"victim_{trial.channel}_{trial.condition}_{trial.configuration}_r{trial.run_index}"
    )
    victim.mkdir()
    (victim / "keep.txt").write_text("precious", encoding="utf-8")

    with pytest.raises(ValueError):
        execute.run_schedule(
            out,
            [trial],
            corpus_root=corpus,
            clock=FIXED_CLOCK,
            canary_factory=_canaries(),
            code_commit_value=COMMIT,
            resume=True,
        )
    assert (victim / "keep.txt").read_text(encoding="utf-8") == "precious"


def test_corpus_containment_holds_on_its_own(tmp_path, monkeypatch):
    monkeypatch.setattr(execute, "validate_trial", lambda trial: None)
    corpus = tmp_path / "corpus" / "a" / "b"
    (corpus / "x").mkdir(parents=True)
    shutil.copy(DEV_001, tmp_path / "corpus" / "a" / "victim.json")
    trial = dataclasses.replace(sched.generate_schedule(_spec())[0], base_case_id="x/../../victim")
    with pytest.raises(ValueError):
        execute.run_schedule(
            tmp_path / "run", [trial], corpus_root=corpus, clock=FIXED_CLOCK,
            canary_factory=_canaries(), code_commit_value=COMMIT,
        )


def test_trial_directory_containment_holds_on_its_own(tmp_path):
    spec = _spec()
    victim = sched.generate_schedule(spec)[0]
    out = tmp_path / "run"
    out.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("precious", encoding="utf-8")
    (out / execute.trial_slug(victim)).symlink_to(outside)  # a valid id, a linked directory
    with pytest.raises(ValueError):
        _run(out, spec, resume=True)
    assert sorted(p.name for p in outside.iterdir()) == ["keep.txt"]


def test_execute_trial_rejects_an_unwired_configuration_itself(tmp_path):
    trial = dataclasses.replace(
        sched.generate_schedule(_spec())[0], configuration="D1_POLICY_GATE"
    )
    base, template = execute._load_base({}, execute.DEFAULT_CORPUS_ROOT, "dev-001")
    with pytest.raises(ValueError):
        execute.execute_trial(
            tmp_path / "trial", trial, base, template, ["CANARY-a", "CANARY-b"], FIXED_CLOCK,
            provider_factory=execute._default_provider_factory, code_commit_value=COMMIT,
        )
    assert not (tmp_path / "trial").exists()


# --- 2. resume from the last durable event --------------------------------


def _mock_factory(*, kill_id=None, kill_at_call=None, calls=None):
    """dev-001's scripted mock, optionally killed at one call index of one trial."""

    def factory(trial, canaries):
        provider = execute.MockProvider(execute.build_script(trial.condition, canaries[1]))
        original = provider.complete

        def complete(*args, **kwargs):
            if calls is not None:
                calls.append((trial.logical_trial_id, provider.calls))
            if trial.logical_trial_id == kill_id and provider.calls == kill_at_call:
                raise Killed()
            return original(*args, **kwargs)

        provider.complete = complete
        return provider

    return factory


def test_resume_continues_after_observable_model_behavior_without_recalling_it(tmp_path):
    spec = _spec()
    reference = tmp_path / "reference"
    schedule = _run(reference, spec)
    victim = schedule[2]

    out = tmp_path / "run"
    with pytest.raises(Killed):
        # Step 1's response is durable; the process dies on step 2's call.
        _run(out, spec, provider_factory=_mock_factory(kill_id=victim.logical_trial_id, kill_at_call=1))

    calls = []
    _run(out, spec, provider_factory=_mock_factory(calls=calls), resume=True)

    # Step 1 is replayed from its durable event; only step 2 reaches the provider.
    assert [c for c in calls if c[0] == victim.logical_trial_id] == [(victim.logical_trial_id, 1)]
    # Resume continued the same trace: byte-identical to an uninterrupted run.
    for trial in schedule:
        slug = execute.trial_slug(trial)
        assert (out / slug / EVENTS_FILE).read_text() == (reference / slug / EVENTS_FILE).read_text()
        assert (out / slug / RESULTS_FILE).read_text() == (reference / slug / RESULTS_FILE).read_text()


def test_resume_drops_a_line_torn_by_the_kill(tmp_path):
    spec = _spec()
    reference = tmp_path / "reference"
    schedule = _run(reference, spec)
    victim = schedule[2]
    out = tmp_path / "run"
    with pytest.raises(Killed):
        _run(out, spec, provider_factory=_mock_factory(kill_id=victim.logical_trial_id, kill_at_call=1))
    with (out / execute.trial_slug(victim) / EVENTS_FILE).open("a", encoding="utf-8") as f:
        f.write('{"schema_version": "1.0.0", "event_id": "torn')  # cut off mid-append

    _run(out, spec, resume=True)
    slug = execute.trial_slug(victim)
    assert (out / slug / EVENTS_FILE).read_text() == (reference / slug / EVENTS_FILE).read_text()


def test_resume_never_mixes_provider_versions_within_a_trial(tmp_path):
    spec = _spec()
    schedule = sched.generate_schedule(spec)
    victim = schedule[2]
    out = tmp_path / "run"
    with pytest.raises(Killed):
        _run(out, spec, provider_factory=_mock_factory(kill_id=victim.logical_trial_id, kill_at_call=1))

    class Upgraded(execute.MockProvider):
        adapter_version = "mock-provider-v1"

    calls = []

    def upgraded(trial, canaries):
        provider = Upgraded(execute.build_script(trial.condition, canaries[1]))
        original = provider.complete

        def complete(*args, **kwargs):
            calls.append(trial.logical_trial_id)
            return original(*args, **kwargs)

        provider.complete = complete
        return provider

    _run(out, spec, provider_factory=upgraded, resume=True)
    assert victim.logical_trial_id not in calls
    assert {e["component_versions"]["provider_adapter"] for e in _events(out, victim)} == {
        execute.PROVIDER_ADAPTER_VERSION
    }
    assert _result(out, victim)["status"] == "infrastructure_failure"


READ_CALL = {"type": "tool_use", "id": "tu1", "name": "read_file", "input": {"path": "notes.txt"}}


class ToolThenAnswer:
    """Stateless like a real model: asks for one read, then answers once it has the result."""

    adapter_version = "test-tool-provider-v0"

    def __init__(self, *, kill_on_answer=False):
        self.kill_on_answer = kill_on_answer
        self.calls = 0

    def complete(self, messages, tool_schemas, decoding, model_request):
        self.calls += 1
        has_result = any(
            isinstance(m.get("content"), list)
            and any(b.get("type") == "tool_result" for b in m["content"])
            for m in messages
        )
        if not has_result:
            raw = {"stop_reason": "tool_use", "content": [dict(READ_CALL)]}
        else:
            if self.kill_on_answer:
                raise Killed()
            raw = {"stop_reason": "end_turn", "content": [{"type": "text", "text": "Done."}]}
        return {
            "outcome": "model_response",
            "provider_request_id": f"req-{self.calls}",
            "model_requested": model_request["model"],
            "model_resolved": model_request["model"],
            "provider_fingerprint": None,
            "raw_response": raw,
        }


def _receipt_dispatch(dispatched, *, kill=False):
    """A local tool whose effect is one sink receipt per real dispatch."""

    def dispatch_factory(trial, sink):
        def dispatch(request):
            dispatched.append(request.call_id)
            receipts = sink.receipts()
            receipts.append({"call_id": request.call_id})
            sink.path.write_text(json.dumps(receipts), encoding="utf-8")
            if kill:
                raise Killed()  # the effect happened; its record never did
            return {"ok": True, "content": "fixture text"}

        return dispatch

    return dispatch_factory


ONE_CELL = {"channels": ["C2"], "conditions": ["attack"]}


def test_resume_never_replays_a_completed_tool_dispatch(tmp_path):
    spec = _spec(**ONE_CELL)
    out = tmp_path / "run"
    dispatched = []
    with pytest.raises(Killed):
        # The read is dispatched and durably recorded; the process dies on the next call.
        _run(
            out,
            spec,
            provider_factory=lambda t, c: ToolThenAnswer(kill_on_answer=True),
            dispatch_factory=_receipt_dispatch(dispatched),
        )
    schedule = _run(
        out,
        spec,
        provider_factory=lambda t, c: ToolThenAnswer(),
        dispatch_factory=_receipt_dispatch(dispatched),
        resume=True,
    )
    (trial,) = schedule
    assert len(dispatched) == 1  # no repeated dispatch
    sink = execute.FakeSink(out / execute.trial_slug(trial) / execute.SINK_FILE)
    assert len(sink.receipts()) == 1  # no repeated effect
    types = [e["event_type"] for e in _events(out, trial)]
    for event_type in ("trial_started", "tool_requested", "tool_dispatch", "tool_result", "effect_observation"):
        assert types.count(event_type) == 1, event_type
    result = _result(out, trial)
    assert result["status"] == "completed" and result["termination_reason"] == "final_answer"


def test_resume_fails_closed_when_a_dispatch_outcome_is_unknown(tmp_path):
    spec = _spec(**ONE_CELL)
    out = tmp_path / "run"
    dispatched = []
    with pytest.raises(Killed):
        # The process dies inside the dispatch: whether the effect happened is unknown.
        _run(
            out,
            spec,
            provider_factory=lambda t, c: ToolThenAnswer(),
            dispatch_factory=_receipt_dispatch(dispatched, kill=True),
        )
    schedule = _run(
        out,
        spec,
        provider_factory=lambda t, c: ToolThenAnswer(),
        dispatch_factory=_receipt_dispatch(dispatched),
        resume=True,
    )
    (trial,) = schedule
    assert len(dispatched) == 1  # never dispatched again
    result = _result(out, trial)
    assert result["status"] == "infrastructure_failure"


def test_resume_commits_an_ended_trial_without_calling_the_provider(tmp_path):
    spec = _spec(**ONE_CELL)
    out = tmp_path / "run"

    def dying_audit(**kwargs):
        raise Killed()  # trial_ended is durable; the result never was

    with pytest.raises(Killed):
        _run(out, spec, audit=dying_audit)
    calls = []
    (trial,) = _run(out, spec, provider_factory=_mock_factory(calls=calls), resume=True)
    assert calls == []
    assert _result(out, trial)["status"] == "completed"
    assert [e["event_type"] for e in _events(out, trial)].count("trial_ended") == 1


def test_resume_after_the_final_output_records_it_once(tmp_path, monkeypatch):
    spec = _spec(**ONE_CELL)
    reference = tmp_path / "reference"
    (trial,) = _run(reference, spec)
    out = tmp_path / "run"
    real_append = execute.EventLog.append

    def dying_append(self, event_type, *args, **kwargs):
        if event_type == "trial_ended":
            raise Killed()  # final_output is durable; trial_ended never was
        return real_append(self, event_type, *args, **kwargs)

    monkeypatch.setattr(execute.EventLog, "append", dying_append)
    with pytest.raises(Killed):
        _run(out, spec)
    monkeypatch.setattr(execute.EventLog, "append", real_append)
    calls = []
    _run(out, spec, provider_factory=_mock_factory(calls=calls), resume=True)
    assert calls == []
    slug = execute.trial_slug(trial)
    assert (out / slug / EVENTS_FILE).read_text() == (reference / slug / EVENTS_FILE).read_text()


def test_resume_fails_closed_when_the_prompt_no_longer_matches(tmp_path, monkeypatch):
    spec = _spec()
    victim = sched.generate_schedule(spec)[2]
    out = tmp_path / "run"
    with pytest.raises(Killed):
        _run(out, spec, provider_factory=_mock_factory(kill_id=victim.logical_trial_id, kill_at_call=1))
    real_build = execute._build_messages

    def changed(*args, **kwargs):
        messages, span, rendered = real_build(*args, **kwargs)
        return [{"role": "system", "content": "a different prompt"}, *messages[1:]], span, rendered

    monkeypatch.setattr(execute, "_build_messages", changed)
    calls = []
    _run(out, spec, provider_factory=_mock_factory(calls=calls), resume=True)
    assert victim.logical_trial_id not in [c[0] for c in calls]
    assert _result(out, victim)["status"] == "infrastructure_failure"


def _kill_after_dispatch(out, spec):
    dispatched = []
    with pytest.raises(Killed):
        _run(
            out,
            spec,
            provider_factory=lambda t, c: ToolThenAnswer(kill_on_answer=True),
            dispatch_factory=_receipt_dispatch(dispatched),
        )
    return dispatched


def test_resume_refuses_a_different_schedule_spec(tmp_path):
    out = tmp_path / "run"
    dispatched = _kill_after_dispatch(out, _spec(**ONE_CELL))
    (trial,) = sched.generate_schedule(_spec(**ONE_CELL))
    before = (out / execute.trial_slug(trial) / EVENTS_FILE).read_bytes()
    with pytest.raises(ValueError):
        _run(
            out,
            _spec(experiment_id="exp-other", **ONE_CELL),
            provider_factory=lambda t, c: ToolThenAnswer(),
            dispatch_factory=_receipt_dispatch(dispatched),
            resume=True,
        )
    assert len(dispatched) == 1
    assert (out / execute.trial_slug(trial) / EVENTS_FILE).read_bytes() == before


@pytest.mark.parametrize("override", [{"experiment_id": "exp-other"}, {"model_id": "other-model"}])
def test_resume_refuses_a_trace_that_belongs_to_another_trial(tmp_path, override):
    out = tmp_path / "run"
    dispatched = _kill_after_dispatch(out, _spec(**ONE_CELL))
    (trial,) = sched.generate_schedule(_spec(**ONE_CELL))
    before = (out / execute.trial_slug(trial) / EVENTS_FILE).read_bytes()
    (other,) = sched.generate_schedule(_spec(**ONE_CELL, **override))
    assert execute.trial_slug(other) == execute.trial_slug(trial)  # same directory
    with pytest.raises(ValueError):
        execute.run_schedule(  # no spec, so only the trace identity can catch it
            out,
            [other],
            clock=FIXED_CLOCK,
            canary_factory=_canaries(),
            code_commit_value=COMMIT,
            provider_factory=lambda t, c: ToolThenAnswer(),
            dispatch_factory=_receipt_dispatch(dispatched),
            resume=True,
        )
    assert len(dispatched) == 1
    assert (out / execute.trial_slug(trial) / EVENTS_FILE).read_bytes() == before


def test_resume_without_the_tool_seam_fails_closed_over_stored_tool_calls(tmp_path):
    spec = _spec(**ONE_CELL)
    out = tmp_path / "run"
    _kill_after_dispatch(out, spec)
    (trial,) = _run(out, spec, provider_factory=lambda t, c: ToolThenAnswer(), resume=True)
    assert _result(out, trial)["status"] == "infrastructure_failure"


def test_tool_requests_survive_a_run_without_an_audit(tmp_path):
    (trial,) = _run(
        tmp_path / "run",
        _spec(**ONE_CELL),
        provider_factory=lambda t, c: ToolThenAnswer(),
        dispatch_factory=_receipt_dispatch([]),
    )
    (record,) = _result(tmp_path / "run", trial)["tool_events"]
    assert record["request_evaluable"] is False and record["authorized"] is None
    assert record["dispatched"] is True


def test_resume_refuses_a_symlinked_file_inside_the_trial(tmp_path):
    spec = _spec()
    victim = sched.generate_schedule(spec)[2]
    out = tmp_path / "run"
    with pytest.raises(Killed):
        _run(out, spec, provider_factory=_mock_factory(kill_id=victim.logical_trial_id, kill_at_call=1))
    events = out / execute.trial_slug(victim) / EVENTS_FILE
    outside = tmp_path / "outside.jsonl"
    outside.write_bytes(events.read_bytes() + b'{"torn')
    events.unlink()
    events.symlink_to(outside)
    with pytest.raises(ValueError):
        _run(out, spec, resume=True)
    assert outside.read_bytes().endswith(b'{"torn')  # never truncated through the link


# --- 3. an unwired defense configuration fails closed ---------------------


@pytest.mark.parametrize("configuration", ["D1_POLICY_GATE", "D2_DATAMARKING"])
def test_unwired_defense_configuration_is_rejected_before_any_trial(tmp_path, configuration):
    out = tmp_path / "run"
    with pytest.raises(ValueError):
        _run(out, _spec(configurations=["D0_BASELINE", configuration]))
    assert not out.exists()


# --- 4. tool-request evidence survives a missing task policy --------------


def test_missing_policy_keeps_tool_requests_as_unevaluable(tmp_path):
    (trial,) = sched.generate_schedule(_spec(**ONE_CELL))
    request = {
        "schema_version": "1.0.0",
        "event_id": f"{trial.logical_trial_id}:e2",
        "sequence": 2,
        "event_type": "tool_requested",
        "logical_trial_id": trial.logical_trial_id,
        "payload": {
            "call_id": f"{trial.logical_trial_id}:step1:call1",
            "step": 1,
            "tool": "read_file",
            "requested_args": {"path": "notes.txt"},
            "normalized_args": {"path": "notes.txt"},
            "normalizer_version": "test",
        },
    }
    tool_events = execute.default_audit(
        events=[request], trial=trial, base={"task": None}, canaries=[]
    )
    assert len(tool_events) == 1
    (record,) = tool_events
    assert record["request_evaluable"] is False
    assert record["authorized"] is None
    assert record["audit_decision"] is None


# --- durability: rendering, post-run assembly, canary map -----------------


def test_rendering_failure_leaves_a_durable_record(tmp_path, monkeypatch):
    def broken(*args, **kwargs):
        raise ValueError("renderer failed")

    monkeypatch.setattr(execute, "_build_messages", broken)
    out = tmp_path / "run"
    schedule = _run(out, _spec())
    for trial in schedule:
        result = _result(out, trial)
        assert result["status"] == "infrastructure_failure"
        assert [e["event_type"] for e in _events(out, trial)] == ["trial_started", "trial_ended"]


def test_audit_failure_still_commits_the_result(tmp_path):
    def broken_audit(**kwargs):
        raise RuntimeError("audit failed")

    out = tmp_path / "run"
    schedule = _run(out, _spec(), audit=broken_audit)
    for trial in schedule:
        result = _result(out, trial)
        assert result["status"] == "completed"
        assert result["security"]["unauthorized_action_requested"] is None


def test_canary_map_is_fsynced_with_its_directory(tmp_path, monkeypatch):
    synced = []
    real_fsync = os.fsync

    def recording_fsync(fd):
        synced.append(os.fstat(fd).st_ino)
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", recording_fsync)
    path = tmp_path / execute.CANARIES_FILE
    execute._persist_canary_map(path, {"sb": {"canaries": ["CANARY-x", "CANARY-y"]}})
    assert path.stat().st_ino in synced  # the file's bytes reached disk before the rename
    assert tmp_path.stat().st_ino in synced  # and so did the rename


# --- version capture names the provider actually used ----------------------


def test_component_versions_name_the_provider_used(tmp_path):
    class Versioned(execute.MockProvider):
        adapter_version = "fake-adapter-v9"

    out = tmp_path / "run"
    schedule = _run(
        out,
        _spec(**ONE_CELL),
        provider_factory=lambda t, c: Versioned(execute.build_script(t.condition, c[1])),
    )
    (trial,) = schedule
    assert {e["component_versions"]["provider_adapter"] for e in _events(out, trial)} == {
        "fake-adapter-v9"
    }
    meta = _result(out, trial)["run_metadata"]
    assert meta["component_versions"]["provider_adapter"] == "fake-adapter-v9"
