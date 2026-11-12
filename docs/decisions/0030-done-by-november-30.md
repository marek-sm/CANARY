# 0030: Finish by Monday, November 30: move the post-cutoff work seven days into the Thanksgiving break, correct the club-week numbering, and keep `F20`

- Status: Accepted. Approved by the project lead on 2026-11-07; drafted with AI assistance. Review sentences amended by [decision 0031](0031-merge-on-green.md). Item 9's first bullet superseded by [decision 0032](0032-tier-input.md).
- Date: 2026-11-07
- Decision scope: Protocol
- Secondary scopes: Governance, Release
- Related specification sections: Sections 0, 9, 11, 12, 13, and 14
- Supersedes, for dates and the sentences named only:
  - Decision 0021: the week table's W12, W13, and club week 14–16 rows; item 3's Gate 5 date of December 3 and release freeze of December 6; item 4's W12 dates (November 30, December 1, December 2), W13 dates (December 2 and December 5), the December 4–5 repair window, and "club week 16"; item 6's "A late W11 merge can't use week 14" and the yellow-item "December 6"; item 7's rows dated November 30, December 1, and December 3, and its closing "December 6"; the 48-hour turnaround's "through December 6"; the club weeks item 8 gives its named pull-forwards; item 9's rehearsal timing; and the premise that Demo Day falls in December 7–11.
  - Decision 0022: item 1's "W13 keeps decision 0021's named same-week start inside club week 15"; item 4's Gate 5 date, its release-freeze date, and, only in item 7's cases below, "and still after the judge-readiness drill and the paper leads' final draft"; and item 5.
  - Decision 0029: item 5's and item 9's "The W12 pull-forwards move into club week 15"; item 7's reading of the Demo Day window, its 48-hour re-plan trigger and the re-dating it orders, and "never adds work in club week 14"; and option 5's reasoning, as far as it rejects re-planning before the date is confirmed. Item 7's rules that Demo Day shows only outputs from the frozen sanitized bundle and labels any earlier number pre-release stay in force.

## Context

**What this record costs, first.**

- **No scientific scope changes.** The Gate 2 close (end of November 10), the tier input (November 11), Gate 3 (November 14), the sweep (November 14–17), Gate 4 (November 19, with the final supported-results decision November 20), and the November 22 data cutoff all stay as decision 0029 set them. The target stays `F20`, and the paper, video, replay, README, and live-first gate all stay.
- **The Thanksgiving break, November 23–29, becomes working time.** W12, the Gate 5 step, W13, and the release freeze move exactly seven days earlier, into it. That was the season's only slack week. W12 now starts the day after the cutoff.
- **The pre-event rehearsal shrinks to one day.** It is Sunday, November 29, on the frozen tag. The rehearsal allowance is spent that day, so any later rehearsal is replay-only.
- **Owners re-accept their W12 and W13 rows,** and a row nobody accepts gets a visible reassignment by November 15.

**The project lead's direction (November 7).** CANARY is complete by Monday, November 30. That means the release is frozen, the paper is final, and the demo is rehearsed.

**The club-week numbering.** Thanksgiving week, November 23–29, is an unnumbered break in the club calendar. Club week 14 starts Monday, November 30, and club week 15 is December 7–13. From Thanksgiving onward, this repository's labels "club week 14", "15", and "16" for November 23–29, November 30–December 6, and December 7–13 are each one off. Weeks 1–13 are unchanged.

**What that does to the Demo Day window.** Club research leadership's November 5 message put Demo Day in club weeks 14–15, date to be confirmed. Decision 0029 read that as November 23–December 6. Under the correct numbering it is November 30–December 11, so Monday, November 30 is the earliest possible date.

**Why the current schedule can't stand.**

- Decision 0021's schedule, kept by 0029, freezes the release on Sunday, December 6.
- It runs the `SPEC.md` Section 13 confirmation-hardware rehearsal in the week after that.
- It keeps November 23–29 dark (decision 0022 item 5).

None of that fits a November 30 event.

## Options considered

1. **Keep the December 6 freeze.** Rejected. It misses the project lead's November 30 direction and the earliest Demo Day date.
2. **Pull the data cutoff or Gate 4 earlier.** Rejected. W11's audits already have only November 18–20, and repair has November 20–22. Shortening either weakens the evidence.
3. **Wait for the confirmed date, as decision 0029 option 5 chose.** Rejected. The earliest date is already known, and any later date only adds rehearsal days.
4. **Move everything after the cutoff exactly seven days into the break, return W12's named pull-forwards to club week 13, and keep every gate before the cutoff.** **Chosen.** It loses no scope, and each post-cutoff step keeps its length.

## Decision

