"""Operating-system sandbox for every tool process (audit F-01; decision 0023).

SPEC.md Section 3 holds under every configuration, D0_BASELINE included: tool
processes run non-root, with a read-only filesystem except their explicit
per-trial state, with no arbitrary network route, and without the hosted-model
credential. Every tool launch therefore goes through ``wrap``, which denies by
default and allows only:

* running the interpreter;
* reading the interpreter, its virtual environment, ``tools/``, the system
  libraries, and the directories the caller names (the trial's fixtures);
* writing only the directories the caller names (the trial's state);
* reaching only the trial's fixture Unix socket, by path. There is no TCP or UDP
  at all, no other socket, no other program, and no system service.

On macOS this is ``sandbox-exec`` with a deny-by-default profile. On Linux it is
``bwrap`` with every namespace unshared and only the named paths mounted. Any
other platform, a missing sandbox binary, or a root user refuses, so a tool
launch fails closed rather than running unconfined. The mode, version, and the
hash of the rendered rules are recorded with every trial's component versions.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
from pathlib import Path
from typing import Iterable, Optional, Sequence

VERSION = "tool-sandbox-v0.1.0"
SOCKET_NAME = "fixture.sock"
TOOLS = Path(__file__).resolve().parent
SANDBOX_EXEC = "/usr/bin/sandbox-exec"
# Read-only system locations the interpreter needs to start. No /usr/bin, /etc,
# /var, /home, /run, or user directory is ever readable.
MACOS_SYSTEM_READS = ("/System", "/usr/lib", "/private/var/db/dyld")
LINUX_SYSTEM_READS = ("/usr/lib", "/usr/lib64", "/lib", "/lib64", "/etc/ld.so.cache")


class SandboxUnavailable(RuntimeError):
    """No supported sandbox on this machine; the tool launch is refused."""


def _real(path: os.PathLike | str) -> str:
    return os.path.realpath(os.fspath(path))


def _venv_home() -> list[str]:
    """``home`` from the virtual environment's ``pyvenv.cfg``, as written and resolved."""
    cfg = Path(sys.prefix) / "pyvenv.cfg"
    try:
        lines = cfg.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        key, _, value = line.partition("=")
        if key.strip() == "home" and value.strip():
            install = Path(value.strip()).parent
            # Only a real Python install, never a shared prefix like /usr or /opt/homebrew.
            if (install / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "os.py").is_file() \
                    and str(install) not in ("/usr", "/usr/local", "/opt/homebrew"):
                return [str(install), _real(install)]
            return []
    return []


def _interpreter_roots() -> list[str]:
    """The interpreter's install tree and the virtual environment, both as the
    interpreter names them and resolved: uv, for one, points a venv at a
    minor-version link whose target is the real install."""
    roots = {
        os.path.abspath(sys.base_prefix), _real(sys.base_prefix),
        os.path.abspath(sys.prefix), _real(sys.prefix),
        str(Path(os.path.abspath(sys.executable)).parent), str(Path(_real(sys.executable)).parent),
        *_venv_home(),
    }
    return sorted(roots)


def mode() -> str:
    """The sandbox this machine provides, or ``SandboxUnavailable``."""
    if os.geteuid() == 0:
        raise SandboxUnavailable("tool processes never run as root (SPEC.md Section 3)")
    if sys.platform == "darwin":
        if not os.access(SANDBOX_EXEC, os.X_OK):
            raise SandboxUnavailable(f"{SANDBOX_EXEC} is missing")
        return "macos-sandbox-exec"
    if sys.platform.startswith("linux"):
        if shutil.which("bwrap") is None:
            raise SandboxUnavailable("bubblewrap (bwrap) is not installed; see README.md, tool sandbox")
        return "linux-bwrap"
    raise SandboxUnavailable(f"no supported tool sandbox on {sys.platform}; use macOS or Linux (WSL2 on Windows)")


def _quote(path: str) -> str:
    if any(ch in path for ch in '"\\\n\0'):
        raise SandboxUnavailable(f"refusing a sandbox path with control characters: {path!r}")
    return f'"{path}"'


