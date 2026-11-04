"""The paid-run gate's refusals, against a real 90-cell mock grid (decision 0023).

Nothing here makes a provider call: the only non-mock providers are local fakes,
and each test stands on the record ``build_record`` writes from a grid that ran.
"""

import copy
import datetime
import hashlib
import importlib.metadata
import importlib.util
import json
import marshal
import os
import platform
import py_compile
import re
import shutil
import sqlite3
import struct
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from runner import grid_dev, paid_run
from runner.mock_provider import MOCK_MODEL_ID, MockProvider

ROOT = Path(__file__).resolve().parents[1]


# --- a preflight counts only if the task worked in every cell ---------------------------------


class TwoCalls(MockProvider):
    """Every reply carries two tool calls, so every trial ends malformed."""

    def complete(self, messages, tool_schemas, decoding, model_request):
        raw = {"stop_reason": "tool_use", "content": [
            {"type": "tool_use", "id": "a", "name": "read_file", "input": {"path": "x"}},
            {"type": "tool_use", "id": "b", "name": "read_file", "input": {"path": "y"}},
        ]}
        return {"outcome": "model_response", "provider_request_id": "r", "model_requested": model_request["model"],
                "model_resolved": MOCK_MODEL_ID, "provider_fingerprint": None, "raw_response": raw,
                "usage": {"input_tokens": None, "output_tokens": None}}


def test_a_healthy_mock_grid_makes_a_record_in_every_cell(gate):
    results = [json.loads(p.read_text()) for p in gate.mock.glob("*/results.jsonl")]
    assert len(results) == 90
    assert {r["condition"] for r in results} == {"attack", "clean"}
    assert all(r["termination_reason"] == "final_answer" and r["utility"]["pass"] is True for r in results)
    assert gate.record()["conditions"]["mock_grid"]["trials"] == 90


def test_the_record_refuses_a_grid_where_every_trial_was_malformed(gate, tmp_path):
    spec = gate.spec
    malformed = gate.root / "results" / "development" / "malformed"
    grid_dev.run_mock_grid(malformed, spec=spec, corpus_root=gate.root / "corpus" / "development",
                           provider_factory=lambda trial, canaries: TwoCalls())
    assert grid_dev.verify_grid_run(malformed, spec)["complete"]  # the audit's point: verify alone passes it
    with pytest.raises(paid_run.PaidRunRefused, match="final_answer"):
        gate.record(malformed)


@pytest.mark.parametrize("reason", ["max_steps", "malformed_model_output", "provider_content_filter"])
def test_the_record_refuses_one_trial_that_didnt_end_final_answer(gate, reason):
    gate.edit_result(gate.trial("D0_BASELINE", "clean"), lambda r: r.update(termination_reason=reason))
    with pytest.raises(paid_run.PaidRunRefused, match="final_answer"):
        gate.record()


@pytest.mark.parametrize("value", [False, None])
def test_the_record_refuses_one_trial_whose_utility_didnt_pass(gate, value):
    gate.edit_result(gate.trial("D2_DATAMARKING"), lambda r: r["utility"].update({"pass": value}))
    with pytest.raises(paid_run.PaidRunRefused, match="utility"):
        gate.record()


@pytest.mark.parametrize("value", [False, None])
def test_the_record_refuses_a_tool_result_that_wasnt_ok(gate, value):
    def fail(event):
        if event["event_type"] == "tool_result":
            event["payload"]["observation"]["ok"] = value

    gate.edit_events(gate.trial("D0_BASELINE"), fail)
    with pytest.raises(paid_run.PaidRunRefused, match="tool result"):
        gate.record()


@pytest.mark.parametrize("field,value", [("seed", "another-seed"), ("model_id", "claude-haiku-5-5"), ("repeats", 2)])
def test_the_record_refuses_a_grid_whose_stored_spec_isnt_the_committed_one(gate, field, value):
    path = gate.mock / "schedule_spec.json"
    stored = json.loads(path.read_text(encoding="utf-8"))
    stored[field] = value
    path.write_text(json.dumps(stored), encoding="utf-8")
    with pytest.raises(paid_run.PaidRunRefused, match="schedule_spec"):
        gate.record()


# --- SPEC.md Section 6: D1_POLICY_GATE conformance in the preflight ----------------------------


def _first_tool_event(record, **changes):
    record["tool_events"][0].update(changes)


def test_the_record_refuses_a_gate_that_dispatched_what_the_audit_rejected(gate):
    gate.edit_result(gate.trial(), lambda r: _first_tool_event(r, authorized=False, dispatched=True))
    with pytest.raises(paid_run.PaidRunRefused, match="audit rejected"):
        gate.record()


@pytest.mark.parametrize("value,words", [(False, "disagreed"), (None, "unknown")])
def test_the_record_refuses_a_gate_and_audit_that_didnt_agree(gate, value, words):
    gate.edit_result(gate.trial(), lambda r: _first_tool_event(r, gate_audit_match=value))
    with pytest.raises(paid_run.PaidRunRefused, match=words):
        gate.record()


def test_the_record_refuses_a_gate_cell_with_no_request(gate):
    gate.edit_result(gate.trial(), lambda r: r.update(tool_events=[]))
    with pytest.raises(paid_run.PaidRunRefused, match="no tool request"):
        gate.record()


