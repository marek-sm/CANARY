"""Registered parameterized queries over a read-only fictional SQLite snapshot."""
from __future__ import annotations

from pathlib import Path
import sqlite3

try:
    from .local_fs import read_bytes
except ImportError:  # isolated worker, without repository imports
    from local_fs import read_bytes

VERSION = "query-db-v0.1.0"
MAX_DB_BYTES = 2 * 1024 * 1024
MAX_ROWS = 100
# Trusted code, never supplied by the model or a retrieved document.
QUERIES = {
    "product_reviews": ("sku", "reviews"),
    "orders": ("order_id", "orders"),
    "supplier_quotes": ("part_id", "quotes"),
    "shipping_notices": ("order_id", "shipping"),
    "meeting_requests": ("meeting_id", "meetings"),
    "tickets_by_status": ("status", "tickets"),
}


def readonly_authorizer(action, first, second, database, trigger):
    """Deny everything except SELECT and reads of the fixture table."""
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ and database == "main" and first == "documents":
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def query_db(root: Path, query_id: str, params: dict) -> dict:
    if not isinstance(query_id, str) or query_id not in QUERIES:
        return {"ok": False, "error": "unregistered_query"}
    parameter, resource = QUERIES[query_id]
    if (not isinstance(params, dict) or set(params) != {parameter}
            or type(params[parameter]) is not str or len(params[parameter]) > 256
            or "\x00" in params[parameter]):
        return {"ok": False, "error": "invalid_query_params"}
    connection = None
    try:
        # Load via no-follow descriptors, then query an isolated in-memory copy.
        # SQLite never opens a model-selected path, journal, ATTACH or extension.
        snapshot = read_bytes(root, "fixture.sqlite", MAX_DB_BYTES)
        connection = sqlite3.connect(":memory:")
        connection.deserialize(snapshot)
        connection.execute("PRAGMA query_only = ON")
        connection.enable_load_extension(False)
        connection.set_authorizer(readonly_authorizer)
        connection.set_progress_handler(lambda: 1, 100000)
        rows = connection.execute(
            "SELECT record_id, content FROM documents WHERE resource = ? AND lookup = ? ORDER BY record_id LIMIT ?",
            (resource, params[parameter], MAX_ROWS + 1),
        ).fetchall()
        if len(rows) > MAX_ROWS or sum(len(str(cell)) for row in rows for cell in row) > 65536:
            return {"ok": False, "error": "query_result_too_large"}
        return {"ok": True, "rows": [{"record_id": key, "content": content} for key, content in rows]}
    except (OSError, ValueError, UnicodeError, sqlite3.Error):
        return {"ok": False, "error": "fixture_database_denied"}
    finally:
        if connection is not None:
            connection.close()
