"""Generate one accessible development-output example from the W5-T3 runner."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping

from demo.trace import UNKNOWN, resolved_display_label
from runner.mock_slice import RESULTS_FILE, read_jsonl
from runner.six_cell import cell_dirs, run_six_cells


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "demo" / "generated" / "accessible_example.md"
FIXED_CLOCK = "2026-09-30T00:00:00Z"
EXPERIMENT_ID = "w6-t5-accessible-example"


def _tri(value: Any) -> str:
    if value is None:
        return UNKNOWN
    return "TRUE" if value else "FALSE"


def render_accessible_example(results: Iterable[Mapping[str, Any]]) -> str:
    """Render a text summary and table equivalent without hand-entered values."""

    rows = []
    for result in results:
        security = result["security"]
        rows.append(
            "| "
            + " | ".join(
                (
                    result["channel"],
                    result["condition"],
                    result["configuration"],
                    resolved_display_label(result) or UNKNOWN,
                    _tri(security["unauthorized_user_disclosure"]),
                    _tri(security["model_violation"]),
                    _tri(security["system_compromise"]),
                    _tri(result["utility"]["pass"]),
                )
            )
            + " |"
        )

    return "\n".join(
        [
            "# CANARY Accessible Generated-Output Example",
            "",
            "> **DEVELOPMENT MOCK — EXCLUDED FROM EVERY ESTIMATE.** This example is",
            "> generated from the W5-T3 six-cell runner with fixed fictional inputs.",
            "> It is instrument evidence, not an empirical result or defense claim.",
            "",
            "## Text summary",
            "",
            "The table contains the three delivery channels (C2, C3, and C4), each",
            "shown once under the attack condition and once under its exact clean twin.",
            "Attack rows exercise exact fictional-canary disclosure. Clean rows retain",
            "unknown values where this development runner has no evidence surface.",
            "",
            "## Figure caption",
            "",
            "Accessible development example generated from six schema-valid D0_BASELINE",
            "mock records. Rows are illustrative and excluded from CANARY estimates.",
            "",
            "## Alt text",
            "",
            "A table of six development records: attack and clean conditions for C2, C3,",
            "and C4. Each row spells out disclosure, model-violation, system-compromise,",
            "utility, and display-label state without relying on color.",
            "",
            "## Table equivalent",
            "",
            "| Channel | Condition | Configuration | Display label | User disclosure | Model violation | System compromise | Utility |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
            *rows,
            "",
            "## Evidence boundary",
            "",
            "- Source: `runner.six_cell`, using the committed development base `dev-001`.",
            "- Provider: no-credit canned mock; no credential or network is used.",
            "- Protocol: not frozen; these records cannot enter an official denominator.",
            "- Values are generated from schema-valid JSONL and are not typed into this table.",
            "",
        ]
    )


def generate_example() -> str:
    """Run the real six-cell development path and render its stored results."""

    tokens = iter(("accessible-fixture-key", "accessible-customer-record"))
    with tempfile.TemporaryDirectory(prefix="canary-w6-t5-") as temp:
        run_dir = run_six_cells(
            Path(temp) / "run",
            clock=lambda: FIXED_CLOCK,
            experiment_id=EXPERIMENT_ID,
            canary_factory=lambda: next(tokens),
        )
        results = [
            read_jsonl(cell / RESULTS_FILE, "result")[-1]
            for cell in cell_dirs(run_dir)
        ]
    return render_accessible_example(results)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    rendered = generate_example()

    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit(f"stale accessible example: {args.output}")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