def test_an_unauthorized_dispatch_outside_the_gate_is_no_conformance_failure(gate):
    # Under D0_BASELINE the audit is observational, and every valid request is dispatched (Section 6).
    gate.edit_result(gate.trial("D0_BASELINE"), lambda r: _first_tool_event(r, authorized=False, dispatched=True))
    assert gate.record()["conditions"]["mock_grid"]["trials"] == 90


# --- one negative test per refusal in build_record ---------------------------------------------


def _set_sandbox(value):
    def edit(event):
        if value is None:
            event["component_versions"].pop("tool_sandbox", None)
        else:
            event["component_versions"]["tool_sandbox"] = value
    return edit


@pytest.mark.parametrize("value", [None, "linux-bwrap:tool-sandbox-v0.0.0:0000000000000000"])
def test_the_record_refuses_a_grid_without_one_recorded_sandbox(gate, value):
    gate.edit_events(gate.trial("D0_BASELINE"), _set_sandbox(value))
    with pytest.raises(paid_run.PaidRunRefused, match="one recorded tool sandbox"):
        gate.record()


def test_the_record_refuses_a_grid_run_without_delivery(gate):
    (gate.mock / "runner_mode.json").write_text(json.dumps({"delivery": False}), encoding="utf-8")
    with pytest.raises(paid_run.PaidRunRefused, match="tool-result delivery"):
        gate.record()


def test_the_record_refuses_a_grid_verify_calls_incomplete(gate, monkeypatch):
    # verify_grid_run raises on a missing trial, so this is the guard behind it.
    monkeypatch.setattr(paid_run, "_READ_MOCK_RUNS", {})
    monkeypatch.setattr(grid_dev, "verify_grid_run", lambda run, spec: {
        "complete": False, "experiment_id": spec["experiment_id"], "trials_found": 89})
    with pytest.raises(paid_run.PaidRunRefused, match="isn't complete"):
        gate.record()


def test_the_record_refuses_a_grid_with_a_trial_missing(gate):
    trial = gate.trial("D0_BASELINE", "clean")
    (trial / "results.jsonl").unlink()
    with pytest.raises(paid_run.PaidRunRefused, match="doesn't verify"):
        gate.record()


def test_the_record_refuses_a_trial_that_didnt_complete(gate):
    gate.edit_result(gate.trial("D0_BASELINE", "clean"),
                     lambda r: r.update(status="infrastructure_failure", termination_reason="infrastructure_failure"))
    with pytest.raises(paid_run.PaidRunRefused, match="didn't complete"):
        gate.record()


def test_the_record_refuses_a_grid_from_another_sandbox(gate, monkeypatch):
    monkeypatch.setattr(paid_run.sandbox, "describe", lambda: "linux-bwrap:tool-sandbox-v0.0.0:0000000000000000")
    with pytest.raises(paid_run.PaidRunRefused, match="machine and sandbox"):
        gate.record()


def test_the_record_refuses_uncommitted_recorded_code(gate):
    (gate.root / "runner" / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    with pytest.raises(paid_run.PaidRunRefused, match="commit or discard"):
        gate.record()


def test_the_record_refuses_a_grid_that_recorded_no_provenance(gate):
    (gate.mock / paid_run.PROVENANCE_FILE).unlink()
    with pytest.raises(paid_run.PaidRunRefused, match="didn't record the code"):
        gate.record()


# --- what the record hashes --------------------------------------------------------------------


def test_every_hashed_path_fits_the_record_schema():
    schema = json.loads((ROOT / "schemas" / "paid_run_record.schema.json").read_text(encoding="utf-8"))
    pattern = schema["properties"]["code_sha256"]["propertyNames"]["pattern"]
    tracked = paid_run.tracked_files()
    assert {"analysis/floor_count.py", "analysis/gate2_budget.py", "paper/estimand_manifest.json"} <= set(tracked)
    assert [path for path in tracked if not re.search(pattern, path)] == []


@pytest.mark.parametrize("path", ["analysis/floor_count.py", "paper/estimand_manifest.json"])
def test_a_change_to_the_scoring_code_closes_paid_runs(gate, path):
    """The audit's probe: FLOOR_THRESHOLD changed, and paid runs stayed open."""
    record = gate.open()
    assert gate.refusal(record) is None
    target = gate.root / path
    text = target.read_text(encoding="utf-8").replace("FLOOR_THRESHOLD = 3", "FLOOR_THRESHOLD = 1").rstrip() + "\n\n"
    target.write_text(text, encoding="utf-8")
    assert "uncommitted" in gate.refusal(record)
    gate.git("add", path)
    gate.git("commit", "-qm", "change it")
    assert "code differs" in gate.refusal(record)


# --- ignored files under hashed directories ----------------------------------------------------


@pytest.mark.parametrize("name", ["runner/shadow.sqlite", "tools/notes.log", "corpus/development/a b.db"])
def test_an_ignored_file_under_a_hashed_directory_closes_paid_runs(gate, name):
    record = gate.open()
    path = gate.root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")
    assert paid_run.dirty_paths(gate.root) == [name]
    assert name in gate.refusal(record)


def _bytecode(gate, source="runner/code.py"):
    return gate.root / importlib.util.cache_from_source(source)


def _shadow_pyc(gate, *, flags=0, header=None, code="VALUE = 99\n", source="runner/code.py"):
    """A ``.pyc`` holding other code. By default its header passes Python's own checks, as a
    timestamp file whose time and size are the source's, so Python loads it instead."""
    stat = (gate.root / source).stat()
    words = header or (int(stat.st_mtime) & 0xFFFFFFFF, stat.st_size & 0xFFFFFFFF)
    return importlib.util.MAGIC_NUMBER + struct.pack("<III", flags, *words) + marshal.dumps(compile(code, source, "exec"))


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _imported_value(gate):
    done = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, '.'); import runner.code; print(runner.code.VALUE)"],
                          cwd=gate.root, check=True, capture_output=True, text=True)
    return int(done.stdout)


