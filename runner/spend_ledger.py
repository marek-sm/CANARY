"""The spend and pilot ledger behind the paid-run gate, and the project lead's spend cap.

Both live in ``~/.canary/``, outside every checkout and every hashed path. Paid runs
start from a fresh clean checkout, so a ledger inside a clone would restart near zero
and undercount, and a cap in a hashed file would close paid runs on every raise. Only
an argument moves them, never an environment variable. Under pytest the real ones refuse,
however this module was reached, so no test can touch the project lead's actual spend.

Every real paid trial appends here: a ``started`` line before its first provider call,
which counts at one trial's bound until it closes, and a ``finished`` line pricing the
usage its ``provider_attempt`` events recorded at the frozen rates. A trial killed in
between stays at its bound, and an attempt with no recorded usage counts as the largest
request, never as zero. The seed line is the October 10 adapter check, which predates
this ledger.

``runner.paid_run`` reads this before each trial's first call, the live smoke's
included. It refuses when spend plus one trial's bound exceeds the cap, or when trials
would pass SPEC.md Section 9's development ceiling. A missing ledger or cap, or a corrupt
ledger, refuses; nothing here reads as zero. The check is per trial, because the sweep's
whole-run bound far exceeds any cap it would really reach.

Every trial counts in dollars. Only development trials count against the ceiling. Section 9
gives the sweep's and the demo's trials their own lines, and the locked result schema's
``split`` is only ``development`` or ``evaluation``, so rehearsal and stage trials keep
``split: development`` and say what they are in ``analysis_role``, a free string there.

Reconciling with the provider's console stays necessary: this prices only what the
provider reported, and a billed attempt that timed out reports nothing, so the console
is the only record of it.

The cap's value is the project lead's. Set it slightly below the workspace limit: a
billed timeout the ledger can't see could otherwise reach the provider's limit first,
which turns each remaining trial into an infrastructure failure instead of a refusal.

Usage:
  python -m runner.spend_ledger init [--ledger PATH]
  python -m runner.spend_ledger set-cap USD [--cap PATH]
  python -m runner.spend_ledger show [--ledger PATH] [--cap PATH]
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from agent.loop import MAX_STEPS
from runner.mock_slice import append_jsonl, utc_now, validator

SCHEMA = "spend_ledger"
DEVELOPMENT_CEILING = 120  # SPEC.md Section 9, including the October 10 check
OCTOBER_10_CHECK = {"cost_usd": 0.00014, "development_trials": 1}  # STATUS.md, the evidence snapshot
DEMO_ROLES = ("demo_rehearsal", "demo_stage")  # analysis_role values outside the development ceiling

# TODO(#70): take the rates and the bound from analysis/price_bound.py once #70 lands.
INPUT_USD_PER_TOKEN = 0.10 / 1_000_000  # decision 0010's list prices
OUTPUT_USD_PER_TOKEN = 0.50 / 1_000_000
LONG_INPUT_USD_PER_TOKEN = 0.50 / 1_000_000
LONG_OUTPUT_USD_PER_TOKEN = 2.50 / 1_000_000
LONG_PROMPT_TOKENS = 100_000
MAX_TOKENS = 4096  # decision 0010 item 6
LARGEST_INPUT_TOKENS = 3000 + (MAX_STEPS - 1) * (MAX_TOKENS + 3000)  # decision 0026 item 6
REQUEST_BOUND_USD = LARGEST_INPUT_TOKENS * INPUT_USD_PER_TOKEN + MAX_TOKENS * OUTPUT_USD_PER_TOKEN
TRIAL_BOUND_USD = MAX_STEPS * REQUEST_BOUND_USD  # decision 0025 item 11


class LedgerError(ValueError):
    """The ledger or the cap is missing or corrupt, so spend is unknown."""


def _password_home() -> Path:
    """The account's home from the password database, which no environment variable moves."""
    import pwd

    return Path(pwd.getpwuid(os.getuid()).pw_dir)


def _account_home() -> Path:
    """The real home, refused under pytest, including in a child process it starts with its
    environment intact, and in this module run a second time. tests/conftest.py stands in."""
    if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
        raise LedgerError("refusing the real ~/.canary under pytest; pass a path, or use tests/conftest.py's stand-in")
    return _password_home()


def ledger_path(path: Optional[Path] = None) -> Path:
    return path or _account_home() / ".canary" / "spend_ledger.jsonl"


