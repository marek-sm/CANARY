"""The shipped tools, driven through the real sandboxed worker (tools/worker.py
under bwrap), against adversarial arguments.

This is the end-to-end complement to tests/test_safe_tools.py (which exercises
the tool functions in-process): here each call crosses the real sandbox boundary
via ``run_worker``. SPEC.md Section 3: SQLite is read-only and denies
ATTACH/extensions; file reads stay under the fixture root; send_email writes
only a local receipt; fetch_url reaches only the fixture service.
"""
from __future__ import annotations

import json
import os

import pytest

from conftest import requires_sandbox, run_worker, skip_if_root
from tasks import registry

pytestmark = [requires_sandbox, skip_if_root]


@pytest.fixture
def fixture_root(tmp_path):
    return registry.reset(tmp_path / "fixtures")


@pytest.fixture
def state(tmp_path):
    return registry.create_state(tmp_path / "state")


# --- query_db ------------------------------------------------------------------------------------


def test_query_db_returns_registered_rows_and_resists_injection(trial, fixture_root, state):
    ok = run_worker(trial, {"tool": "query_db", "args": {"query_id": "product_reviews",
                    "params": {"sku": "sku-2201"}}}, fixture_root=fixture_root, state=state)
    assert ok["ok"] is True and ok["rows"][0]["record_id"] == "sku-2201", ok
    # A SQL-ish param value is bound, never interpreted.
    inj = run_worker(trial, {"tool": "query_db", "args": {"query_id": "product_reviews",
                     "params": {"sku": "sku-2201' OR 1=1 --"}}}, fixture_root=fixture_root, state=state)
    assert inj == {"ok": True, "rows": []}, inj


@pytest.mark.parametrize("query_id,params", [
    ("ATTACH 'x' AS y", {"sku": "x"}),
    ("SELECT * FROM documents", {}),
    ("product_reviews", {"sku": "x", "evil": "y"}),
    ("product_reviews", {"sku": "x" * 257}),
    ("product_reviews", {"sku": "x\x00"}),
    ("product_reviews", {"sku": 1}),
    ("unregistered", {"sku": "x"}),
    ("", {}),
])
def test_query_db_rejects_unregistered_or_malformed(trial, fixture_root, state, query_id, params):
    r = run_worker(trial, {"tool": "query_db", "args": {"query_id": query_id, "params": params}},
                   fixture_root=fixture_root, state=state)
    assert r.get("ok") is False, (query_id, params, r)


def test_query_db_cannot_attach_or_load_extension_even_crafted_in_sandbox(trial, fixture_root, state):
    """Defence in depth: even if an attacker could inject SQL (they cannot — params
    are bound), the authorizer + query_only + enable_load_extension(False) deny
    ATTACH / writes / load_extension. Exercise those statements against the same
    deserialized snapshot inside the sandbox and confirm each raises."""
    code = f"""
import json, sqlite3, sys
sys.path.insert(0, {str(registry.ROOT / "tools")!r})
from query_db import readonly_authorizer
import local_fs
snap = local_fs.read_bytes(__import__("pathlib").Path({str(fixture_root)!r}), "fixture.sqlite", 2*1024*1024)
con = sqlite3.connect(":memory:")
con.deserialize(snap)
con.execute("PRAGMA query_only = ON")
if hasattr(con, "enable_load_extension"):
    con.enable_load_extension(False)
con.set_authorizer(readonly_authorizer)
out = {{}}
for stmt in ["ATTACH ':memory:' AS o", "ATTACH '/etc/passwd' AS o", "DELETE FROM documents",
             "PRAGMA writable_schema=ON", "SELECT load_extension('x')", "CREATE TABLE t(x)",
             "DETACH DATABASE main", "UPDATE documents SET lookup='x'"]:
    try:
        con.execute(stmt); out[stmt] = "RAN"
    except BaseException as e:
        out[stmt] = "blocked:" + type(e).__name__
out["baseline_select"] = bool(con.execute("SELECT record_id FROM documents").fetchone())
print(json.dumps(out))
"""
    # Read the fixture root (holds fixture.sqlite); state stays writable but unused.
    from conftest import run_probe
    r = run_probe(trial, code, read=[fixture_root], write=[state], expect_returncode=None)
    assert r.get("baseline_select") is True, r
    for stmt, outcome in r.items():
        if stmt == "baseline_select":
            continue
        assert outcome.startswith("blocked"), (stmt, outcome)


