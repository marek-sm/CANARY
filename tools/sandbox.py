"""Operating-system sandbox for every tool process (audit F-01; decision 0023).

SPEC.md Section 3 holds under every configuration, D0_BASELINE included: tool
processes run non-root, with a read-only filesystem except their explicit
per-trial state, with no arbitrary network route, and without the hosted-model
credential. Every tool launch therefore goes through ``wrap``, which denies by
default and allows only:

* running the interpreter;
* reading the interpreter, ``tools/``, the system libraries, and the
  directories the caller names (the trial's fixtures);
* writing only the directories the caller names (the trial's state);
* reaching only the trial's fixture Unix socket, by path. There is no TCP or UDP
  at all, no other socket, no other program, and no system service.

The interpreter is its own files, never the directories that hold them: the
executable and the links that lead to it, ``pyvenv.cfg``, the standard library,
and the installation's shared libraries. A distro interpreter in ``/usr/bin``
exposes neither ``/usr`` nor ``/usr/bin``.

On macOS this is ``sandbox-exec`` with a deny-by-default profile that runs only
the interpreter and names the fixture socket's path. On Linux it is ``bwrap``
with every namespace unshared and only the named paths mounted. A Linux mount
can't stop what it holds from running or being connected to, so every Linux
tool starts through ``no_exec.py``, whose seccomp filter fails every attempt to
run a program, including those in the mounted system-library folders; and the
worker gets the fixture socket alone, never its directory, and a launch refuses
when any other socket sits in a directory it would mount. Root-owned system
library directories aren't checked for sockets: a socket there needs root. Any other
platform or Linux machine, a missing sandbox binary, or a root user refuses, so a tool launch
fails closed rather than running unconfined. The mode, version, and the hash of
the rendered rules are recorded with every trial's component versions.
"""

from __future__ import annotations

import functools
import glob
import hashlib
import os
import shutil
import stat
import struct
import sys
import sysconfig
from pathlib import Path
from typing import Iterable, Optional, Sequence

from tools import no_exec

VERSION = "tool-sandbox-v0.3.0"
SOCKET_NAME = "fixture.sock"
TOOLS = Path(__file__).resolve().parent
NO_EXEC = TOOLS / "no_exec.py"
SANDBOX_EXEC = "/usr/bin/sandbox-exec"
# Read-only system locations the interpreter needs to start. No /usr/bin, /etc,
# /var, /home, /run, or user directory is ever readable.
MACOS_SYSTEM_READS = ("/System", "/usr/lib", "/private/var/db/dyld")
LINUX_SYSTEM_READS = ("/usr/lib", "/usr/lib64", "/lib", "/lib64", "/etc/ld.so.cache")


class SandboxUnavailable(RuntimeError):
    """No supported sandbox on this machine; the tool launch is refused."""


def _real(path: os.PathLike | str) -> str:
    return os.path.realpath(os.fspath(path))


def _forms(path: os.PathLike | str) -> list[str]:
    """``path`` as written and resolved: uv, for one, points a venv at a
    minor-version link whose target is the real install."""
    return sorted({os.path.abspath(path), _real(path)})


def _under(path: str, roots: Iterable[str]) -> bool:
    return any(path == root or path.startswith(root.rstrip("/") + "/") for root in roots)


def _executable_chain() -> tuple[list[tuple[str, str]], str]:
    """The links from ``sys.executable`` to the interpreter binary, as (link,
    target) pairs, and the binary as the last link names it."""
    links: list[tuple[str, str]] = []
    path = os.path.abspath(sys.executable)
    while os.path.islink(path):
        if len(links) == 40:
            raise SandboxUnavailable(f"too many links from {sys.executable}")
        target = os.readlink(path)
        links.append((path, target))
        path = os.path.normpath(os.path.join(os.path.dirname(path), target))
    return links, path


def _install_roots(binary: str) -> list[str]:
    """The base installation, as the interpreter, its binary, and ``pyvenv.cfg`` name it."""
    roots = {*_forms(sys.base_prefix), *_forms(sys.base_exec_prefix), *_forms(Path(binary).parent.parent)}
    try:
        lines = (Path(sys.prefix) / "pyvenv.cfg").read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []
    for line in lines:
        key, _, value = line.partition("=")
        if key.strip() == "home" and value.strip():
            roots.update(_forms(Path(value.strip()).parent))
    return sorted(roots)


