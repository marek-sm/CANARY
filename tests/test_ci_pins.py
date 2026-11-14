"""Every GitHub Action CI uses is pinned by commit SHA, with its version as a comment (stack-gaps item 7).

A tag such as ``actions/checkout@v4`` can be moved to other code; a 40-hex SHA can't.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_every_action_is_pinned_by_sha():
    uses = re.findall(r"^\s*-?\s*uses:\s*(\S+)(.*)$", (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"), re.M)
    assert uses
    for action, comment in uses:
        assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", action), action
        assert re.fullmatch(r"\s*# v\d+(\.\d+)*", comment), (action, comment)
