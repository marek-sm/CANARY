# Mutation testing of the number-producing and safety-enforcing code

Status: **in progress** (early push; this file is rewritten at each milestone).

Base commit: `origin/main` at `3b165bfc7036a97804583cd22b5d2ea758ce1b3b`. Branch: `cloud/mutation`.

This is evidence for the project lead to decide on. It is an AI-run report and is not the human review `SPEC.md` requires.

## Environment set-up (as run)

- Ubuntu 24.04.5 LTS, x86_64, running as root. `apt-get install -y bubblewrap` installed bubblewrap 0.9.0.
- `sysctl -w kernel.apparmor_restrict_unprivileged_userns=0` failed: `/proc/sys/kernel/apparmor_restrict_unprivileged_userns` does not exist on this kernel (no AppArmor). Unprivileged user namespaces worked without it: `bwrap --ro-bind / / --unshare-all true` succeeded as the non-root user.
- Non-root user `canary` (`useradd -m canary`). The repository was copied (without `.git`) to `/home/canary/work/CANARY` and owned by `canary`.
- Every test and mutation command ran through `runuser -u canary -- env -i HOME=/home/canary PATH=... LANG=C.UTF-8 UV_NO_SYNC=1 UV_OFFLINE=1 ...`, so no credential, proxy, or provider variable reached the tests. `uv sync` was the only step given the proxy and CA file.
- Python 3.11.18 from `uv` (the repo pins `>=3.11,<3.12`).

## Baseline

`uv run pytest -q -x -p no:cacheprovider` as `canary`: **1860 passed in 232.06s**.
