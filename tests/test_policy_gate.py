"""W6-T4: request canonicalizer, D1_POLICY_GATE evaluator, and the gate."""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import MappingProxyType

import pytest

from defenses import interfaces as di
from defenses.canonicalizer import (
    NORMALIZER_VERSION,
    CanonicalizationError,
    canonicalize_arguments,
    canonicalize_request,
    canonicalize_tool_use,
)
from defenses.policy_gate import (
    PolicyGate,
    PolicyGateAuthorizer,
    gate_and_dispatch,
)
from oracles.authorization.conformance import (
    DEFAULT_VECTORS,
    build_inputs,
    check_authorizer,
    load_vectors,
)

REPO = Path(__file__).resolve().parents[1]


def _noop(outcome, state):
    """A ``commit`` callback for tests that do not inspect the durable write."""


@pytest.fixture(scope="module")
def vectors():
    return load_vectors(DEFAULT_VECTORS)


# --- evaluator conformance -------------------------------------------------


def test_authorizer_satisfies_the_protocol():
    assert isinstance(PolicyGateAuthorizer(), di.Authorizer)


def test_evaluator_passes_every_golden_vector():
    assert check_authorizer(PolicyGateAuthorizer()) == []


def test_gate_outcome_matches_every_vector(vectors):
    gate = PolicyGate()
    for vector in vectors["vectors"]:
        policy, request, prior, grants = build_inputs(vectors, vector)
        expected = vector["expected"]
        outcome = gate.evaluate(policy, request, prior, grants)
        assert outcome.action == expected["gate_action"], vector["vector_id"]
        if outcome.action == "dispatch":
            assert outcome.observation is None
        elif outcome.action == "block":
            assert outcome.observation["status"] == "POLICY_BLOCKED"
            assert outcome.observation["reason_category"] == expected["block_category"], vector["vector_id"]
        else:
            assert outcome.decision is None
            assert dict(outcome.observation) == di.policy_unavailable_observation()


def _snapshot(policy, request, prior, grants):
    return json.dumps(
        [
            _thaw(policy),
            request.tool,
            _thaw(request.normalized_args),
            [(c.tool, _thaw(c.normalized_args), c.dispatched) for c in prior],
            [(g.grant_id, g.policy_id, g.policy_version, g.action_hash, g.consumed) for g in grants.grants],
        ],
        sort_keys=True,
    )


