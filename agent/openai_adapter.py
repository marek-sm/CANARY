"""OpenAI Chat Completions provider adapter (decision 0005).

Implements the provider boundary from docs/INTERFACES.md:

    complete(messages, tool_schemas, decoding, model_request) -> model_response

The client is injected and holds the only credential; this module never reads
the environment. ``build_client`` is called only by the explicitly named live
command (``runner.live_smoke``), never by CI or the mock runners. SDK retries
are off: the agent loop retries a call at most twice, and only when no model
content came back (SPEC.md Section 9); it never retries a content-policy
refusal (decision 0008). Every provider error is returned as a no-content
record, never raised, so each transport attempt is logged.
"""
from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

import httpx2
import openai

# The version also names the fixed request settings: store=False, SDK max_retries=0,
# a 60 s timeout, and no proxy or CA settings taken from the environment.
ADAPTER_VERSION = "openai-chat-adapter-v0.2.0"
API_BASE_URL = "https://api.openai.com/v1"
ENDPOINT = "chat_completions"
DECODING_KEYS = {"endpoint", "reasoning_effort", "max_completion_tokens"}

# OpenAI finish_reason -> the stop_reason agent/loop.py parses. A content-filter
# stop is a completed provider content-filter refusal (SPEC.md Section 9,
# decision 0008), which the loop records as such rather than as a final answer.
# Anything unmapped passes through and the loop records malformed_model_output.
STOP_REASONS = {"stop": "end_turn", "tool_calls": "tool_use", "length": "max_tokens", "content_filter": "content_filter"}

# Provider error codes that identify an HTTP rejection as a content-policy
# refusal, which SPEC.md Section 9 counts as a completed outcome and the loop
# never retries (decision 0008). OpenAI's error-code guide names no such code
# for Chat Completions, so the set starts empty and every HTTP error stays an
# infrastructure failure. This adapter applies the set to HTTP 400 only. A code
# joins only from recorded evidence, with an adapter version bump before Gate 3
# and Section 11 change control after it.
CONTENT_POLICY_CODES: frozenset[str] = frozenset()


def build_client(api_key: str) -> openai.OpenAI:
    """Outer-runner only. Pins the base URL, turns SDK retries off, and ignores
    proxy/CA environment settings. Refuses ambient OPENAI_* variables, which the
    SDK would otherwise read (organization, project, custom headers)."""
    if not api_key:
        raise ValueError("empty provider key")
    ambient = sorted(name for name in os.environ if name.startswith("OPENAI_"))
    if ambient:
        raise ValueError("unset ambient OpenAI variables first: " + ", ".join(ambient))
    return openai.OpenAI(api_key=api_key, base_url=API_BASE_URL, max_retries=0, timeout=60.0,
                         http_client=httpx2.Client(trust_env=False))


def check_decoding(decoding: Mapping[str, Any], has_tools: bool) -> dict[str, Any]:
    """Explicit decoding settings only; sampling parameters are never sent."""
    unknown = set(decoding) - DECODING_KEYS
    if unknown:
        raise ValueError(f"unsupported decoding settings: {sorted(unknown)}")
    if decoding.get("endpoint") != ENDPOINT:
        raise ValueError("endpoint must be 'chat_completions'; the Responses endpoint is not implemented")
    if "reasoning_effort" not in decoding:
        raise ValueError("reasoning_effort must be set explicitly")
    if has_tools and decoding["reasoning_effort"] != "none":
        raise ValueError("Chat Completions tool calling requires reasoning_effort 'none'")
    params = {"reasoning_effort": decoding["reasoning_effort"]}
    if "max_completion_tokens" in decoding:
        limit = decoding["max_completion_tokens"]
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError("max_completion_tokens must be a positive integer")
        params["max_completion_tokens"] = limit
    return params


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _no_constant(name: str) -> Any:
    raise ValueError(f"{name} is not JSON")


def _finite(text: str) -> float:
    number = float(text)
    if not math.isfinite(number):
        raise ValueError(f"{text} is not a finite number")
    return number


def _parse_arguments(arguments: Any) -> Any:
    """Strict JSON: NaN, infinity, and overflowing numbers count as unparseable,
    so the canonical evidence hash (decision 0009) never meets them."""
    return json.loads(arguments, parse_constant=_no_constant, parse_float=_finite)


def to_chat_messages(messages: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Translate the loop's history into Chat Completions messages."""
    out: list[dict[str, Any]] = []
    for message in messages:
        role, content = message["role"], message["content"]
        if isinstance(content, str):
            out.append({"role": role, "content": content})
            continue
        if role == "assistant":
            text = "".join(b["text"] for b in content if b["type"] == "text")
            calls = [{"id": b["id"], "type": "function",
                      "function": {"name": b["name"], "arguments": b["input"] if isinstance(b["input"], str) else _json(b["input"])}}
                     for b in content if b["type"] == "tool_use"]
            if any(b["type"] not in ("text", "tool_use") for b in content):
                raise ValueError("unsupported assistant block")
            entry: dict[str, Any] = {"role": "assistant", "content": text or None}
            if calls:
                entry["tool_calls"] = calls
            out.append(entry)
        elif role == "user" and all(b["type"] == "tool_result" for b in content):
            for b in content:
                result = b["content"]
                out.append({"role": "tool", "tool_call_id": b["tool_use_id"], "content": result if isinstance(result, str) else _json(result)})
        else:
            raise ValueError("unsupported message content")
    return out


def to_chat_tools(tool_schemas: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}}
            for t in tool_schemas]


