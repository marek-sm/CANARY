"""Offline W6-T1 tool/task acceptance runner; no live provider CLI."""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import subprocess
import uuid

from agent.loop import run_loop
from agent.task_requests import parse_request, VERSION as PARSER_VERSION
from oracles.utility.task_suite import validate, VERSION as UTILITY_VERSION
from runner import mock_slice as base
from runner.mock_provider import MockProvider, MOCK_MODEL_ID, PROVIDER_ADAPTER_VERSION
from tasks import registry
from tools.read_file import VERSION as READ_VERSION
from tools.query_db import VERSION as QUERY_VERSION
from tools.fetch_url import VERSION as FETCH_VERSION
from tools.send_email import SINK_NAME, VERSION as EMAIL_VERSION
from tools.local_fs import read_bytes

VERSION = "task-suite-runner-v0.2.0"


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


class TaskProvider(MockProvider):
    """Task-aware no-credit mock; output is computed from actual tool observations."""
    def __init__(self, template, channel):
        super().__init__([])
        self.template = template
        self.variant = template["variants"][channel]
        self.records = []
        self.sent = False

    def complete(self, messages, tool_schemas, decoding, model_request):
        required = self.variant["required_calls"]
        if self.calls:
            previous = required[self.calls - 1]
            observation = messages[-1]["content"][0]["content"]
            if observation["ok"]:
                if previous["tool"] == "send_email":
                    self.sent = True
                elif "rows" in observation:
                    self.records.extend(json.loads(row["content"]) for row in observation["rows"])
                else:
                    text = observation["text"]
                    if text.startswith("<"):
                        parser = Text()
                        parser.feed(text)
                        text = "".join(parser.parts)
                    self.records.append(json.loads(text))
        if self.calls < len(required):
            call = required[self.calls]
            args = dict(call["args"])
            # Email bodies come from the retrieved record, not expected output.
            if call["tool"] == "send_email" and self.records:
                tid = self.template["template_id"]
                key, label = {
                    "shipping-notice-email": ("tracking_id", "Tracking ID"),
                    "meeting-confirm-email": ("date", "Meeting date"),
                    "invoice-receipt-email": ("amount_cents", "Amount cents"),
                    "maintenance-confirm-email": ("date", "Maintenance date"),
                }[tid]
                args["body"] = f"{label}: {self.records[0][key]}"
            raw = {"stop_reason": "tool_use", "content": [{"type": "tool_use", "id": f"task-{self.calls}",
                   "name": call["tool"], "input": args}]}
        else:
            tid = self.template["template_id"]
            if self.template["category"] == "legitimate_high_risk":
                output = {"sent": self.sent}
            elif tid == "open-ticket-ids":
                output = {"ticket_ids": sorted(row["ticket_id"] for row in self.records)}
            elif tid == "supplier-quote-compare" and len(self.records) == 2:
                supplier, internal = self.records
                source = "supplier" if supplier["unit_price_cents"] < internal["unit_price_cents"] else "internal"
                output = {"lower_price_cents": min(supplier["unit_price_cents"], internal["unit_price_cents"]), "source": source}
            elif self.records:
                output = {key: self.records[0][key] for key in self.variant["expected_output"]}
            else:
                output = {}
            raw = {"stop_reason": "end_turn", "content": [{"type": "text", "text": json.dumps(output)}]}
        self._script.append(raw)
        return super().complete(messages, tool_schemas, decoding, model_request)


def sink_receipts(state):
    return [json.loads(line) for line in read_bytes(state, SINK_NAME, 1024 * 1024).decode("utf-8").splitlines()]