def test_the_bytecode_a_healthy_run_leaves_stays_open(gate):
    record = gate.open()
    assert _imported_value(gate) == 1
    assert _bytecode(gate).is_file()
    assert paid_run.dirty_paths(gate.root) == []
    assert gate.refusal(record) is None


def test_a_forged_loadable_pyc_still_refuses(gate):
    """The source and every hash are untouched, and Python runs the forgery."""
    record = gate.open()
    _write(_bytecode(gate), _shadow_pyc(gate))
    assert paid_run.dirty_paths(gate.root) == [importlib.util.cache_from_source("runner/code.py")]
    assert "uncommitted or ignored" in gate.refusal(record)
    assert _imported_value(gate) == 99


@pytest.mark.parametrize("flags", [0b01, 0b11])
def test_hash_based_bytecode_that_differs_from_its_source_refuses(gate, flags):
    record = gate.open()
    _write(_bytecode(gate), _shadow_pyc(gate, flags=flags, header=(0, 0)))
    assert gate.refusal(record) is not None


def test_hash_based_bytecode_of_its_own_source_stays_open(gate):
    record = gate.open()
    _write(_bytecode(gate), _shadow_pyc(gate, flags=0b01, header=(0, 0), code="VALUE = 1\n"))
    assert gate.refusal(record) is None


def test_loadable_bytecode_python_can_t_read_refuses(gate):
    record = gate.open()
    stat = (gate.root / "runner/code.py").stat()
    _write(_bytecode(gate), importlib.util.MAGIC_NUMBER + struct.pack("<III", 0, int(stat.st_mtime), stat.st_size) + b"junk")
    assert gate.refusal(record) is not None


@pytest.mark.parametrize("relative", ["runner/code.pyc", "runner/gone.pyc"])
def test_a_sourceless_pyc_outside_pycache_refuses(gate, relative):
    """Python imports this file when it has no source, and no hash can see it."""
    record = gate.open()
    _write(gate.root / relative, _shadow_pyc(gate))
    assert paid_run.dirty_paths(gate.root) == [relative]
    assert gate.refusal(record) is not None


def test_a_stale_pyc_python_wouldnt_load_stays_open(gate):
    """The false refusal: after changing commits, old bytecode sits beside a changed source."""
    record = gate.open()
    _write(_bytecode(gate), _shadow_pyc(gate, header=(1, 1)))
    assert paid_run.dirty_paths(gate.root) == []
    assert gate.refusal(record) is None
    assert _imported_value(gate) == 1  # and Python really doesn't load it


@pytest.mark.parametrize("relative", [
    "runner/__pycache__/gone.cpython-311.pyc",  # its source is gone
    "runner/__pycache__/code.cpython-39.pyc",  # another interpreter's
    "runner/__pycache__/code.cpython-311.opt-2.pyc",  # another optimization level's
])
def test_bytecode_python_wouldnt_read_stays_open(gate, relative):
    record = gate.open()
    _write(gate.root / relative, _shadow_pyc(gate))
    assert paid_run.dirty_paths(gate.root) == []
    assert gate.refusal(record) is None


@pytest.mark.parametrize("data", [
    b"\0\0\0\0" + b"\0" * 12 + b"x",  # another interpreter's magic number
    importlib.util.MAGIC_NUMBER + b"\0" * 4,  # too short to have a header
    importlib.util.MAGIC_NUMBER + struct.pack("<III", 0b100, 0, 0) + b"x",  # flags Python rejects
])
def test_bytecode_python_would_reject_stays_open(gate, data):
    record = gate.open()
    _write(_bytecode(gate), data)
    assert paid_run.dirty_paths(gate.root) == []
    assert gate.refusal(record) is None


def test_another_ignored_file_in_pycache_refuses(gate):
    record = gate.open()
    _write(gate.root / "runner" / "__pycache__" / "notes.log", b"x")
    assert gate.refusal(record) is not None


@pytest.mark.parametrize("name", ["runner/.DS_Store", "corpus/development/.DS_Store"])
def test_finder_s_ds_store_never_stops_a_run(gate, name):
    """On a Mac, Finder can create one mid-grid, which would stop a paid grid at its next trial."""
    record = gate.open()
    _write(gate.root / name, b"x")
    assert paid_run.dirty_paths(gate.root) == []
    assert gate.refusal(record) is None
    gate.rerun()
    assert json.loads((gate.mock / paid_run.PROVENANCE_FILE).read_text().splitlines()[-1])["dirty_paths"] == []


def test_the_record_refuses_a_grid_run_beside_an_ignored_file(gate):
    extra = gate.root / "runner" / "shadow.sqlite"
    extra.write_text("x", encoding="utf-8")
    gate.rerun()
    extra.unlink()
    with pytest.raises(paid_run.PaidRunRefused, match="uncommitted"):
        gate.record()


# --- the installed environment against uv.lock -------------------------------------------------


def _installed(monkeypatch, **versions):
    """``distributions()`` with these packages changed or added."""
    real = list(importlib.metadata.distributions())
    kept = [d for d in real if str(d.metadata["Name"]).lower() not in versions]
    extra = [SimpleNamespace(metadata={"Name": name}, version=version) for name, version in versions.items()]
    monkeypatch.setattr(importlib.metadata, "distributions", lambda: [*kept, *extra])


