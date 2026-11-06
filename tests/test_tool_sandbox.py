"""Decision 0023: every tool process runs in the sandbox, and no paid call runs
without the project lead's paid-run record.

These are negative tests in real subprocesses on the real platform (sandbox-exec
on macOS, bwrap on Linux CI). A probe launched exactly like the tool worker must
fail to reach anything SPEC.md Section 3 forbids: the network (TCP, UDP, DNS, or
a foreign Unix socket), the provider key file, the home directory, the repository,
the evidence files, the fixture server's log, ``/tmp``, and any other program. It
must still read its fixture root, write its state, and reach its own fixture
socket. The same probe run with no sandbox is the control: each forbidden action
must work there, and each listener must hear it, so a refusal is the sandbox's and
never a bad path or a missing binary. Together with the launch-coverage tests
below, this is the CI proof that no tool can reach an arbitrary external endpoint
(SPEC.md Section 11, Gate 3).
"""

import ast
import json
import os
import re
import shutil
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
import errno, json, os, socket, subprocess, sys
targets = json.loads(sys.argv[1])
control = targets.get("control", False)  # the unwrapped control leaves everything it reaches as it found it
out = {}
def attempt(name, fn):
    # Only a permission error is a refusal on its face. Every other failure keeps its class and errno,
    # so a bad path, a missing binary, or a timeout can't read as containment (see _contained below).
    try:
        fn()
        out[name] = "allowed"
    except PermissionError:
        out[name] = "denied:PermissionError"
    except OSError as exc:
        out[name] = "error:%s:%s" % (type(exc).__name__, errno.errorcode.get(exc.errno, exc.errno))
    except BaseException as exc:
        out[name] = "error:" + type(exc).__name__
def tcp(host, port):
    def f():
        s = socket.socket(); s.settimeout(2); s.connect((host, port)); s.close()
    return f
def unix(path):
    def f():
        s = socket.socket(socket.AF_UNIX); s.settimeout(2); s.connect(path); s.close()
    return f
def udp(payload, port):
    def f():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.sendto(payload, ("127.0.0.1", port)); s.close()
    return f
def route(host, port):
    # Connecting a UDP socket only asks the kernel for a route: no packet leaves, sandboxed or not.
    def f():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect((host, port)); s.close()
    return f
def write(path):
    def f():
        existed = os.path.exists(path)
        with open(path, "a") as handle:
            if not control:
                handle.write("x")
        if control and not existed:
            os.unlink(path)
    return f
attempt("read_fixture", lambda: open(targets["fixture_file"]).read())
attempt("write_state", write(targets["state_file"]))
attempt("own_socket", unix("fixture.sock"))
attempt("read_key_file", lambda: open(targets["key_file"]).read())
attempt("read_repository", lambda: open(targets["repo_file"]).read())
attempt("read_server_log", lambda: open(targets["server_log"]).read())
attempt("read_resolver_config", lambda: open("/etc/resolv.conf").read())
def list_home():
    listing = sorted(os.listdir(targets["home"]))
    if not control:
        out["home_listing"] = listing
attempt("list_home", list_home)
attempt("write_evidence", write(targets["evidence_file"]))
attempt("write_repository", write(targets["repo_write"]))
attempt("write_server_log", write(targets["server_log"]))
attempt("write_tmp", write("/tmp/canary-sandbox-probe"))
attempt("tcp_loopback", tcp("127.0.0.1", targets["tcp_port"]))
attempt("route_external", route("192.0.2.1", 9))  # TEST-NET-1 (RFC 5737)
if "local_address" in targets:
    attempt("tcp_nonloopback", tcp(targets["local_address"], targets["tcp_port"]))  # this machine's own address
if not control:  # a SYN would leave the machine, so the control never sends one; route_external stands in for it
    attempt("tcp_external", tcp("192.0.2.1", 9))
attempt("udp_loopback", udp(b"canary-udp-probe", targets["udp_port"]))
attempt("dns_query", udp(bytes.fromhex(targets["dns_query"]), targets["udp_port"]))  # to a local listener, never a resolver
attempt("dns_system_resolver", lambda: socket.getaddrinfo("localhost", 9))  # the name never leaves the machine
attempt("foreign_socket", unix(targets["foreign_socket"]))
attempt("sibling_socket", unix("sibling.sock"))  # a listener beside fixture.sock in the socket directory
if "planted_socket" in targets:
    attempt("planted_socket", unix(targets["planted_socket"]))
# An exec probe counts as allowed if the program ran at all, whatever its exit code. None of them names a
# URL: even if a sandbox failed, they reach nothing.
for name, program in targets["programs"].items():
    attempt(name, lambda program=program: subprocess.run(program, timeout=3, capture_output=True))
for program in targets.get("library_programs", []):  # programs inside the mounted system-library folders
    attempt("exec_library:" + program[0], lambda program=program: subprocess.run(program, timeout=3, capture_output=True))
