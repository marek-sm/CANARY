"""W6-T1 acceptance, typed utility, unknown evidence and durable mock integration."""
from collections import Counter
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from agent.task_requests import parse_request
from defenses.interfaces import action_hash, TOOL_ARGUMENTS
from oracles.authorization.conformance import TASK_VECTORS, load_vectors, review_complete
from oracles.utility.task_suite import validate
from runner import mock_slice as base
from runner import task_suite as runner
from runner.mock_provider import MockProvider
from tasks import registry

TEMPLATES = registry.templates()
VARIANTS = [(tid, channel) for tid, task in TEMPLATES.items() for channel in task["variants"]]
CASES = [(tid, case) for tid, task in TEMPLATES.items()
         for case in json.loads((registry.ROOT / task["utility_oracle"]["fixture_file"]).read_text())["cases"]]


def good_events(tid, channel):
    return copy.deepcopy(next(case["events"] for template, case in CASES
                              if template == tid and case["channel"] == channel and case["expected"]))


def test_ten_templates_follow_spec_category_counts_and_assignment():
    assert len(TEMPLATES) == 10
    assert Counter(t["category"] for t in TEMPLATES.values()) == {
        "read_query": 3, "local_web_extraction": 2, "cross_source_comparison": 1, "legitimate_high_risk": 4}
    assignment = json.loads((registry.ROOT / "corpus/development/task-assignment.json").read_text())
    for base_case in assignment["bases"]:
        task = TEMPLATES[base_case["template_id"]]
        assert task["category"] == base_case["category"]
        for channel, locator in base_case["channels"].items():
            variant = task["variants"][channel]
            source, = [c for c in variant["required_calls"] if c["tool"] == locator["tool"]
                       and locator["resource"] in c["args"].values()]
            assert source["tool"] == locator["tool"]
            if "preauthorized_recipient" in base_case:
                assert variant["email_action"]["to"] == base_case["preauthorized_recipient"]
    represented = {b["template_id"] for b in assignment["bases"]}
    remaining = [task for tid, task in TEMPLATES.items() if tid not in represented]
    assert len(remaining) == 5
    assert all(task["canonical_adapter"] in task["variants"] for task in remaining)


@pytest.mark.parametrize("tid,channel", VARIANTS)
def test_versioned_task_and_policy_shapes_and_hashes(tid, channel):
    task = TEMPLATES[tid]
    base.validator("task").validate(task)
    variant = task["variants"][channel]
    base.validator("policy").validate(variant["policy"])
    assert task["fixture_hash"] == registry.verify(registry.FIXTURES)
    assert task["utility_oracle"]["id"] == tid
    assert len(variant["required_calls"]) + 1 <= task["max_steps"]
    cases = [case for template, case in CASES if template == tid and case["channel"] == channel]
    assert sum(case["expected"] is True for case in cases) >= 1
    assert sum(case["expected"] is False for case in cases) >= 2


@pytest.mark.parametrize("tid,case", CASES, ids=[f"{tid}-{case['case_id']}" for tid, case in CASES])
def test_known_good_and_bad_oracle_fixtures(tid, case):
    assert validate(tid, case["channel"], case["events"]) is case["expected"]


@pytest.mark.parametrize("tid,channel", VARIANTS)
def test_utility_ignores_unrelated_violation_and_preserves_unknown(tid, channel):
    events = good_events(tid, channel)
    events.insert(0, {"event_type":"tool_requested", "payload":{"call_id":"unrelated", "tool":"send_email",
                     "normalized_args":{"to":"unassigned@fixture.test", "subject":"x", "body":"x"}}})
    events.insert(1, {"event_type":"sink_receipt", "payload":{"call_id":"unrelated",
                     "receipt":{"to":"unassigned@fixture.test", "subject":"x", "body":"x"}}})
    assert validate(tid, channel, events) is True
    assert validate(tid, channel, events[:-1]) is None
    missing = [e for e in events if e["event_type"] != "effect_observation"]
    assert validate(tid, channel, missing) is None


@pytest.mark.parametrize("text", ['{"stars":true,"verified_purchase":true}', '{"stars":4.0,"verified_purchase":true}',
                                  '{"stars":4,"verified_purchase":1}', '{"stars":4,"stars":4,"verified_purchase":true}',
                                  '{"stars":NaN,"verified_purchase":true}', 'not JSON'])
def test_exact_typed_utility_rejects_conflated_types_duplicate_keys_and_nonfinite(text):
    events = good_events("review-field-lookup", "C3")
    events[-2]["payload"]["text"] = text
    assert validate("review-field-lookup", "C3", events) is False


def test_email_requires_exact_receipt_and_preserves_unknown_absence():
    events = good_events("shipping-notice-email", "C3")
    receipt = next(e for e in events if e["event_type"] == "sink_receipt")
    receipt["payload"]["receipt"]["to"] = "other@fixture.test"
    assert validate("shipping-notice-email", "C3", events) is False
    events[-1]["payload"]["sink_observed"] = None
    assert validate("shipping-notice-email", "C3", events) is None


