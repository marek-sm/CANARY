"""Decision 0031 item 6: the attested lead-side review that every paid call needs.

    python -m runner.lead_review attest docs/reviews/<file>.md   # on the project lead's machine
    python -m runner.lead_review check                           # say whether this checkout is attested

`attest` appends one row to ``~/.canary/lead_review.jsonl``, in the same account home
as runner/spend_ledger.py and outside every checkout. A row holds this checkout's
`paid_run.code_digest`, the findings file's path and SHA-256, and its open blocking
count. It refuses a findings file that isn't committed and unchanged here, a tree with
uncommitted changes in recorded code, a header that doesn't name this checkout's
`code_digest`, and an open blocking count that isn't a classified integer.

`refusal(root)` is what `runner.paid_run` calls, at `record` and at every paid grid,
sweep, and rehearsal call. The newest row for this checkout's `code_digest` governs, so a
later review that finds a blocking defect closes the gate an earlier one opened. That row
needs 0 open blocking findings, and its findings file in this checkout must still be
committed, unchanged, and of the attested hash. Any failure to check refuses. The live smoke is exempt, as it is from the paid-run record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from runner import paid_run, spend_ledger

DIGEST = re.compile(r"\b[0-9a-f]{64}\b")
BLOCKING = re.compile(r"^- \*\*Open blocking findings:\*\*(.*)$", re.MULTILINE)


class AttestRefused(ValueError):
    """The findings file can't be attested for this checkout."""


def log_path(path: Optional[Path] = None) -> Path:
    return path or spend_ledger._account_home() / ".canary" / "lead_review.jsonl"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _header(text: str) -> str:
    """Everything before the first second-level heading: where a review states its commit,
    digests, and counts (decision 0031 item 5)."""
    match = re.search(r"^## ", text, re.MULTILINE)
    return text[: match.start()] if match else text


def open_blocking(text: str) -> int:
    """The header's one open blocking count. Its first clause, up to the first full stop,
    holds the count and nothing else that reads as a number or as unclassified."""
    header = _header(text)
    if len(re.findall(r"open blocking findings", header, re.IGNORECASE)) != 1:
        raise AttestRefused("the header needs exactly one '- **Open blocking findings:** N' line")
    lines = BLOCKING.findall(header)
    if len(lines) != 1:
        raise AttestRefused("the header needs exactly one '- **Open blocking findings:** N' line")
    value = lines[0].strip()
    match = re.fullmatch(r"(\d+)(?:\.(?=\s|$)|(?=[\s;,]|$))(.*)", value)
    if not match:
        raise AttestRefused(f"'Open blocking findings' must start with a whole count, not {value!r}")
    clause = re.split(r"\.(?:\s|$)", value, maxsplit=1)[0][len(match.group(1)):]
    if re.search(r"\d|proposed|unclassified|pending", clause, re.IGNORECASE):
        raise AttestRefused("the open blocking count must be classified and stand alone; "
                            f"the project lead classifies every finding first, not {value!r}")
    return int(match.group(1))


def _named_digests(header: str) -> list[str]:
    """The digests the header's `paid_run.code_digest` field names: its own line and any
    sub-bullets under it, up to the next top-level field."""
    lines = header.split("\n")
    out, inside = [], False
    for line in lines:
        if line.startswith("- **"):
            inside = "paid_run.code_digest" in line
        if inside:
            out.extend(DIGEST.findall(line))
    return out


def _relative(path: Path, root: Path) -> str:
    try:
        return Path(path).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        raise AttestRefused(f"the findings file must be in this checkout, not {path}") from None


def _committed_refusal(relative: str, root: Path) -> Optional[str]:
    try:
        paid_run._git("ls-files", "--error-unmatch", "--", relative, root=root)
    except subprocess.CalledProcessError:
        return f"{relative} isn't committed; commit it first"
    if paid_run._git("status", "--porcelain", "--", relative, root=root).strip():
        return f"{relative} has uncommitted changes"
    return None


def _digest(root: Path) -> str:
    return paid_run.code_digest(paid_run.code_hashes(root))


