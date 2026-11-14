"""Shared paid-run gate fixtures: one real 90-cell mock grid of a tiny git checkout.

The gate reads the mock grid's own files, so its tests need a grid that really
ran. The grid is built once; each test works on its own copy of the run and gets
the checkout back as it was.
"""

import itertools
import json
import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from runner import execute, grid_dev, paid_run, spend_ledger
from runner.mock_provider import MOCK_MODEL_ID

ROOT = Path(__file__).resolve().parents[1]
MOCK_RUN = "results/development/grid-mock"


def _git(root, env, *args):
    subprocess.run(["git", *args], cwd=root, check=True, env=env, capture_output=True)


@pytest.fixture(scope="session", autouse=True)
def canary_homes(tmp_path_factory):
    """No test reads or writes the real ``~/.canary``, the project lead's actual spend."""
    base = tmp_path_factory.mktemp("canary-homes")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(spend_ledger, "_account_home", lambda: base / "session")
        yield base, itertools.count()


@pytest.fixture(autouse=True)
def canary_home(canary_homes, monkeypatch):
    base, counter = canary_homes
    home = base / str(next(counter))  # created only by a test that uses it
    monkeypatch.setattr(spend_ledger, "_account_home", lambda: home)
    return home


@pytest.fixture
def clean_environment(monkeypatch):
    for name in list(os.environ):
        if name == "CI" or name.startswith(("ANTHROPIC_", "OPENAI_")):
            monkeypatch.delenv(name, raising=False)


@pytest.fixture(scope="session")
def mock_grid_checkout(tmp_path_factory):
    """A tiny checkout holding hashed code and the corpus, and the mock grid it ran."""
    base = tmp_path_factory.mktemp("paid-gate").resolve()
    root = base / "repo"
    (root / "runner").mkdir(parents=True)
    (root / "protocol").mkdir()
    (root / "runner" / "code.py").write_text("VALUE = 1\n", encoding="utf-8")
    shutil.copytree(ROOT / "corpus" / "development", root / "corpus" / "development")
    (root / "analysis").mkdir()
    (root / "paper").mkdir()
    for name in (".gitignore", "uv.lock", "protocol/development_grid_spec.json", "analysis/floor_count.py",
                 "analysis/__init__.py", "analysis/gate2_budget.py", "paper/estimand_manifest.json"):
        shutil.copy(ROOT / name, root / name)
    env = {"PATH": os.defpath, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com", "HOME": str(base)}
    for args in (["init", "-q"], ["add", "."], ["commit", "-qm", "init"]):
        _git(root, env, *args)
    spec = grid_dev.load_spec(root / "protocol" / "development_grid_spec.json")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(paid_run, "REPO_ROOT", root)
        grid_dev.run_mock_grid(base / "grid", spec=spec, corpus_root=root / "corpus" / "development")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, env=env,
                          capture_output=True, text=True).stdout.strip()
    return SimpleNamespace(root=root, env=env, grid=base / "grid", spec=spec, head=head)


@pytest.fixture(scope="session")
def live_grid_run(mock_grid_checkout):
    """A real-model-named 90-cell grid of the tiny checkout, with recorded usage. load_run
    recomputes every result from its events, so a Gate 2 script's input must really have run."""
    from runner import delivery
    from tests.test_floor_count import MODEL

    root = mock_grid_checkout.root
    spec = {**mock_grid_checkout.spec, "model_id": MODEL}

    class RealShaped(delivery.DeliveryTaskMock):
        def complete(self, messages, tool_schemas, decoding, model_request):
            response = super().complete(messages, tool_schemas, decoding, model_request)
            return {**response, "model_resolved": model_request["model"],
                    "usage": {"input_tokens": 1000, "output_tokens": 200}}

    def factory(trial, _canaries):
        base = json.loads((root / "corpus" / "development" / f"{trial.base_case_id}.json").read_text(encoding="utf-8"))
        return RealShaped(delivery.task_for(base, trial.channel)[0], trial.channel)

    run = mock_grid_checkout.grid.parent / "grid-live"
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(paid_run, "REPO_ROOT", root)
        execute.run_schedule(run, grid_dev.validate_grid_spec(spec), corpus_root=root / "corpus" / "development",
                             spec=spec, delivery=True, provider_factory=factory)
    return run


