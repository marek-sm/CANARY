# 0042: Let Gate 4's step and pass evidence complete through November 20, the final supported-results date, after the November 19 target was missed, as `SPEC.md` Section 11's third recorded exception

- Status: Proposed. Drafted with AI assistance. The project lead approves it by merging this record.
- Date: 2026-11-19
- Decision scope: Protocol (schedule, after the freeze)
- Secondary scopes: Governance
- Related specification sections: the preamble and Sections 9 and 11
- Related records: [decision 0015](0015-cut-process-rules.md) item 1, [decision 0025](0025-full-study.md) item 12, [decision 0027](0027-acceptance-by-work.md), [decision 0028](0028-restore-strength.md) item 8, [decision 0029](0029-gate-chain-shift.md) item 5, [decision 0031](0031-merge-on-green.md), [decision 0035](0035-s1-registered-followup.md), [decision 0036](0036-lead-output-wiring.md) item 5, [decision 0039](0039-gate3-host-environment.md), [decision 0040](0040-gate3-late-step.md), [decision 0041](0041-license-and-author-order.md) item 5, and DEV-0007 and DEV-0008 in [`docs/protocol_deviations.md`](../protocol_deviations.md).
- Supersedes, for the words named and only their times, not the rules around them:
  - decision 0029 item 5's "The project lead's provisional supported-results decision comes Thursday, November 19, the Gate 4 target";
  - `SPEC.md` Section 11's Gate 4 row's "November 19 target", for the fall 2026 run;
  - `TASKS.md`'s lead-decision row for "Thursday, November 19 (Gate 4 target …)", the gate-dates note, the W9 section's "The provisional supported-results decision is Thursday, November 19, the Gate 4 target", the club-week-12 row's Gate 4 target, and the Gate 4 section's "the target is Thursday, November 19".

  Nothing else in those records changes. In particular, the final supported-results decision's date (November 20), the absolute cutoff (November 22), and every pass item stay as written.

## Context

Times are Pacific. `SPEC.md` Section 11 sets Gate 4's dates as "November 19 target; November 20 final supported-results decision; November 22 absolute cutoff". Its pass evidence is the scheduled cells, missingness, comparability, IDs, hashes, resets, attempt histories, raw-to-endpoint recomputation, sanitized manifests, and generated outputs. Most of that evidence is `W9-T3`'s deliverable.

| Deadline | Source | What happened |
|---|---|---|
| `W9-T3` sanitizer pull request, November 15 | Decision 0029 item 5; decision 0040 | Not opened as of the evening of November 19 |
| `W9-T1`, `W9-T2`, `W9-T4`, `W9-T5` pull requests, November 16 | Decision 0029 item 5 | Not opened as of the evening of November 19 |
| `W9-T3` sweep, audit, and generated-results pull request, November 18 | Decision 0029 item 5 | Not opened, and no branch on the remote, as of the evening of November 19 |
| Gate 4 target and the provisional supported-results decision, November 19 | `SPEC.md` Section 11; decision 0029 item 5 | Missed |

Section 11 says "a missed gate reduces scope", with recorded exceptions only. The Gate 4 response permits only the Section 9 symmetric repair rule through November 22, the `ENGINEERING` fallback, or `STOP`. A late audit isn't a repair. So, as written, missing the November 19 target withholds every empirical comparison. That is all 1,080 sweep trials and the 12 official C1 trials.

Decision 0040, the second recorded exception, applied "only because its record merged before any official trial ran or any evaluation outcome existed". That can't be said here. The sweep and the official C1 run finished on November 16, and their raw records exist. This record rests on a narrower basis:
- no pass item, threshold, or claim rule changes;
- no date moves past one the rules already set;
- it merges before the project lead reads any sweep or C1 outcome.

What the project lead has seen is what decision 0025 item 12 allows: completion counts, schema checks, cost, and provider errors. The owners of `W9-T3`, `W11-T1`, and `W11-T4` have had raw access since November 17, as decision 0025 item 12 requires. This record doesn't claim they haven't read outcomes.

## Options considered

1. **Apply Section 11 as written.** Rejected. It withholds every empirical comparison because an audit is late, even though no defect is known.
2. **Move the final supported-results decision to November 22.** Rejected. `W11-T3`'s last push binds to that decision and merges by November 22. `W11-T4`'s claim-boundary audit, the video result summary, and the paper leads' results-bearing draft would then get under 24 hours, and the November 20–22 repair window would close before a defect could be found.
3. **Let the step and its evidence complete through November 20, change nothing else, and disclose it.** Chosen.

