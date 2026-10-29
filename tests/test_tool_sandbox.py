"""Decision 0023: every tool process runs in the sandbox, and no paid call runs
without the project lead's paid-run record.

These are negative tests in real subprocesses on the real platform (sandbox-exec
on macOS, bwrap on Linux CI). A probe launched exactly like the tool worker must
fail to reach anything SPEC.md Section 3 forbids: the network (TCP or a foreign
Unix socket), the provider key file, the home directory, the repository, the
evidence files, ``/tmp``, and any other program. It must still read its fixture
root, write its state, and reach its own fixture socket. Together with the
launch-coverage test below, this is the CI proof that no tool can reach an
arbitrary external endpoint (SPEC.md Section 11, Gate 3).
"""

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from runner import paid_run
from runner.mock_provider import MockProvider
from tools import sandbox

ROOT = Path(__file__).resolve().parents[1]

PROBE = r"""
import json, os, socket, subprocess, sys
targets = json.loads(sys.argv[1])
out = {}
def attempt(name, fn):
    try:
        fn()
        out[name] = "allowed"
    except BaseException as exc:
        out[name] = "denied:" + type(exc).__name__
def tcp(host, port):
    def f():
        s = socket.socket(); s.settimeout(2); s.connect((host, port)); s.close()
    return f
def unix(path):
    def f():
        s = socket.socket(socket.AF_UNIX); s.settimeout(2); s.connect(path); s.close()
    return f
def write(path):
    def f():
        with open(path, "w") as handle:
            handle.write("x")
    return f
attempt("read_fixture", lambda: open(targets["fixture_file"]).read())
attempt("write_state", write(targets["state_file"]))
attempt("own_socket", unix("fixture.sock"))
attempt("read_key_file", lambda: open(targets["key_file"]).read())
attempt("read_repository", lambda: open(targets["repo_file"]).read())
def list_home():
    out["home_listing"] = sorted(os.listdir(targets["home"]))
attempt("list_home", list_home)
attempt("write_evidence", write(targets["evidence_file"]))
attempt("write_repository", write(targets["repo_write"]))
attempt("write_tmp", write("/tmp/canary-sandbox-probe"))
attempt("tcp_loopback", tcp("127.0.0.1", targets["tcp_port"]))
attempt("tcp_external", tcp("192.0.2.1", 9))  # TEST-NET-1 (RFC 5737): routed nowhere, even unsandboxed
attempt("foreign_socket", unix(targets["foreign_socket"]))
# An exec probe counts as allowed if the program ran at all, whatever its exit code.
attempt("exec_shell", lambda: subprocess.run(["/bin/sh", "-c", "true"], timeout=3, capture_output=True))
# The exec probes never name a URL: even if a sandbox failed, they reach nothing.
attempt("exec_curl", lambda: subprocess.run(["/usr/bin/curl", "--version"], timeout=3, capture_output=True))
attempt("exec_open", lambda: subprocess.run(["/usr/bin/open", "-h"], timeout=3, capture_output=True))
out["provider_variables"] = sorted(k for k in os.environ if k.startswith(("ANTHROPIC_", "OPENAI_")))
print(json.dumps(out))
"""

FORBIDDEN = (
    "read_key_file", "read_repository", "write_evidence", "write_repository",
    "write_tmp", "tcp_loopback", "tcp_external", "foreign_socket", "exec_shell", "exec_curl", "exec_open",
)


