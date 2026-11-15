"""W8-T4: the defense freeze manifest and the Section 5 step 8 recheck.

The manifest freezes what the retained defenses rest on (implementations, the
declarative policy schema, the event meanings, the datamarking specification
vectors, and the defense test evidence) and gives `protocol/active.json` one `defense_hash`. The
recheck recomputes the seeded sample and each sampled case's hashes against
`corpus/freeze.json` with code that shares nothing with `corpus/`.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_defense_manifest_is_current():
    from defenses import freeze

    assert freeze.main(["--check"]) == 0
    manifest = json.loads(freeze.OUT.read_text(encoding="utf-8"))
    assert manifest["defense_hash"] == freeze.set_hash(manifest["defense_files"])
    assert manifest["test_evidence_hash"] == freeze.set_hash(manifest["test_evidence_files"])


def test_manifest_covers_every_file_a_defense_runs():
    from defenses import freeze
    from runner import delivery

    manifest = freeze.build()
    for sources in delivery.DEFENSE_SOURCES.values():
        for path in sources:
            assert path in manifest["defense_files"], path
    for required in ("schemas/policy.schema.json", "schemas/event.schema.json", "defenses/vectors/datamarking-w5-t4.json", "docs/DEFENSES_AND_POLICY.md"):
        assert required in manifest["defense_files"], required
    for module in sorted((ROOT / "defenses").glob("*.py")):
        rel = module.relative_to(ROOT).as_posix()
        assert (rel in manifest["defense_files"]) != (rel == "defenses/freeze.py"), rel
    for required in ("oracles/authorization/audit.py", "oracles/authorization/conformance.py"):
        assert required in manifest["test_evidence_files"], required
    assert manifest["test_evidence_files"], "no defense test evidence frozen"
    for path in manifest["test_evidence_files"]:
        assert path.startswith(("tests/", "oracles/authorization/", "schemas/")), path
    assert any(p.startswith("oracles/authorization/golden/") for p in manifest["test_evidence_files"])


def test_configuration_hashes_match_what_run_records_carry():
    from defenses import freeze
    from runner import delivery

    hashes = freeze.build()["configuration_hashes"]
    assert set(hashes) == {"D1_POLICY_GATE", "D2_DATAMARKING"}
    for configuration, value in hashes.items():
        assert value == delivery.defense_hash(configuration)
    assert delivery.defense_hash("D0_BASELINE") is None


def test_check_fails_when_a_frozen_byte_changes(tmp_path, monkeypatch):
    from defenses import freeze

    manifest = freeze.build()
    for rel in list(manifest["defense_files"]) + list(manifest["test_evidence_files"]):
        dest = tmp_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dest)
    out = tmp_path / "defenses" / "freeze.json"
    shutil.copyfile(freeze.OUT, out)
    monkeypatch.setattr(freeze, "ROOT", tmp_path)
    monkeypatch.setattr(freeze, "OUT", out)
    monkeypatch.setattr(freeze, "configuration_hashes", lambda: manifest["configuration_hashes"])
    assert freeze.main(["--check"]) == 0
    target = tmp_path / "defenses" / "policy_gate.py"
    target.write_bytes(target.read_bytes() + b"\n")
    assert freeze.main(["--check"]) == 1


def test_recheck_sample_matches_the_committed_selection_script():
    from corpus import recheck, select

    rows = [json.loads(line) for line in (ROOT / "corpus" / "candidates.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    retained = recheck.evaluation_cases()
    expected = select.recheck_sample(list(retained), select.pool_hash(rows), len(retained))
    assert recheck.sample() == expected
    assert len(expected) == 4  # ceil(0.20 x 20)


def test_recheck_passes_on_the_frozen_fixtures():
    from corpus import recheck

    report = recheck.run()
    assert report["result"] == "PASS"
    assert [case["checks_failed"] for case in report["cases"]] == [[], [], [], []]


def test_recheck_catches_a_changed_rendered_fixture(tmp_path, monkeypatch):
    recheck = _scratch_corpus(tmp_path, monkeypatch)
    case = recheck.evaluation_cases()[recheck.sample()[0]]
    rendered = tmp_path / json.loads((tmp_path / case["fixture"]["rendered_hash_manifest"]).read_text())["c3_attack"]["path"]
    rendered.write_bytes(rendered.read_bytes() + b"x")
    assert recheck.run()["result"] == "FAIL"


def _scratch_corpus(tmp_path, monkeypatch):
    from corpus import recheck

    for rel in ("corpus/candidates.jsonl", "corpus/freeze.json"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, tmp_path / rel)
    shutil.copytree(ROOT / "corpus" / "evaluation", tmp_path / "corpus" / "evaluation")
    shutil.copytree(ROOT / "fixtures", tmp_path / "fixtures")
    monkeypatch.setattr(recheck, "ROOT", tmp_path)
    assert recheck.run()["result"] == "PASS"
    return recheck


def test_recheck_fails_when_a_fixture_and_its_manifest_change_together(tmp_path, monkeypatch):
    import hashlib

    recheck = _scratch_corpus(tmp_path, monkeypatch)
    case = recheck.evaluation_cases()[recheck.sample()[0]]
    manifest_path = tmp_path / case["fixture"]["rendered_hash_manifest"]
    manifest = json.loads(manifest_path.read_text())
    rendered = tmp_path / manifest["c3_attack"]["path"]
    rendered.write_bytes(b"payload removed")
    manifest["c3_attack"]["sha256"] = hashlib.sha256(b"payload removed").hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2))
    assert recheck.run()["result"] == "FAIL"


def test_recheck_fails_when_rendered_entries_go_missing(tmp_path, monkeypatch):
    recheck = _scratch_corpus(tmp_path, monkeypatch)
    case = recheck.evaluation_cases()[recheck.sample()[0]]
    manifest_path = tmp_path / case["fixture"]["rendered_hash_manifest"]
    manifest = json.loads(manifest_path.read_text())
    for key in ("c2_attack", "c2_clean", "c3_clean", "c4_attack", "c4_clean"):
        del manifest[key]
    manifest_path.write_text(json.dumps(manifest, indent=2))
    assert recheck.run()["result"] == "FAIL"


def test_recheck_fails_when_the_case_set_differs_from_the_freeze(tmp_path, monkeypatch):
    recheck = _scratch_corpus(tmp_path, monkeypatch)
    sampled = set(recheck.sample())
    victim = next(r for cid, r in recheck.evaluation_cases().items() if cid not in sampled)
    (tmp_path / "corpus" / "evaluation" / f"{victim['base_case_id']}.json").unlink()
    assert recheck.run()["result"] == "FAIL"


def test_recheck_sample_is_the_selected_prefix_sample():
    from corpus import recheck, select

    rows = select.load_rows() if hasattr(select, "load_rows") else None
    assert rows is not None
    task_order = json.loads((ROOT / "tasks" / "task_order.json").read_text(encoding="utf-8"))
    planned = select.plan(rows, task_order)["prefixes"]
    key = 20 if 20 in planned else "20"
    assert recheck.sample() == planned[key]["recheck_sample"]


def test_recheck_report_names_the_frozen_corpus_hash():
    from corpus import recheck

    frozen = json.loads((ROOT / "corpus" / "freeze.json").read_text(encoding="utf-8"))
    assert recheck.run()["corpus_hash"] == frozen["corpus_hash"]


def test_recheck_report_pins_the_w8_t2_corpus_hash():
    from corpus import recheck

    assert recheck.run()["corpus_hash"] == "5afb8e1ee8f120f7ea8abfcdf4870b1339cdc5f992fe19f8e50a56939b6c9859"


def test_recheck_fails_when_a_ledger_line_is_added(tmp_path, monkeypatch):
    recheck = _scratch_corpus(tmp_path, monkeypatch)
    ledger = tmp_path / "corpus" / "candidates.jsonl"
    row = json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])
    row["candidate_id"] = "0000000000000000000a"
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")
    assert recheck.run()["result"] == "FAIL"


def test_recheck_fails_when_a_sampled_candidate_record_changes(tmp_path, monkeypatch):
    recheck = _scratch_corpus(tmp_path, monkeypatch)
    path = tmp_path / "corpus" / "evaluation" / "candidates" / f"{recheck.sample()[0]}.json"
    path.write_text(json.dumps(json.loads(path.read_text(encoding="utf-8"))), encoding="utf-8")
    assert recheck.run()["result"] == "FAIL"


def test_recheck_fails_when_base_cases_shrink_with_the_freeze(tmp_path, monkeypatch):
    recheck = _scratch_corpus(tmp_path, monkeypatch)
    sampled = set(recheck.sample())
    victims = [r["base_case_id"] for cid, r in recheck.evaluation_cases().items() if cid not in sampled][:5]
    freeze_path = tmp_path / "corpus" / "freeze.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    freeze["base_case_ids"] = [b for b in freeze["base_case_ids"] if b not in victims]
    freeze_path.write_text(json.dumps(freeze, indent=2), encoding="utf-8")
    for base in victims:
        (tmp_path / "corpus" / "evaluation" / f"{base}.json").unlink()
    report = recheck.run()
    assert report["n"] == 15
    assert report["result"] == "FAIL"


def test_recheck_fails_when_an_evaluation_file_is_renamed(tmp_path, monkeypatch):
    recheck = _scratch_corpus(tmp_path, monkeypatch)
    sampled = set(recheck.sample())
    victim = next(r["base_case_id"] for cid, r in recheck.evaluation_cases().items() if cid not in sampled)
    (tmp_path / "corpus" / "evaluation" / f"{victim}.json").rename(tmp_path / "corpus" / "evaluation" / "eval-999.json")
    assert recheck.run()["result"] == "FAIL"
