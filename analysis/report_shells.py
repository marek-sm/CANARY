"""Render accessible pre-results shells from the estimand manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "paper" / "estimand_manifest.json"
DEFAULT_OUTPUT = ROOT / "paper" / "generated" / "estimand_shells.md"
STATUS = "PRE-RESULTS — NO DATA"


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    """Load and minimally validate the predeclared report-shell manifest."""

    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("manifest_version") != "1.0.0":
        raise ValueError("unsupported estimand manifest version")

    entries = manifest.get("estimands")
    if not isinstance(entries, list) or not entries:
        raise ValueError("estimand manifest must contain a non-empty estimands list")

    required = {"id", "title", "group", "caption", "alt_text", "columns"}
    ids: set[str] = set()
    for entry in entries:
        missing = required - entry.keys()
        if missing:
            raise ValueError(f"{entry.get('id', '<unknown>')} missing {sorted(missing)}")
        if entry["id"] in ids:
            raise ValueError(f"duplicate estimand id: {entry['id']}")
        ids.add(entry["id"])
        if not entry["alt_text"].strip():
            raise ValueError(f"{entry['id']} requires alt text")
        if len(entry["columns"]) < 2:
            raise ValueError(f"{entry['id']} requires a table equivalent")
    return manifest


def _table(columns: list[str]) -> list[str]:
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    empty = "| " + " | ".join([STATUS, *(["—"] * (len(columns) - 1))]) + " |"
    return [header, divider, empty]


def render_manifest(manifest: dict[str, Any]) -> str:
    """Return deterministic Markdown with no empirical values or claims."""

    lines = [
        "# CANARY Generated Estimand Shells",
        "",
        "> **PRE-RESULTS — NO DATA.** These placeholders reserve accessible output",
        "> structure only. They are not empirical results and must be regenerated from",
        "> the frozen sanitized bundle after protocol freeze.",
        "",
        "Every future chart must retain its caption, alt text, exact counts or pair",
        "counts, interval labeling where required, and the table equivalent below.",
    ]

    current_group = None
    for entry in manifest["estimands"]:
        if entry["group"] != current_group:
            current_group = entry["group"]
            lines.extend(["", f"## {current_group}"])

        lines.extend(
            [
                "",
                f"### {entry['title']}",
                "",
                f"- **Estimand/output ID:** `{entry['id']}`",
                f"- **Status:** {STATUS}",
                f"- **Caption scaffold:** {entry['caption']}",
                f"- **Alt-text scaffold:** {entry['alt_text']}",
                "- **Figure shell:** Intentionally empty until generated from frozen evidence.",
                "",
                "#### Table equivalent",
                "",
                *_table(entry["columns"]),
            ]
        )

    lines.extend(
        [
            "",
            "## Accessibility and claim check",
            "",
            "- [ ] Every rendered chart has meaningful final alt text.",
            "- [ ] Every chart has a table equivalent with repeated headers.",
            "- [ ] Color is not the sole carrier of meaning and contrast is checked.",
            "- [ ] Exact numerators/denominators or complete/missing pair counts are shown.",
            "- [ ] Required intervals use the approved conditional cluster-resampling label.",
            "- [ ] Boundary warnings appear when an interval collapses.",
            "- [ ] All values came from the frozen sanitized bundle; none were hand-entered.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    rendered = render_manifest(load_manifest(args.manifest))
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit(f"stale generated shell: {args.output}")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
