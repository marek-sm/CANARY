"""The committed task order (decision 0014; SPEC.md Section 5 step 8).

    python -m tasks.task_order          # write tasks/task_order.json
    python -m tasks.task_order --check  # fail if the committed file differs

The ten frozen templates are numbered by category: legitimate high-risk takes
indices 1, 4, 7, and 9; read/query 2, 6, and 10; local-web extraction 3 and 8;
and cross-source comparison 5. Within a category, the template with the lowest
``SHA256("CANARY-2026-task|" + template_id)`` takes the lowest index. The order
reads only template IDs and categories, never a task's content or any result.
Once committed, a template keeps its ID and index through any later fix.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from tasks import registry

ORDER_FILE = registry.ROOT / "tasks" / "task_order.json"
SALT = "CANARY-2026-task|"
INDICES = {
    "legitimate_high_risk": (1, 4, 7, 9),
    "read_query": (2, 6, 10),
    "local_web_extraction": (3, 8),
    "cross_source_comparison": (5,),
}


def task_hash(template_id: str) -> str:
    return hashlib.sha256((SALT + template_id).encode("utf-8")).hexdigest()


def compute(templates: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """The task order for these templates, refused unless the category counts fit."""
    order = []
    for category, indices in INDICES.items():
        ids = sorted((t["template_id"] for t in templates.values() if t["category"] == category), key=task_hash)
        if len(ids) != len(indices):
            raise ValueError(f"{category}: {len(ids)} templates for {len(indices)} indices")
        order += [{"index": i, "template_id": tid, "category": category} for i, tid in zip(indices, ids)]
    if len(order) != len(templates):
        raise ValueError("a template has a category outside the task order")
    return {
        "rule": "decision 0014; SPEC.md Section 5 step 8",
        "salt": SALT,
        "order": sorted(order, key=lambda entry: entry["index"]),
    }


def render(templates: Mapping[str, Mapping[str, Any]]) -> str:
    return json.dumps(compute(templates), indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    text = render(registry.templates())
    if args.check:
        if not ORDER_FILE.exists() or ORDER_FILE.read_text(encoding="utf-8") != text:
            print(f"{ORDER_FILE.name} is missing or stale", file=sys.stderr)
            return 1
        return 0
    if ORDER_FILE.exists() and ORDER_FILE.read_text(encoding="utf-8") != text:
        # Decision 0014: a committed template keeps its index, so never rewrite it.
        print(f"{ORDER_FILE.name} differs from the rule; refusing to overwrite it", file=sys.stderr)
        return 1
    ORDER_FILE.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
