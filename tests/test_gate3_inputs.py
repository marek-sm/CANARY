"""Decision 0038's Stage 1 inputs to the Gate 3 step.

G3-2: `analysis.lead_outputs` read a trial's raw events from beside whichever
`results.jsonl` it globbed, while `runner.sweep.verify_sweep` checked the events in the
trial's scheduled directory (`execute.trial_slug`). A results file moved into another
directory beside edited events passed the verifier and fed those unverified events into
the count-only tables. The sweep here is the real one, through tests/test_sweep.py's fake
provider and stand-in Gate 3 state; nothing reaches a network.
"""

from __future__ import annotations

import json

import pytest

from analysis import lead_outputs
from runner import sweep
from tests.test_sweep import _run, corpus, frozen, provider  # noqa: F401  (fixtures; frozen is autouse)


def _sweep(gate, provider, corpus, tmp_path):
    gate.open()
    out = tmp_path / "sweep"
    _run(provider, corpus, out)
    return out


def _move_one_result_beside_edited_events(out):
    """Move one trial's committed result into `zz/`, beside an edited copy of its events:
    the copy repeats its last event under the next sequence number, so it is not the
    evidence the verifier recomputed."""
    trial_dir = sorted(path.parent for path in out.glob(f"*/{sweep.RESULTS_FILE}"))[0]
    moved = out / "zz"
    moved.mkdir()
    (trial_dir / sweep.RESULTS_FILE).rename(moved / sweep.RESULTS_FILE)
    events = [json.loads(line) for line in (trial_dir / "events.jsonl").read_text(encoding="utf-8").split("\n") if line]
    events.append({**events[-1], "sequence": events[-1].get("sequence", 0) + 1})
    (moved / "events.jsonl").write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
    return trial_dir, moved


def test_g3_2_events_beside_a_moved_result_are_refused(gate, provider, corpus, tmp_path):
    out = _sweep(gate, provider, corpus, tmp_path)
    _move_one_result_beside_edited_events(out)
    # The verifier still passes: it checks the scheduled directory's events, which are intact.
    assert sweep.verify_sweep(out, corpus)["complete"] is True
    report = tmp_path / "report.md"
    with pytest.raises(ValueError, match="not the directory the verifier checked"):
        lead_outputs.main([str(out), "--out", str(report), "--corpus-root", str(corpus)])
    assert not report.exists()


def test_g3_2_an_events_run_with_a_moved_result_is_refused(gate, provider, corpus, tmp_path):
    out = _sweep(gate, provider, corpus, tmp_path)
    records = [json.loads(line) for path in sorted(out.glob(f"*/{sweep.RESULTS_FILE}"))
               for line in path.read_text(encoding="utf-8").split("\n") if line]
    released = tmp_path / "results.jsonl"
    released.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    _move_one_result_beside_edited_events(out)
    report = tmp_path / "report.md"
    with pytest.raises(ValueError, match="not the directory the verifier checked"):
        lead_outputs.main([str(released), "--events", str(out), "--out", str(report), "--corpus-root", str(corpus)])
    assert not report.exists()


def test_g3_2_an_intact_verified_run_still_generates_every_table(gate, provider, corpus, tmp_path):
    out = _sweep(gate, provider, corpus, tmp_path)
    report = tmp_path / "report.md"
    assert lead_outputs.main([str(out), "--out", str(report), "--corpus-root", str(corpus)]) == 0
    text = report.read_text(encoding="utf-8")
    assert "PRE-RESULTS" not in text and lead_outputs.NEEDS_RAW_EVENTS_TEXT not in text


# --------------------------------------------------------------------------
# analysis.gate3_hashes (decision 0038 items 4 and 5), on a scratch git tree
# --------------------------------------------------------------------------

import hashlib  # noqa: E402
import subprocess  # noqa: E402

from analysis import gate3_hashes  # noqa: E402

LEDGER = "e" * 64


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture
def tree(tmp_path):
    root = tmp_path / "tree"
    files = {
        "analysis/__init__.py": "",
        "analysis/zeta.py": "Z = 1\n",
        "analysis/Alpha.py": "A = 1\n",  # upper case sorts before lower case by bytes
        "analysis/sanitizer.py": "S = 1\n",
        "analysis/engineering_report.py": "R = 1\n",
        "paper/estimand_manifest.json": "{}\n",
        "corpus/freeze.json": json.dumps({"source_ledger_hash": LEDGER}),
        "protocol/engineering_validation_plan.json": json.dumps({"validation_id": "CANARY-TEST-ENG-V1"}),
        "schemas/engineering_validation.schema.json": "{}\n",
        "runner/other.py": "O = 1\n",
    }
    for path, text in files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(text, encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "t")
    return root


