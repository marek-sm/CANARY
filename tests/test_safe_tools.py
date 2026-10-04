"""Negative containment checks independent of task policy or defense configuration."""
import json
import os
import socket
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest

from tasks import registry
from tools import query_db as db
from tools import fetch_url as web
from tools import send_email as mail


@pytest.fixture
def root(tmp_path):
    return registry.reset(tmp_path / "fixtures")


def test_database_returns_only_registered_parameterized_rows(root, monkeypatch):
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("database opened a socket"))
    before = (root / "fixture.sqlite").read_bytes()
    assert db.query_db(root, "product_reviews", {"sku": "sku-2201"})["rows"][0]["record_id"] == "sku-2201"
    assert db.query_db(root, "tickets_by_status", {"status": "open"})["rows"] == [
        {"record_id": "T-100", "content": '{"ticket_id": "T-100", "status": "open"}'},
        {"record_id": "T-102", "content": '{"ticket_id": "T-102", "status": "open"}'},
    ]
    assert db.query_db(root, "product_reviews", {"sku": "sku-2201' OR 1=1 --"}) == {"ok": True, "rows": []}
    assert (root / "fixture.sqlite").read_bytes() == before


@pytest.mark.parametrize("query", ["SELECT * FROM documents", "DELETE FROM documents", "ATTACH 'elsewhere' AS other", "load_extension", "", "../fixture.sqlite"])
def test_model_cannot_choose_sql(root, query):
    assert db.query_db(root, query, {}) == {"ok": False, "error": "unregistered_query"}


@pytest.mark.parametrize("params", [{}, {"sku": 1}, {"sku": True}, {"sku": None}, {"sku": []}, {"sku": "x", "extra": "x"}, [], {"sku": "x"*257}, {"sku": "x\x00"}, {"sku": "\ud800"}])
def test_database_parameter_shape_denial(root, params):
    assert db.query_db(root, "product_reviews", params)["ok"] is False


@pytest.mark.parametrize("statement", [
    "DELETE FROM documents", "UPDATE documents SET lookup='x'", "INSERT INTO documents VALUES('x','x','x','x')",
    "CREATE TABLE other(x)", "DROP TABLE documents", "ATTACH ':memory:' AS other", "DETACH DATABASE main",
    "PRAGMA writable_schema=ON", "SELECT load_extension('fictional')", "SELECT sqlite_version()",
])
def test_sqlite_authorizer_denies_mutation_attach_extensions_and_functions(root, statement):
    connection = sqlite3.connect(":memory:")
    try:
        connection.deserialize((root / "fixture.sqlite").read_bytes())
        connection.enable_load_extension(False)
        connection.set_authorizer(db.readonly_authorizer)
        with pytest.raises(sqlite3.Error):
            connection.execute(statement)
        assert connection.execute("SELECT record_id FROM documents").fetchone()
    finally:
        connection.close()


def test_database_rejects_links_special_files_and_bad_snapshots(root, tmp_path):
    target = root / "fixture.sqlite"
    outside = tmp_path / "fictional.sqlite"
    outside.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(outside)
    assert not db.query_db(root, "orders", {"order_id": "ORD-4417"})["ok"]
    target.unlink()
    os.link(outside, target)
    assert not db.query_db(root, "orders", {"order_id": "ORD-4417"})["ok"]
    target.unlink()
    os.mkfifo(target)
    assert not db.query_db(root, "orders", {"order_id": "ORD-4417"})["ok"]
    target.unlink()
    target.write_bytes(b"not sqlite")
    assert not db.query_db(root, "orders", {"order_id": "ORD-4417"})["ok"]


@pytest.mark.parametrize("url", [
    "https://example.com/", "http://127.0.0.1/", "http://localhost/", "http://2130706433/",
    "file:///etc/passwd", "http://catalog.fixture.test.evil.test/products/sku-2201",
    "http://catalog.fixture.test@evil.test/products/sku-2201", "http://catalog.fixture.test:80/products/sku-2201",
    "http://catalog.fixture.test/products/sku-2201?next=http://example.com/", "http://catalog.fixture.test/products/sku-2201#x",
    "http://catalog.fixture.test/products/%73ku-2201", "http://catalog.fixture.test/products/../sku-2201", None, [],
])
def test_url_denial_never_constructs_connection(url, monkeypatch):
    monkeypatch.setattr(web, "LoopbackConnection", lambda *a, **k: pytest.fail("denied URL connected"))
    assert not web.fetch_url(url, {"http://catalog.fixture.test/products/sku-2201": "/fixtures/review"}, 1234)["ok"]


def test_real_fixture_server_has_exact_routes(root, monkeypatch):
    # Proxy settings and DNS cannot select a target for the worker.
    monkeypatch.setenv("HTTP_PROXY", "http://example.com:8000")
    monkeypatch.setenv("HTTPS_PROXY", "http://example.com:8000")
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: pytest.fail("fixture fetch used DNS"))
    routes = json.loads((root / "routes.json").read_text())
    with registry.fixture_service(root) as port:
        assert web.fetch_url("http://catalog.fixture.test/products/sku-2201", routes, port)["ok"]


@pytest.mark.parametrize("status", [301, 302, 307, 308])
def test_redirects_never_follow_location(status):
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            self.send_response(status)
            self.send_header("Location", "http://example.com/fictional")
            self.send_header("Content-Length", "0")
            self.end_headers()
        def log_message(self, *args):
            pass
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        assert web.fetch_url("http://content.fixture.test/page", {"http://content.fixture.test/page":"/page"}, server.server_port)["error"] == "fixture_http_status"
        assert requests == ["/page"]
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_email_is_local_and_authorization_neutral(tmp_path, monkeypatch):
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("email opened socket"))
    state = registry.create_state(tmp_path)
    fields = {"to":"unassigned@fixture.test", "subject":"Fictional unauthorized proposal", "body":"Fictional data"}
    assert mail.send_email(state, **fields) == {"ok": True}
    assert json.loads((state / mail.SINK_NAME).read_text()) == fields
    fresh = registry.create_state(tmp_path)
    assert fresh != state and (fresh / mail.SINK_NAME).read_bytes() == b""


@pytest.mark.parametrize("fields", [
    {"to": [], "subject":"x", "body":"x"}, {"to":"x", "subject":None, "body":"x"},
    {"to":"x", "subject":"x", "body":"x\x00"}, {"to":"x", "subject":"x", "body":"x"*16385},
    {"to":"x", "subject":"x", "body":"\ud800"},
])
def test_email_malformed_fields_never_write(tmp_path, fields):
    state = registry.create_state(tmp_path)
    assert not mail.send_email(state, **fields)["ok"]
    assert (state / mail.SINK_NAME).read_bytes() == b""


def test_email_sink_escape_fails_closed(tmp_path):
    state = registry.create_state(tmp_path)
    outside = tmp_path / "fictional-outside"
    outside.write_bytes(b"")
    sink = state / mail.SINK_NAME
    sink.unlink()
    sink.symlink_to(outside)
    fields = {"to":"other@fixture.test", "subject":"x", "body":"x"}
    assert not mail.send_email(state, **fields)["ok"]
    sink.unlink()
    os.link(outside, sink)
    assert not mail.send_email(state, **fields)["ok"]
    assert outside.read_bytes() == b""
