"""Private fixture service on a Unix socket; never serves caller-selected filesystem paths.

It runs inside the tool sandbox (decision 0023) with no network at all: it binds
``fixture.sock`` in its working directory, the trial's socket directory, and
``fetch_url`` reaches it only through that path. A stale socket from a killed
run is removed before binding, and the service exits when its parent closes
stdin, so a crashed runner never leaves it serving (macOS has no
die-with-parent).

Every request is appended to ``fixture-requests.jsonl`` beside the socket, and
fsynced before its response goes out, so the log holds a request by the time
``fetch_url`` can return (SPEC.md Sections 4 and 7). No tool can read or write
that log, which makes it evidence independent of what ``fetch_url`` reports. A
request that can't be logged isn't served. The log exists from the start, so a
missing log means no service ran, not that no request came.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path
import socketserver
import sys
import threading

VERSION = "fixture-http-v0.3.0"
SOCKET_NAME = "fixture.sock"
LOG_NAME = "fixture-requests.jsonl"


class UnixHTTPServer(socketserver.UnixStreamServer):
    pass


def log_request(path, host, status, body_bytes):
    line = json.dumps({"path": path, "host": host, "status": status, "body_bytes": body_bytes}, sort_keys=True)
    with open(LOG_NAME, "a", encoding="utf-8") as log:
        log.write(line + "\n")
        log.flush()
        os.fsync(log.fileno())


def serve(root):
    pages = json.loads((root / "pages.json").read_text(encoding="utf-8"))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = pages.get(self.path)
            data = b"" if body is None else body.encode("utf-8")
            log_request(self.path, self.headers.get("Host"), 404 if body is None else 200, len(data))
            if body is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def address_string(self):
            return "fixture-socket"

        def log_message(self, *args):
            pass

    try:
        os.unlink(SOCKET_NAME)
    except FileNotFoundError:
        pass
    open(LOG_NAME, "a", encoding="utf-8").close()
    server = UnixHTTPServer(SOCKET_NAME, Handler)

    def stop_when_parent_closes_stdin():
        sys.stdin.read()
        os._exit(0)

    threading.Thread(target=stop_when_parent_closes_stdin, daemon=True).start()
    print("ready", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    serve(Path(sys.argv[1]))
