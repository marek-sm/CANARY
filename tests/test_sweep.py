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
                      "protocol_versions": ["1.19.0"]}
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
    assert set(printed) == {"trials_expected", "trials_found", "missing", "status_counts", "protocol_versions"}


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
