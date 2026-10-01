"""Paid development smoke: one W5-T1 ticket trial on the real OpenAI model.

Explicitly named, never run by CI, and run by hand only (decision 0005). It
refuses when ``CI`` is set, and when any ambient ``OPENAI_*`` variable could
redirect or reconfigure the client. The key comes only from the explicit env
file, stays in this outer process, and never reaches the tool worker, whose
environment is PATH and LANG only (runner.ticket_slice.worker).

Usage: python -m runner.live_smoke [--env-file .env] [--model gpt-6-luna] [--out DIR]
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from agent import openai_adapter
from runner import mock_slice as base
from runner import ticket_slice
from runner.provider_config import load_api_key

DEFAULT_MODEL = "gpt-6-luna"  # decision 0005 development candidate
DECODING = {"endpoint": "chat_completions", "reasoning_effort": "none"}
DEFAULT_OUT_ROOT = base.REPO_ROOT / "results" / "development" / "live"


def refusal() -> Optional[str]:
    if "CI" in os.environ:
        return "refusing: CI is set; paid calls never run in CI"
    ambient = sorted(name for name in os.environ if name.startswith("OPENAI_"))
    if ambient:
        return "refusing: unset ambient OpenAI variables first: " + ", ".join(ambient)
    return None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--env-file", type=Path, default=base.REPO_ROOT / ".env")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out", type=Path, default=None, help="new output directory")
    args = parser.parse_args(argv)

    reason = refusal()
    if reason:
        print(reason, file=sys.stderr)
        return 2
    try:
        key = load_api_key(args.env_file)
    except (OSError, ValueError):
        print(f"refusing: {args.env_file} must hold exactly one OPENAI_API_KEY= line", file=sys.stderr)
        return 2
    if not key:
        print(f"refusing: OPENAI_API_KEY in {args.env_file} is empty", file=sys.stderr)
        return 2
    openai_adapter.check_decoding(DECODING, has_tools=True)

    adapter = openai_adapter.OpenAIChatAdapter(openai_adapter.build_client(key))
    del key
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out = ticket_slice.run(args.out or DEFAULT_OUT_ROOT / stamp, adapter, model=args.model, decoding=DECODING,
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
    print(f"status:           {result['status']} ({result['termination_reason']})")
    print(f"utility pass:     {result['utility']['pass']}")
    print(f"attempts:         {len(attempts)}")
    print(f"input tokens:     {tokens['input_tokens']}")
    print(f"output tokens:    {tokens['output_tokens']}")
    print(f"model resolved:   {sorted({str(a['model_resolved']) for a in attempts})}")
    print(f"fingerprints:     {sorted({str(a['provider_fingerprint']) for a in attempts})}")
    print("Compare the token totals with the OpenAI usage page (decision 0005, Verification).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