def test_the_record_states_the_installed_environment(gate):
    environment = gate.record()["environment"]
    assert environment["python"] == platform.python_version()
    assert environment["packages"]["openai"] == importlib.metadata.version("openai")
    assert environment["packages"]["anthropic"] == importlib.metadata.version("anthropic")


@pytest.mark.parametrize("change", [{"openai": "0.0.1"}, {"unlocked-package": "1.0"}])
def test_a_package_changed_since_the_record_closes_paid_runs(gate, monkeypatch, change):
    record = gate.open()
    assert gate.refusal(record) is None
    _installed(monkeypatch, **change)
    reason = gate.refusal(record)
    assert reason is not None and "uv.lock" in reason


def test_the_tools_a_venv_keeps_are_no_refusal(gate, monkeypatch):
    """The lead's real venv holds these, and ``uv sync`` doesn't remove them."""
    with monkeypatch.context() as patch:
        _installed(patch, pip="26.2.1", setuptools="65.5.0", wheel="0.46.0")
        record = gate.open()
        assert gate.refusal(record) is None
    assert gate.refusal(record) is None  # and they aren't part of what the record pins
    with monkeypatch.context() as patch:
        _installed(patch, pip="99.0")
        assert gate.refusal(record) is None


def test_the_tools_are_refused_at_a_version_other_than_the_lock_s(gate):
    lock = gate.root / "uv.lock"
    lock.write_text(lock.read_text(encoding="utf-8") + '\n[[package]]\nname = "pip"\nversion = "1.0"\n', encoding="utf-8")
    environment = {"python": platform.python_version(), "packages": {"pip": "26.2.1"}}
    assert paid_run.lock_mismatch(environment, gate.root) == ["pip 26.2.1"]


def test_a_package_the_lock_allows_but_the_record_doesnt_closes_paid_runs(gate):
    record = gate.commit_record({**gate.record(), "environment": {"python": platform.python_version(),
                                                                  "packages": {"openai": "0.0.1"}}})
    assert "environment" in gate.refusal(record)


def test_another_python_closes_paid_runs(gate, monkeypatch):
    record = gate.open()
    monkeypatch.setattr(platform, "python_version", lambda: "3.12.1")
    reason = gate.refusal(record)
    assert reason is not None and "python 3.12.1" in reason


def test_another_patch_release_of_python_closes_paid_runs(gate, monkeypatch):
    record = gate.open()
    monkeypatch.setattr(platform, "python_version", lambda: "3.11.0")
    assert "environment" in gate.refusal(record)


def test_the_record_refuses_an_environment_the_lock_doesnt_pin(gate, monkeypatch):
    _installed(monkeypatch, openai="0.0.1")
    with pytest.raises(paid_run.PaidRunRefused, match="uv.lock"):
        gate.record()


def test_the_record_refuses_a_grid_run_under_other_packages(gate, monkeypatch):
    with monkeypatch.context() as patch:
        _installed(patch, openai="0.0.1")
        gate.rerun()
    with pytest.raises(paid_run.PaidRunRefused, match="other installed packages"):
        gate.record()


def test_an_unreadable_lock_closes_paid_runs(gate):
    record = gate.open()
    (gate.root / "uv.lock").write_text("not [toml", encoding="utf-8")
    assert gate.refusal(record) is not None


# --- a record written by hand opens nothing ----------------------------------------------------


def _hand_written(gate, **mock_grid):
    """The record ``build_record`` would write, changed the way a hand could change it."""
    record = copy.deepcopy(gate.record())
    record["conditions"]["mock_grid"].update(mock_grid)
    return record


def test_the_audit_s_hand_written_record_is_refused(gate):
    record = _hand_written(gate, experiment_id="never-ran")
    record.update(recorded_commit="0" * 40, recorded_on="1999-01-01")
    assert gate.refusal(gate.commit_record(record)) is not None


def test_a_recorded_commit_that_doesnt_exist_is_refused(gate):
    assert "ancestor" in gate.refusal(gate.commit_record({**gate.record(), "recorded_commit": "0" * 40}))


def test_a_recorded_commit_off_this_history_is_refused(gate):
    record = gate.record()
    gate.git("commit", "--allow-empty", "-qm", "side")
    side = subprocess.run(["git", "rev-parse", "HEAD"], cwd=gate.root, env=gate.env, check=True,
                          capture_output=True, text=True).stdout.strip()
    gate.git("reset", "-q", "--hard", "HEAD~1")
    assert "ancestor" in gate.refusal(gate.commit_record({**record, "recorded_commit": side}))


@pytest.mark.parametrize("recorded_on", ["1999-01-01", "2999-01-01", "2026-13-45"])
def test_a_date_that_cant_be_the_record_s_is_refused(gate, recorded_on):
    assert "recorded_on" in gate.refusal(gate.commit_record({**gate.record(), "recorded_on": recorded_on}))


def test_an_experiment_that_never_ran_is_refused(gate):
    assert "never-ran" in gate.refusal(gate.commit_record(_hand_written(gate, experiment_id="never-ran")))


@pytest.mark.parametrize("field", ["run_files_sha256", "results_sha256", "events_sha256"])
def test_a_made_up_digest_of_the_mock_grid_is_refused(gate, field):
    record = gate.commit_record(_hand_written(gate, **{field: "a" * 64}))
    assert "changed" in gate.refusal(record)


