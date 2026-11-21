# 0043: Let Gate 4 complete by November 23 after the November 20 time was missed, and re-date the release chain to the confirmed December 3 Demo Day, as `SPEC.md` Section 11's fourth recorded exception

- Status: Accepted. Approved by the project lead on 2026-11-21, and in force from this record's merge; drafted with AI assistance.
- Date: 2026-11-21
- Decision scope: Protocol (schedule, after the freeze)
- Secondary scopes: Governance; Release
- Related specification sections: the preamble, the Section 0 key-parameters table, and Sections 9, 11, 13, and 14
- Related records: [decision 0021](0021-two-week-shift.md), [decision 0025](0025-full-study.md) item 12, [decision 0027](0027-acceptance-by-work.md), [decision 0028](0028-restore-strength.md) items 4 and 8, [decision 0029](0029-gate-chain-shift.md) item 7, [decision 0030](0030-done-by-november-30.md), [decision 0031](0031-merge-on-green.md), [decision 0032](0032-tier-input.md), [decision 0036](0036-lead-output-wiring.md) items 5 and 6, [decision 0041](0041-license-and-author-order.md) item 5, [decision 0042](0042-gate4-late-evidence.md), and DEV-0009 in [`docs/protocol_deviations.md`](../protocol_deviations.md).
- Supersedes, for dates and the named rules only:
  - decision 0042 items 2, 4, and 5; item 9's 6:00 pm November 20 time and its three-name import list; and line 49's "the W11 and W12 dates";
  - decision 0030 items 4–10's dates (lines 54–119), including item 10's "nothing moves later", and item 7's read date (lines 81, 91, and 93);
  - decision 0029 item 7's dates only, and lines 98–99. Its frozen-bundle and pre-release-label rules stay in force;
  - decision 0028 line 75, and item 4's public release of the count-only tables;
  - decision 0036 item 6's November 20 date;
  - decision 0041's November 22 `LICENSE` trigger, item 5's November 23 commit, and line 51;
  - decision 0032 line 102;
  - decision 0031 line 65's turnaround end;
  - `TASKS.md`'s start rules for W12, W12's shortened week, and W13 inside the break, and every matching row, including the `W11-T3` and `W11-T5` `Depends` cells.

  Nothing else in those records changes. Every pass item, every Section 9 rule, and the November 22 data cutoff stay as written.

## Context

Times are Pacific. No sweep or C1 outcome was read to write this record.

| Deadline | Source | What happened |
|---|---|---|
| Gate 4 step and pass evidence, 11:59 pm Friday, November 20 | Decision 0042 item 2 | Missed. `W9-T3`'s Gate 4 evidence never arrived, and decision 0042's once-only exception lapsed |
| Count-only release path, November 20 | Decision 0036 item 6 | Missed |
| Demo Day | Decision 0030 item 10 | The event organizers confirmed to the project lead on November 21 that Demo Day is Thursday, December 3, 7:30–8:30 pm. The slot, time limit, and hardware access are unconfirmed |

Decision 0042 item 2 says that if the step missed November 20 too, nothing in that record moves it again, and Section 11's Gate 4 response applies as written. As written, that withholds every empirical comparison: all 1,080 sweep trials and the 12 official C1 trials.

On November 21, the project lead approved letting Gate 4 complete later with no pass item relaxed, and the lead-side `demo/trace.py` fixes.

This record weakens the study in ways decision 0042 didn't:
- it is the second after-the-fact move of Gate 4, and it lands past Gate 4's own November 22 absolute cutoff;
- official records exist, and the owners of `W9-T3`, `W11-T1`, and `W11-T4` have had raw access since November 17. This record doesn't claim they haven't read outcomes;
- the project lead has seen only what decision 0025 item 12 allows: completion counts, schema checks, cost, and provider errors.

## Options considered

1. **Apply Section 11 as written.** Rejected. It withholds every empirical comparison because an audit is late, even though no defect is known.
2. **Move Gate 4 later than November 23.** Rejected. Item 6's chain already runs to noon on December 2, the day before Demo Day, with no member date on Thursday, November 26. A later step would cut a member ask below 24 hours.
3. **Build an executor for the `ENGINEERING` fallback, so a Gate 4 failure could still fall back.** Rejected. The fallback's plan is frozen, but nothing in the repository writes its validation records, and `analysis/engineering_report.py` only renders the plan. Building one now would be new code after the freeze (`AGENTS.md`, change classification).
4. **Write a script that regenerates the count-only tables from the released bundle.** Rejected. The sanitizer content-addresses the canaries, arguments, raw responses, and observations that `analysis/diagnostics.py` reads in the clear, so the tables can't regenerate from what is released. A new script that generates final tables would also be a feature added after the freeze.
5. **Let Gate 4 complete by 11:59 pm Monday, November 23 with no pass item relaxed, remove the count-only tables from the public release, re-date the chain to Demo Day, and disclose it.** Chosen.