def _interpreter() -> tuple[list[str], list[str], list[str], list[tuple[str, str]]]:
    """What the interpreter needs and nothing beside it: the programs it runs,
    the files and directories it reads, and the links that lead to it."""
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    framework = sysconfig.get_config_var("PYTHONFRAMEWORK") or ""
    links, binary = _executable_chain()
    programs, files, dirs = set(_forms(binary)), set(), set()
    for root in _install_roots(binary):
        for lib in (os.path.join(root, "lib"), os.path.join(root, "lib64")):
            if os.path.isdir(os.path.join(lib, version)):
                dirs.add(os.path.join(lib, version))  # the standard library and its extension modules
            for pattern in ("*.so", "*.so.*", "*.dylib"):  # libpython and what the extensions link
                files.update(p for p in glob.glob(os.path.join(glob.escape(lib), pattern)) if os.path.isfile(p))
        if framework:  # a macOS framework build: its library, and the Python.app its binary runs
            app = os.path.join(root, "Resources", "Python.app", "Contents", "MacOS", framework)
            if os.path.isfile(app):
                programs.add(app)
                dirs.add(os.path.join(root, "Resources"))
            if os.path.isfile(os.path.join(root, framework)):
                files.add(os.path.join(root, framework))
    cfg = Path(sys.prefix) / "pyvenv.cfg"
    if cfg.is_file():
        files.update(_forms(cfg))
    return sorted(programs), sorted(files), sorted(dirs), links


def _sockets(path: str) -> list[str]:
    """Every socket at or under ``path``. An unreadable directory refuses: a
    socket in it could still be reached by name."""
    def unreadable(exc: OSError) -> None:
        raise SandboxUnavailable(f"can't check {exc.filename} for sockets: {exc.strerror}")

    found = []
    for directory, _, names in os.walk(path, onerror=unreadable) if os.path.isdir(path) else [("", [], [path])]:
        for name in names:
            candidate = os.path.join(directory, name)
            try:
                if stat.S_ISSOCK(os.lstat(candidate).st_mode):
                    found.append(candidate)
            except FileNotFoundError:
                pass
    return found


@functools.lru_cache(maxsize=None)
def _interpreter_sockets(dirs: tuple[str, ...]) -> tuple[str, ...]:
    """The installed interpreter doesn't change during a run, so it's checked once per process."""
    return tuple(found for path in dirs for found in _sockets(path))


def _refuse_foreign_sockets(dirs: Iterable[str], socket: Optional[str]) -> None:
    found = [*_interpreter_sockets(tuple(_interpreter()[2])), *(f for path in dirs for f in _sockets(path))]
    foreign = sorted({path for path in found if path != socket})
    if foreign:
        raise SandboxUnavailable("a socket other than the fixture socket is in a directory the tool would mount: "
                                 + ", ".join(foreign[:3]))


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
        if os.uname().machine not in no_exec.ARCHES or struct.calcsize("P") != 8:
            raise SandboxUnavailable(f"no exec filter for {os.uname().machine} with a {struct.calcsize('P') * 8}-bit "
                                     "Python; use 64-bit Python on x86_64 or aarch64 Linux")
        return "linux-bwrap"
    raise SandboxUnavailable(f"no supported tool sandbox on {sys.platform}; use macOS or Linux (WSL2 on Windows)")


def _quote(path: str) -> str:
    if any(ch in path for ch in '"\\\n\0'):
        raise SandboxUnavailable(f"refusing a sandbox path with control characters: {path!r}")
    return f'"{path}"'


