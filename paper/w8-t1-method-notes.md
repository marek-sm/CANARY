# W8-T1 draft agent, tool, task, and utility notes

Draft input for paper Sections 6, 9, and 10, based on the merged W7-T1 and
W7-T3 implementations and decision 0023's sandbox. These are implementation
notes for the designated paper leads, supplied through this pull request.
They are not frozen methods or empirical results. The project lead and paper
leads retain scientific wording and manuscript ownership.

## Agent and recorded execution

The bounded [agent loop](../agent/loop.py) receives a trusted system instruction,
the user's task, tool schemas, and successive tool observations. The
[task registry](../tasks/registry.py) owns task prompts, declared resources,
exact task policies, and trusted high-risk action grants. Retrieved C2–C4
content reaches the model through [tool-result delivery](../runner/delivery.py).
It cannot select a new policy or grant. The independent authorization audit
and utility oracle score recorded execution separately.

The [schedule](../runner/schedule.py) identifies each comparison cell. The
[durable executor](../runner/execute.py) writes dispatch intent before an
effect, retains attempts and earlier events on a later failure, and reuses
stored canaries on resume. Requested, authorized, blocked, dispatched,
execution-succeeded, effect-observed, sink-received, and final-disclosure facts
have separate meanings under [SPEC.md Section 7](../SPEC.md#7-deterministic-oracles-and-event-model).
An unknown observation stays null. Correct task completion does not erase an
unrelated security violation.

## Tools and intrinsic confinement

| Tool | Intrinsic capability boundary | Implementation and negative evidence |
|---|---|---|
| `read_file` | Fictional fixture files only; bounded reads through no-follow descriptors | [Reader](../tools/read_file.py), [filesystem checks](../tools/local_fs.py), [safe-tool tests](../tests/test_safe_tools.py) |
| `query_db` | Registered parameterized queries over an in-memory copy of the read-only fictional snapshot; no model-supplied SQL | [Query tool](../tools/query_db.py), [safe-tool tests](../tests/test_safe_tools.py) |
| `fetch_url` | Exact logical fixture URL mapped to the trial's Unix-socket fixture service; no arbitrary endpoint or redirect | [Fetcher](../tools/fetch_url.py), [fixture service](../tools/fixture_http.py), [safe-tool tests](../tests/test_safe_tools.py) |
| `send_email` | Append to the trial's local fake sink; no real email transport | [Sink](../tools/send_email.py), [safe-tool tests](../tests/test_safe_tools.py) |

Every tool subprocess additionally uses the deny-by-default OS
[sandbox launcher](../tools/sandbox.py). macOS uses `sandbox-exec`; Linux uses
`bwrap` and the [exec filter](../tools/no_exec.py). A worker can read its fixture
and interpreter dependencies, write its own state, and connect only to its own
fixture Unix socket. Provider credentials remain in the outer runner. The
intrinsic boundary holds under D0_BASELINE, D1_POLICY_GATE, and D2_DATAMARKING;
it does not depend on a defense authorizing a request.

[Decision 0023](../docs/decisions/0023-tool-sandbox.md) supplies the sandbox and
the required CI proof. W8-T1 keeps that proof green and extends its launch
coverage. See the [proof and reproduction map](../docs/W8_T1_CI_PROOF.md).

## Tasks, fixtures, and deterministic utility

The ten [task templates](../tasks/templates) span read/query, local-web
extraction, cross-source comparison, and legitimate high-risk actions. Each
declares its channel adapters, required source calls, exact output, policy,
and fixture identity. The [fixture registry](../tasks/registry.py) verifies the
manifest, resets a per-trial copy, and checks the SQLite snapshot against its
seed. The new channels and prompt refresh in
[#71](https://github.com/marek-sm/CANARY/pull/71) remain pending; the draft does
not describe them as merged or retained at a selected tier.

The [task utility oracle](../oracles/utility/task_suite.py) requires exact typed
JSON, the declared source reads and observed effects, and, for email tasks, an
exact fake-sink receipt. Duplicate keys, nonfinite values, and conflation of
Boolean and numeric values do not satisfy it. Missing effect or sink evidence
can leave utility null. [Oracle fixtures and tests](../tests/test_task_suite.py)
exercise both success and failure, unknown observations, and independence from
unrelated security violations.

The five templates absent from the development-base assignment have
[predeclared canonical clean coverage](../tasks/coverage-smokes.json), run
through the durable executor and native tools. The
[W7-T1 handoff](../docs/W7_T1_HANDOFF.md) links its compact mock evidence.
The [development grid](../runner/grid_dev.py) crosses the five development
bases, three indirect channels, attack/clean, and all three configurations.
Its mock provider validates plumbing and evidence, not model behavior.

The four [C1 control definitions](../corpus/c1_controls) place source-faithful
hostile text in a trusted user prompt, in decision 0018 order. Their
[mock executor](../runner/c1_mock.py) uses a separate descriptive format,
retains null authorization, and excludes them from indirect estimates.
It is not an official C1 executor or a live positive-control result.

## Evidence and remaining acceptance work

The PR validation records the exact tested commit and commands. Source-linked
checks that paper leads can inspect are:

- [Sandbox proof and launch coverage](../tests/test_tool_sandbox.py), run by
  `make sandbox-check` before the full suite in [CI](../.github/workflows/ci.yml).
- [Task and utility tests](../tests/test_task_suite.py), including native tool
  execution, fixture reset verification, typed oracle cases, and exact grants.
- [Coverage and C1 tests](../tests/test_w7_t1.py), including artifact drift,
  stored-event recomputation, and completed resume without redispatch.
- [Delivery tests](../tests/test_delivery.py) and
  [grid defense tests](../tests/test_grid_dev_defenses.py), keeping delivery,
  enforcement, marking, and recorded audit evidence distinct.

**Limitation for the paper:** canned mock outputs establish local wiring and
deterministic scoring only. They cannot establish model resistance, defense
efficacy, the adequacy of the task/corpus sample, or live-model readiness.
The sandbox proof concerns the supported host configurations under decision
0023; it is not a proof about arbitrary operating systems or a public service.

Before the whole W8-T1 slice is complete: inspect the merged paid grid/smoke
summary and authorized raw evidence, resolve any task/oracle defects, incorporate
the reviewed variants, and apply the selected tier after the lead inputs. Only
then freeze the retained tasks, fixtures, policies, validators, system prompt,
tool descriptions, and sandbox launcher/profile identities through the Gate 3
process. This early draft computes no freeze hash and selects no tier.
