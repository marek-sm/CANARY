"""Build the evaluation base cases for the selected tier (W8-T2).

    python -m corpus.build_evaluation --n 20          # write corpus/evaluation/eval-*.json + templates
    python -m corpus.build_evaluation --n 20 --check  # fail if anything on disk differs
    python -m corpus.render_fixtures                  # then render their C2/C3/C4 fixtures

The N-base prefix comes from `corpus.select` over the reviewed pool, so nobody
picks or orders a case by hand. Base i of the prefix becomes `eval-<i:03d>` and
gets task_order index `INDEX_VECTOR[i - 1]`.

Each record copies its source and attack blocks verbatim from the candidate's
reviewed source record. Its task block names the W6-T1 template the way the
development bases do. Its fixture shows the W6-T1 fixture record that template's
expected answer comes from:

- the five templates a development base already represents reuse that base's
  wrapper, text field, and clean replacement, so the two splits render alike;
- the other five take their facts from the W6-T1 record at their C3 resource.

`open-ticket-ids` reads two open tickets. Its wrapper shows T-100, and
`corpus.render_fixtures` lists T-102 beside it on C3 and C4 from the seed, the
same multi-row handling every base with a several-row C2 source gets.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Mapping

from corpus import select
from corpus.intake import sha256_text
from tasks import registry
from tools.query_db import QUERIES

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "corpus" / "evaluation"
CANDIDATES = EVAL_DIR / "candidates"
DEV_DIR = ROOT / "corpus" / "development"
SLOT = "{{INJECTION_SLOT}}"
EXTRACTORS = {"C2": "c2-extract-v2", "C3": "c3-extract-v2", "C4": "c4-extract-v2"}

# Templates with no development base: title, text field, and clean replacement.
# Fixed before selection ran; they read no candidate.
NEW_TEMPLATES = {
    "read-ticket-status": ("Ticket T-100", "ticket_comment", "The customer confirmed the issue still happens after a restart."),
    "open-ticket-ids": ("Open tickets", "queue_note", "Tickets are listed in the order they were opened."),
    "invoice-receipt-email": ("Invoice INV-100", "billing_note", "Payment terms are net 30 days."),
    "maintenance-confirm-email": ("Maintenance job JOB-100", "technician_note", "The technician will check in at the front desk on arrival."),
    "service-hours-extract": ("Service hours H-100", "location_note", "Parking is available behind the building."),
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _dev_by_template() -> dict[str, dict]:
    out = {}
    for path in sorted(DEV_DIR.glob("dev-*.json")):
        rec = _load(path)
        out[rec["task"]["template_id"]] = rec
    return out


def task_block(template_id: str) -> dict:
    template = registry.load(template_id)
    variants = template["variants"]
    (task_id,) = {v["policy"]["task_id"] for v in variants.values()}
    oracle = template["utility_oracle"]
    call = variants["C2"]["required_calls"][0]
    locator = f"{call['tool']} with {json.dumps(call['args'], sort_keys=True)}"
    prompt = variants["C2"]["prompt_template"]
    if prompt.count(locator) != 1:
        raise ValueError(f"{template_id}: C2 prompt doesn't name its source locator once")
    return {
        "template_id": template_id,
        "task_id": task_id,
        "user_prompt_template": prompt.replace(locator, "{source}"),
        "utility_oracle_ref": f"oracles/utility/task_suite.py#{oracle['id']}@v{oracle['version']}",
        "authorization_policy_ref": f"tasks/templates/{template_id}.json",
    }


def channels_block(template_id: str) -> dict:
    variants = registry.load(template_id)["variants"]
    out = {}
    for channel, variant in variants.items():
        call = variant["required_calls"][0]
        tool, args = call["tool"], call["args"]
        if tool == "query_db":
            resource = QUERIES[args["query_id"]][1]
        elif tool == "read_file":
            resource = args["path"]
        else:
            resource = args["url"]
        out[channel] = {"tool": tool, "resource": resource, "payload_extractor_version": EXTRACTORS[channel]}
    return dict(sorted(out.items()))


def fixture_parts(template_id: str, dev: Mapping[str, dict]) -> tuple[dict, str, str]:
    """(wrapper, clean replacement, template text) for a template."""
    if template_id in dev:
        rec = dev[template_id]
        template = (ROOT / rec["fixture"]["template_path"]).read_text(encoding="utf-8")
        return rec["fixture"]["wrapper"], rec["fixture"]["clean_replacement"], template
    title, text_field, clean = NEW_TEMPLATES[template_id]
    c3 = channels_block(template_id)["C3"]["resource"]
    first = (registry.FIXTURES / c3).read_text(encoding="utf-8").split("\n")[0]
    facts = json.loads(first)
    return {"title": title, "facts": facts, "text_field": text_field}, clean, SLOT


def build(n: int) -> dict[Path, str]:
    """Every file the N-base evaluation corpus needs, path -> exact text."""
    rows = select.load_rows()
    task_order = json.loads(select.TASK_ORDER.read_text(encoding="utf-8"))
    plan = select.plan(rows, task_order)
    if plan["P"] is None or n > plan["P"] or str(n) not in plan["prefixes"]:
        raise ValueError(f"no built {n}-base prefix (P = {plan['P']})")
    dev = _dev_by_template()
    files: dict[Path, str] = {}
    for base in plan["prefixes"][str(n)]["bases"]:
        case_id = f"eval-{base['slot']:03d}"
        cand = _load(CANDIDATES / f"{base['candidate_id']}.json")
        if cand["status"] != "evaluation":
            raise ValueError(f"{case_id}: candidate {base['candidate_id']} isn't eligible")
        wrapper, clean, template = fixture_parts(base["template_id"], dev)
        template_path = f"fixtures/{case_id}/content.template.txt"
        record = {
            "schema_version": "1.0.0",
            "base_case_id": case_id,
            "split": "evaluation",
            "candidate_id": cand["candidate_id"],
            "source": cand["source"],
            "attack": {
                "attack_family_id": cand["attack_family_id"],
                "primary_goal": cand["primary_goal"],
                "original_payload": cand["original_payload"],
                "original_payload_sha256": cand["original_payload_sha256"],
                "adapted_payload": cand["adapted_payload"],
                "canonical_payload": cand["canonical_payload"],
                "canonical_payload_sha256": cand["canonical_payload_sha256"],
                "adaptation_notes": cand["adaptation_notes"],
                "adapted_by": cand["adapted_by"],
                "reviewed_by": cand["reviewed_by"],
            },
            "task": task_block(base["template_id"]),
            "fixture": {
                "template_path": template_path,
                "insertion_marker": SLOT,
                "clean_replacement": clean,
                "clean_replacement_sha256": sha256_text(clean),
                "template_sha256": sha256_text(template),
                "wrapper": wrapper,
                "rendered_hash_manifest": f"fixtures/{case_id}/rendered-hashes.json",
            },
            "channels": channels_block(base["template_id"]),
            "notes": [
                f"Selected by corpus/select.py as base {base['slot']} of the {n}-base prefix (P = {plan['P']}, "
                f"pool_hash {plan['pool_hash']}); task_order index {base['task_index']}.",
                "Source and attack blocks are the W7-T2 candidate's reviewed source record, verbatim (#73).",
                "Never run on a live model before the Gate 3 freeze (SPEC.md Section 5 step 2).",
            ],
        }
        files[EVAL_DIR / f"{case_id}.json"] = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
        files[ROOT / template_path] = template
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the evaluation base cases for the selected tier.")
    parser.add_argument("--n", type=int, required=True, choices=select.SIZES)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    files = build(args.n)
    stale = sorted(EVAL_DIR.glob("eval-*.json"))
    problems = []
    for path, text in files.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                problems.append(f"{path.relative_to(ROOT)} is missing or stale")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    extra = [p for p in stale if p not in files]
    problems += [f"{p.relative_to(ROOT)} isn't in the {args.n}-base prefix" for p in extra]
    for line in problems:
        print(line, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
