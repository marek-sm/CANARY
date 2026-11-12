"""One-command, read-only replay of a completed W6-T3 development record.

The default is the staged current-schema C2 attack trace. Supplying an events file,
trial directory, or run directory selects that completed record instead. This
module only reads schema-validated JSONL and never imports or calls a provider.

Usage: python -m demo.replay [PATH]
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from demo.trace import render_trace

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS = ROOT / "demo" / "recorded" / "w7-t5"
EVENTS_FILE = "events.jsonl"
DEFAULT_TRIAL = "t0000_dev-001_C2_attack_D0_BASELINE_r1"


def _trial_events(directory: Path) -> Path:
    preferred = directory / DEFAULT_TRIAL / EVENTS_FILE
    if preferred.is_file():
        return preferred
    matches = sorted(directory.glob(f"**/{EVENTS_FILE}"))
    if len(matches) != 1:
        raise FileNotFoundError(f"expected one completed replay record under {directory}")
    return matches[0]


def resolve_events(path: Optional[Path] = None) -> Path:
    """Resolve a completed record without creating or changing run data."""

    if path is None:
        candidate = _trial_events(DEFAULT_RECORDS)
    elif path.is_file():
        candidate = path
    elif (path / EVENTS_FILE).is_file():
        candidate = path / EVENTS_FILE
    else:
        candidate = _trial_events(path)

    if not candidate.is_file():
        raise FileNotFoundError(f"no completed replay record at {candidate}")
    return candidate


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", nargs="?", type=Path, help="events file, trial directory, or run directory")
    args = parser.parse_args(argv)
    print(render_trace(resolve_events(args.path)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
