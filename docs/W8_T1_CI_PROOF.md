# W8-T1: maintaining the tool-isolation CI proof

Decision [0023](decisions/0023-tool-sandbox.md) moved the implementation of
`SPEC.md` Section 11's external-endpoint CI proof into the lead scaffold.
W8-T1 maintains that proof; it does not replace the sandbox or change the
protocol. This is the tier-independent part permitted by
[decision 0025 item 9](decisions/0025-full-study.md), reconciled with
[decision 0028](decisions/0028-restore-strength.md).

## What CI checks

`make sandbox-check` runs [tests/test_tool_sandbox.py](../tests/test_tool_sandbox.py)
in the required [Linux CI job](../.github/workflows/ci.yml), before the full suite.
Decision 0028 also adds an advisory `macos-sandbox` job. Its result is evidence
about GitHub's image, not the project lead's sweep host. The
tests invoke real subprocesses through the real platform sandbox, with
fictional fixtures and mock providers only.

| Required evidence | Test in `tests/test_tool_sandbox.py` |
|---|---|
| Unwrapped controls reach local listeners and sentinel files, while the wrapped probe is confined; fixture reads, state writes, and its own socket still work | `test_a_sandboxed_tool_reaches_only_its_fixtures_state_and_socket` |
| Host route and local non-loopback listener are unavailable to the tool | `test_a_tool_has_no_route_the_host_has` |
| Local UDP/DNS queries reach the control listener, but not from the sandbox | `test_udp_and_dns_reach_nothing_from_the_sandbox` |
| Bad paths, missing binaries, timeouts, and unrelated exceptions cannot count as containment | `test_a_bad_path_or_missing_binary_never_reads_as_containment`, `test_an_unrelated_failure_never_reads_as_containment`, `test_a_program_that_only_timed_out_is_not_denied` |
| Readable system libraries do not grant permission to execute their programs | `test_a_program_inside_a_mounted_library_folder_never_runs` |
| All merged tool-running entry points use the OS wrapper, and setup failures cannot pass vacuously | `test_every_tool_launch_is_sandboxed` |

Launch coverage now exercises the ticket reader, task-suite workers on C2, C3,
and C4, all fifteen canonical coverage cells, the ninety-cell development mock
grid, and all four C1 mock controls. The grid verifies its durable evidence;
the other paths assert completed result records or their separate descriptive
mock summary. Launches must include the expected reader/worker script and
start with the platform confinement launcher. A correct canned answer alone
cannot satisfy the test. The process-launch AST scan and its own positive/negative
fixtures also catch new launch sites outside the wrapper.

The existing suite also checks unsupported-platform/root/missing-binary
refusals, interpreter mounts, Linux exec-filter rules, foreign socket mounts,
and the paid-run gate. Controls use synthetic sentinels and local listeners.
The route probe uses reserved TEST-NET-1; its unwrapped control sends no external
packet. A timeout alone is not evidence of containment.

## Recheck of the sandbox's last fix

Decision 0028 item 8 assigns T1 a recheck of `0434116`. The engineering recheck
compares that change with current main `103e173`, reads `tools/no_exec.py` and
the launcher/profile construction in `tools/sandbox.py`, and reruns real
confinement and mutation regressions. The exec filter is unchanged since that
fix; the launcher differs only in its explanation of checkout identity.

The Linux bootstrap installs `no_new_privs` and the seccomp filter before the
tool's first line, refuses pre-existing threads, checks the ABI, and denies
`execve`, `execveat`, `ptrace`, and `process_vm_writev`, including x32 syscall
numbers. The worker starts as the sandbox's only process. Tests interpret the
BPF against explicit architecture tables. On Linux, a control runs a library
executable with the filter removed and the filtered probe denies it. Worker
mounts expose only the fixture socket; foreign sockets in mounted directories
refuse the launch.

The [sandbox mutation regressions](../tests/test_sandbox_mutants.py) cover
macOS's exact allow rules, no-network profile, path quoting, interpreter mount
boundaries, and fingerprint binding to the exec filter. These are distinct
from live Linux filter execution, which macOS cannot establish. The
[Linux red-team regressions](../tests/redteam) add real worker, network, file,
credential, exec, and orphan-process probes.

This is an AI-assisted engineering recheck, not a formal approval or an
attestation that the accountable human can explain the change. The PR records
the tested head, commands, platform-specific results, skips, and remaining
human review. No freeze identity is computed here.

## Reproduce and assess

Use Python 3.11 and the locked dependencies, from repository root:

```sh
uv sync --locked
uv run make sandbox-check
uv run pytest -q tests/test_sandbox_mutants.py
uv run make test
uv run make w7-t1-check
```

Run on a supported non-root host with the required sandbox available, as
described in [decision 0023 item 10](decisions/0023-tool-sandbox.md). A failure
to initialize the OS sandbox is a failed proof, not permission to run tools
unconfined or skip the tests. Linux CI supplies `bwrap`; local macOS uses
`sandbox-exec`. Local macOS evidence and Linux CI evidence are separate.

The PR carries observed command results and CI links. Gate 3 must use green
evidence for the code it freezes, not infer green status from this document.
These checks produce no empirical attack result, spend, or live-trial credit.

## Later paid-evidence acceptance

The lead supplies grid and coverage verification reports, the matching raw-file
hash manifest, and access-controlled raw records. Decision 0028's verification
recomputes stored results from events; each invocation records OS/Python/SQLite,
lock identity, sandbox fingerprint, and scoring-code provenance. A mock summary
alone does not satisfy W7 acceptance. The paid grid, record creation, record
commit, and paid execution share one fresh clean checkout. The spend-ledger/cap
and acknowledgement gates remain the lead's responsibility. Reproduction above
makes no paid call and initializes no ledger or cap.

## November 13 component handoff

The [paper notes](../paper/w8-t1-method-notes.md) remain a draft handoff.
Paid evidence, reviewed task variants, Gate 2, the tier input, and W8-T2's
corpus freeze have now merged. The [component handoff](W8_T1_FREEZE.md)
records the raw coverage diagnosis, corrected trusted JSON instruction,
and reproducible component-hash candidate. Its manifest
remains pending lead review; it does not finalize the full protocol freeze.

Decision 0028 item 9 keeps the host sweep unless the lead's arm64 Mac passes
the pinned-image sandbox tests, full mock grid, kill/resume, and authorized
live smoke by November 8, with the required superseding record. GitHub Docker
and macOS CI results do not satisfy that tripwire or select an environment.
