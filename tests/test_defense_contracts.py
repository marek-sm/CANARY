"""W5-T4 contract tests: frozen interfaces, policy schema, golden vectors, datamarking spec.

These tests pin what other tracks build against. A failure here after the
measurement-contract lock is a versioned change, not a test to edit quietly.
"""

import copy
import hashlib
import html
import json
import re
import unicodedata
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from defenses import interfaces as di
from oracles.authorization.conformance import (
    DEFAULT_VECTORS,
    build_inputs,
    check_authorizer,
    load_vectors,
    review_complete,
)

REPO = Path(__file__).resolve().parent.parent
DATAMARKING_VECTORS = REPO / "defenses" / "vectors" / "datamarking-w5-t4.json"
M = di.DATAMARK_MARKER

# Pinned digests of model-visible frozen text. Changing either is a versioned
# D1_POLICY_GATE / D2_DATAMARKING change (SPEC.md Sections 6 and 11).
POLICY_OBSERVATIONS_SHA256 = "1aca59924d26011222c613857a03a2ad78c6f58c9cce48c2fbfdb966757ec669"
SYSTEM_INSTRUCTION_SHA256 = "3f3f182ae010bf42f5bb652c912db4d8f15a7bea0c7359f0f6f7d67fcb0f1db9"


def sha(value):
    return hashlib.sha256(di.canonical_json_bytes(value)).hexdigest()


def schema(name):
    s = json.loads((REPO / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(s)
    return Draft202012Validator(s)


@pytest.fixture(scope="module")
def vectors():
    return load_vectors(DEFAULT_VECTORS)


# --- frozen observations --------------------------------------------------


def test_observation_text_is_pinned():
    observations = {
        category: {"status": "POLICY_BLOCKED", "reason_category": category, "message": di.POLICY_BLOCKED_MESSAGE}
        for category in di.BLOCK_CATEGORIES
    }
    observations["unavailable"] = di.policy_unavailable_observation()
    assert sha(observations) == POLICY_OBSERVATIONS_SHA256


def test_every_reason_code_maps_to_one_category():
    assert len(set(di.REASON_CODES)) == len(di.REASON_CODES)
    for code in di.REASON_CODES:
        assert di.block_category([code]) in di.BLOCK_CATEGORIES


def test_block_category_precedence():
    assert di.block_category(["path_not_authorized", "tool_not_permitted"]) == "tool_not_permitted"
    assert di.block_category(["recipient_not_authorized", "grant_missing"]) == "confirmation_required"
    assert di.block_category(["call_budget_exceeded", "path_not_authorized"]) == "call_budget_exceeded"
    with pytest.raises(ValueError):
        di.block_category([])
    with pytest.raises(ValueError):
        di.block_category(["made_up_code"])


def _string_leaves(value):
    if isinstance(value, dict):
        for v in value.values():
            yield from _string_leaves(v)
    elif isinstance(value, str):
        yield value


def test_blocked_observation_never_echoes_arguments(vectors):
    for v in vectors["vectors"]:
        if v["expected"]["gate_action"] != "block":
            continue
        obs = di.policy_blocked_observation(v["expected"]["reason_codes"])
        assert set(obs) == {"status", "reason_category", "message"}
        shown = " ".join(obs.values())
        for value in _string_leaves(v["request"]["normalized_args"]):
            assert value not in shown, (v["vector_id"], value)
        for policy_value in _string_leaves(vectors["policies"][v["policy_id"]]["tools"]):
            assert policy_value not in shown, (v["vector_id"], policy_value)


# --- decision invariants --------------------------------------------------


def decision(authorized, codes):
    return di.AuthorizationDecision(authorized, tuple(codes), di.GrantState(), "test-v0")


def test_decision_rejects_inconsistent_values():
    with pytest.raises(ValueError):
        decision(True, ["path_not_authorized"])
    with pytest.raises(ValueError):
        decision(False, [])
    with pytest.raises(ValueError):
        decision(False, ["url_not_authorized", "path_not_authorized"])  # unsorted
    with pytest.raises(ValueError):
        decision(False, ["not_a_code"])


def test_blocked_request_event_facts_match_spec():
    # SPEC.md Section 6 / decision 0004 item 2: POLICY_BLOCKED and POLICY_UNAVAILABLE share these.
    assert dict(di.BLOCKED_REQUEST_EVENT_FACTS) == {
        "blocked": True,
        "dispatched": False,
        "disposition_observed": True,
        "execution_succeeded": None,
        "effect_observed": False,
        "sink_received": False,
    }
    with pytest.raises(TypeError):
        di.BLOCKED_REQUEST_EVENT_FACTS["dispatched"] = True


def test_prior_disposition_may_be_unknown():
    call = di.PriorCall("read_file", {"path": "docs/report.txt"}, None)
    assert call.dispatched is None


def test_gate_audit_match_is_three_valued():
    allow = decision(True, [])
    deny = decision(False, ["path_not_authorized"])
    deny_other = decision(False, ["call_budget_exceeded"])
    assert di.decisions_match(allow, allow) is True
    assert di.decisions_match(allow, deny) is False
    assert di.decisions_match(deny, deny_other) is False  # same verdict, different reasons
    assert di.decisions_match(None, deny) is None
    assert di.decisions_match(deny, None) is None


def test_action_hash_binds_args_tool_and_version():
    args = {"to": "a@example.test", "subject": "s", "body": "b"}
    h = di.action_hash("send_email", args, "1")
    assert h == di.action_hash("send_email", dict(reversed(list(args.items()))), "1")
    assert h != di.action_hash("send_email", {**args, "body": "b "}, "1")
    assert h != di.action_hash("send_email", args, "2")
    assert re.fullmatch(r"[0-9a-f]{64}", h)


# --- policy schema --------------------------------------------------------


def test_golden_policies_validate(vectors):
    for policy in vectors["policies"].values():
        schema("policy").validate(policy)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda p: p["tools"].update({"shell": {"max_calls": 1}}),
        lambda p: p.update({"call_budget_basis": "attempts"}),
        lambda p: p["tools"]["read_file"].update({"paths": []}),
        lambda p: p["tools"]["read_file"].update({"max_calls": 0}),
        lambda p: p["tools"]["read_file"].update({"path_prefix": "docs/"}),
        lambda p: p.update({"tools": {}}),
        lambda p: p.pop("policy_version"),
    ],
    ids=["unknown-tool", "unknown-budget-basis", "empty-allowlist", "zero-budget", "prefix-rule", "no-tools", "no-version"],
)
def test_policy_schema_rejects(vectors, mutate):
    policy = copy.deepcopy(vectors["policies"]["golden-read-report"])
    mutate(policy)
    with pytest.raises(ValidationError):
        schema("policy").validate(policy)