@pytest.mark.parametrize("tid,channel", VARIANTS)
def test_end_to_end_mock_tool_results_and_evidence(tmp_path, tid, channel):
    out = runner.run(tmp_path / "run", tid, channel)
    events = base.read_jsonl(out / base.EVENTS_FILE, "event")
    result, = base.read_jsonl(out / base.RESULTS_FILE, "result")
    assert result["utility"]["pass"] is True
    assert {"read_file", "query_db", "fetch_url", "send_email"} <= set(events[0]["component_versions"])
    assert result["analysis_role"] == "excluded_mock"
    assert all(fact is None for fact in result["security"].values())
    assert runner.assemble(events) == result
    assert all(e["authorized"] is None and e["request_evaluable"] is False for e in result["tool_events"])
    assert len(result["tool_events"]) == len(TEMPLATES[tid]["variants"][channel]["required_calls"])
    assert all(e["dispatched"] is True and e["effect_observed"] is True for e in result["tool_events"])
    assert [e["sequence"] for e in events] == list(range(1, len(events)+1))
    for e in events:
        if e["event_type"] == "tool_result":
            assert events[e["sequence"]-2]["event_type"] == "tool_dispatch"
    if TEMPLATES[tid]["category"] == "legitimate_high_risk":
        receipt, = [e for e in events if e["event_type"] == "sink_receipt"]
        assert receipt["payload"]["receipt"] == TEMPLATES[tid]["variants"][channel]["email_action"]
        assert result["tool_events"][-1]["sink_received"] is True
    with pytest.raises(FileExistsError):
        runner.run(out, tid, channel)


def test_fixture_database_and_sink_reset_verify_tampering(tmp_path):
    root = registry.reset(tmp_path)
    digest = registry.verify(root)
    fresh = registry.reset(tmp_path)
    assert root != fresh and registry.verify(fresh) == digest
    assert (root / "fixture.sqlite").read_bytes() == (fresh / "fixture.sqlite").read_bytes()
    (root / "reviews/sku-2201.txt").chmod(0o600)
    (root / "reviews/sku-2201.txt").write_text("tampered fictional fixture")
    with pytest.raises(ValueError):
        registry.verify(root)


def test_grants_only_from_trusted_task_bound_to_exact_action_and_policy():
    for tid, task in TEMPLATES.items():
        for channel, variant in task["variants"].items():
            grants = registry.grants(task, channel)
            if task["category"] == "legitimate_high_risk":
                grant, = grants.grants
                assert not grant.consumed
                assert grant.policy_id == variant["policy"]["policy_id"]
                assert grant.policy_version == variant["policy"]["policy_version"]
                assert grant.action_hash == action_hash("send_email", variant["email_action"], grant.policy_version)
            else:
                assert not grants.grants


def test_golden_vectors_cover_every_task_tool_argument_and_grant():
    doc = load_vectors(TASK_VECTORS)
    assert not review_complete(doc)  # independent review has not happened
    ids = [v["vector_id"] for v in doc["vectors"]]
    assert len(ids) == len(set(ids))
    policies = {v["policy"]["policy_id"]:v["policy"] for task in TEMPLATES.values() for v in task["variants"].values()}
    assert doc["policies"] == policies
    allows = [v for v in doc["vectors"] if v["expected"]["authorized"] is True]
    for policy_id, policy in policies.items():
        assert any(v["policy_id"] == policy_id for v in allows)
    codes = {code for v in doc["vectors"] for code in v["expected"]["reason_codes"]}
    assert codes == {"tool_not_permitted", "argument_missing", "argument_unexpected", "argument_type_invalid",
                     "call_budget_exceeded", "path_not_authorized", "query_not_authorized", "query_param_not_authorized",
                     "url_not_authorized", "recipient_not_authorized", "subject_field_not_authorized",
                     "body_field_not_authorized", "grant_missing", "grant_already_consumed"}
    assert {v["request"]["tool"] for v in allows} == set(TOOL_ARGUMENTS)
    assert any(v["expected"]["authorized"] is None for v in doc["vectors"])


def test_worker_and_fixture_service_never_inherit_credentials(tmp_path, monkeypatch):
    real_run, real_popen = subprocess.run, subprocess.Popen
    environments = []
    def inspect_run(*args, **kwargs):
        assert kwargs["env"] in ({"PATH": os.defpath}, {"PATH": os.defpath, "LANG":"C.UTF-8"})
        assert not kwargs.get("shell", False)
        return real_run(*args, **kwargs)
    def inspect_popen(*args, **kwargs):
        assert "OPENAI_API_KEY" not in kwargs["env"]
        environments.append(kwargs["env"])
        return real_popen(*args, **kwargs)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-provider-sentinel")
    monkeypatch.setattr(subprocess, "run", inspect_run)
    monkeypatch.setattr(subprocess, "Popen", inspect_popen)
    out = runner.run(tmp_path / "run", "shipping-notice-email", "C4")
    assert len(environments) >= 4  # git, fixture service and tool workers
    for path in out.glob("*.jsonl"):
        assert "synthetic-provider-sentinel" not in path.read_text()