@pytest.mark.parametrize("run_path", ["results/development/never-ran", "results/../..", "protocol"])
def test_a_mock_grid_that_isnt_there_is_refused(gate, run_path):
    assert gate.refusal(gate.commit_record(_hand_written(gate, run_path=run_path))) is not None


def test_a_run_path_can_t_climb_out_of_results(gate):
    """A real, digest-matching grid outside ``results/``: only the containment check can refuse it."""
    shutil.copytree(gate.mock, gate.root / "elsewhere" / "grid")
    record = gate.commit_record(_hand_written(gate, run_path="results/../elsewhere/grid"))
    assert "isn't under" in gate.refusal(record)


def _other_sandbox():
    if paid_run.sandbox.describe().startswith("linux-bwrap"):
        return "macos-sandbox-exec:tool-sandbox-v0.0.0:0000000000000000"
    return "linux-bwrap:tool-sandbox-v0.0.0:0000000000000000"


def test_a_grid_from_another_sandbox_is_refused_though_the_record_names_this_one(gate):
    """Every trial really ran elsewhere, with digests that match; only reading the grid can tell."""
    healthy = gate.record()
    for trial_dir in sorted(p.parent for p in gate.mock.glob("*/events.jsonl")):
        gate.edit_events(trial_dir, _set_sandbox(_other_sandbox()))
    healthy["conditions"]["mock_grid"].update(tool_sandbox=_other_sandbox(), **paid_run.mock_run_digests(gate.mock))
    assert "ran under" in gate.refusal(gate.commit_record(healthy))


def test_a_record_that_misstates_the_grid_s_sandbox_is_refused(gate):
    record = gate.commit_record(_hand_written(gate, tool_sandbox=_other_sandbox()))
    assert "tool_sandbox" in gate.refusal(record)


def test_the_gate_reads_a_grid_in_full_once_per_process(gate, monkeypatch):
    record = gate.open()
    reads = []
    verify = grid_dev.verify_grid_run
    monkeypatch.setattr(paid_run, "_READ_MOCK_RUNS", {})
    monkeypatch.setattr(grid_dev, "verify_grid_run", lambda run, spec: reads.append(run) or verify(run, spec))
    assert gate.refusal(record) is None
    assert gate.refusal(record) is None
    assert len(reads) == 1


def test_the_digests_of_a_grid_where_nothing_worked_are_refused(gate):
    """A hand copies real digests from a real grid. The gate still reads that grid."""
    malformed = gate.root / "results" / "development" / "malformed"
    grid_dev.run_mock_grid(malformed, spec=gate.spec, corpus_root=gate.root / "corpus" / "development",
                           provider_factory=lambda trial, canaries: TwoCalls())
    record = gate.commit_record(_hand_written(gate, run_path="results/development/malformed",
                                              **paid_run.mock_run_digests(malformed)))
    assert "final_answer" in gate.refusal(record)


@pytest.mark.parametrize("edit", ["result", "event", "provenance", "spec", "mode"])
def test_a_mock_grid_changed_after_the_record_closes_paid_runs(gate, edit):
    record = gate.open()
    assert gate.refusal(record) is None
    if edit == "result":
        gate.edit_result(gate.trial(), lambda r: r["utility"].update({"pass": False}))
    elif edit == "event":
        gate.edit_events(gate.trial(), lambda e: None)
        (gate.trial() / "events.jsonl").write_text((gate.trial() / "events.jsonl").read_text() + "\n")
    elif edit == "provenance":
        with (gate.mock / paid_run.PROVENANCE_FILE).open("a") as handle:
            handle.write("{}\n")
    else:
        name = "schedule_spec.json" if edit == "spec" else "runner_mode.json"
        (gate.mock / name).write_text((gate.mock / name).read_text() + "\n")
    assert "changed" in gate.refusal(record)


def test_a_mock_grid_removed_after_the_record_closes_paid_runs(gate):
    record = gate.open()
    shutil.rmtree(gate.mock)
    assert "mock grid" in gate.refusal(record)


def test_the_record_refuses_a_mock_grid_outside_this_checkout_s_results(gate, tmp_path):
    outside = shutil.copytree(gate.mock, tmp_path / "grid")
    with pytest.raises(paid_run.PaidRunRefused, match="results/"):
        gate.record(outside)


def test_an_uncommitted_record_is_refused(gate):
    record = gate.write_record(gate.record())
    assert "isn't committed" in gate.refusal(record)
    gate.git("add", record.relative_to(gate.root).as_posix())
    assert "uncommitted changes" in gate.refusal(record)


def test_a_record_edited_after_its_commit_is_refused(gate):
    record = gate.open()
    text = record.read_text(encoding="utf-8")
    record.write_text(text + "\n", encoding="utf-8")
    assert "uncommitted changes" in gate.refusal(record)


def test_a_record_outside_this_checkout_is_refused(gate, tmp_path):
    outside = tmp_path / "paid_run_record.json"
    outside.write_text(json.dumps(gate.record()), encoding="utf-8")
    assert "in this checkout" in gate.refusal(outside)


def test_a_directory_git_doesn_t_know_refuses_in_words(gate, tmp_path):
    (tmp_path / "plain").mkdir()
    assert "git" in paid_run.paid_run_refusal(live_smoke=True, root=tmp_path / "plain")


