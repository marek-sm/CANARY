"""Freeze and verify W8-T5's accessible pre-results output pipeline.

The pipeline is intentionally limited to W5-T5's table/figure shell generator,
its estimand manifest, and the generated accessible Markdown shell.  It contains
no result data and does not freeze W8-T3's scientific analysis implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from analysis.report_shells import load_manifest, render_manifest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "paper" / "output_pipeline_freeze.json"
PIPELINE_PATHS = (
    "analysis/report_shells.py",
    "paper/estimand_manifest.json",
    "paper/generated/estimand_shells.md",
)
EVIDENCE_PATHS = (
    "tests/test_paper_scaffold.py",
    "tests/test_make_report.py",
    "tests/test_output_pipeline_freeze.py",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _files(root: Path, paths: tuple[str, ...]) -> dict[str, str]:
    files: dict[str, str] = {}
    for relative in paths:
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"missing output-pipeline file: {relative}")
        files[relative] = _sha256(path)
    return files


def _set_hash(files: dict[str, str]) -> str:
    material = "\n".join(f"{path}\t{digest}" for path, digest in sorted(files.items()))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def build(root: Path = ROOT) -> dict[str, Any]:
    """Return the freeze record after proving the generated shell is current."""

    manifest_path = root / "paper" / "estimand_manifest.json"
    shell_path = root / "paper" / "generated" / "estimand_shells.md"
    manifest = load_manifest(manifest_path)
    if manifest.get("status") != "pre_results_no_data":
        raise ValueError("the W8-T5 freeze accepts only the pre-results/no-data manifest")
    rendered = render_manifest(manifest)
    if not shell_path.is_file() or shell_path.read_text(encoding="utf-8") != rendered:
        raise ValueError("paper/generated/estimand_shells.md is stale; run make paper-shells")

    pipeline_files = _files(root, PIPELINE_PATHS)
    evidence_files = _files(root, EVIDENCE_PATHS)
    return {
        "freeze_version": "1.0.0",
        "rule": "W8-T5 accessible output-pipeline freeze; TASKS.md W8-T5 and SPEC.md Section 11 Gate 3",
        "status": "PRE-RESULTS — NO DATA",
        "generate_command": "python -m analysis.report_shells",
        "check_command": "python -m analysis.output_pipeline_freeze --check",
        "output_pipeline_hash": _set_hash(pipeline_files),
        "test_evidence_hash": _set_hash(evidence_files),
        "pipeline_files": pipeline_files,
        "test_evidence_files": evidence_files,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    try:
        text = json.dumps(build(), indent=2, sort_keys=True) + "\n"
        if args.check:
            if not args.output.is_file() or args.output.read_text(encoding="utf-8") != text:
                print(
                    "paper/output_pipeline_freeze.json is missing or the accessible output pipeline drifted; "
                    "a post-freeze change follows SPEC.md Section 11",
                    file=sys.stderr,
                )
                return 1
            return 0
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        return 0
    except (OSError, ValueError) as error:
        print(f"output-pipeline-freeze: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
