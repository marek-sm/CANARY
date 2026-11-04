"""fetch_url through the real sandboxed worker + live fixture service.

SPEC.md Section 3: "fetch_url reaches only a local fixture service; redirects are
disabled" and "The tool sandbox has no arbitrary network route." The allowlist is
exact-match on the whole URL; the host must end in ``.fixture.test``; no
userinfo, port, fragment, or control characters; and only HTTP 200 is returned
(Location is never followed). In the sandbox there is no TCP/DNS at all, only the
mounted ``fixture.sock``.
"""
from __future__ import annotations

import pytest

from conftest import requires_sandbox, run_worker, skip_if_root
from tasks import registry

pytestmark = [requires_sandbox, skip_if_root]

ALLOWED = "http://catalog.fixture.test/products/sku-2201"


@pytest.fixture
def served(tmp_path):
    """A real fixture root with the fixture HTTP service running, sandboxed."""
    root = registry.reset(tmp_path / "fixtures")
    state = registry.create_state(tmp_path / "state")
    sock_dir = tmp_path / "sock"
    sock_dir.mkdir()
    with registry.fixture_service(root, sock_dir) as endpoint:
        yield root, state, endpoint


def test_allowlisted_url_fetches_only_through_the_socket(trial, served):
    root, state, endpoint = served
    r = run_worker(trial, {"tool": "fetch_url", "args": {"url": ALLOWED}},
                   fixture_root=root, state=state, socket_dir=endpoint)
    assert r.get("ok") is True and isinstance(r.get("text"), str) and r["text"], r


@pytest.mark.parametrize("url", [
    "https://example.com/",
    "http://127.0.0.1/",
    "http://localhost/",
    "http://2130706433/",                                   # decimal-encoded 127.0.0.1
    "file:///etc/passwd",
    "http://catalog.fixture.test.evil.test/products/sku-2201",   # suffix spoof
    "http://catalog.fixture.test@evil.test/products/sku-2201",   # userinfo
    "http://evil.test@catalog.fixture.test/products/sku-2201",
    "http://catalog.fixture.test:80/products/sku-2201",          # explicit port
    "http://catalog.fixture.test/products/sku-2201#x",           # fragment
    "http://catalog.fixture.test/products/sku-2201?next=http://example.com/",  # not exact-match
    "http://catalog.fixture.test/products/%73ku-2201",           # percent-encoded, not exact-match
    "http://catalog.fixture.test/products/../sku-2201",
    "http://CATALOG.fixture.test/products/sku-2201",             # case, not exact-match
    "HTTP://catalog.fixture.test/products/sku-2201",
    "http://catalog.fixture.test/products/sku-2201 ",            # trailing space
    "gopher://catalog.fixture.test/",
    "",
])
def test_non_allowlisted_or_tricky_urls_are_refused(trial, served, url):
    root, state, endpoint = served
    r = run_worker(trial, {"tool": "fetch_url", "args": {"url": url}},
                   fixture_root=root, state=state, socket_dir=endpoint)
    assert r.get("ok") is False, (url, r)


def test_proxy_and_dns_cannot_select_a_target(trial, served):
    """The sandbox environment carries no proxy variables, and fetch_url uses
    AF_UNIX only — so even a crafted hostname cannot cause an outbound lookup.
    An allowlisted-looking host that is not an exact allowlist entry is refused
    before any connection, and a real one only ever hits the socket."""
    root, state, endpoint = served
    # A host that would resolve on a real network, but is not in the allowlist.
    r = run_worker(trial, {"tool": "fetch_url", "args": {"url": "http://example.fixture.test/x"}},
                   fixture_root=root, state=state, socket_dir=endpoint)
    assert r.get("ok") is False and r.get("error") == "url_outside_fixture_allowlist", r
