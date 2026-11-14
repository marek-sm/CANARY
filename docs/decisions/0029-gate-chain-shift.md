# 0029: Move Gate 2's close and Gate 3 three days to keep `F20` after the W7 slip, and wait for the confirmed Demo Day date before re-planning the end

- Status: Accepted. Approved by the project lead on 2026-11-05; drafted with AI assistance. Dates and the sentences it names amended by [decision 0030](0030-done-by-november-30.md), and, for review sentences, by [decision 0031](0031-merge-on-green.md).
- Date: 2026-11-05
- Decision scope: Protocol
- Secondary scopes: Governance
- Related specification sections: Sections 9, 10, 11, 12, 13, and 14
- Supersedes, for dates and the sentences named only:
  - Decision 0025: item 2's carried-forward wiring date; item 4's November 7 close and "doesn't move again"; item 5's November 6 summary date; item 7's November 6 lead date for the task variants; item 9's W8 dates; item 10's November 8 tier-input date; item 12's November 11–14 sweep dates; item 13's "with no further move"; item 14's Gate 3 date.
  - Decision 0022: item 1's W9 start at Monday, November 9 and the W8 changeability that ends with it; item 2's November 11 floor-rerun hold and November 6 notice; item 3's Gate 2 and tier dates; item 4's Gate 3 date and "No date moves later".
  - Decision 0021: item 3's late W8 merges through November 10; item 4's Gate 3, sweep pull-request, and supported-results dates; item 5's wiring date; item 6's "A Gate 3 miss on November 11"; and item 7's table rows for the Gate 3 record and the supported-results decision.
  - Decision 0027: items 2 and 3's November 8 reading date.
  - Decision 0028: item 5's "The November 7 close is never refused for lack of a record" (date only); the Consequences' "by the end of November 4"; item 4's November 10 date for the count-only outputs; item 8's November 15 provisional supported-results date.

## Context

**What this record costs, first.**

- The optional static replay page (`SPEC.md` Section 2) is lost. It needs an empirical Gate 4 by November 15 and authorization by November 17, and neither date can now be met.
- W11's audits get November 18 or 19 through November 20, not a week. Symmetric repair has November 20–22.
- The W12 pull-forwards planned for club week 13 move to club week 15.
- `F20`'s defense comparison is still at risk. Any slip in item 2's chain ends it, and this record allows no fifth move.

**The slip.** `W7-T4` and `W7-T5` missed their November 4 merge date. Decision 0025 item 2 required a visible reassignment, cut, or schedule decision that day, and none was recorded. This record is that decision, one day late. Neither owner has a known capacity change: both pushed, and part of what remains waits on the project lead's merges and on reviews. So it is a schedule decision, not a reassignment.

**What the slip reaches.** The paid development grid needs `W7-T4`'s readiness script, the lead's task variants, the lead's stack-gap fixes, and a run-wide stop rule on `main` (decision 0025 item 4's order; decision 0028). None has merged. Decision 0025 item 4 closes the Gate 2 step at the end of November 7 and says it "doesn't move again". With no paid grid records at that close, no `ALL` or `ONE` row is selectable, and `F20`'s defense comparison is lost, which is the purpose decisions 0016 and 0017 set.

**Why Gate 3 can't stay on November 11.** A first draft kept Gate 3 and split the tier input: `N`, budget, and model on November 8, the readiness suffix by November 10. Review showed it unlawful and unworkable:

