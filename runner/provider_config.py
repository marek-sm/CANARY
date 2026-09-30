"""Optional outer-runner credential boundary; never imported by mock execution.

No adapter or model call is implemented. Callers must keep the returned value
in the outer runner and never pass it into a child process or a record.
"""
from pathlib import Path


def load_api_key(path: Path) -> str:
    """Explicit-only minimal env-file reader, with no shell expansion or env mutation."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) != 1 or not lines[0].startswith("OPENAI_API_KEY="):
        raise ValueError("expected one provider-key assignment")
    return lines[0].partition("=")[2]
