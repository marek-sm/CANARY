"""Decision 0044: the methods checkpoint in docs/commitments.md is pinned and reachable."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMITMENTS = ROOT / "docs" / "commitments.md"
DECISION = ROOT / "docs" / "decisions" / "0044-binding-methods-checkpoint.md"
BEGIN = "<!-- checkpoint:begin -->"
END = "<!-- checkpoint:end -->"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _section(text: str) -> str:
    assert text.count(BEGIN) == 1 and text.count(END) == 1
    start = text.index(BEGIN) + len(BEGIN)
    return text[start : text.index(END)].strip("\n")


def _pinned_hash() -> str:
    match = re.search(r"Checkpoint section SHA-256: `([0-9a-f]{64})`", _text(DECISION))
    assert match, "decision 0044 must state the checkpoint section's SHA-256"
    return match.group(1)


def _block(text: str, heading: str) -> str:
    start = text.index(heading)
    nxt = text.find("\n## ", start + len(heading))
    return text[start : nxt if nxt != -1 else len(text)]


def test_checkpoint_section_matches_the_hash_decision_0044_pins():
    section = _section(_text(COMMITMENTS))
    assert hashlib.sha256(section.encode("utf-8")).hexdigest() == _pinned_hash()


def test_a_one_character_edit_fails_the_pin():
    section = _section(_text(COMMITMENTS))
    edited = section.replace("1,092", "1,093", 1)
    assert edited != section
    assert hashlib.sha256(edited.encode("utf-8")).hexdigest() != _pinned_hash()


def test_every_dated_status_quote_is_in_the_checkpoint():
    text = _text(COMMITMENTS)
    section = _section(text)
    block = _block(text, "## Dated status as of November 21")
    quotes = re.findall(r'^\s*- "(.+)"$', block, re.M)
    rows = re.findall(r"^\s*- `(\|.+\|)`$", block, re.M)
    assert len(quotes) >= 14 and len(rows) == 11
    for quote in quotes + rows:
        assert quote in section, quote


def test_the_corrections_log_exists():
    text = _text(COMMITMENTS)
    assert "## Corrections sent to the mentor" in text
    assert text.index("## Corrections sent to the mentor") < text.index(BEGIN)


def test_contributors_and_tools_are_routed_to_the_file():
    agents = _text(ROOT / "AGENTS.md")
    steps = _block(agents, "## Start every slice")
    assert re.search(r"^1\. Read \[`docs/commitments\.md`\]\(docs/commitments\.md\)", steps, re.M)
    assert "(docs/commitments.md)" in _text(ROOT / "CONTRIBUTING.md")
    assert "(docs/commitments.md)" in _text(ROOT / "TASKS.md")
    assert "| [`docs/commitments.md`](docs/commitments.md) |" in _text(ROOT / "README.md")
    assert "0044-binding-methods-checkpoint.md" in _text(ROOT / "README.md")
    spec_17 = _block(_text(ROOT / "SPEC.md"), "## 17. Repository structure and steering documents")
    assert "| `docs/commitments.md` |" in spec_17
