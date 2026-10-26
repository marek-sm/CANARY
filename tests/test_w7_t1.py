"""W7-T1 predeclaration, source fidelity, isolation, and durable mock evidence."""
import copy
import json

import pytest

from corpus import build_c1
from runner import coverage, delivery, execute
from runner.mock_slice import EVENTS_FILE, RESULTS_FILE, read_jsonl


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
    snapshots = {str(p): p.read_bytes() for p in tmp_path.rglob("*.jsonl")}
    for trial in coverage.schedule():
        directory = tmp_path / execute.trial_slug(trial)
        result, = read_jsonl(directory / RESULTS_FILE, "result")
        assert result["utility"]["pass"] is True
        events = read_jsonl(directory / EVENTS_FILE, "event")
        assert any(e["event_type"] == "tool_requested" for e in events)
    def forbidden(*args, **kwargs):
        pytest.fail("completed resume must not invoke mock/provider")
    monkeypatch.setattr(delivery.DeliveryTaskMock, "complete", forbidden)
    assert coverage.run(tmp_path, resume=True) == report
    assert snapshots == {str(p): p.read_bytes() for p in tmp_path.rglob("*.jsonl")}


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


def test_c1_incomplete_existing_run_never_redispatches(tmp_path):
    from runner import c1_mock
    with pytest.raises(FileNotFoundError):
        c1_mock.run(tmp_path, resume=True)
    with pytest.raises(FileExistsError):
        c1_mock.run(tmp_path)
