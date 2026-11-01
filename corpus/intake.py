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
  and a reason when it isn't kept, so nothing gets dropped silently. It also
  enforces the reviewer rules and the duplicate keeper rule.
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
# A file path is any of:
#   - rooted: /tmp, ./x, ../x, ~/Documents/Private
#   - a dotfile, optionally with more parts: .env, .ssh/id_rsa
#   - relative, two or more parts joined by "/": config/secrets, config/api_keys.env
#   - a bare file name whose extension is a known file type: tempfile.txt
# and nothing else. Bare domains (amazon.com), product names (node.js), a
# missing space after a period (end.Next, '.The'), slashed words (and/or, his/her),
# short codes (C2/C3/C4, 24/7), and closing tags (</INFORMATION>) are not paths.
_PATH_TOKEN = re.compile(r"(?<![\w/<.@~-])(?:~|\.{1,2})?/?[\w.\-]+(?:/[\w.\-]*)*")
_FILE_EXTENSIONS = frozenset(
    "txt csv tsv json jsonl env md pdf doc docx xls xlsx ppt pptx log yaml yml ini cfg conf toml xml "
    "html htm sql db sqlite key pem crt bak zip tar gz mp3 mp4 wav mov png jpg jpeg gif".split()
)
_SLASHED_WORDS = frozenset(
    "and/or either/or his/her he/she s/he him/her yes/no on/off true/false input/output "
    "read/write pass/fail before/after".split()
)


def _is_path(token: str) -> bool:
    if token.startswith(("/", "./", "../", "~/")):
        return len(token) > 1
    if token.startswith(".") and len(token) > 1 and token[1].islower():
        return True  # dotfile; ".The" after a run-on sentence or ".NET" isn't one
    if "/" in token:
        parts = [part for part in token.split("/") if part]
        if len(parts) < 2 or token.casefold() in _SLASHED_WORDS:
            return False
        # short codes like C2/C3/C4 or 24/7 aren't paths
        return any(len(part) >= 3 and any(c.isalpha() for c in part) for part in parts)
    stem, dot, ext = token.rpartition(".")
    return bool(dot) and len(stem) >= 1 and ext in _FILE_EXTENSIONS


def _replace_paths(text: str) -> str:
    def swap(match: re.Match) -> str:
        token = match.group(0)
        trail = ""
        while token and token[-1] in ".-" and token not in ("..", "."):
            token, trail = token[:-1], token[-1] + trail  # sentence-final period
        return (" pathplaceholder " + trail) if _is_path(token) else match.group(0)

    return _PATH_TOKEN.sub(swap, text)


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
    # Placeholders go in before case folding so the path rule can still see
    # case (".env" is a dotfile, ".The" after a run-on sentence isn't). The
    # placeholders are lowercase, so the key is the same either way.
    text = unicodedata.normalize("NFKC", payload)
    text = _URL.sub(" urlplaceholder ", text)
    text = _EMAIL.sub(" emailplaceholder ", text)
    text = _replace_paths(text).casefold()
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


PENDING = "PENDING_REVIEW"


def check_ledger(rows: Iterable[dict], reserved_ids: Iterable[str] = ()) -> list[str]:
    """Return a list of problems; empty means the ledger is consistent.

    `reserved_ids` are the dev, C1, and demo base IDs a `duplicate` row may
    name as its kept case.
    """
    rows = list(rows)
    reserved_ids = set(reserved_ids)
    by_id = {row.get("candidate_id"): row for row in rows}
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
        kept = status in KEPT_STATUSES
        if status not in STATUSES:
            problems.append(f"{where}: unknown status {status!r}")
        elif not kept and not row.get("rejection_reason"):
            problems.append(f"{where}: status {status} needs a rejection_reason")

        for field in ("opened_by", "opened_at", "reviewed_by"):
            if not src.get(field):
                problems.append(f"{where}: source.{field} is empty")
        adapter = row.get("adapted_by")
        if row.get("adapted_payload_sha256") is not None:
            if not adapter:
                problems.append(f"{where}: adapted but adapted_by is empty")
            if kept and not row.get("reviewed_by"):
                problems.append(f"{where}: adapted kept row needs a reviewed_by")
        problems += review_problems(where, src.get("opened_by"), adapter, (src.get("reviewed_by"), row.get("reviewed_by")), kept)

        if status == "evaluation":
            payload = row.get("canonical_payload")
            if not payload:
                problems.append(f"{where}: evaluation row has no canonical_payload, so it can't be deduplicated")
            elif row.get("adapted_payload_sha256") not in (None, sha256_text(payload)):
                problems.append(f"{where}: canonical_payload doesn't match adapted_payload_sha256")

        if status == "duplicate":
            keeper = row.get("duplicate_of")
            if not keeper:
                problems.append(f"{where}: duplicate row must name the kept case in duplicate_of")
            elif keeper in by_id:
                keeper_status = by_id[keeper].get("status")
                if keeper_status == "duplicate":
                    problems.append(f"{where}: duplicate_of {keeper} is itself a duplicate")
                elif keeper_status not in KEPT_STATUSES:
                    problems.append(f"{where}: duplicate_of {keeper} was rejected ({keeper_status}), so it can't be the kept case")
                if selection_hash(keeper) > selection_hash(cid):
                    problems.append(f"{where}: keeper {keeper} doesn't have the lowest selection hash; {cid} should be kept")
            elif keeper not in reserved_ids:
                problems.append(f"{where}: duplicate_of {keeper} isn't a ledger candidate or reserved base")
    return problems


