"""Run one tool with every way to start a program closed (Linux; decision 0023).

bwrap mounts only what the interpreter needs, but the system-library folders it
needs (``/usr/lib``, ``/lib*``) hold programs too, and a Linux mount can't stop
them running. So every Linux tool launch starts here: this bootstrap installs a
seccomp filter that fails every ``execve`` and ``execveat`` with ``EPERM``, then
runs the tool in this same interpreter. It also fails ``ptrace`` and
``process_vm_writev``, so the tool can't steer another process into running one,
and bwrap starts the tool as the sandbox's only process (``--as-pid-1``). The
filter can't be removed, and every thread or child the tool starts inherits it.
macOS needs no bootstrap: its profile already allows running only the
interpreter.

Usage, only as ``tools/sandbox.py`` launches it:
  python -I no_exec.py SCRIPT [ARG ...]
  python -I no_exec.py -c CODE [ARG ...]
"""

from __future__ import annotations

import ctypes
import os
import runpy
import struct
import sys

# (audit arch, execve, execveat, ptrace, process_vm_writev) from <linux/audit.h> and each
# architecture's unistd.h.
ARCHES = {"x86_64": (0xC000003E, 59, 322, 101, 311), "aarch64": (0xC00000B7, 221, 281, 117, 271)}
ARCHES["amd64"], ARCHES["arm64"] = ARCHES["x86_64"], ARCHES["aarch64"]
X32_SYSCALL_BIT = 0x40000000
PR_SET_NO_NEW_PRIVS, PR_SET_SECCOMP, SECCOMP_MODE_FILTER = 38, 22, 2
ALLOW, DENY, KILL = 0x7FFF0000, 0x00050000 | 1, 0x80000000  # SECCOMP_RET_ALLOW, _ERRNO | EPERM, _KILL_PROCESS
LD_ABS, JEQ, JGE, RET = 0x20, 0x15, 0x35, 0x06  # BPF_LD|BPF_W|BPF_ABS, BPF_JMP|BPF_JEQ|BPF_K, ...|BPF_JGE|..., BPF_RET|BPF_K


def program(machine: str) -> list[tuple[int, int, int, int]]:
    """The filter, as (code, jump if true, jump if false, constant) instructions."""
    arch, *denied = ARCHES[machine]
    return [
        (LD_ABS, 0, 0, 4),  # seccomp_data.arch
        (JEQ, 1, 0, arch),
        (RET, 0, 0, KILL),  # another ABI's system calls: never expected
        (LD_ABS, 0, 0, 0),  # seccomp_data.nr
        (JGE, len(denied) + 1, 0, X32_SYSCALL_BIT),  # x32's numbering on x86_64
        *((JEQ, len(denied) - i, 0, nr) for i, nr in enumerate(denied)),
        (RET, 0, 0, ALLOW),
        (RET, 0, 0, DENY),
    ]


class _Program(ctypes.Structure):
    _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.c_void_p)]


def forbid_exec() -> None:
    machine = os.uname().machine
    if machine not in ARCHES:
        raise SystemExit(f"no exec filter for {machine}; refusing to run the tool")
    if len(os.listdir("/proc/self/task")) != 1:  # the filter binds only the calling thread
        raise SystemExit("a thread started before the exec filter; refusing to run the tool")
    instructions = program(machine)
    code = ctypes.create_string_buffer(b"".join(struct.pack("HBBI", *i) for i in instructions))
    prog = _Program(len(instructions), ctypes.cast(code, ctypes.c_void_p))
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    for args in ((PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0), (PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ctypes.addressof(prog), 0, 0)):
        if libc.prctl(*args) != 0:
            raise SystemExit(f"can't close running programs ({os.strerror(ctypes.get_errno())}); refusing to run the tool")


def run(argv: list[str]) -> None:
    """Run ``SCRIPT [ARG ...]`` or ``-c CODE [ARG ...]`` as ``python -I`` would."""
    if argv[:1] == ["-c"]:
        sys.argv = ["-c", *argv[2:]]
        exec(compile(argv[1], "<string>", "exec"), {"__name__": "__main__", "__builtins__": __builtins__})
    else:
        sys.argv = list(argv)
        runpy.run_path(argv[0], run_name="__main__")


if __name__ == "__main__":
    forbid_exec()
    run(sys.argv[1:])