1. **Numbering.** From November 23, the repository uses the club's numbering: November 23–29 is the Thanksgiving break, club week 14 is November 30–December 6, and club week 15 is December 7–13. Live documents use dates first. Earlier decision records keep their wording as history.

2. **Unchanged.** The decision 0029 chain through the November 22 cutoff is unchanged. That covers the Gate 2 close, the tier input, the W8 freezes, Gate 3, the sweep, W9, Gate 4, W11, and the cutoff. So are decision 0029 items 1–6 and 8, and decision 0025 item 6's `W7-T2` dates.

3. **W12's named pull-forwards return to club week 13.**
   - The three named pull-forwards are `W12-T1`'s frozen tool and task test re-run, `W12-T2`'s source re-verification, and `W12-T4`'s defense, authorization, and containment re-runs. Their inputs merge before November 16 (decision 0021 item 8), and they need no Gate 4.
   - They run November 16–22 as optional pull-forward for the W11 owners. If they slip, they run inside W12.

4. **W12 runs in the break.**
   - W12 starts Monday, November 23. `W12-T4`, whose only slice input is `W11-T4`, may start earlier under decision 0022 item 1's conditions: Gate 4's integrity checks pass, `W11-T1` and `W11-T4` have merged, and no repair is pending.
   - `W12-T4`'s claim boundaries reach the project lead Monday, November 23.
   - The project lead approves the final claim language Tuesday, November 24.
   - W12 pull requests are due Tuesday, November 24, and reviewed and merged by Wednesday, November 25.
   - `W12-T1`'s finished video and the Section 13 failure-mode rehearsal are part of its November 24 pull request.
   - No member due date falls on Thursday, November 26.

5. **Gate 5 and W13.**
   - The Gate 5 step runs by the end of Thursday, November 26, on W12 work merged by Wednesday, November 25. It is the project lead's only due item that day.
   - If Gate 5 fails, the Section 11 Gate 5 response runs Friday, November 27 and Saturday, November 28.
   - W13 starts Thursday, November 26, on W12 work merged by Wednesday, November 25, with nothing due before Saturday, November 28. That is decision 0021's same-week exception, now inside the break.
   - `W13-T4`'s README first screen merges by Saturday, November 28.
   - The judge-readiness drill runs Saturday, November 28, with every portfolio owner, without notes. It may be held remotely.
   - A full-length dress-rehearsal recording, the last audiovisual fallback in Section 13, is made that day.
   - The release freezes under one immutable tag and commit by noon on Sunday, November 29, and never later.
   - The 48-hour turnaround runs through November 29.

6. **Lead and outside inputs.**
   - **Event organizers:** the confirmed Demo Day date, slot, time limit, and hardware access, by Monday, November 23 (was November 30). They are recorded in `TASKS.md` with the fields `docs/DEMO_DESIGN.md` names.
   - **Paper leads:**
     - The manuscript draft stays Monday, November 16, with no result numbers (decision 0029 item 5).
     - A results-bearing draft by Monday, November 23, with numbers generated from the bundle. This is a new input, which `W12-T3`'s numerical-claim audit checks by November 24.
     - The final manuscript draft by Wednesday, November 25 (was Thursday, December 3).
     - The project lead approves every result, number, and limitation in it by November 25. This is a Gate 5 item.
   - **Project lead:** the approved result summary for the video stays Sunday, November 22.

7. **Owners, reassignment, and what replaces a cut.**
   - **Acceptance.** Every W12 and W13 row is re-dated, and its owner re-accepts it by a reply, in the team-channel thread or to the project lead. No work on those rows can start before the read, so decision 0027's acceptance by work doesn't apply here. The project lead reads acceptance Sunday, November 15. A row not accepted then is `BLOCKED` and gets a visible decision that day: reassignment to another portfolio owner first, the project lead second.
   - **Limits on reassignment.**
     - `W12-T3`, the numerical audit of the lead's results, and `W12-T4`, the claim boundaries the lead approves, never go to the project lead.
     - A slice the project lead builds keeps its standing-pair member reviewer. Any lead-only review is recorded as a limitation, as decision 0029 did for the stop rule.
     - The project lead takes at most one reassigned slice estimated at 2.5 hours or less.
   - **Last resort.** If nobody can take a slice, the Gate 5 item it serves is recorded failed, and the Section 11 Gate 5 response applies. Any claim that slice gates is withheld from the release:
     - an unaudited number isn't released;
     - without `W12-T4`'s boundaries, the release uses only the Section 1 predeclared floor wording.

     `W12-T1` through `W12-T4` have no defer-first item, so this takes its place.
   - **Drill.** A make-up drill runs Sunday, November 29, by 10:00. If an owner still misses it, the freeze runs anyway, and the drill item is recorded unmet for that owner in `TASKS.md` and `STATUS.md`.
   - **Consent.** If an owner hasn't confirmed publication consent, the W9 consent submitted November 16 stands. With no consent at all, that person isn't publicly named beyond what Section 0 allows.
   - **Paper.** If the paper leads' final draft hasn't arrived by Saturday, November 28, the freeze includes the latest draft that passed `W12-T3`'s audit and the project lead's number approval, and the paper item is recorded unmet.
   - Decision 0022 item 4's ordering of the freeze after the drill and the final draft yields only in these three cases.

