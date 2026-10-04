"""D1_POLICY_GATE: the T4 authorization evaluator and the dispatch-or-block gate.

Implements the frozen W5-T4 contracts in ``defenses.interfaces`` and the
evaluation rules in docs/DEFENSES_AND_POLICY.md Section 1. Scientific meaning
is owned by SPEC.md Sections 6-7.

Two pieces live here:

  * ``PolicyGateAuthorizer``: the pure, argument-level ``Authorizer``. It is the
    T4 half of the gate/audit pair. The audit evaluator (T3, ``runner/``) is a
    separate implementation and this module never imports it.
  * ``PolicyGate``: wraps an ``Authorizer`` and returns a ``GateOutcome`` for one
    canonical request. It dispatches the exact request it evaluated or blocks it
    with the frozen observation. It never rewrites a request, never sees canary
    values, and never filters strings.

``gate_and_dispatch`` is the single place a runner should call, so the object
that is authorized is the object that is dispatched and a grant is committed
only when dispatch commits.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable, Mapping, Optional, Sequence

from defenses.interfaces import (
    TOOL_ARGUMENTS,
    AuthorizationDecision,
    AuthorizationNotComputable,
    Authorizer,
    CanonicalRequest,
    GateOutcome,
    GrantState,
    PriorCall,
    action_hash,
    policy_blocked_observation,
    policy_unavailable_observation,
)

EVALUATOR_VERSION = "d1-policy-gate-evaluator-v0.1.0"
GATE_VERSION = "d1-policy-gate-v0.1.0"


def _scalar_equal(left: Any, right: Any) -> bool:
    """Type-strict equality: ``1``, ``True``, and ``1.0`` are three different values."""
    scalar = (str, bool, int, float)
    if not isinstance(left, scalar) or not isinstance(right, scalar):
        return False
    return type(left) is type(right) and left == right


def _in_allowed(value: Any, allowed: Sequence[Any]) -> bool:
    return any(_scalar_equal(value, candidate) for candidate in allowed)


def _shape_codes(tool: str, args: Mapping[str, Any]) -> list[str]:
    """Shape failures end evaluation: only these codes are reported (rule 2)."""
    expected = TOOL_ARGUMENTS[tool]
    codes: list[str] = []
    names = set(args)
    if set(expected) - names:
        codes.append("argument_missing")
    if names - set(expected):
        codes.append("argument_unexpected")
    for name in expected:
        if name not in args:
            continue
        value = args[name]
        if tool == "query_db" and name == "params":
            ok = isinstance(value, Mapping)
        else:
            ok = isinstance(value, str)
        if not ok:
            codes.append("argument_type_invalid")
            break
    return codes


def _budget_exceeded(rule: Mapping[str, Any], basis: str, tool: str, prior: Sequence[PriorCall]) -> bool:
    """Rule 3 call budget, with decision 0004 item 5 for unknown dispositions."""
    max_calls = rule["max_calls"]
    same_tool = [call for call in prior if call.tool == tool]
    if basis == "requests":
        return len(same_tool) >= max_calls
    known = sum(1 for call in same_tool if call.dispatched is True)
    unknown = sum(1 for call in same_tool if call.dispatched is None)
    if known >= max_calls:
        return True
    if known + unknown < max_calls:
        return False
    raise AuthorizationNotComputable(
        f"{tool} call budget depends on {unknown} prior call(s) with unknown disposition"
    )


def _argument_codes(tool: str, rule: Mapping[str, Any], args: Mapping[str, Any]) -> list[str]:
    codes: list[str] = []
    if tool == "read_file":
        if not _in_allowed(args["path"], rule["paths"]):
            codes.append("path_not_authorized")
    elif tool == "fetch_url":
        if not _in_allowed(args["url"], rule["urls"]):
            codes.append("url_not_authorized")
    elif tool == "query_db":
        entry = next((q for q in rule["queries"] if q["query_id"] == args["query_id"]), None)
        if entry is None:
            codes.append("query_not_authorized")
        else:
            declared = entry["params"]
            params = args["params"]
            if set(params) != set(declared) or not all(
                _in_allowed(params[name], declared[name]) for name in declared if name in params
            ):
                codes.append("query_param_not_authorized")
    elif tool == "send_email":
        if not _in_allowed(args["to"], rule["recipients"]):
            codes.append("recipient_not_authorized")
        if not _in_allowed(args["subject"], rule["subjects"]):
            codes.append("subject_field_not_authorized")
        if not _in_allowed(args["body"], rule["bodies"]):
            codes.append("body_field_not_authorized")
    return codes


def _grant_step(
    policy: Mapping[str, Any], request: CanonicalRequest, grants: GrantState
) -> tuple[list[str], GrantState]:
    """Rule 3 grant check plus rule 5 transition: lowest unconsumed matching grant_id."""
    digest = action_hash(request.tool, request.normalized_args, policy["policy_version"])
    matching = [
        g
        for g in grants.grants
        if g.policy_id == policy["policy_id"]
        and g.policy_version == policy["policy_version"]
        and g.action_hash == digest
    ]
    if not matching:
        return ["grant_missing"], grants
    unconsumed = sorted((g for g in matching if not g.consumed), key=lambda g: g.grant_id)
    if not unconsumed:
        return ["grant_already_consumed"], grants
    chosen = unconsumed[0].grant_id
    next_state = GrantState(
        tuple(replace(g, consumed=True) if g.grant_id == chosen else g for g in grants.grants)
    )
    return [], next_state


class PolicyGateAuthorizer:
    """Pure T4 implementation of ``Authorizer``: no I/O, clock, randomness, or mutation."""

    evaluator_version = EVALUATOR_VERSION

    def authorize(
        self,
        task_policy: Mapping[str, Any],
        request: CanonicalRequest,
        prior_calls: Sequence[PriorCall],
        grant_state: GrantState,
    ) -> AuthorizationDecision:
        tool = request.tool
        rule = task_policy["tools"].get(tool)

        # Rule 1: a tool the policy does not list yields exactly this one code.
        if rule is None or tool not in TOOL_ARGUMENTS:
            return self._decide(["tool_not_permitted"], grant_state)

        # Rule 2: any shape failure ends evaluation with only the shape codes.
        shape = _shape_codes(tool, request.normalized_args)
        if shape:
            return self._decide(shape, grant_state)

        # Rule 3: evaluate everything else and report every failure.
        codes: list[str] = []
        if _budget_exceeded(rule, task_policy["call_budget_basis"], tool, prior_calls):
            codes.append("call_budget_exceeded")
        codes.extend(_argument_codes(tool, rule, request.normalized_args))
        next_state = grant_state
        if rule.get("requires_grant", False):
            grant_codes, next_state = _grant_step(task_policy, request, grant_state)
            codes.extend(grant_codes)
        return self._decide(codes, next_state)

    def _decide(self, codes: Sequence[str], next_state: GrantState) -> AuthorizationDecision:
        reasons = tuple(sorted(set(codes)))
        return AuthorizationDecision(
            authorized=not reasons,
            reason_codes=reasons,
            next_grant_state=next_state,
            evaluator_version=self.evaluator_version,
        )


class PolicyGate:
    """D1_POLICY_GATE. Dispatches the exact canonical request or blocks it; never rewrites."""

    gate_version = GATE_VERSION

    def __init__(self, authorizer: Optional[Authorizer] = None) -> None:
        self._authorizer: Authorizer = authorizer or PolicyGateAuthorizer()

    def evaluate(
        self,
        task_policy: Mapping[str, Any],
        request: CanonicalRequest,
        prior_calls: Sequence[PriorCall],
        grant_state: GrantState,
    ) -> GateOutcome:
        try:
            decision = self._authorizer.authorize(task_policy, request, prior_calls, grant_state)
        except AuthorizationNotComputable:
            return GateOutcome("unavailable", None, policy_unavailable_observation())
        except Exception:  # any evaluator failure fails closed (SPEC.md Section 6)
            return GateOutcome("unavailable", None, policy_unavailable_observation())
        if not isinstance(decision, AuthorizationDecision):
            return GateOutcome("unavailable", None, policy_unavailable_observation())
        if decision.authorized:
            return GateOutcome("dispatch", decision, None)
        return GateOutcome("block", decision, policy_blocked_observation(decision.reason_codes))


@dataclass(frozen=True)
class GatedResult:
    """What one gated request produced.

    ``observation`` is the tool's own result on ``dispatch`` and the frozen
    POLICY_BLOCKED or POLICY_UNAVAILABLE observation otherwise. ``grant_state``
    is the state to keep: the decision's next state only when dispatch commits,
    and the unchanged input state for any block (a block never consumes a grant).
    """

    outcome: GateOutcome
    observation: Any
    grant_state: GrantState


def gate_and_dispatch(
    gate: PolicyGate,
    dispatch: Callable[[CanonicalRequest], Any],
    task_policy: Mapping[str, Any],
    request: CanonicalRequest,
    prior_calls: Sequence[PriorCall],
    grant_state: GrantState,
) -> GatedResult:
    """Evaluate once, then dispatch the very same request object or return the block."""
    outcome = gate.evaluate(task_policy, request, prior_calls, grant_state)
    if outcome.action == "dispatch":
        assert outcome.decision is not None
        result = dispatch(request)
        return GatedResult(outcome, result, outcome.decision.next_grant_state)
    return GatedResult(outcome, dict(outcome.observation or {}), grant_state)
