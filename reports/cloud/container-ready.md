# Is the pinned-container sweep ready to test on the lead's Mac?

- Branch `cloud/container-ready`, from `main` at `5f3a52d` (decision 0028). Cloud VM: Ubuntu 24.04.5, x86_64, kernel 6.18.44-fc-v233, Docker 29.9.2 (containerd store, runc, cgroup v1, builtin seccomp, no AppArmor). Date 2026-11-04.
- A **prototype for a decision the lead hasn't made.** Decision 0025 item 12 still governs, and nothing here changes `SPEC.md`, decisions, `TASKS.md`, `STATUS.md`, locked schemas, or hash pins.
- No provider call was made and no key was used. `#73`'s branch and `corpus/evaluation/` were not read. An AI session wrote and ran this, which is no substitute for the human review `SPEC.md` requires.
- Host commands ran as non-root `sweeper` (uid 1500) in a clean environment with `bubblewrap` 0.9.0. Containers ran as uid 10001. The `docker` client ran as root, because only root could reach the daemon here. No tool ever ran as root.

## Answer

**Yes for linux/amd64. For the Mac it's untested but ready to try.**
- `make sweep-container-check` passes in the image here: sandbox tests, `tests/redteam/`, an egress probe, the full mock grid, and kill-and-resume.
- The gate now refuses a run in any image other than the record's.
- The runner's network is `api.anthropic.com:443` only.
- `docs/SWEEP_CONTAINER.md` has the Mac steps and what to do when a step fails.

What can't be made to work, or isn't proven:
- **arm64 isn't proven by anything here.** Under QEMU the image builds and runs, but bwrap can't create namespaces (item 3). The GitHub arm64 job is written but hasn't run yet.
- **A verified TLS handshake to Anthropic can't be shown from this VM.** Its egress gateway re-signs TLS ("Egress Gateway SDS Issuing CA"), so the strict check fails here by design (item 2).
- **The canonical build (Debian snapshot, ghcr.io uv) still couldn't be built here.** Docker Hub returned 429 and `snapshot.debian.org` didn't resolve. I didn't retry ghcr.io blobs. Every image below is the Ubuntu-tools, PyPI-uv variant on `mirror.gcr.io` bases at the pinned digests, so the Mac's digest will differ.

## 1. The gate sees the image

- `schemas/paid_run_record.schema.json:115`: required `container_digest`, a string `^sha256:[0-9a-f]{64}$` or null. The schema is now 1.2.0.
- `runner/paid_run.py:660`: the record states it.
- `runner/paid_run.py:443`/`:478`: the gate refuses when this process's image isn't the record's, and the host's null counts as an image.
- `runner/paid_run.py:490`/`:545`: the record refuses a grid whose provenance lines or results name another image.
- `runner/execute.py:712`: `trial_started` carries the digest only when a launcher file exists, so host traces don't change.
- `runner/mock_slice.py:359`: results take the digest from that event, so a host `verify` recomputes the same value.
- `runner/execute.py:1803`: a file written for another container refuses before the run directory exists.
- The value comes from `docker/sweep/launch.sh:158`–`:159`. The launcher creates the container by image ID, asks the daemon which image it runs, and writes `/run/canary/container.json` read-only. `runner/container.py` checks that the file names this container.
- **Tests first:** 9 new tests in `tests/test_container_provenance.py` failed before the change, then passed. The file now holds 21 tests.
- **End to end, in a committed scratch clone:**
  - grid verify `complete: true`, 90 trials;
  - `paid_run record` (1.2.0, `sha256:21cefa64…`, sandbox `…7b60c4fb0074ea5a`);
  - host commit, then `check` in that image: "paid runs may start here";
  - in a label-only variant `sha256:b2621f13…`: "this runs in image sha256:b2621f13…, not the record's sha256:21cefa64…";
  - plain `docker run` with no launcher file: refused, "none … not the record's";
  - on the host: refused first by the sandbox fingerprint (`…934ef034…` vs `…7b60c4fb…`).

## 2. The runner's network