def test_an_empty_trace_beside_the_grid_is_a_refusal_not_a_crash(gate):
    extra = gate.mock / "t9999_leftover"
    extra.mkdir()
    (extra / "events.jsonl").write_text("", encoding="utf-8")
    with pytest.raises(paid_run.PaidRunRefused):
        gate.record()


def test_a_later_commit_outside_the_hashed_paths_keeps_paid_runs_open(gate):
    record = gate.open()
    gate.commit_code("docs/note.md", "a later merge\n")
    assert gate.refusal(record) is None


def test_the_record_pins_the_grid_in_this_checkout(gate):
    grid = gate.record()["conditions"]["mock_grid"]
    assert grid["run_path"] == "results/development/grid-mock"
    assert grid == {**grid, **paid_run.mock_run_digests(gate.mock)}
    assert datetime.date.fromisoformat(gate.record()["recorded_on"]) == datetime.date.today()


def test_the_command_writes_a_record_that_validates_and_refuses_in_words(gate, monkeypatch, capsys):
    monkeypatch.setattr(paid_run, "RECORD", gate.root / "protocol" / "paid_run_record.json")
    arguments = ["record", str(gate.mock), "--delivery", "#61", "--sandbox", "#64", "--request-to-effect", "#39"]
    (gate.root / "runner" / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    assert paid_run.main(arguments) == 1
    assert "commit or discard" in capsys.readouterr().err
    gate.git("checkout", "--", "runner/code.py")
    assert paid_run.main(arguments) == 0
    paid_run.validator(paid_run.RECORD_SCHEMA).validate(json.loads(paid_run.RECORD.read_text(encoding="utf-8")))


# --- the live smoke: the pilot exception needs no record, and isn't a way around the rest -----


@pytest.fixture
def smoke_without_a_key(gate, monkeypatch, tmp_path):
    """``live_smoke.main`` with the gate real; it must refuse before it reads any key."""
    from runner import live_smoke

    monkeypatch.setattr(paid_run, "RECORD", tmp_path / "no-record.json")
    monkeypatch.setattr(live_smoke, "load_api_key", lambda *a: pytest.fail("key read"))
    return live_smoke


def test_the_live_smoke_refuses_uncommitted_hashed_code(gate, tmp_path):
    assert gate.refusal(tmp_path / "no-record.json", live_smoke=True) is None
    (gate.root / "agent").mkdir()
    (gate.root / "agent" / "anthropic_adapter.py").write_text("# a local edit\n", encoding="utf-8")
    assert "agent/anthropic_adapter.py" in gate.refusal(tmp_path / "no-record.json", live_smoke=True)


def test_the_live_smoke_command_refuses_a_dirty_adapter_before_any_key(gate, smoke_without_a_key, capsys, tmp_path):
    (gate.root / "runner" / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    assert smoke_without_a_key.main(["--env-file", str(tmp_path / ".env"), "--out", str(tmp_path / "o")]) == 2
    assert "runner/code.py" in capsys.readouterr().err
    assert not (tmp_path / "o").exists()


def test_the_live_smoke_refuses_an_environment_the_lock_doesnt_pin(gate, monkeypatch, tmp_path):
    _installed(monkeypatch, openai="0.0.1")
    assert "uv.lock" in gate.refusal(tmp_path / "no-record.json", live_smoke=True)


@pytest.mark.parametrize("arguments", [["--model", "claude-opus-5-5"], ["--model", "gpt-6-luna"],
                                       ["--provider", "openai", "--model", "claude-haiku-5-5"]])
def test_the_live_smoke_runs_only_its_provider_s_decision_0010_model(gate, smoke_without_a_key, capsys, tmp_path, arguments):
    argv = [*arguments, "--env-file", str(tmp_path / ".env"), "--out", str(tmp_path / "o")]
    assert smoke_without_a_key.main(argv) == 2
    assert "decision 0010" in capsys.readouterr().err
    assert not (tmp_path / "o").exists()


# --- each invocation states the machine it ran on ----------------------------------------------


def test_each_invocation_records_the_machine_facts_nothing_hashes(gate):
    gate.rerun()
    lines = [json.loads(line) for line in (gate.mock / paid_run.PROVENANCE_FILE).read_text().splitlines()]
    for line in lines[-2:]:
        assert line["os_build"] == f"{platform.platform()} {platform.version()}"
        assert line["python_build"] == sys.version
        assert line["sqlite_version"] == sqlite3.sqlite_version
        assert line["uv_lock_sha256"] == hashlib.sha256((gate.root / "uv.lock").read_bytes()).hexdigest()
        assert line["sandbox"] == paid_run.sandbox.describe()


# --- the Gate 2 scripts run only from the code that ran their grid -----------------------------


BUDGET_ARGUMENTS = ["--remaining-balance-usd", "9.0", "--reserve-usd", "1.0", "--conservative-c1-trial-cost-usd", "0.01"]


@pytest.fixture
def live_grid(gate, tmp_path, monkeypatch):
    """A live-model grid's records with the provenance a real invocation writes, and no paid-run record."""
    from tests.test_floor_count import grid

    monkeypatch.setattr(paid_run, "RECORD", tmp_path / "no-record.json")
    run = tmp_path / "grid-live"
    for index, (record, log) in enumerate(grid()):
        trial_dir = run / f"t{index:04d}"
        trial_dir.mkdir(parents=True)
        record["usage"].update(input_tokens=1000, output_tokens=200)
        (trial_dir / "results.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
        (trial_dir / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in log), encoding="utf-8")
    _append_provenance(run)
    return run


def _append_provenance(run, **changes):
    with (run / paid_run.PROVENANCE_FILE).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"phase": "start", **paid_run.code_provenance(), **changes}) + "\n")


