"""W8-T2: the evaluation base cases built from the selected prefix."""

import json
from collections import Counter
from pathlib import Path

import pytest

from corpus import build_evaluation, select
from runner import sweep
from runner.mock_slice import validator
from tasks import registry
from tools.query_db import QUERIES

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "corpus" / "evaluation"
IDS = sorted(p.stem for p in EVAL.glob("eval-*.json"))


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def record(case_id):
    return load(EVAL / f"{case_id}.json")


def test_the_corpus_is_the_twenty_base_prefix_in_order():
    assert IDS == [f"eval-{i:03d}" for i in range(1, 21)]
    plan = select.plan(select.load_rows(), load(select.TASK_ORDER))
    prefix = plan["prefixes"]["20"]["bases"]
    for base in prefix:
        rec = record(f"eval-{base['slot']:03d}")
        assert rec["candidate_id"] == base["candidate_id"]
        assert rec["task"]["template_id"] == base["template_id"]
        assert rec["attack"]["primary_goal"] == base["primary_goal"]


def test_committed_records_match_a_fresh_build():
    assert build_evaluation.main(["--n", "20", "--check"]) == 0


def test_every_template_appears_twice_and_goals_split_ten_ten():
    recs = [record(i) for i in IDS]
    assert Counter(r["task"]["template_id"] for r in recs) == {t["template_id"]: 2 for t in load(select.TASK_ORDER)["order"]}
    assert Counter(r["attack"]["primary_goal"] for r in recs) == {"secret_disclosure": 10, "unauthorized_action": 10}


@pytest.mark.parametrize("case_id", IDS)
def test_record_validates_and_copies_its_reviewed_candidate(case_id):
    rec = record(case_id)
    validator("base_case").validate(rec)
    cand = load(EVAL / "candidates" / f"{rec['candidate_id']}.json")
    assert cand["status"] == "evaluation"
    assert rec["source"] == cand["source"]
    assert rec["source"]["reviewed_by"] == rec["attack"]["reviewed_by"] == "marek-sm"
    for field in ("original_payload", "original_payload_sha256", "adapted_payload", "canonical_payload",
                  "canonical_payload_sha256", "adaptation_notes", "adapted_by", "attack_family_id", "primary_goal"):
        assert rec["attack"][field] == cand[field], field


@pytest.mark.parametrize("case_id", IDS)
def test_task_and_channels_name_real_w6_t1_artifacts(case_id):
    rec = record(case_id)
    task = rec["task"]
    template = registry.load(task["template_id"])
    assert {task["task_id"]} == {v["policy"]["task_id"] for v in template["variants"].values()}
    oracle = template["utility_oracle"]
    assert task["utility_oracle_ref"] == f"oracles/utility/task_suite.py#{oracle['id']}@v{oracle['version']}"
    assert task["authorization_policy_ref"] == f"tasks/templates/{template['template_id']}.json"
    assert task["user_prompt_template"].count("{source}") == 1
    for channel, variant in template["variants"].items():
        call = variant["required_calls"][0]
        locator = f"{call['tool']} with {json.dumps(call['args'], sort_keys=True)}"
        assert task["user_prompt_template"].replace("{source}", locator) == variant["prompt_template"], channel
        assert rec["channels"][channel]["tool"] == call["tool"]
    assert rec["channels"]["C2"]["resource"] == QUERIES[template["variants"]["C2"]["required_calls"][0]["args"]["query_id"]][1]


@pytest.mark.parametrize("case_id", IDS)
def test_every_channel_shows_the_facts_its_answer_comes_from(case_id):
    rec = record(case_id)
    facts = rec["fixture"]["wrapper"]["facts"]
    seed = load(registry.FIXTURES / "db-seed.json")
    rows = [json.loads(r["content"]) for r in seed if r["resource"] == rec["channels"]["C2"]["resource"]]
    assert facts in rows
    others = [r for r in rows if r != facts and r.get("status", "open") == facts.get("status", "open")]
    manifest = load(ROOT / rec["fixture"]["rendered_hash_manifest"])
    for key, entry in manifest.items():
        if not isinstance(entry, dict):
            continue
        rendered = (ROOT / entry["path"]).read_text(encoding="utf-8")
        for name, value in facts.items():
            text = value if isinstance(value, str) else json.dumps(value)
            if key.startswith("c2"):
                assert json.loads(rendered)[name] == value, key
            elif key.startswith("c3"):
                assert f"{name}: {text}\n" in rendered, key
            else:
                assert f"<dt>{name}</dt><dd>{text}</dd>" in rendered, key
        if rec["task"]["template_id"] == "open-ticket-ids" and not key.startswith("c2"):
            for other in others:
                assert other["ticket_id"] in rendered, (key, other)


def test_the_sweep_render_preflight_passes_for_every_cell():
    spec = {"base_case_ids": IDS, "channels": ["C2", "C3", "C4"], "conditions": ["attack", "clean"]}
    assert sweep._bases_refusal(sweep.DEFAULT_CORPUS_ROOT, spec) is None
    assert sweep._renders_refusal(sweep.DEFAULT_CORPUS_ROOT, spec) is None


def test_no_evaluation_payload_carries_a_canary_or_a_real_address():
    for case_id in IDS:
        payload = record(case_id)["attack"]["canonical_payload"]
        assert "CANARY-" not in payload
        assert "@gmail.com" not in payload and "@google.com" not in payload and "@contact.com" not in payload


def test_freeze_manifest_is_current_and_covers_the_corpus():
    from corpus import freeze

    assert freeze.main(["--check"]) == 0
    manifest = load(freeze.OUT)
    assert manifest["base_case_ids"] == IDS
    assert "corpus/candidates.jsonl" in manifest["source_ledger_files"]
    assert all(not p.startswith("corpus/release/") for p in [*manifest["corpus_files"], *manifest["source_ledger_files"]])
    for case_id in IDS:
        assert f"corpus/evaluation/{case_id}.json" in manifest["corpus_files"]
        assert f"fixtures/{case_id}/rendered-hashes.json" in manifest["corpus_files"]
    assert manifest["corpus_hash"] == freeze.set_hash(manifest["corpus_files"])
    assert manifest["source_ledger_hash"] == freeze.set_hash(manifest["source_ledger_files"])
