"""Decision 0030 item 8: the Section 13 live-first rehearsal command, on fakes only.

Every provider here is a fake that reaches no network, behind the real paid-run gate,
ledger, and cap (tests/conftest.py's stand-in home). protocol/active.json is a stand-in
in tmp_path; the demo case is the real corpus/demo/demo-001.json.
"""

import json
from types import SimpleNamespace

import pytest

from runner import live_smoke, paid_run, spend_ledger
from tests.test_verify_evidence import FakeAdapter

VERSION = "1.24.0"
STAGE = ["D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING"]


@pytest.fixture
def active(tmp_path, monkeypatch):
    from runner import rehearsal

    path = tmp_path / "active.json"
    base = {"protocol_version": VERSION, "tier_class": "ALL", "configurations": STAGE, "stage_configurations": STAGE,
            "stage_configuration_count": 3, "empirical": {"model_requested": "fake-model"}}
    state = SimpleNamespace(path=path, committed=None, real_committed=rehearsal._active_committed_refusal,
                            write=lambda **changes: path.write_text(json.dumps({**base, **changes}), encoding="utf-8"))
    state.write()
    monkeypatch.setattr(rehearsal, "ACTIVE", path)
    monkeypatch.setattr(rehearsal, "_active_committed_refusal", lambda: state.committed)
    return state


@pytest.fixture
def provider(monkeypatch, tmp_path):
    adapter, built = FakeAdapter(), []

    def build_client(key):
        built.append(key)
        return object()

    entry = {"module": SimpleNamespace(build_client=build_client), "adapter": lambda client: adapter,
             "check": lambda decoding: None, "model": "fake-model",
             "decoding": {"endpoint": "messages", "thinking": "disabled", "effort": "medium", "max_tokens": 4096},
             "key": "ANTHROPIC_API_KEY", "usage_page": "n/a", "price_step_tokens": None}
    monkeypatch.setitem(live_smoke.PROVIDERS, "anthropic", entry)
    env_file = tmp_path / "synthetic.env"
    env_file.write_text("ANTHROPIC_API_KEY=synthetic-sentinel\n", encoding="utf-8")
    monkeypatch.setenv("CANARY_PAID_RUN_ACK", "1")
    return SimpleNamespace(adapter=adapter, built=built, env_file=env_file)


def _run(provider, out, **changes):
    from runner import rehearsal

    return rehearsal.run_rehearsal(out, **{"protocol_version": VERSION, "env_file": provider.env_file, **changes})


def _results(out):
    return [json.loads(line) for path in sorted(out.glob("*/results.jsonl"))
            for line in path.read_text(encoding="utf-8").split("\n") if line]


def test_ten_dry_runs_over_the_stage_configurations_as_demo_rehearsal(gate, provider, active, tmp_path):
    from runner import rehearsal

    gate.open()
    before = spend_ledger.totals(spend_ledger.read())
    out = tmp_path / "rehearsal"
    _run(provider, out)
    records = _results(out)
    assert len(records) == 30  # 10 × K at F20
    assert {r["base_case_id"] for r in records} == {"demo-001"}
    assert {(r["split"], r["analysis_role"], r["channel"], r["condition"]) for r in records} == {
        ("development", "demo_rehearsal", "C2", "attack")}
    assert sorted({r["configuration"] for r in records}) == STAGE
    assert sorted({r["run_index"] for r in records}) == list(range(1, 11))
    assert {r["protocol_version"] for r in records} == {VERSION}
    # Rehearsal trials count in dollars, never against the development ceiling.
    spend, trials = spend_ledger.totals(spend_ledger.read())
    assert spend > before[0] and trials == before[1]
    report = rehearsal.verify_rehearsal(out)
    assert report["trials_expected"] == report["trials_found"] == 30 and report["missing"] == []
    assert report["status_counts"] == {"completed": 30} and report["complete_dry_runs"] == 10
    assert set(report["dry_runs"]) == {str(i) for i in range(1, 11)}
    assert all(len(rows) == 3 for rows in report["dry_runs"].values())
    assert provider.built == ["synthetic-sentinel"]


def test_a_smaller_stage_list_gets_a_smaller_allowance(gate, provider, active, tmp_path):
    gate.open()
    active.write(stage_configurations=["D0_BASELINE"], stage_configuration_count=1)
    out = tmp_path / "rehearsal"
    _run(provider, out)
    assert len(_results(out)) == 10


