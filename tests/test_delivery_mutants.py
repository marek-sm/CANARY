"""Tool-result delivery behaviour that mutation testing found unpinned
(reports/cloud/mutation.md). Each test names the surviving mutants it kills.

These drive ``TrialTools`` directly with a stand-in tool runner, so no tool
process starts and no provider is involved.
"""

import hashlib
import json

import pytest

from defenses.canonicalizer import canonicalize_request
from defenses.interfaces import DATAMARK_MARKER as M
from defenses.interfaces import Grant, GrantState, action_hash, canonical_json_bytes
from runner import delivery
from runner.delivery import SEND_EFFECT_ORACLE, SINK_NAME, DispatchOutcomeUnknown, TrialTools, create_state

POLICY = {
    "schema_version": "1.0.0", "policy_id": "p", "policy_version": "1", "task_id": "t",
    "call_budget_basis": "dispatches",
    "tools": {"read_file": {"max_calls": 5, "paths": ["docs/report.txt"]}},
}


def _send(n):
    return canonicalize_request("send_email", {"to": "x@example.test", "subject": "s", "body": "b"}, "t", n,
                                call_id=f"c{n}")


def _tools(tmp_path, configuration="D0_BASELINE", stored=None, receipts=()):
    state = create_state(tmp_path / "state", fresh=True)
    (state / SINK_NAME).write_text("".join(json.dumps(r) + "\n" for r in receipts), encoding="utf-8")
    logged, synced = [], []
    tools = TrialTools(
        configuration=configuration, policy=POLICY, grant_state=GrantState(), root=tmp_path, state=state,
        endpoint=str(tmp_path), log=lambda kind, payload: logged.append((kind, dict(payload))),
        sync_sink=lambda rs: synced.append(list(rs)), stored=stored or {},
        run_tool=lambda root, st, endpoint, req: {"ok": True},
    )
    return tools, logged, synced


def _stored_send(n, receipt=True):
    stored = {
        ("tool_dispatch", f"c{n}"): {"call_id": f"c{n}", "step": n, "blocked": False, "dispatched": True},
        ("tool_result", f"c{n}"): {"call_id": f"c{n}", "step": n, "observation": {"ok": True}},
    }
    if receipt:
        stored[("sink_receipt", f"c{n}")] = {"call_id": f"c{n}", "step": n, "receipt": {"n": n}, "sink_received": True}
    return stored


def test_a_blocked_send_records_no_sink_receipt_and_the_send_oracle(tmp_path):
    # Kills xǁTrialToolsǁ_blocked_effect__mutmut_2..15: a D1_POLICY_GATE block's effect
    # facts are known false, under the oracle of the tool that was asked for.
    tools, logged, _ = _tools(tmp_path, "D1_POLICY_GATE")
    request = _send(1)
    observation = tools.dispatch(request)
    assert observation["status"] == "POLICY_BLOCKED"
    assert tools.effect(request, observation) == {
        "effect_observed": False, "effect_oracle_id": SEND_EFFECT_ORACLE, "sink_received": False,
    }
    read = canonicalize_request("read_file", {"path": "secret.txt"}, "t", 2, call_id="c2")
    observation = tools.dispatch(read)
    assert tools.effect(read, observation) == {
        "effect_observed": False, "effect_oracle_id": "read_file-returned-v0.1.0", "sink_received": False,
    }


def test_resumed_sends_keep_their_receipts_and_a_new_send_takes_the_next_one(tmp_path):
    # Kills xǁTrialToolsǁ_account_send__mutmut_10..17 (the stored-receipt branch and its
    # count) and _46..48 (the fresh branch's count): two resumed sends account for the
    # first two receipts, so the third send's receipt is the third one, alone.
    receipts = [{"n": 1}, {"n": 2}, {"n": 3}]
    tools, logged, synced = _tools(tmp_path, stored={**_stored_send(1), **_stored_send(2)}, receipts=receipts)
    for n in (1, 2):
        request = _send(n)
        observation = tools.dispatch(request)
        assert tools.effect(request, observation) == {
            "effect_observed": True, "effect_oracle_id": SEND_EFFECT_ORACLE, "sink_received": True,
        }
    assert tools.accounted == 2
    request = _send(3)
    observation = tools.dispatch(request)
    assert tools.effect(request, observation) == {
        "effect_observed": True, "effect_oracle_id": SEND_EFFECT_ORACLE, "sink_received": True,
    }
    assert ("sink_receipt", {"call_id": "c3", "step": 3, "receipt": {"n": 3}, "sink_received": True}) in logged
    assert synced == [receipts]
    assert tools.accounted == 3


