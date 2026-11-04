"""Write docker/sweep/seccomp-bwrap.json from Docker's default seccomp profile (prototype).

Docker's default profile lets an unprivileged container create no namespace and
mount nothing, so bwrap can't start. This keeps every default rule and adds only
what bwrap needs to build the tool sandbox, as measured on the branch
cloud/container-sweep (reports/cloud/container-sweep.md):

* ``clone`` when its flags ask for all seven namespaces at once (what
  ``bwrap --unshare-all`` asks for). A clone with no namespace flag is already
  allowed by the default; any other mix stays denied.
* ``unshare`` when its flags ask for a user namespace and no other namespace.
  bwrap 0.9.0 makes this call when it mounts ``/proc`` for the tool; denying it
  fails the launch with "unshare user ns: Operation not permitted".
* ``mount``, ``umount2``, and ``pivot_root``, which bwrap uses inside the new
  user and mount namespace it just created.

Everything else stays denied, including any other ``unshare``, ``setns``, ``clone3`` with
namespaces, the new mount API (``fsopen``, ``open_tree``, ``move_mount``, ...),
and ``chroot``.

Usage:
  python docker/sweep/make_seccomp.py DOCKER_DEFAULT_JSON [--out PATH]

DOCKER_DEFAULT_JSON is moby's profiles/seccomp/default.json; the report names
the copy and SHA-256 used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

# <linux/sched.h>
CLONE_NEWNS, CLONE_NEWCGROUP, CLONE_NEWUTS, CLONE_NEWIPC = 0x00020000, 0x02000000, 0x04000000, 0x08000000
CLONE_NEWUSER, CLONE_NEWPID, CLONE_NEWNET = 0x10000000, 0x20000000, 0x40000000
ALL_NAMESPACES = (CLONE_NEWNS | CLONE_NEWCGROUP | CLONE_NEWUTS | CLONE_NEWIPC
                  | CLONE_NEWUSER | CLONE_NEWPID | CLONE_NEWNET)

BWRAP_RULES = [
    {
        "names": ["clone"],
        "action": "SCMP_ACT_ALLOW",
        "args": [{"index": 0, "value": ALL_NAMESPACES, "valueTwo": ALL_NAMESPACES, "op": "SCMP_CMP_MASKED_EQ"}],
        "comment": "bwrap --unshare-all: all seven namespaces in one clone (x86_64/aarch64 argument order)",
        "excludes": {"arches": ["s390", "s390x"]},
    },
    {
        "names": ["unshare"],
        "action": "SCMP_ACT_ALLOW",
        "args": [{"index": 0, "value": ALL_NAMESPACES, "valueTwo": CLONE_NEWUSER, "op": "SCMP_CMP_MASKED_EQ"}],
        "comment": "bwrap 0.9.0 unshares one more user namespace when it mounts /proc",
    },
    {
        "names": ["mount", "umount2", "pivot_root"],
        "action": "SCMP_ACT_ALLOW",
        "comment": "bwrap builds the sandbox's mount tree inside its own user and mount namespace",
    },
]


def build(default: dict) -> dict:
    profile = json.loads(json.dumps(default))
    profile["syscalls"] = [*profile["syscalls"], *BWRAP_RULES]
    return profile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("default", type=Path)
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("seccomp-bwrap.json"))
    args = parser.parse_args()
    raw = args.default.read_bytes()
    profile = build(json.loads(raw))
    args.out.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    print(f"default sha256 {hashlib.sha256(raw).hexdigest()}")
    print(f"wrote {args.out} sha256 {hashlib.sha256(args.out.read_bytes()).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