@pytest.mark.parametrize("change, reason", [
    (lambda a: a.path.unlink(), "active.json"),
    (lambda a: a.path.write_text("[", encoding="utf-8"), "active.json"),
    (lambda a: a.write(protocol_version="1.25.0"), "protocol-version"),
    (lambda a: a.write(stage_configurations=[]), "replay-first"),
    (lambda a: a.write(stage_configurations=["D0_BASELINE", "D0_BASELINE"]), "retained"),
    (lambda a: a.write(stage_configurations=["D3_SOMETHING"]), "retained"),
    (lambda a: a.write(configurations=["D0_BASELINE", "D1_POLICY_GATE"]), "retained"),
    (lambda a: a.write(stage_configuration_count=2), "stage_configuration_count"),
    (lambda a: a.write(tier_class="ENGINEERING"), "replay-first"),
    (lambda a: a.write(tier_class="STOP"), "replay-first"),
    (lambda a: a.write(empirical={"model_requested": "another-model"}), "model_requested"),
    (lambda a: setattr(a, "committed", "protocol/active.json isn't committed"), "isn't committed"),
])
def test_the_rehearsal_refuses_before_any_key_is_read(gate, provider, active, tmp_path, change, reason):
    gate.open()
    change(active)
    with pytest.raises(paid_run.PaidRunRefused, match=reason):
        _run(provider, tmp_path / "rehearsal")
    assert provider.built == [] and not (tmp_path / "rehearsal").exists()


def test_the_rehearsal_needs_the_ack(gate, provider, active, tmp_path, monkeypatch):
    gate.open()
    monkeypatch.delenv("CANARY_PAID_RUN_ACK")
    with pytest.raises(paid_run.PaidRunRefused, match="CANARY_PAID_RUN_ACK"):
        _run(provider, tmp_path / "rehearsal")
    assert provider.built == []


def test_the_rehearsal_needs_the_paid_run_gate(gate, provider, active, tmp_path):
    with pytest.raises(paid_run.PaidRunRefused, match="record"):
        _run(provider, tmp_path / "rehearsal")
    assert provider.built == []


def test_the_rehearsal_refuses_output_inside_git(gate, provider, active):
    gate.open()
    with pytest.raises(paid_run.PaidRunRefused, match="Git"):
        _run(provider, gate.root / "rehearsal-out")
    assert provider.built == []


def test_a_dry_run_is_never_redone_in_a_fresh_directory(gate, provider, active, tmp_path):
    gate.open()
    _run(provider, tmp_path / "first")
    built = list(provider.built)
    with pytest.raises(paid_run.PaidRunRefused, match="--resume"):
        _run(provider, tmp_path / "second")
    assert provider.built == built and not (tmp_path / "second").exists()
    _run(provider, tmp_path / "first", resume=True)  # resuming the first is allowed and adds nothing


def test_the_allowance_counts_earlier_rehearsal_trials(gate, provider, active, tmp_path):
    gate.open()
    for index in range(1):
        spend_ledger.finish(spend_ledger.start(SimpleNamespace(adapter_version="seed"), f"earlier-{index}",
                                               analysis_role="demo_rehearsal"), [])
    with pytest.raises(paid_run.PaidRunRefused, match="allowance"):
        _run(provider, tmp_path / "rehearsal")
    assert provider.built == []


def test_the_demo_case_is_the_excluded_one():
    from runner import rehearsal

    base = json.loads((rehearsal.DEMO_CORPUS_ROOT / f"{rehearsal.DEMO_BASE}.json").read_text(encoding="utf-8"))
    assert base["split"] == "demo" and "C2" in base["channels"]


def test_a_deleted_trial_is_never_rerun_on_resume(gate, provider, active, tmp_path):
    # Round 1 B1: deleting a dry run's trial and resuming doesn't redo it.
    import shutil

    gate.open()
    out = tmp_path / "rehearsal"
    _run(provider, out)
    calls = provider.adapter.calls
    shutil.rmtree(next(out.glob("*_D0_BASELINE_r3")))
    with pytest.raises(paid_run.PaidRunRefused, match="no durable events"):
        _run(provider, out, resume=True)
    assert provider.adapter.calls == calls


def test_a_copied_run_with_trials_removed_is_refused(gate, provider, active, tmp_path):
    import shutil

    gate.open()
    out = tmp_path / "rehearsal"
    _run(provider, out)
    copy = tmp_path / "copy"
    shutil.copytree(out, copy)
    for trial in copy.glob("*_r5"):
        shutil.rmtree(trial)
    calls = provider.adapter.calls
    with pytest.raises(paid_run.PaidRunRefused, match="no durable events"):
        _run(provider, copy, resume=True)
    assert provider.adapter.calls == calls


