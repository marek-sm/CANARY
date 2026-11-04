# Cloud red-team: tool sandbox (`tools/sandbox.py`, `tools/no_exec.py`)

- **Branch:** `cloud/sandbox-redteam`
- **Commit at time of writing:** `0d2bf4ccb7204cfa66d61075787f32bca7297c08`
- **Scope:** authorized security testing of CANARY's own tool sandbox, inside one
  isolated cloud VM. Target guarantees: `SPEC.md` Section 3 ("Non-negotiable
  safety invariants") and `docs/decisions/0023-tool-sandbox.md`.
- **Platform under test:** Linux `6.18.44-fc-v233 x86_64`, Ubuntu 24.04.5 LTS,
  `bubblewrap 0.9.0`, CPython 3.11.18, sandbox fingerprint
  `linux-bwrap:tool-sandbox-v0.3.0:901ea926a5b4c707`.

## Headline result

I launched **68 distinct attack attempts** against the real `bwrap` sandbox and
the tools that run inside it, every one launched the way the production worker
launches a tool (`sandbox.wrap(...)` → `subprocess.run(..., capture_output,
timeout)`). **No attempt escaped the boundary.** Every attempt to read outside
the fixture root, write outside the tool's state dir, reach any network or
foreign socket, run another program, obtain the runner's credential, or orphan a
process on timeout was blocked. All 68 are committed as regression tests under
`tests/redteam/` and pass under real `bwrap`.

There is **one informational observation** (the tool environment also contains
`PWD`), which **cannot change any reported number and does not break a safety
boundary**. Details below.

This is an automated red-team by an AI agent. It is evidence for the project
lead; it does **not** replace the human reviewer `SPEC.md` and decision 0023
require (Chace, as T1 owner, reviews the launcher and tool changes). I made no
real provider call, changed no frozen/claim-bearing artifact, and left
`runner/paid_run.py`'s refusals closed.

## Environment setup (exact commands)

The VM runs as **root**, and `tools/sandbox.py` refuses root by design
(`mode()` raises `SandboxUnavailable`, `tests/test_tool_sandbox.py` asserts it).
That refusal was left intact; all probes run as a created non-root user.

```bash
# bubblewrap
apt-get update
apt-get install -y bubblewrap            # bubblewrap 0.9.0

# unprivileged user namespaces
# NOTE: kernel.apparmor_restrict_unprivileged_userns does NOT exist on this
# kernel (6.18.44-fc-v233); `sysctl -w ...=0` returns "cannot stat". No AppArmor
# userns restriction is in force here, and bwrap --unshare-all works for the
# non-root user without it. (On stock Ubuntu 23.10+ that key must be set to 0.)

# non-root user + project env (venv and cache OUTSIDE the root-owned repo)
useradd -m -s /bin/bash redteam
chmod -R a+rX /home/user/CANARY && chmod a+rx /home/user
cp /root/.ccr/ca-bundle.crt /home/redteam/work/ca-bundle.crt   # readable by redteam
su redteam -c 'cd /home/user/CANARY && \
  HTTPS_PROXY="$HTTPS_PROXY" SSL_CERT_FILE=/home/redteam/work/ca-bundle.crt \
  UV_CACHE_DIR=/home/redteam/work/uvcache UV_PROJECT_ENVIRONMENT=/home/redteam/work/venv \
  uv sync --group dev'
```

Runner helper (`/home/redteam/work/run.sh`) runs any command as `redteam` with
`UV_PROJECT_ENVIRONMENT`/`UV_CACHE_DIR`/`TMPDIR` set and `uv run --no-sync`.

### Validation of the harness before attacking

The project's own sandbox suite passes as the non-root user under real `bwrap`,
confirming the setup is faithful:

```
uv run --no-sync python -m pytest -q tests/test_tool_sandbox.py
# 35 passed
```

## Method

- Each primitive probe is `[python, -I, -c CODE]` wrapped by
  `sandbox.wrap(argv, cwd=..., read=[fixtures], write=[state], socket_dir=...)`
  and run with `cwd` as given and `sandbox.environment([state])` — byte-for-byte
  the launch in `tasks/registry.py:worker` / `fixture_service` and
  `runner/ticket_slice.py`.
- Each tool-level probe calls the **real** `tools/worker.py` through the sandbox
  (`run_worker`), with fixtures built by `tasks.registry.reset` and the fixture
  HTTP service started by `tasks.registry.fixture_service` — the production
  dispatch path, not the in-process tool functions.
- Shared harness: `tests/redteam/conftest.py` (`trial` layout, `run_probe`,
  `run_worker`). Tests skip on non-Linux and when the sandbox refuses (e.g. if
  run as root).

## Raw counts

```
uv run --no-sync python -m pytest tests/redteam/
# 68 passed in 14.69s
```

Per file (all passing):

| file | tests | what it attacks |
|---|---:|---|
| `test_fs_escape.py` | 6 | read outside fixtures, write outside state, /proc & /sys, symlink escape, traversal through the real `read_file` |
| `test_exec_escape.py` | 9 | execve/execveat, raw syscalls, memfd+execveat, fork/clone3 child exec, ptrace, process_vm_writev, filter-removal, i386 `int 0x80`, x32 execve |
| `test_network.py` | 6 | TCP/UDP/raw/IPv6, foreign + abstract Unix sockets, bring loopback up, `/dev` surface, io_uring |
| `test_fetch_url.py` | 20 | allowlist bypass, suffix/userinfo/port/fragment/scheme tricks, DNS/proxy, non-exact match, via the live fixture service |
| `test_tools_sandboxed.py` | 18 | query_db (ATTACH/extensions/pragmas/injection/malformed), send_email (JSONL injection/oversize/symlink sink), read_file bounds, invalid dispatch |
| `test_credential.py` | 3 | provider-var leakage, inherited fds, key-file reachability |
| `test_orphan.py` | 2 | surviving child after a tool timeout; die-with-parent/as-pid-1 present |
| `test_misc.py` | 4 | personality, TIOCSTI, mount/remount, nested user namespace |

## Findings (ranked by impact)

No finding could change a reported number or break a safety boundary. The single
observation is informational.

### 1. (Informational) The tool environment also contains `PWD`

- **Where:** observed via `tests/redteam/test_credential.py:18`
  (`test_no_provider_variable_and_a_minimal_environment`).
- **What:** `tools/sandbox.py:environment()` documents that a tool gets only
  `PATH`, `LANG`, and `TMPDIR`. Under `bwrap` the live process additionally sees
  `PWD`, set by `bwrap`'s `--chdir` to the tool's own working directory (the
  state dir for the worker, the socket dir for the fixture service).
- **Repro:**
  ```bash
  /home/redteam/work/run.sh "uv run --no-sync python -m pytest -q \
    tests/redteam/test_credential.py::test_no_provider_variable_and_a_minimal_environment"
  # env observed: {PATH:/nonexistent, LANG:C.UTF-8, TMPDIR:<state>, PWD:<state>}
  ```
- **Impact:** none to the safety boundary. `PWD` equals the tool's own `cwd`,
  which the tool already knows; it carries no secret, no provider variable, and
  no path outside the sandbox. It does not reach traces or results. I flag it
  only because decision 0023 item 1 and the `environment()` docstring say "only
  `PATH`, `LANG`, and `TMPDIR`"; the accurate statement is "plus `PWD` = the
  tool's cwd, injected by bwrap." No code change is implied; this is a
  documentation-accuracy note for the lead.

### Everything else: blocked (defenses confirmed end-to-end)

Representative confirmations, each with a committed repro:

- **No program can be run.** `execve`/`execveat` (high-level and raw `syscall`),
  `os.posix_spawn`, the dynamic loader as interpreter, `memfd_create`+`execveat`,
  and `/proc/self/fd` exec all return `EPERM`; a forked or `clone3` child inherits
  the filter and cannot exec; the filter cannot be removed (`NO_NEW_PRIVS=1`).
  An i386 `int 0x80` syscall **kills** the process (`SIGSYS`, surfaced as bwrap
  exit `159`), and x32 `execve`/`execveat` return `EPERM`.
  (`test_exec_escape.py:33,50,75,112,138,173,197,241,269`.)
- **No network route.** TCP (loopback/external/public), UDP, IPv6, and
  `AF_PACKET` raw sockets all fail; loopback cannot be brought up
  (`CAP_NET_ADMIN` dropped); foreign Unix sockets (by relative or absolute path)
  and **host abstract-namespace** sockets are unreachable (fresh net namespace);
  io_uring buys nothing because the mount/net namespaces bound it. `/dev` holds
  only the safe pseudo-devices (`/dev/mem`, `kmsg`, host disks absent).
  (`test_network.py`.)
- **Filesystem confinement.** `/etc/passwd`, `/etc/shadow`, the runner key file,
  the repository, and `/root` are unreadable; writes to `/tmp`, the repo, the
  evidence file, the read-only fixtures, `/etc`, and `/` all fail; a symlink
  created in the writable state dir and pointing at a host path still resolves to
  an unmounted path; the real `read_file` refuses traversal, absolute paths, and
  symlinked components. (`test_fs_escape.py`.)
- **Tools.** `query_db` binds params (no injection), rejects unregistered/malformed
  requests, and ATTACH/`load_extension`/writes/`PRAGMA writable_schema` all raise
  under the authorizer + `query_only` + `enable_load_extension(False)` even when
  exercised directly against the same snapshot in the sandbox; `send_email`
  escapes newlines so a crafted recipient cannot inject a second JSONL receipt and
  cannot write through a symlinked sink; `fetch_url` rejects every non-exact and
  tricky URL and only ever reaches `fixture.sock`. (`test_tools_sandboxed.py`,
  `test_fetch_url.py`.)
- **Credential.** No `ANTHROPIC_*`/`OPENAI_*` variable and no synthetic key value
  reaches the tool; no inherited fd points at the key file, repo, or a foreign
  socket. (`test_credential.py`.)
- **Timeouts.** A wedged tool that forks a child and blocks past the 5 s worker
  timeout is fully torn down by `subprocess.run`'s SIGKILL of `bwrap` plus
  `--as-pid-1`/`--die-with-parent`; the child never writes its post-timeout
  marker. (`test_orphan.py:25`.)
- **Misc.** `personality()` does not re-enable exec; `TIOCSTI` and `/dev/tty`
  are unavailable (no controlling terminal, `--new-session`); `mount`/remount and
  a nested user namespace give no route to the host. (`test_misc.py`.)

## Key design observations (why the boundary held)

- The filesystem and network boundaries are **namespace-based** (mount + network
  namespaces), enforced below the syscall layer. `io_uring` — which can sidestep
  a seccomp policy that filters `openat`/`connect` — therefore buys no escape
  here: the only seccomp-filtered calls are the exec family + `ptrace` +
  `process_vm_writev`, and io_uring has no exec/ptrace operation.
- The exec denial is layered correctly: `EPERM` for the native-ABI exec family
  and x32, `SIGSYS` kill for any foreign ABI (i386 `int 0x80`), and the filter is
  locked by `NO_NEW_PRIVS` so it cannot be dropped and is inherited by every
  child/thread.

## What I did NOT check (limitations)

- **macOS `sandbox-exec`** and **aarch64 `bwrap`**: not reachable on this VM
  (x86_64 Linux only). The macOS profile and the aarch64 seccomp numbers are
  unverified here; `tests/test_tool_sandbox.py` covers them structurally.
- **Exhaustive timing fuzzing of symlink/rename TOCTOU races**: I verified the
  structural defenses (`O_NOFOLLOW` on every path component with `dir_fd`, the
  `st_nlink == 1` check, and the mount-namespace boundary that makes host targets
  unnameable) and the orphan-on-timeout behavior once; I did not run millions of
  timing iterations to probe for a race window.
- **Redirect following end-to-end through the sandbox**: covered at unit level by
  `tests/test_safe_tools.py::test_redirects_never_follow_location`; I relied on
  that plus the fact that the sandbox has no network other than `fixture.sock`.
- **A maliciously crafted `fixture.sqlite` / fixture pages**: the DB and pages are
  trusted, hash-verified fixtures; the attacker in the threat model controls only
  untrusted *content* and the bound `params`/`url` values, which I fuzzed. I did
  not fuzz `sqlite3.deserialize` with adversarial database images.
- **The paid-run record / provider gate internals**: out of scope and forbidden
  here. I confirmed only that no provider variable reaches a tool; I made no real
  provider call and left `runner/paid_run.py` refusals closed.
- **Kernel / `bwrap` / seccomp 0-days**: I tested the *policy*, not
  implementation bugs in the kernel or bwrap itself.
- The `kernel.apparmor_restrict_unprivileged_userns` sysctl the brief named does
  not exist on this kernel; I could not set it and did not need to (see setup).

## How to reproduce

```bash
# as the non-root user, from the repo root, under uv (Python 3.11):
uv run --no-sync python -m pytest tests/redteam/          # 68 passed
# a single attack, e.g. the foreign-ABI kill:
uv run --no-sync python -m pytest -q \
  tests/redteam/test_exec_escape.py::test_i386_int_0x80_syscall_kills_the_process
```

(All tests `skip` cleanly on non-Linux or when the sandbox refuses, e.g. if run
as root.)
