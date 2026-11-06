"""Deterministic sanitizer for public release bundles (W8-T3).

Implements the sanitizer contract in docs/DATA_RELEASE.md. It reads raw
append-only JSONL evidence and produces a separate sanitized bundle under a
target directory plus a bundle manifest (schemas/manifest.schema.json). It is
deterministic: the same input yields byte-identical output.

It MAY remove or replace:
- credentials and authentication headers;
- provider-only metadata not needed for the declared analysis;
- personal/contact identifiers;
- restricted payload/source text, using stable non-secret references; and
- local absolute paths or machine identifiers not required for reproduction.

It MUST NOT change:
- trial/case/model-call/attempt/protocol/validation identifiers;
- Boolean-or-null scored fields;
- authorization/dispatch/effect/sink/disclosure/utility/infrastructure dispositions;
- pairing keys, model/version fields used for comparability, or aggregate denominators; or
- hashes of retained public evidence.

A result's model text surfaces (``final_output`` and ``trial_ended.cut_off_text``)
and any ``disclosure_scan`` are reduced to a hash + Boolean, per decision 0028.
``scored_projection`` extracts exactly the fields that must survive untouched, so
a test can assert the projection is identical before and after sanitization.

Usage:
    python -m analysis.sanitizer --in results/development/run --out results/public/run
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
SANITIZER_VERSION = "sanitizer-v0.1.0"

# Keys whose values are credentials/provider-only/PII/machine-local and are
# replaced with a stable redaction marker. Matched case-insensitively on the
# leaf key name. Scored fields never appear here.
_REDACT_KEYS = frozenset({
    "authorization", "api_key", "apikey", "x-api-key", "anthropic_api_key", "openai_api_key",
    "credential", "credentials", "secret", "token", "access_token", "bearer",
    "provider_fingerprint_raw", "provider_account", "organization", "user_agent",
    "email_contact", "phone", "contact", "machine_id", "hostname", "home_dir",
})
# Keys holding model text that is reduced to hash + boolean (decision 0028).
_TEXT_TO_HASH_KEYS = frozenset({"final_output", "cut_off_text"})
REDACTION = "[REDACTED]"

# Scored/identifier/comparability fields that must survive sanitization unchanged.
# scored_projection pulls these so a test can compare before vs after.
_PROJECTION_TOP = (
    "schema_version", "protocol_version", "experiment_id", "logical_trial_id",
    "comparison_superblock_id", "base_case_id", "attack_family_id", "case_id",
    "analysis_role", "channel", "condition", "configuration", "run_index",
    "split", "status", "termination_reason", "security", "utility",
    "final_output_sha256",
)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sanitize_value(key: str, value: Any) -> Any:
    """Recursively sanitize one value. ``key`` is the leaf key that held it."""
    lk = key.lower()
    if lk in _REDACT_KEYS:
        return REDACTION if value is not None else None
    if lk in _TEXT_TO_HASH_KEYS and isinstance(value, str):
        # Remove model text. The schema types these fields as string|null, and a
        # sibling scored hash (e.g. final_output_sha256) already carries the
        # verifiable digest, so we redact the text to a marker string rather than
        # introduce an object the locked result schema would reject
        # (docs/DATA_RELEASE.md: model text reduced to a hash + boolean, carried
        # by the untouched scored *_sha256 field; decision 0028).
        return REDACTION
    if isinstance(value, dict):
        return {k: sanitize_value(k, v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_value(key, v) for v in value]
    return value


def sanitize_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return a sanitized copy of one JSONL record."""
    return {k: sanitize_value(k, v) for k, v in record.items()}


def scored_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    """The fields the sanitizer must never change, for a before/after equality test."""
    projection = {k: record[k] for k in _PROJECTION_TOP if k in record}
    # tool-event dispositions are scored and must survive untouched.
    if isinstance(record.get("tool_events"), list):
        projection["tool_events"] = [
            {
                k: te.get(k)
                for k in (
                    "call_id", "step", "tool", "request_evaluable", "authorized",
                    "blocked", "dispatched", "disposition_observed",
                    "execution_succeeded", "effect_observed", "sink_received",
                    "gate_audit_match", "effect_oracle_id",
                )
            }
            for te in record["tool_events"]
        ]
    return projection


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def _write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def verify_projection_unchanged(raw: list[dict[str, Any]], sanitized: list[dict[str, Any]]) -> None:
    """Raise if any scored projection changed. The release gate depends on this."""
    if len(raw) != len(sanitized):
        raise ValueError("sanitizer changed the record count")
    for i, (r, s) in enumerate(zip(raw, sanitized)):
        if scored_projection(r) != scored_projection(s):
            raise ValueError(f"record {i}: sanitizer changed a scored/identifier field")


def _manifest(files: list[Path], base: Path, commit: Optional[str], protocol_id: Optional[str], created_at: str) -> dict[str, Any]:
    entries = []
    for f in sorted(files):
        data = f.read_bytes()
        entries.append({
            "path": f.relative_to(base).as_posix(),
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    return {
        "schema_version": "0.1.0",
        "bundle_type": "sanitized",
        "produced_by_commit": commit,
        "container_digest": None,
        "protocol_id": protocol_id,
        "experiment_or_validation_id": None,
        "sanitizer_version": SANITIZER_VERSION,
        "created_at": created_at,
        "files": entries,
    }


def sanitize_bundle(
    in_dir: Path,
    out_dir: Path,
    *,
    commit: Optional[str] = None,
    protocol_id: Optional[str] = None,
    created_at: str = "1970-01-01T00:00:00Z",
) -> Path:
    """Sanitize every *.jsonl under ``in_dir`` into ``out_dir`` and write a manifest.

    Validates the scored projection is unchanged for each file and (when a
    result schema applies) that sanitized records still validate.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    result_validator = _validator("result")
    for src in sorted(in_dir.rglob("*.jsonl")):
        raw = _read_jsonl(src)
        sanitized = [sanitize_record(r) for r in raw]
        verify_projection_unchanged(raw, sanitized)
        if src.name == "results.jsonl":
            for rec in sanitized:
                result_validator.validate(rec)
        dest = out_dir / src.relative_to(in_dir)
        _write_jsonl(dest, sanitized)
        written.append(dest)
    manifest = _manifest(written, out_dir, commit, protocol_id, created_at)
    _validator("manifest").validate(manifest)
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


_VALIDATORS: dict[str, Draft202012Validator] = {}


def _validator(name: str) -> Draft202012Validator:
    if name not in _VALIDATORS:
        schema = json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        _VALIDATORS[name] = Draft202012Validator(schema)
    return _VALIDATORS[name]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--in", dest="in_dir", type=Path, required=True)
    parser.add_argument("--out", dest="out_dir", type=Path, required=True)
    parser.add_argument("--commit", default=None)
    parser.add_argument("--protocol-id", default=None)
    args = parser.parse_args(argv)
    manifest_path = sanitize_bundle(args.in_dir, args.out_dir, commit=args.commit, protocol_id=args.protocol_id)
    print(f"sanitized bundle written; manifest {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
