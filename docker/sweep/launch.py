"""Run one CANARY command in the sweep image with tools still sandboxed (prototype).

PROTOTYPE on branch cloud/container-sweep; see reports/cloud/container-sweep.md.
Nothing calls it, and decision 0025 item 12 keeps the official sweep on the host.

It runs the image with the smallest set of ``docker run`` options found to let
bwrap and tools/no_exec.py confine every tool, plus options that only tighten:

  loosen   --security-opt seccomp=docker/sweep/seccomp-bwrap.json
             Docker's default profile plus clone with all seven namespace flags,
             unshare of a user namespace alone, mount, umount2, and pivot_root.
  loosen   --security-opt systempaths=unconfined
             Docker no longer masks /proc paths (/proc/kcore, /proc/keys, ...) or
             makes /proc/sys, /proc/sysrq-trigger, ... read-only. The kernel
             refuses bwrap a fresh /proc while those masks sit on the container's.
  tighten  --user 10001:10001 --cap-drop ALL --security-opt no-new-privileges
           --read-only --tmpfs /tmp --pids-limit --network none

and binds the container to its image: it creates the container, asks the
daemon which image that container ID runs, writes both to
/run/canary/container.json (read-only), and only then starts it. Inside,
runner.container refuses the run if the file names another container.

The checkout is mounted read-only at /app and the results directory read-write
at /results. ``--writable-protocol`` mounts the checkout's protocol/ read-write
too, which ``python -m runner.paid_run record`` needs. ``--key-file`` mounts one
env file read-only at /run/secrets/provider.env for the outer runner's
``--env-file``; tool processes never see /run. ``--network bridge`` gives the
runner (not the tools) a network for a paid run; the default is none.

Usage:
  python docker/sweep/launch.py [--image REF] [--checkout DIR] --results DIR
      [--writable-protocol] [--key-file FILE] [--network none|bridge] -- COMMAND...
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SECCOMP = HERE / "seccomp-bwrap.json"
LAUNCHER_VERSION = "sweep-launch-proto-0.1.0"


def docker(*args: str, capture: bool = True) -> str:
    done = subprocess.run(["docker", *args], check=True, text=True,
                          stdout=subprocess.PIPE if capture else None)
    return (done.stdout or "").strip()


def run_options(*, checkout: Path, results: Path, run_dir: Path, writable_protocol: bool,
                key_file: Path | None, network: str) -> list[str]:
    options = [
        "--user", "10001:10001",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--security-opt", f"seccomp={SECCOMP}",
        "--security-opt", "systempaths=unconfined",
        "--read-only",
        "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=256m",
        "--pids-limit", "512",
        "--network", network,
        "--mount", f"type=bind,src={checkout},dst=/app,readonly",
        "--mount", f"type=bind,src={results},dst=/results",
        "--mount", f"type=bind,src={run_dir},dst=/run/canary,readonly",
    ]
    if writable_protocol:
        options += ["--mount", f"type=bind,src={checkout / 'protocol'},dst=/app/protocol"]
    if key_file is not None:
        options += ["--mount", f"type=bind,src={key_file},dst=/run/secrets/provider.env,readonly"]
    return options


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--image", default="canary-sweep:proto")
    parser.add_argument("--checkout", type=Path, default=REPO)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--writable-protocol", action="store_true")
    parser.add_argument("--key-file", type=Path)
    parser.add_argument("--network", choices=("none", "bridge"), default="none")
    parser.add_argument("command", nargs="+")
    args = parser.parse_args(argv)

    image_id = docker("image", "inspect", args.image, "--format", "{{.Id}}")
    with tempfile.TemporaryDirectory(prefix="canary-container-") as tmp:
        run_dir = Path(tmp)
        os.chmod(run_dir, 0o755)
        options = run_options(checkout=args.checkout.resolve(), results=args.results.resolve(), run_dir=run_dir,
                              writable_protocol=args.writable_protocol,
                              key_file=args.key_file.resolve() if args.key_file else None, network=args.network)
        # By ID, so a tag moved between inspect and create can't change the image.
        container_id = docker("create", *options, image_id, *args.command)
        try:
            running = docker("container", "inspect", container_id, "--format", "{{.Image}}")
            if running != image_id:
                print(f"refusing: container runs {running}, not {image_id}", file=sys.stderr)
                return 2
            record = {"container_id": container_id, "image_digest": running, "image_ref": args.image,
                      "launcher": LAUNCHER_VERSION}
            path = run_dir / "container.json"
            path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
            os.chmod(path, 0o644)
            print(json.dumps(record, sort_keys=True), file=sys.stderr)
            return subprocess.run(["docker", "start", "--attach", container_id]).returncode
        finally:
            subprocess.run(["docker", "rm", "--force", container_id], stdout=subprocess.DEVNULL, check=False)


if __name__ == "__main__":
    raise SystemExit(main())
