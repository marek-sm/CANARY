"""W7-T3: live grid paid-run gate (no network)."""

import json
import shutil
import types
from pathlib import Path

import pytest

from runner import delivery, execute, grid_dev, live_smoke

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "protocol" / "development_grid_spec.json"
CORPUS = ROOT / "corpus" / "development"


def _spec():
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def test_live_run_refusal_without_ack():
    assert grid_dev.live_run_refusal(CORPUS, _spec()) is not None
    assert "CANARY_PAID_RUN_ACK" in grid_dev.live_run_refusal(CORPUS, _spec())


def test_live_main_refuses_without_ack_before_run(tmp_path, monkeypatch):
    monkeypatch.delenv("CANARY_PAID_RUN_ACK", raising=False)
    monkeypatch.setattr(
        grid_dev,
        "run_live_grid",
        lambda *a, **k: pytest.fail("must not start a live grid without paid-run ack"),
    )
    code = grid_dev.main(
        [
            "live",
            "--env-file",
            str(tmp_path / ".env"),
            "--out",
            str(tmp_path / "out"),
        ]
    )
    assert code == 2


def test_live_main_refuses_in_ci(tmp_path, monkeypatch):
    monkeypatch.setenv("CANARY_PAID_RUN_ACK", "1")
    monkeypatch.setenv("CI", "true")
    monkeypatch.setattr(
        grid_dev,
        "run_live_grid",
        lambda *a, **k: pytest.fail("must not start a live grid in CI"),
    )
    assert grid_dev.main(["live", "--env-file", str(tmp_path / ".env"), "--out", str(tmp_path / "o")]) == 2


def test_live_main_refuses_ambient_provider_env(tmp_path, monkeypatch):
    monkeypatch.setenv("CANARY_PAID_RUN_ACK", "1")
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "leak")
    monkeypatch.setattr(
        grid_dev,
        "run_live_grid",
        lambda *a, **k: pytest.fail("must not start a live grid with ambient provider vars"),
    )
    assert grid_dev.main(["live", "--env-file", str(tmp_path / ".env"), "--out", str(tmp_path / "o")]) == 2


