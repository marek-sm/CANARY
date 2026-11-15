"""W8-T3: tests for the deterministic release sanitizer (docs/DATA_RELEASE.md)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis.sanitizer import (
    REDACTION,
    sanitize_bundle,
    sanitize_record,
    scored_projection,
)

ROOT = Path(__file__).resolve().parents[1]
DEV_FIXTURE = ROOT / "tests" / "fixtures" / "result" / "valid_development.json"


def _raw_with_secrets():
    raw = json.loads(DEV_FIXTURE.read_text(encoding="utf-8"))
    raw.setdefault("run_metadata", {})
    raw["run_metadata"]["api_key"] = "sk-REAL-SECRET"
    raw["run_metadata"]["home_dir"] = "C:/Users/someone"
    raw["run_metadata"]["token"] = "bearer-xyz"
    if raw.get("final_output") is None:
        raw["final_output"] = "leaked CANARY-abc here"
    return raw


def test_scored_projection_is_unchanged_by_sanitization():
    raw = _raw_with_secrets()
    san = sanitize_record(raw)
    assert scored_projection(raw) == scored_projection(san)


def test_secrets_paths_and_tokens_are_redacted():
    san = sanitize_record(_raw_with_secrets())
    assert san["run_metadata"]["api_key"] == REDACTION
    assert san["run_metadata"]["home_dir"] == REDACTION
    assert san["run_metadata"]["token"] == REDACTION


def test_comparability_and_scored_hash_fields_survive():
    raw = _raw_with_secrets()
    san = sanitize_record(raw)
    assert san["run_metadata"].get("model_resolved") == raw["run_metadata"].get("model_resolved")
    assert san.get("final_output_sha256") == raw.get("final_output_sha256")


def test_model_text_is_removed_but_field_type_preserved():
    raw = _raw_with_secrets()
    san = sanitize_record(raw)
    # final_output is typed string|null in the locked result schema; redaction
    # keeps it a string marker, with the digest carried by final_output_sha256.
    assert san["final_output"] in (REDACTION, None)
    assert "CANARY" not in json.dumps(san["final_output"])


def test_bundle_writes_schema_valid_manifest_and_is_deterministic(tmp_path):
    raw_dir = tmp_path / "raw" / "cell"
    raw_dir.mkdir(parents=True)
    (raw_dir / "results.jsonl").write_text(json.dumps(_raw_with_secrets()) + "\n", encoding="utf-8")

    out_a = tmp_path / "a"
    manifest_path = sanitize_bundle(tmp_path / "raw", out_a, commit="deadbeef", protocol_id="p")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["bundle_type"] == "sanitized"
    assert manifest["sanitizer_version"]
    assert len(manifest["files"]) == 1

    out_b = tmp_path / "b"
    sanitize_bundle(tmp_path / "raw", out_b, commit="deadbeef", protocol_id="p")
    assert (out_a / "cell" / "results.jsonl").read_bytes() == (out_b / "cell" / "results.jsonl").read_bytes()


def test_sanitized_result_still_validates(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "results.jsonl").write_text(json.dumps(_raw_with_secrets()) + "\n", encoding="utf-8")
    # sanitize_bundle validates results.jsonl against the result schema internally;
    # if the sanitized record broke the schema this would raise.
    sanitize_bundle(raw_dir, tmp_path / "out", commit="c", protocol_id="p")