def _thaw(value):
    if isinstance(value, (MappingProxyType, dict)):
        return {k: _thaw(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_thaw(v) for v in value]
    return value


def test_evaluator_does_not_mutate_inputs(vectors):
    authorizer = PolicyGateAuthorizer()
    for vector in vectors["vectors"]:
        policy, request, prior, grants = build_inputs(vectors, vector)
        before = _snapshot(policy, request, prior, grants)
        try:
            authorizer.authorize(policy, request, prior, grants)
        except di.AuthorizationNotComputable:
            pass
        assert _snapshot(policy, request, prior, grants) == before, vector["vector_id"]


def _policy(basis="dispatches", max_calls=1, tool_rule=None, tool="read_file"):
    rule = tool_rule or {"max_calls": max_calls, "paths": ["docs/report.txt"]}
    return {
        "schema_version": "0.1.0",
        "policy_id": "p",
        "policy_version": "1",
        "task_id": "t",
        "call_budget_basis": basis,
        "tools": {tool: rule},
    }


def _req(tool, **args):
    return di.CanonicalRequest("c", "trial", 1, tool, MappingProxyType(args), "test")


def test_reports_every_failing_code_not_just_the_first():
    policy = _policy(
        tool="send_email",
        tool_rule={
            "max_calls": 1,
            "recipients": ["a@example.test"],
            "subjects": ["s"],
            "bodies": ["b"],
            "requires_grant": True,
        },
    )
    prior = (di.PriorCall("send_email", MappingProxyType({}), True),)
    decision = PolicyGateAuthorizer().authorize(
        policy, _req("send_email", to="x@example.test", subject="y", body="z"), prior, di.GrantState()
    )
    assert decision.reason_codes == (
        "body_field_not_authorized",
        "call_budget_exceeded",
        "grant_missing",
        "recipient_not_authorized",
        "subject_field_not_authorized",
    )


def test_unknown_prior_disposition_is_not_computable_not_coerced():
    policy = _policy(max_calls=1)
    prior = (di.PriorCall("read_file", MappingProxyType({"path": "x"}), None),)
    with pytest.raises(di.AuthorizationNotComputable):
        PolicyGateAuthorizer().authorize(policy, _req("read_file", path="docs/report.txt"), prior, di.GrantState())


def test_requests_basis_counts_blocked_calls():
    prior = (di.PriorCall("read_file", MappingProxyType({"path": "x"}), False),)
    decision = PolicyGateAuthorizer().authorize(
        _policy(basis="requests"), _req("read_file", path="docs/report.txt"), prior, di.GrantState()
    )
    assert decision.reason_codes == ("call_budget_exceeded",)


@pytest.mark.parametrize("value", [1.0, True, "1", 2, None])
def test_query_param_comparison_is_type_strict(value):
    rule = {"max_calls": 1, "queries": [{"query_id": "q", "params": {"n": [1]}}]}
    policy = _policy(tool="query_db", tool_rule=rule)
    auth = PolicyGateAuthorizer()
    ok = auth.authorize(policy, _req("query_db", query_id="q", params=MappingProxyType({"n": 1})), (), di.GrantState())
    assert ok.authorized
    bad = auth.authorize(policy, _req("query_db", query_id="q", params=MappingProxyType({"n": value})), (), di.GrantState())
    assert bad.reason_codes == ("query_param_not_authorized",)


def test_grant_binds_nested_params_and_policy_version():
    rule = {
        "max_calls": 1,
        "queries": [{"query_id": "q", "params": {"status": ["open", "closed"]}}],
        "requires_grant": True,
    }
    policy = _policy(tool="query_db", tool_rule=rule)
    args = MappingProxyType({"query_id": "q", "params": MappingProxyType({"status": "open"})})
    digest = di.action_hash("query_db", args, "1")
    grants = di.GrantState((di.Grant("g1", "p", "1", digest),))
    request = di.CanonicalRequest("c", "trial", 1, "query_db", args, "test")
    auth = PolicyGateAuthorizer()
    decision = auth.authorize(policy, request, (), grants)
    assert decision.authorized and decision.next_grant_state.grants[0].consumed
    stale = di.GrantState((di.Grant("g1", "p", "2", digest),))
    assert auth.authorize(policy, request, (), stale).reason_codes == ("grant_missing",)


# --- the gate --------------------------------------------------------------


class _Boom:
    evaluator_version = "boom"

    def authorize(self, *args):
        raise RuntimeError("evaluator crashed")


class _Unknown:
    evaluator_version = "unknown"

    def authorize(self, *args):
        raise di.AuthorizationNotComputable("unknown prior")


@pytest.mark.parametrize("authorizer", [_Boom(), _Unknown()])
def test_gate_fails_closed_with_the_frozen_unavailable_observation(authorizer):
    outcome = PolicyGate(authorizer).evaluate(_policy(), _req("read_file", path="docs/report.txt"), (), di.GrantState())
    assert outcome.action == "unavailable"
    assert outcome.decision is None
    assert dict(outcome.observation) == di.policy_unavailable_observation()


def test_gate_dispatches_the_exact_request_object_it_evaluated():
    seen = []
    request = _req("read_file", path="docs/report.txt")
    result = gate_and_dispatch(
        PolicyGate(), lambda r: seen.append(r) or {"ok": True}, _policy(), request, (), di.GrantState(), commit=_noop
    )
    assert len(seen) == 1 and seen[0] is request
    assert result.outcome.action == "dispatch" and result.observation == {"ok": True}


def test_blocked_request_is_never_dispatched_and_observation_leaks_nothing():
    called = []
    request = _req("read_file", path="config/secret.env")
    result = gate_and_dispatch(
        PolicyGate(), lambda r: called.append(r), _policy(), request, (), di.GrantState(), commit=_noop
    )
    assert called == []
    assert result.observation == di.policy_blocked_observation(["path_not_authorized"])
    blob = json.dumps(result.observation)
    assert "secret" not in blob and "report" not in blob


def test_block_never_consumes_a_matching_grant_but_dispatch_does(vectors):
    # deny-email-over-budget-with-grant: the evaluator's transition marks the grant
    # consumed (D0/D2 would dispatch it), but the gate blocks, so nothing commits.
    vector = next(v for v in vectors["vectors"] if v["vector_id"] == "deny-email-over-budget-with-grant")
    policy, request, prior, grants = build_inputs(vectors, vector)
    outcome = PolicyGate().evaluate(policy, request, prior, grants)
    assert outcome.action == "block" and outcome.decision.next_grant_state != grants
    result = gate_and_dispatch(PolicyGate(), lambda r: {"ok": True}, policy, request, prior, grants, commit=_noop)
    assert result.grant_state == grants

    allowed = next(v for v in vectors["vectors"] if v["vector_id"] == "allow-email-granted")
    policy, request, prior, grants = build_inputs(vectors, allowed)
    result = gate_and_dispatch(PolicyGate(), lambda r: {"ok": True}, policy, request, prior, grants, commit=_noop)
    assert result.grant_state != grants and sum(g.consumed for g in result.grant_state.grants) == 1


def test_gate_never_dispatches_what_the_evaluator_rejects(vectors):
    gate = PolicyGate()
    for vector in vectors["vectors"]:
        policy, request, prior, grants = build_inputs(vectors, vector)
        called = []
        result = gate_and_dispatch(gate, lambda r: called.append(r) or {}, policy, request, prior, grants, commit=_noop)
        assert bool(called) == (vector["expected"]["gate_action"] == "dispatch"), vector["vector_id"]
        assert result.outcome.action == vector["expected"]["gate_action"]


def test_gate_is_canary_blind_and_independent_of_the_audit():
    for name in ("policy_gate.py", "canonicalizer.py", "datamarking.py"):
        source = (REPO / "defenses" / name).read_text(encoding="utf-8")
        assert "contains_canary" not in source
        assert not re.search(r"^\s*(from|import)\s+runner\b", source, re.MULTILINE), name
        assert not re.search(r"^\s*(from|import)\s+oracles\b", source, re.MULTILINE), name


# --- canonicalizer ---------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("docs/report.txt", "docs/report.txt"),
        ("./docs/report.txt", "docs/report.txt"),
        ("docs//report.txt", "docs/report.txt"),
        ("docs/./report.txt", "docs/report.txt"),
        ("docs/../docs/report.txt", "docs/report.txt"),
        ("../private/keys.txt", "../private/keys.txt"),
        ("/docs/report.txt", "/docs/report.txt"),
        ("//docs/report.txt", "/docs/report.txt"),
        ("docs/caf\u0065\u0301.txt", "docs/caf\u00e9.txt"),
    ],
)
def test_read_file_path_normalization(raw, expected):
    assert canonicalize_arguments("read_file", {"path": raw}) == {"path": expected}


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("HTTP://LocalHost:80/a", "http://localhost/a"),
        ("http://localhost:8080", "http://localhost:8080/"),
        ("https://localhost:443/x#frag", "https://localhost/x"),
        ("http://localhost/a%7eb", "http://localhost/a~b"),
        ("http://localhost/a%2fb", "http://localhost/a%2Fb"),
        ("http://localhost/p?q=%41%3d", "http://localhost/p?q=A%3D"),
    ],
)
def test_fetch_url_normalization(raw, expected):
    assert canonicalize_arguments("fetch_url", {"url": raw})["url"] == expected


