"""W7-T3: ninety-cell mock grid, resume, and verification (the merged development corpus)."""

import json
import shutil
from pathlib import Path

import pytest

from runner import delivery, execute, grid_dev
from runner.mock_provider import MOCK_MODEL_ID
from runner.mock_slice import EVENTS_FILE, RESULTS_FILE, read_jsonl
from runner.schedule import generate_schedule

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpus" / "development"
SPEC_PATH = ROOT / "protocol" / "development_grid_spec.json"
FIXED_CLOCK = lambda: "2020-01-01T00:00:00Z"  # noqa: E731
COMMIT = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"


def _canaries():
    tokens = iter(f"{i:08x}" for i in range(200))
    return lambda: next(tokens)


class Killed(BaseException):
    """Forced termination; not an Exception, so the runner does not catch it."""


def _mock_spec():
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    spec["model_id"] = MOCK_MODEL_ID
    return spec


def _killing_factory(kill_trial_id: str, *, kill_at_call: int = 1):
    """Delivery's own task mock, killed before its call number ``kill_at_call``."""

    def factory(trial, canaries):
        base = json.loads((CORPUS / f"{trial.base_case_id}.json").read_text(encoding="utf-8"))
        template, _ = delivery.task_for(base, trial.channel)
        provider = delivery.DeliveryTaskMock(template, trial.channel)
        original = provider.complete
        made = {"calls": 0}

        def complete(*args, **kwargs):
            if trial.logical_trial_id == kill_trial_id and made["calls"] == kill_at_call:
                raise Killed()
            made["calls"] += 1
            return original(*args, **kwargs)

        provider.complete = complete
        return provider

    return factory


def _run(spec, out, *, resume=False, provider_factory=None):
    schedule = generate_schedule(spec)
    execute.run_schedule(
        out,
        schedule,
        corpus_root=CORPUS,
        resume=resume,
        spec=spec,
        provider_factory=provider_factory,
        clock=FIXED_CLOCK,
        code_commit_value=COMMIT,
        canary_factory=_canaries(),
        delivery=True,
    )
    return schedule


def test_ninety_cell_mock_grid_completes_and_verifies(tmp_path):
    spec = _mock_spec()
    out = tmp_path / "grid"
    _run(spec, out)
    report = grid_dev.verify_grid_run(out, spec)
    assert report["trials_found"] == 90
    summary = grid_dev.summarize_grid_run(out, spec)
    assert len(summary["usage_by_channel_configuration"]) == 9  # 3 channels × 3 configs
    for bucket in summary["usage_by_channel_configuration"].values():
        assert bucket["trials"] == 10  # five bases × two conditions
        assert bucket["provider_requests"] >= bucket["trials"]


def test_ninety_cell_resume_after_kill_matches_uninterrupted_run(tmp_path):
    """Simulate a hard kill after the first provider response, then --resume."""
    spec = _mock_spec()
    schedule = generate_schedule(spec)

    reference = tmp_path / "reference"
    _run(spec, reference)

    victim = None
    for trial in schedule:
        events = read_jsonl(reference / execute.trial_slug(trial) / EVENTS_FILE, "event")
        if sum(1 for e in events if e["event_type"] == "provider_attempt") >= 2:
            victim = trial
            break
    assert victim is not None

    out = tmp_path / "run"
    shutil.copytree(reference, out)
    slug = execute.trial_slug(victim)
    victim_dir = out / slug
    (victim_dir / RESULTS_FILE).unlink(missing_ok=True)
    events_path = victim_dir / EVENTS_FILE
    lines = events_path.read_text(encoding="utf-8").splitlines()
    kept = []
    for line in lines:
        kept.append(line)
        if json.loads(line)["event_type"] == "provider_attempt":
            break
    events_path.write_text("\n".join(kept) + "\n", encoding="utf-8")

    _run(spec, out, resume=True)

    grid_dev.verify_grid_run(out, spec)
    for trial in schedule:
        trial_slug = execute.trial_slug(trial)
        assert (out / trial_slug / EVENTS_FILE).read_text() == (
            reference / trial_slug / EVENTS_FILE
        ).read_text()
        assert (out / trial_slug / RESULTS_FILE).read_text() == (
            reference / trial_slug / RESULTS_FILE
        ).read_text()


def test_ninety_cell_forced_kill_then_resume_via_provider_hook(tmp_path):
    """Provider hook kill matches the invariant tests: no second live call after resume."""
    spec = _mock_spec()
    schedule = generate_schedule(spec)
    victim = schedule[10]

    reference = tmp_path / "reference"
    _run(spec, reference)

    out = tmp_path / "run"
    with pytest.raises(Killed):
        _run(spec, out, provider_factory=_killing_factory(victim.logical_trial_id))
    _run(spec, out, resume=True)
    grid_dev.verify_grid_run(out, spec)
    ref_attempts = sum(
        1
        for e in read_jsonl(reference / execute.trial_slug(victim) / EVENTS_FILE, "event")
        if e["event_type"] == "provider_attempt"
    )
    out_attempts = sum(
        1
        for e in read_jsonl(out / execute.trial_slug(victim) / EVENTS_FILE, "event")
        if e["event_type"] == "provider_attempt"
    )
    assert ref_attempts == out_attempts


def test_verify_rejects_fourth_provider_attempt(tmp_path):
    spec = _mock_spec()
    out = tmp_path / "grid"
    _run(spec, out)
    path = next(out.glob("*/results.jsonl"))
    record = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    extra = dict(record["attempts"][0])
    extra["attempt_index"] = 4
    extra["attempt_id"] = extra["attempt_id"] + "-extra"
    record["attempts"] = list(record["attempts"]) + [extra]
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="provider retries exceeded"):
        grid_dev.verify_grid_run(out, spec)