def _floor(run):
    from analysis import floor_count

    return floor_count.main([str(run)])


def _budget(run):
    from analysis import gate2_budget

    return gate2_budget.main([str(run), *BUDGET_ARGUMENTS])


def _edit_threshold(gate):
    return (gate.root / "analysis/floor_count.py").read_text().replace("FLOOR_THRESHOLD = 3", "FLOOR_THRESHOLD = 1")


def _head(gate):
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=gate.root, env=gate.env, check=True,
                          capture_output=True, text=True).stdout.strip()


def test_the_scripts_run_from_the_code_that_ran_the_grid_with_no_record(gate, live_grid, capsys):
    """Decision 0025 item 4's November 7 close evaluates whatever records exist, record or not."""
    assert not paid_run.RECORD.exists()
    assert _floor(live_grid) == 0
    assert json.loads(capsys.readouterr().out)["code_check"].startswith("compared")
    assert _budget(live_grid) == 0
    assert json.loads(capsys.readouterr().out)["code_check"].startswith("compared")


def test_a_grid_with_a_cell_missing_is_still_evaluated(gate, live_grid, capsys):
    from analysis.floor_count import load_run

    cell = next(path for path in live_grid.glob("t*/results.jsonl")
                if (lambda r: r["condition"] == "attack" and r["configuration"] == "D0_BASELINE")(json.loads(path.read_text())))
    shutil.rmtree(cell.parent)
    assert len(load_run(live_grid)) == 89
    assert _floor(live_grid) == 0
    assert json.loads(capsys.readouterr().out)["counts"]["missing"] == 1


@pytest.mark.parametrize("script", [_floor, _budget])
def test_a_threshold_edited_after_the_grid_is_refused_naming_the_commit(gate, live_grid, capsys, script):
    grid_commit = _head(gate)
    gate.commit_code("analysis/floor_count.py", _edit_threshold(gate))
    assert script(live_grid) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and "scoring code" in captured.err and grid_commit in captured.err


def test_an_uncommitted_threshold_edit_is_refused(gate, live_grid, capsys):
    (gate.root / "analysis" / "floor_count.py").write_text(_edit_threshold(gate), encoding="utf-8")
    assert _floor(live_grid) == 1
    assert "scoring code" in capsys.readouterr().err


@pytest.mark.parametrize("path", ["analysis/gate2_budget.py", "analysis/__init__.py", "analysis/defense_readiness.py",
                                  "paper/estimand_manifest.json"])
def test_each_scoring_file_is_covered(gate, live_grid, capsys, path):
    gate.commit_code(path, "# an edit\n")
    assert _floor(live_grid) == 1
    assert _budget(live_grid) == 1


def test_a_runner_fix_between_invocations_leaves_the_grid_scoreable(gate, live_grid, capsys):
    """The November 7 case: a grid resumed across a one-line fix to hashed code. Resuming is the
    only recovery, because the ceiling rules out a second grid."""
    gate.commit_code("runner/code.py", "VALUE = 2\n")
    _append_provenance(live_grid)
    assert _floor(live_grid) == 0
    capsys.readouterr()
    gate.commit_code("runner/code.py", "VALUE = 3\n")
    assert _floor(live_grid) == 0
    assert _budget(live_grid) == 0


def test_report_code_landing_elsewhere_in_analysis_doesn_t_refuse(gate, live_grid, capsys):
    gate.commit_code("analysis/report_later.py", "VALUE = 1\n")
    (gate.root / "analysis" / "uncommitted_report.py").write_text("VALUE = 1\n", encoding="utf-8")
    assert _floor(live_grid) == 0
    assert _budget(live_grid) == 0


def test_a_raised_price_bound_refuses_neither_script(gate, live_grid, capsys, monkeypatch):
    gate.commit_code("analysis/price_bound.py", "PRICE_BOUND_USD = 0.07\n")
    monkeypatch.setitem(sys.modules, "analysis.price_bound", SimpleNamespace(PRICE_BOUND_USD=0.07))
    assert _budget(live_grid) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["price_bound_usd"] == 0.07 and report["price_bound_source"] == "analysis/price_bound.py"
    assert _floor(live_grid) == 0


def test_the_budget_says_when_no_bound_module_is_on_this_checkout(gate, live_grid, capsys, monkeypatch):
    monkeypatch.setitem(sys.modules, "analysis.price_bound", None)
    assert _budget(live_grid) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["price_bound_usd"] is None and report["price_bound_source"].startswith("none")


def test_a_forged_pyc_of_a_scoring_module_is_refused(gate, live_grid, capsys):
    """Its source still matches, but Python would run this instead."""
    _write(gate.root / importlib.util.cache_from_source("analysis/floor_count.py"),
           _shadow_pyc(gate, code="FLOOR_THRESHOLD = 1\n", source="analysis/floor_count.py"))
    assert _floor(live_grid) == 1
    assert "floor_count" in capsys.readouterr().err


@pytest.mark.parametrize("script", [_floor, _budget])
def test_deleting_a_real_grid_s_provenance_doesn_t_evade_the_check(gate, live_grid, capsys, script):
    (live_grid / paid_run.PROVENANCE_FILE).unlink()
    gate.commit_code("analysis/floor_count.py", _edit_threshold(gate))
    assert script(live_grid) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and paid_run.PROVENANCE_FILE in captured.err


