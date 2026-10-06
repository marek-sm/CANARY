"""Render dev bases that carry a `fixture.wrapper` into C2/C3/C4 fixtures.

    python -m corpus.render_fixtures          # write fixtures + hash manifests
    python -m corpus.render_fixtures --check  # fail if anything on disk drifted

dev-001 predates wrappers and keeps its v1 renders, so it's skipped here.
Every render is parsed back before it's written; a base whose parser doesn't
recover the exact substituted content fails loudly instead of being written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from pathlib import Path

from channels.render import (
    INSERTION_MARKER,
    RECORD_EXTRACTOR_VERSIONS,
    RECORD_RENDERERS,
    substitute,
)

ROOT = Path(__file__).resolve().parents[1]
DEV_DIR = ROOT / "corpus" / "development"
EXTENSIONS = {"C2": "json", "C3": "txt", "C4": "html"}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def wrapped_records() -> list[dict]:
    records = []
    for path in sorted(DEV_DIR.glob("dev-*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if "wrapper" in record["fixture"]:
            records.append(record)
    return records


def expected_files(record: dict) -> dict[Path, str]:
    """Every file this record's fixtures should contain, path -> exact text."""
    base = record["base_case_id"]
    fixture = record["fixture"]
    wrapper = fixture["wrapper"]
    payload = record["attack"]["canonical_payload"]
    clean = fixture["clean_replacement"]

    if unicodedata.normalize("NFC", payload) != payload:
        raise ValueError(f"{base}: canonical_payload is not NFC-normalized")
    if INSERTION_MARKER in payload or INSERTION_MARKER in clean:
        raise ValueError(f"{base}: slot marker inside payload or clean text")

    template_path = ROOT / fixture["template_path"]
    template = template_path.read_text(encoding="utf-8")
    files: dict[Path, str] = {}
    manifest = {}
    for channel, (render, parse) in RECORD_RENDERERS.items():
        if record["channels"][channel]["payload_extractor_version"] != RECORD_EXTRACTOR_VERSIONS[channel]:
            raise ValueError(f"{base}: {channel} extractor version mismatch")
        for condition, value in (("attack", payload), ("clean", clean)):
            content = substitute(template, value)
            rendered = render(content, wrapper)
            if parse(rendered, wrapper) != content:
                raise ValueError(f"{base}: {channel} {condition} doesn't round-trip")
            key = f"{channel.lower()}_{condition}"
            rel = f"fixtures/{base}/rendered/{key}.{EXTENSIONS[channel]}"
            files[ROOT / rel] = rendered
            manifest[key] = {"path": rel, "sha256": sha256_text(rendered)}

    manifest["canonical_payload_sha256"] = sha256_text(payload)
    manifest["clean_replacement_sha256"] = sha256_text(clean)
    manifest["template_sha256"] = sha256_text(template)
    manifest_path = ROOT / fixture["rendered_hash_manifest"]
    files[manifest_path] = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    return files


def check_record_hashes(record: dict) -> list[str]:
    base = record["base_case_id"]
    fixture, attack = record["fixture"], record["attack"]
    template = (ROOT / fixture["template_path"]).read_text(encoding="utf-8")
    pairs = [
        ("fixture.template_sha256", template, fixture["template_sha256"]),
        ("fixture.clean_replacement_sha256", fixture["clean_replacement"], fixture["clean_replacement_sha256"]),
        ("attack.canonical_payload_sha256", attack["canonical_payload"], attack["canonical_payload_sha256"]),
        ("attack.original_payload_sha256", attack["original_payload"], attack["original_payload_sha256"]),
    ]
    return [
        f"{base}: {name} doesn't match"
        for name, text, recorded in pairs
        if sha256_text(text) != recorded
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    problems = []
    for record in wrapped_records():
        problems += check_record_hashes(record)
        for path, text in expected_files(record).items():
            if args.check:
                if not path.exists() or path.read_text(encoding="utf-8") != text:
                    problems.append(f"{path.relative_to(ROOT)} is missing or stale")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")

    for line in problems:
        print(line, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
