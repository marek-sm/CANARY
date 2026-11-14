"""W7-T4 differential tests: the D1_POLICY_GATE evaluator against the T3 audit.

Decision 0006 and SPEC.md Section 6: the two evaluators are implemented
independently and checked against each other over the golden vectors. A
disagreement is ``gate_audit_match = false``: any difference in ``authorized``,
in the sorted ``reason_codes``, or in the grant state they commit. This file
runs both evaluators over every vector in every golden set and fails on the
first disagreement of any kind, so it is a binary engineering check and never
an attack outcome (SPEC.md Section 12).

Nothing here imports the audit from ``defenses/`` or the gate from
``oracles/``; the test module is the only place the two meet.

Vector sets are discovered, not hard-coded, so a new set (the W6-T1 task suite)
is picked up the day it merges. A set that records no independent reviewer is
still compared, but the result is reported as not trusted (decision 0006) and
``test_every_vector_set_has_its_one_independent_reviewer`` fails until it is.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from defenses.interfaces import AuthorizationNotComputable, decisions_match
from defenses.policy_gate import PolicyGateAuthorizer

audit_module = pytest.importorskip(
    "oracles.authorization.audit",
    reason="W6-T3's independent audit (W6-T3 / #47) is not on main yet",
)
conformance = pytest.importorskip(
    "oracles.authorization.conformance",
    reason="the conformance harness is not importable",
)

GOLDEN_DIR = Path(conformance.REPO_ROOT) / "oracles" / "authorization" / "golden"
VECTOR_SETS = sorted(GOLDEN_DIR.glob("*.json"))


def _evaluate(authorizer, doc, vector):
    """Return ('decision', AuthorizationDecision) or ('not_computable', None)."""
    policy, request, prior, grants = conformance.build_inputs(doc, vector)
    try:
        return "decision", authorizer.authorize(policy, request, prior, grants)
    except AuthorizationNotComputable:
        return "not_computable", None


def _cases():
    for path in VECTOR_SETS:
        doc = conformance.load_vectors(path)
        for vector in doc["vectors"]:
            yield pytest.param(path.name, doc, vector, id=f"{path.stem}:{vector['vector_id']}")


@pytest.mark.parametrize("set_name, doc, vector", list(_cases()))
def test_gate_and_audit_agree_on_every_vector(set_name, doc, vector):
    gate = PolicyGateAuthorizer()
    audit = audit_module.AuditAuthorizer()

    gate_kind, gate_decision = _evaluate(gate, doc, vector)
    audit_kind, audit_decision = _evaluate(audit, doc, vector)

    # Both must agree on whether the request can be evaluated at all.
    assert gate_kind == audit_kind, (
        f"{vector['vector_id']}: gate is {gate_kind}, audit is {audit_kind}"
    )
    if gate_kind == "not_computable":
        return

    # gate_audit_match is the frozen definition of agreement (interfaces.decisions_match).
    assert decisions_match(gate_decision, audit_decision) is True, (
        f"{vector['vector_id']}: gate=({gate_decision.authorized}, {list(gate_decision.reason_codes)}) "
        f"audit=({audit_decision.authorized}, {list(audit_decision.reason_codes)})"
    )
    # Agreement on the committed grant transition too, so the two can never
    # disagree about which grant a dispatch consumes.
    assert gate_decision.next_grant_state == audit_decision.next_grant_state, (
        f"{vector['vector_id']}: gate and audit commit different grant states"
    )


@pytest.mark.parametrize("path", VECTOR_SETS, ids=lambda p: p.stem)
def test_each_evaluator_conforms_to_the_set_on_its_own(path):
    """Agreeing on a wrong answer would pass the test above, so check each against the expectations too."""
    assert conformance.check_authorizer(PolicyGateAuthorizer(), path) == []
    assert conformance.check_authorizer(audit_module.AuditAuthorizer(), path) == []


@pytest.mark.parametrize("path", VECTOR_SETS, ids=lambda p: p.stem)
def test_differential_fixtures_classify_match_and_mismatch(path):
    """The set's own fixtures pin what counts as a match, including both-deny-for-different-reasons."""
    doc = conformance.load_vectors(path)
    from defenses.interfaces import AuthorizationDecision, GrantState

    def build(side):
        if side is None:  # a missing decision: gate_audit_match must then be null
            return None
        return AuthorizationDecision(
            authorized=side["authorized"],
            reason_codes=tuple(side["reason_codes"]),
            next_grant_state=GrantState(()),
            evaluator_version="fixture",
        )

    for fixture in doc["differential_fixtures"]:
        got = decisions_match(build(fixture["gate"]), build(fixture["audit"]))
        assert got is fixture["expected_match"], fixture["fixture_id"]


def test_every_vector_set_has_its_one_independent_reviewer():
    """Decision 0006: no differential result is trusted until one non-author reviewer is recorded."""
    unreviewed = [p.name for p in VECTOR_SETS if not conformance.review_complete(conformance.load_vectors(p))]
    assert unreviewed == [], f"vector sets with no independent reviewer recorded: {unreviewed}"
