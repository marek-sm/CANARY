# Testing the pinned-container sweep on an Apple Silicon Mac

**Status: a prototype for a decision the project lead hasn't taken.** [Decision 0025](decisions/0025-full-study.md) item 12 still governs: the official sweep runs on the host under the tool sandbox, with a null `container_digest`. [Decision 0028](decisions/0028-restore-strength.md) item 9 lets a pinned container replace that only if sandbox tests, the full mock grid, kill and resume, and one `make live-smoke` all pass inside the image on the lead's arm64 Mac by the end of Sunday, November 8, and a record then says what it changes. Nothing in this file changes which path is official. The cloud evidence is in `reports/cloud/container-ready.md`.

## What the pieces are

| Piece | What it does |
|---|---|
| `Dockerfile.sweep` | The environment only: Python, the locked packages, bwrap, git, and make. The checkout is mounted in at `/app`, so `code_sha256` keeps covering the code |
| `make sweep-image` | Builds the image for this machine's platform, with no build attestation, so the image ID is reproducible |
| `docker/sweep/launch.sh` | Runs one command in the image with the measured option set. It asks the daemon which image the container runs and writes it to `/run/canary/container.json`, which becomes every result's `container_digest` |
| `docker/sweep/egress_proxy.py` | With `--network egress`, the runner's only route out: TLS to `api.anthropic.com:443`, nothing else. Tools have no network in either mode |
| `make sweep-container-check` | Decision 0028 item 9's checks except the smoke: preflight, sandbox tests, `tests/redteam/`, the egress probe, the full mock grid with verify, and a grid killed with SIGKILL part-way, resumed, and compared with the uninterrupted one |
| `protocol/paid_run_record.json` | Now states `container_digest`. `runner.paid_run` refuses a paid run in any other image, and a host record (null) refuses a run in any image |

## Before you start (once)

1. Docker Desktop for Mac, Apple Silicon build, running. In Settings:
   - **General → file sharing implementation:** VirtioFS (the default).
   - **Resources → File sharing:** the folder holding the checkout must be listed. `/Users` and `/var/folders` are by default. The launcher keeps its container file under `$TMPDIR`, which is in `/var/folders`.
   - **Enhanced Container Isolation:** off. It's an admin setting that swaps the runtime, and nothing here was tested with it.
   - **Resources:** at least 4 CPUs and 6 GB of memory.
2. `docker version --format '{{.Server.Arch}}'` prints `arm64`. If it prints `amd64`, Docker Desktop isn't the Apple Silicon build.
3. `unset DOCKER_DEFAULT_PLATFORM`. An amd64 image under Rosetta or QEMU proves nothing here, and the check refuses one.
4. A fresh clone outside your working checkout, so nothing of yours is mounted: `git clone https://github.com/marek-sm/CANARY ~/canary-container && cd ~/canary-container && git checkout <commit to test>`.

## The steps

1. **Build:** `make sweep-image`. This is the canonical path: Debian snapshot packages and the pinned ghcr.io uv. No cloud run has used it. Then write down the ID: `docker image inspect canary-sweep:local --format '{{.Id}}'`. It's the value every result will carry. An arm64 ID never equals an amd64 one.
2. **Optional reproducibility check:** `make sweep-image SWEEP_BUILD_ARGS=--no-cache`, then compare the ID. A different ID means something in the build isn't pinned. Say so before relying on the digest.
3. **The tripwire:** `make sweep-container-check`. It takes about 5 minutes on the cloud VM, and the Mac may differ. It stops at the first failing step, and the last line is `sweep-container-check: PASSED, image sha256:…`. Keep the whole output, because the preflight line shows the daemon, kernel, and security options.
   - Step 4 makes one TLS handshake to `api.anthropic.com`, then closes it. It sends no HTTP request and no key. `make sweep-container-check SWEEP_CHECK_ARGS=--no-handshake` skips it, but then the allowed path is unproven.
   - `SWEEP_CHECK_ARGS=--keep` keeps the scratch results under `results/development/sweep-container-check-*`.