def test_live_run_refusal_missing_corpus_bases(tmp_path, monkeypatch):
    monkeypatch.setenv("CANARY_PAID_RUN_ACK", "1")
    monkeypatch.delenv("CI", raising=False)
    for name in list(__import__("os").environ):
        if name.startswith(("ANTHROPIC_", "OPENAI_")):
            monkeypatch.delenv(name, raising=False)
    partial = tmp_path / "corpus"
    partial.mkdir()
    (partial / "dev-001.json").write_text(
        (CORPUS / "dev-001.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    reason = grid_dev.live_run_refusal(partial, _spec())
    assert reason is not None and "dev-002" in reason


def test_live_run_refusal_another_corpus(tmp_path, monkeypatch):
    """The paid grid runs only the committed corpus its record hashed (#64 review)."""
    monkeypatch.setenv("CANARY_PAID_RUN_ACK", "1")
    monkeypatch.delenv("CI", raising=False)
    for name in list(__import__("os").environ):
        if name.startswith(("ANTHROPIC_", "OPENAI_")):
            monkeypatch.delenv(name, raising=False)
    other = shutil.copytree(CORPUS, tmp_path / "corpus")
    reason = grid_dev.live_run_refusal(other, _spec())
    assert reason is not None and "corpus/development" in reason


@pytest.fixture
def open_gate_with_a_recording_adapter(monkeypatch):
    """Every gate open, and each provider's adapter a local mock that records the model it's sent."""
    sent = []
    schedule = grid_dev.validate_grid_spec(_spec())[:1]
    base = json.loads((CORPUS / f"{schedule[0].base_case_id}.json").read_text(encoding="utf-8"))
    template, _ = delivery.task_for(base, schedule[0].channel)

    class Adapter(delivery.DeliveryTaskMock):
        adapter_version = "test-delivery-mock"

        def __init__(self, client):
            super().__init__(template, schedule[0].channel)

        def complete(self, messages, tool_schemas, decoding, model_request):
            sent.append(model_request["model"])
            return super().complete(messages, tool_schemas, decoding, model_request)

    monkeypatch.setattr(grid_dev, "validate_grid_spec", lambda _spec: schedule)
    monkeypatch.setattr(grid_dev, "live_run_refusal", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(grid_dev, "load_api_key", lambda _path, _variable: "not-a-real-key")
    for name in live_smoke.PROVIDERS:
        monkeypatch.setitem(live_smoke.PROVIDERS[name], "module", types.SimpleNamespace(build_client=lambda _key: object()))
        monkeypatch.setitem(live_smoke.PROVIDERS[name], "adapter", Adapter)
    return sent


def test_the_fallback_provider_is_never_sent_the_primary_model(tmp_path, open_gate_with_a_recording_adapter):
    """The audit's finding: `--provider openai` sent the Claude model ID the spec names."""
    sent = open_gate_with_a_recording_adapter
    with pytest.raises(ValueError, match="gpt-6-luna"):
        grid_dev.run_live_grid(tmp_path / "live", spec=_spec(), env_file=tmp_path / "never-read.env", provider_name="openai")
    assert sent == []


@pytest.mark.parametrize("model", ["claude-opus-5-5", "gpt-6-luna"])
def test_a_model_argument_can_t_change_what_the_spec_runs(tmp_path, open_gate_with_a_recording_adapter, model):
    sent = open_gate_with_a_recording_adapter
    with pytest.raises(ValueError, match="model"):
        grid_dev.run_live_grid(tmp_path / "live", spec=_spec(), env_file=tmp_path / "never-read.env", model=model)
    assert sent == []


def test_a_mismatch_refuses_before_any_key_is_read(tmp_path, open_gate_with_a_recording_adapter, monkeypatch):
    monkeypatch.setattr(grid_dev, "load_api_key", lambda *_args: pytest.fail("key read"))
    with pytest.raises(ValueError, match="gpt-6-luna"):
        grid_dev.run_live_grid(tmp_path / "live", spec=_spec(), env_file=tmp_path / "never-read.env", provider_name="openai")


def test_the_spec_s_own_model_on_its_own_provider_runs(tmp_path, open_gate_with_a_recording_adapter):
    sent = open_gate_with_a_recording_adapter
    grid_dev.run_live_grid(tmp_path / "live", spec=_spec(), env_file=tmp_path / "never-read.env",
                           model="claude-haiku-5-5", corpus_root=CORPUS)
    assert sent and set(sent) == {"claude-haiku-5-5"}
    assert execute.trial_slug(grid_dev.validate_grid_spec(_spec())[0]) in {p.name for p in (tmp_path / "live").iterdir()}


def test_a_live_grid_runs_only_the_committed_spec(monkeypatch):
    monkeypatch.setenv("CANARY_PAID_RUN_ACK", "1")
    monkeypatch.delenv("CI", raising=False)
    for name in list(__import__("os").environ):
        if name.startswith(("ANTHROPIC_", "OPENAI_")):
            monkeypatch.delenv(name, raising=False)
    reason = grid_dev.live_run_refusal(CORPUS, {**_spec(), "seed": "another-seed"})
    assert reason is not None and "development_grid_spec.json" in reason


def test_a_second_grid_on_one_path_is_refused_in_words(tmp_path, capsys, monkeypatch):
    out = tmp_path / "grid-mock"
    out.mkdir()
    monkeypatch.setattr(grid_dev, "run_mock_grid", lambda *a, **k: pytest.fail("must not start over an existing run"))
    assert grid_dev.main(["mock", "--out", str(out)]) == 2
    err = capsys.readouterr().err
    assert "--out" in err and str(out) in err


def test_a_resume_is_checked_only_for_the_trials_it_hasn_t_started(tmp_path, monkeypatch):
    """A resume isn't checked as 90 new trials, or the ceiling would refuse every resume."""
    from runner import paid_run

    monkeypatch.setenv("CANARY_PAID_RUN_ACK", "1")
    monkeypatch.delenv("CI", raising=False)
    for name in list(__import__("os").environ):
        if name.startswith(("ANTHROPIC_", "OPENAI_")):
            monkeypatch.delenv(name, raising=False)
    out = tmp_path / "grid-live"
    for trial in grid_dev.validate_grid_spec(_spec())[:40]:
        (out / execute.trial_slug(trial)).mkdir(parents=True)
        (out / execute.trial_slug(trial) / "events.jsonl").write_text("", encoding="utf-8")
    asked = []
    monkeypatch.setattr(paid_run, "paid_run_refusal", lambda **kwargs: asked.append(kwargs["new_trials"]) or "stop here")
    assert grid_dev.main(["live", "--resume", "--out", str(out), "--env-file", str(tmp_path / "never-read.env")]) == 2
    with pytest.raises(ValueError, match="stop here"):
        grid_dev.run_live_grid(out, spec=_spec(), env_file=tmp_path / "never-read.env", resume=True, corpus_root=CORPUS)
    assert asked == [50, 50]
    assert grid_dev.live_run_refusal(CORPUS, _spec()) == "stop here"
    assert asked[-1] == 90
