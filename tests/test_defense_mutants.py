"""Defense-contract, datamarking, and conformance-harness checks that mutation
testing found unpinned (reports/cloud/mutation.md). Each test names the
surviving mutants it kills."""

from dataclasses import replace

import pytest

from defenses import interfaces as di
from defenses.datamarking import DatamarkingTransform, mark_html_document, serialize_span
from defenses.interfaces import DATAMARK_MARKER as M
from defenses.interfaces import UntrustedSpan
from oracles.authorization.conformance import _check_single_use


# --- action hash ------------------------------------------------------------


def test_the_action_hash_binds_every_list_element():
    # Kills interfaces.x__plain_json__mutmut_7, which hashed every list element as
    # null: two different actions would then share a grant's action hash.
    a = {"query_id": "orders", "params": {"ids": ["ORD-1", "ORD-2"]}}
    b = {"query_id": "orders", "params": {"ids": ["ORD-3", "ORD-4"]}}
    assert di.action_hash("query_db", a, "1") != di.action_hash("query_db", b, "1")
    frozen = {"query_id": "orders", "params": {"ids": ("ORD-1", "ORD-2")}}
    assert di.action_hash("query_db", frozen, "1") == di.action_hash("query_db", a, "1")
    assert di.action_hash("query_db", a, "1") != di.action_hash(
        "query_db", {"query_id": "orders", "params": {"ids": ["ORD-2", "ORD-1"]}}, "1"
    )


@pytest.mark.parametrize("value", [{"open"}, b"open", object()])
def test_a_non_json_argument_is_refused_by_the_hash_itself(value):
    # Kills x__plain_json__mutmut_9/10/11: the refusal is the hash's own, with its own message.
    with pytest.raises(TypeError, match="^action arguments must be JSON values, not "):
        di.action_hash("query_db", {"query_id": "q", "params": {"x": value}}, "1")
    with pytest.raises(TypeError, match="^action arguments must use string keys$"):
        di.action_hash("query_db", {"query_id": "q", "params": {1: "x"}}, "1")


def test_block_category_refusals_say_why():
    with pytest.raises(ValueError, match="^a blocked request must carry at least one reason code$"):
        di.block_category([])
    with pytest.raises(ValueError, match=r"^unknown reason codes: \['made_up'\]$"):
        di.block_category(["made_up"])


# --- D2_DATAMARKING -----------------------------------------------------------


def test_coverage_counts_every_span_per_channel():
    # Kills datamarking.xǁDatamarkingTransformǁmark__mutmut_33 (`= 1` for `+= 1`).
    spans = [
        UntrustedSpan("a", "C2", "json_string", "x y"),
        UntrustedSpan("b", "C2", "json_string", "p q r"),
        UntrustedSpan("c", "C4", "html_text", "z"),
    ]
    coverage = DatamarkingTransform().mark(spans).coverage
    assert coverage == {"spans_total": 3, "spans_C2": 2, "spans_C3": 0, "spans_C4": 1,
                        "markers_inserted": 3, "preexisting_markers_removed": 0}


def test_mark_refusals_name_the_span_and_value():
    with pytest.raises(ValueError, match="^span 'a' appears twice; mark each span exactly once$"):
        DatamarkingTransform().mark([UntrustedSpan("a", "C2", "text", "x"), UntrustedSpan("a", "C3", "text", "y")])
    with pytest.raises(ValueError, match="^unknown channel: 'C1'$"):
        DatamarkingTransform().mark([UntrustedSpan("a", "C1", "text", "x")])
    with pytest.raises(ValueError, match="^unknown span_format: 'xml'$"):
        DatamarkingTransform().mark([UntrustedSpan("a", "C2", "xml", "x")])


def test_html_comments_and_multiple_attributes_survive_marking():
    # Kills xǁ_HtmlMarkerǁhandle_comment__mutmut_1 (a page with a comment crashed) and
    # xǁ_HtmlMarkerǁ_attrs__mutmut_18 (attributes joined by "XXXX").
    marked, count = mark_html_document('<p class="a b" title="c d">e f<!-- keep me --></p>')
    assert marked == f'<p class="a{M}b" title="c{M}d">e{M}f<!-- keep me --></p>'
    assert count == 3


