# 0039: Name the host environment in `protocol/active.json`, add it as a fourth late Gate 3 input, and fix the step's remaining input values

- Status: Proposed. Drafted with AI assistance; approved by the project lead by merging this record on November 14.
- Date: 2026-11-14
- Decision scope: Protocol (schedule and inputs, before the freeze)
- Secondary scopes: Governance
- Related specification sections: Sections 9, 10, 11, and 12
- Related records: [decision 0023](0023-tool-sandbox.md), [decision 0025](0025-full-study.md) item 12, [decision 0028](0028-restore-strength.md) item 9, [decision 0029](0029-gate-chain-shift.md) item 6, [decision 0031](0031-merge-on-green.md), [decision 0032](0032-tier-input.md), and [decision 0038](0038-gate3-report-module.md).
- Supersedes, for the words named only:
  - [decision 0038](0038-gate3-report-module.md) item 1's "For three inputs only" and "Until the Gate 3 step finishes, nothing else merges to `main` that changes a path in `runner/paid_run.py`'s `HASHED_DIRS`", for the one input in item 1 below;
  - decision 0038 item 6's `ENGINEERING` checkout ("a fresh checkout of `D_G`'s commit … its digest must equal `D_G`") and its `ENGINEERING` check "on `D_G`, `python -m analysis.gate3_hashes --check protocol/active.json`", which become `D_H`'s commit and the check on it, as item 3 below states;
  - decision 0038 item 6's outcomes ("the Gate 3 step runs at `ENGINEERING`", and the branch for a `D_G` not attested by 9:00 pm), wherever the host-environment PR has missed, as item 4 below states;
  - the same cutoff in `TASKS.md` that decision 0038 superseded, for the input in item 1 only.

  Nothing else in those records changes.

## Context

The Gate 3 step runs tonight, November 14. Checking every value the step passes to `analysis.active_protocol.generate(...)` against the committed sources found two gaps.

- **The host environment has no place in `protocol/active.json`.**
  - `SPEC.md` Section 11's Gate 3 row needs "code, container (or, for a host run, the host environment [decision 0029](0029-gate-chain-shift.md) names) … [to] reconcile in `protocol/active.json`".
  - Decision 0029 item 6 names it: the OS build, Python build, SQLite version, `uv.lock` hash, and sandbox launcher and profile hashes, read on the frozen commit. `container_digest` stays null.
  - `schemas/active_protocol.schema.json` has no field for any of these and refuses extra keys, and `generate()` drops unknown keys, as N-77-3 in the [whole-tree review](../reviews/2026-11-13-whole-tree.md) found for an unknown `empirical` key.
  - So no tier's step can meet that pass item on the current code, `ENGINEERING` included. Section 11's Gate 3 response would then apply, and none of the 1,092 planned official trials would run.
  - The committed `runner.paid_run._machine_facts` already reads all five values. Every sweep and C1 invocation writes them to its `code_provenance.jsonl` (`runner/execute.py`). Nothing compares them with a frozen value.
- **Some step inputs are committed nowhere.** No committed source fixes these values:
  - `protocol_id`, `protocol_version`, and `experiment_id`;
  - the schedule seed;
  - the schedule's protocol sentinel, which enters every trial and superblock ID and seeds each superblock's shuffle (`runner/schedule.py`), and whose default the sweep refuses;
  - the concurrency limit;
  - the `data_cutoff` string, the `budget_cap_usd` number, and the `accountable_roles` list;
  - the sweep and C1 spec files.

  A gate step runs committed code and builds nothing new (`TASKS.md`, gate steps), so these values are fixed here, before the step.

None of the 1,092 planned official trials has run. No evaluation, official, or C1 outcome exists.

## Options considered

1. **Run the step without the host environment.** Rejected: that fails a pass item, and the result would be `ENGINEERING` or `STOP`.
2. **Record the host environment only in the Gate 3 record, or shorten decision 0029's list.** Rejected. It weakens the freeze: no frozen machine-readable value would exist for the sweep's invocations to match.
3. **Add the field to `active.json`, with a committed check and the Gate 4 comparison, as a fourth late input.** Chosen.