def test_a_send_with_no_new_receipt_is_known_not_received(tmp_path):
    tools, logged, synced = _tools(tmp_path)
    request = _send(1)
    observation = tools.dispatch(request)
    assert tools.effect(request, observation) == {
        "effect_observed": False, "effect_oracle_id": SEND_EFFECT_ORACLE, "sink_received": False,
    }
    assert synced == [] and not any(kind == "sink_receipt" for kind, _ in logged)


def test_one_send_with_two_new_receipts_leaves_the_effect_unknown(tmp_path):
    # Kills xǁTrialToolsǁ_account_send__mutmut_27 (`> 1` -> `> 2`).
    tools, logged, synced = _tools(tmp_path, receipts=[{"n": 1}, {"n": 2}])
    request = _send(1)
    observation = tools.dispatch(request)
    assert tools.effect(request, observation) == {
        "effect_observed": None, "effect_oracle_id": SEND_EFFECT_ORACLE, "sink_received": None,
    }
    assert synced == [] and not any(kind == "sink_receipt" for kind, _ in logged)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("plain text", f"plain{M}text"),
        ("42", "42"),
        ('{"a": "x y", "b": "é z"}', f'{{"a": "x{M}y", "b": "é{M}z"}}'),
        ('{\n  "a": "x y"\n}', f'{{\n  "a": "x{M}y"\n}}'),
        ('["p q", 1]', f'["p{M}q", 1]'),
        (7, 7),
        (None, None),
    ],
)
def test_a_database_value_is_marked_as_text_or_as_json_keeping_its_layout(value, expected):
    # Kills x__mark_value__mutmut_2..22: a text value comes back as marked text, never
    # as a marker count, and JSON keeps its one-line or indented layout and its
    # non-ASCII characters.
    assert delivery._mark_value(value) == expected


def test_a_read_result_is_marked_as_text_and_a_fetch_result_as_html(tmp_path):
    # Kills x_mark_observation__mutmut_12 (every text marked as HTML).
    text = "a < b & c"
    assert delivery.mark_observation("read_file", {"ok": True, "text": text})["text"] == f"a{M}<{M}b{M}&{M}c"
    assert delivery.mark_observation("fetch_url", {"ok": True, "text": "<p>a b</p>"})["text"] == f"<p>a{M}b</p>"
    failed = {"ok": False, "error": "not found here", "text": "x y"}
    assert delivery.mark_observation("read_file", failed) == failed


def _read(n, path="docs/report.txt"):
    return canonicalize_request("read_file", {"path": path}, "t", n, call_id=f"c{n}")


@pytest.mark.parametrize("configuration", ["D0_BASELINE", "D2_DATAMARKING"])
def test_an_ungated_dispatch_records_what_happened_and_settles_as_dispatched(tmp_path, configuration):
    # Kills xǁTrialToolsǁdispatch__mutmut_159..181 and _settle__mutmut_2..9: under
    # D0_BASELINE and D2_DATAMARKING a request is dispatched, never blocked, its
    # disposition_observed is null, and it counts as a dispatched prior call.
    tools, logged, _ = _tools(tmp_path, configuration)
    tools.run_tool = lambda root, st, endpoint, req: {"ok": True, "text": "a b"}
    request = _read(1)
    observation = tools.dispatch(request)
    assert logged[0] == ("tool_dispatch", {"call_id": "c1", "step": 1, "blocked": False, "dispatched": True,
                                           "disposition_observed": None})
    kind, result = logged[1]
    assert kind == "tool_result" and result["execution_succeeded"] is True
    if configuration == "D2_DATAMARKING":
        # Kills dispatch__mutmut_199/203: the hash of what the tool returned before marking.
        assert result["unmarked_observation_sha256"] == hashlib.sha256(
            canonical_json_bytes({"ok": True, "text": "a b"})).hexdigest()
        assert observation == {"ok": True, "text": f"a{M}b"}
    else:
        assert "unmarked_observation_sha256" not in result
        assert observation == {"ok": True, "text": "a b"}
    assert [(p.tool, dict(p.normalized_args), p.dispatched) for p in tools.prior] == [
        ("read_file", {"path": "docs/report.txt"}, True)]
    assert tools.effect(request, observation) == {
        "effect_observed": True, "effect_oracle_id": "read_file-returned-v0.1.0", "sink_received": False}


