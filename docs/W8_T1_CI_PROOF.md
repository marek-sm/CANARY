# W8-T1: maintaining the tool-isolation CI proof

Decision [0023](decisions/0023-tool-sandbox.md) moved the implementation of
`SPEC.md` Section 11's external-endpoint CI proof into the lead scaffold.
W8-T1 maintains that proof; it does not replace the sandbox or change the
protocol. This is the tier-independent part permitted by
[decision 0025 item 9](decisions/0025-full-study.md).

## What CI checks

`make sandbox-check` runs [tests/test_tool_sandbox.py](../tests/test_tool_sandbox.py)
in the [Linux CI job](../.github/workflows/ci.yml), before the full suite. The
tests invoke real subprocesses through the real platform sandbox, with
fictional fixtures and mock providers only.

| Required evidence | Test in `tests/test_tool_sandbox.py` |
|---|---|
| Fixture read, state write, and own fixture socket work; TCP, foreign/sibling sockets, key-file/repository/evidence access, and unrelated execs fail | `test_a_sandboxed_tool_reaches_only_its_fixtures_state_and_socket` |
| Readable system libraries do not grant permission to execute their programs | `test_a_program_inside_a_mounted_library_folder_never_runs` |
| All merged tool-running entry points use the OS wrapper, and setup failures cannot pass vacuously | `test_every_tool_launch_is_sandboxed` |

Launch coverage now exercises the ticket reader, task-suite workers on C2, C3,
and C4, all fifteen canonical coverage cells, the ninety-cell development mock
grid, and all four C1 mock controls. The grid verifies its durable evidence;
the other paths assert completed result records or their separate descriptive
mock summary. Launches must include the expected reader/worker script and
start with the platform confinement launcher. A correct canned answer alone
cannot satisfy the test.

The existing suite also checks unsupported-platform/root/missing-binary
refusals, interpreter mounts, Linux exec-filter rules, foreign socket mounts,
and the paid-run gate. The TCP destination probe uses the reserved TEST-NET-1
address; no external service or credential is needed.

## Reproduce and assess

Use Python 3.11 and the locked dependencies, from repository root:

```sh
uv sync --locked
uv run make sandbox-check
uv run pytest -q
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

## Work still gated

The [paper notes](../paper/w8-t1-method-notes.md) are a draft handoff through
the PR. Paid grid/smoke evidence and defect resolution remain pending, as do
the reviewed variants and the lead's readiness/tier inputs. No task, prompt,
policy, sandbox profile, or component is marked frozen here. Sandbox hash
freezing belongs to the later W8-T1/Gate 3 step.