def _sha(root, path):
    return hashlib.sha256((root / path).read_bytes()).hexdigest()


def _expected_analysis_hash(root):
    paths = ["analysis/Alpha.py", "analysis/__init__.py", "analysis/engineering_report.py", "analysis/zeta.py",
             "paper/estimand_manifest.json"]
    return hashlib.sha256("\n".join(f"{p} {_sha(root, p)}" for p in paths).encode("utf-8")).hexdigest()


# Decision 0039: the host environment the step machine reads, injected so CI's runner
# (whose sandbox or uv.lock may be absent) doesn't decide a test.
HOST = {"os_build": "macOS-26.1-arm64 Darwin Kernel 27.2.0", "python_build": "3.11.9 (main) [Clang 16]",
        "sqlite_version": "3.45.1", "uv_lock_sha256": "a" * 64,
        "sandbox": "macos-sandbox-exec:tool-sandbox-v0.3.0:10ee91ae313186fa"}


@pytest.fixture(autouse=True)
def _host(monkeypatch):
    monkeypatch.setattr(gate3_hashes, "_machine_facts", lambda root: {**HOST, "unrelated": "x"})


def _active(tree, tier_class="ALL", **changes):
    computed = gate3_hashes.compute(tree)
    active = {"tier": "F20" if tier_class == "ALL" else tier_class, "tier_class": tier_class,
              "empirical": {"analysis_hash": computed["analysis_hash"], "null_reasons": {}},
              "engineering_fallback": dict(computed["engineering_fallback"]),
              "host_environment": dict(computed["host_environment"])}
    if tier_class == "ENGINEERING":
        active["empirical"] = {"analysis_hash": None, "null_reasons": {"analysis_hash": "no generator at ENGINEERING"}}
    for dotted, value in changes.items():
        block, field = dotted.split("__")
        active[block][field] = value
    return active


def test_the_analysis_hash_is_the_record_s_definition(tree):
    computed = gate3_hashes.compute(tree)
    assert computed["analysis_hash"] == _expected_analysis_hash(tree)
    assert computed["engineering_fallback"] == {
        "validation_id": "CANARY-TEST-ENG-V1", "source_ledger_hash": LEDGER,
        "validation_plan_hash": _sha(tree, "protocol/engineering_validation_plan.json"),
        "validation_schema_hash": _sha(tree, "schemas/engineering_validation.schema.json"),
        "report_generator_hash": _sha(tree, "analysis/engineering_report.py")}