## Decision

1. **The miss.** Gate 4's November 19 result is "Not passed", recorded in `TASKS.md` as for Gates 1–3. The Gate 4 record, `STATUS.md`, and the paper say the target was missed and then moved. They never present it as met.
2. **The exception, for the fall 2026 run only, used once.** Gate 4's step may run, and its pass evidence may complete, through **11:59 pm Friday, November 20**. That is the final supported-results decision's existing date. If the step misses that time too, nothing in this record moves it again, and Section 11's Gate 4 response applies as written.
3. **Nothing else changes.**
   - Every Section 11 Gate 4 pass item stands, and so does every Section 9 rule: the 5% threshold per component, the repair block, and the hidden aggregate tables until all cells complete and integrity checks pass.
   - So do the `SPEC.md` Section 1 sentence forms and barred claims.
   - So do decision 0025 item 12's limits on what the project lead sees before the integrity checks pass, decision 0036 item 5's order, decision 0031's lead-side review, the November 22 cutoff, and the W11 and W12 dates.
4. **If any pass item is missing or fails at 11:59 pm November 20,** the Gate 4 response applies as written. It is chosen now, before any outcome is read by the project lead:
   - repair only for a defect an outcome-blind check shows to be localized (Section 9, the repair block);
   - otherwise the unchanged `ENGINEERING` fallback frozen at Gate 3 (`engineering_fallback` in `protocol/active.json`) under a new validation ID, if its validation can pass decision 0039's host comparison;
   - otherwise `STOP`.

   This Mac's `os_build` changed after the sweep (item 7), so `ENGINEERING` validation run here may fail that comparison. In that case the response is `STOP`, unless a separate record, written before any validation run, decides the host.
5. **The final decision.** This record doesn't move it. It comes the day `W11-T1` and `W11-T4` merge, no later than November 20 (decision 0028 item 8), so it follows the Gate 4 step, by 11:59 pm November 20. `W11-T4` audits claim boundaries "against the lead's supported results" and merges November 20. Without a November 19 provisional decision, that audit gets less than a day. The Gate 4 record states whether `W11-T1` and `W11-T4` had merged before the final decision.
6. **Order once the evidence exists.**
   1. The project lead runs `python -m runner.raw_manifest RUN --check MANIFEST` on both run directories, against `docs/evidence/raw-manifests-2026-11-18/`.
   2. The sanitizer and audit code merged for the step has an attested lead-side review with no open blocking finding (decision 0031).
   3. Only after the integrity checks pass does the project lead run `analysis/lead_outputs.py` over the raw sweep run (decision 0036 item 5).
7. **The host for any repair.** macOS updated itself to 27.2.1 on November 18, after decision 0039 item 6's window ended. `python -m analysis.gate3_hashes --check` now differs from `protocol/active.json` on `os_build` only. The sweep and C1 records aren't affected, because `--check-run` compares their stored provenance. No repair runs on this Mac without its own record, written before any repair scope is set. That record can't be outcome-blind toward members who have raw access, and it must say so.
8. **Methods cost, stated once.** Moving a gate time after it was missed weakens what the pre-registration commits to. It does so with official records already in existence, which decision 0040 didn't have to face.
   - The Gate 4 record, `STATUS.md`, and the paper state the miss and this record.
   - What limits the harm:
     - the time moves by one day, to a date the rules already set;
     - no pass item changes;
     - the project lead has read no outcome.
