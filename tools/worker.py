"""Credential-free subprocess entry point; control paths never come from model args."""
import json
from pathlib import Path
import sys

# Python -I excludes the project and environment paths. Import only sibling tools.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from read_file import read_file
from query_db import query_db
from fetch_url import fetch_url
from send_email import send_email


def dispatch(fixture_root, state_root, port, tool, args):
    if tool == "read_file" and set(args) == {"path"}:
        return read_file(fixture_root, **args)
    if tool == "query_db" and set(args) == {"query_id", "params"}:
        return query_db(fixture_root, **args)
    if tool == "fetch_url" and set(args) == {"url"}:
        routes = json.loads((fixture_root / "routes.json").read_text(encoding="utf-8"))
        return fetch_url(routes=routes, port=port, **args)
    if tool == "send_email" and set(args) == {"to", "subject", "body"}:
        return send_email(state_root, **args)
    return {"ok": False, "error": "invalid_tool_request"}


if __name__ == "__main__":
    request = json.load(sys.stdin)
    print(json.dumps(dispatch(Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]),
                              request["tool"], request["args"])))
