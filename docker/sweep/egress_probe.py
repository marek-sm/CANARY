"""What the sweep container can reach, from the outer runner and from a sandboxed tool (prototype).

PROTOTYPE for decision 0028 item 9; see docs/SWEEP_CONTAINER.md. Run inside the
image by ``make sweep-container-check``, under ``launch.sh --network egress``:

    python docker/sweep/egress_probe.py [--no-handshake] [--expect-no-network]

The outer runner must reach api.anthropic.com:443 through the proxy and nothing
else; a tool, launched through ``tools.sandbox.wrap`` as every tool is, must reach
nothing at all. Every check that should fail must fail for a network reason, never
because the probe itself broke, and the probe exits 1 if any check comes out wrong.

Contact with Anthropic: one TLS handshake to api.anthropic.com, with certificate
and host-name verification, then close. No HTTP request, no key, no provider call.
``--no-handshake`` skips it, which leaves the allowed path unproven.
``--expect-no-network`` is for ``--network none``: then even the allowed name must fail.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import ssl
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools import sandbox  # noqa: E402

ALLOWED = "api.anthropic.com"
# Outside hosts by address, so DNS can't be what stops them: public resolvers and a TEST-NET-3 address.
OUTSIDE = [("1.1.1.1", 443), ("8.8.8.8", 53), ("203.0.113.10", 80)]
OUTSIDE_NAMES = ["example.com", "pypi.org", "api.openai.com"]
TIMEOUT = 4.0

TOOL = r"""
import json, socket, sys
targets = json.loads(sys.argv[1])
out = {}
for host, port in targets["tcp"]:
    try:
        socket.create_connection((host, port), timeout=3).close()
        out[f"tcp {host}:{port}"] = "connected"
    except OSError as exc:
        out[f"tcp {host}:{port}"] = f"refused:{type(exc).__name__}:{exc.errno}"
for name in targets["names"]:
    try:
        out[f"dns {name}"] = "resolved:" + socket.getaddrinfo(name, 443)[0][4][0]
    except OSError as exc:
        out[f"dns {name}"] = f"refused:{type(exc).__name__}"
out["interfaces"] = [name for _, name in socket.if_nameindex()]
print(json.dumps(out))
"""


def _tcp(host: str, port: int) -> str:
    try:
        socket.create_connection((host, port), timeout=TIMEOUT).close()
        return "connected"
    except OSError as exc:
        return f"refused:{type(exc).__name__}:{exc.errno}"


def _dns(name: str) -> str:
    try:
        return "resolved:" + socket.getaddrinfo(name, 443)[0][4][0]
    except OSError as exc:
        return f"refused:{type(exc).__name__}"


def _tls(address: str, name: str | None) -> str:
    """A verified handshake to ``address`` naming ``name``, closed at once: no request is sent.
    With no name, verification is off, so only the proxy's refusal can stop it."""
    context = ssl.create_default_context()
    if name is None:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    try:
        with socket.create_connection((address, 443), timeout=TIMEOUT) as raw:
            with context.wrap_socket(raw, server_hostname=name) as tls:
                cert = tls.getpeercert() or {}
                subject = dict(item[0] for item in cert.get("subject", ()))
                return f"handshake:{subject.get('commonName')}:{tls.version()}"
    except (OSError, ssl.SSLError, ValueError) as exc:
        return f"refused:{type(exc).__name__}"


def _plain(address: str) -> str:
    try:
        with socket.create_connection((address, 443), timeout=TIMEOUT) as raw:
            raw.sendall(b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n")
            raw.settimeout(TIMEOUT)
            return "answered" if raw.recv(1) else "refused:closed"
    except OSError as exc:
        return f"refused:{type(exc).__name__}"


def tool_view(targets: dict) -> dict:
    """The same reach, from a tool process the sandbox launched."""
    with tempfile.TemporaryDirectory() as work:
        argv = [sys.executable, "-I", "-c", TOOL, json.dumps(targets)]
        completed = subprocess.run(sandbox.wrap(argv, cwd=work, write=[work]), cwd=work, capture_output=True,
                                   text=True, timeout=120, env=sandbox.environment([work]))
    if completed.returncode != 0:
        return {"error": completed.stderr[-1000:]}
    return json.loads(completed.stdout)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-handshake", action="store_true")
    parser.add_argument("--expect-no-network", action="store_true")
    args = parser.parse_args(argv)

    checks: list[tuple[str, str, bool]] = []  # (what, observed, as expected)

    def expect(what: str, observed: str, allowed: bool) -> None:
        ok = observed.startswith(("connected", "handshake", "resolved", "answered")) == allowed
        checks.append((what, observed, ok))

    proxy = _dns(ALLOWED)
    proxy_address = proxy.split(":", 1)[1] if proxy.startswith("resolved:") else None
    reach = not args.expect_no_network
    expect(f"runner: {ALLOWED} resolves (to the proxy, from /etc/hosts)", proxy, reach)
    if proxy_address and not args.no_handshake:
        expect(f"runner: verified TLS handshake to {ALLOWED}", _tls(proxy_address, ALLOWED), reach)
    if proxy_address:
        expect("runner: TLS naming example.com, through the proxy", _tls(proxy_address, "example.com"), False)
        expect("runner: TLS naming no host, through the proxy", _tls(proxy_address, None), False)
        expect("runner: plain HTTP to the proxy", _plain(proxy_address), False)
        expect("runner: the proxy on another port (80)", _tcp(proxy_address, 80), False)
    for host, port in OUTSIDE:
        expect(f"runner: direct TCP to {host}:{port}", _tcp(host, port), False)
    for name in OUTSIDE_NAMES:
        expect(f"runner: DNS for {name}", _dns(name), False)

    targets = {"tcp": [*OUTSIDE, *([(proxy_address, 443)] if proxy_address else [])], "names": [ALLOWED, *OUTSIDE_NAMES]}
    tool = tool_view(targets)
    if "error" in tool:
        checks.append(("tool: the sandboxed probe ran", tool["error"], False))
    else:
        for what, observed in tool.items():
            if what == "interfaces":
                checks.append(("tool: network interfaces", ",".join(observed), observed in ([], ["lo"])))
            else:
                expect(f"tool: {what}", observed, False)

    for what, observed, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'}  {what}: {observed}")
    failed = sum(not ok for _, _, ok in checks)
    print(json.dumps({"egress_probe": "pass" if not failed else "fail", "checks": len(checks), "failed": failed,
                      "uid": os.getuid()}))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
