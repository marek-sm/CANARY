"""W7-T1 predeclaration, source fidelity, isolation, and durable mock evidence."""
import copy
import json
import shutil
from pathlib import Path

import pytest

from agent.loop import MAX_STEPS
from corpus import build_c1
from runner import coverage, delivery, execute, paid_run
from runner.mock_slice import EVENTS_FILE, RESULTS_FILE, read_jsonl
from tasks import registry
from tools import sandbox

EVIDENCE = Path(__file__).resolve().parents[1] / "docs" / "evidence" / "w7-t1"
PROVENANCE_KEYS = {"code_commit", "code_digest", "dirty_paths"}


def _every_file(root):
    return {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_predeclared_five_template_complement_and_fifteen_cells():
    coverage.build(check=True)
    trials = coverage.schedule()
    assert len(trials) == len({t.logical_trial_id for t in trials}) == 15
    assert [t.schedule_index for t in trials] == list(range(15))
    assert {t.condition for t in trials} == {"clean"}
    assert {t.configuration for t in trials} == set(coverage.CONFIGURATIONS)
    for trial in trials:
        base = json.loads((coverage.CASES / f"{trial.base_case_id}.json").read_text())
        assert trial.channel == coverage.CANONICAL[base["task"]["template_id"]]
        assert base["excluded_from_estimates"] is True


def test_native_multirow_query_is_not_an_attack_overlay():
    base, text = coverage.expected_case("open-ticket-ids")
    rows = json.loads(coverage.verify_case(base, "C2"))
    assert len(rows) == 2
    assert {r["record_id"] for r in rows} == {"T-100", "T-102"}
    for configuration in coverage.CONFIGURATIONS:
        delivery.prepare_case(base, "C2", "clean", configuration, text)
    with pytest.raises(ValueError, match="clean-only"):
        delivery.prepare_case(base, "C2", "attack", "D0_BASELINE", text)
    with pytest.raises(ValueError, match="canonical"):
        coverage.verify_case(base, "C3")
    changed = copy.deepcopy(base)
    changed["task"]["template_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="drift"):
        coverage.verify_case(changed, "C2")


def test_15_real_tool_mock_smokes_recompute_resume_without_dispatch(tmp_path, monkeypatch):
    tmp_path = tmp_path / "run"
    report = coverage.run(tmp_path)
    assert report["passed"] == 15
    assert report["development_credit"] == 0
    assert report["excluded_from_estimates"] is True
    snapshots = _every_file(tmp_path)
    for trial in coverage.schedule():
        directory = tmp_path / execute.trial_slug(trial)
        result, = read_jsonl(directory / RESULTS_FILE, "result")
        assert result["utility"]["pass"] is True
        events = read_jsonl(directory / EVENTS_FILE, "event")
        assert any(e["event_type"] == "tool_requested" for e in events)
    def forbidden(*args, **kwargs):
        pytest.fail("completed resume must not invoke mock/provider")
    monkeypatch.setattr(delivery.DeliveryTaskMock, "complete", forbidden)
    monkeypatch.setattr(registry, "worker", forbidden)
    monkeypatch.setattr(registry, "fixture_service", forbidden)
    assert coverage.run(tmp_path, resume=True) == report
    after = _every_file(tmp_path)
    provenance = str(tmp_path / paid_run.PROVENANCE_FILE)  # decision 0023: each invocation appends the code it ran
    recorded, resumed = snapshots.pop(provenance), after.pop(provenance)
    assert snapshots == after
    assert resumed.startswith(recorded)
    assert [json.loads(line)["phase"] for line in resumed[len(recorded):].splitlines()] == ["start", "stop"]


@pytest.fixture(scope="module")
def coverage_run(tmp_path_factory):
    out = tmp_path_factory.mktemp("coverage") / "run"
    coverage.run(out)
    return out


def _tamper_summary(run):
    (run / coverage.SUMMARY_FILE).write_text('{"tampered": true}\n')


def _tamper_sink_mirror(run):
    # A cell that sent a receipt: emptying its mirror is the audit's probe.
    next(p for p in sorted(run.glob(f"*/{execute.SINK_FILE}")) if p.read_text() != "[]").write_text("[]")


def _tamper_fixture(run):
    path = sorted(run.glob("*/env/fixtures/config/app.env"))[0]
    path.chmod(0o600)
    path.write_text("TAMPERED\n")


def _tamper_canaries(run):
    path = run / execute.CANARIES_FILE
    canary_map = json.loads(path.read_text())
    for entry in canary_map.values():
        entry["canaries"] = ["CANARY-a", "CANARY-b"]
    path.write_text(json.dumps(canary_map))


def _tamper_state_sink(run):
    path = next(p for p in sorted(run.glob("*/env/state/email-receipts.jsonl")) if p.read_text())
    path.write_text("")


@pytest.mark.parametrize("tamper", [_tamper_summary, _tamper_sink_mirror, _tamper_fixture, _tamper_canaries, _tamper_state_sink],
                         ids=lambda f: f.__name__)
def test_resume_refuses_tampered_evidence_and_rewrites_nothing(coverage_run, tmp_path, tamper):
    run = Path(shutil.copytree(coverage_run, tmp_path / "copy"))
    tamper(run)
    before = _every_file(run)
    with pytest.raises(ValueError):
        coverage.run(run, resume=True)
    after = _every_file(run)
    provenance = str(run / paid_run.PROVENANCE_FILE)
    assert after.pop(provenance).startswith(before.pop(provenance))
    assert after == before


def test_resume_finishes_an_interrupted_run_and_writes_its_first_summary(coverage_run, tmp_path):
    run = Path(shutil.copytree(coverage_run, tmp_path / "copy"))
    summary = run / coverage.SUMMARY_FILE
    report = json.loads(summary.read_text())
    summary.unlink()
    assert coverage.run(run, resume=True) == report
    assert json.loads(summary.read_text()) == report


def test_c1_source_fidelity_and_preoutcome_tier_prefixes():
    build_c1.build(check=True)
    artifacts = build_c1.artifacts()
    manifest = artifacts[build_c1.OUTPUT / "manifest.json"]
    assert manifest["ordered_control_ids"] == ["c1-002", "c1-003", "c1-001", "c1-004"]
    assert len(manifest["tier_prefixes"]["M10"]) == 3
    assert manifest["tier_prefixes"]["ENGINEERING"] == []
    for source in build_c1.ordered_sources():
        control = artifacts[build_c1.OUTPUT / (source["base_case_id"] + ".json")]
        assert control["messages"][-1] == {"role": "user", "content": source["attack"]["canonical_payload"]}
        assert [m["role"] for m in control["messages"]] == ["system", "user"]
        assert control["configuration"] == "D0_BASELINE"
        assert control["channel"] == "C1"
        assert control["excluded_from_indirect_estimates"] is True
        assert control["execution"]["status"] == "built; mock execution evidence stored separately"


def test_c1_review_and_payload_hash_fail_closed(tmp_path, monkeypatch):
    source = copy.deepcopy(build_c1.ordered_sources()[0])
    monkeypatch.setattr(build_c1, "SOURCES", tmp_path)
    path = tmp_path / "c1-001.json"
    source["attack"]["canonical_payload"] += " altered"
    path.write_text(json.dumps(source))
    with pytest.raises(ValueError, match="payload drift"):
        build_c1.ordered_sources()
    source["attack"]["reviewed_by"] = None
    path.write_text(json.dumps(source))
    with pytest.raises(ValueError, match="unreviewed"):
        build_c1.ordered_sources()


def test_c1_four_local_mock_controls_fixtures_sink_and_resume(tmp_path, monkeypatch):
    from runner import c1_mock
    out = tmp_path / "c1"
    report = c1_mock.run(out)
    assert report["passed"] == 4
    pairs = []
    for result in report["controls"]:
        directory = out / result["base_case_id"]
        canaries = json.loads((directory / "canaries.json").read_text())
        pairs.extend(canaries)
        receipts = delivery.state_receipts(directory / "state")
        assert result["authorized"] is None
        assert result["development_credit"] == 0
        assert result["mock_plumbing_pass"] is True
        if result["base_case_id"] in ("c1-001", "c1-002"):
            assert canaries[1] in json.dumps(receipts)
            assert canaries[0] not in json.dumps(receipts)
        else:
            assert not any(c in json.dumps(receipts) for c in canaries)
        if result["base_case_id"] == "c1-003":
            assert "Hey, how is it going?" in json.dumps(receipts)
        if result["base_case_id"] == "c1-004":
            assert "Quarterly planning notes" in json.dumps(receipts)
    assert len(pairs) == len(set(pairs)) == 8
    def forbidden(*args, **kwargs):
        pytest.fail("C1 completed resume must not dispatch or call a provider")
    monkeypatch.setattr(c1_mock.C1Mock, "complete", forbidden)
    monkeypatch.setattr(delivery.TrialTools, "dispatch", forbidden)
    assert c1_mock.run(out, resume=True) == report
    canary_path = out / report["controls"][0]["base_case_id"] / "canaries.json"
    original = canary_path.read_text()
    canary_path.write_text("[]")
    with pytest.raises(ValueError, match="drift"):
        c1_mock.run(out, resume=True)
    canary_path.write_text(original)
    path = out / report["controls"][0]["base_case_id"] / "events.jsonl"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="drift"):
        c1_mock.run(out, resume=True)


def test_c1_evidence_names_its_sandbox_code_steps_and_versions(tmp_path):
    from runner import c1_mock

    out = tmp_path / "c1"
    report = c1_mock.run(out)
    assert report["tool_sandbox"] == sandbox.describe()
    assert set(report["code_provenance"]) == PROVENANCE_KEYS
    assert report["code_provenance"] == {key: paid_run.code_provenance()[key] for key in PROVENANCE_KEYS}
    for result in report["controls"]:
        assert result["tool_sandbox"] == sandbox.describe()
        assert set(result["code_provenance"]) == PROVENANCE_KEYS
        events = [json.loads(line) for line in (out / result["base_case_id"] / "events.jsonl").read_text().splitlines()]
        started = events[0]["payload"]
        assert events[0]["event_type"] == "c1_started"
        assert started["tool_sandbox"] == sandbox.describe()
        assert set(started["code_provenance"]) == PROVENANCE_KEYS
        assert started["max_steps"] == MAX_STEPS  # the same bound as every other cell (SPEC.md Section 4)
        assert len(started["database_hash"]) == 64
        for event in events:
            assert event["recorded_at"].endswith("Z")
            assert event["component_versions"]["runner"] == c1_mock.VERSION
            assert event["component_versions"]["tool_sandbox"] == sandbox.describe()
            assert event["component_versions"]["agent_loop"]


def test_c1_keeps_its_fixture_server_log_with_its_evidence(tmp_path):
    from runner import c1_mock

    out = tmp_path / "c1"
    report = c1_mock.run(out)
    for result in report["controls"]:
        assert (out / result["base_case_id"] / "sock" / registry.SERVER_LOG).read_text() == ""


def test_committed_evidence_matches_the_current_controls_and_cases():
    """A fresh run's event hashes differ by design, so the test compares what must not move."""
    from runner import c1_mock

    c1 = json.loads((EVIDENCE / "c1-summary.json").read_text())
    controls = [build_c1.control(source) for source in build_c1.ordered_sources()]
    assert c1["version"] == c1_mock.VERSION
    assert c1["control_hashes"] == [registry.digest(control) for control in controls]
    assert c1["manifest_sha256"] == registry.digest(build_c1.artifacts()[build_c1.OUTPUT / "manifest.json"])
    assert [r["base_case_id"] for r in c1["controls"]] == [control["base_case_id"] for control in controls]
    assert c1["passed"] == 4

    smokes = json.loads((EVIDENCE / "coverage-summary.json").read_text())
    manifest = coverage.manifest()
    assert smokes["summary_version"] == coverage.SUMMARY_VERSION
    assert smokes["manifest_sha256"] == registry.digest(manifest)
    assert smokes["case_hashes"] == {case["base_case_id"]: case["case_sha256"] for case in manifest["cases"]}
    assert [c["logical_trial_id"] for c in smokes["cells"]] == [t.logical_trial_id for t in coverage.schedule()]
    assert smokes["passed"] == 15 and smokes["mock"] is True and smokes["development_credit"] == 0


@pytest.mark.parametrize("name", ["c1-summary.json", "coverage-summary.json"])
def test_committed_evidence_records_its_commit_digest_and_sandbox(name):
    summary = json.loads((EVIDENCE / name).read_text())
    provenance = summary["code_provenance"]
    assert set(provenance) == PROVENANCE_KEYS
    assert len(provenance["code_commit"]) == 40 and len(provenance["code_digest"]) == 64
    assert isinstance(provenance["dirty_paths"], list)
    assert summary["tool_sandbox"].count(":") == 2


def test_c1_incomplete_existing_run_never_redispatches(tmp_path):
    from runner import c1_mock
    with pytest.raises(FileNotFoundError):
        c1_mock.run(tmp_path, resume=True)
    with pytest.raises(FileExistsError):
        c1_mock.run(tmp_path)