@pytest.fixture
def trial(tmp_path, monkeypatch):
    """A trial-shaped layout: fixtures, state, socket dir, and evidence beside them."""
    env = tmp_path / "t" / "env"
    fixtures, state, sock = env / "fixtures", env / "state", env / "sock"
    for path in (fixtures, state, sock):
        path.mkdir(parents=True)
    (fixtures / "doc.txt").write_text("fixture", encoding="utf-8")
    (tmp_path / "t" / "events.jsonl").write_text("", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / ".env").write_text("ANTHROPIC_API_KEY=synthetic-sentinel\n", encoding="utf-8")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic-sentinel")

    listeners = []
    monkeypatch.chdir(sock)
    own = socket.socket(socket.AF_UNIX)
    own.bind("fixture.sock")
    own.listen(4)
    monkeypatch.chdir(outside)
    foreign = socket.socket(socket.AF_UNIX)
    foreign.bind("foreign.sock")
    foreign.listen(4)
    tcp = socket.socket()
    tcp.bind(("127.0.0.1", 0))
    tcp.listen(4)
    listeners += [own, foreign, tcp]
    yield {
        "fixtures": fixtures, "state": state, "sock": sock, "outside": outside,
        "tcp_port": tcp.getsockname()[1],
    }
    for listener in listeners:
        listener.close()


