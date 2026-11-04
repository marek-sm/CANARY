"""One digest over what a grid's trials found, so two runs can be compared (prototype).

For ``make sweep-container-check``: an uninterrupted mock grid and one killed and
resumed must find the same thing. The digest covers each trial's identity,
status, termination reason, security and utility blocks, and every tool event's
facts. It leaves out what legitimately differs between runs: timestamps, event
and attempt IDs, and canary values. It also reports every ``container_digest``
the results carry.

Usage: python docker/sweep/outcome_digest.py RUN_DIR [RUN_DIR ...]
Prints one JSON line per run directory.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

KEEP = ("logical_trial_id", "base_case_id", "channel", "condition", "configuration", "run_index", "status",
        "termination_reason", "security", "utility")
TOOL_FACTS = ("tool_name", "dispatched", "execution_succeeded", "effect_observed", "sink_received", "authorized",
              "blocked")


def _scrub(value, canaries):
    if isinstance(value, dict):
        return {k: _scrub(v, canaries) for k, v in sorted(value.items()) if not k.endswith("_at")}
    if isinstance(value, list):
        return [_scrub(v, canaries) for v in value]
    if isinstance(value, str):
        for canary in canaries:
            value = value.replace(canary, "<canary>")
    return value


def summarize(run_dir: Path) -> dict:
    trials, images = {}, set()
    for results_path in sorted(run_dir.glob("*/results.jsonl")):
        for line in results_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            images.add(record["run_metadata"].get("container_digest"))
            canaries = [c for c in json.dumps(record.get("canaries", {})).split('"') if len(c) >= 12]
            kept = {key: record.get(key) for key in KEEP}
            kept["tool_events"] = [{key: event.get(key) for key in TOOL_FACTS}
                                   for event in record.get("tool_events") or []]
            trials[results_path.parent.name] = _scrub(kept, canaries)
    blob = json.dumps(trials, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"run": str(run_dir), "trials": len(trials), "outcome_sha256": hashlib.sha256(blob).hexdigest(),
            "container_digests": sorted(map(str, images))}


def main(argv: list[str]) -> int:
    for run in argv:
        print(json.dumps(summarize(Path(run)), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
