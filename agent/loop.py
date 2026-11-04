"""Bounded hand-written loop; only the outer runner owns tools and credentials."""
from __future__ import annotations
import copy
from dataclasses import dataclass, replace
from typing import Any, Callable, Mapping, Optional, Sequence

from defenses.canonicalizer import NORMALIZER_VERSION, CanonicalizationError, canonicalize_tool_use, thaw_json
from defenses.interfaces import CanonicalRequest

# PROTOTYPE (branch cloud/parallel-calls, not decided): v0.5.0 executes every
# tool call in a reply, in order, and names MAX_CALLS_PER_REPLY. Decision 0026
# item 2's reply rule is what main runs; this version is evidence for the lead.
LOOP_VERSION = "agent-loop-v0.5.0-parallel-prototype"
SUPPORTED_TOOLS = ("read_file",)  # widened by W6-T1 as each safe tool lands
MAX_STEPS = 8
# A reply may carry at most this many tool calls; one with more records none of
# them and ends the trial as malformed_model_output, so one step can't fan out
# into an unbounded number of dispatches. The value is a placeholder for a lead
# decision: it equals MAX_STEPS, so a trial can't dispatch more per reply than
# the one-call loop could dispatch in a whole trial.
MAX_CALLS_PER_REPLY = 8
# Follows a reply cut off at the output limit. Some providers reject a
# conversation that ends with an assistant turn (decision 0010).
CONTINUATION_PROMPT = "Your previous reply was cut off at the output limit. Continue from where it stopped."


@dataclass(frozen=True)
class LoopOutcome:
    termination_reason: str
    final_text: Optional[str]
    steps_used: int


def response_text(raw_response: Mapping[str, Any]) -> str:
    return "".join(block["text"] for block in raw_response["content"] if block.get("type") == "text")


def call_id_for(trial_id: str, step: int, position: int) -> str:
    """The runner's call ID: the step's model call plus the call's 1-based place in
    the reply. A one-call reply keeps the ``:call1`` ID the canonicalizer gives."""
    return f"{trial_id}:step{step}:call{position}"


def parse_request(block, trial_id, step, supported_tools: Sequence[str] = SUPPORTED_TOOLS, position: int = 1):
    """Canonicalize one provider tool_use block, exactly once, via the W6-T4 canonicalizer.

    ``supported_tools`` is the set of tools this runner can dispatch today; a call to
    any other tool cannot be handled and is treated as malformed model output.
    ``position`` is the call's 1-based place in its reply; it sets the call ID
    before the request object is logged, authorized, or dispatched.
    """
    try:
        if not isinstance(block, Mapping) or block.get("name") not in supported_tools:
            raise ValueError("unsupported tool shape")
        request = canonicalize_tool_use(block, trial_id, step)
    except CanonicalizationError as exc:
        raise ValueError(str(exc)) from exc
    if position != 1:
        request = replace(request, call_id=call_id_for(trial_id, step, position))
    return request


def parse_reply_calls(calls, trial_id, step, supported_tools: Sequence[str], seen_ids: set,
                      max_calls: int = MAX_CALLS_PER_REPLY) -> list[tuple[Mapping[str, Any], CanonicalRequest]]:
    """Validate every tool call in one reply before any of them is recorded.

    The reply is all or nothing: one malformed call, a provider ID repeated
    inside the reply or seen earlier in the trial, or more than ``max_calls``
    calls makes the whole reply malformed, and none of its calls is recorded
    (the same rule decision 0026 item 2 applies to a one-call reply). Pure: it
    records nothing and leaves ``seen_ids`` unchanged.
    """
    if not 1 <= len(calls) <= max_calls:
        raise ValueError("tool call count outside the reply bound")
    ids = [block.get("id") if isinstance(block, Mapping) else None for block in calls]
    if len(set(map(repr, ids))) != len(ids):
        raise ValueError("duplicate provider call id in one reply")
    parsed = [(block, parse_request(block, trial_id, step, supported_tools, position))
              for position, block in enumerate(calls, start=1)]
    if any(block["id"] in seen_ids for block, _ in parsed):
        raise ValueError("duplicate provider call id")
    return parsed


def requested_payload(request: CanonicalRequest, block: Mapping[str, Any], step: int) -> dict[str, Any]:
    return {"call_id": request.call_id, "step": step, "tool": request.tool, "requested_args": block["input"],
            "normalized_args": thaw_json(request.normalized_args), "normalizer_version": request.normalizer_version}


