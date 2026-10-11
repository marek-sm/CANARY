"""Candidate intake: IDs, dedup, and ledger checks (SPEC.md Section 5).

Everything here runs on payload text and source fields only. Nothing reads a
model output or a trial result, so none of it can turn into outcome-based
selection.

- `candidate_id` is step 2: first 20 hex of SHA-256 over the compact JSON array
  `[citation_key, source_version, source_case_id_or_sentinel,
  original_payload_sha256]`, computed before adaptation.
- `dedup_key`, `jaccard_3gram`, and `duplicate_groups` are step 4, exactly as
  decision 0007 froze it.
- `check_ledger` makes sure every considered candidate has one allowed status
  and a reason when it isn't kept, so nothing gets dropped silently.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Iterable

NO_SOURCE_CASE_ID = "NO_SOURCE_CASE_ID"
SELECTION_SALT = "CANARY-2026|"
NEAR_DUPLICATE_JACCARD = 0.8

# The frozen SPEC.md Section 5 status list.
STATUSES = (
    "development",
    "evaluation",
    "duplicate",
    "unsupported_capability",
    "unsafe",
    "license_unclear",
    "not_deterministically_scorable",
    "cannot_port_without_changing_goal",
    "out_of_scope",
)
KEPT_STATUSES = ("development", "evaluation")

# One fixed placeholder per kind. Order matters: URLs before emails before
# paths, so a URL's path or an email's dots aren't half-replaced first.
_URL = re.compile(r"\b(?:https?|ftp)://\S+|\bwww\.\S+", re.I)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PATH = re.compile(r"(?<![\w/])(?:~|\.{1,2})?/[\w.\-]+(?:/[\w.\-]*)*")
_DIGITS = re.compile(r"\d+")
_PUNCT = re.compile(r"[^\w\s]")
_SPACE = re.compile(r"\s+")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def candidate_id(
    citation_key: str,
    source_version: str,
    source_case_id: str | None,
    original_payload_sha256: str,
) -> str:
    case_id = source_case_id or NO_SOURCE_CASE_ID
    blob = json.dumps(
        [citation_key, source_version, case_id, original_payload_sha256],
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return sha256_text(blob)[:20]


def selection_hash(cid: str) -> str:
    return sha256_text(SELECTION_SALT + cid)


def dedup_key(payload: str) -> str:
    text = unicodedata.normalize("NFKC", payload).casefold()
    text = _URL.sub(" urlplaceholder ", text)
    text = _EMAIL.sub(" emailplaceholder ", text)
    text = _PATH.sub(" pathplaceholder ", text)
    text = _DIGITS.sub(" digitsplaceholder ", text)
    text = _PUNCT.sub("", text)
    return _SPACE.sub(" ", text).strip()


def _word_3grams(key: str) -> set[tuple[str, ...]]:
    words = key.split()
    if len(words) < 3:
        return {tuple(words)} if words else set()
    return {tuple(words[i : i + 3]) for i in range(len(words) - 2)}


def jaccard_3gram(a: str, b: str) -> float:
    """Jaccard similarity of the word 3-gram sets of two payloads' dedup keys."""
    ga, gb = _word_3grams(dedup_key(a)), _word_3grams(dedup_key(b))
    if not ga and not gb:
        return 1.0
    return len(ga & gb) / len(ga | gb)


def near_identical(a: str, b: str) -> bool:
    if dedup_key(a) == dedup_key(b):
        return True
    return jaccard_3gram(a, b) >= NEAR_DUPLICATE_JACCARD