## Decision

1. **Merge time.**
   - This record merges by 1:00 pm Sunday, November 22.
   - Samson's `W9-T3` work counts for the scaffold choice (item 3) if it is complete and reviewed 24 hours after this record merges, and no later than 1:00 pm Monday, November 23.
   - The project lead's sanitizer merges, and is attested, right after that time. That leaves about 11 hours for the bundle, the audit, the step, and the outputs.
   - **"Data lock" means the trial and repair cutoff.** `SPEC.md`'s preamble, `TASKS.md`'s W11 heading and introduction, its Gate 4 repair item, and `W11-T3`'s "nothing crosses the data lock" are amended to say so.
2. **Gate 4 completes by 11:59 pm Monday, November 23.**
   - **What stands unchanged:** every pass item, every Section 9 rule, the Section 1 sentence forms, decision 0025 item 12's blinding, decision 0036 item 5's order, and decision 0031's lead-side review.
   - **The data cutoff stays 11:59 pm November 22.** No trial and no repair runs after it.
   - **Missingness is a per-comparison eligibility, not a gate-wide failure** (`SPEC.md` Section 9, the 5% threshold).
     - The audit's `missingness` item checks only that the accounting is complete.
     - Each headline comparison over 5% goes to the supported-results decision as ineligible. The audit prints `eligible_<comparison>: pass|fail`, which is completeness information decision 0025 item 12 allows. Secondary outcomes are reported with their ranges, but those come from `analysis/lead_outputs.py` after the audit passes, never from the audit.
     - `SPEC.md` Section 11's Gate 4 row and `TASKS.md`'s Gate 4 missingness item get this reading.
     - A C1 failure excludes C1 only.
     - The other pass items apply to the whole sweep: verify, the sanitized match, comparability, attempt histories, IDs, and resets.
   - **If one of those whole-sweep items is missing or fails at 11:59 pm November 23, or no headline comparison remains eligible, the response is `STOP`.**
     - The repair window has closed.
     - The `ENGINEERING` fallback has a frozen plan but no executor (option 3).
     - The project lead chose this outcome-blind on November 21.
3. **The lead scaffold.** Decision 0042 item 9 applies, changed as follows.
   - **Items the project lead may produce,** each only where Samson's work doesn't cover it by item 1's time:
     - the sanitizer v0.2.0;
     - the sanitized sweep and C1 bundles and their manifests, from `sanitize_bundle`, which the project lead runs outside any AI session;
     - the count-only audit `scripts/gate4_audit.py`, covering the sweep and C1, with pass-or-fail-only output;
     - the generated outputs, from `analysis/lead_outputs.py`, run outside any AI session after the audit passes (decision 0036 item 5).
   - **The audit's imports from `analysis/report.py`, exactly:**
     - the constants `THRESHOLD`, `SECURITY`, `UNIONS`, `CONDITIONS`, `BASELINE`, `GATE`, `MARKING`, and `ADAPTER_CONTRASTS`;
     - `Design` and `design_from`, which give the geometry from `active.json` and the corpus;
     - `endpoint`, whose value is tested only for null;
     - `_index`, which maps records to cells and refuses duplicates;
     - `_keys` and `_key_of`, the component keys;
     - `_counts`, base multiplicity.

     None computes a rate, estimate, or difference. One test pins the list, and another asserts that no value reaches stdout, stderr, or exception text.
   - **Dependencies.** `W11-T3`'s and `W11-T5`'s `Depends` cells read "`W9-T3`, or the lead's Gate 4 scaffold (decision 0043 item 3)". A dated lead-inputs row, 11:59 pm Monday, November 23, is added under `TASKS.md`'s rule for project-lead inputs, so a missing `W9-T3` merge doesn't block them.
   - **The code changes this needs in the built audit:** the `missingness` split in item 2, a C1 failure reported separately that doesn't fail the sweep, and a header that cites this item. Each gets failing tests first and its own review pass.
