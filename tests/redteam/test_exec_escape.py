"""No tool may run another program (decision 0023; SPEC.md Section 3).

On Linux the mount namespace still contains runnable binaries (``/usr/lib*``,
``/lib*``), so ``tools/no_exec.py`` installs a seccomp filter that fails
``execve``, ``execveat`` (EPERM), and also ``ptrace`` and ``process_vm_writev``,
kills on any foreign ABI, and is locked by ``PR_SET_NO_NEW_PRIVS`` so it cannot
be dropped and every child/thread inherits it. ``bwrap --as-pid-1`` makes the
tool the only process in its pid namespace.

These probes run inside the filter and try every route to a new program that is
reachable from Python + ctypes. EPERM surfaces as ``PermissionError`` (high-level
calls) or a ``-1``/errno result (raw ``syscall``).
"""
from __future__ import annotations

import os

from conftest import attempt_snippet, requires_sandbox, run_probe, skip_if_root

pytestmark = [requires_sandbox, skip_if_root]

# A real executable that exists inside the mounted system-library folders.
LIB_PROG = "/lib64/ld-linux-x86-64.so.2" if os.path.exists("/lib64/ld-linux-x86-64.so.2") else "/bin/true"


def test_high_level_exec_paths_are_blocked(trial):
    code = attempt_snippet() + f"""
import os, subprocess
attempt("subprocess_run", lambda: subprocess.run(["/bin/sh","-c","echo hi"], capture_output=True))
attempt("os_system", lambda: os.system("echo hi") or os.WEXITSTATUS(0))
attempt("os_execv", lambda: os.execv("/bin/sh", ["sh","-c","true"]))
attempt("os_execve_libpath", lambda: os.execve({LIB_PROG!r}, [{LIB_PROG!r},"--version"], {{}}))
attempt("os_posix_spawn", lambda: os.posix_spawn("/bin/sh", ["sh","-c","true"], {{}}))
emit()
"""
    r = run_probe(trial, code, expect_returncode=None)
    for name in ("subprocess_run", "os_execv", "os_execve_libpath", "os_posix_spawn"):
        assert r[name][0] == "denied", (name, r[name])
    # os.system returns the shell wait-status; a blocked exec yields non-zero, never 0 ("hi" ran).
    assert r["os_system"][0] == "denied" or r["os_system"][1] != 0, r["os_system"]


def test_raw_execve_and_execveat_syscalls_return_eperm(trial):
    """ctypes issues the syscall directly, bypassing glibc — seccomp is at the
    syscall boundary, so it still fails."""
    code = attempt_snippet() + r"""
import ctypes, os
libc = ctypes.CDLL(None, use_errno=True)
NR = {"execve": 59, "execveat": 322}
path = b"/bin/sh"
argv = (ctypes.c_char_p * 2)(b"sh", None)
envp = (ctypes.c_char_p * 1)(None)
def call(nr, *a):
    ctypes.set_errno(0)
    rc = libc.syscall(ctypes.c_long(nr), *a)
    return {"rc": rc, "errno": ctypes.get_errno(), "errstr": os.strerror(ctypes.get_errno())}
attempt("raw_execve", lambda: call(NR["execve"], path, argv, envp))
attempt("raw_execveat", lambda: call(NR["execveat"], -100, path, argv, envp, 0))
emit()
"""
    r = run_probe(trial, code, expect_returncode=None)
    for name in ("raw_execve", "raw_execveat"):
        assert r[name][0] == "allowed", (name, r[name])   # the syscall returned (did not run a program)
        res = r[name][1]
        assert res["rc"] == -1 and res["errno"] == 1, (name, res)  # EPERM == 1


def test_memfd_create_plus_execveat_fd_is_blocked(trial):
    """The classic fileless exec: write an ELF into an anonymous memfd, then
    execveat(fd, "", AT_EMPTY_PATH). execveat is filtered, so it fails."""
    code = attempt_snippet() + r"""
import ctypes, os
libc = ctypes.CDLL(None, use_errno=True)
# memfd_create is syscall 319 on x86_64; also try the glibc wrapper / os.memfd_create.
def make_memfd():
    if hasattr(os, "memfd_create"):
        return os.memfd_create("x", 0)
    ctypes.set_errno(0)
    fd = libc.syscall(ctypes.c_long(319), b"x", 0)
    if fd < 0:
        raise OSError(ctypes.get_errno(), "memfd_create")
    return fd
def attack():
    fd = make_memfd()
    # a tiny but real ELF header is unnecessary: execveat is refused before exec validation
    os.write(fd, b"\x7fELF" + b"\x00" * 64)
    AT_EMPTY_PATH = 0x1000
    ctypes.set_errno(0)
    rc = libc.syscall(ctypes.c_long(322), fd, b"", None, None, AT_EMPTY_PATH)
    return {"rc": rc, "errno": ctypes.get_errno()}
attempt("memfd_execveat", attack)
# os.execve on the /proc/self/fd path of the memfd (loader-as-interpreter trick)
def attack_fdpath():
    fd = make_memfd(); os.write(fd, b"\x7fELF")
    os.execve("/proc/self/fd/%d" % fd, ["x"], {})
attempt("memfd_fdpath_execve", attack_fdpath)
emit()
"""
    r = run_probe(trial, code, expect_returncode=None)
    res = r["memfd_execveat"]
    assert res[0] == "allowed" and res[1]["rc"] == -1 and res[1]["errno"] == 1, res
    assert r["memfd_fdpath_execve"][0] == "denied", r["memfd_fdpath_execve"]


