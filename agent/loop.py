"""Bounded hand-written loop; only the outer runner owns tools and credentials."""
from __future__ import annotations
import copy
from dataclasses import dataclass
import posixpath
from types import MappingProxyType
from typing import Any, Callable, Mapping, Optional, Sequence
import unicodedata

from defenses.interfaces import CanonicalRequest

LOOP_VERSION = "agent-loop-v0.1.0"
NORMALIZER_VERSION = "read-file-normalizer-v0.1.0"
MAX_STEPS = 8


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
                request = parse_request(block, logical_trial_id, step)
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
