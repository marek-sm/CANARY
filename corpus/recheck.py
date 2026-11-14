"""Section 5 step 8 recheck (W8-T4): the seeded sample and its fixture hashes.

    python -m corpus.recheck   # print the report as JSON; exit 1 on any mismatch

Recomputes, with code that imports nothing from the rest of `corpus/`:

- the sample: the ceil(0.20 x N) evaluation cases with the lowest
  SHA256("CANARY-2026-recheck|" + pool_hash + "|" + candidate_id), where pool_hash
  is the SHA-256 of the newline-joined, sorted candidate IDs in corpus/candidates.jsonl;
- for each sampled case: the template, clean-replacement, canonical-payload,
  original-payload, and every rendered-fixture hash against the record and its
  rendered-hash manifest, and that the case's source and attack fields are still
  exactly those of its reviewed candidate record;
- against the frozen corpus (corpus/freeze.json, read as data): that the evaluation
  files on disk, their `base_case_id`s, and the evaluation records listed in
  `corpus_files` are all exactly its `base_case_ids`; that its `corpus_hash` and
  `source_ledger_hash` are the hashes of their own file lists; that
  corpus/candidates.jsonl, which sets the sample, hashes to its frozen value; and that
  each sampled record, reviewed candidate record, template, rendered-hash manifest,
  and all six rendered C2/C3/C4 attack and clean files hash to their frozen values.

The human half of the recheck, reopening each sampled source, is recorded in
docs/audits/; this module never opens a source or makes a network call.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SALT = "CANARY-2026-recheck|"
RENDERED_KEYS = ("c2_attack", "c2_clean", "c3_attack", "c3_clean", "c4_attack", "c4_clean")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def pool_hash() -> str:
    lines = (ROOT / "corpus" / "candidates.jsonl").read_text(encoding="utf-8").split("\n")
    ids = sorted(json.loads(line)["candidate_id"] for line in lines if line.strip())
    return _sha("\n".join(ids).encode("utf-8"))


def frozen() -> dict:
    return _load("corpus/freeze.json")


def frozen_set_hash(entries: dict[str, str]) -> str:
    return _sha("\n".join(f"{path}\t{sha}" for path, sha in sorted(entries.items())).encode("utf-8"))


def evaluation_cases() -> dict[str, dict]:
    """Evaluation records keyed by candidate ID, in base-case order."""
    out = {}
    for path in sorted((ROOT / "corpus" / "evaluation").glob("eval-*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        out[record["candidate_id"]] = record
    return out


def sample() -> list[str]:
    base_ids = set(frozen()["base_case_ids"])
    cases = {cid: r for cid, r in evaluation_cases().items() if r["base_case_id"] in base_ids}
    pool = pool_hash()
    count = math.ceil(0.20 * len(base_ids))
    return sorted(cases, key=lambda cid: (_sha((SALT + pool + "|" + cid).encode("utf-8")), cid))[:count]


def _frozen_match(files: dict[str, str], rel: str) -> bool:
    path = ROOT / rel
    return rel in files and path.is_file() and _sha(path.read_bytes()) == files[rel]


def check_case(record: dict, files: dict[str, str], ledger: dict[str, str]) -> dict[str, bool]:
    fixture, attack = record["fixture"], record["attack"]
    manifest = _load(fixture["rendered_hash_manifest"])
    record_rel = f"corpus/evaluation/{record['base_case_id']}.json"
    candidate = _load(f"corpus/evaluation/candidates/{record['candidate_id']}.json")
    checks = {
        "template file matches the record": _sha((ROOT / fixture["template_path"]).read_bytes()) == fixture["template_sha256"],
        "template hash matches the manifest": manifest.get("template_sha256") == fixture["template_sha256"],
        "clean replacement hash": _sha(fixture["clean_replacement"].encode("utf-8")) == fixture["clean_replacement_sha256"] == manifest.get("clean_replacement_sha256"),
        "canonical payload hash": _sha(attack["canonical_payload"].encode("utf-8")) == attack["canonical_payload_sha256"] == manifest.get("canonical_payload_sha256"),
        "original payload hash": _sha(attack["original_payload"].encode("utf-8")) == attack["original_payload_sha256"],
        "source matches the reviewed candidate": record["source"] == candidate.get("source"),
        "attack matches the reviewed candidate": all(candidate.get(key) == value for key, value in attack.items()),
    }
    checks["record matches the frozen corpus"] = _frozen_match(files, record_rel)
    checks["reviewed candidate record matches the frozen ledger"] = _frozen_match(ledger, f"corpus/evaluation/candidates/{record['candidate_id']}.json")
    checks["template matches the frozen corpus"] = _frozen_match(files, fixture["template_path"])
    checks["rendered-hash manifest matches the frozen corpus"] = _frozen_match(files, fixture["rendered_hash_manifest"])
    rendered = {key: entry for key, entry in manifest.items() if isinstance(entry, dict) and "path" in entry}
    checks["exactly the six rendered files listed"] = sorted(rendered) == sorted(RENDERED_KEYS)
    for key in RENDERED_KEYS:
        entry = rendered.get(key)
        path = ROOT / entry["path"] if entry else None
        checks[f"rendered {key}"] = bool(entry) and path.is_file() and _sha(path.read_bytes()) == entry["sha256"]
        checks[f"rendered {key} matches the frozen corpus"] = bool(entry) and _frozen_match(files, entry["path"])
    return checks


def run() -> dict:
    freeze = frozen()
    files, ledger = freeze["corpus_files"], freeze["source_ledger_files"]
    cases = evaluation_cases()
    frozen_ids = sorted(freeze["base_case_ids"])
    on_disk = sorted(r["base_case_id"] for r in cases.values())
    stems = sorted(path.stem for path in (ROOT / "corpus" / "evaluation").glob("eval-*.json"))
    listed = sorted(
        Path(rel).stem for rel in files
        if rel.startswith("corpus/evaluation/eval-") and rel.endswith(".json") and "/" not in rel[len("corpus/evaluation/"):]
    )
    report = {
        "corpus_hash": freeze["corpus_hash"],
        "pool_hash": pool_hash(),
        "n": len(freeze["base_case_ids"]),
        "corpus_checks_failed": [
            name for name, ok in {
                "evaluation cases on disk are the frozen base cases": on_disk == frozen_ids,
                "evaluation file names on disk are the frozen base cases": stems == frozen_ids,
                "evaluation records in corpus_files are the frozen base cases": listed == frozen_ids,
                "frozen corpus_hash is the hash of its file list": frozen_set_hash(files) == freeze["corpus_hash"],
                "frozen source_ledger_hash is the hash of its file list": frozen_set_hash(ledger) == freeze["source_ledger_hash"],
                "candidate ledger matches the frozen ledger": _frozen_match(ledger, "corpus/candidates.jsonl"),
            }.items() if not ok
        ],
        "sample": sample(),
        "cases": [],
    }
    for cid in report["sample"]:
        checks = check_case(cases[cid], files, ledger)
        report["cases"].append({
            "base_case_id": cases[cid]["base_case_id"],
            "candidate_id": cid,
            "citation_key": cases[cid]["source"]["citation_key"],
            "checks": len(checks),
            "checks_failed": [name for name, ok in checks.items() if not ok],
        })
    expected = math.ceil(0.20 * report["n"])
    passed = len(report["cases"]) == expected and not report["corpus_checks_failed"] and not any(c["checks_failed"] for c in report["cases"])
    report["result"] = "PASS" if passed else "FAIL"
    return report


def main() -> int:
    report = run()
    print(json.dumps(report, indent=2))
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
