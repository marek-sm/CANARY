"""D1_POLICY_GATE and canonicalizer behaviour that mutation testing found
unpinned (reports/cloud/mutation.md). Each test names the surviving mutants
it kills."""

import pytest

from defenses import interfaces as di
from defenses.canonicalizer import CanonicalizationError, canonicalize_arguments
from defenses.policy_gate import PolicyGate, gate_and_dispatch
from tests.test_policy_gate import _policy, _req


class _ReturnsNonDecision:
    evaluator_version = "non-decision"

    def __init__(self, value):
        self.value = value

    def authorize(self, *args):
        return self.value


@pytest.mark.parametrize("value", [None, {"authorized": True, "reason_codes": []}, True])
def test_an_evaluator_that_returns_no_decision_fails_closed(value):
    # Kills xǁPolicyGateǁevaluate__mutmut_25..31: the "not an AuthorizationDecision"
    # branch had no test, so it could return a malformed outcome.
    gate = PolicyGate(_ReturnsNonDecision(value))
    request = _req("read_file", path="docs/report.txt")
    outcome = gate.evaluate(_policy(), request, (), di.GrantState())
    assert outcome == di.GateOutcome("unavailable", None, di.policy_unavailable_observation())
    dispatched, committed = [], []
    result = gate_and_dispatch(gate, dispatched.append, _policy(), request, (), di.GrantState(),
                               commit=lambda o, keep: committed.append((o.action, keep)))
    assert dispatched == []
    assert committed == [("unavailable", di.GrantState())]
    assert result.observation == di.policy_unavailable_observation()


@pytest.mark.parametrize("url", ["", "http://localhost/a\x00b", "\x00"])
def test_an_empty_url_or_one_with_a_nul_byte_fails_canonicalization(url):
    # Kills canonicalizer.x__url__mutmut_3/5 (`or` -> `and`, and the NUL literal changed).
    with pytest.raises(CanonicalizationError, match="^unrepresentable url$"):
        canonicalize_arguments("fetch_url", {"url": url})


@pytest.mark.parametrize("to", ["a\x00@example.test", "\x00"])
def test_a_recipient_with_a_nul_byte_fails_canonicalization(to):
    # Kills canonicalizer.x__email_to__mutmut_4.
    with pytest.raises(CanonicalizationError, match="^unrepresentable recipient$"):
        canonicalize_arguments("send_email", {"to": to, "subject": "s", "body": "b"})


@pytest.mark.parametrize(
    "raw, expected",
    [
        # IPv6 literals keep their brackets (x__url__mutmut_19/20/22).
        ("http://[::1]/x", "http://[::1]/x"),
        ("http://[::1]:8080/x", "http://[::1]:8080/x"),
        ("HTTP://[FE80::1]:80/", "http://[fe80::1]/"),
        # A non-default port is kept (x__url__mutmut_36).
        ("http://Example.TEST:8080/a", "http://example.test:8080/a"),
        # User information is kept exactly, password included (x__url__mutmut_30..35).
        ("http://user:pw@example.test/a", "http://user:pw@example.test/a"),
        ("http://user@example.test/a", "http://user@example.test/a"),
        ("http://user:@example.test/a", "http://user:@example.test/a"),
        # No host at all stays hostless rather than gaining one.
        ("file:///etc/passwd", "file:///etc/passwd"),
    ],
)
def test_fetch_url_keeps_host_port_and_userinfo_exactly(raw, expected):
    assert canonicalize_arguments("fetch_url", {"url": raw})["url"] == expected


def test_a_password_in_a_url_never_canonicalizes_to_an_allowlisted_url_without_it():
    allowed = canonicalize_arguments("fetch_url", {"url": "http://user@example.test/a"})["url"]
    assert canonicalize_arguments("fetch_url", {"url": "http://user:secret@example.test/a"})["url"] != allowed
