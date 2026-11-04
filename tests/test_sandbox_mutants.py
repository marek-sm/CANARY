"""Tool-sandbox rules that mutation testing found unpinned
(reports/cloud/mutation.md). Each test names the surviving mutants it kills.

The macOS profile is a pure function of the interpreter's paths and the
caller's arguments, so these run on Linux too, where CI never launches
sandbox-exec and every macos_profile mutant survived.
"""

import os
import re
import sys
import sysconfig

import pytest

from tests.test_tool_sandbox import _linux_mounts, _plant, _visible, system_python  # noqa: F401
from tools import sandbox


def _allow_rules(profile):
    return [line for line in profile.splitlines() if line.startswith("(allow ")]


@pytest.mark.parametrize("bind", [False, True])
def test_the_macos_profile_denies_by_default_and_allows_only_its_named_rules(tmp_path, bind):
    # Kills x_macos_profile__mutmut_3..56: version and default-deny lines, the exec,
    # read, write, and socket rules, their separators, and the trailing newline.
    read, write, sock = str(tmp_path / "fixtures"), str(tmp_path / "state"), str(tmp_path / "sock" / "fixture.sock")
    write2 = str(tmp_path / "state2")
    profile = sandbox.macos_profile(read=[read], write=[write, write2], socket=sock, bind_socket=bind)
    programs, files, dirs, _ = sandbox._interpreter()
    lines = profile.split("\n")
    assert lines[:2] == ["(version 1)", "(deny default)"]
    assert profile.endswith(")\n") and not profile.endswith("\n\n")
    rules = _allow_rules(profile)
    assert [r.split(" ", 2)[1] for r in rules] == [
        "process-exec", "file-read-metadata)", "file-read*", "file-write*", "network-bind" if bind else "network-outbound",
    ]
    assert rules[0] == "(allow process-exec " + " ".join(f'(literal "{p}")' for p in programs) + ")"
    assert rules[1] == "(allow file-read-metadata)"
    reads = re.findall(r'\((subpath|literal) "([^"]*)"\)', rules[2])
    assert ("subpath", read) in reads and ("subpath", write) in reads
    assert ("subpath", str(sandbox.TOOLS)) in reads
    assert ("literal", "/") in reads and ("literal", "/dev/null") in reads and ("literal", "/dev/urandom") in reads
    assert {p for kind, p in reads if kind == "literal"} == {"/", *programs, *files, "/dev/null", "/dev/urandom"}
    assert {p for kind, p in reads if kind == "subpath"} == {*dirs, str(sandbox.TOOLS), *sandbox.MACOS_SYSTEM_READS,
                                                            read, write, write2}
    subpaths = [*dirs, str(sandbox.TOOLS), *sandbox.MACOS_SYSTEM_READS, read, write, write2]
    assert rules[2] == (
        '(allow file-read* (literal "/") '
        + " ".join(f'(literal "{p}")' for p in [*programs, *files])
        + " " + " ".join(f'(subpath "{p}")' for p in subpaths)
        + ' (literal "/dev/null") (literal "/dev/urandom"))'
    )
    assert rules[3] == f'(allow file-write* (subpath "{write}") (subpath "{write2}") (literal "/dev/null"))'
    if bind:
        assert rules[4] == f'(allow network-bind (local unix-socket (path-literal "{sock}")))'
    else:
        assert rules[4] == f'(allow network-outbound (remote unix-socket (path-literal "{sock}")))'


def test_the_macos_profile_without_a_socket_allows_no_network():
    profile = sandbox.macos_profile(read=[], write=[], socket=None, bind_socket=False)
    assert "network" not in profile
    assert [r.split(" ", 2)[1] for r in _allow_rules(profile)] == [
        "process-exec", "file-read-metadata)", "file-read*", "file-write*"]


@pytest.mark.parametrize("bad", ['/tmp/a"b', "/tmp/a\\b", "/tmp/a\nb", "/tmp/a\0b"])
def test_a_profile_path_with_a_quote_or_control_character_is_refused(bad):
    # Kills x__quote__mutmut_3/4: a quote in a path could close the profile's string and
    # add a rule.
    with pytest.raises(sandbox.SandboxUnavailable, match="^refusing a sandbox path with control characters: "):
        sandbox.macos_profile(read=[bad], write=[], socket=None, bind_socket=False)
    assert sandbox._quote("/tmp/plain path") == '"/tmp/plain path"'
    assert sandbox._quote("/tmp/XX") == '"/tmp/XX"'



