"""The image a sweep container runs, as the Docker daemon reported it (prototype).

PROTOTYPE on branch cloud/container-sweep, for a decision the project lead hasn't
made (reports/cloud/container-sweep.md). Decision 0025 item 12 keeps the
official sweep on the host, where this returns ``None`` and records keep a null
``container_digest``.

A container can't measure its own image digest, and a digest passed in by hand
could name any image. So ``docker/sweep/launch.py`` creates the container, asks
the daemon which image that container ID runs (``docker container inspect``),
and writes both into ``/run/canary/container.json`` before the container
starts, on a read-only mount. Here the runner checks that the file names *this*
container: the ID must equal the one the kernel shows in this process's mount
table (Docker mounts ``/etc/hostname`` from the container's own directory), so
a file made for another container, or typed by hand, refuses the run rather
than labelling it.

* No file: ``None``, which is unknown, never a claim (host runs, or a container
  started without the launcher).
* A file that doesn't validate or names another container: ``ContainerMismatch``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

PROVENANCE = Path("/run/canary/container.json")
MOUNTINFO = Path("/proc/self/mountinfo")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_ID = re.compile(r"^[0-9a-f]{64}$")
# Docker's own bind of the container's hostname file, e.g.
# /var/lib/docker/containers/<64 hex>/hostname /etc/hostname
_HOSTNAME_MOUNT = re.compile(r"/containers/([0-9a-f]{64})/hostname$")


class ContainerMismatch(RuntimeError):
    """The container provenance file doesn't describe this container."""


def kernel_container_id(mountinfo: Path = MOUNTINFO) -> Optional[str]:
    """The container ID in the source of this mount namespace's ``/etc/hostname``."""
    try:
        lines = mountinfo.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        fields = line.split(" ")
        if len(fields) > 4 and fields[4] == "/etc/hostname":
            match = _HOSTNAME_MOUNT.search(fields[3])
            if match:
                return match.group(1)
    return None


def container_digest(path: Path = PROVENANCE, mountinfo: Path = MOUNTINFO) -> Optional[str]:
    """The daemon-reported image digest of this container, or ``None`` when no
    launcher recorded one."""
    if not path.exists():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ContainerMismatch(f"{path} doesn't parse: {exc}") from exc
    image, container_id = record.get("image_digest"), record.get("container_id")
    if not isinstance(image, str) or not _DIGEST.match(image):
        raise ContainerMismatch(f"{path} has no sha256 image_digest")
    if not isinstance(container_id, str) or not _ID.match(container_id):
        raise ContainerMismatch(f"{path} has no 64-hex container_id")
    running = kernel_container_id(mountinfo)
    if running != container_id:
        raise ContainerMismatch(f"{path} was written for container {container_id[:12]}, "
                                f"not this one ({(running or 'unknown')[:12]})")
    return image
