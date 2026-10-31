"""Private fixture service on a Unix socket; never serves caller-selected filesystem paths.

It runs inside the tool sandbox (decision 0023) with no network at all: it binds
``fixture.sock`` in its working directory, the trial's socket directory, and
``fetch_url`` reaches it only through that path. A stale socket from a killed
run is removed before binding, and the service exits when its parent closes
stdin, so a crashed runner never leaves it serving (macOS has no
die-with-parent).
"""
from http.server import BaseHTTPRequestHandler
import json
import os
from pathlib import Path
import socketserver
import sys
import threading

VERSION = "fixture-http-v0.2.0"
SOCKET_NAME = "fixture.sock"


class UnixHTTPServer(socketserver.UnixStreamServer):
    pass


def serve(root):
    pages = json.loads((root / "pages.json").read_text(encoding="utf-8"))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = pages.get(self.path)
            if body is None:
                self.send_error(404)
                return
            data = body.encode("utf-8")
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