def test_send_email_normalization():
    args = canonicalize_arguments(
        "send_email", {"to": "  Support-Lead@Example.TEST \n", "subject": "a\r\nb", "body": "x\ry"}
    )
    assert args == {"to": "support-lead@example.test", "subject": "a\nb", "body": "x\ny"}


def test_query_params_are_nfc_and_read_only():
    args = canonicalize_arguments("query_db", {"query_id": "q", "params": {"k": "e\u0301", "n": 1}})
    assert args["params"] == {"k": "\u00e9", "n": 1}
    with pytest.raises(TypeError):
        args["params"]["n"] = 2


@pytest.mark.parametrize(
    "tool, raw",
    [
        ("shell", {"cmd": "ls"}),
        ("read_file", {}),
        ("read_file", {"path": "a", "mode": "rb"}),
        ("read_file", {"path": 5}),
        ("read_file", {"path": ""}),
        ("read_file", {"path": "a\x00b"}),
        ("read_file", "docs/report.txt"),
        ("fetch_url", {"url": "http://[::1"}),
        ("fetch_url", {"url": "http://localhost:99999/"}),
        ("query_db", {"query_id": "q", "params": ["a"]}),
        ("query_db", {"query_id": "q", "params": {"n": {1, 2}}}),
        ("query_db", {"query_id": "q", "params": {"n": float("nan")}}),
        ("send_email", {"to": "a@example.test", "subject": "s"}),
    ],
)
def test_unrepresentable_calls_fail_canonicalization(tool, raw):
    with pytest.raises(CanonicalizationError):
        canonicalize_arguments(tool, raw)


