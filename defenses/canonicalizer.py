"""The one request canonicalizer (W6-T4).

Runs exactly once per model tool call, before authorization. The object it
returns is the object that is logged, authorized, and, if allowed, dispatched
(SPEC.md Section 7). Nothing downstream reinterprets raw arguments.

Normalization rules are the ones in docs/DEFENSES_AND_POLICY.md Section 1,
"Normalization the canonicalizer must apply". Allowlists are exact matches, so
the policy is only as strong as this module.

Canonicalization failure is reserved for a call that cannot be represented at
all: an unknown tool, malformed arguments, a NUL byte, an empty path, or a URL
that cannot be parsed. A syntactically valid request for a resource outside the
fixture root or the allowlist is NOT a failure. It is canonicalized, evaluated,
and denied (SPEC.md Section 7, decision 0004 item 4).
"""

from __future__ import annotations

import math
import posixpath
import re
import unicodedata
from types import MappingProxyType
from typing import Any, Mapping
from urllib.parse import SplitResult, urlsplit, urlunsplit

from defenses.interfaces import TOOL_ARGUMENTS, TOOLS, CanonicalRequest

NORMALIZER_VERSION = "request-canonicalizer-v0.1.0"

_DEFAULT_PORTS = {"http": 80, "https": 443}
_UNRESERVED = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
_PERCENT = re.compile(r"%([0-9A-Fa-f]{2})")


class CanonicalizationError(ValueError):
    """The call cannot be represented as a canonical request."""


def _text(value: str) -> str:
    """NFC, with CRLF and CR folded to LF."""
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))


def _percent(component: str) -> str:
    """Decode percent-encoded unreserved characters and uppercase the remaining hex digits."""

    def fix(match: re.Match[str]) -> str:
        char = chr(int(match.group(1), 16))
        return char if char in _UNRESERVED else "%" + match.group(1).upper()

    return _PERCENT.sub(fix, component)


def _path(value: str) -> str:
    text = _text(value)
    if not text or "\x00" in text:
        raise CanonicalizationError("unrepresentable path")
    # POSIX normalization resolves '.' and duplicate slashes and keeps an escaping
    # '..' or a leading '/' so the evaluators can deny it (decision 0004 item 4).
    normalized = posixpath.normpath(text)
    if normalized.startswith("//"):
        normalized = "/" + normalized.lstrip("/")
    return normalized


def _url(value: str) -> str:
    text = _text(value)
    if not text or "\x00" in text:
        raise CanonicalizationError("unrepresentable url")
    try:
        parts = urlsplit(text)
        port = parts.port
    except ValueError as exc:
        raise CanonicalizationError(f"unrepresentable url: {exc}") from exc
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    if ":" in host:  # IPv6 literal
        host = f"[{host}]"
    netloc = host
    if port is not None and _DEFAULT_PORTS.get(scheme) != port:
        netloc = f"{host}:{port}"
    if parts.username is not None:
        userinfo = parts.username + (f":{parts.password}" if parts.password is not None else "")
        netloc = f"{userinfo}@{netloc}"
    path = _percent(parts.path) or "/"
    query = _percent(parts.query)
    return urlunsplit(SplitResult(scheme, netloc, path, query, ""))  # fragment removed


def _email_to(value: str) -> str:
    text = _text(value).strip().lower()
    if "\x00" in text:
        raise CanonicalizationError("unrepresentable recipient")
    return text


def _json_value(value: Any) -> Any:
    """NFC every string in a JSON value and freeze containers; reject non-JSON."""
    if isinstance(value, Mapping):
        if not all(isinstance(k, str) for k in value):
            raise CanonicalizationError("argument object keys must be strings")
        frozen: dict[str, Any] = {}
        for key, item in value.items():
            name = _text(key)
            if name in frozen:
                # Two distinct keys that normalize to one would silently drop a value, and
                # input order would then decide which survives (and the authorization verdict).
                raise CanonicalizationError("argument object keys collide after normalization")
            frozen[name] = _json_value(item)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_json_value(v) for v in value)
    if isinstance(value, str):
        return _text(value)
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalizationError("non-finite number")
        return value
    raise CanonicalizationError(f"argument is not a JSON value: {type(value).__name__}")


def thaw_json(value: Any) -> Any:
    """Plain dicts and lists at every depth: the inverse of the freezing in ``_json_value``.

    Use at an evidence boundary (event payloads, JSON files) where read-only containers
    such as ``MappingProxyType`` are not JSON serializable.
    """
    if isinstance(value, Mapping):
        return {k: thaw_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [thaw_json(v) for v in value]
    return value


def canonicalize_arguments(tool: str, raw_args: Any) -> Mapping[str, Any]:
    """Return read-only normalized arguments for one tool, or raise ``CanonicalizationError``."""
    if tool not in TOOLS:
        raise CanonicalizationError(f"unknown tool: {tool!r}")
    if not isinstance(raw_args, Mapping) or set(raw_args) != set(TOOL_ARGUMENTS[tool]):
        raise CanonicalizationError("arguments do not match the tool's required names")

    if tool == "read_file":
        _require_str(raw_args, "path")
        return MappingProxyType({"path": _path(raw_args["path"])})
    if tool == "fetch_url":
        _require_str(raw_args, "url")
        return MappingProxyType({"url": _url(raw_args["url"])})
    if tool == "query_db":
        _require_str(raw_args, "query_id")
        params = raw_args["params"]
        if not isinstance(params, Mapping):
            raise CanonicalizationError("query_db.params must be an object")
        query_id = _text(raw_args["query_id"])
        if not query_id or "\x00" in query_id:
            raise CanonicalizationError("unrepresentable query_id")
        return MappingProxyType({"query_id": query_id, "params": _json_value(params)})
    # send_email
    for name in ("to", "subject", "body"):
        _require_str(raw_args, name)
    return MappingProxyType(
        {
            "to": _email_to(raw_args["to"]),
            "subject": _text(raw_args["subject"]),
            "body": _text(raw_args["body"]),
        }
    )


def _require_str(args: Mapping[str, Any], name: str) -> None:
    if not isinstance(args[name], str):
        raise CanonicalizationError(f"{name} must be a string")


def canonicalize_request(
    tool: str, raw_args: Any, logical_trial_id: str, step: int, call_id: str | None = None
) -> CanonicalRequest:
    """Build the single immutable ``CanonicalRequest`` for one model tool call."""
    args = canonicalize_arguments(tool, raw_args)
    return CanonicalRequest(
        call_id=call_id or f"{logical_trial_id}:step{step}:call1",
        logical_trial_id=logical_trial_id,
        step=step,
        tool=tool,
        normalized_args=args,
        normalizer_version=NORMALIZER_VERSION,
    )


def canonicalize_tool_use(block: Mapping[str, Any], logical_trial_id: str, step: int) -> CanonicalRequest:
    """Canonicalize one provider ``tool_use`` content block.

    The block must have exactly ``type``, ``id``, ``name``, and ``input``, and a
    non-empty string provider id; anything else cannot be represented.
    """
    if set(block) != {"type", "id", "name", "input"} or block.get("type") != "tool_use":
        raise CanonicalizationError("unsupported tool_use block shape")
    if not isinstance(block["id"], str) or not block["id"]:
        raise CanonicalizationError("invalid call id")
    if not isinstance(block["name"], str):
        raise CanonicalizationError("invalid tool name")
    return canonicalize_request(block["name"], block["input"], logical_trial_id, step)
