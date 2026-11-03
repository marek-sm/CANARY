"""W7-T2 evaluation intake: every considered candidate's source record.

Each ledger row added by W7-T2 has a source record in
`corpus/evaluation/candidates/<candidate_id>.json` that carries what the ledger
schema leaves out: the source locator, the original payload text, and the
adaptation notes. The project lead's source review reads these.
"""

import difflib
import json
import re
from pathlib import Path

import pytest

from corpus.intake import candidate_id, sha256_text

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "corpus" / "evaluation" / "candidates"
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def records():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(CANDIDATES.glob("*.json"))]


def ledger():
    lines = (ROOT / "corpus" / "candidates.jsonl").read_text(encoding="utf-8").splitlines()
    return {r["candidate_id"]: r for r in (json.loads(line) for line in lines if line.strip())}


@pytest.mark.parametrize("rec", records(), ids=lambda r: r["candidate_id"])
def test_record_matches_its_ledger_row(rec):
    row = ledger()[rec["candidate_id"]]
    src = rec["source"]
    assert rec["candidate_id"] == candidate_id(src["citation_key"], src["source_version"], src["source_case_id"], rec["original_payload_sha256"])
    assert sha256_text(rec["original_payload"]) == rec["original_payload_sha256"] == row["original_payload_sha256"]
    for field in ("status", "rejection_reason", "decision_stage", "primary_goal", "attack_family_id", "adapted_by", "reviewed_by"):
        assert rec[field] == row[field], field
    assert {k: v for k, v in src.items() if k != "source_locator"} == row["source"]
    assert src["source_locator"]
    assert rec.get("duplicate_of") == row.get("duplicate_of")


@pytest.mark.parametrize("rec", records(), ids=lambda r: r["candidate_id"])
def test_adapted_payloads_substitute_and_stay_synthetic(rec):
    if rec["adapted_payload"] is None:
        assert rec["decision_stage"] == "source_screening" and rec["rejection_reason"]
        return
    assert rec["canonical_payload"] == rec["adapted_payload"]
    assert sha256_text(rec["canonical_payload"]) == rec["canonical_payload_sha256"]
    row = ledger()[rec["candidate_id"]]
    assert row["adapted_payload_sha256"] == rec["canonical_payload_sha256"]
    if row["status"] == "evaluation":
        assert row["canonical_payload"] == rec["canonical_payload"]
    # SPEC.md Section 5: substitutions only, never dropped or added text.
    ops = difflib.SequenceMatcher(None, rec["original_payload"].split(" "), rec["adapted_payload"].split(" ")).get_opcodes()
    assert not [op for op in ops if op[0] in ("delete", "insert")]
    for address in EMAIL.findall(rec["adapted_payload"]):
        assert address.endswith("@fixture.test"), address
    assert "CANARY-" not in rec["adapted_payload"]
    assert rec["adaptation_notes"]


def test_every_w7_t2_ledger_row_has_a_record():
    rows = ledger()
    have = {r["candidate_id"] for r in records()}
    w7 = {cid for cid, r in rows.items() if r["status"] != "development"}
    assert w7 == have


def test_every_considered_candidate_has_a_status_and_rejections_have_reasons():
    for rec in records():
        if rec["status"] == "evaluation":
            assert rec["rejection_reason"] is None
        else:
            assert rec["rejection_reason"]


PORT_WRAPPER = {"title": "Fixture record", "facts": {"record_id": "R-1"}, "text_field": "note"}


@pytest.mark.parametrize("rec", [r for r in records() if r["status"] == "evaluation"], ids=lambda r: r["candidate_id"])
def test_every_eligible_candidate_ports_to_c2_c3_and_c4(rec):
    # Decision 0025: every candidate has to port to all three channels. Each
    # channel's serializer escapes or wraps the payload differently, and each
    # parser has to recover the exact canonical string.
    from channels.render import RECORD_RENDERERS

    payload = rec["canonical_payload"]
    rendered = {}
    for channel, (render, parse) in RECORD_RENDERERS.items():
        rendered[channel] = render(payload, PORT_WRAPPER)
        assert parse(rendered[channel], PORT_WRAPPER) == payload, channel
    assert len(set(rendered.values())) == 3
