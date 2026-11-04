"""Build a reference ``Trial`` from a repo run directory's durable evidence.

Reads only evidence: events.jsonl, sink_receipts.json, the trial's canaries, the
trusted task template (tasks/templates/*.json, validated by schemas/task.schema.json),
and the grant state the trial_started event records. It never reads the result
record's scored fields; those are only compared afterwards (compare.py).

Event payload shapes beyond schemas/event.schema.json were learned from mock run
output (data), not from runner code; the report records that.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from .core import (
    TOOL_ARG_TYPES,
    CallEvidence,
    Grant,
    Reply,
    ToolCall,
    Trial,
)

REPO = Path(__file__).resolve().parents[2]

CONTENT_FILTER_STOPS = {"content_filter", "refusal"}


def load_template(template_id: str) -> dict:
    return json.loads((REPO / "tasks" / "templates" / f"{template_id}.json").read_text())


def reference_action_hash(policy: dict, tool: str, nargs: dict) -> str:
    """Reference-only action identity: SPEC binds a grant to "the hash of the exact
    normalized authorized action and policy version" but gives no hash function.
    Equality of this digest is equality of (policy_id, policy_version, tool, args)."""
    blob = json.dumps([policy["policy_id"], policy["policy_version"], tool, nargs], sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()


def observed_action_hash(policy: dict, tool: str, nargs: dict) -> str:
    """Action hash matching the grants recorded in t1-suite trial_started events,
    identified by black-box matching against one recorded grant (not by reading
    runner code): SHA-256 of compact, key-sorted JSON {args, policy_version, tool}.
    policy_id is matched separately on the grant record."""
    blob = json.dumps({"args": nargs, "policy_version": policy["policy_version"], "tool": tool},
                      sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def _events(run_dir: Path) -> list[dict]:
    return [json.loads(l) for l in (run_dir / "events.jsonl").read_text().splitlines() if l.strip()]


def _attempt_payload(e: dict) -> Optional[dict]:
    """provider_attempt (event schema) or model_attempt (C1 mock log)."""
    if e["event_type"] == "provider_attempt":
        return e["payload"]
    if e["event_type"] == "model_attempt":
        p = dict(e["payload"].get("response", {}))
        p["step"] = e["payload"]["step"]
        return p
    return None


def replies_from_events(events: list[dict]) -> tuple[list[Reply], Optional[int], bool]:
    replies: list[Reply] = []
    cf_step = None
    responses_complete = True
    for e in events:
        p = _attempt_payload(e)
        if p is None:
            continue
        outcome = p.get("outcome")
        raw = p.get("raw_response")
        if outcome == "no_model_content":
            continue  # retried transport attempt; no model behavior
        if raw is None:
            if outcome == "provider_content_filter":
                # HTTP rejection: "An HTTP rejection adds no request at that step."
                cf_step = p["step"]
                continue
            responses_complete = False
            continue
        content = raw.get("content") or []
        stop = raw.get("stop_reason")
        is_cf = outcome == "provider_content_filter" or stop in CONTENT_FILTER_STOPS
        if is_cf:
            cf_step = p["step"]
        calls = [ToolCall(b.get("id"), b.get("name"), b.get("input"))
                 for b in content if isinstance(b, dict) and b.get("type") == "tool_use"]
        text = "".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
        replies.append(Reply(
            step=p["step"],
            stop_reason="content_filter" if is_cf else stop,
            block_types=[b.get("type") if isinstance(b, dict) else repr(type(b)) for b in content],
            tool_calls=calls,
            text=text,
        ))
    return replies, cf_step, responses_complete


def evidence_from_events(events: list[dict], configuration: str) -> dict:
    """Group per-call evidence by (step, position) and by repo call_id."""
    by_id: dict[str, CallEvidence] = {}
    order: list[str] = []
    requested_meta: dict[str, dict] = {}
    for e in events:
        p = e.get("payload", {})
        cid = p.get("call_id")
        if cid is None:
            continue
        ev = by_id.setdefault(cid, CallEvidence())
        t = e["event_type"]
        if t == "tool_requested":
            order.append(cid)
            requested_meta[cid] = p
            if configuration == "D1_POLICY_GATE":
                ev.gate_completed = False
        elif t == "authorization_decision":
            action = p.get("gate_action")
            gd = p.get("gate_decision")
            if configuration == "D1_POLICY_GATE":
                ev.gate_completed = action in ("dispatch", "block") and gd is not None and gd.get("authorized") is not None
                if action in ("block", "unavailable"):
                    ev.gate_block_recorded = True
            if "audit_decision" in p and p["audit_decision"] is None:
                ev.audit_completed = False
        elif t == "tool_dispatch":
            if p.get("dispatched") is True:
                ev.dispatch_recorded = True
            if p.get("blocked") is True and configuration == "D1_POLICY_GATE":
                ev.gate_block_recorded = True
        elif t == "tool_result":
            ev.result_recorded = True
            obs = p.get("observation")
            if isinstance(obs, dict) and isinstance(obs.get("ok"), bool):
                ev.result_error = not obs["ok"]
            elif isinstance(p.get("execution_succeeded"), bool):
                ev.result_error = not p["execution_succeeded"]
        elif t == "effect_observation":
            if isinstance(p.get("effect_observed"), bool):
                ev.effect_recorded = True
                ev.effect_value = p["effect_observed"]
        elif t == "sink_receipt":
            if p.get("receipt") is not None:
                ev.sink_receipts.append(p["receipt"])
    return {"by_id": by_id, "order": order, "requested_meta": requested_meta}


def _position(cid: str) -> Optional[tuple[int, int]]:
    # repo call ids end with ":step<n>:call<k>" (learned from mock output)
    parts = cid.split(":")
    try:
        step = int(parts[-2].removeprefix("step"))
        k = int(parts[-1].removeprefix("call"))
        return step, k
    except (ValueError, IndexError):
        return None


def build_trial(run_dir: Path, canaries: Optional[list[str]] = None, result: Optional[dict] = None,
                template: Optional[dict] = None, derive_grants: bool = False,
                repo_normalization: bool = False) -> tuple[Trial, dict]:
    events = _events(run_dir)
    start = events[0]
    configuration = start.get("configuration") or (result or {}).get("configuration") or "D0_BASELINE"
    sp = start["payload"]
    template_id = sp.get("template_id")
    channel = sp.get("channel") or sp.get("task_channel")
    policy = None
    variant = None
    if template is None and template_id:
        try:
            template = load_template(template_id)
        except FileNotFoundError:
            template = None
    if template is not None and channel in template.get("variants", {}):
        variant = template["variants"][channel]
        policy = variant["policy"]

    grants: Optional[list[Grant]] = None
    grant_source = "none"
    if "grants" in sp:
        grants = []
        grant_source = "trial_started"
        for g in sp["grants"]:
            grants.append(Grant(g["grant_id"], g["policy_id"], g["policy_version"], g["action_hash"],
                                g.get("consumed", False)))

    if grants is None and derive_grants and variant is not None and policy is not None:
        # SPEC.md Section 6: "For a legitimate high-risk task, the harness creates a
        # trusted grant bound to the hash of the exact normalized authorized action
        # and policy version." The trusted action is the template's email_action.
        grants = []
        grant_source = "derived_from_template"
        for tool, tp in policy["tools"].items():
            if tp.get("requires_grant") and tool == "send_email" and "email_action" in variant:
                grants.append(Grant("derived-email-grant", policy["policy_id"], policy["policy_version"],
                                    observed_action_hash(policy, tool, variant["email_action"]), False))

    replies, cf_step, responses_complete = replies_from_events(events)
    evd = evidence_from_events(events, configuration)

    # Map reference (step, position) -> repo call id.
    pos_to_id = {}
    for cid in evd["order"]:
        pos = _position(cid)
        if pos:
            pos_to_id[pos] = cid
    evidence = {}
    repo_nargs = {}
    for r in replies:
        for i, c in enumerate(r.tool_calls, start=1):
            cid = pos_to_id.get((r.step, i))
            if cid is not None:
                evidence[(r.step, i)] = evd["by_id"][cid]
                repo_nargs[(r.step, i)] = evd["requested_meta"][cid].get("normalized_args")

    ended = [e for e in events if e["event_type"] in ("trial_ended", "c1_ended")]
    status = ended[-1]["payload"].get("status", "completed") if ended else None
    term = ended[-1]["payload"].get("termination_reason") if ended else None
    trial_complete = bool(ended) and status == "completed"

    finals = [e for e in events if e["event_type"] == "final_output"]
    if finals:
        final_output = finals[-1]["payload"]["text"]
    elif trial_complete:
        # SPEC.md Section 9: refusal, malformed output, and max-step endings "remain
        # completed model/provider outcomes and stay in denominators". A durably
        # completed trial that showed the user no final text has a complete, empty
        # user-visible final response. (Interpretation; see report.)
        final_output = ""
    else:
        final_output = None

    receipts: list = []
    for e in events:
        if e["event_type"] == "sink_receipt" and e["payload"].get("receipt") is not None:
            receipts.append(e["payload"]["receipt"])
    file_receipts = None
    if (run_dir / "sink_receipts.json").exists():
        file_receipts = json.loads((run_dir / "sink_receipts.json").read_text())

    if canaries is None:
        canaries = list((result or {}).get("canaries") or [])

    trial = Trial(
        configuration=configuration,
        canaries=canaries,
        policy=policy,
        grants=grants,
        offered_tools=dict(TOOL_ARG_TYPES),
        replies=replies,
        evidence=evidence,
        final_output=final_output,
        sink_receipts=receipts,
        trial_complete=trial_complete,
        status=status,
        termination_reason=term,
        content_filter_step=cf_step,
        responses_complete=responses_complete,
        action_hash=observed_action_hash,
        normalized_override=repo_nargs if repo_normalization else None,
    )
    meta = {
        "events": events,
        "variant": variant,
        "template": template,
        "template_id": template_id,
        "channel": channel,
        "grant_source": grant_source,
        "file_receipts": file_receipts,
        "pos_to_id": pos_to_id,
        "repo_requested_ids": evd["order"],
        "requested_meta": evd["requested_meta"],
        "policy_hash": sp.get("policy_hash"),
    }
    return trial, meta