def review_problems(where, opener, adapter, reviewers, kept) -> list[str]:
    """Reviewer checks for one ledger row or reserved record.

    Every named reviewer must differ from the opener and the adapter, and a
    kept case can't still be waiting on its review.
    """
    problems = []
    for reviewer in reviewers:
        if not reviewer:
            continue
        if reviewer == PENDING:
            if kept:
                problems.append(f"{where}: still {PENDING}")
        elif reviewer in (opener, adapter):
            problems.append(f"{where}: reviewer {reviewer} must differ from opener and adapter")
    return sorted(set(problems))


def exact_hash_duplicates(rows: Iterable[dict], reserved: dict[str, dict] | None = None) -> list[str]:
    """Kept rows that share a payload hash or candidate ID with each other or
    with a reserved (dev, C1, demo) record.

    `reserved` maps a base ID to {"candidate_id", "original_payload_sha256",
    "canonical_payload_sha256"}. A development row is allowed to match its own
    development record.
    """
    problems = []
    seen: dict[tuple[str, str], str] = {}
    kept_rows = [row for row in rows if row.get("status") in KEPT_STATUSES]
    for row in kept_rows:
        for field in ("original_payload_sha256", "adapted_payload_sha256"):
            value = row.get(field)
            if value is None:
                continue
            other = seen.setdefault((field, value), row["candidate_id"])
            if other != row["candidate_id"]:
                problems.append(f"{row['candidate_id']}: same {field} as {other}")

    for row in kept_rows:
        cid = row["candidate_id"]
        hashes = {row.get("original_payload_sha256"), row.get("adapted_payload_sha256")} - {None}
        for base, rec in sorted((reserved or {}).items()):
            if row.get("status") == "development" and base.startswith("dev-") and rec["candidate_id"] == cid:
                continue
            if rec["candidate_id"] == cid:
                problems.append(f"{cid}: same candidate_id as reserved base {base}")
            elif hashes & {rec["original_payload_sha256"], rec["canonical_payload_sha256"]}:
                problems.append(f"{cid}: same payload hash as reserved base {base}")
    return problems


def load_reserved(root) -> dict[str, dict]:
    """Every dev, C1, and demo record, keyed by base ID."""
    reserved = {}
    for pattern in ("development/dev-*.json", "c1/*.json", "demo/*.json"):
        for path in sorted((root / "corpus").glob(pattern)):
            reserved_rec = json.loads(path.read_text(encoding="utf-8"))
            reserved[reserved_rec["base_case_id"]] = reserved_rec
    return reserved


def reserved_summary(rec: dict) -> dict:
    src, attack = rec["source"], rec["attack"]
    return {
        "candidate_id": rec.get("candidate_id") or candidate_id(
            src["citation_key"], src["source_version"], src["source_case_id"], attack["original_payload_sha256"]
        ),
        "original_payload_sha256": attack["original_payload_sha256"],
        "canonical_payload_sha256": attack["canonical_payload_sha256"],
    }


def main(argv: list[str] | None = None) -> int:
    """`python -m corpus.intake`: check the ledger against the reserved bases."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    rows = [
        json.loads(line)
        for line in (root / "corpus" / "candidates.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    records = load_reserved(root)
    summaries = {base: reserved_summary(rec) for base, rec in records.items()}
    problems = check_ledger(rows, reserved_ids=records) + exact_hash_duplicates(rows, summaries)

    # Reserved records are kept cases too, so the same reviewer rules apply.
    for base, rec in sorted(records.items()):
        src, attack = rec["source"], rec["attack"]
        problems += review_problems(
            base, src.get("opened_by"), attack.get("adapted_by"),
            (src.get("reviewed_by"), attack.get("reviewed_by")), kept=True,
        )

    reserved = {base: rec["attack"]["canonical_payload"] for base, rec in records.items()}
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
