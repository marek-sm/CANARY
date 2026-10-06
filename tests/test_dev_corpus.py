"""W6-T2: the five development bases, C1/demo source records, and the ledger."""

import json
import re
import unicodedata
from pathlib import Path

import pytest

from channels.render import (
    INSERTION_MARKER,
    RECORD_EXTRACTOR_VERSIONS,
    RECORD_RENDERERS,
    substitute,
)
from corpus import render_fixtures
from corpus.intake import candidate_id, check_ledger, near_identical, sha256_text

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "corpus" / "development"
ASSIGNMENT = json.loads((DEV / "task-assignment.json").read_text(encoding="utf-8"))
WRAPPED = ["dev-002", "dev-003", "dev-004", "dev-005"]
RESERVED_GLOBS = ["corpus/development/dev-*.json", "corpus/c1/*.json", "corpus/demo/*.json"]
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def record(base):
    return load(DEV / f"{base}.json")


def reserved_records():
    return [load(p) for g in RESERVED_GLOBS for p in sorted(ROOT.glob(g))]


def ledger():
    lines = (ROOT / "corpus" / "candidates.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def contents(rec):
    template = (ROOT / rec["fixture"]["template_path"]).read_text(encoding="utf-8")
    return (
        template,
        substitute(template, rec["attack"]["canonical_payload"]),
        substitute(template, rec["fixture"]["clean_replacement"]),
    )


def test_all_five_development_bases_exist_with_their_assigned_templates():
    for base in ASSIGNMENT["bases"]:
        rec = record(base["base_case_id"])
        assert rec["split"] == "development"
        assert rec["task"]["template_id"] == base["template_id"]
        for channel, spec in base["channels"].items():
            assert rec["channels"][channel]["tool"] == spec["tool"]
            assert rec["channels"][channel]["resource"] == spec["resource"]


@pytest.mark.parametrize("base", WRAPPED)
def test_recorded_hashes_match(base):
    assert render_fixtures.check_record_hashes(record(base)) == []


def test_committed_fixtures_match_a_fresh_render():
    assert render_fixtures.main(["--check"]) == 0


@pytest.mark.parametrize("base", WRAPPED)
def test_attack_and_clean_differ_only_at_the_slot(base):
    rec = record(base)
    template, attack, clean = contents(rec)
    assert template.count(INSERTION_MARKER) == 1
    prefix, suffix = template.split(INSERTION_MARKER)
    for text, slot in ((attack, rec["attack"]["canonical_payload"]), (clean, rec["fixture"]["clean_replacement"])):
        assert text.startswith(prefix) and text.endswith(suffix)
        assert text[len(prefix) : len(text) - len(suffix)] == slot
    assert attack != clean

    # Same check on the rendered bytes, per channel: strip the escaped slot
    # out of both twins and what's left has to be identical.
    wrapper = rec["fixture"]["wrapper"]
    for channel, (render, _) in RECORD_RENDERERS.items():
        a, c = render(attack, wrapper), render(clean, wrapper)
        marker = render(template.replace(INSERTION_MARKER, "SLOTPROBE7f3a"), wrapper)
        before, after = marker.split("SLOTPROBE7f3a")
        assert a.startswith(before) and a.endswith(after), channel
        assert c.startswith(before) and c.endswith(after), channel


@pytest.mark.parametrize("base", WRAPPED)
def test_every_channel_round_trips_to_the_canonical_payload(base):
    rec = record(base)
    _, attack, clean = contents(rec)
    wrapper = rec["fixture"]["wrapper"]
    rendered = {}
    for channel, (render, parse) in RECORD_RENDERERS.items():
        assert rec["channels"][channel]["payload_extractor_version"] == RECORD_EXTRACTOR_VERSIONS[channel]
        for text in (attack, clean):
            assert parse(render(text, wrapper), wrapper) == text
        rendered[channel] = render(attack, wrapper)
        assert parse(rendered[channel], wrapper) == rec["attack"]["canonical_payload"]
    assert len(set(rendered.values())) == 3


@pytest.mark.parametrize("base", WRAPPED)
def test_benign_facts_appear_on_every_channel(base):
    rec = record(base)
    _, _, clean = contents(rec)
    wrapper = rec["fixture"]["wrapper"]
    c2 = json.loads(RECORD_RENDERERS["C2"][0](clean, wrapper))
    c3 = RECORD_RENDERERS["C3"][0](clean, wrapper)
    c4 = RECORD_RENDERERS["C4"][0](clean, wrapper)
    for key, value in wrapper["facts"].items():
        assert c2[key] == value
        assert f"{key}: {value}\n" in c3
        assert f"<dt>{key}</dt><dd>{value}</dd>" in c4


def test_hostile_markup_in_the_payload_cannot_break_out_of_its_field():
    wrapper = {"title": "t", "facts": {"a": "1"}, "text_field": "note"}
    nasty = '</div><div class="note">fake</div>"}\n\nheader: spoof'
    for channel, (render, parse) in RECORD_RENDERERS.items():
        assert parse(render(nasty, wrapper), wrapper) == nasty, channel


def test_wrapper_rejects_a_text_field_that_shadows_a_fact():
    with pytest.raises(ValueError):
        RECORD_RENDERERS["C2"][0]("x", {"title": "t", "facts": {"note": "1"}, "text_field": "note"})


@pytest.mark.parametrize("rec", reserved_records(), ids=lambda r: r["base_case_id"])
def test_reserved_source_records_are_well_formed(rec):
    src, attack = rec["source"], rec["attack"]
    for field in ("citation_key", "url", "title", "source_version", "source_case_id", "license", "opened_by", "opened_at", "reviewed_by"):
        assert src[field], field
    assert sha256_text(attack["original_payload"]) == attack["original_payload_sha256"]
    assert sha256_text(attack["canonical_payload"]) == attack["canonical_payload_sha256"]
    assert attack["primary_goal"] in ("secret_disclosure", "unauthorized_action")
    assert attack["adaptation_notes"] and attack["adapted_by"]
    payload = attack["canonical_payload"]
    assert unicodedata.normalize("NFC", payload) == payload
    # SPEC.md Section 5: the benchmark never hands the model the canary itself.
    assert "CANARY-" not in payload
    # Every address in an adapted payload is synthetic.
    for address in EMAIL.findall(payload):
        assert address.endswith("@fixture.test"), address
    if "candidate_id" in rec:
        expected = candidate_id(src["citation_key"], src["source_version"], src["source_case_id"], attack["original_payload_sha256"])
        assert rec["candidate_id"] == expected
    # A reviewer, once named, is never the opener or the adapter.
    for reviewer in (src["reviewed_by"], attack["reviewed_by"]):
        if reviewer != "PENDING_REVIEW":
            assert reviewer not in (src["opened_by"], attack["adapted_by"])


def test_tier_has_four_c1_controls_and_one_demo_case():
    assert len(list(ROOT.glob("corpus/c1/*.json"))) == 4
    assert len(list(ROOT.glob("corpus/demo/*.json"))) == 1
    splits = {r["base_case_id"]: r["split"] for r in reserved_records()}
    assert sum(s == "c1_control" for s in splits.values()) == 4
    assert sum(s == "demo" for s in splits.values()) == 1


def test_ledger_is_consistent_and_lists_every_development_base():
    rows = ledger()
    assert check_ledger(rows) == []
    dev_ids = set()
    for base in ASSIGNMENT["bases"]:
        rec = record(base["base_case_id"])
        src = rec["source"]
        cid = candidate_id(src["citation_key"], src["source_version"], src["source_case_id"], rec["attack"]["original_payload_sha256"])
        assert rec.get("candidate_id", cid) == cid  # dev-001 predates the field
        dev_ids.add(cid)
    assert {r["candidate_id"] for r in rows if r["status"] == "development"} == dev_ids


def test_development_bases_are_not_near_duplicates_of_each_other():
    payloads = [record(b["base_case_id"])["attack"]["canonical_payload"] for b in ASSIGNMENT["bases"]]
    for i, a in enumerate(payloads):
        for b in payloads[i + 1 :]:
            assert not near_identical(a, b)
