"""Shared harness for the authorized sandbox red-team (cloud/sandbox-redteam).

These tests attack ``tools/sandbox.py`` + ``tools/no_exec.py`` and the tools that
run in them, under the real platform sandbox (``bwrap`` on Linux). They are
negative regression tests: each asserts that an escape SPEC.md Section 3 forbids
stays blocked. A test that starts passing (an escape that works) is a finding.

Every probe is launched exactly like the real tool worker
(``tasks/registry.py:worker``): ``sandbox.wrap([python, -I, -c CODE | SCRIPT],
cwd=..., read=[...], write=[...], socket_dir=...)`` run with ``cwd`` as given and
``sandbox.environment(...)`` as the environment, ``capture_output``, ``timeout``.
Nothing here needs root; the VM creates a non-root user to run them (see
``reports/cloud/sandbox-redteam.md``).
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from tools import sandbox

ROOT = Path(__file__).resolve().parents[2]

requires_sandbox = pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason="the cloud red-team runs under Linux bwrap",
)


def _sandbox_available() -> bool:
    try:
        sandbox.mode()
        return True
    except sandbox.SandboxUnavailable:
        return False


skip_if_root = pytest.mark.skipif(
    not _sandbox_available(),
    reason="sandbox refuses here (root, or no bwrap); run as the non-root user",
)


class Trial:
    """A trial-shaped layout: a fixture root (read), a state dir (write), a
    socket dir, and sentinel secrets placed outside every mounted path."""

    def __init__(self, tmp_path: Path):
        self.base = tmp_path
        env = tmp_path / "t" / "env"
        self.fixtures = env / "fixtures"
        self.state = env / "state"
        self.sock = env / "sock"
        for path in (self.fixtures, self.state, self.sock):
            path.mkdir(parents=True)
        (self.fixtures / "doc.txt").write_text("fixture-body", encoding="utf-8")
        (tmp_path / "t" / "events.jsonl").write_text("", encoding="utf-8")
        self.outside = tmp_path / "outside"
        self.outside.mkdir()
        (self.outside / ".env").write_text(
            "ANTHROPIC_API_KEY=synthetic-sentinel-must-never-leak\n", encoding="utf-8"
        )
        self.listeners: list[socket.socket] = []

    def listen_unix(self, directory: Path, name: str) -> str:
        """Bind a foreign listener by a short relative name; return its path
        relative to the socket dir (macOS caps socket paths, Linux is fine)."""
        cwd = os.getcwd()
        os.chdir(directory)
        try:
            listener = socket.socket(socket.AF_UNIX)
            listener.bind(name)
            listener.listen(4)
        finally:
            os.chdir(cwd)
        self.listeners.append(listener)
        return os.path.relpath(directory / name, self.sock)

    def listen_tcp(self) -> int:
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(4)
        self.listeners.append(listener)
        return listener.getsockname()[1]

    def close(self) -> None:
        for listener in self.listeners:
            listener.close()


@pytest.fixture
def trial(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic-sentinel-must-never-leak")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-sentinel-openai")
    t = Trial(tmp_path)
    yield t
    t.close()


def run_probe(
    trial: Trial,
    code: str,
    *,
    argv_extra=(),
    read=None,
    write=None,
    socket_dir=None,
    bind_socket=False,
    timeout=60,
    expect_returncode=0,
):
    """Run CODE as the sandboxed tool worker would, returning parsed JSON stdout.

    CODE must print one JSON object. ``read``/``write``/``socket_dir`` default to
    the trial's fixture/state/socket dirs, matching ``worker()``.
    """
    read = [trial.fixtures] if read is None else read
    write = [trial.state] if write is None else write
    # socket_dir stays None unless a test binds a real socket there: bwrap --ro-bind
    # of a missing socket path would fail the launch itself.
    cwd = socket_dir if socket_dir is not None else (write[0] if write else trial.state)
    argv = [sys.executable, "-I", "-c", code, *argv_extra]
    wrapped = sandbox.wrap(
        argv, cwd=cwd, read=read, write=write, socket_dir=socket_dir, bind_socket=bind_socket
    )
    completed = subprocess.run(
        wrapped, cwd=cwd, capture_output=True, text=True, timeout=timeout,
        env=sandbox.environment(write),
    )
    if expect_returncode is not None:
        assert completed.returncode == expect_returncode, (
            f"rc={completed.returncode}\nSTDOUT:{completed.stdout[-2000:]}\nSTDERR:{completed.stderr[-2000:]}"
        )
    return _parse(completed)


def _parse(completed):
    try:
        return json.loads(completed.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"_raw_stdout": completed.stdout, "_stderr": completed.stderr,
                "_rc": completed.returncode}


def run_worker(trial: Trial, request: dict, *, fixture_root=None, state=None,
               socket_dir=None, timeout=10):
    """Invoke the real ``tools/worker.py`` through the sandbox exactly as
    ``tasks/registry.py:worker`` does, and return the tool's JSON result."""
    fixture_root = trial.fixtures if fixture_root is None else fixture_root
    state = trial.state if state is None else state
    # The worker runs from the socket dir when a fixture service is used (matching
    # tasks/registry.py:worker), else from its state dir.
    cwd = socket_dir if socket_dir is not None else state
    sock_name = sandbox.SOCKET_NAME if socket_dir is not None else ""
    argv = [sys.executable, "-I", str(ROOT / "tools/worker.py"),
            str(Path(fixture_root).resolve()), str(Path(state).resolve()), sock_name]
    wrapped = sandbox.wrap(
        argv, cwd=cwd, read=[fixture_root], write=[state], socket_dir=socket_dir,
    )
    completed = subprocess.run(
        wrapped, cwd=cwd, input=json.dumps(request), capture_output=True, text=True,
        timeout=timeout, env=sandbox.environment([state]),
    )
    return _parse(completed)


def attempt_snippet() -> str:
    """A reusable helper, prepended to probe CODE, giving attempt()/emit()."""
    return (
        "import json,os,sys\n"
        "R={}\n"
        "def attempt(name, fn):\n"
        "    try:\n"
        "        R[name]=['allowed', fn()]\n"
        "    except BaseException as e:\n"
        "        R[name]=['denied', type(e).__name__, str(e)[:200]]\n"
        "def emit():\n"
        "    print(json.dumps(R))\n"
    )