# --- the conformance harness's single-use replay -----------------------------


def _grants(*consumed):
    return di.GrantState(tuple(di.Grant(f"grant-{i}", "p", "1", "h" * 64, c) for i, c in enumerate(consumed, 1)))


REQUEST = di.CanonicalRequest("v", "golden:test", 1, "send_email", {"to": "a", "subject": "b", "body": "c"}, "t")


class _ConsumesAllOnReplay:
    """Correct on the first grant; on a replay it consumes every unused grant at once."""

    evaluator_version = "consumes-all-test"

    def authorize(self, task_policy, request, prior_calls, grant_state):
        unused = [g.grant_id for g in grant_state.grants if not g.consumed]
        if not unused:
            return di.AuthorizationDecision(False, ("grant_already_consumed",), grant_state, self.evaluator_version)
        take = set(unused) if any(g.consumed for g in grant_state.grants) else {unused[0]}
        grants = tuple(replace(g, consumed=True) if g.grant_id in take else g for g in grant_state.grants)
        return di.AuthorizationDecision(True, (), di.GrantState(grants), self.evaluator_version)


class _WrongCodeWhenExhausted:
    """Uses one grant per replay, but denies an exhausted replay with grant_missing."""

    evaluator_version = "wrong-code-test"

    def authorize(self, task_policy, request, prior_calls, grant_state):
        unused = [g.grant_id for g in grant_state.grants if not g.consumed]
        if not unused:
            return di.AuthorizationDecision(False, ("grant_missing",), grant_state, self.evaluator_version)
        grants = tuple(replace(g, consumed=True) if g.grant_id == unused[0] else g for g in grant_state.grants)
        return di.AuthorizationDecision(True, (), di.GrantState(grants), self.evaluator_version)


def test_the_replay_catches_two_grants_consumed_at_once():
    # Kills conformance.x__check_single_use__mutmut_19 (`or` -> `and`).
    failures = _check_single_use(_ConsumesAllOnReplay(), "v", {}, REQUEST, (), _grants(True, False, False))
    assert failures == ["v: replay consumed more than one grant or changed another grant"]


def test_the_replay_requires_grant_already_consumed_once_every_grant_is_used():
    # Kills conformance.x__check_single_use__mutmut_32 (`or` -> `and`).
    failures = _check_single_use(_WrongCodeWhenExhausted(), "v", {}, REQUEST, (), _grants(True, False))
    assert failures == [
        "v: replay after every matching grant was used was not denied with grant_already_consumed"
    ]


def test_a_correct_replay_passes():
    class _Correct(_WrongCodeWhenExhausted):
        def authorize(self, task_policy, request, prior_calls, grant_state):
            d = super().authorize(task_policy, request, prior_calls, grant_state)
            if d.reason_codes == ("grant_missing",):
                return di.AuthorizationDecision(False, ("grant_already_consumed",), grant_state, "t")
            return d

    assert _check_single_use(_Correct(), "v", {}, REQUEST, (), _grants(True, False, False)) == []


def test_span_serializers_escape_only_what_their_format_needs():
    # Kills the constant mutants on `_SERIALIZERS` (ensure_ascii and quote flipped):
    # D2_DATAMARKING must not change characters beyond the marker and the format's escaping.
    assert serialize_span("text", 'é "q" <a>') == 'é "q" <a>'
    assert serialize_span("json_string", 'é "q"') == '"é \\"q\\""'
    assert serialize_span("html_text", 'é "q" <a> & b') == 'é "q" &lt;a&gt; &amp; b'
    assert serialize_span("html_attribute", 'é "q" <a>') == 'é &quot;q&quot; &lt;a&gt;'
    with pytest.raises(ValueError, match="^unknown span_format: 'xml'$"):
        serialize_span("xml", "x")