8. **The live path and the Section 13 rehearsals.**
   - **The rehearsal command.**
     - No runner command runs the excluded demo case live today. Only `execute.run_schedule` takes `analysis_role`, and `runner/sweep.py` forces the evaluation split.
     - The project lead adds that command as lead scaffold, tested on the mock provider, and merges it with the W8 work by Friday, November 13. The Gate 3 freeze then includes it, and it is not a feature added after the freeze (Section 16).
   - **Where live calls run.** Live trials run only on the project lead's Mac, and the key never leaves it (decision 0023 item 8; decision 0028 item 7).
   - **Sunday, November 29.** After the noon freeze:
     1. the project lead makes a fresh checkout of the tag;
     2. runs the mock grid and `python -m runner.paid_run record`;
     3. commits the record on a branch on top of the tag, not inside it;
     4. runs the Section 13 live-first gate: ten dry runs over the three retained configurations, from the 30-trial rehearsal allowance.
   - **The confirmation-hardware rehearsal** runs before the event on the organizers' hardware. It is replay-only unless that hardware is the project lead's Mac. If access isn't confirmed by November 23 or isn't available on November 29, the rehearsal runs replay-only on presentation-equivalent hardware, and the item is recorded unmet in `TASKS.md` and `STATUS.md`.
   - The presentation is replay-first unless the live-first gate passes.
   - Every rehearsal after November 29 is replay-only.
   - `W13-T5`'s live dry runs execute on the project lead's Mac, a visible reassignment of execution only, like the paid commands in `TASKS.md`'s October 28 note. Miles keeps the slice.

9. **Spend and the development-trial count.**
   - The workspace limit and the spend cap rise by Tuesday, November 10, before the November 11 tier input, recorded in `STATUS.md` first (decision 0028 item 7). The Section 9 budget equation at `F20` needs about $90.50 of funded balance at the decision 0028 bound.
   - Rehearsal trials fall on November 29. The three stage trials fall on Demo Day. If that is in December, the December monthly limit covers only them, and the ledger on the project lead's Mac keeps the season's total.
   - The development-trial count, recounted November 7, fits with no change. It is 107: the October 10 check, decision 0026's live check, the 90-cell grid, and the 15 coverage smokes. The ten live task-variant checks bring it to 117, the figure decision 0026 set for decision 0025 item 7, within Section 9's ceiling of 120.

10. **A Demo Day on a confirmed date.**
    - **After November 30:** nothing moves later. The extra days carry replay rehearsal only, and the package stays frozen.
    - **Before November 30, inside the break:** a follow-up record within 48 hours decides what is cut and states it publicly. It never moves the cutoff or Gate 4.
    - **Whatever the date:** Demo Day shows only outputs from the frozen sanitized bundle, replay-first, as decision 0029 item 7 requires.

11. **Numbering and version.** This record takes 0030. `SPEC.md` moves to v1.21.0. Only unpinned text changes: the release-freeze date, the Gate 5 date, the Section 13 rehearsal timing, and the Section 14 delivery dates.

## Consequences

- **The team works through Thanksgiving.** Owners hear it on November 8, more than two weeks ahead, and re-accept or decline by November 15.
- **Capacity.**
  - W12 and W13 carry 28 member hours in the break, about 5.6 per owner.
  - The project lead's break-week work comes to about 6–7 hours: claim language, number approval, Gate 5, the freeze, and the November 29 record and dry runs. A fallback slice of at most 2.5 hours keeps the week under 10.
- **Unchanged risk.** `F20` still depends on the November 10 close and on an active-contributor count of 6 at the November 11 tier input. This record changes neither.
- **The confirmation-hardware rehearsal depends on organizer access.** Without it, the item is recorded unmet and the stage stays replay-first.
- **No result exists, and none is promised.**

## Verification

- `tests/test_tasks_dependencies.py` passes unchanged, because no `Depends` cell names a new slice.
- `tests/test_contract_lock.py`, `tests/test_corpus_rules_freeze.py`, and `tests/test_request_effect.py` pass unchanged, which shows no pinned `SPEC.md` text changed.
- `tests/test_status_consistency.py` and `tests/test_paid_run_gate.py` pass.