4. **The key file can be read (no call):** put the key in a file outside the checkout holding exactly one `ANTHROPIC_API_KEY=` line, mode 600. Then run `sh docker/sweep/launch.sh --key-file ~/.config/canary/provider.env -- sh -c 'test -r /run/secrets/provider.env && echo readable'`. It prints only `readable`. Never pass the key with `-e`, because `docker inspect` would show it.
5. **The one live smoke (spends; only when you decide to; it takes the reserve from 13 to 12):**
   `sh docker/sweep/launch.sh --network egress --ledger ~/.canary --key-file ~/.config/canary/provider.env -- python -m runner.live_smoke --env-file /run/secrets/provider.env`
   - `--ledger ~/.canary` makes the image debit the same spend ledger as the host. Without it, the smoke finds no ledger and refuses.
   - The smoke runs `runner.paid_run`'s live-smoke checks inside the image: clean code, the lock, and the ledger. No cloud session ran this step.
6. **If the container path is chosen:** run the mock grid, `paid_run record`, and every paid command in the same image through `launch.sh`. Use `--writable-protocol` for `record`, then commit the record on the host.
   - A record made on the host (null digest, `macos-sandbox-exec`) never opens a run in the image, and a record made in the image never opens one on the host. Both the sandbox fingerprint and `container_digest` refuse it.

## If a step fails

Stop at the first failure and keep the output. A refusal is the design working, so never work around one by loosening an option for a real run.

| Step and message | Likely cause | What to do |
|---|---|---|
| 1, `docker isn't reachable` | Docker Desktop isn't running | Start it and wait for "Engine running" |
| 1, `the image is linux/amd64 but the daemon is linux/arm64` | Built under emulation, or `DOCKER_DEFAULT_PLATFORM` is set | Unset it and run `make sweep-image` again |
| 1, `uid 10001 can't write … or read the checkout` | File sharing doesn't cover the checkout, or ownership blocks uid 10001 | Check Resources → File sharing and VirtioFS. If it still fails, run `chmod -R a+rwX results/development` on this scratch clone only and retry. Report which fixed it |
| 1, `git … dubious ownership`, or a null `code_commit` later | The image's `safe.directory` didn't apply | Report it. Don't add a global git exception on the host |
| 2, `Can't mount proc on /newroot/proc` | `systempaths=unconfined` didn't take effect | Check that `docker info` lists seccomp, and that Enhanced Container Isolation is off. Report the output |
| 2, `No permissions to create new namespace`, `setting up uid map`, or `Operation not permitted` from bwrap | The kernel or a profile refuses an unprivileged user namespace or mount | For diagnosis only, rerun step 2 with `seccomp=unconfined` by hand. If that passes, the custom profile needs a rule this kernel wants; report which. Never run a grid that way |
| 2 or 3, any other test failure | A real difference between the image and the sandbox's assumptions | Send the failing test's output. Don't rerun until it passes |
| 4, `FAIL runner: verified TLS handshake` with `SSLCertVerificationError` | Something between the Mac and Anthropic intercepts TLS (a VPN, or a corporate proxy). The cloud VM had this | Disconnect the VPN and retry. A paid call would fail the same way |
| 4, `FAIL` on any line that should be refused | The runner or a tool reached something it mustn't | Stop. That's a safety finding, not a flake |
| 5, `the full mock grid didn't run and verify` | A grid or verify error | Read the verify output, then run `make grid-check` on the host for comparison |
| 6, `ended before 30 trials` or `finished before the kill` | The machine is faster or slower than expected | Rerun with `SWEEP_CHECK_ARGS='--kill-after 10'` |
| 6, `found something the uninterrupted one didn't` | Resume isn't exact in the image | Keep the results (`--keep`) and send `outcomes.jsonl`. This fails the tripwire |

## What the container adds and loosens

- **It adds a boundary around the outer runner, the process that holds the key.** The runner runs as uid 10001 with no capabilities, a read-only image and checkout, and writes only to results and `/tmp`. Its network is none, or `api.anthropic.com:443` only. On the host it has your whole account.
- **It loosens two things, and both apply to every process in the container, the runner included:**
  - A seccomp profile that adds user-namespace `clone` and `unshare`, plus `mount`, `umount2`, and `pivot_root`.
  - `systempaths=unconfined`, which unmasks read-only `/proc` information such as `/proc/timer_list` for the runner.
  - The tools' own boundary is bwrap plus `no_exec`, as on any Linux host.
- **`sandbox-exec` on the Mac has never been red-teamed.** `tests/redteam/` was written against bwrap (`tests/redteam/conftest.py`). No CI job runs it on macOS, and no record shows it run against `sandbox-exec`. In the image, it runs against bwrap. Two of its tests apply only to x86_64, so they skip on arm64.

The report has the full comparison and what was and wasn't measured.