- The budget equation needs observed development cost and the balance after the paid grid (`SPEC.md` Section 9), and the model is confirmed from Section 9's completion and cost criteria. `analysis/gate2_budget.py` refuses an empty, mock, or incomplete grid.
- `N` can't be fixed apart from the suffix: there are no `F20-ONE` or `F20-BASE` rows (Section 12), so one ready defense means at most `M10-ONE`.
- No W8 work freezes before the readiness step and tier input (decision 0025 item 9; Section 11's Gate 2 response), so a November 10 step leaves the four W8 freezes part of one day.

The strongest option that keeps `F20` moves the whole chain (Gate 2 step, tier input, W8 freezes, Gate 3) three days, with decision 0025's spacing between links.

**Club research leadership's November 5 message.** It says, in paraphrase:

- Demo Day falls in club week 14 or 15, November 23 to December 6, date to be confirmed. Decision 0021 assumed club week 16.
- A midpoint check-in on November 7–12 collects each project's methods and results.
- Leadership has drafted each paper's abstract and introduction.
- A reviewer board will admit papers using the club's editorial policies, which follow the NeurIPS paper checklist and the IEEE paper structure. `paper/venue-checklists.md` already maps both.

## Options considered

1. **Let the Gate 2 step close on November 7, as decision 0025 says.** Rejected. It removes the defense comparison.
2. **Keep Gate 3 on November 11 and split the tier input.** Rejected for the reasons above.
3. **Move Gate 3 later and keep `M10-BASE` or `ENGINEERING` as the planned outcome.** Rejected by the project lead's direction to keep the full study while it remains possible.
4. **Move the Gate 2 close, the tier input, the W8 freezes, and Gate 3 three days, keep the November 22 cutoff and Gate 4's November 20 latest date, and re-plan Demo Day only once its date is confirmed.** **Chosen.**
5. **Re-plan for a November 23 Demo Day now.** Rejected. It would move inputs that haven't merged earlier on a guessed date.

## Decision

1. **A fourth move, and the last.**
   - The Gate 2 step closes at the end of Tuesday, November 10. There is no fifth move.
   - If the step hasn't run by then, decision 0025 item 4's rule applies with this date. Committed code evaluates the floor once over whatever grid records exist, absent cells count as missing, and no `ALL` or `ONE` row is selectable.
   - In that case at most `M10-BASE` remains (Section 12), and only if the D0_BASELINE summary merges and the project lead records D0_BASELINE readiness against it by Thursday, November 12. The W8 freezes then freeze against `M10-BASE`. If that misses too, Gate 3 is `ENGINEERING` or `STOP`.
   - In practice, a slip anywhere in item 2's chain ends the defense comparison.

2. **The chain.** This record takes effect when it merges, planned for the morning of Friday, November 6. Every date set for a portfolio owner falls at least 24 hours after that merge. If the merge slips, those dates slip with it, and the November 10 close doesn't.

   | Item | Owner or reviewer | Latest |
   |---|---|---|
   | The stack-gap fixes, CI green, merged | Project lead (the lead's own pull requests merge on the lead's approval) | End of Saturday, November 7 |
   | A run-wide stop rule: a run that hits a run-wide failure stops, and verification doesn't call it complete. Its only reviews are the project lead's and an AI review, with no portfolio owner's, a limitation the Gate 2 record states | Project lead | End of Saturday, November 7 |
   | Task variants: `main` merged on November 6, then T1's review | T1 | End of Sunday, November 8 |
   | `W7-T4`: one push that merges `main` and makes `analysis/defense_readiness.py` call `paid_run.check_code_matches_run` (decision 0028; `docs/INTERFACES.md`) | T4 | End of Saturday, November 7 |
   | `W7-T4`: review of that push, which dismisses earlier review states | T1 | End of Sunday, November 8 |
   | `W7-T5`: `main` merged and its conflict resolved; whichever of `W7-T5` and the stack-gap fixes merges second keeps one `replay` target and one `_observation_text`, and the project lead does that in the stack-gap fixes if they merge second | T5 | End of Sunday, November 8 |
   | `W7-T5`: review | T2 | End of Monday, November 9 |
   | Mock grid, paid-run record, paid grid, and smokes, in decision 0028's order | Project lead | Monday, November 9 |
   | Paid summary (decision 0025 item 5's contents), reviewed by `W7-T3`'s and `W7-T1`'s reviewers, each told on November 6 | Project lead | Merged by the end of Tuesday, November 10 |
   | Gate 2 step | Project lead | End of Tuesday, November 10 |

   - If `W7-T4`'s push hasn't arrived by the end of November 7, the project lead records a visible scope change in `TASKS.md` on November 8 and makes that one push, with only the merge and the call. T4 keeps the slice, and T1 reviews within 24 hours.
   - If T1 reopens `W7-T4`'s earlier change request, T4 answers under the 48-hour rule, and the close doesn't move.
   - The task variants and the stop rule change grid-scored facts, so they merge before the mock grid, as decision 0028 requires. Only its "by the end of November 4" changes, to November 8.

3. **The tier input moves to Wednesday, November 11.**
   - It comes after the Gate 2 step and after every W7 slice has merged, decision 0022 item 3's order. Its contents are decision 0025 item 10's.
   - `W8-T2`'s first step still posts `P` on Sunday, November 8, because it needs no tier.
   - Decision 0027 reads acceptance on November 11, not November 8. Its rule that a later acceptance doesn't raise a recorded tier input stands. If an owner has no counted reply or work by November 11, the count is 5 and the ceiling is `R15`, final for this run.

4. **W8.**
   - Before the tier input, decision 0025 item 9's tier-independent list still bounds W8.
   - The freezes run Wednesday, November 11 through Friday, November 13, in decision 0025 item 9's order: `W8-T2` merges first, then `W8-T3`'s and `W8-T4`'s last pushes, each reviewed within 24 hours.
   - `W8-T2` and `W8-T4` open by the morning of Monday, November 9. `W8-T5` opens the day `W7-T5` merges.
   - Every W8 slice's last merge is Friday, November 13.
   - W8 work stays changeable through November 13. Each W9 slice starts the day its W8 inputs are on `main` (decision 0022's start-on-merge rule), not on Monday, November 9.
   - Decision 0012's output wiring and decision 0028 item 4's count-only outputs are due Friday, November 13. The project lead tells `W9-T3`'s owner about the wiring the day W8's last slice merges.

5. **W9, Gate 3, the sweep, and W11.**
   - Gate 3 runs Saturday, November 14, on W8 work merged by Friday, November 13. The optional floor-rerun hold ends no later than November 14.
   - `W9-T3`'s sanitizer pull request is due Sunday, November 15. It starts after `W8-T3` merges, and the sweep's sanitizing waits for it.
   - The sweep runs Saturday, November 14 through Tuesday, November 17 under `W9-T3`.
   - `W9-T3`'s sweep, audit, and generated-results pull request is due Wednesday, November 18, and reviewed by the morning of Thursday, November 19.
   - `W9-T1`, `W9-T2`, `W9-T4`, and `W9-T5` pull requests are due Monday, November 16, and reviewed by Tuesday, November 17.
   - The project lead's provisional supported-results decision comes Thursday, November 19, the Gate 4 target.
   - `W11-T1` and `W11-T4` merge by Friday, November 20, and the final supported-results decision comes that day, its unchanged latest date. `W11-T3`'s last approved push binds to it.
   - `W11-T2`, `W11-T3`, and `W11-T5` merge by the unchanged November 22 cutoff. Symmetric repair under Section 11 has November 20–22.
   - The W12 parts planned as pull-forward into club week 13 run in club week 15.
   - The paper leads' November 16 manuscript draft uses no result numbers, provisional or final.
   - `SPEC.md` moves to v1.20.0. Only unpinned text changes: the Gate 3 date, the sweep's club week, Gate 4's target, and the static replay page's dates.

6. **The environment Gate 3 freezes.**
   - The sweep runs on the host under the tool sandbox (decision 0025 item 12), so Section 11's "container digest" freeze item is answered by the host environment instead.
   - At Gate 3, `protocol/active.json` names the OS build, Python build, SQLite version, `uv.lock` hash, and sandbox launcher and profile hashes, read on the frozen commit. `container_digest` stays null.
   - The sweep's own paid-run record, written after Gate 3 (decision 0025 item 12), must match these values, and the Gate 4 step compares them per invocation (decision 0028 item 9).
   - This holds only if decision 0028 item 9's test leaves the host as the sweep's platform.

7. **Demo Day.**
   - The event date is an outside input. The project lead asks the organizers for it now, and `TASKS.md` records it once confirmed.
   - If the confirmed date is before Monday, December 7, a follow-up record within 48 hours re-dates the rehearsals, the video, final claim language, the Gate 5 step, and the release-freeze rows against it. That record never moves the data cutoff or Gate 4 earlier and never adds work in club week 14.
   - A Demo Day in club week 14 would leave no finished video, no Section 13 rehearsal, and no Gate 5 before the event. That follow-up record decides what is cut, and the cut is stated publicly.
   - Whatever the date, Demo Day shows only outputs generated from the frozen sanitized bundle that `W11-T3` binds by November 22 and that the final supported-results decision approves, in the predeclared result sentence's form (Section 1), replay-first (Section 13).
   - A number shown before `W12-T3`'s numerical-claim audit and Gate 5 is labelled pre-release. Anything later checks correct is corrected publicly.

8. **The paper.**
   - At the midpoint check-in the project lead supplies methods only: the protocol, estimands, analysis plan, threat model, and limitations, marked as a draft until the Gate 3 freeze. No result is supplied. Development-run numbers are development evidence and are never reported as results (decision 0025 item 2).
   - Results reach the paper leads after the final supported-results decision, generated from the bundle.
   - Leadership's abstract and introduction stand only after the project lead checks them against Section 1's permitted claims, decision 0017's gap-claim scope, and Section 14's abstract rule, which needs the exact tier and `N` and so can't be completed before Gate 3.
   - Admission by the club's reviewer board is described as admission, never as peer review or publication (Sections 1 and 14).

9. **Capacity.**
   - From November 7 to November 17 the owners carry W7 rework and reviews, decision 0028 item 8's human reviews, the four W8 freezes, `W8-T5`, and the W9 slices other than the sweep (`W9-T5` alone is estimated at 7.0 hours).
   - The W12 pull-forwards then move into club week 15.
   - No measured turnaround supports this load. This record promises no result.

10. **Numbering.** This record takes 0029. `SPEC.md` moves to v1.20.0, with unpinned text changes only.

## Consequences

- **This is the fourth move of the Gate 2 step.** Decision 0025 said there would be no third. Public posts lead with that and promise no result.
- **The defense comparison depends on six merges in four days.** T1 carries two of the reviews, and the project lead carries the stop rule, the stack-gap fixes, the paid runs, and the summary.
- **Results come later relative to Demo Day.** They are final on November 20 at the latest, and Demo Day could fall as early as November 23.
- **W11 has two or three days for its audits,** and repair has the last three days before the cutoff.
- **The paper's results section can't reach the check-in.** The check-in gets methods only.

## Verification

- `tests/test_tasks_dependencies.py` passes unchanged, because no `Depends` cell changes.
- `tests/test_contract_lock.py`, `tests/test_corpus_rules_freeze.py`, and `tests/test_request_effect.py` pass unchanged, which shows no pinned `SPEC.md` text changed.
- `tests/test_status_consistency.py` and `tests/test_paid_run_gate.py` pass.
