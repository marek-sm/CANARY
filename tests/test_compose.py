"""compose.yaml runs the CI docker job's container (stack-gaps item 5).

The CI job runs ``docker run --rm --network none --read-only --tmpfs ... canary:ci``.
``docker compose run --rm mock`` must apply the same flags to the same image command,
so it prints the same mock trace. The flag check always runs. The container check
runs when CANARY_DOCKER_IMAGE names an image built from this checkout's Dockerfile
(CI doesn't set it, so the test job builds nothing).
"""

import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def ci_docker_run() -> list[str]:
    """The CI docker job's ``docker run`` flags, between ``run`` and the image tag."""
    lines = [line for line in (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8").splitlines()
             if re.match(r"\s*- run: docker run ", line)]
    assert len(lines) == 1, lines
    words = shlex.split(lines[0].split("- run: ", 1)[1])
    assert words[:2] == ["docker", "run"] and words[-1] == "canary:ci"
    return words[2:-1]


def compose_service() -> dict[str, object]:
    """compose.yaml's one service, read without a YAML library (the lock has none)."""
    text = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    assert re.findall(r"^  (\w+):$", text, re.M) == ["mock"], "one service, mock"
    tmpfs = re.findall(r"^      - (\S+)$", text, re.M)
    scalars = dict(re.findall(r"^    (\w+): (\S+)$", text, re.M))
    return {**scalars, "tmpfs": tmpfs}


def test_compose_applies_exactly_the_ci_docker_job_s_flags():
    flags = ci_docker_run()
    expected = {"tmpfs": [flags[i + 1] for i, flag in enumerate(flags) if flag == "--tmpfs"]}
    assert "--rm" in flags and "--read-only" in flags
    assert flags[flags.index("--network") + 1] == "none"
    assert len(flags) == 1 + 2 + 1 + 2 * len(expected["tmpfs"])  # nothing else to carry over
    service = compose_service()
    assert service == {"build": ".", "network_mode": "none", "read_only": "true", **expected}
    assert "command" not in service and "entrypoint" not in service  # the image's CMD, as in CI


def test_the_readme_documents_the_one_compose_command():
    assert "docker compose run --rm mock" in (ROOT / "README.md").read_text(encoding="utf-8")


@pytest.mark.skipif(not os.environ.get("CANARY_DOCKER_IMAGE") or shutil.which("docker") is None,
                    reason="set CANARY_DOCKER_IMAGE to an image built from this checkout")
def test_compose_prints_the_ci_job_s_trace(tmp_path):
    image = os.environ["CANARY_DOCKER_IMAGE"]
    ci = subprocess.run(["docker", "run", *ci_docker_run(), image], capture_output=True, text=True, timeout=300)
    override = tmp_path / "compose.override.yaml"
    override.write_text(f"services:\n  mock:\n    image: {image}\n", encoding="utf-8")
    composed = subprocess.run(
        ["docker", "compose", "-f", str(ROOT / "compose.yaml"), "-f", str(override), "-p", "canary-compose-test",
         "run", "--rm", "-T", "mock"], cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert ci.returncode == 0 and composed.returncode == 0, (ci.stderr, composed.stderr)
    assert "CANARY  |  RECORDED TRACE" in ci.stdout
    assert composed.stdout == ci.stdout