def test_out_of_root_and_off_allowlist_requests_are_evaluable_not_failures():
    request = canonicalize_request("read_file", {"path": "../private/keys.txt"}, "trial", 1)
    decision = PolicyGateAuthorizer().authorize(_policy(), request, (), di.GrantState())
    assert decision.reason_codes == ("path_not_authorized",)
    url = canonicalize_request("fetch_url", {"url": "http://evil.example.test/x"}, "trial", 1)
    assert url.normalized_args["url"] == "http://evil.example.test/x"


@pytest.mark.parametrize(
    "tool, raw",
    [
        ("read_file", {"path": "./docs//a/../report.txt"}),
        ("fetch_url", {"url": "HTTP://Localhost:80/a%7e%2f?x=%3d#f"}),
        ("send_email", {"to": " A@B.TEST ", "subject": "s\r\n", "body": "b"}),
        ("query_db", {"query_id": "q", "params": {"k": "e\u0301"}}),
    ],
)
def test_canonicalization_is_a_fixed_point(tool, raw):
    once = canonicalize_arguments(tool, raw)
    twice = canonicalize_arguments(tool, once)
    assert once == twice
    assert di.action_hash(tool, once, "1") == di.action_hash(tool, twice, "1")


def test_equivalent_spellings_share_one_action_hash_and_one_decision():
    a = canonicalize_request("read_file", {"path": "./docs//report.txt"}, "trial", 1)
    b = canonicalize_request("read_file", {"path": "docs/report.txt"}, "trial", 1)
    assert a.normalized_args == b.normalized_args
    auth = PolicyGateAuthorizer()
    assert auth.authorize(_policy(), a, (), di.GrantState()) == auth.authorize(_policy(), b, (), di.GrantState())


def test_canonical_request_is_immutable_and_versioned():
    request = canonicalize_request("read_file", {"path": "docs/report.txt"}, "trial", 3)
    assert request.normalizer_version == NORMALIZER_VERSION and request.call_id == "trial:step3:call1"
    with pytest.raises(TypeError):
        request.normalized_args["path"] = "other"
    with pytest.raises(Exception):
        request.tool = "send_email"  # frozen dataclass


def test_tool_use_block_shape():
    block = {"type": "tool_use", "id": "toolu_1", "name": "read_file", "input": {"path": "docs/report.txt"}}
    assert canonicalize_tool_use(block, "trial", 1).tool == "read_file"
    for bad in (
        {**block, "extra": 1},
        {**block, "id": ""},
        {**block, "type": "text"},
        {k: v for k, v in block.items() if k != "input"},
    ):
        with pytest.raises(CanonicalizationError):
            canonicalize_tool_use(bad, "trial", 1)


# --- review fixes: durable commit before dispatch, JSON evidence, filter path, key collisions ---


def _granted_email(vectors):
    allowed = next(v for v in vectors["vectors"] if v["vector_id"] == "allow-email-granted")
    return build_inputs(vectors, allowed)


def test_grant_transition_commits_before_the_tool_runs(vectors):
    policy, request, prior, grants = _granted_email(vectors)
    order = []

    def commit(outcome, state):
        order.append(("commit", outcome.action, sum(g.consumed for g in state.grants)))

    result = gate_and_dispatch(
        PolicyGate(), lambda r: order.append(("dispatch",)) or {"ok": True}, policy, request, prior, grants, commit=commit
    )
    assert order == [("commit", "dispatch", 1), ("dispatch",)]
    assert result.grant_state != grants


