"""The hosted-model credential never reaches a tool (decision 0023; SPEC.md §3).

``sandbox.environment`` hands a tool only ``PATH``, ``LANG``, and ``TMPDIR`` — no
``ANTHROPIC_*`` / ``OPENAI_*`` — and the launch uses ``close_fds`` so no open file
descriptor to a key file, the repo, or a foreign socket is inherited. The runner's
own environment (which, in this test, *does* hold a synthetic key) must not cross
the boundary.
"""
from __future__ import annotations

import os

from conftest import attempt_snippet, requires_sandbox, run_probe, skip_if_root

pytestmark = [requires_sandbox, skip_if_root]


def test_no_provider_variable_and_a_minimal_environment(trial):
    code = attempt_snippet() + r"""
import os
R["env"] = dict(os.environ)
R["provider_vars"] = sorted(k for k in os.environ if k.startswith(("ANTHROPIC_", "OPENAI_")))
emit()
"""
    r = run_probe(trial, code)
    assert r["provider_vars"] == [], r["provider_vars"]
    # sandbox.environment grants PATH, LANG, TMPDIR; bwrap additionally sets PWD to
    # the --chdir target (the tool's own cwd, i.e. the state dir) — not a secret.
    assert set(r["env"]) <= {"PATH", "LANG", "TMPDIR", "PWD"}, r["env"]
    if "PWD" in r["env"]:
        assert r["env"]["PWD"] == str(trial.state.resolve()), r["env"]["PWD"]
    assert r["env"].get("PATH") == "/nonexistent", r["env"]
    # The runner's synthetic key never appears anywhere in the tool environment.
    assert "synthetic-sentinel" not in "".join(r["env"].values()), r["env"]


def test_no_inherited_descriptor_points_outside_the_sandbox(trial):
    """close_fds means only stdio pipes are inherited; none resolves to the key
    file, the repository, or a non-fixture socket."""
    code = attempt_snippet() + r"""
import os
fds = {}
for name in os.listdir("/proc/self/fd"):
    try:
        fds[name] = os.readlink("/proc/self/fd/" + name)
    except OSError:
        fds[name] = "<gone>"
R["fds"] = fds
emit()
"""
    r = run_probe(trial, code)
    for fd, target in r["fds"].items():
        # stdio may be pipes or /dev/null; the fd used to list /proc/self/fd is a dir fd.
        assert "synthetic-sentinel" not in target, (fd, target)
        assert ".env" not in target, (fd, target)
        assert "README" not in target and "SPEC.md" not in target, (fd, target)
        # No inherited AF_UNIX connection to anything but (possibly) the fixture socket.
        assert "foreign" not in target and "sibling" not in target, (fd, target)


def test_the_key_file_content_is_unreachable_even_by_path(trial):
    code = attempt_snippet() + f"""
attempt("key", lambda: open({str(trial.outside / ".env")!r}).read())
emit()
"""
    r = run_probe(trial, code)
    assert r["key"][0] == "denied", r["key"]
