"""Paid development smoke: one W5-T1 ticket trial on a real provider model.

Explicitly named, never run by CI, and run by hand only (decision 0010). The
default provider is the development candidate; ``--provider openai`` runs the
declared fallback. It refuses when ``CI`` is set, and when any ambient
``ANTHROPIC_*`` or ``OPENAI_*`` variable could redirect or reconfigure a client.
The key comes only from the explicit env file, stays in this outer process,
and never reaches the tool worker, whose environment is PATH and LANG only
(runner.ticket_slice.worker).

Usage: python -m runner.live_smoke [--provider anthropic|openai] [--env-file .env] [--model ID] [--out DIR]
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from agent import anthropic_adapter, openai_adapter
from runner import mock_slice as base
from runner import ticket_slice
from runner.provider_config import load_api_key

DEFAULT_PROVIDER = "anthropic"
# Each adapter module is looked up when the command runs, so tests can replace build_client.
PROVIDERS = {
    # Decision 0010 development candidate.
    "anthropic": {
        "module": anthropic_adapter, "adapter": anthropic_adapter.AnthropicMessagesAdapter,
        "check": anthropic_adapter.check_decoding, "model": "claude-haiku-5-5",
        "decoding": {"endpoint": "messages", "thinking": "disabled", "effort": "medium", "max_tokens": 4096},
        "key": "ANTHROPIC_API_KEY", "usage_page": "the Claude Console usage page",
        # Claude Haiku 5.5's price rises for prompts over 100,000 tokens.
        "price_step_tokens": 100_000,
    },
    # Decision 0010 declared fallback (decision 0005's candidate).
    "openai": {
        "module": openai_adapter, "adapter": openai_adapter.OpenAIChatAdapter,
        "check": lambda decoding: openai_adapter.check_decoding(decoding, has_tools=True), "model": "gpt-6-luna",
        "decoding": {"endpoint": "chat_completions", "reasoning_effort": "none"},
        "key": "OPENAI_API_KEY", "usage_page": "the OpenAI usage page", "price_step_tokens": None,
    },
}
DEFAULT_OUT_ROOT = base.REPO_ROOT / "results" / "development" / "live"


def refusal() -> Optional[str]:
    if "CI" in os.environ:
        return "refusing: CI is set; paid calls never run in CI"
    ambient = sorted(name for name in os.environ if name.startswith(("ANTHROPIC_", "OPENAI_")))
    if ambient:
        return "refusing: unset ambient provider variables first: " + ", ".join(ambient)
    return None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--provider", choices=sorted(PROVIDERS), default=DEFAULT_PROVIDER)
    parser.add_argument("--env-file", type=Path, default=base.REPO_ROOT / ".env")
    parser.add_argument("--model", default=None, help="defaults to the provider's decision 0010 model")
    parser.add_argument("--out", type=Path, default=None, help="new output directory")
    args = parser.parse_args(argv)
    provider = PROVIDERS[args.provider]
    model = args.model or provider["model"]

    reason = refusal()
    if reason:
        print(reason, file=sys.stderr)
        return 2
    try:
        key = load_api_key(args.env_file, provider["key"])
    except (OSError, ValueError):
        print(f"refusing: {args.env_file} must hold exactly one {provider['key']}= line", file=sys.stderr)
        return 2
    if not key:
        print(f"refusing: {provider['key']} in {args.env_file} is empty", file=sys.stderr)
        return 2
    provider["check"](provider["decoding"])

    adapter = provider["adapter"](provider["module"].build_client(key))
    del key
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ticket_slice.run(args.out or DEFAULT_OUT_ROOT / stamp, adapter, model=model, decoding=provider["decoding"],
                           experiment_id=f"live-dev-{stamp}", analysis_role="excluded_development")

    events = base.read_jsonl(out / base.EVENTS_FILE, "event")
    [result] = base.read_jsonl(out / base.RESULTS_FILE, "result")
    attempts = [e["payload"] for e in events if e["event_type"] == "provider_attempt"]
    responses = [a for a in attempts if a["outcome"] == "model_response"]

    def total(kind):
        values = [(a.get("usage") or {}).get(kind) for a in responses]
        return "unknown" if any(v is None for v in values) else sum(values)  # never print unknown as 0

    tokens = {kind: total(kind) for kind in ("input_tokens", "output_tokens")}
    print(f"output:           {out}")
    print(f"provider:         {args.provider}")
    print(f"status:           {result['status']} ({result['termination_reason']})")
    print(f"utility pass:     {result['utility']['pass']}")
    print(f"attempts:         {len(attempts)}")
    print(f"input tokens:     {tokens['input_tokens']}")
    print(f"output tokens:    {tokens['output_tokens']}")
    print(f"model resolved:   {sorted({str(a['model_resolved']) for a in attempts})}")
    print(f"fingerprints:     {sorted({str(a['provider_fingerprint']) for a in attempts})}")
    step = provider["price_step_tokens"]
    if step:
        prompts = [(a.get("usage") or {}).get("input_tokens") for a in responses]
        if any(n is not None and n > step for n in prompts):
            print(f"warning: a prompt exceeded {step:,} tokens, where the higher long-prompt price applies")
        elif any(n is None for n in prompts):
            print(f"warning: a prompt's token count is unknown, so whether it crossed {step:,} tokens is unknown")
    print(f"Compare the token totals with {provider['usage_page']} (decision 0010, Verification).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
