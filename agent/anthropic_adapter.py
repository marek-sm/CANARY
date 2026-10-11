"""Anthropic Messages provider adapter (decision 0010).

Implements the provider boundary from docs/INTERFACES.md:

    complete(messages, tool_schemas, decoding, model_request) -> model_response

It returns the same record keys as agent/openai_adapter.py. The client is
injected and holds the only credential; this module never reads the key from
the environment. ``build_client`` is called only by the explicitly named live
command (``runner.live_smoke``), never by CI or the mock runners. SDK retries
are off: the agent loop retries a call at most twice, and only when no model
content came back (SPEC.md Section 9); it never retries a content-filter
refusal (decision 0008). Every provider error is returned as a no-content
record, never raised, so each transport attempt is logged.
"""
from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

import anthropic
import httpx2

# The version also names the fixed request settings: SDK max_retries=0, a 60 s
# timeout, no prompt caching, and no proxy or CA settings taken from the environment.
ADAPTER_VERSION = "anthropic-messages-adapter-v0.1.0"
API_BASE_URL = "https://api.anthropic.com"
ENDPOINT = "messages"
DECODING_KEYS = {"endpoint", "thinking", "effort", "max_tokens"}
# Claude Haiku 5.5 accepts disabled thinking only at these effort levels.
EFFORTS = {"low", "medium", "high"}

# Anthropic stop_reason -> the stop_reason agent/loop.py parses. A refusal is the
# provider's safety-classifier decline, a completed provider content-filter
# refusal (SPEC.md Section 9, decisions 0008 and 0010). Anything unmapped passes
# through and the loop records malformed_model_output.
STOP_REASONS = {"end_turn": "end_turn", "tool_use": "tool_use", "max_tokens": "max_tokens", "refusal": "content_filter"}

# Provider error codes (error.details.error_code) that identify an HTTP 400 as a
# content-policy refusal (decision 0008). Anthropic documents no such code, so
# the set starts empty and every HTTP error stays an infrastructure failure. A
# code joins only from recorded evidence, with an adapter version bump before
# Gate 3 and Section 11 change control after it.
CONTENT_POLICY_CODES: frozenset[str] = frozenset()


def build_client(api_key: str) -> anthropic.Anthropic:
    """Outer-runner only. Pins the base URL, turns SDK retries off, and ignores
    proxy/CA environment settings. Refuses ambient ANTHROPIC_* variables, which the
    SDK would otherwise read (auth token, base URL, custom headers, profiles)."""
    if not api_key:
        raise ValueError("empty provider key")
    ambient = sorted(name for name in os.environ if name.startswith("ANTHROPIC_"))
    if ambient:
        raise ValueError("unset ambient Anthropic variables first: " + ", ".join(ambient))
    return anthropic.Anthropic(api_key=api_key, base_url=API_BASE_URL, max_retries=0, timeout=60.0,
                               http_client=httpx2.Client(trust_env=False))


def check_decoding(decoding: Mapping[str, Any]) -> dict[str, Any]:
    """Explicit decoding settings only; sampling parameters are never sent."""
    unknown = set(decoding) - DECODING_KEYS
    if unknown:
        raise ValueError(f"unsupported decoding settings: {sorted(unknown)}")
    if decoding.get("endpoint") != ENDPOINT:
        raise ValueError("endpoint must be 'messages'")
    if decoding.get("thinking") != "disabled":
        # Thinking blocks must be sent back unchanged, which agent/loop.py doesn't do.
        raise ValueError("thinking must be set explicitly to 'disabled'; adaptive thinking is not implemented")
    if decoding.get("effort") not in EFFORTS:
        raise ValueError(f"effort must be set explicitly to one of {sorted(EFFORTS)}")
    limit = decoding.get("max_tokens")
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("max_tokens must be a positive integer")
    return {"thinking": {"type": "disabled"}, "output_config": {"effort": decoding["effort"]}, "max_tokens": limit}


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _no_constant(name: str) -> Any:
    raise ValueError(f"{name} is not JSON")


def _finite(text: str) -> float:
    number = float(text)
    if not math.isfinite(number):
        raise ValueError(f"{text} is not a finite number")
    return number


def _strict_json(text: str) -> Any:
    """Strict JSON: NaN, infinity, and overflowing numbers are rejected, so the
    canonical evidence hash (decision 0009) never meets them."""
    return json.loads(text, parse_constant=_no_constant, parse_float=_finite)


def _tool_input(value: Any) -> Any:
    """A tool input that isn't finite JSON stays a raw string, so the loop's
    parser rejects it without dispatch."""
    try:
        json.dumps(value, allow_nan=False)
    except ValueError:
        return json.dumps(value)
    return value


def to_messages(messages: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Translate the loop's history into Messages API system blocks and messages."""
    system: list[dict[str, Any]] = []
    out: list[dict[str, Any]] = []
    for message in messages:
        role, content = message["role"], message["content"]
        if role == "system":
            if out or not isinstance(content, str):
                raise ValueError("only leading text system messages are supported")
            system.append({"type": "text", "text": content})
            continue
        if isinstance(content, str):
            if role == "assistant" and not content.strip():
                continue  # the API rejects whitespace-only text
            out.append({"role": role, "content": content})
            continue
        if role == "assistant":
            blocks: list[dict[str, Any]] = []
            for b in content:
                if b["type"] == "text":
                    if b["text"].strip():
                        blocks.append({"type": "text", "text": b["text"]})
                elif b["type"] == "tool_use" and isinstance(b["input"], dict):
                    blocks.append({"type": "tool_use", "id": b["id"], "name": b["name"], "input": b["input"]})
                else:
                    raise ValueError("unsupported assistant block")
            out.append({"role": "assistant", "content": blocks})
        elif role == "user" and all(b["type"] == "tool_result" for b in content):
            out.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": b["tool_use_id"],
                 "content": b["content"] if isinstance(b["content"], str) else _json(b["content"])} for b in content]})
        else:
            raise ValueError("unsupported message content")
    if out and out[-1]["role"] == "assistant":
        # A prefill; the loop follows a cut-off reply with a user turn instead.
        raise ValueError("a conversation may not end with an assistant turn")
    return system, out


