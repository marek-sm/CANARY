"""Replay renders every delivery-path record the grid writes (stack-gaps item 2).

The audit found demo/trace.py raised KeyError: 'text' on query_db rows, 54 of 90
mock-grid traces. Every tool returns one of three successful observation shapes:
``text`` (read_file, fetch_url), ``rows`` (query_db), or bare ``ok`` (send_email).
"""

import subprocess
import sys
from pathlib import Path

from demo import trace
from runner import grid_dev

ROOT = Path(__file__).resolve().parents[1]


def test_every_successful_observation_shape_has_text_or_nothing():
    assert trace._observation_text({"ok": True, "text": "page"}) == "page"
    assert trace._observation_text({"ok": True, "rows": [{"record_id": "r-1", "content": "c"}]}) == (
        '{"rows": [{"content": "c", "record_id": "r-1"}]}'
    )
    assert trace._observation_text({"ok": True}) is None


def test_all_ninety_mock_grid_traces_render(mock_grid_checkout):
    events = sorted(Path(mock_grid_checkout.grid).glob("*/events.jsonl"))
    assert len(events) == grid_dev.EXPECTED_TRIALS
    rendered = [trace.render_trace(path) for path in events]
    assert all("CANARY  |  RECORDED TRACE" in text and "OUTCOME" in text for text in rendered)
    assert sum("rows" in path.read_text(encoding="utf-8") for path in events) > 0


def test_replay_renders_a_whole_run_directory(mock_grid_checkout, capsys):
    assert trace.main([str(mock_grid_checkout.grid)]) == 0
    assert capsys.readouterr().out.count("CANARY  |  RECORDED TRACE") == grid_dev.EXPECTED_TRIALS


def test_replay_of_a_missing_run_says_what_to_do(tmp_path, capsys):
    assert trace.main([str(tmp_path / "absent")]) == 2
    assert "make grid-mock" in capsys.readouterr().err


def test_make_replay_needs_no_key_or_network(mock_grid_checkout):
    """The target reads records only: no provider variable, no network, no key file."""
    env = {"PATH": f"{Path(sys.executable).parent}:/usr/bin:/bin", "HOME": str(mock_grid_checkout.root)}
    done = subprocess.run(
        ["unshare", "-rn", "make", "-s", "replay", f"RUN={mock_grid_checkout.grid}"] if _can_unshare()
        else ["make", "-s", "replay", f"RUN={mock_grid_checkout.grid}"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=120,
    )
    assert done.returncode == 0, done.stderr
    assert done.stdout.count("CANARY  |  RECORDED TRACE") == grid_dev.EXPECTED_TRIALS


def _can_unshare() -> bool:
    try:
        return subprocess.run(["unshare", "-rn", "true"], capture_output=True, timeout=10).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False