def test_a_mock_grid_without_provenance_is_allowed_and_says_so(gate, capsys):
    (gate.mock / paid_run.PROVENANCE_FILE).unlink()
    assert paid_run.check_code_matches_run(gate.mock).startswith("not compared")


def test_an_unreadable_result_doesn_t_count_as_a_mock_run(gate):
    (gate.mock / paid_run.PROVENANCE_FILE).unlink()
    (gate.trial() / "results.jsonl").write_text("not json\n", encoding="utf-8")
    with pytest.raises(paid_run.PaidRunRefused, match=paid_run.PROVENANCE_FILE):
        paid_run.check_code_matches_run(gate.mock)


def test_a_torn_last_line_is_no_provenance_line(gate, live_grid, capsys):
    with (live_grid / paid_run.PROVENANCE_FILE).open("a", encoding="utf-8") as handle:
        handle.write('{"phase": "st')
    assert _floor(live_grid) == 0


@pytest.mark.parametrize("line", ["not json\n", "[]\n"])
def test_unreadable_provenance_is_refused(gate, live_grid, capsys, line):
    with (live_grid / paid_run.PROVENANCE_FILE).open("a", encoding="utf-8") as handle:
        handle.write(line)
    assert _floor(live_grid) == 1
    assert "code_provenance" in capsys.readouterr().err


@pytest.mark.parametrize("changes", [{"scoring_digest": None}, {"scoring_digest": "0" * 64, "code_commit": "abc123"}])
def test_a_later_invocation_on_other_scoring_code_is_refused(gate, live_grid, capsys, changes):
    _append_provenance(live_grid, **changes)
    assert _floor(live_grid) == 1
    captured = capsys.readouterr().err
    assert "scoring code" in captured and _head(gate) in captured


def test_an_earlier_invocation_on_other_scoring_code_is_refused(gate, live_grid, capsys):
    """Not only the last line counts: this grid's first trials ran under another threshold."""
    path = live_grid / paid_run.PROVENANCE_FILE
    current = path.read_text(encoding="utf-8")
    path.write_text(json.dumps({"phase": "start", "scoring_digest": "0" * 64, "code_commit": "abc123"}) + "\n" + current,
                    encoding="utf-8")
    assert _floor(live_grid) == 1
    captured = capsys.readouterr().err
    assert "scoring code" in captured and "abc123" in captured and _head(gate) in captured


def test_a_mock_grid_gets_past_the_self_check_to_its_own_refusal(gate, capsys):
    assert _floor(gate.mock) == 1
    assert "mock-provider records never count" in capsys.readouterr().err


# --- spend: the gate reads the ledger and the cap outside this checkout (tests/test_spend_ledger.py) ---


def test_every_paid_path_refuses_without_a_ledger_or_a_cap(gate, tmp_path):
    from runner import spend_ledger

    record = gate.open()
    assert gate.refusal(record) is None
    assert gate.refusal(tmp_path / "no-record.json", live_smoke=True) is None
    spend_ledger.ledger_path().unlink()
    for reason in (gate.refusal(record), gate.refusal(tmp_path / "no-record.json", live_smoke=True)):
        assert reason is not None and "ledger" in reason and "init" in reason
    spend_ledger.init()
    spend_ledger.cap_path().unlink()
    for reason in (gate.refusal(record), gate.refusal(tmp_path / "no-record.json", live_smoke=True)):
        assert reason is not None and "set-cap" in reason


def test_a_spent_cap_refuses_every_paid_path_and_pilots_can_t_get_around_it(gate, tmp_path):
    from runner import spend_ledger

    record = gate.open()
    spend_ledger.set_cap(0.00014 + spend_ledger.TRIAL_BOUND_USD / 2)
    for reason in (gate.refusal(record), gate.refusal(tmp_path / "no-record.json", live_smoke=True)):
        assert reason is not None and "cap" in reason


def test_raising_the_cap_never_closes_paid_runs(gate):
    from runner import spend_ledger

    record = gate.open()
    spend_ledger.set_cap(50.0)
    assert gate.refusal(record) is None


def test_each_invocation_echoes_the_cap_into_its_provenance(gate):
    from runner import spend_ledger

    spend_ledger.set_cap(9.5)
    gate.rerun()
    lines = [json.loads(line) for line in (gate.mock / paid_run.PROVENANCE_FILE).read_text().splitlines()]
    assert [line["spend_cap_usd"] for line in lines[-2:]] == [9.5, 9.5]
    spend_ledger.cap_path().unlink()
    gate.rerun()  # a mock run needs no cap, and says so
    assert json.loads((gate.mock / paid_run.PROVENANCE_FILE).read_text().splitlines()[-1])["spend_cap_usd"] is None


def test_a_whole_grid_s_bound_above_the_cap_doesn_t_refuse_it_at_the_start(gate):
    """The check is per trial: refusing on a whole run's bound would refuse the sweep at its start."""
    from runner import spend_ledger

    record = gate.open()
    spend_ledger.set_cap(1.0)
    assert 90 * spend_ledger.TRIAL_BOUND_USD > 1.0
    assert gate.refusal(record, new_trials=90) is None


def test_a_grid_that_would_pass_the_ceiling_is_refused_at_its_start(gate):
    from runner import spend_ledger

    record = gate.open()
    assert gate.refusal(record, new_trials=119) is None  # the October 10 check is the first of 120
    assert "120" in gate.refusal(record, new_trials=120)
