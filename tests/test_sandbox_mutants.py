"""Tool-sandbox rules that mutation testing found unpinned
(reports/cloud/mutation.md). Each test names the surviving mutants it kills.

The macOS profile is a pure function of the interpreter's paths and the
caller's arguments, so these run on Linux too, where CI never launches
sandbox-exec and every macos_profile mutant survived.
"""

import re

import pytest

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