def cap_path(path: Optional[Path] = None) -> Path:
    return path or _account_home() / ".canary" / "spend_cap.json"


def init(path: Optional[Path] = None) -> Path:
    """Create the ledger, seeded with the October 10 check. It never overwrites one."""
    path = ledger_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise LedgerError(f"{path} already exists")
    path.touch()
    append_jsonl(path, {"schema_version": "1.0.0", "phase": "seed", "recorded_at": utc_now(), **OCTOBER_10_CHECK}, SCHEMA)
    return path


def read(path: Optional[Path] = None) -> list[dict[str, Any]]:
    path = ledger_path(path)
    if not path.exists():
        raise LedgerError(f"no spend ledger at {path}; create it with python -m runner.spend_ledger init")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise LedgerError(f"the spend ledger at {path} is corrupt: {exc}") from exc
    if text and not text.endswith("\n"):
        raise LedgerError(f"the spend ledger at {path} is corrupt: a kill cut off its last line. To repair it, delete that "
                          "partial line by hand, then reconcile with the provider's console, because the start or "
                          "finish it held is lost")
    try:
        lines = [json.loads(line) for line in text.splitlines()]
        for line in lines:
            validator(SCHEMA).validate(line)
    except Exception as exc:
        raise LedgerError(f"the spend ledger at {path} is corrupt: {exc}") from exc
    if not lines:
        raise LedgerError(f"the spend ledger at {path} is corrupt: it has no seed line")
    started, finished = set(), set()
    for index, line in enumerate(lines):
        phase, entry = line["phase"], line.get("invocation_id")
        if (phase == "seed") != (index == 0):
            raise LedgerError(f"the spend ledger at {path} is corrupt: its seed must be its first line and only there")
        if phase == "started" and entry in started:
            raise LedgerError(f"the spend ledger at {path} is corrupt: {entry} started twice")
        if phase == "finished" and (entry not in started or entry in finished):
            raise LedgerError(f"the spend ledger at {path} is corrupt: {entry} finished without one start")
        (started if phase == "started" else finished).add(entry)
    return lines


def counts_against_ceiling(split: str, analysis_role: Optional[str]) -> bool:
    return split == "development" and analysis_role not in DEMO_ROLES


def totals(lines: Iterable[Mapping[str, Any]]) -> tuple[float, int]:
    """Spend so far, every trial's, and the development trials started so far."""
    lines = list(lines)
    finished = {line["invocation_id"]: line["cost_usd"] for line in lines if line["phase"] == "finished"}
    spend, trials = 0.0, 0
    for line in lines:
        if line["phase"] == "seed":
            spend, trials = spend + line["cost_usd"], trials + line["development_trials"]
        elif line["phase"] == "started":
            spend += finished.get(line["invocation_id"], line["bound_usd"])
            trials += line["new_trial"] and counts_against_ceiling(line["split"], line["analysis_role"])
    return spend, trials


def read_cap(path: Optional[Path] = None) -> float:
    path = cap_path(path)
    try:
        cap = json.loads(path.read_text(encoding="utf-8"))["cap_usd"]
    except FileNotFoundError as exc:
        raise LedgerError(f"no spend cap at {path}; the project lead sets it with python -m runner.spend_ledger "
                          "set-cap USD, slightly below the workspace limit") from exc
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise LedgerError(f"the spend cap at {path} is corrupt: {exc}") from exc
    if isinstance(cap, bool) or not isinstance(cap, (int, float)) or not 0 < cap < math.inf:
        raise LedgerError(f"the spend cap at {path} is corrupt: {cap!r}")
    return float(cap)


def cap_or_none(path: Optional[Path] = None) -> Optional[float]:
    """The cap to echo into a run's provenance. A mock run needs none, so this never refuses."""
    try:
        return read_cap(path)
    except LedgerError:
        return None