def test_fork_child_still_inherits_the_filter(trial):
    """A forked child cannot drop the filter (NO_NEW_PRIVS) and cannot exec."""
    code = attempt_snippet() + r"""
import os, subprocess
def forked_exec():
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(r)
        try:
            os.execv("/bin/sh", ["sh","-c","true"])
            os.write(w, b"EXECED")
        except BaseException as e:
            os.write(w, b"BLOCKED:" + type(e).__name__.encode())
        os._exit(0)
    os.close(w)
    os.waitpid(pid, 0)
    return os.read(r, 64).decode()
attempt("forked_exec", forked_exec)
emit()
"""
    r = run_probe(trial, code, expect_returncode=None)
    assert r["forked_exec"][0] == "allowed", r["forked_exec"]
    assert r["forked_exec"][1].startswith("BLOCKED"), r["forked_exec"]


def test_clone3_child_cannot_exec(trial):
    """clone/clone3 are not filtered (not exec), but any child they spawn inherits
    the seccomp filter, so the child still cannot run a program."""
    code = attempt_snippet() + r"""
import ctypes, os, struct
libc = ctypes.CDLL(None, use_errno=True)
# clone3(struct clone_args) == syscall 435 on x86_64.
class CloneArgs(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint64) for n in
        ("flags","pidfd","child_tid","parent_tid","exit_signal","stack","stack_size","tls","set_tid","set_tid_size","cgroup")]
def attack():
    args = CloneArgs(); args.exit_signal = 17  # SIGCHLD
    ctypes.set_errno(0)
    pid = libc.syscall(ctypes.c_long(435), ctypes.byref(args), ctypes.sizeof(args))
    if pid == 0:
        # child: try to exec; filter must deny
        try:
            os.execv("/bin/sh", ["sh","-c","true"])
        except BaseException:
            os._exit(7)
        os._exit(0)
    if pid < 0:
        return {"clone3_errno": ctypes.get_errno()}
    _, status = os.waitpid(pid, 0)
    return {"child_exit": os.WEXITSTATUS(status)}
attempt("clone3_child_exec", attack)
emit()
"""
    r = run_probe(trial, code, expect_returncode=None)
    res = r["clone3_child_exec"]
    assert res[0] == "allowed", res
    # Either clone3 itself was unavailable (errno) or the child was blocked from exec (exit 7).
    assert res[1].get("child_exit") in (7, None) and res[1].get("child_exit") != 0, res


def test_ptrace_and_process_vm_writev_are_blocked(trial):
    """So a tool cannot steer another process into running a program, nor poke
    another address space. (In-sandbox there is only pid 1, but the calls must
    still fail per decision 0023.)"""
    code = attempt_snippet() + r"""
import ctypes, os
libc = ctypes.CDLL(None, use_errno=True)
def ptrace_traceme():
    ctypes.set_errno(0)
    rc = libc.syscall(ctypes.c_long(101), 0, 0, 0, 0)  # PTRACE_TRACEME
    return {"rc": rc, "errno": ctypes.get_errno()}
def pvw():
    ctypes.set_errno(0)
    rc = libc.syscall(ctypes.c_long(311), 1, 0, 0, 0, 0, 0)  # process_vm_writev
    return {"rc": rc, "errno": ctypes.get_errno()}
attempt("ptrace_traceme", ptrace_traceme)
attempt("process_vm_writev", pvw)
emit()
"""
    r = run_probe(trial, code, expect_returncode=None)
    assert r["ptrace_traceme"][1]["rc"] == -1 and r["ptrace_traceme"][1]["errno"] == 1, r["ptrace_traceme"]
    assert r["process_vm_writev"][1]["rc"] == -1 and r["process_vm_writev"][1]["errno"] == 1, r["process_vm_writev"]


def test_the_filter_cannot_be_removed_and_no_new_privs_is_set(trial):
    """A tool cannot clear seccomp (only add stricter layers); NO_NEW_PRIVS is on,
    and adding another filter never re-allows exec."""
    code = attempt_snippet() + r"""
import ctypes, os, subprocess
libc = ctypes.CDLL(None, use_errno=True)
PR_GET_NO_NEW_PRIVS = 39
attempt("no_new_privs_is_1", lambda: libc.prctl(PR_GET_NO_NEW_PRIVS, 0, 0, 0, 0))
# Try to install an allow-all seccomp filter; even if it "succeeds" it only stacks,
# and the existing EPERM layer still denies exec.
def stack_allow_all():
    SO = [(0x06, 0, 0, 0x7fff0000)]  # BPF_RET|BPF_K ALLOW
    import struct
    blob = b"".join(struct.pack("HBBI", *i) for i in SO)
    buf = ctypes.create_string_buffer(blob)
    class P(ctypes.Structure):
        _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.c_void_p)]
    prog = P(len(SO), ctypes.cast(buf, ctypes.c_void_p))
    rc = libc.prctl(22, 2, ctypes.addressof(prog), 0, 0)  # PR_SET_SECCOMP, MODE_FILTER
    # now attempt exec again
    try:
        subprocess.run(["/bin/sh","-c","true"], capture_output=True)
        return {"set_rc": rc, "exec": "RAN"}
    except BaseException as e:
        return {"set_rc": rc, "exec": "BLOCKED:" + type(e).__name__}
attempt("stack_allow_all_then_exec", stack_allow_all)
emit()
"""
    r = run_probe(trial, code, expect_returncode=None)
    assert r["no_new_privs_is_1"][1] == 1, r["no_new_privs_is_1"]
    assert r["stack_allow_all_then_exec"][1]["exec"].startswith("BLOCKED"), r["stack_allow_all_then_exec"]
