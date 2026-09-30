import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "SPEC.md"

START = "### Corpus composition\n"
END = "### Crossed indirect-delivery design\n"

# Frozen at Gate 1 by decision 0007. Changing the rules text needs SPEC.md
# Section 11 change control, then a deliberate update of this value.
FROZEN_SHA256 = "ed11c65c87bd0f0ab4f7fc2e0bc3652fd3061eb1967f56ab569509fa6afc48b0"


def frozen_rules_text():
    text = SPEC.read_text(encoding="utf-8")
    return text[text.index(START):text.index(END)]


def test_corpus_rules_match_the_gate1_freeze():
    digest = hashlib.sha256(frozen_rules_text().encode("utf-8")).hexdigest()
    assert digest == FROZEN_SHA256


def test_frozen_text_defines_near_duplicates():
    assert "near-identical when their deduplication keys are equal" in frozen_rules_text()