def test_grant_stays_consumed_when_the_tool_errors_after_its_effect(vectors):
    policy, request, prior, grants = _granted_email(vectors)
    committed = []
    effects = []

    def tool(r):
        effects.append(r)  # the effect happens ...
        raise RuntimeError("tool failed after its effect")  # ... and then the tool errors

    with pytest.raises(RuntimeError):
        gate_and_dispatch(
            PolicyGate(), tool, policy, request, prior, grants, commit=lambda o, s: committed.append(s)
        )
    assert len(effects) == 1 and len(committed) == 1
    # Replaying with the state the runner durably committed cannot reuse the grant.
    replay = gate_and_dispatch(
        PolicyGate(), lambda r: effects.append(r) or {"ok": True}, policy, request, prior, committed[0], commit=_noop
    )
    assert replay.outcome.action == "block"
    assert "grant_already_consumed" in replay.outcome.decision.reason_codes
    assert len(effects) == 1


def test_nothing_dispatches_if_the_durable_commit_fails(vectors):
    policy, request, prior, grants = _granted_email(vectors)
    called = []

    def commit(outcome, state):
        raise OSError("disk full")

    with pytest.raises(OSError):
        gate_and_dispatch(PolicyGate(), lambda r: called.append(r) or {}, policy, request, prior, grants, commit=commit)
    assert called == []


def test_a_block_commits_the_unchanged_grant_state(vectors):
    deny = next(v for v in vectors["vectors"] if v["vector_id"] == "deny-email-over-budget-with-grant")
    policy, request, prior, grants = build_inputs(vectors, deny)
    seen = []
    gate_and_dispatch(
        PolicyGate(), lambda r: {"ok": True}, policy, request, prior, grants, commit=lambda o, s: seen.append((o.action, s))
    )
    assert seen == [("block", grants)]


def test_nested_query_params_are_json_serializable_in_the_requested_event():
    from agent.loop import requested_payload

    block = {"type": "tool_use", "id": "t1", "name": "query_db",
             "input": {"query_id": "q1", "params": {"k": "v", "nested": {"a": [1, {"b": 2}]}}}}
    request = canonicalize_tool_use(block, "trial", 1)
    payload = requested_payload(request, block, 1)
    text = json.dumps(payload)  # raised "mappingproxy is not JSON serializable" before the fix
    assert json.loads(text)["normalized_args"]["params"] == {"k": "v", "nested": {"a": [1, {"b": 2}]}}


def test_filtered_call_to_a_registered_tool_is_recorded_without_dispatch():
    from agent.loop import run_loop

    call = {"type": "tool_use", "id": "t1", "name": "send_email",
            "input": {"to": "a@example.com", "subject": "s", "body": "b"}}

    class Provider:
        def complete(self, *args):
            return {"raw_response": {"content": [call], "stop_reason": "content_filter"}}

    events, dispatched = [], []
    outcome = run_loop(
        Provider(), [], tool_schemas=[], decoding={}, model_request={}, on_attempt=lambda *a: None,
        dispatch=lambda r: dispatched.append(r), on_tool=lambda kind, payload: events.append((kind, payload)),
        supported_tools=("read_file", "send_email"),
    )
    assert outcome.termination_reason == "provider_content_filter" and dispatched == []
    assert [kind for kind, _ in events] == ["tool_requested"] and events[0][1]["tool"] == "send_email"


def test_keys_that_collide_after_normalization_are_rejected_in_either_order():
    composed, decomposed = "\u00e9", "e\u0301"  # distinct keys, the same NFC key
    for params in ({composed: "X", decomposed: "Y"}, {decomposed: "Y", composed: "X"}):
        with pytest.raises(CanonicalizationError, match="collide"):
            canonicalize_arguments("query_db", {"query_id": "q", "params": params})
    ok = canonicalize_arguments("query_db", {"query_id": "q", "params": {composed: "X", "z": "Y"}})
    assert dict(ok["params"]) == {composed: "X", "z": "Y"}
