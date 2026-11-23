"""N-77-1, N-77-2, and N-77-11: the release sanitizer over a whole mock sweep run.

The run comes from the real sweep path in tests/test_sweep.py (a fake provider that
reaches no network). Nothing here reads results/ or any official record.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import jsonschema
import pytest

from analysis.sanitizer import REDACTION, sanitize_bundle, sanitize_record, verify_projection_unchanged
from tests.test_sweep import _run, corpus, frozen, provider  # noqa: F401  (fixtures)

_HEX64 = re.compile(r"[0-9a-f]{64}")


@pytest.fixture
def run(gate, provider, corpus, tmp_path):  # noqa: F811
    gate.open()
    out = tmp_path / "sweep"
    _run(provider, corpus, out)
    return out


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]


def _strings(node):
    """Every string leaf and every dict key."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _strings(value)


def _text(value: str) -> bool:
    """Free text, as opposed to an identifier or a digest: it has whitespace."""
    return len(value) >= 12 and any(ch.isspace() for ch in value)


def _released_strings(out: Path) -> list[str]:
    """Every string leaf of every released JSONL record, decoded, so JSON escaping can't hide a match."""
    return [s for p in sorted(out.rglob("*.jsonl")) for record in _jsonl(p) for s in _strings(record)]


def test_n77_1_no_model_text_raw_body_tool_content_or_canary_is_released(run, tmp_path):
    secrets: set[str] = set()
    for events in run.glob("*/events.jsonl"):
        for event in _jsonl(events):
            payload = event["payload"]
            kind = event["event_type"]
            if kind == "final_output" and isinstance(payload.get("text"), str):
                secrets.add(payload["text"])
            if kind == "provider_attempt":
                secrets |= {s for s in _strings(payload.get("raw_response")) if _text(s)}
            if kind in ("tool_requested", "tool_result", "tool_dispatch", "sink_receipt", "effect_observation"):
                secrets |= {s for s in _strings(payload) if _text(s)}
    for results in run.glob("*/results.jsonl"):
        for record in _jsonl(results):
            secrets |= set(record["canaries"])
            for tool_event in record["tool_events"]:
                secrets |= {s for s in _strings(tool_event.get("requested_args")) if _text(s)}
    assert secrets, "the mock run should produce model text, tool content, and canaries"

    out = tmp_path / "public"
    sanitize_bundle(run, out, commit="c", protocol_id="p")
    released = _released_strings(out)
    leaked = sorted(s for s in secrets if any(s in leaf for leaf in released))
    assert not leaked, f"{len(leaked)} of {len(secrets)} raw strings released, e.g. {leaked[:3]}"


def test_n77_1_released_text_is_a_content_address(run, tmp_path):
    """Removed text is replaced by its SHA-256, so the public bundle stays checkable against the raw one."""
    out = tmp_path / "public"
    sanitize_bundle(run, out, commit="c", protocol_id="p")
    [raw_record] = _jsonl(next(run.glob("*/results.jsonl")))
    trial = next(run.glob("*/results.jsonl")).parent.name
    [public_record] = _jsonl(out / trial / "results.jsonl")
    assert raw_record["canaries"], "the mock trial has canaries"
    for raw, public in zip(raw_record["canaries"], public_record["canaries"]):
        assert public.startswith("sha256:") and _HEX64.fullmatch(public.removeprefix("sha256:"))
        assert public != raw


def test_n77_2_every_events_file_is_schema_checked(run, tmp_path):
    events = next(run.glob("*/events.jsonl"))
    lines = events.read_text(encoding="utf-8").split("\n")
    first = json.loads(lines[0])
    first["not_in_the_event_schema"] = True
    lines[0] = json.dumps(first)
    events.write_text("\n".join(lines), encoding="utf-8")
    with pytest.raises(jsonschema.ValidationError):
        sanitize_bundle(run, tmp_path / "public", commit="c", protocol_id="p")


@pytest.mark.parametrize("field", ["event_id", "sequence", "event_type", "model_call_id", "attempt_id"])
def test_n77_2_event_identifiers_are_in_the_projection_check(run, field):
    event = _jsonl(next(run.glob("*/events.jsonl")))[1]
    changed = copy.deepcopy(event)
    changed[field] = 999 if field == "sequence" else ("trial_ended" if field == "event_type" else "changed")
    with pytest.raises(ValueError):
        verify_projection_unchanged([event], [changed])


def test_n77_2_raw_evidence_digest_is_in_the_projection_check(run):
    event = next(e for e in _jsonl(next(run.glob("*/events.jsonl"))) if e["raw_evidence"].get("sha256"))
    changed = copy.deepcopy(event)
    changed["raw_evidence"]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        verify_projection_unchanged([event], [changed])


def test_n77_2_only_schema_bound_jsonl_is_released(run, tmp_path):
    out = tmp_path / "public"
    sanitize_bundle(run, out, commit="c", protocol_id="p")
    released = {p.name for p in out.rglob("*.jsonl")}
    assert released == {"results.jsonl", "events.jsonl"}