def macos_profile(*, read: Sequence[str], write: Sequence[str], socket: Optional[str], bind_socket: bool) -> str:
    reads = ["/", *_interpreter_roots(), str(TOOLS), *MACOS_SYSTEM_READS, *read, *write]
    lines = [
        "(version 1)",
        "(deny default)",
        "(allow process-exec " + " ".join(f"(subpath {_quote(p)})" for p in _interpreter_roots()) + ")",
        "(allow file-read-metadata)",
        "(allow file-read* (literal \"/\") "
        + " ".join(f"(subpath {_quote(p)})" for p in reads[1:])
        + ' (literal "/dev/null") (literal "/dev/urandom"))',
        "(allow file-write* " + " ".join(f"(subpath {_quote(p)})" for p in write) + ' (literal "/dev/null"))',
    ]
    if socket is not None:
        rule = "network-bind (local" if bind_socket else "network-outbound (remote"
        lines.append(f"(allow {rule} unix-socket (path-literal {_quote(socket)})))")
    return "\n".join(lines) + "\n"


def linux_argv(*, read: Sequence[str], write: Sequence[str], cwd: str) -> list[str]:
    argv = [
        shutil.which("bwrap") or "bwrap",
        "--die-with-parent", "--new-session", "--unshare-all", "--cap-drop", "ALL",
        "--clearenv", "--setenv", "PATH", "/nonexistent", "--setenv", "LANG", "C.UTF-8",
        "--proc", "/proc", "--dev", "/dev",
    ]
    for path in LINUX_SYSTEM_READS:
        argv += ["--ro-bind-try", path, path]
    for path in [*_interpreter_roots(), str(TOOLS), *read]:
        argv += ["--ro-bind", path, path]
    for path in write:
        argv += ["--bind", path, path]
    if write:
        argv += ["--setenv", "TMPDIR", write[0]]
    # bwrap builds the empty parents of each mount on a tmpfs root; make it read-only
    # so a tool can't create files there either (only its own bind stays writable).
    return argv + ["--remount-ro", "/", "--chdir", cwd, "--"]


def wrap(
    argv: Sequence[str],
    *,
    cwd: os.PathLike | str,
    read: Iterable[os.PathLike | str] = (),
    write: Iterable[os.PathLike | str] = (),
    socket_dir: Optional[os.PathLike | str] = None,
    bind_socket: bool = False,
) -> list[str]:
    """The sandboxed argv for one tool process; run it with ``cwd`` as given.

    ``socket_dir`` is the trial's fixture-socket directory: the fixture service
    binds ``fixture.sock`` there (``bind_socket=True``) and the worker connects
    to it by its relative name from ``cwd``.
    """
    reads = [_real(p) for p in read]
    writes = [_real(p) for p in write]
    cwd_real = _real(cwd)
    socket = None if socket_dir is None else os.path.join(_real(socket_dir), SOCKET_NAME)
    if socket_dir is not None and _real(socket_dir) not in reads + writes:
        reads.append(_real(socket_dir))
    sandbox = mode()
    if sandbox == "macos-sandbox-exec":
        profile = macos_profile(read=reads, write=writes, socket=socket, bind_socket=bind_socket)
        return [SANDBOX_EXEC, "-p", profile, *argv]
    return [*linux_argv(read=reads, write=writes, cwd=cwd_real), *argv]


def environment(write: Iterable[os.PathLike | str] = ()) -> dict[str, str]:
    """The only environment a tool process gets: no provider variable, ever."""
    env = {"PATH": os.defpath, "LANG": "C.UTF-8"}
    writes = [_real(p) for p in write]
    if writes:
        env["TMPDIR"] = writes[0]
    return env


def describe() -> str:
    """``mode:version:rules-hash`` for component versions (decision 0023).

    The hash covers the rules, not where this machine keeps them: the
    interpreter, virtual environment, ``tools/``, and ``bwrap`` paths are
    replaced by placeholders, so a mock grid in one checkout and the paid run
    from a clean checkout of the same commit on the same platform agree.
    """
    sandbox = mode()
    template = (
        macos_profile(read=["<read>"], write=["<write>"], socket="<socket>", bind_socket=False)
        if sandbox == "macos-sandbox-exec"
        else " ".join(linux_argv(read=["<read>"], write=["<write>"], cwd="<cwd>"))
    )
    machine_paths = [*_interpreter_roots(), str(TOOLS), shutil.which("bwrap") or ""]
    for path in sorted((p for p in machine_paths if p), key=len, reverse=True):
        template = template.replace(path, "<installed>")
    digest = hashlib.sha256(template.encode("utf-8")).hexdigest()[:16]
    return f"{sandbox}:{VERSION}:{digest}"
