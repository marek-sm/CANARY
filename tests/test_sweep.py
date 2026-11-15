"""The sweep's entry point: split="evaluation" through the paid grid's own runner path.

Every provider here is a fake that reaches no network, behind the real paid-run gate,
ledger, and cap (tests/conftest.py's stand-in home). The corpus is a temporary copy of
a development base relabelled as evaluation, under an ``eval-`` ID so its record
validates against base_case.schema.json; corpus/evaluation is never read.
"""

import json
import shutil
from types import SimpleNamespace

import pytest

from runner import delivery, execute, live_smoke, paid_run, spend_ledger, sweep
from tests.test_verify_evidence import FakeAdapter

EVAL_ID = "eval-901"  # dev-001 relabelled; not a real evaluation candidate
SPEC = {"experiment_id": "sweep-test", "model_id": "fake-model", "seed": "sweep-seed", "protocol_sentinel": "v1-19-0",
        "base_case_ids": [EVAL_ID], "channels": ["C2", "C3", "C4"], "conditions": ["attack", "clean"],
        "configurations": ["D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING"], "repeats": 1}


CORPUS_HASH, DEFENSE_HASH = "c" * 64, "d" * 64


@pytest.fixture(autouse=True)
def frozen(monkeypatch, tmp_path):
    """N-93-1: a stand-in Gate 3 state for the temporary corpus. protocol/active.json and
    both freeze manifests agree with SPEC, and neither freeze has drifted."""
    active = {"protocol_version": "1.19.0", "base_case_ids": [EVAL_ID], "channels": ["C2", "C3", "C4"],
              "configurations": ["D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING"], "run_indices": [1],
              "empirical": {"corpus_hash": CORPUS_HASH, "defense_hash": DEFENSE_HASH, "experiment_id": "sweep-test",
                            "model_requested": "fake-model", "schedule_seed": "sweep-seed"}}
    path = tmp_path / "active.json"
    path.write_text(json.dumps(active), encoding="utf-8")
    state = SimpleNamespace(path=path, active=active,
                            corpus={"corpus_hash": CORPUS_HASH, "base_case_ids": [EVAL_ID]},
                            defense={"defense_hash": DEFENSE_HASH}, drift=None, committed=None,
                            real_drift=getattr(sweep, "_drift", None), real_manifests=getattr(sweep, "_manifests", None),
                            real_committed=getattr(sweep, "_active_committed_refusal", None))
    monkeypatch.setattr(sweep, "ACTIVE", path, raising=False)
    monkeypatch.setattr(sweep, "FROZEN_CORPUS_ROOT", tmp_path / "evaluation", raising=False)
    monkeypatch.setattr(sweep, "_manifests", lambda: (state.corpus, state.defense), raising=False)
    monkeypatch.setattr(sweep, "_drift", lambda: state.drift, raising=False)
    monkeypatch.setattr(sweep, "_active_committed_refusal", lambda: state.committed, raising=False)
    return state


def _write_active(frozen, **changes):
    frozen.path.write_text(json.dumps({**frozen.active, **changes}), encoding="utf-8")


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


@pytest.fixture
def corpus(tmp_path, monkeypatch):
    """dev-001 as a schema-valid evaluation base: its renders copied under fixtures/EVAL_ID
    in a fixture root that delivery reads (as tests/test_delivery.py repoints it)."""
    root = tmp_path / "evaluation"
    root.mkdir()
    base = json.loads((execute.DEFAULT_CORPUS_ROOT / "dev-001.json").read_text(encoding="utf-8"))
    fixture_root = tmp_path / "fixture-root"
    shutil.copytree(delivery.REPO_ROOT / "fixtures" / "dev-001", fixture_root / "fixtures" / EVAL_ID)
    pins = fixture_root / "fixtures" / EVAL_ID / "rendered-hashes.json"
    pins.write_text(pins.read_text(encoding="utf-8").replace("fixtures/dev-001/", f"fixtures/{EVAL_ID}/"), encoding="utf-8")
    for real in (delivery.REPO_ROOT / "fixtures").iterdir():  # every other base's renders, unchanged
        (fixture_root / "fixtures" / real.name).symlink_to(real)
    monkeypatch.setattr(delivery, "REPO_ROOT", fixture_root)
    fixture = {**base["fixture"], "rendered_hash_manifest": f"fixtures/{EVAL_ID}/rendered-hashes.json"}
    (root / f"{EVAL_ID}.json").write_text(
        json.dumps({**base, "split": "evaluation", "base_case_id": EVAL_ID, "fixture": fixture}), encoding="utf-8")
    return root