def run_loop(provider: Any, messages: Sequence[Mapping[str, Any]], *,
             tool_schemas: Sequence[Mapping[str, Any]], decoding: Mapping[str, Any],
             model_request: Mapping[str, Any], on_attempt: Callable,
             max_steps: int = MAX_STEPS, logical_trial_id: str = "mock",
             dispatch: Optional[Callable] = None, on_tool: Optional[Callable] = None,
             supported_tools: Sequence[str] = SUPPORTED_TOOLS,
             effect_observer: Optional[Callable] = None) -> LoopOutcome:
    """Persist attempts before acting. A response consumes one step, retries do not."""
    if max_steps < 1:
        raise ValueError("max_steps must be at least 1")
    history = copy.deepcopy(list(messages))
    seen_ids = set()
    for step in range(1, max_steps + 1):
        # range(1, 4): one initial provider call plus at most two retries (SPEC.md Section 9).
        for attempt in range(1, 4):
            response = provider.complete(history, tool_schemas, decoding, model_request)
            on_attempt(step, attempt, response)
            raw = response["raw_response"]
            if raw is not None or response.get("outcome") == "provider_content_filter":
                break
        if response.get("outcome") == "provider_content_filter":
            # A content-policy rejection is a completed refusal, never retried; the
            # final-output surface is complete and empty (decision 0008).
            return LoopOutcome("provider_content_filter", "", step)
        if raw is None:
            return LoopOutcome("infrastructure_failure", None, step)
        try:
            content = raw["content"]
            if not isinstance(content, list) or any(not isinstance(b, dict) for b in content):
                raise ValueError("invalid content")
            if any(b.get("type") not in ("text", "tool_use") for b in content):
                raise ValueError("invalid block")
            if any(not isinstance(b.get("text"), str) for b in content if b.get("type") == "text"):
                raise ValueError("invalid text")
            calls = [b for b in content if b.get("type") == "tool_use"]
            if raw["stop_reason"] == "tool_use":
                if dispatch is None or on_tool is None:
                    raise ValueError("a registered tool seam is required")
                parsed = parse_reply_calls(calls, logical_trial_id, step, supported_tools, seen_ids)
                seen_ids.update(block["id"] for block, _ in parsed)
            elif raw["stop_reason"] != "content_filter" and (calls or raw["stop_reason"] not in ("end_turn", "max_tokens")):
                raise ValueError("invalid stop reason")
        except (KeyError, TypeError, ValueError):
            return LoopOutcome("malformed_model_output", None, step)
        if raw["stop_reason"] == "content_filter":
            # A provider content-filter refusal is a completed outcome (SPEC.md
            # Section 9, decision 0008). One valid call is still a request, recorded
            # for audit, but the trial has ended, so it is never dispatched.
            if on_tool is not None and len(calls) == 1:
                try:
                    filtered = parse_request(calls[0], logical_trial_id, step, supported_tools)
                except (KeyError, TypeError, ValueError):
                    filtered = None
                if filtered is not None:
                    on_tool("tool_requested", requested_payload(filtered, calls[0], step))
            return LoopOutcome("provider_content_filter", response_text(raw), step)
        if raw["stop_reason"] == "tool_use":
            # Every call runs in reply order, one at a time: each is recorded, then
            # gated or dispatched by the seam, then its effect recorded, before the
            # next call is recorded. A later call sees the earlier ones as prior
            # calls, with their dispositions and any grant they consumed. The reply
            # takes one step however many calls it carries, and the next message
            # returns every result, in the reply's order (both providers require one
            # result per call ID).
            results = []
            for block, request in parsed:
                on_tool("tool_requested", requested_payload(request, block, step))
                observation = dispatch(request)
                effect = effect_observer(request, observation) if effect_observer is not None else {
                    "effect_observed": observation["ok"], "effect_oracle_id": "read-returned-v0.1.0"}
                on_tool("effect_observation", {"call_id": request.call_id, "step": step, **effect})
                results.append({"type": "tool_result", "tool_use_id": block["id"], "content": observation})
            history.append({"role": "assistant", "content": copy.deepcopy(content)})
            history.append({"role": "user", "content": results})
            continue
        text = response_text(raw)
        if raw["stop_reason"] == "end_turn":
            return LoopOutcome("final_answer", text, step)
        if text:  # an empty text block is invalid on some providers
            history.append({"role": "assistant", "content": text})
        history.append({"role": "user", "content": CONTINUATION_PROMPT})
    return LoopOutcome("max_steps", None, max_steps)