def test_n77_11_a_fixture_argument_named_like_a_credential_is_hashed_not_blanked():
    """Key-name redaction blanked a legitimate argument; now argument text keeps a content address."""
    record = {"tool_events": [{"call_id": "c1", "requested_args": {"organization": "Acme Corp", "contact": "Dana Lee"}}]}
    args = sanitize_record(record)["tool_events"][0]["requested_args"]
    values = list(args.values())
    assert REDACTION not in values and len(set(values)) == 2
    assert all(v.startswith("sha256:") for v in values)
    assert "Acme" not in json.dumps(args)


def test_credentials_in_run_metadata_are_still_redacted():
    record = {"run_metadata": {"api_key": "sk-REAL", "home_dir": "/Users/someone", "model_resolved": "m"}}
    metadata = sanitize_record(record)["run_metadata"]
    assert metadata["api_key"] == REDACTION and metadata["home_dir"] == REDACTION
    assert metadata["model_resolved"] == "m"


def test_sanitized_bundle_validates_and_keeps_every_scored_field(run, tmp_path):
    out = tmp_path / "public"
    sanitize_bundle(run, out, commit="c", protocol_id="p")  # validates and checks projections internally
    for raw in run.glob("*/results.jsonl"):
        public = out / raw.parent.name / "results.jsonl"
        verify_projection_unchanged(_jsonl(raw), _jsonl(public))
    for raw in run.glob("*/events.jsonl"):
        verify_projection_unchanged(_jsonl(raw), _jsonl(out / raw.parent.name / "events.jsonl"))


def test_sanitizing_twice_is_byte_identical(run, tmp_path):
    sanitize_bundle(run, tmp_path / "a", commit="c", protocol_id="p")
    sanitize_bundle(run, tmp_path / "b", commit="c", protocol_id="p")
    for path in sorted((tmp_path / "a").rglob("*")):
        if path.is_file():
            assert path.read_bytes() == (tmp_path / "b" / path.relative_to(tmp_path / "a")).read_bytes()


def test_b1_model_chosen_argument_names_are_addressed_too():
    record = {"tool_events": [{"call_id": "c1", "requested_args": {"CANARY-0123456789abcdef": "x"}}],
              "payload": {"raw_response": {"content": [{"input": {"CANARY-0123456789abcdef": "y"}}]}}}
    assert "CANARY-0123456789abcdef" not in json.dumps(sanitize_record(record))


def test_b2_disclosure_scan_keeps_its_hash_and_boolean():
    scan = {"scanned_sha256": "a" * 64, "beyond_final_output": True}
    record = {"disclosure_scan": scan}
    assert sanitize_record(record)["disclosure_scan"] == scan
    changed = {"disclosure_scan": {**scan, "scanned_sha256": "b" * 64}}
    with pytest.raises(ValueError):
        verify_projection_unchanged([record], [changed])


def test_error_class_survives_but_error_text_does_not():
    payload = {"error": {"type": "invalid_body", "message": "provider said something long here"}}
    out = sanitize_record({"event_id": "t:e1", "payload": payload})["payload"]["error"]
    assert out["type"] == "invalid_body" and out["message"].startswith("sha256:")


def test_an_empty_final_output_stays_empty():
    """An empty string reveals nothing, and a redaction marker would misstate it as removed text."""
    assert sanitize_record({"final_output": ""})["final_output"] == ""
    assert sanitize_record({"final_output": "model text"})["final_output"] == REDACTION
    assert sanitize_record({"final_output": None})["final_output"] is None


def test_an_empty_redacted_field_stays_empty():
    metadata = sanitize_record({"run_metadata": {"api_key": "", "home_dir": "", "hostname": "box"}})["run_metadata"]
    assert metadata == {"api_key": "", "home_dir": "", "hostname": REDACTION}


def test_cut_off_text_is_addressed_as_payload_text_not_redacted():
    """`trial_ended.cut_off_text` sits in an event payload, so it gets the payload rule: its content
    address, like every other model text there. No key list claims a treatment it never gets."""
    from analysis import sanitizer

    ended = sanitize_record({"event_id": "t:e9", "payload": {"cut_off_text": "partial model text"}})
    assert ended["payload"]["cut_off_text"] == sanitizer.address("partial model text")
    assert "cut_off_text" not in sanitizer._TEXT_TO_HASH_KEYS


def test_every_released_final_output_is_redacted_or_empty(run, tmp_path):
    out = tmp_path / "public"
    sanitize_bundle(run, out, commit="c", protocol_id="p")
    raw = {r["logical_trial_id"]: r for p in run.glob("*/results.jsonl") for r in _jsonl(p)}
    for path in out.glob("*/results.jsonl"):
        for record in _jsonl(path):
            original = raw[record["logical_trial_id"]]["final_output"]
            expected = original if original in ("", None) else REDACTION
            assert record["final_output"] == expected