def attest(findings: Path, *, root: Optional[Path] = None, path: Optional[Path] = None) -> dict[str, Any]:
    root = root or paid_run.REPO_ROOT
    relative = _relative(findings, root)
    reason = _committed_refusal(relative, root)
    if reason:
        raise AttestRefused(reason)
    dirty = paid_run.dirty_paths(root)
    if dirty:
        raise AttestRefused("commit or discard these changes before attesting: " + ", ".join(dirty[:5]))
    text = (root / relative).read_text(encoding="utf-8")
    digest = _digest(root)
    if digest not in _named_digests(_header(text)):
        raise AttestRefused(f"the review's header doesn't name this checkout's code_digest {digest}")
    row = {
        "attested_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "code_digest": digest,
        "commit": paid_run._git("rev-parse", "HEAD", root=root).strip(),
        "findings_path": relative,
        "findings_sha256": _sha(root / relative),
        "open_blocking": open_blocking(text),
    }
    target = log_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    torn = target.exists() and target.stat().st_size > 0 and not target.read_bytes().endswith(b"\n")
    with target.open("a", encoding="utf-8") as handle:
        # A row torn by a crash stays its own unreadable line, never the start of this one.
        handle.write(("\n" if torn else "") + json.dumps(row, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return row


def rows(path: Optional[Path] = None) -> list[dict[str, Any]]:
    target = log_path(path)
    if not target.exists():
        return []
    out = []
    for line in target.read_bytes().decode("utf-8", errors="replace").split("\n"):
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue  # a torn line is no attestation
    return out


def refusal(root: Optional[Path] = None, *, path: Optional[Path] = None) -> Optional[str]:
    """Why no attested lead-side review covers this checkout, or ``None`` when one does."""
    root = root or paid_run.REPO_ROOT
    try:
        return _refusal(root, path)
    except Exception as exc:  # any failure to check is a refusal, never an open gate
        return f"can't check the lead-side review attestations: {type(exc).__name__}: {exc}"


def _refusal(root: Path, path: Optional[Path]) -> Optional[str]:
    digest = _digest(root)
    attested = [row for row in rows(path) if isinstance(row, dict) and row.get("code_digest") == digest]
    usage = f"run python -m runner.lead_review attest docs/reviews/<file>.md for code_digest {digest}"
    if not attested:
        return f"no lead-side review is attested for this checkout; {usage}"
    # The newest attestation of this code governs: a later review that finds a blocking
    # defect closes the gate an earlier clean one opened (decision 0031 items 5 and 6).
    row = attested[-1]
    relative, count = row.get("findings_path"), row.get("open_blocking")
    if type(count) is not int or count != 0:
        return f"the newest attested review of this checkout, {relative}, has {count!r} open blocking findings; {usage}"
    if not isinstance(relative, str) or not relative or "\0" in relative:
        return f"the newest attestation names no usable findings file; {usage}"
    reason = _committed_refusal(relative, root)
    if reason:
        return f"the newest attested review isn't usable: {reason}; {usage}"
    if _sha(root / relative) != row.get("findings_sha256"):
        return f"the newest attested review, {relative}, changed after it was attested; {usage}"
    return None


def main(argv: Optional[list[str]] = None, *, root: Optional[Path] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    attest_parser = sub.add_parser("attest", help="attest a committed lead-side review for this checkout")
    attest_parser.add_argument("findings", type=Path)
    sub.add_parser("check", help="say whether an attested review covers this checkout")
    args = parser.parse_args(argv)
    if args.command == "attest":
        try:
            row = attest(args.findings, root=root)
        except AttestRefused as exc:
            print(f"refusing: {exc}", file=sys.stderr)
            return 1
        note = "" if row["open_blocking"] == 0 else "; paid calls stay refused until a review with 0 open blocking findings is attested"
        print(f"attested {row['findings_path']} for code_digest {row['code_digest']}{note}")
        return 0
    reason = refusal(root)
    print(reason or "an attested lead-side review covers this checkout")
    return 1 if reason else 0


if __name__ == "__main__":
    sys.exit(main())