def to_tools(tool_schemas: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [{"name": t["name"], "description": t["description"], "input_schema": t["input_schema"]} for t in tool_schemas]


def normalize(body: Mapping[str, Any]) -> dict[str, Any]:
    """One Messages response -> the loop's {stop_reason, content} shape.

    A block of any other type (such as thinking) keeps only its type, which the
    loop rejects as malformed.
    """
    content: list[dict[str, Any]] = []
    for block in body["content"]:
        kind = block.get("type")
        if kind == "text":
            content.append({"type": "text", "text": block["text"]})
        elif kind == "tool_use":
            content.append({"type": "tool_use", "id": block["id"], "name": block["name"], "input": _tool_input(block["input"])})
        else:
            content.append({"type": kind if isinstance(kind, str) else "unsupported_block"})
    stop = body.get("stop_reason")
    return {"stop_reason": STOP_REASONS.get(stop, stop), "content": content}


def _count(value: Any) -> Any:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _text(value: Any) -> Any:
    """Strings only, so a malformed field never reaches a record as NaN or an object."""
    return value if isinstance(value, str) else None


def _error_code(body: Any) -> Any:
    error = body.get("error") if isinstance(body, dict) else None
    details = error.get("details") if isinstance(error, dict) else None
    return _text(details.get("error_code")) if isinstance(details, dict) else None


def _hashable(normalized: dict[str, Any]) -> bool:
    """True when the canonical evidence hash (decision 0009) can take it."""
    try:
        json.dumps(normalized, allow_nan=False)
    except (ValueError, RecursionError):
        return False
    return True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class AnthropicMessagesAdapter:
    adapter_version = ADAPTER_VERSION

    def __init__(self, client: anthropic.Anthropic) -> None:
        # The loop owns retries; SDK retries would be invisible attempts.
        self._client = client.with_options(max_retries=0)

    def complete(
        self,
        messages: Sequence[Mapping[str, Any]],
        tool_schemas: Sequence[Mapping[str, Any]],
        decoding: Mapping[str, Any],
        model_request: Mapping[str, Any],
    ) -> dict[str, Any]:
        params = check_decoding(decoding)
        system, chat = to_messages(messages)
        request: dict[str, Any] = {"model": model_request["model"], "messages": chat, **params}
        if system:
            request["system"] = system
        if tool_schemas:
            request["tools"] = to_tools(tool_schemas)
        record: dict[str, Any] = {
            "outcome": "no_model_content", "provider_request_id": None, "model_requested": model_request["model"],
            "model_resolved": None, "provider_fingerprint": None, "raw_response": None,
            "usage": {"input_tokens": None, "output_tokens": None}, "provider_response": None,
            "requested_at": _now(), "completed_at": None, "latency_ms": None, "error": None,
        }
        started = time.monotonic()
        try:
            raw = self._client.messages.with_raw_response.create(**request)
        except (anthropic.APITimeoutError, anthropic.APIConnectionError) as exc:
            record["error"] = {"type": type(exc).__name__, "status": None}
        except anthropic.APIStatusError as exc:
            # Any HTTP error returns no model content. It is returned, not raised,
            # so the loop logs every attempt (SPEC.md Section 9); the loop's two
            # retries then end the trial as an infrastructure failure, unless the
            # code marks a content-policy refusal (decision 0008). The error
            # message is never kept.
            code = _error_code(exc.body)
            record.update(provider_request_id=_text(exc.request_id),
                          error={"type": type(exc).__name__, "status": exc.status_code, "provider_code": code, "provider_type": _text(exc.type)})
            if exc.status_code == 400 and code in CONTENT_POLICY_CODES:
                record["outcome"] = "provider_content_filter"
        else:
            record["provider_request_id"] = _text(raw.request_id)
            text = raw.http_response.text
            try:
                body = _strict_json(text)
                record["provider_response"] = body
            except (ValueError, RecursionError):
                # Unparseable, or JSON carrying NaN or infinity: keep the text.
                record["provider_response"] = text
                try:
                    body = json.loads(text)
                except (ValueError, RecursionError):
                    body = None
            if isinstance(body, dict):
                record["model_resolved"] = _text(body.get("model"))
                usage = body.get("usage") if isinstance(body.get("usage"), dict) else {}
                record["usage"] = {"input_tokens": _count(usage.get("input_tokens")), "output_tokens": _count(usage.get("output_tokens"))}
            if isinstance(body, dict) and isinstance(body.get("content"), list):
                try:
                    normalized = normalize(body)
                except (KeyError, TypeError, AttributeError, RecursionError):
                    normalized = None
                if normalized is None or not _hashable(normalized):
                    # Content came back but its structure is unusable, or it carries
                    # NaN or infinity outside a tool input: a completed model outcome
                    # the loop rejects as malformed, never dispatched.
                    normalized = {"stop_reason": None, "content": [{"type": "unparseable_provider_response"}]}
                record.update(outcome="model_response", raw_response=normalized)
            else:
                record["error"] = {"type": "no_content" if isinstance(body, dict) else "invalid_body", "status": raw.http_response.status_code}
        record["completed_at"] = _now()
        record["latency_ms"] = int((time.monotonic() - started) * 1000)
        return record
