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


def _bare_launch_facts(trial) -> str:
    """What a tool launched by bwrap alone, without ``tools/no_exec.py``, sees: its
    death signal after bwrap's exec and its AppArmor label. A failure message
    carries them, so one CI run tells a cleared death signal (raw 0, fixed by
    ``no_exec.py``) from one that is set but not delivered (raw 9)."""
    code = (
        "import ctypes, sys\n"
        "libc = ctypes.CDLL(None, use_errno=True)\n"
        "signal = ctypes.c_int(-1)\n"
        "libc.prctl(2, ctypes.byref(signal), 0, 0, 0)\n"
        "try:\n"
        "    label = open('/proc/self/attr/current').read().strip()\n"
        "except OSError as error:\n"
        "    label = repr(error)\n"
        "sys.stdout.write(f'raw death signal {signal.value}, AppArmor label {label!r}')\n"
    )
    fixtures, state = str(trial.fixtures.resolve()), str(trial.state.resolve())
    argv = sandbox.linux_argv(read=[fixtures], write=[state], cwd=state)
    try:
        done = subprocess.run([*argv, sys.executable, "-I", "-c", code], cwd=trial.state, capture_output=True,
                              text=True, timeout=10, env=sandbox.environment([trial.state]))
        return done.stdout or done.stderr
    except (OSError, subprocess.SubprocessError) as error:
        return repr(error)


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
        + marker.read_text(errors="replace") + "; bare bwrap launch: " + _bare_launch_facts(trial)
    )
    assert time.time() - start < 30


def test_the_tool_itself_holds_the_death_signal(trial):
    """The property the timing test above relies on, checked without timing.

    ``--die-with-parent`` sets the death signal before bwrap execs the
    interpreter, and the kernel clears it on a secure exec (an LSM transition
    can make one). ``tools/no_exec.py`` sets it again after the exec. Since
    November 5, GitHub's runner let a timed-out tool's child survive; a cleared
    signal is the suspected cause, and the timing test's message says which."""
    code = """
import ctypes, sys
libc = ctypes.CDLL(None, use_errno=True)
signal = ctypes.c_int(-1)
libc.prctl(2, ctypes.byref(signal), 0, 0, 0)  # PR_GET_PDEATHSIG
sys.stdout.write(str(signal.value))
"""
    argv = [sys.executable, "-I", "-c", code]
    wrapped = sandbox.wrap(argv, cwd=trial.state, read=[trial.fixtures], write=[trial.state])
    done = subprocess.run(wrapped, cwd=trial.state, capture_output=True, text=True, timeout=10,
                          env=sandbox.environment([trial.state]))
    assert done.returncode == 0, done.stderr
    assert done.stdout == "9", f"the tool's death signal is {done.stdout!r}, not SIGKILL (9)"


def test_die_with_parent_is_present_in_the_launch(trial):
    """A structural check so a regression that drops the flag is caught even on a
    platform where the timing test is flaky."""
    argv = [sys.executable, "-I", "-c", "pass"]
    wrapped = sandbox.wrap(argv, cwd=trial.state, read=[trial.fixtures], write=[trial.state])
    assert "--die-with-parent" in wrapped and "--as-pid-1" in wrapped, wrapped


def test_no_exec_sets_the_death_signal_itself(tmp_path):
    """The bootstrap sets SIGKILL itself, on any host: launched directly, with no
    bwrap and so no inherited death signal, the tool still reports 9."""
    code = ("import ctypes, sys; libc = ctypes.CDLL(None); s = ctypes.c_int(-1); "
            "libc.prctl(2, ctypes.byref(s), 0, 0, 0); sys.stdout.write(str(s.value))")
    done = subprocess.run([sys.executable, "-I", str(sandbox.NO_EXEC), "-c", code], cwd=tmp_path,
                          capture_output=True, text=True, timeout=10)
    assert done.returncode == 0, done.stderr
    assert done.stdout == "9"
