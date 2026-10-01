"""Excluded W5-T1 smoke; provisional records pending the W5-T3 contract."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

from agent.loop import run_loop
from oracles.utility.ticket import validate, VERSION as UTILITY_VERSION
from tasks import ticket
from runner import mock_slice as base
from runner.mock_provider import MockProvider, MOCK_MODEL_ID, PROVIDER_ADAPTER_VERSION

VERSION = "ticket-runner-v0.1.0"
# Present only in real-provider responses (agent/openai_adapter.py); the mock has none.
PROVIDER_EVIDENCE_KEYS = ("usage", "requested_at", "completed_at", "latency_ms", "error", "provider_response")


class TicketProvider(MockProvider):
    """Offline task-aware mock: final answer depends on the actual tool result."""
    def complete(self, messages, tool_schemas, decoding, model_request):
        if self.calls == 0:
            raw = {"stop_reason": "tool_use", "content": [{"type": "tool_use", "id": "ticket-read", "name": "read_file", "input": {"path": "inbox/ticket-100.txt"}}]}
        else:
            observation = messages[-1]["content"][0]["content"]
            fields = {}
            if observation["ok"]:
                for line in observation["text"].splitlines():
                    if ": " in line:
                        key, value = line.split(": ", 1)
                        if key in ("ticket_id", "status"):
                            fields[key] = value
            raw = {"stop_reason": "end_turn", "content": [{"type": "text", "text": json.dumps(fields)}]}
        self._script.append(raw)
        return super().complete(messages, tool_schemas, decoding, model_request)

    def __init__(self):
        super().__init__([])


def worker(root, request):
    completed = subprocess.run(
        [sys.executable, "-I", str(ticket.ROOT / "tools/read_file.py"), str(root)],
        input=json.dumps(dict(request.normalized_args)), capture_output=True, text=True,
        env={"PATH": os.defpath, "LANG": "C.UTF-8"}, timeout=5, check=True,
    )
    return json.loads(completed.stdout)


def assemble(events, analysis_role="excluded_mock"):
    result = base.assemble_result(events)
    start = events[0]
    p = start["payload"]
    result.update(experiment_id=start["experiment_id"], logical_trial_id=start["logical_trial_id"], base_case_id=ticket.TASK_ID,
                  case_id=ticket.TASK_ID + ":none:none", analysis_role=analysis_role,
                  measurement_limitation="W5-T3 audit/security scoring and final contract unavailable")
    result["run_metadata"].update(rendered_fixture_hash=p["fixture_hash"], task_policy_hash=p["policy_hash"], utility_oracle_hash=p["utility_hash"])
    result["utility"] = {"oracle_id": ticket.TASK_ID, "oracle_version": UTILITY_VERSION,
                         "pass": validate(events), "reason_codes": ["deterministic_ticket_evidence"]}
    result["tool_events"] = []
    for event in events:
        if event["event_type"] != "tool_requested":
            continue
        request = dict(event["payload"])
        related = [e for e in events if e["payload"].get("call_id") == request["call_id"]]
        returned = next((e["payload"] for e in related if e["event_type"] == "tool_result"), None)
        effect = next((e["payload"] for e in related if e["event_type"] == "effect_observation"), None)
        entered = any(e["event_type"] == "tool_dispatch" for e in related)
        request.update(request_evaluable=False, authorized=None, gate_decision=None, audit_decision=None,
                       gate_audit_match=None, blocked=False, dispatched=True if entered else None,
                       disposition_observed=None, execution_succeeded=returned["observation"]["ok"] if returned else None,
                       effect_observed=effect["effect_observed"] if effect else None,
                       effect_oracle_id="read-returned-v0.1.0", sink_received=False,
                       evidence_refs=[e["event_id"] for e in related])
        result["tool_events"].append(request)
    return result


def run(out: Path, provider=None, *, model=MOCK_MODEL_ID, decoding=base.DECODING, experiment_id=base.EXPERIMENT_ID,
        analysis_role="excluded_mock"):
    out.mkdir(parents=True, exist_ok=False)
    provider = provider or TicketProvider()
    fixture = ticket.reset(out / "fixtures")
    manifest = ticket.manifest()
    base.validator("policy").validate(manifest["policy"])
    trial = f"{experiment_id}:unfrozen:{model}:{ticket.TASK_ID}:none:none:D0_BASELINE:r1"
    log = base.EventLog(out / base.EVENTS_FILE, base.utc_now, logical_trial_id=trial, experiment_id=experiment_id, component_versions={**base.COMPONENT_VERSIONS, "provider_adapter": getattr(provider, "adapter_version", PROVIDER_ADAPTER_VERSION), "runner": VERSION, "read_file": "read-file-v0.1.0", "utility": str(UTILITY_VERSION)})
    messages = [{"role": "system", "content": ticket.SYSTEM_PROMPT}, {"role": "user", "content": ticket.TASK_PROMPT}]
    log.append("trial_started", {"task_prompt": ticket.TASK_PROMPT, "prompt_sha256": base.sha256_json(messages),
               "model_requested": model, "decoding": dict(decoding), "max_steps": manifest["max_steps"],
               "code_commit": base.code_commit(), "tier": None, "fixture_hash": ticket.verify(fixture),
               "policy_hash": base.sha256_json(manifest["policy"]),
               "utility_hash": base.sha256_text((ticket.ROOT / "oracles/utility/ticket.py").read_text()),
               "tool_schema_hash": base.sha256_json(ticket.TOOL_SCHEMA), "task_version": manifest["version"],
               "runner_version": VERSION, "measurement_limitation": "W5-T3 unavailable; provisional integration"})

    def on_attempt(step, attempt_index, response):
        call = f"{trial}:step{step}"
        payload = {"step": step, "attempt_index": attempt_index,
                   **{key: response[key] for key in ("outcome", "provider_request_id", "model_requested", "model_resolved", "provider_fingerprint", "raw_response")}}
        if "provider_response" in response:
            payload.update({key: response.get(key) for key in PROVIDER_EVIDENCE_KEYS})
        log.append("provider_attempt", payload,
                   model_call_id=call, attempt_id=f"{call}:a{attempt_index}", raw_sha256=base.sha256_json(response["raw_response"]))

    def on_tool(kind, payload):
        log.append(kind, payload, model_call_id=f"{trial}:step{payload['step']}", raw_sha256=base.sha256_json(payload))

    def dispatch(request):
        on_tool("tool_dispatch", {"call_id": request.call_id, "step": request.step, "dispatched": True, "blocked": False})
        observation = worker(fixture, request)
        on_tool("tool_result", {"call_id": request.call_id, "step": request.step, "observation": observation})
        return observation

    try:
        outcome = run_loop(provider, messages, tool_schemas=[ticket.TOOL_SCHEMA],
                           decoding=decoding, model_request={"model": model}, on_attempt=on_attempt,
                           max_steps=manifest["max_steps"], logical_trial_id=trial, dispatch=dispatch, on_tool=on_tool)
        if outcome.final_text is not None:
            log.append("final_output", {"text": outcome.final_text, "text_sha256": base.sha256_text(outcome.final_text)})
        termination, steps = outcome.termination_reason, outcome.steps_used
    except (OSError, subprocess.SubprocessError, ValueError, RuntimeError):
        # Keep prior evidence. Never persist exception strings, credentials, or host paths.
        termination, steps = "infrastructure_failure", len({e["payload"]["step"] for e in base.read_jsonl(out / base.EVENTS_FILE, "event") if e["event_type"] == "provider_attempt"})
    log.append("trial_ended", {"status": "infrastructure_failure" if termination == "infrastructure_failure" else "completed", "termination_reason": termination, "steps_used": steps})
    events = base.read_jsonl(out / base.EVENTS_FILE, "event")
    (out / base.RESULTS_FILE).touch(exist_ok=False)
    base.append_jsonl(out / base.RESULTS_FILE, assemble(events, analysis_role), "result")
    return out


def main():
    from demo.trace import render_trace
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = run(args.out or ticket.ROOT / "results/development/ticket" / stamp)
    print(render_trace(out / base.EVENTS_FILE))


if __name__ == "__main__":
    main()