def set_cap(usd: float, path: Optional[Path] = None) -> Path:
    path = cap_path(path)
    if isinstance(usd, bool) or not 0 < usd < math.inf:
        raise LedgerError(f"a spend cap is a positive number of dollars, not {usd!r}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps({"cap_usd": usd}) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    return path


def refusal(*, new_trials: int = 1, ledger: Optional[Path] = None, cap: Optional[Path] = None) -> Optional[str]:
    """Why the next trial can't start, or ``None``. ``new_trials`` is how many development
    trials this run still adds; a resumed trial adds none but still spends."""
    try:
        spent, trials = totals(read(ledger))
        limit = read_cap(cap)
    except LedgerError as exc:
        return str(exc)
    if trials + new_trials > DEVELOPMENT_CEILING:
        return (f"{trials} development trials so far plus {new_trials} would pass SPEC.md Section 9's ceiling of "
                f"{DEVELOPMENT_CEILING}")
    if spent + TRIAL_BOUND_USD > limit:
        return f"spend ${spent:.6f} plus one trial's bound ${TRIAL_BOUND_USD:.6f} exceeds the ${limit:.2f} spend cap"
    return None


def start(provider: Any, logical_trial_id: str, *, new_trial: bool = True, split: str = "development",
          analysis_role: Optional[str] = None, path: Optional[Path] = None) -> str:
    """Append a paid trial's start before its first call, under the labels its result carries."""
    read(path)  # a missing or corrupt ledger stops the trial here
    invocation_id = uuid.uuid4().hex
    append_jsonl(ledger_path(path), {
        "schema_version": "1.0.0", "phase": "started", "recorded_at": utc_now(), "invocation_id": invocation_id,
        "logical_trial_id": logical_trial_id, "provider_adapter": str(getattr(provider, "adapter_version", type(provider).__name__)),
        "split": split, "analysis_role": analysis_role, "new_trial": new_trial, "bound_usd": TRIAL_BOUND_USD,
        "cap_usd": cap_or_none(),
    }, SCHEMA)
    return invocation_id


def _recorded(usage: Optional[Mapping[str, Any]]) -> bool:
    counts = (usage or {}).get("input_tokens"), (usage or {}).get("output_tokens")
    return all(isinstance(count, int) and not isinstance(count, bool) for count in counts)


def attempt_usd(usage: Optional[Mapping[str, Any]]) -> float:
    """One attempt's price, or the largest request's when its usage wasn't recorded."""
    if not _recorded(usage):
        return REQUEST_BOUND_USD
    if usage["input_tokens"] > LONG_PROMPT_TOKENS:
        return usage["input_tokens"] * LONG_INPUT_USD_PER_TOKEN + usage["output_tokens"] * LONG_OUTPUT_USD_PER_TOKEN
    return usage["input_tokens"] * INPUT_USD_PER_TOKEN + usage["output_tokens"] * OUTPUT_USD_PER_TOKEN


def finish(invocation_id: str, events: Iterable[Mapping[str, Any]], *, path: Optional[Path] = None) -> None:
    """Close a trial with the priced usage of the attempts this invocation made."""
    attempts = [event["payload"].get("usage") for event in events if event["event_type"] == "provider_attempt"]
    known = [usage for usage in attempts if _recorded(usage)]
    append_jsonl(ledger_path(path), {
        "schema_version": "1.0.0", "phase": "finished", "recorded_at": utc_now(), "invocation_id": invocation_id,
        "attempts": len(attempts), "input_tokens": sum(usage["input_tokens"] for usage in known),
        "output_tokens": sum(usage["output_tokens"] for usage in known),
        "unknown_usage_attempts": len(attempts) - len(known), "cost_usd": sum(map(attempt_usd, attempts)),
    }, SCHEMA)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    init_parser = sub.add_parser("init", help="create the ledger, seeded with the October 10 check")
    init_parser.add_argument("--ledger", type=Path)
    cap_parser = sub.add_parser("set-cap", help="set the cap, slightly below the workspace limit")
    cap_parser.add_argument("usd", type=float)
    cap_parser.add_argument("--cap", type=Path)
    show_parser = sub.add_parser("show", help="print spend, trials, and the cap")
    show_parser.add_argument("--ledger", type=Path)
    show_parser.add_argument("--cap", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            print(f"wrote {init(args.ledger)}")
        elif args.command == "set-cap":
            print(f"wrote {set_cap(args.usd, args.cap)}")
        else:
            spent, trials = totals(read(args.ledger))
            print(f"spend ${spent:.6f}; {trials} of {DEVELOPMENT_CEILING} development trials; cap ${read_cap(args.cap):.2f}")
            print(f"seeded with ${OCTOBER_10_CHECK['cost_usd']}; reconcile with the provider's console")
    except LedgerError as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