def normalize(choice: Mapping[str, Any]) -> dict[str, Any]:
    """One Chat choice -> the loop's {stop_reason, content} shape.

    Unparseable tool arguments stay a raw string so the loop's parser rejects
    them without dispatch. A non-function tool call becomes an unknown block,
    which the loop also rejects.
    """
    message = choice["message"]
    content: list[dict[str, Any]] = []
    text = message.get("content")
    if text is None:
        text = message.get("refusal")
    if text is not None:
        content.append({"type": "text", "text": text})
    for call in message.get("tool_calls") or []:
        if call.get("type") != "function":
            content.append({"type": "unsupported_tool_call"})
            continue
        arguments = call["function"]["arguments"]
        try:
            parsed: Any = _parse_arguments(arguments)
        except (TypeError, ValueError):
            parsed = arguments
        content.append({"type": "tool_use", "id": call["id"], "name": call["function"]["name"], "input": parsed})
    finish = choice.get("finish_reason")
    return {"stop_reason": STOP_REASONS.get(finish, finish), "content": content}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class OpenAIChatAdapter:
    adapter_version = ADAPTER_VERSION

    def __init__(self, client: openai.OpenAI) -> None:
        # The loop owns retries; SDK retries would be invisible attempts.
        self._client = client.with_options(max_retries=0)

    def complete(
        self,
        messages: Sequence[Mapping[str, Any]],
        tool_schemas: Sequence[Mapping[str, Any]],
        decoding: Mapping[str, Any],
        model_request: Mapping[str, Any],
    ) -> dict[str, Any]:
        params = check_decoding(decoding, bool(tool_schemas))
        request: dict[str, Any] = {"model": model_request["model"], "messages": to_chat_messages(messages), "store": False, **params}
        if tool_schemas:
            request["tools"] = to_chat_tools(tool_schemas)
        record: dict[str, Any] = {
            "outcome": "no_model_content", "provider_request_id": None, "model_requested": model_request["model"],
            "model_resolved": None, "provider_fingerprint": None, "raw_response": None,
            "usage": {"input_tokens": None, "output_tokens": None}, "provider_response": None,
            "requested_at": _now(), "completed_at": None, "latency_ms": None, "error": None,
        }
        started = time.monotonic()
        try:
            raw = self._client.chat.completions.with_raw_response.create(**request)
        except (openai.APITimeoutError, openai.APIConnectionError) as exc:
            record["error"] = {"type": type(exc).__name__, "status": None}
        except openai.APIStatusError as exc:
            # Any HTTP error returns no model content. It is returned, not raised,
            # so the loop logs every attempt (SPEC.md Section 9); rejected requests
            # are not billed, and the loop's two retries then end the trial as an
            # infrastructure failure, unless the code marks a content-policy
            # refusal (decision 0008). The error message is never kept.
            record.update(provider_request_id=exc.request_id,
                          error={"type": type(exc).__name__, "status": exc.status_code, "provider_code": exc.code, "provider_type": exc.type})
            if exc.status_code == 400 and exc.code in CONTENT_POLICY_CODES:
                record["outcome"] = "provider_content_filter"
        else:
            record["provider_request_id"] = raw.request_id or raw.http_response.headers.get("x-request-id")
            try:
                body = raw.http_response.json()
            except ValueError:
                body = None
                record["provider_response"] = raw.http_response.text
            if isinstance(body, dict):
                record["provider_response"] = body
                record["model_resolved"] = body.get("model")
                record["provider_fingerprint"] = body.get("system_fingerprint")
                usage = body.get("usage") or {}
                record["usage"] = {"input_tokens": usage.get("prompt_tokens"), "output_tokens": usage.get("completion_tokens")}
            choices = body.get("choices") if isinstance(body, dict) else None
            if choices and isinstance(choices[0], dict) and isinstance(choices[0].get("message"), dict):
                try:
                    normalized = normalize(choices[0])
                except (KeyError, TypeError, AttributeError):
                    # Content came back but its structure is unusable: a completed
                    # model outcome the loop rejects as malformed, never dispatched.
                    normalized = {"stop_reason": None, "content": [{"type": "unparseable_provider_response"}]}
                record.update(outcome="model_response", raw_response=normalized)
            else:
                record["error"] = {"type": "no_choices" if isinstance(body, dict) else "invalid_body", "status": raw.http_response.status_code}
        record["completed_at"] = _now()
        record["latency_ms"] = int((time.monotonic() - started) * 1000)
        return record