@pytest.mark.parametrize("ok, expected", [(False, False), (None, None), ("yes", None), (1, None)])
def test_a_read_effect_is_the_tool_s_own_boolean_or_unknown(tmp_path, ok, expected):
    # Kills xǁTrialToolsǁeffect__mutmut_22..28: a non-boolean `ok` is unknown, and a read
    # never reaches the sink.
    tools, _, _ = _tools(tmp_path)
    tools.run_tool = lambda root, st, endpoint, req: {"ok": ok}
    request = _read(1)
    observation = tools.dispatch(request)
    assert tools.effect(request, observation) == {
        "effect_observed": expected, "effect_oracle_id": "read_file-returned-v0.1.0", "sink_received": False}


def test_a_stored_effect_is_replayed_exactly(tmp_path):
    # Kills xǁTrialToolsǁeffect__mutmut_1..12.
    stored = {("effect_observation", "c1"): {"call_id": "c1", "step": 1, "effect_observed": None,
                                             "effect_oracle_id": "read_file-returned-v0.1.0", "sink_received": False}}
    tools, _, _ = _tools(tmp_path, stored=stored)
    assert tools.effect(_read(1), {"ok": True}) == {
        "effect_observed": None, "effect_oracle_id": "read_file-returned-v0.1.0", "sink_received": False}


def test_a_d1_block_settles_as_not_dispatched_and_keeps_the_grant_state(tmp_path):
    # Kills dispatch__mutmut_119..136: the blocked disposition, its observation, and the
    # prior call it leaves behind.
    tools, logged, _ = _tools(tmp_path, "D1_POLICY_GATE")
    request = _read(1, "secret.txt")
    observation = tools.dispatch(request)
    kinds = [k for k, _ in logged]
    assert kinds == ["authorization_decision", "tool_dispatch"]
    decision = logged[0][1]
    assert decision["gate_action"] == "block"
    assert decision["gate_decision"]["reason_codes"] == ["path_not_authorized"]
    disposition = logged[1][1]
    assert disposition == {"call_id": "c1", "step": 1, "blocked": True, "dispatched": False,
                           "disposition_observed": True, "observation": observation}
    assert observation["status"] == "POLICY_BLOCKED"
    assert [(p.tool, p.dispatched) for p in tools.prior] == [("read_file", False)]
    assert tools.grant_state == GrantState()


def test_a_resumed_block_is_replayed_without_running_the_tool(tmp_path):
    # Kills dispatch__mutmut_14..24: a stored block returns its stored observation and
    # settles as not dispatched.
    stored_observation = {"status": "POLICY_BLOCKED", "reason_category": "argument_not_permitted", "message": "m"}
    stored = {("tool_dispatch", "c1"): {"call_id": "c1", "step": 1, "blocked": True, "dispatched": False,
                                        "observation": stored_observation}}
    tools, logged, _ = _tools(tmp_path, "D1_POLICY_GATE", stored=stored)
    tools.run_tool = lambda *args: pytest.fail("a stored block must not run the tool")
    request = _read(1, "secret.txt")
    assert tools.dispatch(request) == stored_observation
    assert logged == []
    assert [(p.tool, p.dispatched) for p in tools.prior] == [("read_file", False)]
    assert tools.effect(request, stored_observation) == {
        "effect_observed": False, "effect_oracle_id": "read_file-returned-v0.1.0", "sink_received": False}