out["provider_variables"] = sorted(k for k in os.environ if k.startswith(("ANTHROPIC_", "OPENAI_")))
print(json.dumps(out))
"""

FORBIDDEN = (
    "read_key_file", "read_repository", "read_server_log", "write_evidence", "write_repository",
    "write_server_log", "write_tmp", "tcp_loopback", "foreign_socket", "sibling_socket",
)
# Harmless programs: each only prints its version or usage. A machine without one has nothing to prove with
# it, which is not containment, so _targets leaves it out rather than count its absence as a denial.
PROGRAMS = {
    "exec_shell": ["/bin/sh", "-c", "true"],
    "exec_curl": ["/usr/bin/curl", "--version"],
    **({"exec_open": ["/usr/bin/open", "-h"]} if sys.platform == "darwin" else {}),  # another program on Linux
}
# A well-formed DNS question for a reserved name: one query, A record, class IN.
DNS_QUERY = (bytes.fromhex("ca7a01000001000000000000") + b"\x14canary-sandbox-probe\x07invalid\x00" + bytes.fromhex("00010001"))
# macOS refuses every forbidden action with EPERM. bwrap refuses by absence, and each of these is a sandbox
# refusal only where the unwrapped control shows the action works, so _assert_contained takes both.
LINUX_ABSENCE = {
    "error:FileNotFoundError:ENOENT",  # the path isn't mounted
    "error:OSError:EROFS",  # the read-only root
    "error:OSError:ENETUNREACH",  # an empty network namespace has no route
    "error:ConnectionRefusedError:ECONNREFUSED",  # the namespace's own loopback, where nothing listens
}


def _contained(outcome):
    return outcome == "denied:PermissionError" or (sandbox.mode() == "linux-bwrap" and outcome in LINUX_ABSENCE)


def _assert_contained(names, control, result):
    """Each action works without the sandbox and fails inside it, so the refusal is the sandbox's."""
    for name in names:
        assert control[name] == "allowed", (name, "fails without the sandbox too, so its refusal proves nothing", control[name])
        assert _contained(result[name]), (name, result[name])


@pytest.fixture
def trial(tmp_path, monkeypatch):
    """A trial-shaped layout: fixtures, state, socket dir, and evidence beside them."""
    env = tmp_path / "t" / "env"
    fixtures, state, sock = env / "fixtures", env / "state", env / "sock"
    for path in (fixtures, state, sock):
        path.mkdir(parents=True)
    (fixtures / "doc.txt").write_text("fixture", encoding="utf-8")
    (tmp_path / "t" / "events.jsonl").write_text("", encoding="utf-8")
    (sock / "fixture-requests.jsonl").write_text("", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / ".env").write_text("ANTHROPIC_API_KEY=synthetic-sentinel\n", encoding="utf-8")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic-sentinel")

    listeners = []
    monkeypatch.chdir(sock)
    own = socket.socket(socket.AF_UNIX)
    own.bind("fixture.sock")
    own.listen(4)
    sibling = socket.socket(socket.AF_UNIX)
    sibling.bind("sibling.sock")
    sibling.listen(4)
    monkeypatch.chdir(outside)
    foreign = socket.socket(socket.AF_UNIX)
    foreign.bind("foreign.sock")
    foreign.listen(4)
    tcp = socket.socket()
    tcp.bind(("127.0.0.1", 0))
    tcp.listen(4)
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("127.0.0.1", 0))
    listeners += [own, sibling, foreign, tcp, udp]
    yield {
        "fixtures": fixtures, "state": state, "sock": sock, "outside": outside,
        "tcp_port": tcp.getsockname()[1], "udp_port": udp.getsockname()[1], "listeners": listeners,
        "heard": {"tcp_loopback": tcp, "foreign_socket": foreign, "sibling_socket": sibling}, "own": own, "udp": udp,
    }
    for listener in listeners:
        listener.close()


def _targets(trial):
    return {
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
        "server_log": str(trial["sock"] / "fixture-requests.jsonl"),
        "udp_port": trial["udp_port"],
        "dns_query": DNS_QUERY.hex(),
        "programs": {name: argv for name, argv in PROGRAMS.items() if os.access(argv[0], os.X_OK)},
    }


