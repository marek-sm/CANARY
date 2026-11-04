"""Paid-run gate checks that mutation testing found unpinned
(reports/cloud/mutation.md). Each test names the surviving mutants it kills.

No test here makes or enables a provider call: ``RealProvider`` raises if it
is ever called, and every passing path is a refusal or a direct call to a
refusal helper.
"""

import hashlib
import json
import subprocess

import pytest

from runner import paid_run
from runner.mock_slice import validator
from tests.test_tool_sandbox import (  # noqa: F401  (fixtures used by name)
    RealProvider,
    _record,
    clean_environment,
    preflight,
    repo,
)


@pytest.mark.parametrize("name", ["ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "OPENAI_API_KEY", "OPENAI_ORG_ID"])
def test_any_ambient_provider_variable_refuses(clean_environment, monkeypatch, tmp_path, name):
    # Kills x_environment_refusal__mutmut_10/11: the existing test sets only
    # OPENAI_API_KEY, so a broken ANTHROPIC_ prefix let an ambient Anthropic key through.
    monkeypatch.setenv(name, "synthetic-not-a-key")
    assert paid_run.environment_refusal() == f"unset ambient provider variables first: {name}"
    with pytest.raises(paid_run.PaidRunRefused, match=name):
        paid_run.require_paid_run(RealProvider(), record_path=tmp_path / "missing.json")
    with pytest.raises(paid_run.PaidRunRefused, match=name):
        paid_run.require_paid_run(RealProvider(), live_smoke=True, record_path=tmp_path / "missing.json")


def test_the_refusal_lists_every_ambient_variable_sorted(clean_environment, monkeypatch):
    # Kills x_environment_refusal__mutmut_15/18 (message text and separator).
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic")
    assert paid_run.environment_refusal() == (
        "unset ambient provider variables first: ANTHROPIC_API_KEY, OPENAI_API_KEY"
    )
    monkeypatch.setenv("CI", "")  # set but empty still counts: CI is present
    assert paid_run.environment_refusal() == "CI is set; paid calls never run in CI"


def test_a_lowercase_or_unrelated_variable_does_not_refuse(clean_environment, monkeypatch):
    monkeypatch.setenv("anthropic_api_key_note", "x")
    monkeypatch.setenv("MY_ANTHROPIC_API_KEY", "x")
    assert paid_run.environment_refusal() is None


def test_require_paid_run_reads_the_record_it_is_given(clean_environment, tmp_path):
    # Kills x_require_paid_run__mutmut_6/8, which dropped record_path and read the
    # repository's default record path instead.
    missing = tmp_path / "given" / "record.json"
    with pytest.raises(paid_run.PaidRunRefused) as refused:
        paid_run.require_paid_run(RealProvider(), record_path=missing)
    assert str(missing) in str(refused.value)


def test_require_paid_run_passes_the_live_smoke_exception_through(clean_environment, tmp_path):
    # Kills x_require_paid_run__mutmut_5/7, which dropped live_smoke. The live smoke
    # still needs the sandbox and a clean environment; it needs no record.
    assert paid_run.require_paid_run(RealProvider(), live_smoke=True, record_path=tmp_path / "missing.json") is None
    with pytest.raises(paid_run.PaidRunRefused, match="no paid-run record"):
        paid_run.require_paid_run(RealProvider(), live_smoke=False, record_path=tmp_path / "missing.json")


def test_dirty_paths_name_each_untracked_file_under_the_hashed_directories_only(repo):
    # Kills x_dirty_paths__mutmut_9 (untracked directories collapsed), _11 (every
    # directory in the repository counted), and _20 (the path's first character cut).
    root, _ = repo
    (root / "README.md").write_text("not hashed\n", encoding="utf-8")
    (root / "results").mkdir()
    (root / "results" / "out.json").write_text("{}\n", encoding="utf-8")
    assert paid_run.dirty_paths(root) == []
    (root / "runner" / "sub").mkdir()
    (root / "runner" / "sub" / "new.py").write_text("X = 1\n", encoding="utf-8")
    assert paid_run.dirty_paths(root) == ["runner/sub/new.py"]


def test_code_hashes_cover_the_hashed_directories_only(repo):
    # Kills x_tracked_files__mutmut_10 (every tracked file hashed).
    root, env = repo
    (root / "README.md").write_text("docs\n", encoding="utf-8")
    (root / "uv.lock").write_text("lock\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "more"], cwd=root, check=True, env=env)
    hashes = paid_run.code_hashes(root)
    assert sorted(hashes) == ["runner/code.py", "uv.lock"]
    assert hashes["uv.lock"] == hashlib.sha256(b"lock\n").hexdigest()


def test_code_digest_is_the_sha256_of_compact_sorted_json():
    # Kills x_code_digest__mutmut_4..13: the digest is compared with digests that
    # earlier runs wrote to code_provenance.jsonl, so its serialization is fixed.
    hashes = {"runner/b.py": "2" * 64, "agent/a.py": "1" * 64}
    expected = hashlib.sha256(
        ('{"agent/a.py":"' + "1" * 64 + '","runner/b.py":"' + "2" * 64 + '"}').encode("utf-8")
    ).hexdigest()
    assert paid_run.code_digest(hashes) == expected


def test_the_code_refusal_names_changed_added_and_removed_files(clean_environment, repo, tmp_path):
    # Kills x_paid_run_refusal__mutmut_27/32/33/34 (which paths the refusal names).
    root, env = repo
    record = _record(root, tmp_path / "record.json")
    (root / "runner" / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    (root / "runner" / "added.py").write_text("NEW = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "change"], cwd=root, check=True, env=env)
    assert paid_run.paid_run_refusal(record_path=record, root=root) == (
        "code differs from the paid-run record: runner/added.py, runner/code.py"
    )


def _events_with_sandbox(run, name, mode):
    trial = run / name
    trial.mkdir(parents=True)
    versions = {"runner": "t"} if mode is None else {"runner": "t", "tool_sandbox": mode}
    lines = [{"sequence": 1, "component_versions": versions}, {"sequence": 2, "component_versions": versions}]
    (trial / "events.jsonl").write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")


def test_a_mock_grid_under_two_sandboxes_or_an_unrecorded_one_is_refused(tmp_path):
    # Kills x__mock_run_sandbox__mutmut (`or` -> `and` and friends): a mixed or unknown
    # sandbox can't be the one the paid run is bound to.
    mixed = tmp_path / "mixed"
    _events_with_sandbox(mixed, "t1", "linux-bwrap:tool-sandbox-v0.3.0:" + "a" * 16)
    _events_with_sandbox(mixed, "t2", "linux-bwrap:tool-sandbox-v0.3.0:" + "b" * 16)
    with pytest.raises(paid_run.PaidRunRefused, match="one recorded tool sandbox"):
        paid_run._mock_run_sandbox(mixed)
    unknown = tmp_path / "unknown"
    _events_with_sandbox(unknown, "t1", None)
    with pytest.raises(paid_run.PaidRunRefused, match="None"):
        paid_run._mock_run_sandbox(unknown)
    one = tmp_path / "one"
    _events_with_sandbox(one, "t1", "linux-bwrap:tool-sandbox-v0.3.0:" + "c" * 16)
    _events_with_sandbox(one, "t2", "linux-bwrap:tool-sandbox-v0.3.0:" + "c" * 16)
    assert paid_run._mock_run_sandbox(one) == "linux-bwrap:tool-sandbox-v0.3.0:" + "c" * 16
    with pytest.raises(paid_run.PaidRunRefused):
        paid_run._mock_run_sandbox(tmp_path / "empty")


def test_the_record_is_schema_valid_and_states_what_was_checked(preflight, tmp_path):
    # Kills the build_record key- and value-renaming mutants: the happy-path test only
    # compared code_sha256.
    root, env, run, record = preflight
    built = record(run(tmp_path / "mock"))
    validator("paid_run_record").validate(built)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, env=env,
                          check=True).stdout.strip()
    assert built["recorded_commit"] == head
    assert built["recorded_by"] == "marek-sm"
    assert built["sandbox"] == built["conditions"]["mock_grid"]["tool_sandbox"]
    assert built["conditions"]["mock_grid"]["verify_complete"] is True
    assert built["conditions"]["tool_result_delivery"] == {"merged_in": "#61"}
    assert built["conditions"]["tool_sandbox"] == {"merged_in": "#64"}
    assert built["conditions"]["request_to_effect"] == {"merged_in": "#39"}


def test_the_record_verifies_the_mock_run_it_is_given(preflight, tmp_path, monkeypatch):
    # Kills x_build_record__mutmut (verify_grid_run(None, ...)) and the incomplete-grid
    # refusal: the fixture's stand-in verifier ignored its argument.
    from runner import grid_dev

    root, env, run, record = preflight
    mock = run(tmp_path / "mock")
    seen = []

    def verify(run_dir, spec):
        seen.append(run_dir)
        return {"complete": False, "experiment_id": spec["experiment_id"], "trials_found": 1}

    monkeypatch.setattr(grid_dev, "verify_grid_run", verify)
    with pytest.raises(paid_run.PaidRunRefused, match="isn't complete"):
        record(mock)
    assert seen == [mock]


def test_the_record_refuses_unfinished_trials_by_name(preflight, tmp_path):
    root, env, run, record = preflight
    mock = run(tmp_path / "mock")
    [results] = list(mock.glob("*/results.jsonl"))
    line = json.loads(results.read_text(encoding="utf-8"))
    line["status"] = "infrastructure_failure"
    results.write_text(json.dumps(line) + "\n", encoding="utf-8")
    with pytest.raises(paid_run.PaidRunRefused, match=f"didn't complete: {results.parent.name}$"):
        record(mock)


def test_the_record_refuses_an_untracked_hashed_file_present_at_recording(preflight, tmp_path):
    # Kills x_build_record__mutmut (`dirty = None`): a clean preflight doesn't excuse a
    # dirty checkout when the record is written; the committed hashes can't see it.
    root, env, run, record = preflight
    mock = run(tmp_path / "mock")
    (root / "runner" / "late.py").write_text("LATE = 1\n", encoding="utf-8")
    with pytest.raises(paid_run.PaidRunRefused, match="commit or discard these changes before recording: runner/late.py"):
        record(mock)


def test_check_reports_a_refusal_with_a_failing_exit_code(clean_environment, monkeypatch, capsys):
    # Kills x_main mutants on the `check` path (no test called main before).
    monkeypatch.setenv("CI", "true")
    assert paid_run.main(["check"]) == 1
    assert capsys.readouterr().out == "CI is set; paid calls never run in CI\n"
    monkeypatch.setattr(paid_run, "paid_run_refusal", lambda: None)
    assert paid_run.main(["check"]) == 0
    assert capsys.readouterr().out == "paid runs may start here\n"


def test_record_validates_before_writing(monkeypatch, tmp_path, capsys):
    # Kills x_main mutants on the `record` path: an invalid record is never written,
    # and a valid one is written as sorted, indented JSON.
    from jsonschema import ValidationError

    target = tmp_path / "protocol" / "paid_run_record.json"
    target.parent.mkdir()
    monkeypatch.setattr(paid_run, "RECORD", target)
    monkeypatch.setattr(paid_run, "REPO_ROOT", tmp_path)
    seen = {}

    def build(mock_run, *, delivery, sandbox_pr, request_to_effect):
        seen.update(mock_run=mock_run, delivery=delivery, sandbox_pr=sandbox_pr, request_to_effect=request_to_effect)
        return {"schema_version": "1.0.0"}

    monkeypatch.setattr(paid_run, "build_record", build)
    argv = ["record", str(tmp_path / "mock"), "--delivery", "#61", "--sandbox", "#64", "--request-to-effect", "#39"]
    with pytest.raises(ValidationError):
        paid_run.main(argv)
    assert not target.exists()
    assert seen == {"mock_run": tmp_path / "mock", "delivery": "#61", "sandbox_pr": "#64", "request_to_effect": "#39"}

    valid = {
        "schema_version": "1.0.0", "recorded_on": "2026-11-04", "recorded_by": "marek-sm", "recorded_commit": "0" * 40,
        "sandbox": "linux-bwrap:tool-sandbox-v0.3.0:" + "0" * 16,
        "conditions": {
            "tool_result_delivery": {"merged_in": "#61"}, "request_to_effect": {"merged_in": "#39"},
            "tool_sandbox": {"merged_in": "#64"},
            "mock_grid": {"experiment_id": "grid-dev", "trials": 90, "verify_complete": True,
                          "tool_sandbox": "linux-bwrap:tool-sandbox-v0.3.0:" + "0" * 16},
        },
        "code_sha256": {"runner/code.py": "0" * 64},
    }
    monkeypatch.setattr(paid_run, "build_record", lambda *a, **k: valid)
    assert paid_run.main(argv) == 0
    assert target.read_text(encoding="utf-8") == json.dumps(valid, indent=2, sort_keys=True) + "\n"
    assert "protocol/paid_run_record.json" in capsys.readouterr().out


def test_the_record_refuses_a_mock_grid_run_without_tool_result_delivery(preflight, tmp_path):
    # No test ran this refusal: only message mutants of it survived, so deleting the
    # check would also have passed.
    from runner import execute

    root, env, run, record = preflight
    mock = run(tmp_path / "mock")
    (mock / execute.MODE_FILE).write_text(json.dumps({"delivery": False}), encoding="utf-8")
    with pytest.raises(paid_run.PaidRunRefused, match="^the mock grid didn't run with tool-result delivery$"):
        record(mock)


def test_the_record_refuses_on_another_sandbox_than_the_mock_grid_ran_under(preflight, tmp_path, monkeypatch):
    from tools import sandbox

    root, env, run, record = preflight
    mock = run(tmp_path / "mock")
    recorded = sandbox.describe()
    monkeypatch.setattr(sandbox, "describe", lambda: recorded[:-16] + "f" * 16)
    with pytest.raises(paid_run.PaidRunRefused, match="^record the paid run on the machine and sandbox"):
        record(mock)


def test_the_record_refuses_a_preflight_whose_provenance_is_unknown(preflight, tmp_path):
    # A provenance line without git (dirty_paths null) is refused and says why.
    root, env, run, record = preflight
    mock = run(tmp_path / "mock")
    provenance = mock / paid_run.PROVENANCE_FILE
    lines = [json.loads(line) for line in provenance.read_text(encoding="utf-8").splitlines()]
    lines[0]["dirty_paths"] = None
    provenance.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
    with pytest.raises(paid_run.PaidRunRefused, match="uncommitted changes in recorded code: unknown, without git$"):
        record(mock)
    lines[0]["dirty_paths"] = ["runner/a.py", "runner/b.py"]
    provenance.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
    with pytest.raises(paid_run.PaidRunRefused, match="uncommitted changes in recorded code: runner/a.py, runner/b.py$"):
        record(mock)