## Decision

1. **A fourth late input.** This is a schedule decision before the freeze (`AGENTS.md`, "Change classification", third row). Decision 0038 item 1's window also admits the host-environment PR, opened by 7:00 pm and merged through 9:00 pm on November 14. Nothing else changes in that window.
2. **What the host-environment PR adds (lead scaffold).**
   - **Scope changes, recorded here before the host-environment PR opens:**
     - `W8-T3`'s `active.json` schema and generator gain a `host_environment` object;
     - `W8-T1`'s `tasks/freeze.json` is regenerated, because its `schema` group pins `schemas/active_protocol.schema.json`.

     Each owner keeps the slice, and their hours don't change. The project lead tells both owners in an informative notice that asks nothing.
   - **Schema.** `schemas/active_protocol.schema.json` moves to `schema_version` 0.2.0. It adds a required top-level `host_environment` object with exactly five string-or-null fields: `os_build`, `python_build`, `sqlite_version`, `uv_lock_sha256`, and `sandbox`, the values `runner.paid_run._machine_facts` reads.
     - `sandbox` is `tools.sandbox.describe()`: the launcher mode, the sandbox version, and the profile-rules hash.
     - The launcher's code, `tools/sandbox.py`, is pinned by `code_commit` and by `tasks/freeze.json`'s `sandbox` group.
   - **Generator.** `generate(..., host_environment=...)` copies the five fields and refuses any other key.
   - **Check.** `python -m analysis.gate3_hashes` prints `host_environment` read on the machine it runs on. `--check protocol/active.json` fails at every tier but `STOP` if any of the five fields is null or differs from that machine's value. It is run on the step machine.
   - **Gate 4 comparison.** `python -m analysis.gate3_hashes --check-run RUN --active protocol/active.json` fails unless every invocation line in `RUN`'s `code_provenance.jsonl` carries the same five values. Decision 0028 item 9's Gate 4 step runs it on every sweep and C1 run directory. It is built now so that it freezes with the analysis code.
   - **Tests.** They are failing-first, and the host values are injected, not read from the CI runner.
   - **Review.** `docs/reviews/2026-11-14-host-environment.md` (decision 0031 items 4 and 5) is committed in the host-environment PR. It names the digest of `main` once that PR merges, `D_H`, which is computed beforehand from the merged content. After the merge, the project lead prints the digest on `main`, confirms it equals `D_H`, and attests it.
3. **Order and fallback base.**
   - The merges go in this order:
     1. `D_G` is attested (decision 0038 item 2).
     2. The host-environment PR merges, and `D_H` is attested.
     3. The report module PR merges, and its review is attested.
   - Decision 0038 item 6's `ENGINEERING` checkout becomes `D_H`'s commit: `main` with only the report module PR reverted, whose digest must equal `D_H`. At `ENGINEERING`, `active.json` therefore also names the host environment, and `--check` on that checkout covers it.
   - At an empirical tier, decision 0038 item 1's "attested digest" is the final digest: `main` with all four inputs merged, attested after the report module's review.
   - A finding in the host-environment PR's review doesn't change whether the report module is done under decision 0038 item 6.
4. **If the host-environment PR misses.** Suppose it isn't merged by 9:00 pm, with `D_H` attested and 0 open blocking findings. That includes the case where `D_G` itself isn't attested, since the PR merges only after `D_G`. Then nothing is relaxed:
   - No commit without it can name the host environment in `active.json`. The host-environment pass item is therefore unmet at every tier, `ENGINEERING` included.
   - A smaller prefix doesn't repair code (Section 11, "Gate 3 fails"). So the Gate 3 response is `STOP`, committed as `protocol/active.json` at `STOP` and the Gate 3 record by 11:59 pm.
   - This outcome takes the place of decision 0038 item 6's `ENGINEERING` outcomes whenever the host-environment PR has missed, whether or not the report module is done.
   - This record adds no fallback that would treat that pass item as met some other way.
