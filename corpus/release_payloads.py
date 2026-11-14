"""Release-safe payload list (W8-T2, docs/DATA_RELEASE.md "Payload and source release").

    python -m corpus.release_payloads          # write corpus/release/payloads.json
    python -m corpus.release_payloads --check  # fail if the committed file is stale

One entry per considered case: the development bases, C1 controls, demo case, and
every W7-T2 candidate, kept or rejected. Each carries its source pointer, license
decision, and the payload text the public release may carry.

All four sources are MIT, so payload text may be redistributed. Adapted payloads
only hold `@fixture.test` addresses and are released in full. Originals keep
their wording, but every email address outside `fixture.test` becomes a stable
placeholder, since DATA_RELEASE.md treats contact identifiers as removable and
the benchmarks' addresses sit on real domains. The original's SHA-256 and source
locator stay, so anyone can check the withheld text against the pinned source.

This reads only corpus records; it never touches a trial or a result. W9-T3's
sanitizer reads this file before the sweep (TASKS.md W8-T2, decision 0011).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "corpus" / "release" / "payloads.json"
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
SYNTHETIC_DOMAIN = "@fixture.test"
REDISTRIBUTABLE = ("MIT",)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def withhold_addresses(text: str) -> tuple[str, list[str]]:
    """Replace every non-fixture email with `[address withheld <sha8>]`."""
    withheld: list[str] = []

    def swap(match: re.Match) -> str:
        address = match.group(0)
        if address.lower().endswith(SYNTHETIC_DOMAIN):
            return address
        withheld.append(address)
        return f"[address withheld {_sha(address.lower())[:8]}]"

    return EMAIL.sub(swap, text), withheld


def _reserved() -> list[dict]:
    out = []
    for pattern in ("development/dev-*.json", "c1/*.json", "demo/*.json"):
        for path in sorted((ROOT / "corpus").glob(pattern)):
            rec = json.loads(path.read_text(encoding="utf-8"))
            attack = rec["attack"]
            out.append({
                "case_id": rec["base_case_id"],
                "candidate_id": rec["candidate_id"],
                "split": rec["split"],
                "status": rec["split"],
                "source": rec["source"],
                "original_payload": attack["original_payload"],
                "original_payload_sha256": attack["original_payload_sha256"],
                "adapted_payload": attack["adapted_payload"],
                "adaptation_notes": attack["adaptation_notes"],
                "rejection_reason": None,
            })
    return out


def _candidates() -> list[dict]:
    out = []
    for path in sorted((ROOT / "corpus" / "evaluation" / "candidates").glob("*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        out.append({
            "case_id": rec["candidate_id"],
            "candidate_id": rec["candidate_id"],
            "split": "evaluation_candidate",
            "status": rec["status"],
            "source": rec["source"],
            "original_payload": rec["original_payload"],
            "original_payload_sha256": rec["original_payload_sha256"],
            "adapted_payload": rec["adapted_payload"],
            "adaptation_notes": rec["adaptation_notes"],
            "rejection_reason": rec["rejection_reason"],
        })
    return out


def build() -> dict:
    entries = []
    for item in _reserved() + _candidates():
        src = item["source"]
        if not src["license"].startswith(REDISTRIBUTABLE):
            raise ValueError(f"{item['case_id']}: license {src['license']!r} isn't on the redistributable list")
        if _sha(item["original_payload"]) != item["original_payload_sha256"]:
            raise ValueError(f"{item['case_id']}: original payload hash doesn't match")
        original, withheld = withhold_addresses(item["original_payload"])
        adapted = item["adapted_payload"]
        if adapted is not None and withhold_addresses(adapted)[1]:
            raise ValueError(f"{item['case_id']}: adapted payload holds a non-fixture address")
        entries.append({
            "case_id": item["case_id"],
            "candidate_id": item["candidate_id"],
            "split": item["split"],
            "status": item["status"],
            "citation_key": src["citation_key"],
            "url": src["url"],
            "source_version": src["source_version"],
            "source_case_id": src["source_case_id"],
            "source_locator": src.get("source_locator"),
            "license": src["license"],
            "redistribution": "permitted",
            "original_payload_sha256": item["original_payload_sha256"],
            "original_payload_release": "contact addresses withheld" if withheld else "full",
            "original_payload_public": original,
            "adapted_payload_public": adapted,
            "adaptation_notes": item["adaptation_notes"],
            "rejection_reason": item["rejection_reason"],
        })
    return {
        "policy": "docs/DATA_RELEASE.md, 'Payload and source release'; TASKS.md W8-T2",
        "address_placeholder": "[address withheld <first 8 hex of SHA-256 of the lowercased address>]",
        "entries": entries,
    }


def render() -> str:
    return json.dumps(build(), indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write or check the release-safe payload list.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    text = render()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"{OUT.relative_to(ROOT)} is missing or stale; run python -m corpus.release_payloads", file=sys.stderr)
            return 1
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