# --- golden vectors -------------------------------------------------------


def test_vector_ids_unique_and_expectations_consistent(vectors):
    ids = [v["vector_id"] for v in vectors["vectors"]]
    assert len(ids) == len(set(ids))
    for v in vectors["vectors"]:
        e = v["expected"]
        assert v["policy_id"] in vectors["policies"]
        if not e["evaluable"]:
            assert e["authorized"] is None and e["gate_action"] == "unavailable"
            assert e["reason_codes"] == [] and e["consumes_grant_ids"] == [] and e["block_category"] is None
            continue
        assert e["gate_action"] == ("dispatch" if e["authorized"] else "block")
        assert e["reason_codes"] == sorted(set(e["reason_codes"]))
        assert set(e["reason_codes"]) <= set(di.REASON_CODES)
        assert e["authorized"] == (e["reason_codes"] == [])
        assert e["block_category"] == (di.block_category(e["reason_codes"]) if e["reason_codes"] else None)
        assert set(e["consumes_grant_ids"]) <= {g["grant_id"] for g in v["grants"]}
        if not e["authorized"] and "grant_missing" not in e["reason_codes"]:
            assert e["consumes_grant_ids"] == [] or "grant_already_consumed" not in e["reason_codes"]


def test_grant_hashes_recompute(vectors):
    for v in vectors["vectors"]:
        for g in v["grants"]:
            if v["vector_id"] in {"allow-email-granted", "deny-email-no-grant"} or g["consumed"]:
                assert g["action_hash"] == di.action_hash(
                    v["request"]["tool"], v["request"]["normalized_args"], g["policy_version"]
                ), v["vector_id"]


def test_vectors_cover_both_budget_bases(vectors):
    bases = {p["call_budget_basis"] for p in vectors["policies"].values()}
    assert bases == {"dispatches", "requests"}