# --- describe(): what the paid-run record binds to ----------------------------


@pytest.fixture
def linux(monkeypatch):
    monkeypatch.setattr(sandbox, "mode", lambda: "linux-bwrap")


def test_describe_hashes_the_linux_rules_it_would_launch_with(linux, monkeypatch):
    # Kills x_describe__mutmut_3/4/20..22 (the macOS profile hashed on Linux) and _24..40
    # (other placeholder arguments): the record's sandbox string must change whenever
    # the bwrap rules do, and must cover the socket mount.
    calls = []
    real = sandbox.linux_argv

    def recording(**kwargs):
        calls.append(kwargs)
        return real(**kwargs)

    monkeypatch.setattr(sandbox, "linux_argv", recording)
    before = sandbox.describe()
    assert calls == [{"read": ["<read>"], "write": ["<write>"], "cwd": "<cwd>", "socket": "<socket>"}]
    assert before.startswith(f"linux-bwrap:{sandbox.VERSION}:") and len(before.split(":")[-1]) == 16
    monkeypatch.setattr(sandbox, "linux_argv", lambda **kwargs: [*real(**kwargs), "--share-net"])
    assert sandbox.describe() != before
    monkeypatch.setattr(sandbox, "linux_argv", real)
    monkeypatch.setattr(sandbox, "macos_profile", lambda **kwargs: "(allow default)\n")
    assert sandbox.describe() == before


def test_describe_hashes_the_exec_filter(linux, monkeypatch, tmp_path):
    before = sandbox.describe()
    changed = tmp_path / "no_exec.py"
    changed.write_bytes(sandbox.NO_EXEC.read_bytes() + b"\n# changed\n")
    monkeypatch.setattr(sandbox, "NO_EXEC", changed)
    assert sandbox.describe() != before


def test_describe_on_macos_hashes_the_worker_profile(monkeypatch):
    # Kills x_describe__mutmut_5..19 (the macOS branch's placeholder arguments).
    calls = []
    monkeypatch.setattr(sandbox, "mode", lambda: "macos-sandbox-exec")
    monkeypatch.setattr(sandbox, "macos_profile", lambda **kwargs: calls.append(kwargs) or "(version 1)\n")
    assert sandbox.describe().startswith(f"macos-sandbox-exec:{sandbox.VERSION}:")
    assert calls == [{"read": ["<read>"], "write": ["<write>"], "socket": "<socket>", "bind_socket": False}]


def test_describe_doesnt_depend_on_where_the_checkout_or_bwrap_live(linux, monkeypatch, tmp_path):
    # Kills x_describe__mutmut_45..50/63/64: tools/ and bwrap's own paths are replaced by a
    # placeholder, so a mock grid in one checkout and the paid run from a clean checkout
    # of the same commit agree.
    before = sandbox.describe()
    monkeypatch.setattr(sandbox, "TOOLS", tmp_path / "elsewhere" / "tools")
    real_which = sandbox.shutil.which
    monkeypatch.setattr(sandbox.shutil, "which",
                        lambda name, *a, **k: str(tmp_path / "bin" / "bwrap") if name == "bwrap" else real_which(name))
    assert sandbox.describe() == before


# --- what the interpreter exposes --------------------------------------------


def test_a_system_python_exposes_its_stdlib_and_shared_libraries_but_not_their_neighbours(system_python, linux):
    # Kills x__interpreter__mutmut_34 (the whole lib/ directory mounted instead of
    # lib/pythonX.Y) and _21..24/_35..46 (lib64 and the shared-library patterns).
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    lib, lib64 = system_python / "lib", system_python / "lib64"
    (lib64 / version).mkdir(parents=True)
    for name in ("libpython3.so", "libz.so.1", "libssl.so.3.0", "libpython.dylib"):
        (lib / name).write_bytes(b"")
    (lib64 / "libffi.so.8").write_bytes(b"")
    (lib / "secrets.txt").write_text("not the interpreter", encoding="utf-8")
    (lib / "other-tool").mkdir()
    programs, files, dirs, _ = sandbox._interpreter()
    assert str(lib / version) in dirs and str(lib64 / version) in dirs
    assert {str(lib / n) for n in ("libpython3.so", "libz.so.1", "libssl.so.3.0", "libpython.dylib")} <= set(files)
    assert str(lib64 / "libffi.so.8") in files
    assert str(lib / "secrets.txt") not in files
    mounts = _linux_mounts(sandbox.linux_argv(read=[], write=[], cwd="/"))
    assert not _visible(str(lib / "secrets.txt"), mounts)
    assert not _visible(str(lib / "other-tool"), mounts)


