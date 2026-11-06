"""Assorted escape surfaces the red-team brief names: personality, TIOCSTI
terminal injection, mounting, and regaining capabilities via a nested user
namespace. None may give a tool a route out of the sandbox (decision 0023).
"""
from __future__ import annotations

from conftest import attempt_snippet, requires_sandbox, run_probe, skip_if_root

pytestmark = [requires_sandbox, skip_if_root]


def test_personality_does_not_re_enable_exec(trial):
    """personality() is not filtered, but switching exec domain / ASLR flags does
    not bypass the seccomp exec denial."""
    code = attempt_snippet() + r"""
import ctypes, os, subprocess
libc = ctypes.CDLL(None, use_errno=True)
ADDR_NO_RANDOMIZE = 0x0040000
READ_IMPLIES_EXEC = 0x0400000
def set_pers(flag):
    ctypes.set_errno(0)
    rc = libc.personality(flag)
    return {"rc": rc, "errno": ctypes.get_errno()}
attempt("personality_noaslr", lambda: set_pers(ADDR_NO_RANDOMIZE))
attempt("personality_readexec", lambda: set_pers(READ_IMPLIES_EXEC))
def exec_after():
    libc.personality(READ_IMPLIES_EXEC)
    try:
        subprocess.run(["/bin/sh","-c","true"], capture_output=True)
        return "RAN"
    except BaseException as e:
        return "BLOCKED:" + type(e).__name__
attempt("exec_after_personality", exec_after)
emit()
"""
    r = run_probe(trial, code, expect_returncode=None)
    assert r["exec_after_personality"][1].startswith("BLOCKED"), r["exec_after_personality"]


def test_tiocsti_terminal_injection_is_unavailable(trial):
    """--new-session drops the controlling terminal, stdio are pipes, and modern
    kernels gate TIOCSTI behind CAP_SYS_ADMIN. No character can be pushed into a
    parent terminal's input queue."""
    code = attempt_snippet() + r"""
import fcntl, os
TIOCSTI = 0x5412
attempt("open_dev_tty", lambda: os.open("/dev/tty", os.O_RDWR))
def inject(fd):
    def f():
        for ch in b"id\n":
            fcntl.ioctl(fd, TIOCSTI, bytes([ch]))
        return "injected"
    return f
attempt("tiocsti_stdin", inject(0))
attempt("tiocsti_stdout", inject(1))
emit()
"""
    r = run_probe(trial, code, expect_returncode=None)
    assert r["open_dev_tty"][0] == "denied", r["open_dev_tty"]
    assert r["tiocsti_stdin"][0] == "denied", r["tiocsti_stdin"]
    assert r["tiocsti_stdout"][0] == "denied", r["tiocsti_stdout"]


def test_cannot_mount_or_remount_to_reach_the_host(trial):
    """--cap-drop ALL removes CAP_SYS_ADMIN, so mount/remount fail; and the host
    paths are not in the mount namespace to bind anyway."""
    code = attempt_snippet() + r"""
import ctypes, os
libc = ctypes.CDLL(None, use_errno=True)
def mount(src, dst, fstype, flags, data):
    ctypes.set_errno(0)
    rc = libc.mount(src, dst, fstype, ctypes.c_ulong(flags), data)
    return {"rc": rc, "errno": ctypes.get_errno()}
# remount / read-write
attempt("remount_root_rw", lambda: mount(None, b"/", None, 32|1, None))      # MS_REMOUNT|MS_RDONLY off
attempt("mount_proc", lambda: mount(b"proc", b"/proc", b"proc", 0, None))
attempt("mount_tmpfs_over_state", lambda: mount(b"tmpfs", {state!r}.encode(), b"tmpfs", 0, None))
attempt("bind_host_root", lambda: mount(b"/", b"/mnt", None, 4096, None))     # MS_BIND
emit()
""".replace("{state!r}", repr(str(trial.state)))
    r = run_probe(trial, code, expect_returncode=None)
    for name in ("remount_root_rw", "mount_proc", "mount_tmpfs_over_state", "bind_host_root"):
        res = r[name]
        # Either the libc wrapper is missing (allowed->rc -1/errno) or it raised; never rc==0.
        if res[0] == "allowed":
            assert res[1]["rc"] != 0, (name, res)
        else:
            assert res[0] == "denied", (name, res)


def test_nested_user_namespace_grants_no_route_to_the_host(trial):
    """Even if a nested CLONE_NEWUSER yields capabilities inside it, the mount
    namespace still contains no host path to mount, and exec stays filtered."""
    code = attempt_snippet() + r"""
import ctypes, os
libc = ctypes.CDLL(None, use_errno=True)
CLONE_NEWUSER = 0x10000000
CLONE_NEWNS = 0x00020000
def unshare(flags):
    ctypes.set_errno(0)
    rc = libc.unshare(flags)
    return {"rc": rc, "errno": ctypes.get_errno()}
attempt("unshare_userns", lambda: unshare(CLONE_NEWUSER))
# Whatever unshare returned, the host filesystem is still absent and exec blocked.
attempt("host_still_absent", lambda: open("/etc/passwd").read(8))
import subprocess
def exec_try():
    try:
        subprocess.run(["/bin/sh","-c","true"], capture_output=True); return "RAN"
    except BaseException as e:
        return "BLOCKED:" + type(e).__name__
attempt("exec_still_blocked", exec_try)
emit()
"""
    r = run_probe(trial, code, expect_returncode=None)
    assert r["host_still_absent"][0] == "denied", r["host_still_absent"]
    assert r["exec_still_blocked"][1].startswith("BLOCKED"), r["exec_still_blocked"]