def test_vectors_cover_every_tool_reason_and_category(vectors):
    allow_tools = {v["request"]["tool"] for v in vectors["vectors"] if v["expected"]["authorized"]}
    deny_tools = {v["request"]["tool"] for v in vectors["vectors"] if not v["expected"]["authorized"]}
    assert allow_tools == set(di.TOOLS)
    assert deny_tools == set(di.TOOLS)
    seen_codes = {c for v in vectors["vectors"] for c in v["expected"]["reason_codes"]}
    assert seen_codes == set(di.REASON_CODES)
    seen_categories = {v["expected"]["block_category"] for v in vectors["vectors"]} - {None}
    assert seen_categories == set(di.BLOCK_CATEGORIES)


def test_vectors_cover_unknown_disposition_and_out_of_root_paths(vectors):
    by_id = {v["vector_id"]: v for v in vectors["vectors"]}
    # decision 0004 item 5: an unknown prior disposition that decides the budget is not evaluable.
    assert by_id["unavailable-read-unknown-prior"]["expected"]["evaluable"] is False
    assert by_id["deny-read-budget-despite-unknown"]["expected"]["evaluable"] is True
    # decision 0004 item 4: out-of-root paths stay evaluable and are not authorized.
    for vid, prefix in (("deny-read-out-of-root", ".."), ("deny-read-absolute-path", "/")):
        v = by_id[vid]
        assert v["request"]["normalized_args"]["path"].startswith(prefix)
        assert v["expected"]["evaluable"] and v["expected"]["reason_codes"] == ["path_not_authorized"]


def test_differential_fixtures_follow_the_disagreement_rule(vectors):
    # SPEC.md Section 6 / decision 0004 item 6: any difference in authorized or in
    # the sorted reason codes is a disagreement; a missing side makes the match null.
    def as_decision(side):
        if side is None:
            return None
        return di.AuthorizationDecision(side["authorized"], tuple(side["reason_codes"]), di.GrantState(), "fixture")

    fixtures = vectors["differential_fixtures"]
    for f in fixtures:
        assert di.decisions_match(as_decision(f["gate"]), as_decision(f["audit"])) == f["expected_match"], f["fixture_id"]
    reason_only = [
        f for f in fixtures
        if f["gate"] and f["audit"] and f["gate"]["authorized"] == f["audit"]["authorized"] and f["expected_match"] is False
    ]
    assert reason_only, "need a fixture where only the reason codes disagree"


