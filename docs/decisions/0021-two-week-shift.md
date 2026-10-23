# 0021: Two-working-week shift of W7 onward: Gate 3 on November 11, data cutoff November 22, release freeze December 6

- Status: Accepted. Approved by the project lead on 2026-10-23; drafted with AI assistance.
- Date: 2026-10-23
- Decision scope: Protocol
- Secondary scopes: Governance, Release
- Related specification sections: the preamble, Sections 0, 2, 9, 11, 12, 13, and 14
- Supersedes: decision 0011 items 1 and 5, item 3's lattice-week table (its W10 fold and work moves stand), item 4's first two bullets (dates only; its third bullet stands), and item 9's October 28 date; decision 0012 item 6's "with no second slip" reference and item 7's dates; decision 0017 items 6 and 7 (dates only; the October 25 judge-drill practice round is unchanged); the `TASKS.md` weekly-cadence clause that a yellow item never extends the November 8 data cutoff or November 22 release freeze; and the `TASKS.md` statement that week 15 is frozen-package staging and rehearsal only.

## Context

State on October 22, at `15aea3d`:

- **Week 6.** `W6-T3` (#47), `W6-T4` (#25), and `W6-T5` (#28) are merged.
  - `W6-T1` (#32) was approved on October 12, has had no push since, and conflicts with `main`.
  - `W6-T2` (#34) passed the project lead's source review on October 22, with two changes and the sign-off push left.
- **Week 7.** No slice has merged.
  - `W7-T3` (#49) has a change request from October 18, and `W7-T4` (#54) has no review.
  - `W7-T1`, `W7-T2`, and `W7-T5` have no pull request.
  - Every W7 slice is `BLOCKED` on `W6-T1` or `W6-T2`.
- **Week 8.** No pull request is open. They were due October 22.
- **Lead scaffold.** Tool-result delivery, the `task_order` file, the corpus-record schemas, and the `dev-001` re-render are built and wait only on #32 and #34.
- **Decision 0011 item 5 has fired.** The live-model development grid can't merge by October 23, so as things stand, the October 28 Gate 3 choice is `ENGINEERING` or `STOP`. With `ENGINEERING`, CANARY would give no evidence about either defense, which is the purpose decisions 0016 and 0017 set.
- **Turnaround is the binding constraint, not the calendar or the size of the work.**
  - With AI-assisted implementation, building a slice is rarely the slow step. Work waited on turnaround instead: an approved pull request has waited ten days unmerged, and replies to review comments have taken several days.
  - Moving dates without changing how work moves only moves the failure.
- **The calendar.**
  - `SPEC.md` says all its dates are protocol dates, and none is tied to an outside event.
  - Demo Day and paper delivery fall in club week 16, December 7–11. Week 14 (Thanksgiving, November 23–29) is unavailable.
  - `TASKS.md` keeps week 15 for frozen-package staging and rehearsal, so that no substantive work relies on the week before the event.
- **No pins are affected.** Decision 0009 leaves the gate dates unpinned. Section 11's freeze heading already says "the week-8 freeze" names the Gate 3 freeze, whatever club week it falls in.

## Options considered

1. **Keep the dates; Gate 3 chooses `ENGINEERING` on October 28.** Rejected. It removes the defense comparison that gives CANARY its purpose.
2. **Re-date with no change to turnaround.** Rejected. The slip came from turnaround, not from the size of the work, so new dates alone would slip the same way.
3. **Hold the November 22 release freeze.** Rejected. Club weeks 10–13 give four working weeks for six lattice weeks (W7, W8, W9, W11, W12, W13), which needs two folds. Folding W11 and W12 together puts W12 on same-week W11 work and the W11 audits after the data cutoff, which is what decision 0011 option 4 rejected.
4. **Count week 14 as working time.** Rejected. The team is away; `TASKS.md` keeps week 14 dark.
5. **Shift every lattice week two working weeks later, once, with a 48-hour turnaround rule for every owner.** Club weeks 10–13 and 15 give five working weeks for the six lattice weeks, so one fold remains: W12 and W13 share club week 15, and the release freeze is Sunday, December 6. Because week 14 is dark, W12 lands three club weeks later. **Chosen.**

## Decision

1. **Effective on merge, October 23.** The October 24 Gate 2 step under decision 0011 item 5 does not run; the step moves to October 31 (item 3). The record has no outside condition: the release freeze falls before the Demo Day week (December 7–11) whichever day the event takes, and the designated paper leads are told the item 7 dates.

2. **Lattice weeks and club weeks.**

   | Lattice week | Club week | Dates |
   |---|---|---|
   | W7 | 10 | October 26–November 1 |
   | W8 | 11 | November 2–8; Gate 3 step Wednesday, November 11 |
   | W9 | 12 | November 9–15 |
   | W10 | — | Folded (unchanged, decision 0011 item 3) |
   | W11 | 13 | November 16–22 |
   | — | 14 | November 23–29, unavailable |
   | W12 | 15 | Monday, November 30–Wednesday, December 2 |
   | W13 | 15 | Thursday, December 3–Sunday, December 6 |

   The W6 slices still open close in what remains of club week 9. `W7-T2`'s evaluation intake may start on the day `W6-T2` merges, which restates the October 7 early-intake exception for this week. No W7 slice without an open pull request starts before Monday, October 26.

3. **Gates and fixed dates.**
   - **Gate 2 step:** Saturday, October 31, on work merged by Friday, October 30. Gate 2 keeps its October 11 date and its "Not passed" record; only the step moves, as in decision 0011.
   - **Project lead's tier, budget, model, and decoding input:** Sunday, November 1.
   - **Gate 3 step:** Wednesday, November 11. W8 work not merged by Friday, November 6 may merge through Tuesday, November 10. W8 work merged by November 6 doesn't change after that, except for the decision 0012 wiring in item 5.
   - **Gate 4:** Sunday, November 15 target. The absolute data cutoff is Sunday, November 22.
   - **Gate 5 step:** Thursday, December 3.
   - **Public release freeze:** Sunday, December 6, under one immutable tag and commit.
   - Gate 1's and Gate 2's recorded results don't change.

4. **Cadence rules and exceptions.**
   - **New: 48-hour turnaround.** From Monday, October 26 through December 6, every owner answers review comments, merge conflicts, and questions on their own pull requests within 48 hours, or sooner where a row's date requires it, as in W12's shortened week. This extends the `TASKS.md` 48-hour review service level from reviewers to authors.
   - **Carried over from decision 0011:**
     - The Gate 3 step's Wednesday date and Tuesday merge cutoff.
     - `W9-T3`'s sweep starting on the Gate 3 record. Its sanitizer pull request is due Thursday, November 12. Its sweep, audit, and generated-results pull request is due Saturday, November 14, and is reviewed by the morning of Sunday, November 15. The supported-results decision is Sunday, November 15.
   - **New: W12's shortened week.** `W12-T4`'s claim boundaries are due Monday, November 30, so the project lead can approve the final claim language on Tuesday, December 1. The other W12 pull requests are due Tuesday, December 1, and every W12 pull request is reviewed by Wednesday, December 2. The Gate 5 step runs Thursday, December 3 instead of on a Saturday.
   - **New: W13 inside club week 15.** The W13 rows start on W12 work merged by Wednesday, December 2. Inside W13, `W13-T4`'s README first-screen assembly (item 8) merges by Saturday, December 5, and `W13-T5`'s release freeze includes it. These are the only same-week slice dependencies this record adds, and no other row may plan around same-week work. The judge-readiness drill runs Saturday, December 5. Gate 5's drill item is checked at the release freeze rather than at the Gate 5 step.
   - **Gate 5 repair window.** If Gate 5 fails, the Section 11 Gate 5 response runs on December 4–5. Anything still broken is removed. The release freeze never moves into club week 16.

5. **Decision 0012 wiring.** The project lead adds the two outputs to `W8-T3`'s merged report code by Tuesday, November 10, as an additive change that alters no existing output, and tells `W9-T3`'s owner at the November 6 review cutoff. If the wiring isn't on `main` by November 10, decision 0012 item 7's withdrawal applies before the Gate 3 step.

6. **Slip rule. There is no third move.**
   - If `W7-T3`'s live-model development-grid records aren't merged by Friday, October 30, no comparable D0_BASELINE baseline is ready, and the Section 11 Gate 2 response makes the November 11 Gate 3 choice `ENGINEERING` or `STOP`. Mock runs never count.
   - If `W7-T4`'s readiness script isn't merged by then, neither defense passes Gate 2, and Section 12 step 3 applies.
   - A Gate 3 miss on November 11 takes the Section 11 Gate 3 response.
   - The November 22 cutoff is absolute. A late W11 merge can't use week 14.
   - A yellow item never extends the November 22 data cutoff or the December 6 release freeze.

7. **Lead and outside inputs, re-dated.**

   | Input | Was | Now |
   |---|---|---|
   | Tier, budget, model, and decoding | October 25 | November 1 |
   | Gap sentence or its absence, with reference 15 resolved (decision 0017 item 6) | October 25 | November 8 |
   | License choice and author order | November 1 | November 8 |
   | Gate 3 record | October 28 | November 11 |
   | Supported results | November 1 | November 15 |
   | Manuscript draft (paper leads) | November 2 | November 16 |
   | Approved result summary for the video | November 8 | November 22 |
   | Confirmed demo hardware (organizers) | November 16 | November 30 |
   | `W12-T4` claim boundaries to the project lead | November 15 | Monday, November 30 |
   | Final claim language, including the paper's close (decision 0017 item 7) | November 15 | Tuesday, December 1 |
   | Final manuscript draft (paper leads) | November 16 | Thursday, December 3 |

   The paper leads draft against the November 16 date in the table, which replaces decision 0017 item 7's October 26 to November 1 drafting window. The paper is submission-ready at the release freeze, December 6, and is delivered on Demo Day.

8. **Work moves.**
   - **Planned pull-forward into club week 13.** These are W12 parts whose inputs are merged before Monday, November 16. If they slip, they run in week 15.
     - `W12-T1`'s frozen tool and task test re-run.
     - `W12-T2`'s source re-verification.
     - `W12-T4`'s defense, authorization, and containment re-runs.
   - **Named pull-forwards.** Each uses only work merged before that week's Monday. `TASKS.md` keeps pull-forward optional; these are the planned use of that time, and the club week 12 and 13 schedule assumes them. If one slips, its work stays in its own week and its owner's dates don't move.
     - `W9-T3`'s sanitizer is built and tested on merged development and grid records in club week 11.
     - `W9-T5`'s pre-results paper assets that use only `W5-T5`'s shells move to club week 11.
     - `W11-T5`'s `LICENSE` moves to club week 12, from the November 8 license choice. `CITATION.cff` stays in `W11-T5`, because it reads the W9 consents.
   - **Visible reassignments, re-accepted with the Monday, October 26 post (item 11).** Both move fixed-cost release work toward T1 and T4, as the capacity arithmetic already plans.
     - `W13-T5`'s README first-screen assembly moves to `W13-T4`.
     - `W12-T5`'s Section 13 failure-mode rehearsal moves to `W12-T1`.
   - **Pairing.** T4 pairs on `W7-T2`'s candidate search under the cadence's explicit-pairing rule. T2 remains the owner, and the project lead remains the source reviewer, reviewing candidates as they arrive.
   - **No member hours are removed.** Estimates move with the work.

9. **Section 13 rehearsal.**
   - Presentation-equivalent hardware is rehearsed in club week 15.
   - The confirmation-hardware rehearsal and the live-first rehearsal gate run in club week 16 before the event, as presentation work on the frozen package under the existing rehearsal allowance.
   - The planned presentation is replay-first unless that gate passes.

10. **`SPEC.md` moves to v1.15.0, with unpinned text changes only.**
    - The preamble's date paragraph and Section 0's fixed-scope table.
    - Section 2's static-page dates.
    - Section 11's statement that the week-8 freeze names Gate 3 now carries November 11.
    - Section 11's freeze heading paragraph, gate table, and Gate 4 response.
    - Section 13's rehearsal weeks.
    - Section 14's paper and release-tag dates.

    No frozen artifact or outcome exists, so there's nothing to rerun and no `docs/protocol_deviations.md` entry.

11. **Re-acceptance.** Every owner re-accepts their re-dated slices by replying to the Monday, October 26 post (decision 0015), including the reassigned items in item 8. An owner who doesn't re-accept leaves that slice `BLOCKED` under the `TASKS.md` ownership rule until a visible reassignment, tier, cut, or schedule decision is recorded.

12. **Numbering.** This record and its `SPEC.md` version follow merge order: if another record merges first, this one takes the next free number and minor version before it merges.

## Consequences

- **The week-15 buffer is gone.** The plan kept it so that no substantive work would rely on the week before the event. This record says openly that some now does: W12 and W13 run in club week 15, and only the Section 13 rehearsal falls in week 16.
- **The paper leads' last window shrinks.** It runs from the December 1 claim language to the December 6 freeze. The project lead tells them the item 7 dates when this record merges.
- **`W6-T1` (#32) is the single point of failure.** It blocks almost every W7 slice and the lead scaffold. If #32 hasn't merged by the night of Sunday, October 25, the project lead opens a replacement pull request on Monday, October 26 from its commits that keeps their authorship (the #47-from-#31 precedent), as a visible reassignment with T4 reviewing.
- **The project lead's tightest week is club week 10,** with rolling source review of about 14 candidates, the Gate 2 step, and the tier decision.
- **The schedule depends on turnaround.** It sets no hours assumption; the `TASKS.md` estimates predate AI-assisted work and remain relative sizes. It does assume the 48-hour turnaround in item 4 and the pull-forwards and reassignments in item 8. A missed date on the critical path triggers the item 6 slip rule, never another move.
- **The data cutoff falls right before the dead week.** Supported results land on November 15 and the approved summary on November 22, so the paper leads and the video have results before the break.

## Verification

- `tests/test_contract_lock.py`, `tests/test_corpus_rules_freeze.py`, and `tests/test_request_effect.py` pass unchanged, which shows no pinned `SPEC.md` text changed.
- `tests/test_tasks_dependencies.py` passes. Because it compares slice IDs, not club weeks, a manual check confirms that no row plans around same-week work beyond the exceptions in item 4.
- `tests/test_status_consistency.py` passes against the October 25 rollup.
- `SPEC.md`'s Section 0 table and Section 11 gate table read November 11, November 15 and 22, December 3, and December 6. `TASKS.md`'s week headings, gate steps, lead and outside inputs, slice tables, and club-week milestones match this record. The W7 heading keeps its October 12–18 text, because `TASKS.md` and `STATUS.md` link to its anchor; a dated note under it carries the new W7 dates.
- `paper/lead-inputs.md` names the December 1 claim language, and `paper/venue-checklists.md` names the November 1 tier input and the November 8 license choice.
