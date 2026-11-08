"""Exact fixture URL routing to the trial's fixture service; no DNS, network, or redirects.

The service listens on a Unix socket in the trial's socket directory (decision
0023), so this tool needs no network route at all: the sandbox denies every
TCP and UDP connection and allows only that socket path.
"""
from __future__ import annotations

from http.client import HTTPConnection, HTTPException
import socket
from urllib.parse import urlsplit

VERSION = "fetch-url-v0.2.0"
MAX_BYTES = 65536


class FixtureSocketConnection(HTTPConnection):
    """Connect to the fixture service's Unix socket; never DNS, a proxy, or TCP."""
    def __init__(self, socket_path: str, timeout: float):
        super().__init__("fixture.test", timeout=timeout)
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            self.sock.settimeout(self.timeout)
            self.sock.connect(self.socket_path)
        except OSError:
            self.sock.close()
            raise


def fetch_url(url: str, routes: dict[str, str], socket_path: str) -> dict:
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
    if type(socket_path) is not str or not socket_path or "\x00" in socket_path:
        return {"ok": False, "error": "fixture_service_unavailable"}
    connection = FixtureSocketConnection(socket_path, timeout=3)
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
