"""Generate the dormant ENGINEERING no-estimate validation report (W8-T3).

SPEC.md Section 11 requires, for every non-`STOP` tier, a frozen ENGINEERING
fallback: a validation plan, a validation schema, an empty report shell, and a
report generator, all dormant while an empirical tier is active. This module is
that generator. Given the frozen validation plan (and, when ENGINEERING is
actually active, the frozen validation records), it renders a deterministic
report that summarizes only check pass/fail/indeterminate counts and named
limitations. It makes NO official model estimate or defense claim (Section 1,
Section 12 ENGINEERING row).

Usage:
    python -m analysis.engineering_report --plan protocol/engineering_validation_plan.json
    python -m analysis.engineering_report --check paper/generated/engineering_report.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / "protocol" / "engineering_validation_plan.json"
DEFAULT_OUTPUT = ROOT / "paper" / "generated" / "engineering_report.md"
STATUS = "DORMANT — NO ENGINEERING RUN"


def load_plan(path: Path = DEFAULT_PLAN) -> dict[str, Any]:
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    if plan.get("plan_version") != "0.1.0":
        raise ValueError("unsupported engineering validation plan version")
    if plan.get("official_empirical_experiment") is not False:
        raise ValueError("ENGINEERING plan must declare official_empirical_experiment = false")
    checks = plan.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("ENGINEERING plan must list at least one check")
    ids: set[str] = set()
    for check in checks:
        for field in ("check_id", "category", "name", "input", "expected"):
            if not str(check.get(field, "")).strip():
                raise ValueError(f"check {check.get('check_id', '<unknown>')} missing {field}")
        if check["check_id"] in ids:
            raise ValueError(f"duplicate check_id: {check['check_id']}")
        ids.add(check["check_id"])
    return plan


def render(plan: dict[str, Any], records: Optional[list[dict[str, Any]]] = None) -> str:
    """Deterministic Markdown. With no records (dormant) it is a plan-only shell;
    with frozen records it summarizes pass/fail/indeterminate counts, never an estimate."""
    by_id: dict[str, Optional[bool]] = {}
    if records:
        for r in records:
            by_id[r["check_id"]] = r.get("passed")

    dormant = not records
    lines = [
        "# CANARY ENGINEERING Validation Report",
        "",
        f"> **{'DORMANT — NO ENGINEERING RUN' if dormant else 'ENGINEERING VALIDATION — NO OFFICIAL MODEL EXPERIMENT'}.**",
        "> This report summarizes instrument-validation checks on mocks and excluded",
        "> development/demo cases only. No official model experiment ran, and it makes",
        "> no empirical estimate or defense-efficacy claim (SPEC.md Sections 1, 11, 12).",
        "",
        f"- **Validation ID:** `{plan.get('validation_id', 'PENDING')}`",
        f"- **Plan version:** {plan['plan_version']}",
        f"- **Official empirical experiment:** {plan['official_empirical_experiment']}",
        "",
    ]

    if not dormant:
        passed = sum(1 for v in by_id.values() if v is True)
        failed = sum(1 for v in by_id.values() if v is False)
        indeterminate = sum(1 for v in by_id.values() if v is None)
        lines += [
            "## Check outcome counts",
            "",
            f"- Passed: {passed}",
            f"- Failed: {failed}",
            f"- Indeterminate (incomplete evidence, not false): {indeterminate}",
            "",
        ]

    lines += ["## Checks", "", "| Check | Category | Outcome |", "| --- | --- | --- |"]
    for check in plan["checks"]:
        if dormant:
            outcome = STATUS
        else:
            value = by_id.get(check["check_id"], None)
            outcome = {True: "PASS", False: "FAIL", None: "INDETERMINATE"}[value]
        lines.append(f"| {check['name']} | {check['category']} | {outcome} |")

    lines += [
        "",
        "## Named limitations",
        "",
        "- One hand-built agent; at ENGINEERING no official model experiment ran.",
        "- The corpus source ledger and excluded cases support validation only.",
        "- Exact-marker and enumerated-policy oracles under-detect semantic/encoded/partial harms.",
        "- Containment is intrinsic to the tools, not to any defense.",
        "",
    ]
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="fail if the generated shell is stale")
    args = parser.parse_args(argv)

    rendered = render(load_plan(args.plan))
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit(f"stale generated engineering report: {args.output}")
        print(f"{args.output}: current")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
