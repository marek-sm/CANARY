# 0023: Every tool process runs in a deny-by-default OS sandbox, and no paid call runs without the lead's paid-run record

- Status: Accepted. Approved by the project lead on 2026-10-28; drafted with AI assistance.
- Date: 2026-10-28
- Decision scope: Protocol
- Secondary scopes: Release, Governance
- Related specification sections: Sections 3, 9, 11, and 13
- Supersedes: `TASKS.md`'s paid-run condition wording "all three of these hold" and its live-smoke sentence ("doesn't depend on any of the three"), which become four items with the live smoke as the stated exception; decision 0022 item 8's "the paid-run condition" as unchanged; the `TASKS.md` statement that the container checks of `W6-T1`'s tool runs are required in the container (they move to the host job under the sandbox); and `W8-T1`'s Committed item "the `SPEC.md` Section 11 CI proof that no tool can reach an arbitrary external endpoint committed and green", which this record's lead scaffold delivers and `W8-T1` keeps green.

## Context

The October 17 audit's F-01 (High) found that every tool process ran as a bare host subprocess, with a writable filesystem, the host's network, and read access to everything the operator can read. `SPEC.md` Section 3 (pinned by decision 0009) requires, under every configuration including D0_BASELINE:
- tool processes run non-root;
- they have a read-only filesystem except per-trial state and result mounts;
- the tool sandbox has no arbitrary network route;
- the hosted-model credential never enters tool environments.

