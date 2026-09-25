"""Run any ``Authorizer`` against a golden authorization vector set.

Both the D1_POLICY_GATE evaluator (T4) and the independent audit evaluator (T3)
call ``check_authorizer`` from their own tests. This module holds no evaluator
logic of its own, so importing it does not couple the two implementations.

Usage in a test:

    from oracles.authorization.conformance import check_authorizer, DEFAULT_VECTORS
    assert check_authorizer(MyEvaluator(), DEFAULT_VECTORS) == []
"""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from defenses.interfaces import (
    AuthorizationDecision,
    AuthorizationNotComputable,
    Authorizer,
    CanonicalRequest,
    Grant,
    GrantState,
    PriorCall,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VECTORS = REPO_ROOT / "oracles" / "authorization" / "golden" / "w5-t4-initial.json"
SCHEMA_DIR = REPO_ROOT / "schemas"

# SPEC.md Section 6: with three or more active contributors, golden vectors need
# two independent reviewers before any differential result is trusted.
REQUIRED_REVIEWERS = 2


@lru_cache(maxsize=None)
def _validator(name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def load_vectors(path: Path = DEFAULT_VECTORS) -> dict[str, Any]:
    """Load and schema-validate a vector set and every policy inside it."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    _validator("authorization_vectors").validate(doc)
    for policy in doc["policies"].values():
        _validator("policy").validate(policy)
    if doc["authored_by"] in doc["reviewed_by"]:
        raise ValueError("the author of a vector set cannot also review it")
    return doc


def review_complete(doc: Mapping[str, Any]) -> bool:
    """True once enough independent reviewers are recorded to trust a differential result."""
    reviewers = set(doc["reviewed_by"]) - {doc["authored_by"]}
    return len(reviewers) >= REQUIRED_REVIEWERS


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def build_inputs(
    doc: Mapping[str, Any], vector: Mapping[str, Any]
) -> tuple[Mapping[str, Any], CanonicalRequest, tuple[PriorCall, ...], GrantState]:
    policy = doc["policies"][vector["policy_id"]]
    request = CanonicalRequest(
        call_id=vector["vector_id"],
        logical_trial_id=f"golden:{doc['vector_set_id']}",
        step=len(vector["prior_calls"]) + 1,
        tool=vector["request"]["tool"],
        normalized_args=_freeze(copy.deepcopy(vector["request"]["normalized_args"])),
        normalizer_version="golden-vectors",
    )
    prior = tuple(
        PriorCall(c["tool"], _freeze(copy.deepcopy(c["normalized_args"])), c["dispatched"])
        for c in vector["prior_calls"]
    )
    grants = GrantState(tuple(Grant(**g) for g in vector["grants"]))
    return _freeze(copy.deepcopy(policy)), request, prior, grants


def _consumed_ids(before: GrantState, after: GrantState) -> list[str]:
    was = {g.grant_id for g in before.grants if g.consumed}
    now = {g.grant_id for g in after.grants if g.consumed}
    return sorted(now - was)


def _with_consumed(state: GrantState, grant_ids: list[str]) -> GrantState:
    """The input state with exactly these grants marked consumed and nothing else changed."""
    ids = set(grant_ids)
    return GrantState(tuple(replace(g, consumed=True) if g.grant_id in ids else g for g in state.grants))


def _check_single_use(
    authorizer: Authorizer, vid: str, policy: Any, request: CanonicalRequest,
    prior: tuple[PriorCall, ...], state: GrantState,
) -> list[str]:
    """Replay the same request against each committed grant state until no grant is left.

    Each replay that uses a grant must consume exactly one grant that was unused
    before, so no grant is ever used twice. Once none is left, the replay must be
    denied with ``grant_already_consumed`` and leave the state unchanged. This is
    about grants, not the verdict: a request can consume a matching grant while
    denied for another reason (SPEC.md Section 7), since D0_BASELINE and
    D2_DATAMARKING still dispatch it.
    """
    for _ in range(len(state.grants) + 1):
        try:
            decision = authorizer.authorize(policy, request, prior, state)
        except Exception as exc:
            return [f"{vid}: replay raised {type(exc).__name__}: {exc}"]
        newly = _consumed_ids(state, decision.next_grant_state)
        if newly:
            if len(newly) != 1 or decision.next_grant_state != _with_consumed(state, newly):
                return [f"{vid}: replay consumed more than one grant or changed another grant"]
            state = decision.next_grant_state
            continue
        failures: list[str] = []
        if decision.next_grant_state != state:
            failures.append(f"{vid}: replay changed the grant state without consuming a grant")
        if decision.authorized or "grant_already_consumed" not in decision.reason_codes:
            failures.append(f"{vid}: replay after every matching grant was used was not denied with grant_already_consumed")
        return failures
    return [f"{vid}: replay kept consuming grants after every grant was used"]


def check_authorizer(authorizer: Authorizer, path: Path = DEFAULT_VECTORS) -> list[str]:
    """Return one human-readable line per mismatch; an empty list means conformance.

    A vector with ``evaluable = false`` passes only if the evaluator raises
    ``AuthorizationNotComputable``; any other exception is a failure.
    """
    doc = load_vectors(path)
    failures: list[str] = []
    for vector in doc["vectors"]:
        vid = vector["vector_id"]
        expected = vector["expected"]
        policy, request, prior, grants = build_inputs(doc, vector)
        try:
            decision = authorizer.authorize(policy, request, prior, grants)
            again = authorizer.authorize(policy, request, prior, grants)
        except AuthorizationNotComputable as exc:
            if expected["evaluable"]:
                failures.append(f"{vid}: raised AuthorizationNotComputable on an evaluable request: {exc}")
            continue
        except Exception as exc:  # an evaluator crash is a conformance failure
            failures.append(f"{vid}: raised {type(exc).__name__}: {exc}")
            continue
        if not expected["evaluable"]:
            failures.append(f"{vid}: returned a decision, expected AuthorizationNotComputable")
            continue
        if not isinstance(decision, AuthorizationDecision):
            failures.append(f"{vid}: returned {type(decision).__name__}, not AuthorizationDecision")
            continue
        if decision != again:
            failures.append(f"{vid}: not deterministic across two identical calls")
        if decision.authorized != expected["authorized"]:
            failures.append(f"{vid}: authorized={decision.authorized}, expected {expected['authorized']}")
        if list(decision.reason_codes) != expected["reason_codes"]:
            failures.append(f"{vid}: reason_codes={list(decision.reason_codes)}, expected {expected['reason_codes']}")
        consumed = _consumed_ids(grants, decision.next_grant_state)
        if consumed != sorted(expected["consumes_grant_ids"]):
            failures.append(f"{vid}: consumes {consumed}, expected {sorted(expected['consumes_grant_ids'])}")
        if decision.next_grant_state != _with_consumed(grants, expected["consumes_grant_ids"]):
            failures.append(
                f"{vid}: next_grant_state must equal the input with only {sorted(expected['consumes_grant_ids'])} "
                "marked consumed (no grant added, dropped, reordered, edited, or un-consumed)"
            )
        if expected["consumes_grant_ids"]:
            failures.extend(_check_single_use(authorizer, vid, policy, request, prior, decision.next_grant_state))
    return failures
