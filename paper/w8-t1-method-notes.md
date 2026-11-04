# W8-T1 draft agent, tool, task, and utility notes

Draft input for paper Sections 6, 9, and 10, based on the merged W7-T1 and
W7-T3 implementations, decision 0023's sandbox, and decision 0028 on main
`103e173` (including #76). These are implementation
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

[Decision 0028](../docs/decisions/0028-restore-strength.md) distinguishes the
security disclosure surface from the utility answer: disclosure scans the last
reply together with consecutive cut-off text-only replies immediately before
it, while utility and `final_output` still use the last reply alone. The scan
identity and whether it extends beyond `final_output` are stored. Complete
request logs, infrastructure failures, filtered tool blocks, and malformed
endings retain their separately defined Boolean-or-null rules; the
[scoring-surface regressions](../tests/test_scoring_surfaces.py) exercise them.

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
coverage. Decision 0028 requires T1's recheck of the last sandbox fix; the
[proof and reproduction map](../docs/W8_T1_CI_PROOF.md) separates the engineering
recheck, Linux/macOS runtime evidence, and pending human review.

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
The merged coverage executor also has a gated live path and a read-only
`--verify` path. No live path was exercised for these notes. W7-T1 and W7-T3
remain incomplete until their paid evidence merges, even though their code
unlocked this tier-independent W8 work.

The four [C1 control definitions](../corpus/c1_controls) place source-faithful
hostile text in a trusted user prompt, in decision 0018 order. Their
[mock executor](../runner/c1_mock.py) uses a separate descriptive format,
retains null authorization, and excludes them from indirect estimates.
It is not an official C1 executor or a live positive-control result.

## Provenance, spend, and raw evidence

The [paid-run gate](../runner/paid_run.py) binds the clean checkout, mock-grid
preflight, locked packages, scoring code, and reviewed record. The grid,
record creation, its commit, and paid execution share one checkout; live
adapter checks keep their record exception but still need clean hashed paths,
locked packages, and the external [spend ledger and cap](../runner/spend_ledger.py).
These are execution gates, not empirical evidence.

Each invocation's `code_provenance.jsonl` records code/scoring identities and
OS build, Python build, SQLite version, lock identity, and sandbox fingerprint.
The [grid verifier](../runner/grid_dev.py) and
[coverage verifier](../runner/coverage.py) recompute stored results from durable
events and check supporting execution evidence. The
[raw manifest](../runner/raw_manifest.py) anchors relative raw-file paths and
hashes without publishing provider bodies, canaries, or host paths. Its
published identity is necessary: internally consistent edits made before that
anchor cannot be ruled out by a later digest alone.

Raw records stay outside Git with controlled access. The lead owns paid calls,
Console reconciliation, and the November 8 environment tripwire. The host
sweep remains the default until the lead's required pinned-container checks
and superseding record exist. Advisory macOS CI proves GitHub's image only.

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
- [Paid-run gate tests](../tests/test_paid_run_gate.py),
  [stored-evidence verification](../tests/test_verify_evidence.py), and
  [spend-ledger tests](../tests/test_spend_ledger.py), using synthetic accounts,
  records, and providers. They do not initialize or spend against the lead's ledger.

**Limitation for the paper:** canned mock outputs establish local wiring and
deterministic scoring only. They cannot establish model resistance, defense
efficacy, the adequacy of the task/corpus sample, or live-model readiness.
The sandbox proof concerns the supported host configurations under decision
0023; it is not a proof about arbitrary operating systems or a public service.
Decision 0028 also preserves a measurement limit: malformed endings can leave
security endpoints unknown, and the one-tool-call-per-reply restriction
remains. The lead's forthcoming count-only diagnostics quantify those gaps;
these notes neither supply them nor change endpoint definitions.

Before the whole W8-T1 slice is complete: inspect the merged paid grid/smoke
summary and authorized raw evidence, resolve any task/oracle defects, incorporate
the reviewed variants, and apply the selected tier after the lead inputs. Only
then freeze the retained tasks, fixtures, policies, validators, system prompt,
tool descriptions, and sandbox launcher/profile identities through the Gate 3
process. This early draft computes no freeze hash and selects no tier.