Tool-result delivery (#61) therefore refused any non-mock provider, which kept paid runs closed.

The F-01 evidence on `main` before this change is a probe launched exactly like the tool worker. It could:
- read an operator key file, the repository, and the home directory;
- write the trial's `events.jsonl`, the repository, and `/tmp`;
- connect over loopback TCP and to a foreign Unix socket;
- run `sh`, `curl`, and `open`.

An October 21 design ran each tool call in a Docker container. It was parked after its review found six blocking problems:
- a mock/CI exemption that narrowed pinned Section 3;
- a container path never exercised before paid calls;
- an image not tied to the commit;
- uid and mount ownership;
- containers orphaned on timeout or crash;
- unstated new preconditions and hours.

The project lead's Mac has no Docker.

## Options considered

1. **Per-call Docker containers (October 21).** Rejected for the six problems above.
2. **Sandbox only paid runs.** Rejected. Section 3 holds under every configuration, and a path first exercised during the paid grid can't be rerun inside the Section 9 ceiling.
3. **A deny-by-default OS sandbox for every tool launch, mock and CI included, plus a paid-run record checked on every paid path.** Chosen.

## Decision

1. **One launcher, `tools/sandbox.py`, wraps every tool process.** That covers the three launch sites: `tasks/registry.py` `worker()` and `fixture_service()`, and `runner/ticket_slice.py` `worker()`. It denies by default and allows only:
   - running the interpreter;
   - reading the interpreter, its virtual environment, `tools/`, the system libraries, and the trial's fixture root;
   - writing only the process's own directory (the tool state, or the fixture-socket directory);
   - reaching only the trial's fixture Unix socket, by path.

   It refuses a root user, an unsupported platform, or a missing sandbox binary, so a launch fails closed. Tool processes get only `PATH`, `LANG`, and `TMPDIR` (their own writable directory), never a provider variable.
   - **macOS:** `sandbox-exec` with `(deny default)`. The interpreter needs no system service: the allowed `mach-lookup` list is empty, and `sysctl-read` isn't allowed. File metadata (names, sizes, and dates through `stat`) stays readable everywhere, because Python's startup resolves paths through it. File contents, directory listings, and writes are denied outside the allowed paths.
   - **Linux:** `bwrap` with every namespace unshared. Only the named paths, the interpreter, and `/usr/lib`, `/lib*`, and `/etc/ld.so.cache` are mounted. `/`, `/home`, `/run`, `/var`, the repository root, and `/tmp` are not. bwrap creates empty parent folders for each mount, and `--remount-ro /` makes them read-only.
   - **Other platforms** refuse. Windows members use WSL2.
2. **Tools have no network at all.** `tools/fixture_http.py` serves the trial's fixture pages on `fixture.sock` in the trial's socket directory instead of loopback TCP, and `tools/fetch_url.py` connects to it over `AF_UNIX`. The allowlist, the `.fixture.test` check, and the no-redirect rule are unchanged. The `fetch_url` description, `TOOL_SCHEMAS`, fixture hashes, and `task_order` don't change.

   The service removes a stale socket before binding and exits when its parent closes stdin. The runner removes the socket file when the service stops, so a crash leaves nothing serving.

   Versions: `fetch-url-v0.2.0` and `fixture-http-v0.2.0`.
3. **Evidence is unwritable by tools.** Each tool writes only its own directory, so the trial's `events.jsonl`, `results.jsonl`, and sink mirror, and the repository, are beyond its reach.
4. **`query_db` on Python builds without extension loading.** `tools/query_db.py` calls `enable_load_extension(False)` only where the method exists. python.org's macOS build compiles extension loading out, so it can't load extensions at all. That build otherwise crashed every C2 cell. Version: `query-db-v0.1.2`.
5. **Version capture.** `component_versions.tool_sandbox` records `mode:version:rules-hash` in delivery, `task_suite`, and `ticket_slice` events, including the live smoke's.
6. **The paid-run record.** `protocol/paid_run_record.json` (schema `paid_run_record`) is the project lead's dated record that every paid-run condition holds. `python -m runner.paid_run record` writes it from a verified mock grid. It holds:
   - the date and recorder;
   - the commit;
   - the sandbox the mock grid ran under;
   - each condition's evidence;
   - the SHA-256 of every git-tracked file under `agent/`, `channels/`, `defenses/`, `oracles/`, `runner/`, `tasks/`, `tools/`, `corpus/`, `fixtures/`, and `schemas/`, plus `protocol/development_grid_spec.json` and `uv.lock`. A change to any of them closes paid runs until the lead records again.

   The sandbox fingerprint covers the rules, not machine paths, so the recorded mock grid and the paid run must share a platform and sandbox version, not a directory. A checkout reached through a symlinked path changes the fingerprint, which refuses the paid run, so it fails closed. The mock grid behind the record runs on the paid-run machine, as part of the paid commands in item 8.

   `runner.paid_run.require_paid_run` runs before any non-mock provider's first call, in `execute.execute_trial`, `ticket_slice.run`, and `mock_slice.run_mock_trial`. It refuses unless all of these hold:
   - `CI` and ambient provider variables are absent;
   - the sandbox is available;
   - the record validates;
   - the running sandbox equals the record's;
   - no hashed path has uncommitted or untracked changes;
   - every hash matches.

   The text-only runner body refuses any paid provider, because it measures direct injection. Paid commands run from a clean checkout of the recorded commit, so a later merge can't invalidate the record or a resume. `grid_dev.live_run_refusal` uses the same check.
7. **The paid-run condition has four items.** These are tool-result delivery, a full mock grid on that runner, the request-to-effect table and ablation, and now every tool process running in the sandbox. The record is how the project lead records the date all four hold.

   The live smoke (`make live-smoke`) stays the one exception. It needs no record, but its read tool runs sandboxed and it still refuses in CI or with ambient provider variables.
8. **Who runs the paid commands.** The paid grid (`W7-T3`) and the paid smokes (`W7-T1`) run on the project lead's Mac. That keeps one platform and sandbox for the record, keeps the self-funded key on its machine, and avoids member machine setup before Friday.

   This is a visible reassignment of executing those commands only. Samson and Chace keep their slices, deliverables, and reviews, and re-accept it by replying to its start notice.
9. **Gate 3.**
   - `W8-T1` keeps the sandbox's CI proof green, and its Committed row adds "the sandbox launcher and profile hashes frozen". Chace re-accepts that row on its start notice.
   - The Gate 3 step's "Uses" cell adds this CI proof.
   - `W9-T4`'s sandbox-hash verification reads that freeze.
   - The CI container digest stays Gate 3's container artifact.

   `compose.yaml` (audit F-07) stays a separate item.
10. **Members.** `make sandbox-check` runs the sandbox tests. macOS needs nothing. Linux needs `bubblewrap` and, on Ubuntu 23.10 and later, `kernel.apparmor_restrict_unprivileged_userns=0` in `/etc/sysctl.d`. Windows needs WSL2 Ubuntu. Members run it once and report a failure the same day.
11. **Review.** Chace (T1, the tools' owner) reviews the launcher, its tests, and the tool changes.

## Consequences

- **Section 3 holds on every path.** That includes mock runs and CI, under every configuration and the live smoke. The CI proof Gate 3 needs now exists: the sandbox tests run in CI under `bwrap`.
- **The CI container job keeps only the tool-free mock trace.** The `t1-smoke` and `t1-suite` checks run on the host job under the sandbox. The container can't run `bwrap` without loosening its own isolation.
- **Paid runs open only through the record.** Any change to hashed code after it is recorded closes them again until the lead records anew. That's deliberate: the paid grid runs exactly the code its mock preflight ran.
- **The lead's time.** Recording the paid-run record and starting the paid commands is about an hour this week.

## Verification

- `tests/test_tool_sandbox.py` (run by `make sandbox-check`) passes on macOS (`sandbox-exec`) and in CI (`bwrap`). It covers:
  - the probe's twelve forbidden actions denied and its three allowed actions working;
  - the launcher's refusals;
  - every tool launch wrapped;
  - every paid-run refusal on the delivery, text-only, `ticket_slice`, and `mock_slice` paths;
  - the live-smoke exception.
- On `main` before this change, the same probe launched like the worker was allowed 11 of its 12 forbidden actions.
- The full suite passes on macOS without the local SQLite shim (1820 tests), because of item 4.
- `tests/test_contract_lock.py`, `tests/test_corpus_rules_freeze.py`, and `tests/test_request_effect.py` pass unchanged, so no pinned text changed.
