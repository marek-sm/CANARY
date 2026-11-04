"""The sweep container's egress proxy (docker/sweep/egress_proxy.py, prototype): it
forwards TLS for the allowed name only, to its fixed upstream, and nothing else.

Every connection here is local. The in-image check that the runner reaches nothing
else and the tools reach nothing at all is docker/sweep/egress_probe.py, run by
``make sweep-container-check``.
"""

import asyncio
import importlib.util
import ssl
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("egress_proxy", ROOT / "docker" / "sweep" / "egress_proxy.py")
proxy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(proxy)


def client_hello(name=None):
    """The bytes Python's own TLS client sends first for ``name`` (no SNI when ``None``)."""
    context = ssl.create_default_context()
    context.check_hostname = name is not None
    incoming, outgoing = ssl.MemoryBIO(), ssl.MemoryBIO()
    tls = context.wrap_bio(incoming, outgoing, server_hostname=name)
    with pytest.raises(ssl.SSLWantReadError):
        tls.do_handshake()
    return outgoing.read()


def test_the_allowed_name_is_read_from_a_real_client_hello():
    assert proxy.server_name(client_hello("api.anthropic.com")) == "api.anthropic.com"
    proxy.decide(client_hello("api.anthropic.com"), "api.anthropic.com")
    proxy.decide(client_hello("API.Anthropic.com"), "api.anthropic.com")


@pytest.mark.parametrize("name", ["example.com", "api.anthropic.com.example.com", "anthropic.com",
                                  "api.openai.com", "xapi.anthropic.com"])
def test_any_other_name_is_refused(name):
    with pytest.raises(proxy.Refused, match="isn't allowed"):
        proxy.decide(client_hello(name), "api.anthropic.com")


def test_a_hello_with_no_name_is_refused():
    with pytest.raises(proxy.Refused, match="names no host"):
        proxy.decide(client_hello(None), "api.anthropic.com")


@pytest.mark.parametrize("data", [b"GET / HTTP/1.1\r\nHost: api.anthropic.com\r\n\r\n",
                                  b"CONNECT example.com:443 HTTP/1.1\r\n\r\n",
                                  b"\x16\x03\x01\xff\xff" + b"\x00" * 10,
                                  b"\x16\x03\x01\x00\x05\x02\x00\x00\x01\x00"])
def test_what_isnt_a_client_hello_is_refused(data):
    with pytest.raises(proxy.Refused):
        proxy.decide(data, "api.anthropic.com")


def test_a_partial_hello_asks_for_more():
    hello = client_hello("api.anthropic.com")
    for cut in (0, 3, 5, len(hello) - 1):
        with pytest.raises(EOFError):
            proxy.decide(hello[:cut], "api.anthropic.com")


def test_every_truncation_of_a_hello_either_waits_or_refuses():
    hello = client_hello("api.anthropic.com")
    body = hello[5:]
    for cut in range(len(body)):
        forged = hello[:3] + cut.to_bytes(2, "big") + body[:cut]
        with pytest.raises((EOFError, proxy.Refused)):
            proxy.decide(forged, "api.anthropic.com")


def _serve(upstream_port):
    """A proxy on an ephemeral local port whose fixed upstream is a local echo server."""
    async def run(check):
        received = []

        async def echo(reader, writer):
            data = await reader.read(65536)
            received.append(data)
            writer.write(b"echo:" + data)
            await writer.drain()
            writer.close()

        upstream = await asyncio.start_server(echo, "127.0.0.1", upstream_port)
        slots = asyncio.Semaphore(proxy.MAX_CLIENTS)
        port = upstream.sockets[0].getsockname()[1]
        server = await asyncio.start_server(
            lambda r, w: proxy.handle(r, w, allowed="api.anthropic.com", upstream=("127.0.0.1", port), slots=slots),
            "127.0.0.1", 0)
        async with upstream, server:
            return await check(server.sockets[0].getsockname()[1], received)
    return run


async def _exchange(port, data):
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(data)
    await writer.drain()
    reply = await asyncio.wait_for(reader.read(65536), 5)
    writer.close()
    return reply


def test_the_allowed_hello_is_forwarded_unchanged_to_the_fixed_upstream():
    hello = client_hello("api.anthropic.com")

    async def check(port, received):
        reply = await _exchange(port, hello)
        return reply, received

    reply, received = asyncio.run(_serve(0)(check))
    assert reply == b"echo:" + hello
    assert received == [hello]


@pytest.mark.parametrize("data", [client_hello("example.com"), client_hello(None), b"GET / HTTP/1.0\r\n\r\n"])
def test_a_refused_connection_sends_nothing_upstream(data):
    async def check(port, received):
        reply = await _exchange(port, data)
        return reply, received

    reply, received = asyncio.run(_serve(0)(check))
    assert reply == b""
    assert received == []


def test_a_client_that_names_another_host_cant_choose_where_the_proxy_connects():
    # The upstream is a constant; nothing in the request is ever used to pick it.
    source = (ROOT / "docker" / "sweep" / "egress_proxy.py").read_text(encoding="utf-8")
    assert "open_connection(*upstream)" in source
    assert source.count("open_connection(") == 1


def test_the_default_listens_for_tls_and_allows_only_the_anthropic_api():
    assert proxy.ALLOWED_NAME == "api.anthropic.com"
    assert proxy.UPSTREAM == ("api.anthropic.com", 443)


def test_the_proxy_starts_no_process_and_reads_no_file():
    source = (ROOT / "docker" / "sweep" / "egress_proxy.py").read_text(encoding="utf-8")
    for word in ("subprocess", "os.system", "open(", "environ"):
        assert word not in source


def test_a_silent_client_is_closed():
    async def check(port, received):
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        reply = await asyncio.wait_for(reader.read(1), proxy.HELLO_TIMEOUT + 5)
        writer.close()
        return reply, received

    original = proxy.HELLO_TIMEOUT
    proxy.HELLO_TIMEOUT = 0.2
    try:
        reply, received = asyncio.run(_serve(0)(check))
    finally:
        proxy.HELLO_TIMEOUT = original
    assert reply == b"" and received == []

