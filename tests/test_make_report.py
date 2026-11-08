"""`make report`, which the Gate 3 step runs (TASKS.md), exists and says what's missing.

It runs what is on main, ``analysis.report_shells``, and then W8-T3's analysis and
report code. Until W8-T3 merges, it fails with a message naming W8-T3, never silently.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHELLS = ROOT / "paper" / "generated" / "estimand_shells.md"


def _make(*args):
    env = {"PATH": f"{Path(sys.executable).parent}:/usr/bin:/bin", "HOME": str(ROOT)}
    return subprocess.run(["make", "-s", "report", *args], cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)


def test_make_report_runs_the_shells_and_names_what_w8_t3_hasn_t_built():
    before = SHELLS.read_bytes()
    done = _make("REPORT_MODULE=analysis.not_built_here")
    assert done.returncode != 0
    assert "W8-T3" in done.stderr and "analysis.not_built_here" in done.stderr
    assert "No rule to make target" not in done.stderr
    assert SHELLS.read_bytes() == before  # the generated shells are the committed ones


def test_make_report_runs_w8_t3_s_module_once_it_exists():
    done = _make("REPORT_MODULE=analysis.report_shells")
    assert done.returncode == 0, done.stderr
