"""The sweep runner's only route out: TLS to api.anthropic.com:443, nothing else (prototype).

PROTOTYPE for decision 0028 item 9, which the project lead hasn't taken; see
docs/SWEEP_CONTAINER.md. Decision 0025 item 12 keeps the official sweep on the host.

``docker/sweep/launch.sh --network egress`` puts the outer runner on an
``--internal`` Docker network, which has no route off the host, and runs this
file in a second container that sits on that network and on an ordinary bridge.
The runner's ``/etc/hosts`` points ``api.anthropic.com`` at this container, so
the provider client (``agent/anthropic_adapter.py``, which ignores proxy
variables) needs no change.

For each connection it reads the TLS ClientHello, and forwards the bytes, both
ways and unchanged, only when the server name is the allowed one. The upstream
is fixed: whatever a client sends, the only place this ever connects is the
allowed host on the allowed port, resolved here. TLS stays end to end, so this
never sees the key or a request. Anything else (another name, no name, not TLS,
a ClientHello too large or too slow) is closed without a byte upstream, and one
line saying why goes to stderr.

Usage: python egress_proxy.py [--listen HOST:PORT] [--allow NAME] [--upstream HOST:PORT]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Optional

ALLOWED_NAME = "api.anthropic.com"
UPSTREAM = ("api.anthropic.com", 443)
MAX_HELLO = 16 * 1024
HELLO_TIMEOUT = 10.0
MAX_CLIENTS = 64


class Refused(ValueError):
    """The connection isn't TLS to the allowed name."""


def server_name(data: bytes) -> Optional[str]:
    """The SNI host name in a complete TLS ClientHello, ``None`` if the hello names none.
    Raises ``Refused`` for anything that isn't a well-formed ClientHello, and
    ``EOFError`` when more bytes are needed."""
    if len(data) < 5:
        raise EOFError
    if data[0] != 0x16 or data[1] != 0x03:
        raise Refused("not a TLS handshake record")
    length = int.from_bytes(data[3:5], "big")
    if length > MAX_HELLO:
        raise Refused("handshake record too large")
    if len(data) < 5 + length:
        raise EOFError
    body = memoryview(data)[5:5 + length]
    if len(body) < 4 or body[0] != 0x01:
        raise Refused("not a ClientHello")
    hello_len = int.from_bytes(body[1:4], "big")
    if hello_len + 4 > len(body):
        raise Refused("ClientHello split across records")
    hello = body[4:4 + hello_len]
    at = 2 + 32  # version, random
    try:
        at += 1 + hello[at]                                   # session id
        at += 2 + int.from_bytes(hello[at:at + 2], "big")     # cipher suites
        at += 1 + hello[at]                                   # compression
        if at == len(hello):
            return None
        end = at + 2 + int.from_bytes(hello[at:at + 2], "big")
        if end != len(hello):
            raise Refused("malformed extensions")
        at += 2
        while at < end:
            kind = int.from_bytes(hello[at:at + 2], "big")
            size = int.from_bytes(hello[at + 2:at + 4], "big")
            ext = hello[at + 4:at + 4 + size]
            if len(ext) != size:
                raise Refused("malformed extension")
            at += 4 + size
            if kind != 0:
                continue
            names = ext[2:2 + int.from_bytes(ext[0:2], "big")]
            found = []
            i = 0
            while i + 3 <= len(names):
                name_type, name_len = names[i], int.from_bytes(names[i + 1:i + 3], "big")
                if name_type == 0:
                    found.append(bytes(names[i + 3:i + 3 + name_len]).decode("ascii"))
                i += 3 + name_len
            if len(found) != 1:
                raise Refused("not exactly one host name")
            return found[0]
    except (IndexError, UnicodeDecodeError) as exc:
        raise Refused("malformed ClientHello") from exc
    return None


def decide(data: bytes, allowed: str) -> None:
    """``None`` if ``data`` is a ClientHello for ``allowed`` (case-insensitive, no trailing dot);
    otherwise ``Refused``. ``EOFError`` means read more."""
    name = server_name(data)
    if name is None:
        raise Refused("ClientHello names no host")
    if name.lower() != allowed.lower():
        raise Refused(f"host {name!r} isn't allowed")


def _log(peer: object, message: str) -> None:
    print(f"egress-proxy {peer}: {message}", file=sys.stderr, flush=True)


async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while chunk := await reader.read(65536):
            writer.write(chunk)
            await writer.drain()
    except (ConnectionError, OSError):
        pass
    finally:
        try:
            writer.close()
        except (ConnectionError, OSError):
            pass


async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, *, allowed: str,
                 upstream: tuple[str, int], slots: asyncio.Semaphore) -> None:
    peer = writer.get_extra_info("peername")
    if slots.locked():
        _log(peer, "refused: too many connections")
        writer.close()
        return
    async with slots:
        data = b""
        try:
            async with asyncio.timeout(HELLO_TIMEOUT):
                while True:
                    try:
                        decide(data, allowed)
                        break
                    except EOFError:
                        chunk = await reader.read(MAX_HELLO + 5 - len(data))
                        if not chunk:
                            raise Refused("closed before a ClientHello")
                        data += chunk
        except (Refused, TimeoutError) as exc:
            _log(peer, f"refused: {exc or 'no ClientHello in time'}")
            writer.close()
            return
        try:
            up_reader, up_writer = await asyncio.open_connection(*upstream)
        except OSError as exc:
            _log(peer, f"upstream unreachable: {exc}")
            writer.close()
            return
        _log(peer, f"forwarding to {upstream[0]}:{upstream[1]}")
        up_writer.write(data)
        await asyncio.gather(_pipe(reader, up_writer), _pipe(up_reader, writer))


def _address(text: str) -> tuple[str, int]:
    host, _, port = text.rpartition(":")
    return host, int(port)


async def serve(listen: tuple[str, int], allowed: str, upstream: tuple[str, int]) -> None:
    slots = asyncio.Semaphore(MAX_CLIENTS)
    server = await asyncio.start_server(
        lambda r, w: handle(r, w, allowed=allowed, upstream=upstream, slots=slots), *listen)
    _log("-", f"listening on {listen[0]}:{listen[1]}, allowing {allowed} to {upstream[0]}:{upstream[1]}")
    async with server:
        await server.serve_forever()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--listen", type=_address, default=("0.0.0.0", 443))
    parser.add_argument("--allow", default=ALLOWED_NAME)
    parser.add_argument("--upstream", type=_address, default=UPSTREAM)
    args = parser.parse_args(argv)
    asyncio.run(serve(args.listen, args.allow, args.upstream))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