class GateCheckout:
    """One test's view of the checkout, with its own copy of the mock grid."""

    def __init__(self, checkout):
        self.root, self.env, self.spec = checkout.root, checkout.env, checkout.spec
        self.mock = self.root / MOCK_RUN
        # Verify reads each trial's env/ (fixtures, state, server log); only sockets can't be copied.
        shutil.copytree(checkout.grid, self.mock, ignore=shutil.ignore_patterns("*.sock"))

    def git(self, *args):
        _git(self.root, self.env, *args)

    def attest(self):
        """Decision 0031 item 6's healthy path: a committed review of this checkout's
        code_digest with 0 open blocking findings, attested in the stand-in home."""
        from runner import lead_review

        digest = paid_run.code_digest(paid_run.code_hashes(self.root))
        relative = f"docs/reviews/gate-{digest[:12]}.md"
        path = self.root / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# Gate test review\n\n- **`paid_run.code_digest`:** `{digest}`\n"
                            "- **Open blocking findings:** 0\n", encoding="utf-8")
            self.git("add", relative)
            self.git("commit", "-qm", "review", "--", relative)
        return lead_review.attest(path, root=self.root)

    def record_unattested(self, mock=None, **kwargs):
        return paid_run.build_record(mock or self.mock, delivery="#61", sandbox_pr="#64",
                                     request_to_effect="#39", root=self.root, **kwargs)

    def record(self, mock=None, **kwargs):
        from runner import lead_review

        if paid_run._lead_review_refusal(self.root):
            try:
                self.attest()
            except lead_review.AttestRefused:
                pass  # a dirty tree: build_record names its own refusal
        return self.record_unattested(mock, **kwargs)

    def write_record(self, record):
        path = self.root / "protocol" / "paid_run_record.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def commit_record(self, record):
        path = self.write_record(record)
        self.git("add", path.relative_to(self.root).as_posix())
        self.git("commit", "-qm", "record")
        return path

    def open(self, **kwargs):
        """The healthy path: commit the record ``build_record`` writes from the grid."""
        return self.commit_record(self.record(**kwargs))

    def refusal(self, record_path, **kwargs):
        return paid_run.paid_run_refusal(record_path=record_path, root=self.root, **kwargs)

    def commit_code(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        self.git("add", relative)
        self.git("commit", "-qm", f"change {relative}")

    def trial(self, configuration="D1_POLICY_GATE", condition="attack"):
        return sorted(self.mock.glob(f"*_{condition}_{configuration}_r1"))[0]

    def edit_result(self, trial_dir, edit):
        path = trial_dir / "results.jsonl"
        record = json.loads(path.read_text(encoding="utf-8"))
        edit(record)
        path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    def edit_events(self, trial_dir, edit):
        path = trial_dir / "events.jsonl"
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        for event in events:
            edit(event)
        path.write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")

    def rerun(self, corpus=None):
        """One more real invocation over the finished grid: every trial is skipped,
        and it appends the code running now to the grid's provenance."""
        spec = {**self.spec, "model_id": MOCK_MODEL_ID}
        execute.run_schedule(self.mock, grid_dev.validate_grid_spec(spec),
                             corpus_root=corpus or self.root / "corpus" / "development",
                             spec=spec, delivery=True, resume=True)


@pytest.fixture
def gate(mock_grid_checkout, clean_environment, monkeypatch):
    monkeypatch.setattr(paid_run, "REPO_ROOT", mock_grid_checkout.root)
    monkeypatch.setattr(paid_run, "RECORD", mock_grid_checkout.root / "protocol" / "paid_run_record.json")
    spend_ledger.init()
    spend_ledger.set_cap(10.0)
    yield GateCheckout(mock_grid_checkout)
    _git(mock_grid_checkout.root, mock_grid_checkout.env, "reset", "-q", "--hard", mock_grid_checkout.head)
    _git(mock_grid_checkout.root, mock_grid_checkout.env, "clean", "-qfdx")
