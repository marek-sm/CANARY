"""Private loopback fixture service; never serves caller-selected filesystem paths."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import sys


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

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    print(server.server_port, flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    serve(Path(sys.argv[1]))
