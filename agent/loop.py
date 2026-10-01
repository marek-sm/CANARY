"""Bounded hand-written loop; only the outer runner owns tools and credentials."""
from __future__ import annotations
import copy
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Sequence

from defenses.canonicalizer import NORMALIZER_VERSION, CanonicalizationError, canonicalize_tool_use

LOOP_VERSION = "agent-loop-v0.1.0"
SUPPORTED_TOOLS = ("read_file",)  # widened by W6-T1 as each safe tool lands
MAX_STEPS = 8


@dataclass(frozen=True)
class LoopOutcome:
    termination_reason: str
    final_text: Optional[str]
    steps_used: int


def response_text(raw_response: Mapping[str, Any]) -> str:
    return "".join(block["text"] for block in raw_response["content"] if block.get("type") == "text")


def parse_request(block, trial_id, step, supported_tools: Sequence[str] = SUPPORTED_TOOLS):
    """Canonicalize one provider tool_use block, exactly once, via the W6-T4 canonicalizer.

    ``supported_tools`` is the set of tools this runner can dispatch today; a call to
    any other tool cannot be handled and is treated as malformed model output.
    """
    try:
        if not isinstance(block, Mapping) or block.get("name") not in supported_tools:
            raise ValueError("unsupported tool shape")
        return canonicalize_tool_use(block, trial_id, step)
    except CanonicalizationError as exc:
        raise ValueError(str(exc)) from exc


def run_loop(provider: Any, messages: Sequence[Mapping[str, Any]], *,
             tool_schemas: Sequence[Mapping[str, Any]], decoding: Mapping[str, Any],
             model_request: Mapping[str, Any], on_attempt: Callable,
             max_steps: int = MAX_STEPS, logical_trial_id: str = "mock",
             dispatch: Optional[Callable] = None, on_tool: Optional[Callable] = None,
             supported_tools: Sequence[str] = SUPPORTED_TOOLS) -> LoopOutcome:
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
            if raw is not None:
                break
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
                request = parse_request(block, logical_trial_id, step, supported_tools)
                if block["id"] in seen_ids:
                    raise ValueError("duplicate provider call id")
                seen_ids.add(block["id"])
            elif calls or raw["stop_reason"] not in ("end_turn", "max_tokens"):
                raise ValueError("invalid stop reason")
        except (KeyError, TypeError, ValueError):
            return LoopOutcome("malformed_model_output", None, step)
        if raw["stop_reason"] == "tool_use":
            on_tool("tool_requested", {"call_id": request.call_id, "step": step, "tool": request.tool,
                    "requested_args": block["input"], "normalized_args": dict(request.normalized_args),
                    "normalizer_version": request.normalizer_version})
            observation = dispatch(request)
            history.append({"role": "assistant", "content": copy.deepcopy(content)})
            history.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": block["id"], "content": observation}]})
            on_tool("effect_observation", {"call_id": request.call_id, "step": step,
                    "effect_observed": observation["ok"], "effect_oracle_id": "read-returned-v0.1.0"})
            continue
        text = response_text(raw)
        if raw["stop_reason"] == "end_turn":
            return LoopOutcome("final_answer", text, step)
        history.append({"role": "assistant", "content": text})
    return LoopOutcome("max_steps", None, max_steps)