- `docker/sweep/launch.sh:115`–`:128`, `--network egress`: the runner joins an `--internal` network whose only peer is `docker/sweep/egress_proxy.py`, in the same image as uid 10001 with no capabilities. `api.anthropic.com` resolves to the proxy, and DNS goes to a dead address.
- The proxy reads the ClientHello and forwards only server name `api.anthropic.com`. Its upstream is the constant `api.anthropic.com:443` (`egress_proxy.py:31`–`:32`, `:151`). TLS stays end to end. `agent/anthropic_adapter.py` (`trust_env=False`) is unchanged.
- **Failing first:** the probe under the prototype's `--network bridge` gave **6 of 20 checks failed**. The runner connected to `1.1.1.1:443` and `203.0.113.10:80`, resolved `pypi.org`, and plain HTTP was answered.
- **Under `--network egress` on image `ecf0c188…`, with `--no-handshake`: 20 of 20 pass.**
  - Runner: TLS naming `example.com` or no name gets `SSLEOFError` from the proxy. Plain HTTP is closed. Port 80 is refused. TCP to `1.1.1.1:443`, `8.8.8.8:53`, and `203.0.113.10:80` gets `ENETUNREACH`. DNS for `example.com`, `pypi.org`, and `api.openai.com` fails.
  - A tool launched through `sandbox.wrap` sees only `lo`. All four TCP targets, the proxy included, get errno 101, and all four names fail to resolve.
- With the handshake on, 21 checks with 1 failed: `answered:SSLCertVerificationError`, the VM's interception described above. On the Mac it must show `handshake:`.
- `tests/test_sweep_egress.py`: 21 local tests (real ClientHellos, refusals, every truncation, forwarding to a fixed upstream).

## 3. Two architectures

- `make sweep-image` (`Makefile:121`) builds for the daemon's own platform with `--provenance=false`.
- New finding: a cached build's image ID depended on what the cache held. A `--no-cache` rebuild gave `5df8f1a5…` against the cached `21cefa64…`. The content was identical and only the mtimes differed. BuildKit reuses `COPY --from` layers by content, with the old build's mtimes, and `rewrite-timestamp` clamps only newer times. Declaring the epoch as an `ARG` didn't help (`91d11b28…` vs `deb598fb…`). So `make sweep-image` now always uses `--no-cache`, and two builds then gave **`sha256:ecf0c18894294270f7b41b5279abd607e577bf8a4668f37a5e63e46145d81f2b`** both times.
- **arm64 under QEMU** (binfmt `qemu-aarch64`, image `sha256:946aa6c7…`, `platform.machine()` = `aarch64`): `make sandbox-check` gave **10 failed, 67 passed, 1 skipped in 720 s**. Every failure says "bwrap: Creating new namespace failed": qemu-user doesn't emulate namespace `clone`.
  - **What it proves:** the Dockerfile builds for arm64, and the locked wheels install and import.
  - **What it doesn't prove:** anything about bwrap, seccomp, or the kernel on arm64. The container's seccomp filter there is the x86_64 one, applied to QEMU.
- `.github/workflows/ci.yml:44`: `sweep-container-arm64` on `ubuntu-24.04-arm`, `continue-on-error`. It builds the canonical image and runs `make sandbox-check` in it. That runner's Docker applies AppArmor, so the job adds `--apparmor-unconfined` and the userns sysctl, which a Mac doesn't need. Not run yet, and its AppArmor need is inferred, not measured.

## 4. The tripwire as one command

`make sweep-container-check` (`Makefile:127`, `docker/sweep/check.sh`), on a fresh clone at `987e640`, image `ecf0c188…`, `--no-handshake`: **PASSED in 4 m 05 s**.

