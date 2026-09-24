import json
from pathlib import Path

from analysis.report_shells import DEFAULT_MANIFEST, DEFAULT_OUTPUT, STATUS, load_manifest, render_manifest


ROOT = Path(__file__).resolve().parents[1]
OUTLINE = ROOT / "paper" / "outline.md"

REQUIRED_ESTIMANDS = {
    "ModelViolationRate",
    "SystemCompromiseRate",
    "CleanUtility",
    "DatamarkingAttackRiskDifference",
    "DatamarkingInjectionSpecificDifference",
    "CleanUtilityCost",
    "PolicyGateResidualSystemRiskDifference",
    "AuthorizedHighRiskCleanUtility",
    "PolicyGateUnauthorizedBlockRate",
    "PolicyGateEnforcementEscapeRate",
    "PolicyGateAuthorizedDispatchRate",
    "BackgroundModelViolationRate",
    "BackgroundSystemCompromiseRate",
    "InjectionExcessRisk",
    "AttackTaskCompletion",
    "SecureTaskCompletion",
}


def test_outline_has_section_14_hierarchy_and_owner_map():
    outline = OUTLINE.read_text(encoding="utf-8")
    headings = [line for line in outline.splitlines() if line.startswith("## ")]

    assert headings[:11] == [
        "## Technical-input owner map",
        "## 1. Abstract",
        "## 2. Introduction and scoped contribution",
        "## 3. Related work and explicit overlap",
        "## 4. Threat model and real-world safety boundary",
        "## 5. Corpus selection, adaptation, rejection ledger, and crossed adapters",
        "## 6. Agent, deterministic tasks/oracles, and defenses",
        "## 7. Frozen protocol and analysis plan",
        "## 8. Results or engineering-validation evidence",
        "## 9. Limitations, ethics, and release safety",
        "## 10. Reproducibility and contribution statement",
    ]
    for owner in ("Project lead", "T1", "T2", "T3", "T4", "T5"):
        assert owner in outline
    assert "Pre-results structure only" in outline


def test_manifest_covers_every_named_estimand():
    manifest = load_manifest()
    ids = {entry["id"] for entry in manifest["estimands"]}
    assert REQUIRED_ESTIMANDS <= ids


def test_every_shell_has_caption_alt_text_and_table_equivalent():
    manifest = load_manifest()
    for entry in manifest["estimands"]:
        assert entry["caption"].strip()
        assert entry["alt_text"].strip()
        assert len(entry["columns"]) >= 2


def test_generated_shell_is_current_and_contains_no_result_values():
    manifest = load_manifest()
    rendered = render_manifest(manifest)

    assert DEFAULT_OUTPUT.read_text(encoding="utf-8") == rendered
    assert rendered.count("**Figure shell:**") == len(manifest["estimands"])
    assert rendered.count("#### Table equivalent") == len(manifest["estimands"])
    assert rendered.count(f"**Status:** {STATUS}") == len(manifest["estimands"])
    assert "PRE-RESULTS — NO DATA" in rendered

    parsed = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    assert parsed["status"] == "pre_results_no_data"
