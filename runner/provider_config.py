"""Optional outer-runner credential boundary; never imported by mock execution.

Only the explicitly named live command (``runner.live_smoke``) calls it.
Callers must keep the returned value in the outer runner and never pass it into
a child process or a record.
"""
from pathlib import Path


def load_api_key(path: Path, variable: str) -> str:
    """Explicit-only minimal env-file reader, with no shell expansion or env mutation.
    The file holds exactly one ``variable=`` line (decision 0010)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) != 1 or not lines[0].startswith(variable + "="):
        raise ValueError("expected one provider-key assignment")
    return lines[0].partition("=")[2]
