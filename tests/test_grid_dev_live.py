"""W7-T3: live grid paid-run gate (no network)."""

import json
from pathlib import Path

import pytest

from runner import grid_dev

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "protocol" / "development_grid_spec.json"
FIXTURE_CORPUS = ROOT / "tests" / "fixtures" / "corpus" / "development"


def _spec():
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def test_live_run_refusal_without_ack():
    assert grid_dev.live_run_refusal(FIXTURE_CORPUS, _spec()) is not None
    assert "CANARY_PAID_RUN_ACK" in grid_dev.live_run_refusal(FIXTURE_CORPUS, _spec())


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
        (FIXTURE_CORPUS / "dev-001.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    reason = grid_dev.live_run_refusal(partial, _spec())
    assert reason is not None and "dev-002" in reason