def test_a_resumed_gate_decision_must_match_the_one_the_gate_makes_now(tmp_path):
    # Kills dispatch__mutmut_91..99: a stored decision that differs refuses; an equal one
    # is not logged twice.
    same = {"call_id": "c1", "step": 1, "gate_action": "block",
            "gate_decision": {"authorized": False, "reason_codes": ["path_not_authorized"],
                              "evaluator_version": "d1-policy-gate-evaluator-v0.1.0"}}
    tools, logged, _ = _tools(tmp_path, "D1_POLICY_GATE", stored={("authorization_decision", "c1"): same})
    tools.dispatch(_read(1, "secret.txt"))
    assert [k for k, _ in logged] == ["tool_dispatch"]
    differs = {**same, "gate_action": "dispatch"}
    tools, logged, _ = _tools(tmp_path / "again", "D1_POLICY_GATE", stored={("authorization_decision", "c1"): differs})
    with pytest.raises(DispatchOutcomeUnknown):
        tools.dispatch(_read(1, "secret.txt"))


GRANT_POLICY = {
    "schema_version": "1.0.0", "policy_id": "p", "policy_version": "1", "task_id": "t",
    "call_budget_basis": "dispatches",
    "tools": {"send_email": {"max_calls": 3, "requires_grant": True, "recipients": ["x@example.test"],
                             "subjects": ["s"], "bodies": ["b"]}},
}


def _granted_tools(tmp_path, configuration, stored=None):
    tools, logged, synced = _tools(tmp_path, configuration, stored=stored)
    tools.policy = GRANT_POLICY
    digest = action_hash("send_email", _send(1).normalized_args, "1")
    tools.grant_state = GrantState((Grant("g1", "p", "1", digest), Grant("g2", "p", "1", digest)))
    return tools, logged


def _consumed(tools):
    return [g.grant_id for g in tools.grant_state.grants if g.consumed]


@pytest.mark.parametrize("configuration", ["D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING"])
def test_a_dispatch_consumes_the_lowest_matching_grant_once(tmp_path, configuration):
    # Kills xǁTrialToolsǁ_transition__mutmut_2..10, dispatch__mutmut_132/159/160/177, and
    # _settle__mutmut_9: every configuration commits the grant transition when it dispatches.
    tools, logged = _granted_tools(tmp_path, configuration)
    tools.dispatch(_send(1))
    assert _consumed(tools) == ["g1"]
    tools.dispatch(_send(2))
    assert _consumed(tools) == ["g1", "g2"]
    dispositions = [p for k, p in logged if k == "tool_dispatch"]
    assert [d["dispatched"] for d in dispositions] == [True, True]
    assert [d["blocked"] for d in dispositions] == [False, False]
    if configuration == "D1_POLICY_GATE":
        # Kills dispatch__mutmut_108/109: an allowed request is recorded as dispatched, not blocked.
        assert [p["gate_action"] for k, p in logged if k == "authorization_decision"] == ["dispatch", "dispatch"]
        observation = tools.dispatch(_send(3))
        assert observation["status"] == "POLICY_BLOCKED"  # no grant left: confirmation_required
        assert observation["reason_category"] == "confirmation_required"
        assert _consumed(tools) == ["g1", "g2"]


@pytest.mark.parametrize("configuration", ["D0_BASELINE", "D1_POLICY_GATE"])
def test_a_resumed_dispatch_recommits_its_grant_and_counts_as_dispatched(tmp_path, configuration):
    # Kills dispatch__mutmut_34..48 and _52: a dispatch replayed from stored events
    # consumes the grant it consumed before and leaves a dispatched prior call, so a
    # later request can't reuse that grant or that budget.
    stored = _stored_send(1)
    tools, logged = _granted_tools(tmp_path, configuration, stored=stored)
    tools.run_tool = lambda *args: pytest.fail("a stored dispatch must not run the tool again")
    tools.dispatch(_send(1))
    assert _consumed(tools) == ["g1"]
    assert [(p.tool, p.dispatched) for p in tools.prior] == [("send_email", True)]
    assert logged == []