def _probe(trial, **extra):
    argv = [sys.executable, "-I", "-c", PROBE, json.dumps({**_targets(trial), **extra})]
    completed = subprocess.run(
        sandbox.wrap(argv, cwd=trial["sock"], read=[trial["fixtures"]], write=[trial["state"]], socket_dir=trial["sock"]),
        cwd=trial["sock"], capture_output=True, text=True, timeout=60, env=sandbox.environment([trial["state"]]),
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    return json.loads(completed.stdout)


def _control(trial, **extra):
    """The same probe and targets from the same directory and environment, with no sandbox."""
    argv = [sys.executable, "-I", "-c", PROBE, json.dumps({**_targets(trial), "control": True, **extra})]
    completed = subprocess.run(argv, cwd=trial["sock"], capture_output=True, text=True, timeout=60,
                               env=sandbox.environment([trial["state"]]))
    assert completed.returncode == 0, completed.stderr[-2000:]
    return json.loads(completed.stdout)


def _pending(listener):
    """How many connections a stream listener heard, emptying its queue. A listener hears what an error can't say."""
    listener.setblocking(False)
    count = 0
    while True:
        try:
            connection, _ = listener.accept()
        except BlockingIOError:
            return count
        connection.close()
        count += 1


def _datagrams(listener):
    """Every datagram a listener heard. A loopback send is delivered before it returns."""
    listener.setblocking(False)
    heard = []
    while True:
        try:
            heard.append(listener.recv(4096))
        except BlockingIOError:
            return heard


def _local_address():
    """This machine's own non-loopback address, or None without a default route."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        try:
            probe.connect(("192.0.2.1", 9))  # picks a route; sends nothing
        except OSError:
            return None
        address = probe.getsockname()[0]
    return None if address.startswith("127.") or address == "0.0.0.0" else address


def test_a_sandboxed_tool_reaches_only_its_fixtures_state_and_socket(trial):
    control = _control(trial)
    assert all(_pending(listener) == 1 for listener in trial["heard"].values())  # each was really listening
    assert _pending(trial["own"]) == 1
    result = _probe(trial)
    assert result["read_fixture"] == "allowed"
    assert result["write_state"] == "allowed"
    assert result["own_socket"] == "allowed"
    assert _pending(trial["own"]) == 1
    assert "exec_shell" in _targets(trial)["programs"]
    _assert_contained([*FORBIDDEN, *_targets(trial)["programs"]], control, result)
    assert all(_pending(listener) == 0 for listener in trial["heard"].values())
    # bwrap builds empty parent directories for its mounts, so on Linux the home
    # directory may list; it must show nothing but those synthetic parents.
    if result["list_home"] == "allowed":
        home = Path.home()
        programs, files, dirs, links = sandbox._interpreter()
        mounts = [*programs, *files, *dirs, *(link for link, _ in links), str(sandbox.TOOLS)]
        parents = {Path(m).relative_to(home).parts[0] for m in mounts if Path(m).is_relative_to(home)}
        assert set(result["home_listing"]) <= parents, result["home_listing"]
    else:
        assert _contained(result["list_home"])
    assert result["provider_variables"] == []
    assert not (ROOT / "sandbox-probe-should-not-exist.txt").exists()
    assert (trial["state"].parent.parent / "events.jsonl").read_text(encoding="utf-8") == ""
    # Never reached, so never recorded by the control: a sandbox refusal is all it can show.
    assert _contained(result["tcp_external"]), result["tcp_external"]


def test_a_tool_has_no_route_the_host_has(trial):
    """TEST-NET-1 is routed nowhere even unsandboxed, so ``tcp_external`` alone proves little: this compares routes."""
    address = _local_address()
    if address is None:
        pytest.skip("this machine has no default route to compare with the sandbox's")
    control = _control(trial, local_address=address)
    assert control["route_external"] == "allowed"
    # Refused, not unreachable: the connection reached this machine, where nothing listens on that address.
    assert control["tcp_nonloopback"] == "error:ConnectionRefusedError:ECONNREFUSED"
    result = _probe(trial, local_address=address)
    assert result["route_external"] in ("denied:PermissionError", "error:OSError:ENETUNREACH"), result["route_external"]
    assert result["tcp_nonloopback"] in ("denied:PermissionError", "error:OSError:ENETUNREACH"), result["tcp_nonloopback"]


def test_udp_and_dns_reach_nothing_from_the_sandbox(trial):
    control = _control(trial)
    assert control["udp_loopback"] == control["dns_query"] == control["dns_system_resolver"] == "allowed"
    assert sorted(_datagrams(trial["udp"])) == sorted([b"canary-udp-probe", DNS_QUERY])
    result = _probe(trial)
    # A send on a Linux sandbox's own loopback can succeed and still reach nothing, so the listener decides.
    assert _datagrams(trial["udp"]) == []
    if sandbox.mode() == "macos-sandbox-exec":
        assert result["udp_loopback"] == result["dns_query"] == "denied:PermissionError"
        assert result["dns_system_resolver"].startswith("error:gaierror"), result["dns_system_resolver"]
    # glibc may answer "localhost" itself with no network at all, so on Linux only the resolver's
    # configuration and the wire query above say anything.
    if control["read_resolver_config"] == "allowed":
        assert _contained(result["read_resolver_config"]), result["read_resolver_config"]


def test_a_bad_path_or_missing_binary_never_reads_as_containment(trial):
    control = _control(trial, key_file=str(trial["outside"] / "no-such-file"), foreign_socket="no-such.sock",
                       programs={"exec_curl": ["/nonexistent/curl", "--version"]})
    for name in ("read_key_file", "foreign_socket", "exec_curl"):
        assert control[name] == "error:FileNotFoundError:ENOENT", name
        # Even a clean-looking denial proves nothing when the action fails without the sandbox too.
        with pytest.raises(AssertionError, match=name):
            _assert_contained([name], control, {name: "denied:PermissionError"})
    if sandbox.mode() == "macos-sandbox-exec":
        assert not _contained("error:FileNotFoundError:ENOENT")


@pytest.mark.parametrize("outcome", ["error:TimeoutError", "error:TimeoutExpired", "error:OSError:ENAMETOOLONG",
                                     "error:ValueError", "error:OSError:EINVAL", "error:gaierror:8", "allowed"])
def test_an_unrelated_failure_never_reads_as_containment(outcome):
    assert not _contained(outcome)


def test_a_program_that_only_timed_out_is_not_denied(trial):
    control = _control(trial, programs={"exec_slow": ["/bin/sh", "-c", "sleep 10"]})
    assert control["exec_slow"] == "error:TimeoutExpired"


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


# --- no process starts outside the wrapper ----------------------------------------------------------


LAUNCHERS = {
    "subprocess": {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"},
    "os": {"system", "popen", "fork", "forkpty", "posix_spawn", "posix_spawnp", "execl", "execle", "execlp",
           "execlpe", "execv", "execve", "execvp", "execvpe", "spawnl", "spawnle", "spawnlp", "spawnlpe",
           "spawnv", "spawnve", "spawnvp", "spawnvpe"},
    "asyncio": {"create_subprocess_exec", "create_subprocess_shell"},
    "pty": {"fork", "spawn"},
    "multiprocessing": {"Process", "Pool"},
    "concurrent.futures": {"ProcessPoolExecutor"},
}


def _through_the_wrapper(call):
    """A launch is fine when its argv is ``sandbox.wrap(...)`` written at the call, or a literal ``["git", ...]``.
    An argv built elsewhere fails here on purpose: the wrapper must be visible where the process starts."""
    argv = call.args[0] if call.args else next((k.value for k in call.keywords if k.arg == "args"), None)
    if isinstance(argv, ast.Call):
        func = argv.func
        return isinstance(func, ast.Attribute) and func.attr == "wrap" and isinstance(func.value, ast.Name) and func.value.id == "sandbox"
    return (isinstance(argv, ast.List) and bool(argv.elts) and isinstance(argv.elts[0], ast.Constant)
            and argv.elts[0].value == "git")


def _unsandboxed_launches(source):
    """(line, target) for every call in ``source`` that can start a process outside the wrapper."""
    tree = ast.parse(source)
    modules, names, found = {}, {}, []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules[alias.asname or alias.name.split(".")[0]] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                if alias.name == "*" and node.module in LAUNCHERS:
                    found.append((node.lineno, f"from {node.module} import *"))
                names[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            qualified = f"{modules.get(func.value.id, names.get(func.value.id, func.value.id))}.{func.attr}"
        elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Call):
            inner = func.value.func  # __import__("subprocess").run(...)
            qualified = None
            if isinstance(inner, ast.Name) and inner.id == "__import__" and func.value.args:
                qualified = f"{getattr(func.value.args[0], 'value', '')}.{func.attr}"
        elif isinstance(func, ast.Name):
            qualified = names.get(func.id, func.id)
            if qualified in ("__import__", "importlib.import_module", "getattr") and node.args:
                first = node.args[0]
                module = first.value if isinstance(first, ast.Constant) else modules.get(getattr(first, "id", None))
                if module in LAUNCHERS:
                    found.append((node.lineno, f"{qualified}({module})"))
                continue
        else:
            qualified = None
        if qualified is None:
            continue
        if qualified == "importlib.import_module" and node.args and getattr(node.args[0], "value", None) in LAUNCHERS:
            found.append((node.lineno, f"{qualified}({node.args[0].value})"))
            continue
        module, _, attr = qualified.rpartition(".")
        if attr in LAUNCHERS.get(module, ()) and not _through_the_wrapper(node):
            found.append((node.lineno, qualified))
    return found


def test_no_new_code_starts_a_process_outside_the_wrapper():
    """Every tool launch goes through ``tools.sandbox.wrap`` (decision 0023). A run can only see the paths it runs."""
    found = {}
    scanned = 0
    for path in sorted(ROOT.rglob("*.py")):
        relative = path.relative_to(ROOT)
        if relative.parts[0] in ("tests", "results") or any(part.startswith(".") for part in relative.parts):
            continue
        scanned += 1
        launches = _unsandboxed_launches(path.read_text(encoding="utf-8"))
        if launches:
            found[str(relative)] = launches
    assert scanned > 50
    assert found == {}


@pytest.mark.parametrize("source", [
    "import subprocess, sys\nsubprocess.run([sys.executable, 'tools/worker.py'])",
    "import subprocess\nargv = ['python']\nsubprocess.run(argv)",
    "import subprocess\nsubprocess.Popen(['python', 'tools/fixture_http.py'], stdin=-1)",
    "import subprocess as sp\nsp.call(['python'])",
    "import subprocess as sp\nsp.check_output(['python'])",
    "from subprocess import Popen\nPopen(['python'])",
    "from subprocess import run as launch\nlaunch(['python'])",
    "from subprocess import *\nrun(['python'])",
    "import os\nos.system('python')",
    "import os\nos.popen('python')",
    "import os\nos.execv('/bin/sh', ['sh'])",
    "import os\nos.fork()",
    "from os import posix_spawn\nposix_spawn('/bin/sh', ['sh'], {})",
    "import asyncio\nasyncio.create_subprocess_exec('python')",
    "import multiprocessing\nmultiprocessing.Process(target=print)",
    "import concurrent.futures as cf\ncf.ProcessPoolExecutor()",
    "import pty\npty.spawn('sh')",
    "__import__('subprocess').run(['python'])",
    "__import__('subprocess')",
    "import importlib\nimportlib.import_module('subprocess')",
    "from importlib import import_module\nimport_module('subprocess')",
    "import subprocess\ngetattr(subprocess, 'run')(['python'])",
    "import subprocess\nsubprocess.run(sandbox.other(['python']))",
    "import subprocess\nsubprocess.run(['gitx', 'status'])",
    "import subprocess\nsubprocess.run(args=['python'])",
])
def test_the_launch_scan_catches(source):
    assert _unsandboxed_launches(source), source


@pytest.mark.parametrize("source", [
    "import subprocess\nsubprocess.run(sandbox.wrap(argv, cwd=root), cwd=root)",
    "import subprocess\nsubprocess.Popen(sandbox.wrap(argv, cwd=root), stdin=subprocess.PIPE)",
    "import subprocess\nsubprocess.run(['git', 'rev-parse', 'HEAD'], check=True)",
    "import subprocess\nsubprocess.run(args=sandbox.wrap(argv, cwd=root))",
    "import subprocess\nexcept_types = (subprocess.SubprocessError, subprocess.TimeoutExpired)",
])
def test_the_launch_scan_accepts(source):
    assert _unsandboxed_launches(source) == []


# --- what each platform's rules expose (#64 review) -----------------------------------------------


TOOL_ARGV = [sys.executable, "-I", "tool.py"]
# Harmless programs that live inside a platform's mounted system-library folders: each only prints
# its version or usage, so even a failed sandbox runs nothing that matters.
LIBRARY_PROGRAMS = {
    "linux-bwrap": [
        ["/usr/lib/git-core/git", "--version"],
        ["/lib64/ld-linux-x86-64.so.2", "--version"],
        ["/lib/ld-linux-aarch64.so.1", "--version"],
    ],
    "macos-sandbox-exec": [
        ["/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"],
    ],
}


def test_a_program_inside_a_mounted_library_folder_never_runs(trial):
    """Decision 0023 lets a tool read the system libraries, and run only the interpreter."""
    running = sandbox.mode()
    reads = sandbox.LINUX_SYSTEM_READS if running == "linux-bwrap" else sandbox.MACOS_SYSTEM_READS
    programs = [p for p in LIBRARY_PROGRAMS[running]
                if os.access(p[0], os.X_OK) and sandbox._under(p[0], reads) and sandbox._under(os.path.realpath(p[0]), reads)]
    assert programs, "no library-folder program to probe on this machine"
    if running == "linux-bwrap":
        # The control: the probe's own launch with only the exec filter taken out. The mounts alone
        # let every one of these programs run (#64 review).
        argv = [sys.executable, "-I", "-c", PROBE, json.dumps({**_targets(trial), "library_programs": programs})]
        launch = sandbox.wrap(argv, cwd=trial["sock"], read=[trial["fixtures"]], write=[trial["state"]],
                              socket_dir=trial["sock"])
        start = launch.index("--") + 1
        assert launch[start:start + 3] == [sys.executable, "-I", str(sandbox.NO_EXEC)]
        control = subprocess.run(
            [*launch[:start], *launch[start:start + 2], *launch[start + 3:]],
            cwd=trial["sock"], capture_output=True, text=True, timeout=60, env=sandbox.environment([trial["state"]]))
        assert control.returncode == 0, control.stderr[-2000:]
        ran = json.loads(control.stdout)
        assert all(ran["exec_library:" + p[0]] == "allowed" for p in programs), ran
    result = _probe(trial, library_programs=programs)
    for program in programs:
        outcome = result["exec_library:" + program[0]]
        assert outcome == "denied:PermissionError" if running == "linux-bwrap" else outcome.startswith("denied"), \
            (program, outcome)


def _linux_mounts(argv):
    """Each (kind, destination) a bwrap argv mounts or links inside the sandbox."""
    mounts, i = [], 0
    while i < len(argv) and argv[i] != "--":
        if argv[i] in ("--ro-bind", "--ro-bind-try", "--bind", "--symlink"):
            mounts.append((argv[i], argv[i + 2]))
            i += 3
        else:
            i += 1
    return mounts


def _visible(path, mounts):
    return any(path == dest or path.startswith(dest.rstrip("/") + "/") for kind, dest in mounts if kind != "--symlink")


def _profile_paths(profile, rule):
    """The (filter, path) pairs one allow rule of a macOS profile names."""
    line = next(line for line in profile.splitlines() if line.startswith(f"(allow {rule} "))
    return re.findall(r'\((subpath|literal) "([^"]*)"\)', line)


def _allowed(path, filters):
    return any(path == p or (kind == "subpath" and path.startswith(p.rstrip("/") + "/")) for kind, p in filters)


@pytest.fixture
def system_python(tmp_path, monkeypatch):
    """A distro interpreter: ``usr/bin/pythonX.Y`` beside other programs, its stdlib in ``usr/lib``."""
    usr = (tmp_path / "usr").resolve()
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    (usr / "bin").mkdir(parents=True)
    (usr / "lib" / version).mkdir(parents=True)
    (usr / "lib" / version / "os.py").write_text("", encoding="utf-8")
    for name in (version, "curl"):
        (usr / "bin" / name).write_bytes(b"")
        (usr / "bin" / name).chmod(0o755)
    monkeypatch.setattr(sys, "executable", str(usr / "bin" / version))
    for name in ("prefix", "base_prefix", "exec_prefix", "base_exec_prefix"):
        monkeypatch.setattr(sys, name, str(usr))
    return usr


def test_a_system_python_exposes_only_the_interpreter_on_linux(system_python):
    mounts = _linux_mounts(sandbox.linux_argv(read=[], write=[], cwd="/"))
    version = Path(sys.executable).name
    assert _visible(sys.executable, mounts)
    assert _visible(str(system_python / "lib" / version / "os.py"), mounts)
    for hidden in (system_python, system_python / "bin", system_python / "bin" / "curl"):
        assert not _visible(str(hidden), mounts), hidden


def test_a_system_python_runs_and_reads_only_the_interpreter_on_macos(system_python):
    profile = sandbox.macos_profile(read=[], write=[], socket=None, bind_socket=False)
    curl = str(system_python / "bin" / "curl")
    assert _allowed(sys.executable, _profile_paths(profile, "process-exec"))
    assert not _allowed(curl, _profile_paths(profile, "process-exec"))
    assert not _allowed(curl, _profile_paths(profile, "file-read*"))


@pytest.fixture
def linux(monkeypatch):
    """Generate the bwrap arguments on any platform."""
    monkeypatch.setattr(sandbox, "mode", lambda: "linux-bwrap")


def _plant(directory, monkeypatch, name="planted.sock"):
    """A foreign listener in ``directory``, bound by a short relative name (macOS caps socket paths)."""
    monkeypatch.chdir(directory)
    listener = socket.socket(socket.AF_UNIX)
    listener.bind(name)
    listener.listen(1)
    return listener


def test_on_linux_every_tool_runs_behind_the_exec_filter(tmp_path, linux):
    argv = sandbox.wrap([sys.executable, "-I", "tool.py", "arg"], cwd=tmp_path, write=[tmp_path])
    assert argv[argv.index("--") + 1:] == [sys.executable, "-I", str(sandbox.NO_EXEC), "tool.py", "arg"]
    assert _visible(str(sandbox.NO_EXEC), _linux_mounts(argv))
    assert "--as-pid-1" in argv  # no unfiltered process shares the tool's sandbox


@pytest.mark.parametrize("argv", [["/bin/sh", "-c", "true"], [sys.executable, "tool.py"],
                                  [sys.executable, "-I", "-u", "tool.py"], [sys.executable, "-I"],
                                  [sys.executable, "-I", "-c"]])
def test_on_linux_only_the_isolated_interpreter_launches(tmp_path, linux, argv):
    with pytest.raises(sandbox.SandboxUnavailable, match="-I"):
        sandbox.wrap(argv, cwd=tmp_path, write=[tmp_path])


def test_linux_refuses_a_machine_without_an_exec_filter(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(sandbox.shutil, "which", lambda name: "/usr/bin/bwrap")
    monkeypatch.setattr(sandbox.os, "uname", lambda: os.uname_result(("Linux", "h", "6", "1", "riscv64")))
    with pytest.raises(sandbox.SandboxUnavailable, match="riscv64"):
        sandbox.mode()
    monkeypatch.setattr(sandbox.os, "uname", lambda: os.uname_result(("Linux", "h", "6", "1", "x86_64")))
    monkeypatch.setattr(sandbox.struct, "calcsize", lambda fmt: 4)
    with pytest.raises(sandbox.SandboxUnavailable, match="32-bit"):
        sandbox.mode()


def _run_filter(program, nr, arch):
    """Evaluate a seccomp cBPF program (the four opcodes it uses) on one syscall."""
    data = {0: nr, 4: arch}
    accumulator, pc = 0, 0
    while True:
        code, jt, jf, k = program[pc]
        if code == 0x20:  # BPF_LD | BPF_W | BPF_ABS
            accumulator, pc = data[k], pc + 1
        elif code in (0x15, 0x35):  # BPF_JMP | BPF_JEQ / BPF_JGE, with a constant
            taken = accumulator == k if code == 0x15 else accumulator >= k
            pc += 1 + (jt if taken else jf)
        elif code == 0x06:  # BPF_RET
            return k
        else:
            raise AssertionError(f"unexpected opcode {code:#x}")


# Written out from <linux/audit.h> and each architecture's unistd.h, not read from no_exec, so a wrong
# number there fails here: audit arch, then execve, execveat, ptrace, and process_vm_writev.
SYSCALLS = {"x86_64": (0xC000003E, (59, 322, 101, 311)), "aarch64": (0xC00000B7, (221, 281, 117, 271))}
EPERM, ALLOW, KILL_PROCESS = 0x00050000 | 1, 0x7FFF0000, 0x80000000


@pytest.mark.parametrize("machine", ["x86_64", "aarch64"])
def test_the_exec_filter_fails_exactly_the_calls_that_start_a_program(machine):
    from tools import no_exec

    arch, denied = SYSCALLS[machine]
    program = no_exec.program(machine)
    for nr in denied:
        assert _run_filter(program, nr, arch) == EPERM, nr
    for nr in range(0, 460):
        if nr not in denied:
            assert _run_filter(program, nr, arch) == ALLOW, nr
    if machine == "x86_64":
        for nr in (0x40000000 | 520, 0x40000000 | 545):  # x32's execve and execveat
            assert _run_filter(program, nr, arch) == EPERM
    assert _run_filter(program, 11, 0x40000003) == KILL_PROCESS  # i386's execve, another ABI


def test_on_linux_the_worker_mounts_the_fixture_socket_alone(trial, linux):
    sock = str(trial["sock"].resolve())
    client = sandbox.wrap(TOOL_ARGV, cwd=trial["sock"], read=[trial["fixtures"]], write=[trial["state"]],
                          socket_dir=trial["sock"])
    mounts = _linux_mounts(client)
    assert ("--ro-bind", os.path.join(sock, sandbox.SOCKET_NAME)) in mounts
    assert not _visible(os.path.join(sock, "sibling.sock"), mounts)


@pytest.mark.parametrize("where", ["fixtures", "state"])
def test_on_linux_a_foreign_socket_in_a_mounted_directory_refuses_the_worker(trial, linux, monkeypatch, where):
    trial["listeners"].append(_plant(trial[where], monkeypatch))
    with pytest.raises(sandbox.SandboxUnavailable, match="planted.sock"):
        sandbox.wrap(TOOL_ARGV, cwd=trial["sock"], read=[trial["fixtures"]], write=[trial["state"]],
                     socket_dir=trial["sock"])


def test_on_linux_a_foreign_socket_beside_the_fixture_socket_refuses_the_service(trial, linux):
    # The service writes the socket directory, so the trial fixture's sibling.sock is mounted for it.
    with pytest.raises(sandbox.SandboxUnavailable, match="sibling.sock"):
        sandbox.wrap(TOOL_ARGV, cwd=trial["sock"], read=[trial["fixtures"]], write=[trial["sock"]],
                     socket_dir=trial["sock"], bind_socket=True)


def test_a_foreign_listener_inside_the_fixtures_is_never_reached(trial, monkeypatch):
    trial["listeners"].append(_plant(trial["fixtures"], monkeypatch))
    planted = os.path.relpath(trial["fixtures"] / "planted.sock", trial["sock"])
    if sandbox.mode() == "linux-bwrap":
        with pytest.raises(sandbox.SandboxUnavailable, match="planted.sock"):
            _probe(trial, planted_socket=planted)
    else:
        assert _probe(trial, planted_socket=planted)["planted_socket"].startswith("denied")


# --- the paid-run record --------------------------------------------------------------------------


class RealProvider:
    adapter_version = "real-adapter-test"

    def complete(self, *args):  # pragma: no cover - the gate refuses before any call
        raise AssertionError("a paid provider was called")


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


def test_a_valid_record_opens_paid_runs_for_exactly_that_code(gate):
    record = gate.open()
    assert gate.refusal(record) is None

    (gate.root / "runner" / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    assert "uncommitted" in gate.refusal(record)
    gate.git("commit", "-qam", "change")
    assert "code differs" in gate.refusal(record)


def test_a_record_from_another_sandbox_or_malformed_is_refused(gate):
    healthy = gate.record()
    other = "linux-bwrap:tool-sandbox-v0.0.0:0000000000000000"
    if sandbox.describe().startswith("linux-bwrap"):
        other = "macos-sandbox-exec:tool-sandbox-v0.0.0:0000000000000000"
    assert "isn't the recorded mock grid's" in gate.refusal(gate.commit_record({**healthy, "sandbox": other}))
    assert "doesn't validate" in gate.refusal(gate.commit_record({**healthy, "recorded_by": ""}))


def test_the_live_smoke_is_the_one_exception(gate, tmp_path):
    assert gate.refusal(tmp_path / "missing.json", live_smoke=True) is None


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


# --- the mock preflight behind the record (#64 review) --------------------------------------------


class Killed(BaseException):
    """A forced stop; not an Exception, so the runner doesn't catch it."""


def test_the_record_refuses_a_preflight_of_code_committed_since(gate):
    assert gate.record()["code_sha256"] == paid_run.code_hashes(gate.root)
    gate.commit_code("runner/code.py", "VALUE = 2\n")
    with pytest.raises(paid_run.PaidRunRefused, match="other code"):
        gate.record()


def test_the_record_refuses_a_preflight_run_with_uncommitted_code(gate):
    extra = gate.root / "runner" / "extra.py"  # untracked, so the committed hashes alone can't see it
    extra.write_text("VALUE = 3\n", encoding="utf-8")
    gate.rerun()
    extra.unlink()
    with pytest.raises(paid_run.PaidRunRefused, match="uncommitted"):
        gate.record()


def test_the_record_refuses_a_preflight_on_another_corpus(gate, tmp_path):
    gate.rerun(shutil.copytree(gate.root / "corpus" / "development", tmp_path / "other-corpus"))
    with pytest.raises(paid_run.PaidRunRefused, match="corpus"):
        gate.record()


def test_every_invocation_records_its_code_even_when_stopped(gate, tmp_path):
    from runner import execute, grid_dev
    from runner.mock_provider import MOCK_MODEL_ID

    def stopped(trial, canaries):
        raise Killed()

    spec = {**gate.spec, "model_id": MOCK_MODEL_ID}
    with pytest.raises(Killed):
        execute.run_schedule(tmp_path / "mock", grid_dev.validate_grid_spec(spec)[:1], spec=spec, delivery=True,
                             corpus_root=gate.root / "corpus" / "development", provider_factory=stopped)
    lines = [json.loads(line) for line in (tmp_path / "mock" / paid_run.PROVENANCE_FILE).read_text().splitlines()]
    assert [line["phase"] for line in lines] == ["start", "stop"]
    assert {line["code_digest"] for line in lines} == {paid_run.code_digest(paid_run.code_hashes(gate.root))}
    assert all(line["dirty_paths"] == [] for line in lines)


def test_the_record_refuses_a_preflight_that_stopped_unrecorded(gate):
    provenance = gate.mock / paid_run.PROVENANCE_FILE
    provenance.write_text(provenance.read_text().splitlines()[0] + "\n")  # killed before its stop line
    with pytest.raises(paid_run.PaidRunRefused, match="without recording"):
        gate.record()


def test_a_paid_provider_must_ask_for_one_tool_call_per_reply(monkeypatch):
    """Decision 0026 item 3 is enforced where paid runs open, not only recorded."""
    monkeypatch.setattr(paid_run, "paid_run_refusal", lambda **kwargs: None)
    class Undeclared:
        pass
    class Parallel:
        request_settings = {"tool_choice": {"type": "auto", "disable_parallel_tool_use": False}}
    class Falsy:
        request_settings = {"parallel_tool_calls": 0}
    for provider in (Undeclared(), Parallel(), Falsy()):
        for live_smoke in (False, True):
            with pytest.raises(paid_run.PaidRunRefused, match="one tool call"):
                paid_run.require_paid_run(provider, live_smoke=live_smoke)
    from agent.anthropic_adapter import AnthropicMessagesAdapter
    from agent.openai_adapter import OpenAIChatAdapter
    for adapter in (AnthropicMessagesAdapter, OpenAIChatAdapter):
        assert adapter.request_settings in paid_run.ONE_CALL_SETTINGS
        paid_run.require_paid_run(adapter.__new__(adapter), live_smoke=True)
