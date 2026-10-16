"""W7-T3: committed development grid spec and orchestration helpers."""

import json
from pathlib import Path

import pytest

from runner import grid_dev
from runner.mock_provider import MOCK_MODEL_ID
from runner.schedule import generate_schedule

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "protocol" / "development_grid_spec.json"


def test_verify_matches_mock_run_model_when_spec_lists_live_model(tmp_path):
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert spec["model_id"] != MOCK_MODEL_ID
    mock_spec = dict(spec)
    mock_spec["model_id"] = MOCK_MODEL_ID
    out = tmp_path / "grid"
    grid_dev.run_mock_grid(
        out,
        spec=mock_spec,
        corpus_root=ROOT / "tests" / "fixtures" / "corpus" / "development",
    )
    report = grid_dev.verify_grid_run(out, spec)
    assert report["trials_found"] == 90
    assert report["complete"] is True


def test_spec_for_verification_prefers_model_requested(tmp_path):
    spec = {"experiment_id": "grid-dev", "model_id": "claude-haiku-5-5", "seed": "x"}
    run_dir = tmp_path / "run"
    trial_dir = run_dir / "trial-a"
    trial_dir.mkdir(parents=True)
    record = {
        "logical_trial_id": "ignored",
        "run_metadata": {"model_requested": "claude-haiku-5-5", "model_resolved": "other-resolved"},
    }
    (trial_dir / "results.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    rebuilt = grid_dev._spec_for_run_verification(run_dir, spec)
    assert rebuilt["model_id"] == "claude-haiku-5-5"


def test_verify_rejects_repeated_dispatch_effect_or_sink():
    base = {"call_id": "tool-1"}
    with pytest.raises(ValueError, match="repeated tool_dispatch"):
        grid_dev._check_no_repeated_dispatch(
            [
                {"event_type": "tool_dispatch", "payload": {**base, "dispatched": True}},
                {"event_type": "tool_dispatch", "payload": {**base, "dispatched": True}},
            ]
        )
    with pytest.raises(ValueError, match="repeated effect_observation"):
        grid_dev._check_no_repeated_effect(
            [
                {"event_type": "effect_observation", "payload": {**base, "effect_observed": True}},
                {"event_type": "effect_observation", "payload": {**base, "effect_observed": True}},
            ]
        )
    with pytest.raises(ValueError, match="repeated sink_receipt"):
        grid_dev._check_no_repeated_sink(
            [
                {"event_type": "sink_receipt", "payload": {**base, "sink_received": True}},
                {"event_type": "sink_receipt", "payload": {**base, "sink_received": True}},
            ]
        )


def test_committed_spec_generates_ninety_unique_trials():
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    schedule = grid_dev.validate_grid_spec(spec)
    assert len(schedule) == 90
    assert len({t.logical_trial_id for t in schedule}) == 90
    assert schedule[0].experiment_id == "grid-dev"


def test_validate_cli_shape():
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    schedule = generate_schedule(spec)
    configurations = {t.configuration for t in schedule}
    assert configurations == {"D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING"}


def test_mock_grid_refuses_missing_corpus(tmp_path):
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="corpus missing"):
        grid_dev.run_mock_grid(
            tmp_path / "run",
            spec=spec,
            corpus_root=tmp_path / "empty-corpus",
        )


def test_mock_grid_runs_dev001_only_spec(tmp_path):
    from runner import execute
    from runner.mock_provider import MOCK_MODEL_ID

    spec = {
        "experiment_id": "grid-dev-test",
        "model_id": MOCK_MODEL_ID,
        "seed": "test-seed",
        "base_case_ids": ["dev-001"],
        "channels": ["C2", "C3", "C4"],
        "conditions": ["attack", "clean"],
        "configurations": ["D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING"],
        "repeats": 1,
    }
    out = tmp_path / "mini-grid"
    schedule = generate_schedule(spec)
    execute.run_schedule(
        out,
        schedule,
        corpus_root=ROOT / "corpus" / "development",
        spec=spec,
        audit=execute.default_audit,
    )
    results = list(out.glob("*/results.jsonl"))
    assert len(results) == 18
    configs = set()
    for path in results:
        record = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
        configs.add(record["configuration"])
    assert configs == {"D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING"}


def test_d2_configuration_marks_untrusted_span_differently_from_d0(tmp_path):
    from runner import execute
    from runner.mock_provider import MOCK_MODEL_ID
    from runner.schedule import generate_schedule

    spec = {
        "experiment_id": "d2-check",
        "model_id": MOCK_MODEL_ID,
        "seed": "d2-seed",
        "base_case_ids": ["dev-001"],
        "channels": ["C2"],
        "conditions": ["attack"],
        "configurations": ["D0_BASELINE", "D2_DATAMARKING"],
        "repeats": 1,
    }
    out = tmp_path / "d2"
    schedule = generate_schedule(spec)
    execute.run_schedule(
        out,
        schedule,
        corpus_root=ROOT / "corpus" / "development",
        spec=spec,
        audit=execute.default_audit,
    )
    d0 = json.loads(
        (out / execute.trial_slug(schedule[0]) / "results.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    d2 = json.loads(
        (out / execute.trial_slug(schedule[1]) / "results.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    d0_events = json.loads(
        (out / execute.trial_slug(schedule[0]) / "events.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    d2_events = json.loads(
        (out / execute.trial_slug(schedule[1]) / "events.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    assert d0["configuration"] == "D0_BASELINE"
    assert d2["configuration"] == "D2_DATAMARKING"
    assert d0_events["payload"]["prompt_sha256"] != d2_events["payload"]["prompt_sha256"]
    assert d0_events["payload"]["untrusted_span"] != d2_events["payload"]["untrusted_span"]