9. **A lead scaffold for two Gate 4 items, recorded before any work on it.** This follows decision 0029 item 2 and decision 0031 item 8, a visible scope change after the owner's date has passed, and decision 0041 item 5's visible reassignment, by analogy.
   - **Ownership.** `W9-T3` stays Samson's (decision 0027). The project lead takes only two scaffold items. Any later work by Samson counts toward the slice.
     - **The sanitizer fixes N-77-1, N-77-2, and N-77-11** in `analysis/sanitizer.py`. That file is outside `analysis_hash` but inside `runner/paid_run.py`'s `HASHED_DIRS`, so any attestation is redone on the new commit.
     - **A count-only audit,** `scripts/gate4_audit.py`. `scripts/` is outside every frozen hash. The audit imports only `THRESHOLD`, `_keys`, and `_counts` from `analysis/report.py`, and calls no `rate`, `_estimate`, or difference function. It computes missing over planned per arm and per component from scheduled cells against null endpoints. It also checks the sanitized-to-raw match, comparability, resets, attempt histories, and IDs.
   - **What the project lead sees.** The audit prints only pass or fail per item. A test asserts that its output holds nothing else (decision 0025 item 12). The project lead runs it outside any AI session, and no AI session runs it on official data.
   - **Attestation.** `runner.lead_review attest` binds only `code_digest`, which doesn't cover `scripts/`. So the review file's header and the Gate 4 record name the audit file's commit and SHA-256. Before running it, the project lead recomputes that hash and refuses on a mismatch.
   - **Which version is used.** Samson's work is preferred, because it is more independent. The project lead's scaffold is used only for an item that Samson's pull request doesn't cover, complete, by **6:00 pm Friday, November 20**. The project lead's `analysis/sanitizer.py` change stays off `main` until then, so it can't preempt or conflict with Samson's edit to the same file.
   - **Disclosure.** The Gate 4 record and the paper state which items the project lead built, ran, and checked, including a lead-built sanitizer checked by a lead-built match (`SPEC.md` Section 9), and that no member reviewed them. That adds to decision 0028 item 10's limitation on the lead's raw access.
   - **Time.** The project lead's November 20 total is about 4 hours: this record's merge, the raw-manifest re-check, reviewing up to two pull requests, the step, `lead_outputs`, the count-only release path, and the final decision. The week's total goes to the November 22 rollup against decision 0031's 10-hour trigger.
10. **Deviation entries.** This is a change after the freeze, so DEV-0008 is opened in this record's pull request before the step (decision 0015 item 1). It finds the change not material: no measurement, schema, oracle, scorer, estimand, threshold, or pass-evidence text changes, only a gate time. DEV-0007, in the same pull request, records decision 0028 item 8's in-sweep steps, which didn't run.
11. **`SPEC.md` Section 11.**
    - "the two recorded exceptions below" becomes "the three recorded exceptions below".
    - The Gate 4 row's target says that it moved after the fact to November 20 for the fall 2026 run.
    - The "Gate 4 fails" response adds this sentence: "For the fall 2026 run only, decision 0042 lets the Gate 4 step and its pass evidence complete through November 20, the final supported-results date, after the November 19 target was missed; it changes no pass evidence and no other date, and it merged before the project lead read any sweep or C1 outcome ([record](docs/decisions/0042-gate4-late-evidence.md))."
    - This text isn't pinned (`tests/test_contract_lock.py`'s `FROZEN_SECTIONS`). DEV-0008 finds the change not material, so `SPEC.md` stays at v1.24.0, as decision 0035's post-freeze documentation edit kept it. `tests/test_c1_reference_policy.py` asserts that header, and its SHA-256 is pinned in `tasks/freeze.json`.
    - `SPEC.md`, `TASKS.md`, and `docs/` are outside every frozen hash (`runner/paid_run.py`'s `HASHED_DIRS` and `analysis/gate3_hashes.py`).
12. **Authorities updated in this record's pull request:**
    - `SPEC.md`, as item 11 says;
    - `docs/protocol_deviations.md`'s header count, DEV-0007, and DEV-0008;
    - `TASKS.md`: the lead-decision row for November 19, the gate-dates note, the W9 section, the club-week-12 row, and the Gate 4 section;
    - `README.md`'s decisions row.

    `STATUS.md` changes in the November 22 rollup.
13. **Numbering.** This record takes 0042.

## Consequences

- **What is still at risk.** Every empirical comparison depends on Gate 4's evidence landing by 11:59 pm November 20. `W9-T3`'s owner keeps the slice (decision 0027).
- **The project lead's added time** is about 4 hours on November 20, as item 9 itemizes.
- **The study's account of Gate 4 changes.** The paper reports a Gate 4 that ran up to one day after its target, under a rule written after the miss, with official records in existence and unread by the project lead. This record claims nothing about what any estimand will show.

## Verification

- `tests/test_contract_lock.py`, `tests/test_c1_reference_policy.py`, `tests/test_status_consistency.py`, `tests/test_tasks_dependencies.py`, and the full suite pass on this record's pull request.
- At the step, `python -m runner.raw_manifest RUN --check MANIFEST` passes on both runs, and `python -m analysis.gate3_hashes --check-run` stays clean on both.