def _run(provider, corpus, out, **changes):
    arguments = {"spec": SPEC, "protocol_version": "1.19.0", "corpus_root": corpus, "env_file": provider.env_file,
                 "analysis_role": "primary_indirect", **changes}
    return sweep.run_sweep(out, **arguments)


def test_a_sweep_runs_at_116_development_trials_and_verifies(gate, provider, corpus, tmp_path):
    gate.open()
    for index in range(115):  # the seed is the 116th
        spend_ledger.finish(spend_ledger.start(SimpleNamespace(adapter_version="seed"), f"dev-{index}"), [])
    out = tmp_path / "sweep"
    _run(provider, corpus, out)
    report = sweep.verify_sweep(out, corpus)
    assert report == {"trials_expected": 18, "trials_found": 18, "missing": 0, "status_counts": {"completed": 18},
                      "protocol_versions": ["1.19.0"], "run_wide_stops": [], "complete": True}
    for results in out.glob("*/results.jsonl"):
        [record] = [json.loads(line) for line in results.read_text(encoding="utf-8").split("\n") if line]
        assert record["split"] == "evaluation" and ":v1-19-0:" in record["logical_trial_id"] and record["channel"]
    assert spend_ledger.totals(spend_ledger.read())[1] == 116
    assert provider.built == ["synthetic-sentinel"] and provider.adapter.calls > 0