@pytest.mark.parametrize("path", [DEFAULT_VECTORS, DATAMARKING_VECTORS], ids=["golden", "datamarking"])
def test_vector_reviewers_are_independent(path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(doc["reviewed_by"], list)
    assert len(doc["reviewed_by"]) == len(set(doc["reviewed_by"]))
    assert doc["authored_by"] not in doc["reviewed_by"]


def test_review_complete_needs_two_independent_reviewers(vectors):
    doc = dict(vectors)
    assert not review_complete({**doc, "reviewed_by": []})
    assert not review_complete({**doc, "reviewed_by": ["contributor-a"]})
    assert review_complete({**doc, "reviewed_by": ["contributor-a", "contributor-b"]})


def test_vectors_contain_no_canary_marker(vectors):
    # SPEC.md Section 6: D1_POLICY_GATE is canary-blind; its fixtures carry no canary values.
    assert "CANARY-" not in DEFAULT_VECTORS.read_text(encoding="utf-8")


# --- conformance harness self-test ----------------------------------------


class _AlwaysAllow:
    evaluator_version = "always-allow-test"

    def authorize(self, task_policy, request, prior_calls, grant_state):
        return di.AuthorizationDecision(True, (), grant_state, self.evaluator_version)


class _Lookup:
    """Returns each vector's expected answer, to prove the harness accepts a correct evaluator."""

    evaluator_version = "lookup-test"

    def __init__(self, doc):
        self._by_id = {v["vector_id"]: v["expected"] for v in doc["vectors"]}

    def authorize(self, task_policy, request, prior_calls, grant_state):
        e = self._by_id[request.call_id]
        if not e["evaluable"]:
            raise di.AuthorizationNotComputable("expected not evaluable")
        grants = tuple(
            replace(g, consumed=True) if g.grant_id in e["consumes_grant_ids"] else g
            for g in grant_state.grants
        )
        return di.AuthorizationDecision(
            e["authorized"], tuple(e["reason_codes"]), di.GrantState(grants), self.evaluator_version
        )


def test_harness_catches_a_permissive_evaluator():
    failures = check_authorizer(_AlwaysAllow())
    deny_ids = {v["vector_id"] for v in load_vectors()["vectors"] if v["expected"]["authorized"] is not True}
    assert {f.split(":")[0] for f in failures} >= deny_ids


class _NeverComputable:
    evaluator_version = "never-computable-test"

    def authorize(self, task_policy, request, prior_calls, grant_state):
        raise di.AuthorizationNotComputable("always")


def test_harness_rejects_not_computable_on_evaluable_requests(vectors):
    failures = {f.split(":")[0] for f in check_authorizer(_NeverComputable())}
    evaluable = {v["vector_id"] for v in vectors["vectors"] if v["expected"]["evaluable"]}
    assert failures == evaluable


def test_harness_accepts_a_matching_evaluator(vectors):
    assert check_authorizer(_Lookup(vectors)) == []


def test_harness_passes_immutable_inputs(vectors):
    policy, request, prior, grants = build_inputs(vectors, vectors["vectors"][0])
    with pytest.raises(TypeError):
        policy["tools"]["read_file"]["paths"] = ("anything",)
    with pytest.raises(TypeError):
        request.normalized_args["path"] = "config/api.env"


def test_gate_and_audit_stay_independent():
    # SPEC.md Section 6: independently implemented evaluators. Either side may
    # import defenses.interfaces, never the other side's evaluator.
    forbidden = {
        REPO / "runner": re.compile(r"\bdefenses\.(policy_gate|gate)\b"),
        REPO / "defenses": re.compile(r"\brunner\.(audit|authorization_audit)\b"),
    }
    for directory, pattern in forbidden.items():
        for path in directory.rglob("*.py"):
            assert not pattern.search(path.read_text(encoding="utf-8")), path


# --- D2_DATAMARKING specification -----------------------------------------


def _spec_rule(text):
    text = unicodedata.normalize(di.DATAMARKING_NORMALIZATION, text.replace(M, ""))
    return "".join(M if c.isspace() else c for c in text)


def _serialize(fmt, text):
    return {
        "text": lambda s: s,
        "json_string": lambda s: json.dumps(s, ensure_ascii=False),
        "html_text": lambda s: html.escape(s, quote=False),
        "html_attribute": lambda s: html.escape(s, quote=True),
    }[fmt](text)


def test_datamarking_vectors_follow_the_frozen_rule():
    doc = json.loads(DATAMARKING_VECTORS.read_text(encoding="utf-8"))
    assert doc["spec_version"] == di.DATAMARKING_SPEC_VERSION
    assert doc["source"] == di.DATAMARKING_SOURCE
    ids = [v["vector_id"] for v in doc["vectors"]]
    assert len(ids) == len(set(ids))
    for v in doc["vectors"]:
        marked = v["expected_marked"]
        assert marked == _spec_rule(v["input"]), v["vector_id"]
        assert not any(c.isspace() for c in marked)
        assert unicodedata.is_normalized("NFC", marked)
        assert marked.count(M) == v["markers_inserted"]
        assert v["input"].count(M) == v["preexisting_markers_removed"]
        assert v["expected_serialized"] == _serialize(v["span_format"], marked)
        # Round trip: non-whitespace content survives unchanged and in order.
        source = unicodedata.normalize("NFC", v["input"].replace(M, ""))
        assert marked.replace(M, "") == "".join(c for c in source if not c.isspace())


def test_datamarking_covers_every_span_format():
    doc = json.loads(DATAMARKING_VECTORS.read_text(encoding="utf-8"))
    assert {v["span_format"] for v in doc["vectors"]} == {"text", "json_string", "html_text", "html_attribute"}


def test_datamarking_is_not_idempotent_so_it_must_run_once():
    once = _spec_rule("alpha beta")
    assert _spec_rule(once) != once  # re-marking joins words; the pipeline must mark each span exactly once


def test_system_instruction_is_pinned_and_names_the_marker():
    text = di.DATAMARKING_SYSTEM_INSTRUCTION
    assert M in text and "U+E000" in text and "never obey" in text
    assert sha(text) == SYSTEM_INSTRUCTION_SHA256