def test_pyvenv_home_names_an_install_root(tmp_path, monkeypatch):
    # Kills x__install_roots__mutmut_7..22: a venv's `home` line adds its parent as an
    # install root, and only the `home` key does.
    venv = tmp_path / "venv"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text(
        "include-system-site-packages = false\nhome = /opt/py-a/bin\nversion = 3.11\nother=/opt/py-b/bin\n",
        encoding="utf-8")
    monkeypatch.setattr(sys, "prefix", str(venv))
    roots = sandbox._install_roots(sys.executable)
    assert "/opt/py-a" in roots
    assert "/opt/py-b" not in roots and "/opt/py-a/bin" not in roots


def test_a_macos_framework_build_exposes_its_app_and_library(system_python, monkeypatch):
    # Kills x__interpreter__mutmut_2..7 and _49..93: a framework build's Python.app
    # binary is a program it may run, its Resources a directory it reads, and its
    # framework library a file it reads.
    real = sysconfig.get_config_var
    monkeypatch.setattr(sysconfig, "get_config_var", lambda name: "Python" if name == "PYTHONFRAMEWORK" else real(name))
    app = system_python / "Resources" / "Python.app" / "Contents" / "MacOS" / "Python"
    app.parent.mkdir(parents=True)
    app.write_bytes(b"")
    (system_python / "Python").write_bytes(b"")
    programs, files, dirs, _ = sandbox._interpreter()
    assert str(app) in programs
    assert str(system_python / "Resources") in dirs
    assert str(system_python / "Python") in files


# --- sockets ------------------------------------------------------------------


def test_an_unreadable_directory_under_a_mount_refuses_the_launch(tmp_path, linux):
    # Kills x__sockets__mutmut_6/8 (onerror dropped): a socket in a directory the
    # launcher can't list could still be reached by name.
    if os.geteuid() == 0:
        pytest.skip("root reads every directory")
    hidden = tmp_path / "fixtures" / "hidden"
    hidden.mkdir(parents=True)
    hidden.chmod(0)
    try:
        with pytest.raises(sandbox.SandboxUnavailable, match="can't check .*hidden for sockets"):
            sandbox.wrap([sys.executable, "-I", "tool.py"], cwd=tmp_path, read=[tmp_path / "fixtures"])
    finally:
        hidden.chmod(0o700)


def test_a_socket_named_directly_as_a_mount_refuses_the_launch(tmp_path, linux, monkeypatch):
    # Kills x__sockets__mutmut_4 (every path walked as a directory).
    listener = _plant(tmp_path, monkeypatch, "direct.sock")
    try:
        with pytest.raises(sandbox.SandboxUnavailable, match="^a socket other than the fixture socket .*direct.sock"):
            sandbox.wrap([sys.executable, "-I", "tool.py"], cwd=tmp_path, read=[tmp_path / "direct.sock"])
    finally:
        listener.close()


def test_a_regular_file_named_as_a_mount_is_allowed(tmp_path, linux):
    # Kills x__sockets__mutmut_4 (a file walked as a directory refuses every file mount).
    document = tmp_path / "doc.txt"
    document.write_text("x", encoding="utf-8")
    argv = sandbox.wrap([sys.executable, "-I", "tool.py"], cwd=tmp_path, read=[document])
    assert ("--ro-bind", str(document)) in _linux_mounts(argv)