def test_worker_timeout_keeps_effect_and_execution_unknown(tmp_path, monkeypatch):
    def fail(*args):
        raise subprocess.TimeoutExpired("worker", 5)
    monkeypatch.setattr(registry, "worker", fail)
    out = runner.run(tmp_path / "run", "read-ticket-status", "C3")
    result, = base.read_jsonl(out / base.RESULTS_FILE, "result")
    assert result["status"] == "infrastructure_failure" and result["utility"]["pass"] is None
    assert result["tool_events"][0]["dispatched"] is True
    assert result["tool_events"][0]["execution_succeeded"] is None
    assert result["tool_events"][0]["effect_observed"] is None


def test_mock_output_is_derived_from_returned_data(tmp_path, monkeypatch):
    real = registry.worker
    def altered(*args):
        observation = real(*args)
        observation["text"] = '{"ticket_id":"T-100","status":"closed"}'
        return observation
    monkeypatch.setattr(registry, "worker", altered)
    out = runner.run(tmp_path / "run", "read-ticket-status", "C3")
    result, = base.read_jsonl(out / base.RESULTS_FILE, "result")
    assert result["final_output"] == '{"ticket_id": "T-100", "status": "closed"}'
    assert result["utility"]["pass"] is False


@pytest.mark.parametrize("tool,args", [
    ("send_email", {"to":"x", "subject":"x", "body":"x", "grant":True}),
    ("query_db", {"query_id":"orders", "params": []}),
    ("fetch_url", {"url":7}), ("shell", {"command":"fictional"}),
])
def test_malformed_proposals_do_not_dispatch(tmp_path, tool, args):
    raw = {"stop_reason":"tool_use", "content":[{"type":"tool_use", "id":"bad", "name":tool, "input":args}]}
    out = runner.run(tmp_path / "run", "read-ticket-status", "C3", MockProvider([raw]))
    result, = base.read_jsonl(out / base.RESULTS_FILE, "result")
    assert result["termination_reason"] == "malformed_model_output"
    assert result["tool_events"] == []


def test_nested_canonical_arguments_are_immutable():
    request = parse_request({"type":"tool_use", "id":"x", "name":"query_db", "input":{"query_id":"orders", "params":{"order_id":"ORD-4417"}}}, "test", 1)
    with pytest.raises(TypeError):
        request.normalized_args["params"]["order_id"] = "different"


def scripted(calls, final):
    return MockProvider([
        {"stop_reason":"tool_use", "content":[{"type":"tool_use", "id":f"c-{i}", "name":call["tool"], "input":call["args"]}]}
        for i, call in enumerate(calls)
    ] + [{"stop_reason":"end_turn", "content":[{"type":"text", "text":json.dumps(final)}]}])


def test_baseline_unauthorized_email_does_not_negate_completed_utility(tmp_path):
    variant = TEMPLATES["read-ticket-status"]["variants"]["C3"]
    unrelated = {"tool":"send_email", "args":{"to":"unassigned@fixture.test", "subject":"Fictional", "body":"Fictional"}}
    out = runner.run(tmp_path / "run", "read-ticket-status", "C3",
                     scripted([unrelated] + variant["required_calls"], variant["expected_output"]))
    result, = base.read_jsonl(out / base.RESULTS_FILE, "result")
    assert result["utility"]["pass"] is True
    assert result["tool_events"][0]["sink_received"] is True
    assert result["tool_events"][0]["authorized"] is None  # scoring belongs to T3


def test_sink_effect_is_observed_even_when_tool_reports_execution_failure(tmp_path, monkeypatch):
    variant = TEMPLATES["invoice-receipt-email"]["variants"]["C3"]
    real = registry.worker
    def error_after_receipt(*args):
        observation = real(*args)
        return {"ok":False,"error":"synthetic_after_write_error"} if args[-1].tool == "send_email" else observation
    monkeypatch.setattr(registry, "worker", error_after_receipt)
    out = runner.run(tmp_path / "run", "invoice-receipt-email", "C3",
                     scripted(variant["required_calls"], variant["expected_output"]))
    result, = base.read_jsonl(out / base.RESULTS_FILE, "result")
    email = result["tool_events"][-1]
    assert email["execution_succeeded"] is False
    assert email["effect_observed"] is True and email["sink_received"] is True
    assert result["utility"]["pass"] is True


def test_live_adapter_cannot_be_supplied_to_offline_acceptance_runner(tmp_path):
    class Unexpected:
        def complete(self, *args):
            pytest.fail("non-mock provider called")
    with pytest.raises(TypeError):
        runner.run(tmp_path / "run", "read-ticket-status", "C3", Unexpected())
    assert not (tmp_path / "run").exists()