4. **The count-only tables leave the final public tables** (decision 0036 item 6's second outcome).
   - They can't regenerate from the released bundle (option 4).
   - Under Section 11, this supersedes decision 0028 item 4's public release of those tables. The project lead may still generate them from the raw runs as an internal check. They appear in no public table, number, or claim.
   - Decision 0036 item 6's November 20 date was missed, and this records it.
   - `normalized_args` stays content-addressed.
5. **A defect found after the cutoff** by anyone, including `W11-T1`, `W11-T4`, and `W12-T3`, can't be repaired. Under `SPEC.md` Section 9's repair block, the whole affected comparison is preserved and excluded. If the scope is uncertain, the whole affected experiment is. Cells aren't marked missing, because the finders have raw access. If no supported comparison remains, the response is `STOP`.
6. **The re-dated chain.**
   - Every member date moves later or stays put.
   - No member date falls on Thursday, November 26.
   - Every member ask has at least 24 hours from its input. The one exception is `W13-T5`'s freeze packaging, 18 hours after the README first screen. That is `TASKS.md`'s existing same-week exception for W13, carried over.
   - Same-week starts are named exceptions ([decision 0021](0021-two-week-shift.md)).

   | When | What |
   |---|---|
   | Sun Nov 22, 1:00 pm | This record merged; the data cutoff at 11:59 pm |
   | Mon Nov 23, 1:00 pm | Last time for Samson's work (item 1) |
   | Mon Nov 23, 11:59 pm | Gate 4 step and evidence; the provisional supported-results decision follows the step |
   | Tue Nov 24, 6:00 pm | Re-acceptance read for every re-dated row: `W11-T1`, `W11-T3`, `W11-T4`, `W11-T5`, and the W12 and W13 rows. Decision 0030 item 7's rules apply: acceptance by work doesn't apply to re-dated rows, its reassignment order holds, and every ask gives at least 24 hours' notice. `W11-T3` (3.0 hours, over the project lead's 2.5-hour cap, decision 0030 line 85) and `W12-T3` never go to the project lead |
   | Wed Nov 25, 6:00 pm | `W11-T1` and `W11-T4` merged. `W11-T4` gets about 42 hours after the provisional decision |
   | Wed Nov 25, 11:59 pm | The final supported-results decision; the approved result summary for the video; `W11-T5`'s `LICENSE` trigger, which moves from November 22. If `LICENSE` isn't on `main`, a visible reassignment is made and the project lead commits it by 6:00 pm Friday, November 27 |
   | Fri Nov 27, 6:00 pm | `W11-T3` binds the approved results; `W11-T5` integrates; `W12-T4`'s claim boundaries reach the project lead (48 hours after `W11-T4`; moved from November 23); W12 starts (a named same-week exception) |
   | Sat Nov 28, 6:00 pm | The paper leads' results-bearing draft |
   | Sun Nov 29, 6:00 pm | `W12-T3`'s numerical audit of that draft (24 hours) |
   | Sun Nov 29, 11:59 pm | The other W12 pull requests due, including `W12-T2` (about 54 hours after the `LICENSE` fallback) |
   | Mon Nov 30 | 6:00 pm: the project lead approves the final claim language, from `W12-T4`'s November 27 handoff; the paper leads' final manuscript draft (24 hours after the audit); W12 merged. 9:00 pm: the project lead approves every number. 11:59 pm: the Gate 5 step |
   | Tue Dec 1 | The Gate 5 failure response, if needed: one day, down from two, with fixes going to the project lead (decision 0031 line 87). W13 starts (a named same-week exception). 6:00 pm: `W13-T4`'s README first screen (24 hours after W12 merges). 7:00 pm: the judge-readiness drill (remote allowed). 8:30 pm: the dress-rehearsal recording |
   | Wed Dec 2 | 10:00 am: the make-up drill. Noon: the release freezes under one tag. Afternoon: a fresh checkout, `paid_run record`, and the live-first gate on the project lead's Mac. 5:00 pm: the confirmation-hardware rehearsal, replay-only unless it's the project lead's Mac |
   | Thu Dec 3, 7:30 pm | Demo Day |

   - Decision 0030's make-up, unmet, and last-resort rules carry over to these dates. The 48-hour turnaround runs through December 2.
   - **Samson's load from November 26 to December 1:** `W11-T3` 3.0 hours, `W12-T3` 4.5 hours, and `W13-T3` 1.0 hour, about 8.5 hours. Item 3 covers `W9-T3` if he doesn't deliver.
   - **If he doesn't re-accept on November 24:** `W13-T3` goes by decision 0030's order. `W11-T3` and `W12-T3` never go to the project lead, so another member must take them. If nobody takes `W11-T3`, no results are bound. If nobody takes `W12-T3`, decision 0030's last resort applies, and no unaudited number is released. That is the single biggest remaining risk to the results.
   - **Spend.** The rehearsal trials now fall in December. This supersedes decision 0032 line 102's "December's limit covers only them": December's limit covers the 30 rehearsal trials and the 3 stage trials, which is within the funded balance.