def assemble(events):
    result = base.assemble_result(events)
    start = events[0]
    metadata = start["payload"]
    tid, channel = metadata["template_id"], metadata["task_channel"]
    result.update(experiment_id=start["experiment_id"], logical_trial_id=start["logical_trial_id"],
                  base_case_id=tid, case_id=f"{tid}:{channel}:clean", channel=channel, condition="clean",
                  analysis_role="excluded_mock", measurement_limitation="Offline task acceptance; independent authorization audit not yet integrated")
    result["run_metadata"].update(rendered_fixture_hash=metadata["fixture_hash"],
                                  task_policy_hash=metadata["policy_hash"], utility_oracle_hash=metadata["utility_hash"])
    result["utility"] = {"oracle_id": tid, "oracle_version": UTILITY_VERSION,
                         "pass": validate(tid, channel, events), "reason_codes": ["deterministic_task_evidence"]}
    ended = next(e for e in events if e["event_type"] == "trial_ended")
    for event in events:
        if event["event_type"] != "tool_requested":
            continue
        request = dict(event["payload"])
        related = [e for e in events if e["payload"].get("call_id") == request["call_id"]]
        returned = next((e["payload"] for e in related if e["event_type"] == "tool_result"), None)
        effect = next((e["payload"] for e in related if e["event_type"] == "effect_observation"), None)
        dispatched = any(e["event_type"] == "tool_dispatch" for e in related)
        # Only the refused step's durable end proves no dispatch/effect. Earlier
        # missing evidence remains unknown (SPEC.md Section 9, decision 0008).
        filtered = (not dispatched and ended["payload"]["termination_reason"] == "provider_content_filter"
                    and request["step"] == ended["payload"]["steps_used"])
        request.update(request_evaluable=False, authorized=None, gate_decision=None, audit_decision=None,
                       gate_audit_match=None, blocked=False, dispatched=True if dispatched else (False if filtered else None),
                       disposition_observed=None,
                       execution_succeeded=returned["observation"]["ok"] if returned else None,
                       effect_observed=effect["effect_observed"] if effect else (False if filtered else None),
                       effect_oracle_id=("fake-sink-append-v0.1.0" if request["tool"] == "send_email"
                                         else f"{request['tool']}-returned-v0.1.0"),
                       sink_received=(effect.get("sink_received") if effect else (False if filtered else None))
                                     if request["tool"] == "send_email" else False,
                       evidence_refs=[e["event_id"] for e in related] + ([ended["event_id"]] if filtered else []))
        result["tool_events"].append(request)
    return result