def macos_profile(*, read: Sequence[str], write: Sequence[str], socket: Optional[str], bind_socket: bool) -> str:
    programs, files, dirs, _ = _interpreter()
    subpaths = [*dirs, str(TOOLS), *MACOS_SYSTEM_READS, *read, *write]
    lines = [
        "(version 1)",
        "(deny default)",
        "(allow process-exec " + " ".join(f"(literal {_quote(p)})" for p in programs) + ")",
        "(allow file-read-metadata)",
        "(allow file-read* (literal \"/\") "
        + " ".join(f"(literal {_quote(p)})" for p in [*programs, *files])
        + " " + " ".join(f"(subpath {_quote(p)})" for p in subpaths)
        + ' (literal "/dev/null") (literal "/dev/urandom"))',
        "(allow file-write* " + " ".join(f"(subpath {_quote(p)})" for p in write) + ' (literal "/dev/null"))',
    ]
    if socket is not None:
        rule = "network-bind (local" if bind_socket else "network-outbound (remote"
        lines.append(f"(allow {rule} unix-socket (path-literal {_quote(socket)})))")
    return "\n".join(lines) + "\n"


def linux_argv(*, read: Sequence[str], write: Sequence[str], cwd: str,
               socket: Optional[str] = None, bind_socket: bool = False) -> list[str]:
    programs, files, dirs, links = _interpreter()
    argv = [
        shutil.which("bwrap") or "bwrap",
        "--die-with-parent", "--new-session", "--unshare-all", "--as-pid-1", "--cap-drop", "ALL",
        "--clearenv", "--setenv", "PATH", "/nonexistent", "--setenv", "LANG", "C.UTF-8",
        "--proc", "/proc", "--dev", "/dev",
    ]
    for path in LINUX_SYSTEM_READS:
        argv += ["--ro-bind-try", path, path]
    mounted = [*LINUX_SYSTEM_READS, *dirs, str(TOOLS), *read]
    for path in mounted[len(LINUX_SYSTEM_READS):]:
        argv += ["--ro-bind", path, path]
    for path in [*files, *programs]:
        if not _under(path, mounted):
            argv += ["--ro-bind", path, path]
    for link, target in links:  # recreated, so the loader finds libraries beside the real binary
        if not _under(link, mounted):
            argv += ["--symlink", target, link]
    if socket is not None and not bind_socket and not _under(socket, mounted):
        # The worker connects to the fixture socket, mounted alone: any socket in a
        # mounted directory would be reachable too.
        argv += ["--ro-bind", socket, socket]
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
    sandbox = mode()
    if sandbox == "macos-sandbox-exec":
        profile = macos_profile(read=reads, write=writes, socket=socket, bind_socket=bind_socket)
        return [SANDBOX_EXEC, "-p", profile, *argv]
    if list(argv[:2]) != [sys.executable, "-I"] or len(argv) < 3 or len(argv) < 4 and argv[2] == "-c" \
            or (argv[2].startswith("-") and argv[2] != "-c"):
        raise SandboxUnavailable(f"a sandboxed tool runs as {sys.executable} -I SCRIPT or -I -c CODE, "
                                 f"not {list(argv[:3])}")
    _refuse_foreign_sockets([*reads, *writes, str(TOOLS)], socket)
    # The exec filter goes on before the tool's first line runs (no_exec.py).
    return [*linux_argv(read=reads, write=writes, cwd=cwd_real, socket=socket, bind_socket=bind_socket),
            sys.executable, "-I", str(NO_EXEC), *argv[2:]]


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
    interpreter's files and links, ``tools/``, and ``bwrap`` paths are
    replaced by placeholders, so a mock grid in one checkout and the paid run
    from a clean checkout of the same commit on the same platform agree.
    """
    sandbox = mode()
    template = (
        macos_profile(read=["<read>"], write=["<write>"], socket="<socket>", bind_socket=False)
        if sandbox == "macos-sandbox-exec"
        else " ".join([*linux_argv(read=["<read>"], write=["<write>"], cwd="<cwd>", socket="<socket>"),
                       hashlib.sha256(NO_EXEC.read_bytes()).hexdigest()])
    )
    programs, files, dirs, links = _interpreter()
    machine_paths = [*programs, *files, *dirs, *(p for link in links for p in link if os.path.isabs(p)),
                     str(TOOLS), shutil.which("bwrap") or ""]
    for path in sorted((p for p in machine_paths if p), key=len, reverse=True):
        template = template.replace(path, "<installed>")
    digest = hashlib.sha256(template.encode("utf-8")).hexdigest()[:16]
    return f"{sandbox}:{VERSION}:{digest}"