7. **Visible reassignment of the replay fixes.**
   - The project lead takes, from `W11-T5`, only the `demo/trace.py` fixes WT-11, WT-12, WT-13, N-66-1, N-66-2, and N-66-4. They have already passed review.
   - They were built on November 21, before this record. That order is disclosed (`AGENTS.md`, ownership and completion).
   - Miles keeps the slice and reviews them. Otherwise the lead-only review is a recorded limitation (decision 0031 line 154).
   - Demo wording gets its own Section 13 record before the freeze. Until the slot, laptop, and Wi-Fi are confirmed, the plan is replay-first.
8. **Section 11 and `SPEC.md`.** This is Section 11's fourth recorded exception, for the fall 2026 run only.
   - The protocol froze at Gate 3 on November 15, and none of that changes. The release artifacts aren't frozen yet.
   - This record supersedes `SPEC.md`'s preamble "never later" for these dates only: Gate 4, the final supported-results decision, Gate 5, and the release freeze. It is a change-control exception, not event logistics reopening a frozen artifact.
   - **Edits:**
     - the preamble and the Section 0 key-parameters row: the release freezes by "noon on Wednesday, December 2";
     - Section 11's readiness-gate sentence: "four recorded exceptions";
     - the Gate 4 row: Gate 4 on November 23 and the final decision on November 25; "November 22 absolute cutoff" becomes "November 22 data cutoff (trials and repairs)"; and item 2's missingness reading;
     - the Gate 5 row: November 30;
     - the "Gate 4 fails" response gets one sentence;
     - Section 14's paper and repository items: the release-freeze date.
   - This text isn't pinned (`tests/test_contract_lock.py`'s `FROZEN_SECTIONS`). `SPEC.md`, `TASKS.md`, and `docs/` are outside every frozen hash.
9. **Disclosure.** The Gate 4 record, `STATUS.md`, and the paper state:
   - both misses;
   - this second move, past Gate 4's own cutoff, with official records in existence, members with raw access, and the project lead blind;
   - which items the project lead built and ran, with no member review of the audit;
   - the removal of the count-only tables, which size a bias that can favor D2_DATAMARKING (decision 0028 lines 25 and 48). They are still computed internally and withheld from the public tables;
   - that the frozen `ENGINEERING` fallback had no executor at Gate 3 (`SPEC.md` Section 11, reproducibility acceptance criteria);
   - that the replay fixes came before this record.
10. **Deviation and version.** DEV-0009 is opened in this record's pull request.
    - It finds the date changes not material.
    - It assesses the count-only removal as a reporting change made outcome-blind: no estimand, scorer, threshold, or pass item changes.
    - The required response is claim removal: no claim that Gate 4 met any earlier time, and no count-only public table.
    - The `SPEC.md` header stays v1.24.0. `tests/test_c1_reference_policy.py` asserts it.
11. **Supersedes.** The list in this record's header, for dates and the named rules only.
12. **Lead hours.**
    - Sunday: the merge, in the November 22 rollup.
    - Monday: about 4 hours for the reviews, the bundle run, the audit, the step, and the outputs.
    - November 24 to December 2: about 1 hour for the re-acceptance read and reassignments, 1 hour for the final decision, 0.5 hours for the `LICENSE` fallback, 1.5 hours for number and claim approval, 1 hour for Gate 5, 1 hour for any Gate 5 fixes, and 2 hours for the freeze and the live-first gate. That's about 8 hours over two weeks, under the 10-hour trigger each week.
    - Totals go against decision 0031's 10-hour trigger. The project lead's cost is review and running commands.

## Consequences

- **What is lost.** No headline comparison is lost by this record. Without it, every empirical comparison is lost, because Gate 4 failed at 11:59 pm November 20. This record does remove two things:
  - decision 0028 item 4's count-only tables leave the public release (item 4);
  - a Gate 4 failure on Monday now means `STOP`, because `ENGINEERING` has no executor (item 2).
- **What is still at risk.** Every empirical comparison depends on Gate 4's evidence landing by 11:59 pm November 23. The biggest remaining risk is that nobody takes `W11-T3` and `W12-T3` if Samson doesn't re-accept on November 24 (item 6).
- **The project lead's added time** is about 4 hours on November 23 and about 8 hours from November 24 to December 2 (item 12).
- **The study's account of Gate 4 changes.** The paper reports a Gate 4 that moved twice after the fact, the second time past its own cutoff, under rules written after each miss, with official records in existence and unread by the project lead. This record claims nothing about what any estimand will show.

## Verification

- `tests/test_contract_lock.py`, `tests/test_c1_reference_policy.py`, `tests/test_status_consistency.py`, `tests/test_tasks_dependencies.py`, and the full suite pass on this record's pull request.
- At the step, `python -m runner.raw_manifest RUN --check MANIFEST` passes on both runs, and `python -m analysis.gate3_hashes --check-run` stays clean on both.