def test_a_trial_started_twice_refuses_every_later_run(gate, provider, active, tmp_path):
    gate.open()
    out = tmp_path / "rehearsal"
    _run(provider, out)
    trial_id = json.loads(next(out.glob("*/results.jsonl")).read_text(encoding="utf-8").split("\n")[0])["logical_trial_id"]
    spend_ledger.finish(spend_ledger.start(SimpleNamespace(adapter_version="seed"), trial_id,
                                           analysis_role="demo_rehearsal"), [])
    with pytest.raises(paid_run.PaidRunRefused, match="more than once"):
        _run(provider, out, resume=True)


def test_resume_needs_an_earlier_run_and_fresh_needs_a_new_directory(gate, provider, active, tmp_path):
    gate.open()
    with pytest.raises(paid_run.PaidRunRefused, match="--resume needs"):
        _run(provider, tmp_path / "nothing-here", resume=True)
    (tmp_path / "taken").mkdir()
    with pytest.raises(paid_run.PaidRunRefused, match="already exists"):
        _run(provider, tmp_path / "taken")
    assert provider.built == []


def test_verify_counts_dry_runs_against_the_stored_schedule(gate, provider, active, tmp_path):
    # Round 1 B2: a configuration missing from every run leaves no dry run complete.
    import shutil

    from runner import rehearsal

    gate.open()
    out = tmp_path / "rehearsal"
    _run(provider, out)
    for trial in out.glob("*_D2_DATAMARKING_r*"):
        shutil.rmtree(trial)
    report = rehearsal.verify_rehearsal(out)
    assert report["trials_found"] == 20 and len(report["missing"]) == 10
    assert report["complete_dry_runs"] == 0
    assert all(any(row["status"] == "missing" for row in rows) for rows in report["dry_runs"].values())


def test_verify_refuses_an_edited_result(gate, provider, active, tmp_path):
    from runner import rehearsal

    gate.open()
    out = tmp_path / "rehearsal"
    _run(provider, out)
    path = next(out.glob("*_D0_BASELINE_r1/results.jsonl"))
    record = json.loads(path.read_text(encoding="utf-8").split("\n")[0])
    record["security"]["unauthorized_action_effect"] = not record["security"]["unauthorized_action_effect"]
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(ValueError):
        rehearsal.verify_rehearsal(out)


def test_a_non_demo_case_is_refused(gate, provider, active, tmp_path, monkeypatch):
    import shutil

    from runner import rehearsal

    gate.open()
    root = tmp_path / "demo-corpus"
    shutil.copytree(rehearsal.DEMO_CORPUS_ROOT, root)
    record = json.loads((root / "demo-001.json").read_text(encoding="utf-8"))
    (root / "demo-001.json").write_text(json.dumps({**record, "split": "development"}), encoding="utf-8")
    monkeypatch.setattr(rehearsal, "DEMO_CORPUS_ROOT", root)
    with pytest.raises(paid_run.PaidRunRefused, match="excluded demo case"):
        _run(provider, tmp_path / "rehearsal")
    assert provider.built == []


def test_an_active_protocol_outside_the_checkout_is_refused(active):
    reason = active.real_committed()
    assert reason is not None and "active.json" in reason


def test_the_command_line_refuses_in_words(gate, active, capsys, monkeypatch):
    from runner import rehearsal

    monkeypatch.delenv("CANARY_PAID_RUN_ACK", raising=False)
    assert rehearsal.main(["live", "--protocol-version", VERSION, "--env-file", "nowhere.env"]) == 1
    assert "refusing:" in capsys.readouterr().err


def test_an_emptied_trace_never_lets_a_dry_run_rerun(gate, provider, active, tmp_path):
    # Round 2 B-A: an empty events.jsonl in a recreated trial directory isn't a started trial's trace.
    import shutil

    gate.open()
    out = tmp_path / "rehearsal"
    _run(provider, out)
    calls = provider.adapter.calls
    trial = next(out.glob("*_D0_BASELINE_r3"))
    shutil.rmtree(trial)
    trial.mkdir()
    (trial / "events.jsonl").touch()
    with pytest.raises(paid_run.PaidRunRefused, match="no durable events"):
        _run(provider, out, resume=True)
    assert provider.adapter.calls == calls


def test_verify_never_counts_a_dry_run_whose_trial_was_started_twice(gate, provider, active, tmp_path):
    from runner import rehearsal

    gate.open()
    out = tmp_path / "rehearsal"
    _run(provider, out)
    record = json.loads(next(out.glob("*_D1_POLICY_GATE_r4/results.jsonl")).read_text(encoding="utf-8").split("\n")[0])
    spend_ledger.finish(spend_ledger.start(SimpleNamespace(adapter_version="seed"), record["logical_trial_id"],
                                           analysis_role="demo_rehearsal"), [])
    report = rehearsal.verify_rehearsal(out)
    assert report["trials_started_more_than_once"] == [record["logical_trial_id"]]
    assert report["complete_dry_runs"] == 9