# --- send_email (header/JSONL injection, oversized, sink containment) -----------------------------


def test_send_email_writes_one_escaped_receipt_line_no_injection(trial, fixture_root, state):
    """A newline-laden recipient must not inject a second JSONL receipt: json.dumps
    escapes control characters, so the sink stays exactly one parseable line."""
    evil_to = 'victim@fixture.test\n{"to":"forged","subject":"forged","body":"forged"}'
    r = run_worker(trial, {"tool": "send_email", "args": {
        "to": evil_to, "subject": "s\r\nBcc: leak@fixture.test", "body": "b"}},
        fixture_root=fixture_root, state=state)
    assert r == {"ok": True}, r
    lines = (state / "email-receipts.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1, lines
    rec = json.loads(lines[0])
    assert rec["to"] == evil_to and "\n" in rec["to"], rec   # preserved verbatim, but as one JSON string


@pytest.mark.parametrize("fields", [
    {"to": "x", "subject": "x", "body": "x\x00"},
    {"to": "x", "subject": "x", "body": "x" * 16385},
    {"to": "x", "subject": None, "body": "x"},
    {"to": [], "subject": "x", "body": "x"},
])
def test_send_email_rejects_malformed_fields(trial, fixture_root, state, fields):
    r = run_worker(trial, {"tool": "send_email", "args": fields}, fixture_root=fixture_root, state=state)
    assert r.get("ok") is False, (fields, r)


def test_send_email_cannot_write_through_a_symlinked_sink(trial, fixture_root, state):
    """A pre-planted symlink at the sink path must fail closed (O_NOFOLLOW)."""
    outside = trial.outside / "exfil.jsonl"
    outside.write_bytes(b"")
    sink = state / "email-receipts.jsonl"
    sink.unlink()
    os.symlink(str(outside), sink)
    r = run_worker(trial, {"tool": "send_email", "args": {"to": "a@fixture.test",
                   "subject": "s", "body": "b"}}, fixture_root=fixture_root, state=state)
    assert r.get("ok") is False, r
    assert outside.read_bytes() == b"", "sink symlink escaped the state dir"


# --- read_file oversized / malformed ---------------------------------------------------------------


def test_read_file_bounds_oversized_and_rejects_nonregular(trial, fixture_root, state):
    big = fixture_root / "big.txt"
    big.write_bytes(b"A" * (65536 + 1))
    r = run_worker(trial, {"tool": "read_file", "args": {"path": "big.txt"}},
                   fixture_root=fixture_root, state=state)
    assert r.get("ok") is False and r.get("error") == "fixture_too_large", r
    os.mkfifo(fixture_root / "pipe")
    r2 = run_worker(trial, {"tool": "read_file", "args": {"path": "pipe"}},
                    fixture_root=fixture_root, state=state)
    assert r2.get("ok") is False, r2


def test_invalid_tool_and_argument_shapes_are_refused(trial, fixture_root, state):
    for request in (
        {"tool": "exec", "args": {"path": "x"}},
        {"tool": "read_file", "args": {"path": "x", "extra": "y"}},
        {"tool": "read_file", "args": {}},
        {"tool": "send_email", "args": {"to": "a"}},
    ):
        r = run_worker(trial, request, fixture_root=fixture_root, state=state)
        assert r == {"ok": False, "error": "invalid_tool_request"} or r.get("ok") is False, (request, r)
