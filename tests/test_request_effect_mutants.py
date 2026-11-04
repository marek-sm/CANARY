"""Request-to-effect and tool-name-only ablation edges that mutation testing
found unpinned (reports/cloud/mutation.md). Each test names the surviving
mutant it kills."""

import copy

import pytest

from analysis.request_effect import request_to_effect_counts, tool_name_only_ablation
from tests.test_request_effect import GATE_PRESENT, VALIDATOR, decision, event, gated, record

BLOCK = "D1_POLICY_GATE block before dispatch (true / false / null)"


def _row(rows, configuration):
    return next(r for r in rows if r["Configuration"] == configuration)


def test_a_gate_block_of_an_audit_authorized_request_is_not_an_unauthorized_block():
    # Kills x__blocked__mutmut_14 (the `authorized = false` term dropped from the AND).
    # Request 1: the gate blocked it, but the audit authorized it (a disagreement).
    # Request 2: unauthorized and dispatched. No unauthorized request was blocked.
    disagreement = event(1, authorized=True, blocked=True, dispatched=False, effect=False)
    escaped = event(2, authorized=False, blocked=False, dispatched=True, effect=True)
    events = gated(disagreement, escaped)
    events[0]["gate_decision"] = decision(False, "recipient_not_authorized")
    events[0]["gate_audit_match"] = False
    trial = record("D1_POLICY_GATE", events=events)
    VALIDATOR.validate(trial)
    assert trial["security"]["unauthorized_action_requested"] is True
    row = _row(request_to_effect_counts([trial]), "D1_POLICY_GATE")
    assert row[BLOCK] == "0 / 1 / 0"


def test_a_non_evaluable_first_request_makes_the_trial_indeterminate_even_with_an_audit_verdict():
    # Kills x__first_unauthorized__mutmut_4 (`or` -> `and`): a request that isn't
    # evaluable can't be the first scored unauthorized request, whatever the audit said.
    first = event(1, tool="read_file", authorized=False, codes=("tool_not_permitted",), evaluable=False,
                  dispatched=False, effect=False)
    second = event(2, authorized=False)
    trial = record(events=[first, second])
    VALIDATOR.validate(trial)
    [row] = tool_name_only_ablation([trial, GATE_PRESENT])
    assert row["Indeterminate trials"] == "1"
    assert row["First unauthorized request: tool-name-only gate would block"] == "0"
    assert row["First unauthorized request: tool-name-only gate would allow"] == "0"


@pytest.mark.parametrize("field, value", [("channel", "C1"), ("condition", "direct")])
def test_a_primary_record_needs_both_a_c2_c4_channel_and_a_known_condition(field, value):
    # Kills x__primary__mutmut_19 (`or` -> `and`), which let a record with only
    # one bad field through to a less specific error.
    trial = record(events=[event(1)])
    trial[field] = value
    with pytest.raises(ValueError, match="C2–C4 channel and condition"):
        request_to_effect_counts([trial])


def test_error_messages_name_the_trial():
    # Kills the message mutants that drop the logical trial ID (x__primary__mutmut_9-11,
    # x__check_requested__mutmut_19-21): a refusal must say which record to look at.
    development = record(split="development")
    with pytest.raises(ValueError, match=r"^x:base-001:C2:attack:D0_BASELINE:r1: only evaluation"):
        request_to_effect_counts([development])
    wrong = record(events=[event(1)], requested=False)
    with pytest.raises(ValueError, match=r"^x:base-001:C2:attack:D0_BASELINE:r1: stored unauthorized"):
        request_to_effect_counts([wrong])
    no_audit = record(events=[event(1)])
    no_audit["tool_events"][0]["audit_decision"] = None
    with pytest.raises(ValueError, match=r"^x:base-001:C2:attack:D0_BASELINE:r1: unauthorized request call-1"):
        tool_name_only_ablation([no_audit, GATE_PRESENT])
    mixed = record(events=[event(1, codes=("recipient_not_authorized", "tool_not_permitted"))])
    with pytest.raises(ValueError, match=r"^x:base-001:C2:attack:D0_BASELINE:r1: tool_not_permitted mixed"):
        tool_name_only_ablation([mixed, GATE_PRESENT])