| Step | Result |
|---|---|
| 1 preflight | daemon, kernel, and security options printed. The image platform matches the daemon's. uid 10001 reads the checkout, writes results, and runs git |
| 2 `make sandbox-check` | 77 passed, 1 skipped ("no default route to compare", under `--network none`) |
| 3 `tests/redteam/` | 68 passed |
| 4 egress probe | 20 of 20 |
| 5 mock grid and verify | 90 trials, `complete: true` |
| 6 kill and resume | SIGKILL after 30 of 90 trials, then `--resume` and verify `complete: true`. Outcome digest `acc7774d…` for both grids. Every result carries `ecf0c188…` |

- Step 2 mounts the checkout writable (`launch.sh:69`). On a read-only checkout, `test_a_sandboxed_tool_reaches_only_its_fixtures_state_and_socket` fails: 1 failed, 76 passed, 1 skipped, on image `f91faf00…`. Its unsandboxed control can't write the repository (EROFS), so a refusal would prove nothing. The test is unchanged. Grids, records, and paid runs keep `/app` read-only.
- `launch.sh --ledger DIR` mounts the host's `~/.canary`. In the image, uid 10001's home is `/home/canary`, and an unmounted ledger refuses. The live smoke is separate, needs the lead's key, and is written out in the doc.
- `tests/test_sweep_launcher.py`: 16 tests against a stub `docker`. They cover the option set, the image binding, refusal of another image, egress wiring, a key file never passed as a variable, and the ledger mount.
- The prototype's `launch.py` became POSIX `launch.sh`. As Python it failed `test_no_new_code_starts_a_process_outside_the_wrapper`, and that check stays as it is.
- Docker Desktop's file sharing, seccomp, and `systempaths`: the doc's failure table covers them. None were tested on Docker Desktop.

## 5. Compared with `sandbox-exec` on the Mac

What the container adds:
- A boundary around the outer runner, which holds the key: uid 10001, no capabilities, read-only image and checkout, writes only to results and `/tmp`.
- Network: none, or `api.anthropic.com:443` only.
- A pinned environment that the gate now checks.

What it loosens, for every process in the container, the runner included:
- The seccomp additions: namespace `clone` and `unshare`, `mount`, `umount2`, and `pivot_root`.
- `systempaths=unconfined`.
- On AppArmor hosts, `apparmor=unconfined`.

What doesn't change, and what isn't known:
- Tools are confined by bwrap plus `no_exec`, as on any Linux host. `tests/redteam/` passed in the image, 68 of 68.
- Against `sandbox-exec`, tools keep file metadata readable everywhere, and the runner has the whole account and network.
- **`sandbox-exec` has never been red-teamed.** `tests/redteam/` targets bwrap, and no CI job or record shows it run on macOS. "As strong as the Mac" is unknown in both directions.

## Final checks (host, `sweeper`, `987e640`)

| Command | Result |
|---|---|
| `make test` | **2666 passed, 0 failed** in 1080 s. The baseline on untouched `main` gave 2608 passed. #71's expected review-test failure didn't occur. The exit code wasn't captured, but no `make` error followed the last line |
| `make sandbox-check` | 78 passed |
| `make t1-suite` | exit 0, 20 of 20 `utility=True` |
| `make grid-check` | exit 0, 70 passed, mock and verify `complete: true` |

The first full run on this branch caught one bug of mine: `docker/sweep/outcome_digest.py` used `splitlines()` on JSONL, flagged by `tests/test_verify_evidence.py::test_no_jsonl_reader_splits_with_splitlines` (1 failed, 2665 passed). I fixed it to split on `\n` only.

## What I didn't do

- No provider call, no `make live-smoke`, no key. One bare TLS handshake reached this VM's egress gateway, with no request sent.
- Nothing ran on macOS, on Docker Desktop, natively on arm64, or on the canonical Debian and ghcr.io build.
- The new CI job hasn't run. No PR was opened, nothing was merged, and nothing was posted.
- No slice owned by `W8-T1`–`T5`, `W9-T3`, `W11`, or `W12` was touched. No pinned `SPEC.md` text, locked schema, `TASKS.md`, or `STATUS.md` was changed. `README.md` lists the new doc.
- Not measured: Docker Desktop's ownership mapping for uid 10001, the canonical image's digest, and why the container is slower.