def test_verify_prints_no_outcome_aggregate(gate, provider, corpus, tmp_path, capsys):
    gate.open()
    _run(provider, corpus, tmp_path / "sweep")
    assert sweep.main(["verify", str(tmp_path / "sweep"), "--corpus-root", str(corpus)]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert set(printed) == {"trials_expected", "trials_found", "missing", "status_counts", "protocol_versions",
                            "run_wide_stops", "complete"}


@pytest.mark.parametrize("change, reason", [
    ({"protocol_version": ""}, "protocol_version"),
    ({"spec": {**SPEC, "protocol_sentinel": "unfrozen"}}, "protocol_sentinel"),
    ({"spec": {key: value for key, value in SPEC.items() if key != "protocol_sentinel"}}, "protocol_sentinel"),
])
def test_the_sweep_refuses_before_any_key_is_read(gate, provider, corpus, tmp_path, change, reason):
    gate.open()
    with pytest.raises(paid_run.PaidRunRefused, match=reason):
        _run(provider, corpus, tmp_path / "sweep", **change)
    assert provider.built == [] and not (tmp_path / "sweep").exists()


def test_the_sweep_refuses_a_development_base_without_the_ack_or_inside_git(gate, provider, corpus, tmp_path, monkeypatch):
    gate.open()
    base = json.loads((corpus / f"{EVAL_ID}.json").read_text(encoding="utf-8"))
    (corpus / f"{EVAL_ID}.json").write_text(json.dumps({**base, "split": "development"}), encoding="utf-8")
    with pytest.raises(paid_run.PaidRunRefused, match="evaluation base"):
        _run(provider, corpus, tmp_path / "sweep")
    (corpus / f"{EVAL_ID}.json").write_text(json.dumps(base), encoding="utf-8")
    with pytest.raises(paid_run.PaidRunRefused, match="Git"):
        _run(provider, corpus, gate.root / "sweep-out")
    monkeypatch.delenv("CANARY_PAID_RUN_ACK")
    with pytest.raises(paid_run.PaidRunRefused, match="CANARY_PAID_RUN_ACK"):
        _run(provider, corpus, tmp_path / "sweep")
    assert provider.built == []


def test_the_sweep_refuses_without_a_paid_run_record(gate, provider, corpus, tmp_path):
    with pytest.raises(paid_run.PaidRunRefused, match="record"):
        _run(provider, corpus, tmp_path / "sweep")
    assert provider.built == []


# Stack-gaps item 6: a missing or drifted render refuses the sweep before any trial,
# instead of becoming one silent infrastructure_failure per cell.
@pytest.mark.parametrize("damage", ["missing_file", "changed_file", "missing_pin", "missing_manifest"])
def test_the_sweep_refuses_before_any_trial_when_a_render_is_missing(gate, provider, corpus, tmp_path, damage):
    gate.open()
    renders = delivery.REPO_ROOT / "fixtures" / EVAL_ID
    pins = renders / "rendered-hashes.json"
    if damage == "missing_file":
        (renders / "rendered" / "c3_attack.txt").unlink()
    elif damage == "changed_file":
        (renders / "rendered" / "c4_clean.html").write_text("<p>drift</p>", encoding="utf-8")
    elif damage == "missing_pin":
        table = json.loads(pins.read_text(encoding="utf-8"))
        del table["c2_clean"]
        pins.write_text(json.dumps(table), encoding="utf-8")
    else:
        pins.unlink()
    with pytest.raises(paid_run.PaidRunRefused, match=f"{EVAL_ID}.*render"):
        _run(provider, corpus, tmp_path / "sweep")
    assert provider.built == [] and provider.adapter.calls == 0
    assert not (tmp_path / "sweep").exists()


def test_the_render_preflight_passes_a_complete_corpus(corpus):
    assert sweep._renders_refusal(corpus, SPEC) is None


def test_the_fallback_sweep_stays_closed_until_a_decision_names_it(gate, provider, corpus, tmp_path):
    with pytest.raises(paid_run.PaidRunRefused, match="decision 0010 item 3"):
        _run(provider, corpus, tmp_path / "sweep", provider_name="openai")
    assert provider.built == [] and not (tmp_path / "sweep").exists()


def test_a_base_the_schema_refuses_doesn_t_print_its_payload(corpus):
    # An evaluation record's refusal lands in terminal logs, so it names the problem only.
    path = corpus / f"{EVAL_ID}.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    del record["source"]
    path.write_text(json.dumps(record), encoding="utf-8")
    reason = sweep._renders_refusal(corpus, SPEC)
    assert "'source' is a required property" in reason
    assert "canonical_payload" not in reason and "attack" not in reason


# N-93-1 (docs/reviews/2026-11-13-w8-t2.md): the live sweep runs only the frozen protocol.
@pytest.mark.parametrize("change, reason", [
    (lambda f: f.path.unlink(), "active.json"),
    (lambda f: f.path.write_text("{", encoding="utf-8"), "active.json"),
    (lambda f: _write_active(f, protocol_version="1.20.0"), "protocol_version"),
    (lambda f: _write_active(f, base_case_ids=[EVAL_ID, "eval-902"]), "base_case_ids"),
    (lambda f: _write_active(f, empirical={**f.active["empirical"], "corpus_hash": "e" * 64}), "corpus_hash"),
    (lambda f: _write_active(f, empirical={**f.active["empirical"], "defense_hash": "e" * 64}), "defense_hash"),
    (lambda f: _write_active(f, empirical={"corpus_hash": CORPUS_HASH}), "defense_hash"),
    (lambda f: setattr(f, "corpus", {**f.corpus, "base_case_ids": ["eval-001"]}), "corpus/freeze.json"),
    (lambda f: setattr(f, "drift", "corpus/freeze.json doesn't match the tree"), "freeze.json doesn't match"),
    (lambda f: setattr(f, "committed", "protocol/active.json isn't committed"), "isn't committed"),
])
def test_the_sweep_refuses_anything_but_the_frozen_protocol(gate, provider, corpus, tmp_path, frozen, change, reason):
    gate.open()
    change(frozen)
    with pytest.raises(paid_run.PaidRunRefused, match=reason):
        _run(provider, corpus, tmp_path / "sweep")
    assert provider.built == [] and not (tmp_path / "sweep").exists()


# Whole-tree review F-A: the sweep runs only the schedule protocol/active.json names
# (SPEC.md Sections 9, 11, and 12: its seed, model, channels, configurations, and run indices).
@pytest.mark.parametrize("change, reason", [
    (lambda f: _write_active(f, empirical={**f.active["empirical"], "schedule_seed": "other-seed"}), "seed"),
    (lambda f: _write_active(f, empirical={**f.active["empirical"], "experiment_id": "other-experiment"}), "experiment_id"),
    (lambda f: _write_active(f, empirical={**f.active["empirical"], "model_requested": "other-model"}), "model"),
    (lambda f: _write_active(f, empirical={k: v for k, v in f.active["empirical"].items() if k != "schedule_seed"}), "seed"),
    (lambda f: _write_active(f, channels=["C2"]), "channels"),
    (lambda f: _write_active(f, configurations=["D0_BASELINE", "D1_POLICY_GATE"]), "configurations"),
    (lambda f: _write_active(f, run_indices=[1, 2, 3]), "run_indices"),
])
def test_the_sweep_refuses_a_schedule_active_json_does_not_name(gate, provider, corpus, tmp_path, frozen, change, reason):
    gate.open()
    change(frozen)
    with pytest.raises(paid_run.PaidRunRefused, match=reason):
        _run(provider, corpus, tmp_path / "sweep")
    assert provider.built == [] and not (tmp_path / "sweep").exists()


def test_the_sweep_refuses_conditions_other_than_attack_and_clean(gate, provider, corpus, tmp_path):
    gate.open()
    with pytest.raises(paid_run.PaidRunRefused, match="conditions"):
        _run(provider, corpus, tmp_path / "sweep", spec={**SPEC, "conditions": ["attack"]})
    assert provider.built == []


# The schedule generator iterates its lists in order (runner/schedule.py), so the same
# members in another order give another schedule: active.json's lists match in exact order.
@pytest.mark.parametrize("change, spec_change, reason", [
    (lambda f: _write_active(f, channels=["C3", "C2", "C4"]), {}, "channels"),
    (lambda f: _write_active(f, configurations=["D0_BASELINE", "D2_DATAMARKING", "D1_POLICY_GATE"]), {}, "configurations"),
    (lambda f: (setattr(f, "corpus", {**f.corpus, "base_case_ids": [EVAL_ID, "eval-902"]}),
                _write_active(f, base_case_ids=["eval-902", EVAL_ID])),
     {"base_case_ids": [EVAL_ID, "eval-902"]}, "base_case_ids aren't protocol/active.json's"),
    (lambda f: None, {"conditions": ["clean", "attack"]}, "conditions"),
])
def test_the_sweep_refuses_active_json_lists_in_another_order(gate, provider, corpus, tmp_path, frozen,
                                                              change, spec_change, reason):
    gate.open()
    change(frozen)
    with pytest.raises(paid_run.PaidRunRefused, match=reason):
        _run(provider, corpus, tmp_path / "sweep", spec={**SPEC, **spec_change})
    assert provider.built == [] and not (tmp_path / "sweep").exists()


# Whole-tree review F-B: every official sweep record is primary_indirect, with no flag to forget.
def test_the_sweep_writes_primary_indirect_without_a_flag(gate, provider, corpus, tmp_path):
    gate.open()
    out = tmp_path / "sweep"
    sweep.run_sweep(out, spec=SPEC, protocol_version="1.19.0", corpus_root=corpus, env_file=provider.env_file)
    roles = {json.loads(line)["analysis_role"] for results in out.glob("*/results.jsonl")
             for line in results.read_text(encoding="utf-8").split("\n") if line}
    assert roles == {"primary_indirect"}


@pytest.mark.parametrize("role", [None, "excluded_mock", "c1_control", "demo_rehearsal"])
def test_the_sweep_refuses_any_other_analysis_role(gate, provider, corpus, tmp_path, role):
    gate.open()
    with pytest.raises(paid_run.PaidRunRefused, match="primary_indirect"):
        _run(provider, corpus, tmp_path / "sweep", analysis_role=role)
    assert provider.built == [] and not (tmp_path / "sweep").exists()


def test_the_sweep_cli_has_no_analysis_role_default_but_primary_indirect():
    parser_text = (sweep.REPO_ROOT / "runner" / "sweep.py").read_text(encoding="utf-8")
    assert 'live.add_argument("--analysis-role", default=None)' not in parser_text


def test_the_sweep_refuses_a_corpus_root_the_freeze_doesnt_cover(gate, provider, corpus, tmp_path, monkeypatch):
    gate.open()
    monkeypatch.setattr(sweep, "FROZEN_CORPUS_ROOT", tmp_path / "somewhere-else")
    with pytest.raises(paid_run.PaidRunRefused, match="corpus root"):
        _run(provider, corpus, tmp_path / "sweep")
    assert provider.built == []


def test_this_tree_has_no_active_protocol_so_the_sweep_is_closed(monkeypatch):
    # Before Gate 3 writes protocol/active.json, no live sweep can start (N-93-1's test).
    monkeypatch.setattr(sweep, "ACTIVE", sweep.REPO_ROOT / "protocol" / "active.json")
    monkeypatch.setattr(sweep, "FROZEN_CORPUS_ROOT", sweep.DEFAULT_CORPUS_ROOT)
    if sweep.ACTIVE.exists():
        pytest.skip("the Gate 3 step has committed protocol/active.json")
    reason = sweep._freeze_refusal(SPEC, "1.19.0", sweep.DEFAULT_CORPUS_ROOT)
    assert reason is not None and "active.json" in reason


def test_the_real_freeze_checks_read_this_tree(frozen):
    # On this tree corpus/freeze.json is current. defenses/freeze.json lands with W8-T4;
    # until then the drift check refuses by naming it, and after, both checks pass.
    corpus, _defense = (None, None)
    reason = frozen.real_drift()
    assert reason is None or "defenses/freeze.json" in reason
    try:
        corpus, _defense = frozen.real_manifests()
    except sweep.FreezeMissing as exc:
        assert "defenses/freeze.json" in str(exc)
    else:
        assert len(corpus["base_case_ids"]) == 20


def test_an_active_protocol_outside_the_checkout_is_refused(frozen, monkeypatch):
    # The real committed-file check: a stand-in active.json in tmp_path isn't this checkout's.
    monkeypatch.setattr(sweep, "ACTIVE", frozen.path)
    reason = frozen.real_committed()
    assert reason is not None and "active.json" in reason


def test_an_uncommitted_active_protocol_is_refused(frozen, monkeypatch, tmp_path):
    # A scratch name inside the checkout, never the real protocol/active.json.
    path = sweep.REPO_ROOT / "protocol" / f"active-uncommitted-{tmp_path.name}.json"
    assert not path.exists()
    monkeypatch.setattr(sweep, "ACTIVE", path)
    path.write_text("{}", encoding="utf-8")
    try:
        reason = frozen.real_committed()
    finally:
        path.unlink()
    assert reason is not None and "committed" in reason


def _defense_checker(monkeypatch, result):
    import sys

    import defenses

    fake = SimpleNamespace(main=lambda _argv: result)
    monkeypatch.setitem(sys.modules, "defenses.freeze", fake)
    monkeypatch.setattr(defenses, "freeze", fake, raising=False)


def test_a_freeze_check_that_cannot_run_refuses(frozen, monkeypatch):
    from corpus import freeze as corpus_freeze

    def broken(_argv):
        raise SystemExit(2)

    _defense_checker(monkeypatch, 0)
    monkeypatch.setattr(corpus_freeze, "main", broken)
    reason = frozen.real_drift()
    assert reason is not None and "corpus/freeze.json" in reason


def test_the_drift_check_reads_each_freeze(frozen, monkeypatch):
    from corpus import freeze as corpus_freeze

    _defense_checker(monkeypatch, 0)
    assert frozen.real_drift() is None  # corpus/freeze.json is current on this tree
    monkeypatch.setattr(corpus_freeze, "main", lambda _argv: 1)
    assert "corpus/freeze.json" in frozen.real_drift()
    monkeypatch.undo()
    monkeypatch.setattr(sweep, "_drift", frozen.real_drift)
    _defense_checker(monkeypatch, 1)
    assert "defenses/freeze.json" in frozen.real_drift()
