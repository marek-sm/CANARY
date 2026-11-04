"""A timed-out tool must not orphan a surviving child (decision 0023).

The real launch is ``subprocess.run(sandbox.wrap(...), timeout=5)``
(tasks/registry.py:worker). On timeout, ``subprocess.run`` SIGKILLs the direct
child (``bwrap``). With ``--as-pid-1`` (the tool is pid 1 of a fresh pid
namespace) and ``--die-with-parent``, tearing down bwrap must take the whole
sandbox — including any child the tool forked — with it. If a forked child keeps
running after the timeout and writes to the (host-backed) state dir, that is an
orphan escape.
"""
from __future__ import annotations

import subprocess
import sys
import time

import pytest

from conftest import requires_sandbox, skip_if_root
from tools import sandbox

pytestmark = [requires_sandbox, skip_if_root]


def test_a_timed_out_tool_leaves_no_surviving_child(trial):
    marker = trial.state / "orphan-marker.txt"
    # Parent (pid 1) spawns a child that waits, then writes the marker; the parent
    # then blocks far past the timeout. Mirrors a wedged tool that forked a worker.
    code = f"""
import os, sys, time
pid = os.fork()
if pid == 0:
    # child: detach from stdio, outlive a naive parent-kill, then write
    try:
        os.setsid()
    except OSError:
        pass
    time.sleep(4)
    try:
        open({str(marker)!r}, "w").write("ORPHAN_SURVIVED")
    except BaseException:
        pass
    os._exit(0)
sys.stdout.write("started\\n"); sys.stdout.flush()
time.sleep(60)
"""
    argv = [sys.executable, "-I", "-c", code]
    wrapped = sandbox.wrap(argv, cwd=trial.state, read=[trial.fixtures], write=[trial.state])
    start = time.time()
    try:
        subprocess.run(wrapped, cwd=trial.state, capture_output=True, text=True,
                       timeout=2, env=sandbox.environment([trial.state]))
        raise AssertionError("probe should have timed out")
    except subprocess.TimeoutExpired:
        pass  # subprocess.run has now SIGKILLed bwrap, exactly as the worker's timeout does
    # Wait well past the child's 4s sleep; a surviving orphan would write the marker.
    time.sleep(6)
    assert not marker.exists(), (
        "a forked child survived the tool timeout and wrote to the state dir: "
        + marker.read_text(errors="replace")
    )
    assert time.time() - start < 30


def test_die_with_parent_is_present_in_the_launch(trial):
    """A structural check so a regression that drops the flag is caught even on a
    platform where the timing test is flaky."""
    argv = [sys.executable, "-I", "-c", "pass"]
    wrapped = sandbox.wrap(argv, cwd=trial.state, read=[trial.fixtures], write=[trial.state])
    assert "--die-with-parent" in wrapped and "--as-pid-1" in wrapped, wrapped