def duplicate_groups(payloads: dict[str, str]) -> list[list[str]]:
    """Group candidate IDs whose canonical payloads are near-identical.

    Groups are connected components of the near-identical relation, and each
    group is ordered with the keeper (lowest selection hash) first.
    Singletons are left out.
    """
    ids = sorted(payloads)
    parent = {cid: cid for cid in ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            if near_identical(payloads[a], payloads[b]):
                parent[find(a)] = find(b)

    groups: dict[str, list[str]] = {}
    for cid in ids:
        groups.setdefault(find(cid), []).append(cid)
    return [
        sorted(members, key=selection_hash)
        for members in groups.values()
        if len(members) > 1
    ]


def reserved_collisions(
    candidates: dict[str, str], reserved: dict[str, str]
) -> dict[str, str]:
    """Map each candidate near-identical to a development, C1, or demo base
    onto the reserved base it collides with. Those become `duplicate` and
    never enter evaluation."""
    hits = {}
    for cid, payload in sorted(candidates.items()):
        for rid, rpayload in sorted(reserved.items()):
            if near_identical(payload, rpayload):
                hits[cid] = rid
                break
    return hits


def check_ledger(rows: Iterable[dict]) -> list[str]:
    """Return a list of problems; empty means the ledger is consistent."""
    problems = []
    seen = set()
    for n, row in enumerate(rows, 1):
        cid = row.get("candidate_id")
        where = f"row {n} ({cid})"
        src = row.get("source") or {}
        expected = candidate_id(
            src.get("citation_key", ""),
            src.get("source_version", ""),
            src.get("source_case_id"),
            row.get("original_payload_sha256", ""),
        )
        if cid != expected:
            problems.append(f"{where}: candidate_id should be {expected}")
        if cid in seen:
            problems.append(f"{where}: repeated candidate_id")
        seen.add(cid)
        status = row.get("status")
        if status not in STATUSES:
            problems.append(f"{where}: unknown status {status!r}")
        elif status not in KEPT_STATUSES and not row.get("rejection_reason"):
            problems.append(f"{where}: status {status} needs a rejection_reason")
        for field in ("opened_by", "opened_at", "reviewed_by"):
            if not src.get(field):
                problems.append(f"{where}: source.{field} is empty")
        if row.get("adapted_payload_sha256") is not None:
            adapter = row.get("adapted_by")
            reviewer = row.get("reviewed_by")
            if not adapter:
                problems.append(f"{where}: adapted but adapted_by is empty")
            if reviewer and reviewer != "PENDING_REVIEW" and reviewer in (
                adapter,
                src.get("opened_by"),
            ):
                problems.append(f"{where}: reviewer must differ from opener and adapter")
    return problems


def exact_hash_duplicates(rows: Iterable[dict]) -> list[str]:
    """Kept rows that share an original or adapted payload hash."""
    problems = []
    seen: dict[tuple[str, str], str] = {}
    for row in rows:
        if row.get("status") not in KEPT_STATUSES:
            continue
        for field in ("original_payload_sha256", "adapted_payload_sha256"):
            value = row.get(field)
            if value is None:
                continue
            other = seen.setdefault((field, value), row["candidate_id"])
            if other != row["candidate_id"]:
                problems.append(f"{row['candidate_id']}: same {field} as {other}")
    return problems


def main(argv: list[str] | None = None) -> int:
    """`python -m corpus.intake`: check the ledger against the reserved bases."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    rows = [
        json.loads(line)
        for line in (root / "corpus" / "candidates.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    problems = check_ledger(rows) + exact_hash_duplicates(rows)

    reserved = {}
    for pattern in ("development/dev-*.json", "c1/*.json", "demo/*.json"):
        for path in sorted((root / "corpus").glob(pattern)):
            rec = json.loads(path.read_text(encoding="utf-8"))
            reserved[rec["base_case_id"]] = rec["attack"]["canonical_payload"]

    evaluation = {
        row["candidate_id"]: row["canonical_payload"]
        for row in rows
        if row.get("status") == "evaluation" and row.get("canonical_payload")
    }
    for cid, rid in reserved_collisions(evaluation, reserved).items():
        problems.append(f"{cid}: near-identical to reserved base {rid}; record it as duplicate")
    for group in duplicate_groups(evaluation):
        keeper, *rest = group
        for cid in rest:
            problems.append(f"{cid}: near-identical to {keeper}, which is kept; record it as duplicate")

    for line in problems:
        print(line)
    kept = sum(r.get("status") in KEPT_STATUSES for r in rows)
    print(f"{len(rows)} ledger rows, {kept} kept, {len(reserved)} reserved bases, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
