"""Hand-written agent loop placeholder with an explicit step limit.

No agent framework is used (SPEC.md Section 4). This placeholder handles only
text turns: tool dispatch, retries, and parsing arrive with W5-T1. A
tool-use response raises rather than being silently ignored.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Sequence

LOOP_VERSION = "agent-loop-placeholder-v0"

# SPEC.md Section 4 default; the development reliability pilot may lock another value.
MAX_STEPS = 8


@dataclass(frozen=True)
class LoopOutcome:
    termination_reason: str  # "final_answer" or "max_steps"
    final_text: Optional[str]
    steps_used: int


def response_text(raw_response: Mapping[str, Any]) -> str:
    return "".join(
        block["text"] for block in raw_response["content"] if block.get("type") == "text"
    )


def run_loop(
    provider: Any,
    messages: Sequence[Mapping[str, Any]],
    *,
    tool_schemas: Sequence[Mapping[str, Any]],
    decoding: Mapping[str, Any],
    model_request: Mapping[str, Any],
    on_attempt: Callable[[int, int, Mapping[str, Any]], None],
    max_steps: int = MAX_STEPS,
) -> LoopOutcome:
    """Run at most ``max_steps`` model calls.

    ``on_attempt(step, attempt_index, response)`` must durably persist the
    attempt; it is called before the loop acts on the response or starts the
    next step.
    """
    if max_steps < 1:
        raise ValueError("max_steps must be at least 1")
    history = [dict(m) for m in messages]
    for step in range(1, max_steps + 1):
        response = provider.complete(history, tool_schemas, decoding, model_request)
        on_attempt(step, 1, response)
        raw = response["raw_response"]
        if raw is None:
            raise NotImplementedError("no-content retry handling arrives with W5-T1")
        if raw["stop_reason"] == "tool_use":
            raise NotImplementedError("tool dispatch arrives with W5-T1")
        text = response_text(raw)
        if raw["stop_reason"] == "end_turn":
            return LoopOutcome("final_answer", text, step)
        history.append({"role": "assistant", "content": text})
    return LoopOutcome("max_steps", None, max_steps)