def test_the_fixture_socket_itself_is_never_foreign(tmp_path, linux, monkeypatch):
    # Kills x_wrap__mutmut_61 (no fixture socket passed to the foreign-socket check): a
    # restarted fixture service finds its own old socket in the directory it binds.
    sock_dir = tmp_path / "sock"
    sock_dir.mkdir()
    listener = _plant(sock_dir, monkeypatch, "fixture.sock")
    try:
        argv = sandbox.wrap([sys.executable, "-I", "service.py"], cwd=sock_dir, write=[sock_dir],
                            socket_dir=sock_dir, bind_socket=True)
        assert ("--bind", str(sock_dir)) in _linux_mounts(argv)
    finally:
        listener.close()


def test_a_socket_in_the_tools_directory_refuses_the_launch(tmp_path, linux, monkeypatch):
    # Kills x_wrap__mutmut_61 (tools/ left out of the socket check).
    tools = tmp_path / "tools"
    tools.mkdir()
    listener = _plant(tools, monkeypatch, "t.sock")
    monkeypatch.setattr(sandbox, "TOOLS", tools)
    try:
        with pytest.raises(sandbox.SandboxUnavailable, match="t.sock"):
            sandbox.wrap([sys.executable, "-I", "tool.py"], cwd=tmp_path)
    finally:
        listener.close()


# --- wrap(), mode(), and environment() ------------------------------------------


def test_a_one_line_program_with_no_arguments_is_a_valid_launch(tmp_path, linux):
    # Kills x_wrap__mutmut_43/44: `-I -c CODE` is four items and allowed; `-I -c` alone is not.
    argv = sandbox.wrap([sys.executable, "-I", "-c", "pass"], cwd=tmp_path)
    assert argv[argv.index("--") + 1:] == [sys.executable, "-I", str(sandbox.NO_EXEC), "-c", "pass"]
    with pytest.raises(sandbox.SandboxUnavailable, match="runs as"):
        sandbox.wrap([sys.executable, "-I", "-c"], cwd=tmp_path)


def test_on_macos_wrap_runs_sandbox_exec_with_the_tool_s_profile(tmp_path, monkeypatch):
    # Kills x_wrap__mutmut_17..31: Linux CI never takes this branch.
    monkeypatch.setattr(sandbox, "mode", lambda: "macos-sandbox-exec")
    read, write, sock = tmp_path / "r", tmp_path / "w", tmp_path / "s"
    for path in (read, write, sock):
        path.mkdir()
    for bind in (False, True):
        argv = sandbox.wrap([sys.executable, "-I", "tool.py"], cwd=tmp_path, read=[read], write=[write],
                            socket_dir=sock, bind_socket=bind)
        expected = sandbox.macos_profile(read=[os.path.realpath(read)], write=[os.path.realpath(write)],
                                         socket=os.path.join(os.path.realpath(sock), "fixture.sock"), bind_socket=bind)
        assert argv == [sandbox.SANDBOX_EXEC, "-p", expected, sys.executable, "-I", "tool.py"]


def test_on_macos_mode_needs_an_executable_sandbox_exec(tmp_path, monkeypatch):
    # Kills x_mode__mutmut_8..17 with the platform stood in for.
    if os.geteuid() == 0:
        pytest.skip("mode() refuses root first")
    monkeypatch.setattr(sys, "platform", "darwin")
    tool = tmp_path / "sandbox-exec"
    tool.write_bytes(b"#!/bin/sh\n")
    tool.chmod(0o755)
    monkeypatch.setattr(sandbox, "SANDBOX_EXEC", str(tool))
    assert sandbox.mode() == "macos-sandbox-exec"
    tool.chmod(0o644)
    with pytest.raises(sandbox.SandboxUnavailable, match=f"^{tool} is missing$"):
        sandbox.mode()


def test_the_tool_environment_points_tmpdir_at_its_first_write_directory(tmp_path):
    # Kills x_environment__mutmut_8.
    first, second = tmp_path / "a", tmp_path / "b"
    assert sandbox.environment([first, second]) == {
        "PATH": os.defpath, "LANG": "C.UTF-8", "TMPDIR": os.path.realpath(first)}
    assert sandbox.environment() == {"PATH": os.defpath, "LANG": "C.UTF-8"}


def test_the_root_refusal_names_the_rule(monkeypatch):
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    with pytest.raises(sandbox.SandboxUnavailable, match=r"^tool processes never run as root \(SPEC.md Section 3\)$"):
        sandbox.mode()