def test_the_sanitizer_and_files_outside_analysis_are_not_covered(tree):
    before = gate3_hashes.compute(tree)["analysis_hash"]
    for path in ("analysis/sanitizer.py", "runner/other.py"):
        (tree / path).write_text("changed = True\n", encoding="utf-8")
    _git(tree, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-qam", "t2")
    assert gate3_hashes.compute(tree)["analysis_hash"] == before


@pytest.mark.parametrize("path", ["analysis/zeta.py", "paper/estimand_manifest.json"])
def test_a_committed_change_to_a_covered_file_changes_the_hash(tree, path):
    before = gate3_hashes.compute(tree)["analysis_hash"]
    (tree / path).write_text("changed = True\n", encoding="utf-8")
    _git(tree, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-qam", "t2")
    assert gate3_hashes.compute(tree)["analysis_hash"] != before


@pytest.mark.parametrize("damage", ["modified", "untracked"])
def test_a_checkout_that_isnt_clean_is_refused(tree, damage):
    if damage == "modified":
        (tree / "analysis/zeta.py").write_text("Z = 2\n", encoding="utf-8")
    else:
        (tree / "analysis/extra.py").write_text("E = 1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not a clean checkout"):
        gate3_hashes.compute(tree)
    assert gate3_hashes.main(["--root", str(tree)]) == 1


def test_a_pending_validation_id_is_refused(tree):
    (tree / "protocol/engineering_validation_plan.json").write_text(json.dumps({"validation_id": "PENDING-validation-id"}))
    _git(tree, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-qam", "t2")
    with pytest.raises(ValueError, match="validation_id"):
        gate3_hashes.compute(tree)


@pytest.mark.parametrize("tier_class", ["ALL", "ENGINEERING"])
def test_the_check_passes_an_active_json_that_agrees(tree, tmp_path, tier_class, capsys):
    path = tmp_path / "active.json"
    path.write_text(json.dumps(_active(tree, tier_class)), encoding="utf-8")
    assert gate3_hashes.main(["--root", str(tree), "--check", str(path)]) == 0


@pytest.mark.parametrize("tier_class", ["ALL", "ENGINEERING"])
@pytest.mark.parametrize("field", gate3_hashes.FALLBACK_FIELDS)
@pytest.mark.parametrize("value", [None, "0" * 64])
def test_the_check_refuses_a_null_or_mismatched_fallback_field(tree, tmp_path, tier_class, field, value, capsys):
    path = tmp_path / "active.json"
    path.write_text(json.dumps(_active(tree, tier_class, **{f"engineering_fallback__{field}": value})), encoding="utf-8")
    assert gate3_hashes.main(["--root", str(tree), "--check", str(path)]) == 1
    assert f"engineering_fallback.{field}" in capsys.readouterr().err


@pytest.mark.parametrize("value", [None, "0" * 64])
def test_the_check_refuses_an_empirical_analysis_hash_that_is_null_or_wrong(tree, tmp_path, value, capsys):
    path = tmp_path / "active.json"
    path.write_text(json.dumps(_active(tree, "ALL", empirical__analysis_hash=value)), encoding="utf-8")
    assert gate3_hashes.main(["--root", str(tree), "--check", str(path)]) == 1
    assert "empirical.analysis_hash" in capsys.readouterr().err


@pytest.mark.parametrize("changes", [{"empirical__analysis_hash": "0" * 64}, {"empirical__null_reasons": {}},
                                     {"empirical__null_reasons": {"analysis_hash": " "}}])
def test_at_engineering_the_analysis_hash_is_null_with_its_own_reason(tree, tmp_path, changes, capsys):
    path = tmp_path / "active.json"
    path.write_text(json.dumps(_active(tree, "ENGINEERING", **changes)), encoding="utf-8")
    assert gate3_hashes.main(["--root", str(tree), "--check", str(path)]) == 1
    assert "empirical.analysis_hash" in capsys.readouterr().err


def test_stop_is_not_checked_here(tree, tmp_path):
    path = tmp_path / "active.json"
    path.write_text(json.dumps({"tier": "STOP", "tier_class": "STOP"}), encoding="utf-8")
    assert gate3_hashes.main(["--root", str(tree), "--check", str(path)]) == 1


def test_this_checkout_s_hash_prints():
    if gate3_hashes._clean_refusal(gate3_hashes.ROOT, [*gate3_hashes.analysis_paths(), gate3_hashes.CORPUS_FREEZE]):
        pytest.skip("this checkout has uncommitted changes under analysis/")
    assert len(gate3_hashes.analysis_hash()) == 64


# --------------------------------------------------------------------------
# Decision 0039: the host environment in protocol/active.json
# --------------------------------------------------------------------------


def test_compute_reads_exactly_the_five_host_fields(tree):
    assert gate3_hashes.compute(tree)["host_environment"] == HOST
    assert gate3_hashes.HOST_FIELDS == ("os_build", "python_build", "sqlite_version", "uv_lock_sha256", "sandbox")


@pytest.mark.parametrize("tier_class", ["ALL", "ENGINEERING"])
@pytest.mark.parametrize("field", ["os_build", "python_build", "sqlite_version", "uv_lock_sha256", "sandbox"])
@pytest.mark.parametrize("value", [None, "something else"])
def test_the_check_refuses_a_null_or_different_host_field(tree, tmp_path, tier_class, field, value, capsys):
    path = tmp_path / "active.json"
    path.write_text(json.dumps(_active(tree, tier_class, **{f"host_environment__{field}": value})), encoding="utf-8")
    assert gate3_hashes.main(["--root", str(tree), "--check", str(path)]) == 1
    assert f"host_environment.{field}" in capsys.readouterr().err


@pytest.mark.parametrize("tier_class", ["ALL", "ENGINEERING"])
def test_the_check_refuses_an_active_json_without_a_host_environment(tree, tmp_path, tier_class, capsys):
    active = _active(tree, tier_class)
    del active["host_environment"]
    path = tmp_path / "active.json"
    path.write_text(json.dumps(active), encoding="utf-8")
    assert gate3_hashes.main(["--root", str(tree), "--check", str(path)]) == 1
    assert "host_environment" in capsys.readouterr().err


def test_the_check_refuses_a_machine_that_can_t_read_a_host_field(tree, tmp_path, monkeypatch, capsys):
    path = tmp_path / "active.json"
    path.write_text(json.dumps(_active(tree, "ALL")), encoding="utf-8")
    monkeypatch.setattr(gate3_hashes, "_machine_facts", lambda root: {**HOST, "sandbox": None})
    assert gate3_hashes.main(["--root", str(tree), "--check", str(path)]) == 1
    assert "host_environment.sandbox" in capsys.readouterr().err


def _run_dir(tmp_path, lines):
    run = tmp_path / "run"
    run.mkdir()
    (run / "code_provenance.jsonl").write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
    return run


def _invocation(phase, **changes):
    return {"phase": phase, "code_commit": "c" * 40, "code_digest": "d" * 64, "spend_cap_usd": 9.9, **HOST, **changes}


def test_check_run_passes_when_every_invocation_ran_in_the_frozen_host(tree, tmp_path, capsys):
    active = tmp_path / "active.json"
    active.write_text(json.dumps(_active(tree, "ALL")), encoding="utf-8")
    run = _run_dir(tmp_path, [_invocation("start"), _invocation("stop"), _invocation("start"), _invocation("stop")])
    assert gate3_hashes.main(["--check-run", str(run), "--active", str(active)]) == 0


@pytest.mark.parametrize("field", ["os_build", "python_build", "sqlite_version", "uv_lock_sha256", "sandbox"])
@pytest.mark.parametrize("value", [None, "something else", "missing"])
def test_check_run_refuses_an_invocation_in_another_host(tree, tmp_path, field, value, capsys):
    active = tmp_path / "active.json"
    active.write_text(json.dumps(_active(tree, "ALL")), encoding="utf-8")
    other = _invocation("start", **{field: value})
    if value == "missing":
        del other[field]
    run = _run_dir(tmp_path, [_invocation("start"), _invocation("stop"), other])
    assert gate3_hashes.main(["--check-run", str(run), "--active", str(active)]) == 1
    err = capsys.readouterr().err
    assert field in err and "line 3" in err


@pytest.mark.parametrize("content", [None, "", "{not json\n", "[]\n"])
def test_check_run_refuses_a_run_without_readable_provenance(tree, tmp_path, content, capsys):
    active = tmp_path / "active.json"
    active.write_text(json.dumps(_active(tree, "ALL")), encoding="utf-8")
    run = tmp_path / "run"
    run.mkdir()
    if content is not None:
        (run / "code_provenance.jsonl").write_text(content, encoding="utf-8")
    assert gate3_hashes.main(["--check-run", str(run), "--active", str(active)]) == 1


def test_check_run_refuses_an_active_json_whose_host_environment_is_null(tree, tmp_path, capsys):
    active = tmp_path / "active.json"
    active.write_text(json.dumps(_active(tree, "ALL", host_environment__sandbox=None)), encoding="utf-8")
    run = _run_dir(tmp_path, [_invocation("start", sandbox=None)])
    assert gate3_hashes.main(["--check-run", str(run), "--active", str(active)]) == 1
    assert "host_environment.sandbox" in capsys.readouterr().err


@pytest.mark.parametrize("field", ["os_build", "python_build", "sqlite_version", "uv_lock_sha256", "sandbox"])
@pytest.mark.parametrize("near", ["trailing space", "case", "suffix", "number"])
def test_near_miss_host_values_are_refused_by_both_checks(tree, tmp_path, field, near, capsys):
    value = {"trailing space": HOST[field] + " ", "case": HOST[field].swapcase(),
             "suffix": HOST[field][:-1] + ("0" if HOST[field][-1] != "0" else "1"), "number": 1}[near]
    if value == HOST[field]:
        pytest.skip("this value has no letters whose case could change")
    path = tmp_path / "active.json"
    path.write_text(json.dumps(_active(tree, "ALL", **{f"host_environment__{field}": value})), encoding="utf-8")
    assert gate3_hashes.main(["--root", str(tree), "--check", str(path)]) == 1
    assert f"host_environment.{field}" in capsys.readouterr().err
    good = tmp_path / "good.json"
    good.write_text(json.dumps(_active(tree, "ALL")), encoding="utf-8")
    run = _run_dir(tmp_path, [_invocation("start"), _invocation("start", **{field: value}), _invocation("stop")])
    assert gate3_hashes.main(["--check-run", str(run), "--active", str(good)]) == 1
    err = capsys.readouterr().err
    assert field in err and "line 2" in err and "line 3" not in err


def test_check_and_check_run_can_t_be_combined(tree, tmp_path):
    path = tmp_path / "active.json"
    path.write_text(json.dumps(_active(tree, "ALL")), encoding="utf-8")
    with pytest.raises(SystemExit):
        gate3_hashes.main(["--check", str(path), "--check-run", str(tmp_path)])


@pytest.mark.parametrize("path", ["uv.lock", "tools/sandbox.py"])
def test_an_uncommitted_host_input_is_refused(tree, path):
    (tree / path).parent.mkdir(parents=True, exist_ok=True)
    (tree / path).write_text("committed\n", encoding="utf-8")
    _git(tree, "add", "-A")
    _git(tree, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-qm", "t2")
    (tree / path).write_text("edited\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not a clean checkout"):
        gate3_hashes.compute(tree)