5. **The step's remaining inputs, fixed now and outcome-blind.** No evaluation schedule has been generated.

   | Input | Value | Source or reason |
   |---|---|---|
   | `protocol_id` | `CANARY-2026-F20` | — |
   | `protocol_version` | `1.0.0` | The sweep and C1 runs pass it as `--protocol-version` |
   | `empirical.experiment_id` | `canary-2026-sweep` | Names the sweep and the official C1 run |
   | `empirical.schedule_seed` | `CANARY-2026-sweep-20261114` | — |
   | Protocol sentinel (`protocol_sentinel` in both spec files) | `canary-2026-v1` | — |
   | `empirical.schedule_concurrency` | `1` | The runner executes one trial at a time, and the sweep and C1 runs never overlap |
   | `data_cutoff` | `2026-11-22` | `SPEC.md` Section 1 and decision 0030 |
   | `budget_cap_usd` | `10.0` | Decision 0032 item 8's funded cap: the Console workspace's monthly limit. The ledger cap just below it is recorded per invocation as `spend_cap_usd` |
   | `accountable_roles` | Two entries: `"project lead: the lead inputs, the estimand report module, the Gate 3 step, and the sweep's and C1 run's execution"` and `"the owner of each W8–W13 slice in TASKS.md"` | Decision 0032 item 9; no names (`SPEC.md` Section 12) |
   | `selection_reason_category` | `headcount ceiling` | Decision 0032 |
   | `active_contributor_count` | `6` | Decision 0032 item 3. The Gate 3 record states whether any disclaimer of the November 9 reply arrived; if one did, decision 0032 item 3 governs |
   | `common_hashes.container_digest` | null | Decision 0029 item 6 |

   - **The step commits two spec files.** `protocol/sweep_spec.json` and `protocol/c1_spec.json` are built from `active.json` and the sentinel. Each must pass `runner.sweep`'s or `runner.c1_trial`'s schedule refusal before the step commits.
   - **Every other value comes from a committed freeze or a committed command:**
     - the bases `eval-001` to `eval-020` and `corpus_hash`, from `corpus/freeze.json`;
     - `defense_hash`, from `defenses/freeze.json`;
     - the four common hashes, from `tasks/freeze.json` as regenerated by the host-environment PR;
     - the model, endpoint, reasoning effort, and `development_floor`, from `docs/evidence/gate2-2026-11-10/floor-count.json`;
     - `analysis_hash`, the fallback hashes, and `host_environment`, from `python -m analysis.gate3_hashes`;
     - `code_commit`, the commit the step runs on.
6. **Host stability.**
   - Automatic macOS updates stay off on the project lead's machine from the Gate 3 step through the end of the sweep, November 17. `os_build` includes the kernel version, so an update would make the frozen environment mismatch.
   - The sweep's Python is the project's virtual environment, the same one the step uses.
7. **Authorities.** Nothing is frozen, so this record's pull request updates every affected authority together:
   - `TASKS.md`'s dependency rule (the Gate 3 record entry), the gate-steps paragraph, the W8 gate-step row (which named "the CI container digest" against decision 0029 item 6), the `W8-T1` and `W8-T3` rows, and the November 14 lead-inputs row;
   - `STATUS.md`'s next-gate row;
   - `README.md`'s decisions row.

   `SPEC.md` doesn't change, and no protocol-deviation record is needed.
8. **Numbering.** This record takes 0039.

## Consequences

- **Added time.** About 1.5 hours for the project lead on November 14: the PR's review and its attestation, plus the two spec files at the step.
- **Three attestations tonight:** `D_G`, `D_H`, and the final digest.
- **The host-environment PR is on the critical path.** Without it, no tier's step meets Section 11's host-environment item.
- **At Gate 4**, a sweep or C1 invocation that ran in a different host environment fails `--check-run`, and decision 0028 item 9 governs.
- This record claims nothing about what any estimand will show.

## Verification

- The host-environment PR's tests fail on `main` before the change and pass after it.
- `python -m tasks.freeze --check` and the full suite pass on the PR.
- At the step, all of these pass: `python -m analysis.gate3_hashes --check protocol/active.json`, `python -m analysis.active_protocol --check protocol/active.json`, and both spec files' schedule refusals.
