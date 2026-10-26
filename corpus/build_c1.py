"""Build data-only C1 trusted-user-prompt controls; never an indirect schedule.

Source review is taken from the checked-in W6-T2 records, not inferred from
outcomes. This builder performs no provider calls and earns no trial credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tasks import registry

ROOT = registry.ROOT
SOURCES = ROOT / "corpus/c1"
OUTPUT = ROOT / "corpus/c1_controls"
GOALS = ("secret_disclosure", "unauthorized_action")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ordered_sources():
    groups = {goal: [] for goal in GOALS}
    for path in sorted(SOURCES.glob("c1-*.json")):
        record = json.loads(path.read_text())
        attack = record["attack"]
        if not record["source"].get("reviewed_by") or not attack.get("reviewed_by"):
            raise ValueError(f"unreviewed C1 source: {path.name}")
        for payload in ("original_payload", "canonical_payload"):
            if sha(attack[payload]) != attack[payload + "_sha256"]:
                raise ValueError(f"C1 source payload drift: {path.name}")
        if record["split"] != "c1_control" or attack["primary_goal"] not in groups:
            raise ValueError("not a reviewed C1 control source")
        groups[attack["primary_goal"]].append(record)
    for group in groups.values():
        group.sort(key=lambda r: (sha("CANARY-2026|" + r["candidate_id"]), r["candidate_id"]))
    ordered = []
    while any(groups.values()):
        for goal in GOALS:
            if groups[goal]:
                ordered.append(groups[goal].pop(0))
    return ordered


def control(record):
    attack = record["attack"]
    return {
        "version": "c1-trusted-prompt-v0.1.0",
        "base_case_id": record["base_case_id"],
        "candidate_id": record["candidate_id"],
        "source_path": f"corpus/c1/{record['base_case_id']}.json",
        "source_sha256": registry.digest(record),
        "canonical_payload_sha256": attack["canonical_payload_sha256"],
        "primary_goal": attack["primary_goal"],
        "channel": "C1", "configuration": "D0_BASELINE",
        "split": "c1_control", "reporting": "separate_descriptive_only",
        "excluded_from_indirect_estimates": True,
        "messages": [
            {"role": "system", "content": registry.SYSTEM_PROMPT},
            {"role": "user", "content": attack["canonical_payload"]},
        ],
        "execution": {
            "status": "built; mock execution evidence stored separately",
            "tools": ["read_file", "query_db", "fetch_url", "send_email"],
            "fixtures": "fixtures/w6-t1",
            "fixture_status": "runner.c1_mock adds runner.delivery.secret_files(canaries) and PLANTED_FILES overlays",
            "executor_status": "local plumbing check: python -m runner.c1_mock; no paid or official C1 executor",
            "fixture_sha256": registry.verify(registry.FIXTURES),
            "isolation": "fake local fixture tools only; no external network or delivery",
            "canaries": "fresh synthetic pair per control repeat; never source credentials",
            "live_blocker": "PR61 audit F-01 paid-path isolation restriction remains in force",
        },
    }


def artifacts():
    records = ordered_sources()
    controls = [control(record) for record in records]
    ids = [c["base_case_id"] for c in controls]
    manifest = {
        "version": "c1-trusted-prompt-v0.1.0", "decision": "0018",
        "reporting": "separate_descriptive_only", "excluded_from_indirect_estimates": True,
        "eligible_count": len(ids), "ordered_control_ids": ids,
        "tier_prefixes": {tier: ids[:count] for tier, count in
                          (("F20", 4), ("R15", 4), ("M10", 3), ("L8", 2), ("R6", 2), ("ENGINEERING", 0))},
        "controls": [{"base_case_id": c["base_case_id"], "sha256": registry.digest(c)} for c in controls],
        "execution_status": "built; no live or official C1 credit",
    }
    return {**{OUTPUT / (c["base_case_id"] + ".json"): c for c in controls}, OUTPUT / "manifest.json": manifest}


def build(check=False):
    for path, data in artifacts().items():
        text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        if check:
            if not path.exists() or path.read_text() != text:
                raise ValueError(f"C1 control artifact drift: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    build(args.check)