def run(out: Path, template_id: str, channel: str, provider=None):
    if provider is not None and not isinstance(provider, MockProvider):
        raise TypeError("offline task acceptance requires a mock provider")
    template = registry.load(template_id)
    base.validator("task").validate(template)
    variant = template["variants"][channel]
    base.validator("policy").validate(variant["policy"])
    out.mkdir(parents=True, exist_ok=False)
    root = registry.reset(out / "fixtures")
    state = registry.create_state(out / "states")
    if registry.verify(root) != template["fixture_hash"]:
        raise ValueError("task fixture hash mismatch")
    provider = provider if provider is not None else TaskProvider(template, channel)
    trial = f"w6-t1:{uuid.uuid4().hex}:{template_id}:{channel}:clean:D0_BASELINE:r1"
    log = base.EventLog(out / base.EVENTS_FILE, base.utc_now, logical_trial_id=trial,
                        experiment_id="w6-t1-offline-acceptance", component_versions={
                            **base.COMPONENT_VERSIONS, "runner": VERSION, "task_registry": registry.VERSION,
                            "provider_adapter": PROVIDER_ADAPTER_VERSION, "utility": str(UTILITY_VERSION),
                            "parser": PARSER_VERSION, "read_file": READ_VERSION, "query_db": QUERY_VERSION,
                            "fetch_url": FETCH_VERSION, "send_email": EMAIL_VERSION,
                            "fixture_service": "fixture-http-v0.1.0"})
    messages = [{"role": "system", "content": registry.SYSTEM_PROMPT},
                {"role": "user", "content": variant["prompt_template"]}]
    grant_state = registry.grants(template, channel)
    log.append("trial_started", {"template_id": template_id, "task_channel": channel,
               "task_version": template["version"], "task_prompt": variant["prompt_template"],
               "prompt_sha256": base.sha256_json(messages), "model_requested": MOCK_MODEL_ID,
               "decoding": base.DECODING, "max_steps": template["max_steps"], "code_commit": base.code_commit(),
               "fixture_hash": registry.verify(root), "database_hash": hashlib.sha256((root / "fixture.sqlite").read_bytes()).hexdigest(),
               "policy_hash": base.sha256_json(variant["policy"]),
               "utility_hash": base.sha256_text((registry.ROOT / "oracles/utility/task_suite.py").read_text()),
               "tool_schema_hash": base.sha256_json(registry.TOOL_SCHEMAS),
               "grants": [vars(g) for g in grant_state.grants]})

    def on_tool(kind, payload):
        log.append(kind, payload, model_call_id=f"{trial}:step{payload['step']}", raw_sha256=base.sha256_json(payload))

    def on_attempt(step, attempt, response):
        call_id = f"{trial}:step{step}"
        payload = {"step": step, "attempt_index": attempt,
                   **{key: response[key] for key in ("outcome", "provider_request_id", "model_requested",
                      "model_resolved", "provider_fingerprint", "raw_response")}}
        log.append("provider_attempt", payload, model_call_id=call_id, attempt_id=f"{call_id}:a{attempt}",
                   raw_sha256=base.sha256_json(response["raw_response"]))

    def effect(request, observation):
        if request.tool == "send_email":
            return email_effects[request.call_id]
        return {"effect_observed": observation["ok"], "effect_oracle_id": f"{request.tool}-returned-v0.1.0"}

    email_effects = {}
    steps = 0
    termination = "infrastructure_failure"
    try:
        with registry.fixture_service(root) as port:
            def dispatch(request):
                before = sink_receipts(state) if request.tool == "send_email" else []
                on_tool("tool_dispatch", {"call_id": request.call_id, "step": request.step,
                                          "blocked": False, "dispatched": True})
                observation = registry.worker(root, state, port, request)
                on_tool("tool_result", {"call_id": request.call_id, "step": request.step, "observation": observation})
                if request.tool == "send_email":
                    try:
                        after = sink_receipts(state)
                        received = len(after) > len(before)
                        for receipt in after[len(before):]:
                            on_tool("sink_receipt", {"call_id": request.call_id, "step": request.step, "receipt": receipt})
                    except (OSError, ValueError, UnicodeError):
                        received = None
                    email_effects[request.call_id] = {"effect_observed": received, "sink_received": received,
                                                     "effect_oracle_id": "fake-sink-append-v0.1.0"}
                return observation

            outcome = run_loop(provider, messages, tool_schemas=registry.TOOL_SCHEMAS, decoding=base.DECODING,
                               model_request={"model": MOCK_MODEL_ID}, on_attempt=on_attempt, max_steps=template["max_steps"],
                               logical_trial_id=trial, dispatch=dispatch, on_tool=on_tool,
                               request_parser=parse_request, effect_observer=effect)
            termination, steps = outcome.termination_reason, outcome.steps_used
            if outcome.final_text is not None:
                log.append("final_output", {"text": outcome.final_text, "text_sha256": base.sha256_text(outcome.final_text)})
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError):
        events = base.read_jsonl(out / base.EVENTS_FILE, "event")
        steps = len({e["payload"]["step"] for e in events if e["event_type"] == "provider_attempt"})
    try:
        sink_receipts(state)
        sink_observed = True
    except (OSError, ValueError, UnicodeError):
        sink_observed = None
    log.append("trial_ended", {"status": "infrastructure_failure" if termination == "infrastructure_failure" else "completed",
                              "termination_reason": termination, "steps_used": steps, "sink_observed": sink_observed})
    events = base.read_jsonl(out / base.EVENTS_FILE, "event")
    base.append_jsonl(out / base.RESULTS_FILE, assemble(events), "result")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    for template_id, template in registry.templates().items():
        for channel in template["variants"]:
            out = run(args.out / f"{template_id}-{channel}", template_id, channel)
            result, = base.read_jsonl(out / base.RESULTS_FILE, "result")
            print(f"{template_id} {channel}: utility={result['utility']['pass']}")
            if result["utility"]["pass"] is not True:
                raise SystemExit("offline task acceptance failed")


if __name__ == "__main__":
    main()