def _probe(trial):
    targets = {
        "fixture_file": str(trial["fixtures"] / "doc.txt"),
        "state_file": str(trial["state"] / "receipt.txt"),
        "key_file": str(trial["outside"] / ".env"),
        "repo_file": str(ROOT / "README.md"),
        "home": str(Path.home()),
        "evidence_file": str(trial["state"].parent.parent / "events.jsonl"),
        "repo_write": str(ROOT / "sandbox-probe-should-not-exist.txt"),
        "tcp_port": trial["tcp_port"],
        # Relative to the probe's working directory: a Unix socket path must stay
        # under 104 bytes on macOS, or the connect fails for length, not the sandbox.
        "foreign_socket": os.path.relpath(trial["outside"] / "foreign.sock", trial["sock"]),
    }
    argv = [sys.executable, "-I", "-c", PROBE, json.dumps(targets)]
    completed = subprocess.run(
        sandbox.wrap(argv, cwd=trial["sock"], read=[trial["fixtures"]], write=[trial["state"]], socket_dir=trial["sock"]),
        cwd=trial["sock"], capture_output=True, text=True, timeout=60, env=sandbox.environment([trial["state"]]),
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    return json.loads(completed.stdout)


def test_a_sandboxed_tool_reaches_only_its_fixtures_state_and_socket(trial):
    result = _probe(trial)
    assert result["read_fixture"] == "allowed"
    assert result["write_state"] == "allowed"
    assert result["own_socket"] == "allowed"
    for name in FORBIDDEN:
        assert result[name].startswith("denied"), (name, result[name])
    # bwrap builds empty parent directories for its mounts, so on Linux the home
    # directory may list; it must show nothing but those synthetic parents.
    if result["list_home"] == "allowed":
        home = Path.home()
        mounts = [*sandbox._interpreter_roots(), str(sandbox.TOOLS)]
        parents = {Path(m).relative_to(home).parts[0] for m in mounts if Path(m).is_relative_to(home)}
        assert set(result["home_listing"]) <= parents, result["home_listing"]
    else:
        assert result["list_home"].startswith("denied")
    assert result["provider_variables"] == []
    assert not (ROOT / "sandbox-probe-should-not-exist.txt").exists()
    assert (trial["state"].parent.parent / "events.jsonl").read_text(encoding="utf-8") == ""


def test_the_launcher_refuses_as_root(monkeypatch):
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    with pytest.raises(sandbox.SandboxUnavailable, match="root"):
        sandbox.mode()


def test_the_launcher_refuses_an_unsupported_platform(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    with pytest.raises(sandbox.SandboxUnavailable, match="no supported tool sandbox"):
        sandbox.mode()


def test_the_launcher_refuses_without_its_sandbox_binary(monkeypatch):
    if sys.platform == "darwin":
        monkeypatch.setattr(sandbox, "SANDBOX_EXEC", "/nonexistent/sandbox-exec")
    else:
        monkeypatch.setattr(sandbox.shutil, "which", lambda name: None)
    with pytest.raises(sandbox.SandboxUnavailable):
        sandbox.mode()


def test_every_tool_launch_is_sandboxed(tmp_path, monkeypatch):
    """The audit's fix: a tool launch that isn't sandboxed fails this test."""
    from runner import task_suite, ticket_slice

    prefix = sandbox.SANDBOX_EXEC if sys.platform == "darwin" else "bwrap"
    launches = []
    real_run, real_popen = subprocess.run, subprocess.Popen

    def record(argv):
        if any("tools/" in str(part) for part in argv):
            launches.append([str(part) for part in argv])

    def run(argv, *args, **kwargs):
        record(argv)
        return real_run(argv, *args, **kwargs)

    def popen(argv, *args, **kwargs):
        record(argv)
        return real_popen(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(subprocess, "Popen", popen)
    ticket_slice.run(tmp_path / "smoke")
    task_suite.run(tmp_path / "suite", "shipping-notice-email", "C4")
    assert len(launches) >= 3  # the reader, the fixture service, and at least one worker call
    for argv in launches:
        assert Path(argv[0]).name == Path(prefix).name, argv[:3]


# --- the paid-run record --------------------------------------------------------------------------


class RealProvider:
    adapter_version = "real-adapter-test"

    def complete(self, *args):  # pragma: no cover - the gate refuses before any call
        raise AssertionError("a paid provider was called")


@pytest.fixture
def clean_environment(monkeypatch):
    for name in list(os.environ):
        if name == "CI" or name.startswith(("ANTHROPIC_", "OPENAI_")):
            monkeypatch.delenv(name, raising=False)


@pytest.fixture
def repo(tmp_path):
    """A tiny git repository with hashed code, standing in for the real one."""
    root = tmp_path / "repo"
    (root / "runner").mkdir(parents=True)
    (root / "runner" / "code.py").write_text("VALUE = 1\n", encoding="utf-8")
    env = {"PATH": os.defpath, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com", "HOME": str(tmp_path)}
    for args in (["init", "-q"], ["add", "."], ["commit", "-q", "-m", "init"]):
        subprocess.run(["git", *args], cwd=root, check=True, env=env)
    return root, env


def _record(root, record_path, **overrides):
    record = {
        "schema_version": "1.0.0",
        "recorded_on": "2026-10-29",
        "recorded_by": "marek-sm",
        "recorded_commit": "0" * 40,
        "sandbox": sandbox.describe(),
        "conditions": {
            "tool_result_delivery": {"merged_in": "#61"},
            "mock_grid": {"experiment_id": "grid-dev", "trials": 90, "verify_complete": True,
                          "tool_sandbox": sandbox.describe()},
            "request_to_effect": {"merged_in": "#39"},
            "tool_sandbox": {"merged_in": "#64"},
        },
        "code_sha256": paid_run.code_hashes(root),
    }
    record.update(overrides)
    record_path.write_text(json.dumps(record), encoding="utf-8")
    return record_path


def test_a_mock_provider_never_needs_the_record():
    paid_run.require_paid_run(MockProvider(), record_path=Path("/nonexistent/record.json"))


def test_a_real_provider_is_refused_without_a_record(clean_environment, tmp_path):
    with pytest.raises(paid_run.PaidRunRefused, match="no paid-run record"):
        paid_run.require_paid_run(RealProvider(), record_path=tmp_path / "missing.json")


def test_a_real_provider_is_refused_in_ci_or_with_ambient_keys(clean_environment, monkeypatch, tmp_path):
    monkeypatch.setenv("CI", "true")
    with pytest.raises(paid_run.PaidRunRefused, match="CI"):
        paid_run.require_paid_run(RealProvider(), record_path=tmp_path / "missing.json")
    monkeypatch.delenv("CI")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic")
    with pytest.raises(paid_run.PaidRunRefused, match="ambient"):
        paid_run.require_paid_run(RealProvider(), record_path=tmp_path / "missing.json")


def test_a_valid_record_opens_paid_runs_for_exactly_that_code(clean_environment, repo, tmp_path):
    root, env = repo
    record = _record(root, tmp_path / "record.json")
    assert paid_run.paid_run_refusal(record_path=record, root=root) is None

    (root / "runner" / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    assert "uncommitted" in paid_run.paid_run_refusal(record_path=record, root=root)
    subprocess.run(["git", "commit", "-qam", "change"], cwd=root, check=True, env=env)
    assert "code differs" in paid_run.paid_run_refusal(record_path=record, root=root)


def test_a_record_from_another_sandbox_or_malformed_is_refused(clean_environment, repo, tmp_path):
    root, _ = repo
    other = _record(root, tmp_path / "other.json", sandbox="linux-bwrap:tool-sandbox-v0.0.0:0000000000000000")
    if sandbox.describe().startswith("linux-bwrap"):
        other = _record(root, tmp_path / "other.json", sandbox="macos-sandbox-exec:tool-sandbox-v0.0.0:0000000000000000")
    assert "isn't the recorded mock grid's" in paid_run.paid_run_refusal(record_path=other, root=root)
    broken = _record(root, tmp_path / "broken.json", recorded_by="")
    assert "doesn't validate" in paid_run.paid_run_refusal(record_path=broken, root=root)


def test_the_live_smoke_is_the_one_exception(clean_environment, tmp_path):
    assert paid_run.paid_run_refusal(live_smoke=True, record_path=tmp_path / "missing.json") is None


def test_every_runner_path_refuses_a_real_provider_without_the_record(clean_environment, tmp_path, monkeypatch):
    from runner import execute, mock_slice, ticket_slice
    from runner import schedule as sched

    monkeypatch.setattr(paid_run, "RECORD", tmp_path / "missing.json")
    with pytest.raises(paid_run.PaidRunRefused):
        ticket_slice.run(tmp_path / "ticket", RealProvider())
    with pytest.raises(paid_run.PaidRunRefused):
        mock_slice.run_mock_trial(tmp_path / "mock", RealProvider())
    spec = {"experiment_id": "gate", "model_id": "mock-canned-v0", "seed": "s", "base_case_ids": ["dev-002"],
            "channels": ["C3"], "conditions": ["clean"], "configurations": ["D0_BASELINE"], "repeats": 1}
    for delivery in (True, False):
        with pytest.raises(paid_run.PaidRunRefused):
            execute.run_schedule(tmp_path / f"grid-{delivery}", sched.generate_schedule(spec), spec=spec,
                                 delivery=delivery, provider_factory=lambda trial, canaries: RealProvider())


def test_tools_launch_from_a_relative_run_directory(tmp_path, monkeypatch):
    """``--out results/...`` is relative to the operator's directory; each tool runs
    from its own directory in the sandbox, so its paths must not stay relative."""
    from runner import execute, grid_dev, ticket_slice
    from runner.mock_provider import MOCK_MODEL_ID

    spec = json.loads((ROOT / "protocol" / "development_grid_spec.json").read_text(encoding="utf-8"))
    spec["model_id"] = MOCK_MODEL_ID
    trial = grid_dev.validate_grid_spec(spec)[0]
    monkeypatch.chdir(tmp_path)
    execute.run_schedule(Path("grid"), [trial], corpus_root=execute.DEFAULT_CORPUS_ROOT, spec=spec, delivery=True)
    events = (Path("grid") / execute.trial_slug(trial) / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(events[-1])["payload"]["status"] == "completed"
    tool_results = [json.loads(line)["payload"] for line in events if json.loads(line)["event_type"] == "tool_result"]
    # A relative path that reached the worker would read as a denial, not a failure.
    assert tool_results and all(r["observation"].get("ok") is True for r in tool_results)

    ticket_slice.run(Path("ticket"))
    ticket_events = [json.loads(line) for line in (Path("ticket") / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    results = [e["payload"] for e in ticket_events if e["event_type"] == "tool_result"]
    assert results and all(r["observation"].get("ok") is True for r in results)
