"""Bounded hand-written loop; only the outer runner owns tools and credentials."""
from __future__ import annotations
import copy
from dataclasses import dataclass
import posixpath
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional, Sequence
import unicodedata

from defenses.interfaces import CanonicalRequest

LOOP_VERSION = "agent-loop-v0.3.0"
NORMALIZER_VERSION = "read-file-normalizer-v0.1.0"
MAX_STEPS = 8
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


def parse_request(block, trial_id, step):
    if set(block) != {"type", "id", "name", "input"} or block["name"] != "read_file":
        raise ValueError("unsupported tool shape")
    if not isinstance(block["id"], str) or not block["id"]:
        raise ValueError("invalid call id")
    args = block["input"]
    if not isinstance(args, dict) or set(args) != {"path"} or not isinstance(args["path"], str):
        raise ValueError("invalid arguments")
    path = unicodedata.normalize("NFC", args["path"].replace("\r\n", "\n").replace("\r", "\n"))
    if not path or "\x00" in path:
        raise ValueError("unrepresentable path")
    # POSIX normalization preserves escaping '..' and absolute paths for audit.
    path = posixpath.normpath(path)
    if path.startswith("//"):
        path = "/" + path.lstrip("/")
    return CanonicalRequest(f"{trial_id}:step{step}:call1", trial_id, step, "read_file", MappingProxyType({"path": path}), NORMALIZER_VERSION)


def requested_payload(request: CanonicalRequest, block: Mapping[str, Any], step: int) -> dict[str, Any]:
    return {"call_id": request.call_id, "step": step, "tool": request.tool, "requested_args": block["input"],
            "normalized_args": dict(request.normalized_args), "normalizer_version": request.normalizer_version}


def run_loop(provider: Any, messages: Sequence[Mapping[str, Any]], *,
             tool_schemas: Sequence[Mapping[str, Any]], decoding: Mapping[str, Any],
             model_request: Mapping[str, Any], on_attempt: Callable,
             max_steps: int = MAX_STEPS, logical_trial_id: str = "mock",
             dispatch: Optional[Callable] = None, on_tool: Optional[Callable] = None) -> LoopOutcome:
    """Persist attempts before acting. A response consumes one step, retries do not."""
    if max_steps < 1:
        raise ValueError("max_steps must be at least 1")
    history = copy.deepcopy(list(messages))
    seen_ids = set()
    for step in range(1, max_steps + 1):
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
                if len(calls) != 1 or dispatch is None or on_tool is None:
                    raise ValueError("one registered tool call required")
                block = calls[0]
                request = parse_request(block, logical_trial_id, step)
                if block["id"] in seen_ids:
                    raise ValueError("duplicate provider call id")
                seen_ids.add(block["id"])
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
                    filtered = parse_request(calls[0], logical_trial_id, step)
                except ValueError:
                    filtered = None
                if filtered is not None:
                    on_tool("tool_requested", requested_payload(filtered, calls[0], step))
            return LoopOutcome("provider_content_filter", response_text(raw), step)
        if raw["stop_reason"] == "tool_use":
            on_tool("tool_requested", requested_payload(request, block, step))
            observation = dispatch(request)
            history.append({"role": "assistant", "content": copy.deepcopy(content)})
            history.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": block["id"], "content": observation}]})
            on_tool("effect_observation", {"call_id": request.call_id, "step": step,
                    "effect_observed": observation["ok"], "effect_oracle_id": "read-returned-v0.1.0"})
            continue
        text = response_text(raw)
        if raw["stop_reason"] == "end_turn":
            return LoopOutcome("final_answer", text, step)
        if text:  # an empty text block is invalid on some providers
            history.append({"role": "assistant", "content": text})
        history.append({"role": "user", "content": CONTINUATION_PROMPT})
    return LoopOutcome("max_steps", None, max_steps)
