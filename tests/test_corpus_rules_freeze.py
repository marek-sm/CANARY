import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "SPEC.md"

START = "### Corpus composition\n"
END = "### Crossed indirect-delivery design\n"

# Frozen at Gate 1 by decision 0007 and re-pinned by decision 0014
# (DEV-0001). Changing the rules text needs SPEC.md Section 11 change
# control, then a deliberate update of this value.
FROZEN_SHA256 = "31e63055a31dfe3ab702d04482695dfe9aa49644927830d2c2c5ad6dc60afa87"


def frozen_rules_text():
    text = SPEC.read_text(encoding="utf-8")
    return text[text.index(START):text.index(END)]


def test_corpus_rules_match_the_gate1_freeze():
    digest = hashlib.sha256(frozen_rules_text().encode("utf-8")).hexdigest()
    assert digest == FROZEN_SHA256


def test_frozen_text_defines_near_duplicates():
    assert "near-identical when their deduplication keys are equal" in frozen_rules_text()


def test_frozen_text_defines_selection_for_a_short_pool():
    text = frozen_rules_text()
    assert "The script builds the largest size `P` for which a feasible vector exists" in text
    assert "breaking any tie by `candidate_id`" in text
    assert "SHA256(\"CANARY-2026-task|\" + template_id)" in text
    assert "SHA256(\"CANARY-2026-recheck|\" + pool_hash + \"|\" + candidate_id)" in text
