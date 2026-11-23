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

A result's model text surfaces and any ``disclosure_scan`` are reduced to a hash + Boolean,
per decision 0028: ``final_output`` becomes a redaction marker beside its untouched
``final_output_sha256``, and ``trial_ended.cut_off_text``, inside an event payload, becomes
its content address like every other payload text. An empty string stays empty in a
redacted field: it reveals nothing, and a marker would misstate it as removed text.
``scored_projection`` extracts exactly the fields that must survive untouched, so
a test can assert the projection is identical before and after sanitization.

Free content is removed by content address, never by key name (N-77-1, N-77-11):
- inside an event ``payload``, a string survives only under a structural key (an
  identifier, digest, version, timestamp, disposition code, or model name); every
  other string becomes ``sha256:<hex>`` of its UTF-8 text;
- inside a content subtree (tool arguments, provider bodies, tool observations,
  server-log entries, and a result's ``canaries``), every string becomes its address.
Numbers, Booleans, and nulls are kept, so every disposition survives. Only
``results.jsonl`` and ``events.jsonl`` are released, each validated against its
schema, and an event's identifiers and dispositions are in the projection check (N-77-2).

Known consequence: ``normalized_args`` is addressed like every other argument, so
``analysis/lead_outputs.py --events`` can't bind released records to raw events
(its ``TOOL_EVENT_FIELDS`` include ``normalized_args``). The count-only release path
(decision 0036 item 6) needs the project lead's decision on that.

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
SANITIZER_VERSION = "sanitizer-v0.2.0"
# The only JSONL files released, each with the schema it must validate against (N-77-2).
RELEASED = {"results.jsonl": "result", "events.jsonl": "event"}

# Keys whose values are credentials/provider-only/PII/machine-local and are
# replaced with a stable redaction marker. Matched case-insensitively on the
# leaf key name. Scored fields never appear here.
_REDACT_KEYS = frozenset({
    "authorization", "api_key", "apikey", "x-api-key", "anthropic_api_key", "openai_api_key",
    "credential", "credentials", "secret", "token", "access_token", "bearer",
    "provider_fingerprint_raw", "provider_account", "organization", "user_agent",
    "email_contact", "phone", "contact", "machine_id", "hostname", "home_dir",
})
# Result keys holding model text that is reduced to hash + boolean (decision 0028). An event
# payload's model text (``trial_ended.cut_off_text``) is addressed by the payload rule instead.
_TEXT_TO_HASH_KEYS = frozenset({"final_output"})
REDACTION = "[REDACTED]"
ADDRESS_PREFIX = "sha256:"
# Subtrees of free content: every string inside becomes its content address.
_CONTENT_KEYS = frozenset({
    "requested_args", "normalized_args", "raw_response", "provider_response", "observation",
    "server_log_entry", "receipt", "canaries",
})
# Inside an event payload, the only keys whose string values survive.
_STRUCTURAL_KEYS = frozenset({
    "call_id", "tool", "gate_action", "evaluator_version", "effect_oracle_id", "model_requested",
    "model_resolved", "outcome", "provider_request_id", "provider_fingerprint", "normalizer_version",
    "status", "termination_reason", "channel", "condition", "configuration", "code_commit",
    "task_version", "template_id", "delivery_version", "tier", "type", "effort", "endpoint",
    "thinking", "reasoning_effort", "reason_codes",
})
_STRUCTURAL_SUFFIXES = ("_id", "_ids", "_sha256", "_hash", "_version", "_at")

# Scored/identifier/comparability fields that must survive sanitization unchanged.
# scored_projection pulls these so a test can compare before vs after.
_PROJECTION_TOP = (
    "schema_version", "protocol_version", "experiment_id", "logical_trial_id",
    "comparison_superblock_id", "base_case_id", "attack_family_id", "case_id",
    "analysis_role", "channel", "condition", "configuration", "run_index",
    "split", "status", "termination_reason", "security", "utility",
    "final_output_sha256", "display_label", "usage", "disclosure_scan",
)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def address(text: str) -> str:
    """The stable, non-secret reference that replaces removed text."""
    return ADDRESS_PREFIX + _sha256_text(text)


def _structural(key: str) -> bool:
    lk = key.lower()
    return lk in _STRUCTURAL_KEYS or lk.endswith(_STRUCTURAL_SUFFIXES)


def _content(value: Any) -> Any:
    """Every string in a content subtree becomes its address, dict keys included,
    because the model chooses argument names; other leaves stay."""
    if isinstance(value, str):
        return address(value)
    if isinstance(value, dict):
        return {address(k): _content(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_content(v) for v in value]
    return value


def _payload(key: str, value: Any) -> Any:
    """Inside an event payload, a string survives only under a structural key."""
    if key.lower() in _CONTENT_KEYS:
        return _content(value)
    if isinstance(value, str):
        return value if _structural(key) else address(value)
    if isinstance(value, dict):
        return {k: _payload(k, v) for k, v in value.items()}
    if isinstance(value, list):
        return [_payload(key, v) for v in value]
    return value


def sanitize_value(key: str, value: Any) -> Any:
    """Recursively sanitize one value. ``key`` is the leaf key that held it."""
    lk = key.lower()
    if lk == "payload" and isinstance(value, dict):
        return {k: _payload(k, v) for k, v in value.items()}
    if lk in _CONTENT_KEYS:
        return _content(value)
    if lk in _REDACT_KEYS:
        return value if value is None or value == "" else REDACTION
    if lk in _TEXT_TO_HASH_KEYS and isinstance(value, str) and value:
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


_EVENT_TOP = (
    "schema_version", "event_id", "sequence", "event_type", "experiment_id", "logical_trial_id",
    "model_call_id", "attempt_id", "configuration", "recorded_at", "component_versions",
)


def _leaves(value: Any) -> list[str]:
    """A content subtree's non-string leaves as a sorted multiset. Its keys and strings are
    addressed, and the bundle is written with sorted keys, so neither order is comparable."""
    def walk(node: Any):
        if isinstance(node, dict):
            for v in node.values():
                yield from walk(v)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v)
        elif not isinstance(node, str):
            yield json.dumps(node)
    return sorted(walk(value))


def _kept(key: str, value: Any, in_content: bool = False) -> Any:
    """The part of a payload the sanitizer must keep: every non-string leaf, and
    every string under a structural key outside a content subtree."""
    if not in_content and key.lower() in _CONTENT_KEYS:
        return _leaves(value)
    if isinstance(value, dict):
        return {k: _kept(k, v, in_content) for k, v in value.items()}
    if isinstance(value, list):
        return [_kept(key, v, in_content) for v in value]
    if isinstance(value, str):
        return value if (not in_content and _structural(key)) else None
    return value


def scored_projection(record: Mapping[str, Any]) -> dict[str, Any]:
    """The fields the sanitizer must never change, for a before/after equality test."""
    if "event_id" in record:  # an event record (N-77-2)
        projection = {k: record.get(k) for k in _EVENT_TOP}
        projection["raw_evidence_sha256"] = (record.get("raw_evidence") or {}).get("sha256")
        projection["payload"] = _kept("payload", record.get("payload"))
        return projection
    projection = {k: record[k] for k in _PROJECTION_TOP if k in record}
    metadata = record.get("run_metadata")
    if isinstance(metadata, dict):
        projection["run_metadata"] = {k: v for k, v in metadata.items() if _structural(k) or k in (
            "model_requested", "model_resolved", "provider_request_ids", "temperature", "top_p",
            "provider_seed", "max_steps", "schedule_index", "schedule_seed", "started_at")}
    for name in ("attempts", "model_calls"):
        if isinstance(record.get(name), list):
            projection[name] = record[name]
    if isinstance(record.get("canaries"), list):
        projection["canary_count"] = len(record["canaries"])
    # tool-event dispositions are scored and must survive untouched.
    if isinstance(record.get("tool_events"), list):
        projection["tool_events"] = [
            {
                k: te.get(k)
                for k in (
                    "call_id", "step", "tool", "request_evaluable", "authorized",
                    "blocked", "dispatched", "disposition_observed",
                    "execution_succeeded", "effect_observed", "sink_received",
                    "gate_audit_match", "effect_oracle_id", "gate_decision", "audit_decision",
                )
            }
            for te in record["tool_events"]
        ]
    return projection


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
    # Split only on the "\n" record separator we write. Records are written with
    # ensure_ascii=False, so model text may hold U+2028/U+2029/U+0085, which
    # str.splitlines() would wrongly split on and corrupt a record
    # (tests/test_verify_evidence.py::test_no_jsonl_reader_splits_with_splitlines).
    for line in path.read_text(encoding="utf-8").split("\n"):
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
    """Sanitize every released JSONL file under ``in_dir`` into ``out_dir`` and write a manifest.

    Validates every raw and sanitized record against its schema, and checks that
    the scored projection is unchanged for each file.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for src in sorted(in_dir.rglob("*.jsonl")):
        if src.name not in RELEASED:  # e.g. code_provenance.jsonl: not part of the public bundle
            continue
        validator = _validator(RELEASED[src.name])
        raw = _read_jsonl(src)
        for rec in raw:
            validator.validate(rec)
        sanitized = [sanitize_record(r) for r in raw]
        verify_projection_unchanged(raw, sanitized)
        for rec in sanitized:
            validator.validate(rec)
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
