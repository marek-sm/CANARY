"""CI stays no-credit: no workflow references a secret or a provider credential.

SPEC.md Section 4 and AGENTS.md forbid paid or credentialed model calls in CI.
Decision 0005 introduces a real provider key for local development, so this
check keeps that key out of every workflow and local action under `.github/`.
"""

import re
from pathlib import Path

import pytest

GITHUB_DIR = Path(__file__).resolve().parent.parent / ".github"
# `secrets` as a word catches every way an expression can reach a secret:
# `secrets.NAME`, `secrets['NAME']`, `toJSON(secrets)`, and `secrets: inherit`.
FORBIDDEN = re.compile(r"\bsecrets\b|API_KEY|OPENAI|ANTHROPIC|GEMINI", re.IGNORECASE)


def workflow_files(root=GITHUB_DIR):
    return sorted(p for p in root.rglob("*") if p.suffix in {".yml", ".yaml"})


def test_workflows_exist():
    assert any(p.parent.name == "workflows" for p in workflow_files())


def test_local_actions_are_scanned_too(tmp_path):
    action = tmp_path / ".github" / "actions" / "setup" / "action.yml"
    action.parent.mkdir(parents=True)
    action.write_text("runs:\n  using: composite\n")
    assert action in workflow_files(tmp_path / ".github")


@pytest.mark.parametrize("line", [
    "  KEY: ${{ secrets.PROVIDER_TOKEN }}",
    "  ALL: ${{ toJSON(secrets) }}",
    "  KEY: ${{ secrets['PROVIDER_TOKEN'] }}",
    "  KEY: ${{ secrets[format('{0}_TOKEN', 'PROVIDER')] }}",
    "    secrets: inherit",
    "  OPENAI_BASE_URL: https://example.invalid",
])
def test_forbidden_pattern_catches_every_secret_reference(line):
    assert FORBIDDEN.search(line)


def test_no_workflow_references_a_credential():
    for path in workflow_files():
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            assert not FORBIDDEN.search(line), f"{path.name}:{lineno}: {line.strip()}"
