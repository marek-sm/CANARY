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
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from defenses.interfaces import (
    AuthorizationDecision,
    Authorizer,
    CanonicalRequest,
    Grant,
    GrantState,
    PriorCall,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VECTORS = REPO_ROOT / "oracles" / "authorization" / "golden" / "w5-t4-initial.json"
SCHEMA_DIR = REPO_ROOT / "schemas"


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
    return doc


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


def check_authorizer(authorizer: Authorizer, path: Path = DEFAULT_VECTORS) -> list[str]:
    """Return one human-readable line per mismatch; an empty list means conformance."""
    doc = load_vectors(path)
    failures: list[str] = []
    for vector in doc["vectors"]:
        vid = vector["vector_id"]
        expected = vector["expected"]
        policy, request, prior, grants = build_inputs(doc, vector)
        try:
            decision = authorizer.authorize(policy, request, prior, grants)
            again = authorizer.authorize(policy, request, prior, grants)
        except Exception as exc:  # an evaluator crash is a conformance failure
            failures.append(f"{vid}: raised {type(exc).__name__}: {exc}")
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
        if {g.grant_id for g in decision.next_grant_state.grants} != {g.grant_id for g in grants.grants}:
            failures.append(f"{vid}: next_grant_state added or dropped a grant")
    return failures
