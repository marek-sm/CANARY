import json
import shutil
import subprocess
import sys
from pathlib import Path

from analysis import output_pipeline_freeze


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "paper" / "output_pipeline_freeze.json"


def _copy_pipeline(root: Path) -> None:
    for relative in (*output_pipeline_freeze.PIPELINE_PATHS, *output_pipeline_freeze.EVIDENCE_PATHS):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)


def test_committed_output_pipeline_freeze_is_current_and_pre_results_only():
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
    assert frozen == output_pipeline_freeze.build()
    assert frozen["status"] == "PRE-RESULTS — NO DATA"
    assert set(frozen["pipeline_files"]) == set(output_pipeline_freeze.PIPELINE_PATHS)
    assert "analysis/report.py" not in frozen["pipeline_files"]


def test_build_refuses_a_stale_generated_shell(tmp_path):
    _copy_pipeline(tmp_path)
    shell = tmp_path / "paper" / "generated" / "estimand_shells.md"
    shell.write_text(shell.read_text(encoding="utf-8") + "typed result\n", encoding="utf-8")
    try:
        output_pipeline_freeze.build(tmp_path)
    except ValueError as error:
        assert "stale" in str(error)
    else:
        raise AssertionError("a stale generated shell was accepted")


def test_make_report_runs_the_frozen_accessible_pipeline():
    env = {"PATH": f"{Path(sys.executable).parent}:/usr/bin:/bin", "HOME": str(ROOT)}
    done = subprocess.run(
        ["make", "-s", "report", "REPORT_MODULE=analysis.report_shells"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert done.returncode == 0, done.stderr
