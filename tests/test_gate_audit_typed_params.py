"""The audit evaluator compared query_db parameter values with Python ``in``, so
``True`` and ``1.0`` matched an allowlisted ``1``, while the D1_POLICY_GATE
evaluator compares type-strictly. Decision 0028 item 3 makes both strict.

docs/DEFENSES_AND_POLICY.md Section 1 says a parameter is unauthorized when its
value "is not in its allowed list", and the D1_POLICY_GATE section says "Value
comparison against allowlists is type-strict, so `1`, `1.0`, and `true` never
match each other." schemas/policy.schema.json allows integer and boolean
allowlist values, and the canonicalizer passes booleans, integers, and finite
floats through unchanged, so a model's ``{"n": true}`` reaches both evaluators.
The two then disagree (``gate_audit_match = false``) and the audit, which is
the ``authorized`` fact every security estimand reads, records the request as
authorized.

Found while reviewing mutation-testing survivors (reports/cloud/mutation.md).
No current task policy is affected: every allowlisted parameter value in
tasks/templates and the golden vector sets is a string.
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from defenses.canonicalizer import canonicalize_request
from defenses.interfaces import GrantState, decisions_match
from defenses.policy_gate import PolicyGateAuthorizer
from oracles.authorization.audit import AuditAuthorizer

ROOT = Path(__file__).resolve().parents[1]
POLICY = {
    "schema_version": "1.0.0",
    "policy_id": "typed-params",
    "policy_version": "1",
    "task_id": "typed-params",
    "call_budget_basis": "dispatches",
    "tools": {
        "query_db": {
            "max_calls": 3,
            "queries": [{"query_id": "orders_by_flags", "params": {"limit": [1], "open": [False]}}],
        }
    },
}


def test_the_policy_is_schema_valid():
    schema = json.loads((ROOT / "schemas" / "policy.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(POLICY)


@pytest.mark.parametrize("limit, open_", [(True, False), (1.0, False), (1, 0), (1, 0.0)])
def test_audit_and_gate_agree_on_values_of_another_json_type(limit, open_):
    request = canonicalize_request(
        "query_db", {"query_id": "orders_by_flags", "params": {"limit": limit, "open": open_}}, "t", 1
    )
    gate = PolicyGateAuthorizer().authorize(POLICY, request, (), GrantState())
    audit = AuditAuthorizer().authorize(POLICY, request, (), GrantState())
    assert gate.reason_codes == ("query_param_not_authorized",)
    assert audit.reason_codes == ("query_param_not_authorized",), (
        f"audit authorized {limit!r}/{open_!r} against allowlists [1]/[False]"
    )
    assert decisions_match(gate, audit) is True


def test_the_exactly_typed_values_are_authorized_by_both():
    request = canonicalize_request(
        "query_db", {"query_id": "orders_by_flags", "params": {"limit": 1, "open": False}}, "t", 1
    )
    assert PolicyGateAuthorizer().authorize(POLICY, request, (), GrantState()).authorized is True
    assert AuditAuthorizer().authorize(POLICY, request, (), GrantState()).authorized is True
