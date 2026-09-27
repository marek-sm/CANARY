"""CI stays no-credit: no workflow references a secret or a provider credential.

SPEC.md Section 4 and AGENTS.md forbid paid or credentialed model calls in CI.
Decision 0005 introduces a real provider key for local development, so this
check keeps that key out of every workflow.
"""

import re
from pathlib import Path

WORKFLOW_DIR = Path(__file__).resolve().parent.parent / ".github" / "workflows"
FORBIDDEN = re.compile(r"secrets\.|API_KEY|OPENAI|ANTHROPIC|GEMINI", re.IGNORECASE)


def workflow_files():
    return sorted(p for p in WORKFLOW_DIR.iterdir() if p.suffix in {".yml", ".yaml"})


def test_workflows_exist():
    assert workflow_files()


def test_no_workflow_references_a_credential():
    for path in workflow_files():
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            assert not FORBIDDEN.search(line), f"{path.name}:{lineno}: {line.strip()}"
