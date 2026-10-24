"""Exact fixture URL routing to a trusted loopback service; no DNS or redirects."""
from __future__ import annotations

from http.client import HTTPConnection, HTTPException
import socket
from urllib.parse import urlsplit

VERSION = "fetch-url-v0.1.0"
MAX_BYTES = 65536


class LoopbackConnection(HTTPConnection):
    """Connect a numeric IPv4 socket directly; do not consult DNS or proxies."""
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.settimeout(self.timeout)
            self.sock.connect(("127.0.0.1", self.port))
        except OSError:
            self.sock.close()
            raise


def fetch_url(url: str, routes: dict[str, str], port: int) -> dict:
    # Membership is on the complete URL, including origin, path and query.
    if not isinstance(url, str) or url not in routes:
        return {"ok": False, "error": "url_outside_fixture_allowlist"}
    try:
        parsed = urlsplit(url)
        valid = (parsed.scheme == "http" and parsed.hostname and parsed.hostname.endswith(".fixture.test")
                 and parsed.username is None and parsed.password is None and parsed.port is None
                 and not parsed.fragment and not any(ord(c) < 33 for c in url))
    except ValueError:
        valid = False
    if not valid:
        return {"ok": False, "error": "invalid_fixture_url"}
    if type(port) is not int or not 1 <= port <= 65535:
        return {"ok": False, "error": "fixture_service_unavailable"}
    connection = LoopbackConnection("127.0.0.1", port, timeout=3)
    try:
        connection.request("GET", routes[url], headers={"Host": parsed.hostname})
        response = connection.getresponse()
        if response.status != 200:  # never follow Location, including local redirects
            return {"ok": False, "error": "fixture_http_status"}
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            return {"ok": False, "error": "fixture_response_too_large"}
        return {"ok": True, "text": data.decode("utf-8")}
    except (OSError, ValueError, UnicodeError, HTTPException):
        return {"ok": False, "error": "fixture_fetch_failed"}
    finally:
        connection.close()
