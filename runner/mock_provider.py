"""Deterministic canned provider for the no-credit mock slice.

Implements the provider boundary from docs/INTERFACES.md:

    complete(messages, tool_schemas, decoding, model_request) -> model_response

It makes no network call, reads no environment variable, and holds no
credential. Responses depend only on the call index, so repeated runs are
identical.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping, Sequence

PROVIDER_ADAPTER_VERSION = "mock-provider-v0"
MOCK_MODEL_ID = "mock-canned-v0"

# Two canned steps so the runner must persist step 1 before step 2 begins.
# The fictional task text lives in runner/mock_slice.py; nothing here is a
# corpus case or an evaluation candidate.
DEFAULT_SCRIPT: tuple[dict[str, Any], ...] = (
    {
        "stop_reason": "max_tokens",
        "content": [{"type": "text", "text": "The fictional note lists"}],
    },
    {
        "stop_reason": "end_turn",
        "content": [
            {
                "type": "text",
                "text": "The fictional note lists two follow-ups: "
                "restock the demo shelf and reply to ticket T-100.",
            }
        ],
    },
)


class MockProvider:
    def __init__(self, script: Sequence[Mapping[str, Any]] = DEFAULT_SCRIPT) -> None:
        self._script = [copy.deepcopy(dict(r)) for r in script]
        self.calls = 0

    def complete(
        self,
        messages: Sequence[Mapping[str, Any]],
        tool_schemas: Sequence[Mapping[str, Any]],
        decoding: Mapping[str, Any],
        model_request: Mapping[str, Any],
    ) -> dict[str, Any]:
        if self.calls >= len(self._script):
            raise RuntimeError("mock provider script exhausted")
        raw = copy.deepcopy(self._script[self.calls])
        self.calls += 1
        return {
            "outcome": "model_response",
            "provider_request_id": f"mock-req-{self.calls}",
            "model_requested": model_request["model"],
            "model_resolved": MOCK_MODEL_ID,
            "provider_fingerprint": None,
            "raw_response": raw,
            "usage": {"input_tokens": None, "output_tokens": None},
        }
