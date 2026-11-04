"""Filesystem boundary: read only the named fixture root, write only the state.

SPEC.md Section 3: "File reads stay under a canonicalized fixture root; traversal
and symlink escape fail closed." "Tool processes run ... with a read-only
filesystem except explicit per-trial state and result mounts." On Linux the real
boundary is the bwrap mount namespace: paths that are never mounted cannot be
named at all, whatever symlink or ``..`` is used.
"""
from __future__ import annotations

import os
from pathlib import Path

from conftest import attempt_snippet, requires_sandbox, run_probe, run_worker, skip_if_root, ROOT

pytestmark = [requires_sandbox, skip_if_root]


def test_cannot_read_outside_the_fixture_root(trial):
    code = attempt_snippet() + f"""
attempt("etc_passwd", lambda: open("/etc/passwd").read(16))
attempt("etc_shadow", lambda: open("/etc/shadow").read(16))
attempt("key_file", lambda: open({str(trial.outside / ".env")!r}).read())
attempt("repo_readme", lambda: open({str(ROOT / "README.md")!r}).read(16))
attempt("repo_spec", lambda: open({str(ROOT / "SPEC.md")!r}).read(16))
attempt("home_root", lambda: os.listdir("/root"))
attempt("home_user", lambda: os.listdir({str(Path.home())!r}))
attempt("fixture_ok", lambda: open({str(trial.fixtures / "doc.txt")!r}).read())
emit()
"""
    r = run_probe(trial, code)
    assert r["fixture_ok"][0] == "allowed", r["fixture_ok"]
    for name in ("etc_passwd", "etc_shadow", "key_file", "repo_readme", "repo_spec", "home_root"):
        assert r[name][0] == "denied", (name, r[name])


def test_cannot_write_outside_the_state_dir(trial):
    code = attempt_snippet() + f"""
def w(p):
    def f():
        open(p, "w").write("x"); return p
    return f
attempt("tmp", w("/tmp/canary-redteam-probe"))
attempt("repo", w({str(ROOT / "redteam-should-not-exist.txt")!r}))
attempt("evidence", w({str(trial.base / "t" / "events.jsonl")!r}))
attempt("fixtures_ro", w({str(trial.fixtures / "injected.txt")!r}))
attempt("etc", w("/etc/canary-redteam-probe"))
attempt("root_slash", w("/canary-redteam-probe"))
attempt("state_ok", w({str(trial.state / "receipt.txt")!r}))
emit()
"""
    r = run_probe(trial, code)
    assert r["state_ok"][0] == "allowed", r["state_ok"]
    for name in ("tmp", "repo", "evidence", "fixtures_ro", "etc", "root_slash"):
        assert r[name][0] == "denied", (name, r[name])
    assert not (ROOT / "redteam-should-not-exist.txt").exists()
    assert (trial.base / "t" / "events.jsonl").read_text() == ""


def test_symlink_in_state_cannot_escape_the_mount_namespace(trial):
    """A tool may create a symlink in its own writable dir pointing at an absolute
    host path; following it still lands on an unmounted path, so it fails closed."""
    code = attempt_snippet() + """
import os
os.symlink("/etc/passwd", "escape")            # in cwd... but cwd is the socket dir (ro)
attempt("via_state_symlink", lambda: open(os.path.join({state!r}, "esc")).read(16))
# build the symlink in the writable state dir, then read through it
os.symlink("/etc/passwd", os.path.join({state!r}, "esc2"))
attempt("via_state_symlink2", lambda: open(os.path.join({state!r}, "esc2")).read(16))
os.symlink({keyfile!r}, os.path.join({state!r}, "esc3"))
attempt("via_state_to_keyfile", lambda: open(os.path.join({state!r}, "esc3")).read())
emit()
""".format(state=str(trial.state), keyfile=str(trial.outside / ".env"))
    # cwd is the socket dir (read-only); the first symlink() may itself fail — that is fine.
    r = run_probe(trial, code, expect_returncode=None)
    # Whatever got created, reading through a symlink to an unmounted path must fail.
    assert r.get("via_state_symlink2", ["denied"])[0] == "denied", r
    assert r.get("via_state_to_keyfile", ["denied"])[0] == "denied", r


def test_proc_and_sys_expose_nothing_outside_the_sandbox(trial):
    """`--proc /proc` gives a fresh proc for the sandbox pid namespace; the tool is
    pid 1 and the only process. /sys is not mounted."""
    code = attempt_snippet() + """
import os
attempt("proc_list", lambda: sorted(p for p in os.listdir("/proc") if p.isdigit()))
attempt("proc1_environ", lambda: open("/proc/1/environ","rb").read())
attempt("proc1_cmdline", lambda: open("/proc/1/cmdline","rb").read().split(b"\\0"))
attempt("proc1_maps", lambda: open("/proc/1/maps").read(64))
attempt("self_environ", lambda: open("/proc/self/environ","rb").read())
attempt("sys_list", lambda: os.listdir("/sys"))
attempt("proc_kallsyms", lambda: open("/proc/kallsyms").read(64))
attempt("proc_sysrq", lambda: open("/proc/sysrq-trigger","w"))
emit()
"""
    r = run_probe(trial, code, expect_returncode=None)
    # Only the tool itself exists in the pid namespace.
    if r.get("proc_list", ["denied"])[0] == "allowed":
        assert r["proc_list"][1] == ["1"], r["proc_list"]
    # Its own environ is the sandbox env only (no provider var) — checked in test_credential.
    # /sys must not expose the host.
    if r.get("sys_list", ["denied"])[0] == "allowed":
        assert r["sys_list"][1] == [], r["sys_list"]
    assert r.get("proc_sysrq", ["denied"])[0] == "denied", r.get("proc_sysrq")


def test_read_file_tool_rejects_traversal_and_absolute_paths(trial):
    """The shipped read_file tool, through the real worker, must refuse traversal."""
    (trial.fixtures / "doc.txt").write_text("fixture-body", encoding="utf-8")
    for bad in ("../../etc/passwd", "/etc/passwd", "..", "a/../../b", "doc.txt\x00.png"):
        r = run_worker(trial, {"tool": "read_file", "args": {"path": bad}})
        assert r.get("ok") is False, (bad, r)
    good = run_worker(trial, {"tool": "read_file", "args": {"path": "doc.txt"}})
    assert good == {"ok": True, "text": "fixture-body"}, good


def test_read_file_tool_does_not_follow_a_symlink_inside_the_fixture_root(trial):
    """A planted symlink inside the fixture root pointing outside must not be read
    (O_NOFOLLOW on the final component); the file it points at is also unmounted."""
    target = trial.outside / ".env"
    os.symlink(str(target), trial.fixtures / "link.txt")
    r = run_worker(trial, {"tool": "read_file", "args": {"path": "link.txt"}})
    assert r.get("ok") is False, r
    # And a symlinked *directory* component.
    (trial.fixtures / "real").mkdir()
    (trial.fixtures / "real" / "secret.txt").write_text("x", encoding="utf-8")
    os.symlink(str(trial.outside), trial.fixtures / "dirlink")
    r2 = run_worker(trial, {"tool": "read_file", "args": {"path": "dirlink/.env"}})
    assert r2.get("ok") is False, r2
