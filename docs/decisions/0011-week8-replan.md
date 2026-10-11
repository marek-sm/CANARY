# 0011: Re-plan of Week 8 onward: Gate 3 on October 28, provisional M10-ALL, W10 folded

- Status: Accepted. Approved by the project lead on 2026-10-10; drafted with AI assistance.
- Date: 2026-10-10
- Decision scope: Protocol
- Secondary scopes: Governance
- Related specification sections: Sections 0, 5, 9, 10, 11, and 12
- Supersedes: None. The `TASKS.md` Week 7 recovery decision (October 4) scheduled this re-plan for October 11 and left W8–W13 unscheduled until it.

## Context

The Week 7 recovery decision made October 5–11 a recovery week. It moved the W7 slices to October 12–18 and recorded that Gate 3 can't pass on its October 18 date, because no W8 freeze can finish by then. It also promised a re-plan of W8 onward on October 11 that would either move the gate dates through a `SPEC.md` change or keep them and accept the Section 11 Gate 3 response (`ENGINEERING` or `STOP`).

State on October 10, at `670dd31`:

- The lock merged on October 7 as #35. The October 10 fresh-clone recovery check met every Gate 1 item, and Gate 1's recorded result stays "Not passed".
- No W6 pull request had merged:
  - #25 (`W6-T4`) was approved on October 9;
  - #28 (`W6-T5`) had a change request;
  - #31 (`W6-T3` Part A), #32 (`W6-T1`), and #34 (`W6-T2`) had no review, and #31 was a draft.
- Every W7 slice depends on W6 work, so any W6 slice not merged by Monday, October 12 leaves its W7 consumers `BLOCKED`.
- No slice row owned tool-result delivery, which is the first item of the paid-run condition. The `STATUS.md` risk said `W6-T3` would move delivery to tool results, but `W6-T3`'s Committed row doesn't name it.
- Decision 0009 item 8 left the corpus-record schema owner to this re-plan.
- W8–W13 carry 93.5 estimated member hours at full `F20` scope against about 62.5 hours of committed member capacity left: five contributors × 2.5 hours × five club weeks.

Decision 0009 hash-pins chosen `SPEC.md` text and leaves the gate dates unpinned, so this re-plan can change them. Decision 0007 pins Section 5, including step 8's "freeze … in week 8", and has no date carve-out.

## Options considered

1. **Keep Gate 3 on October 18.** Rejected. It fails on its date, and Section 11 then requires `ENGINEERING` or `STOP` with no empirical result.
2. **Move Gates 2 and 3, with a backstop date if Gate 3 slips again.** Not chosen. On October 7 the project lead chose to move only Gate 3 and to set no backstop. Gate 2 is already recorded not passed under the recovery decision.
3. **Move only Gate 3, to Wednesday, October 28, with no backstop. Chosen.** The Monday and Tuesday after W8's week give late W8 freeze work room without moving Gate 4's November 1 target, the November 8 data lock, Gate 5, or the November 22 release freeze.
4. **Absorb the lost week by squeezing W11 or W12.** Rejected. W11 holds the data lock and W12 holds Gate 5, and both would need a same-week dependency or a moved gate.

## Decision

1. **Gate 3 moves from October 18 to Wednesday, October 28, with no backstop.**
   - If Gate 3 is missed, the Section 11 Gate 3 response applies.
   - Gate 1, Gate 2 (October 11), Gate 4 (November 1 target), Gate 5 (November 15), the November 8 data lock, and the November 22 release freeze keep their dates.
   - `SPEC.md` moves to v1.5.0, with unpinned text changes only.
   - The Gate 3 step runs on Wednesday, October 28, not on a Saturday. W8 work not merged by Friday, October 23 may still merge through Tuesday, October 27. W8 work merged by October 23 doesn't change after that date, because W9 consumers have started from it.
2. **Provisional build geometry `M10-ALL`, with a 14-candidate pool.**
   - `M10-ALL` is 10 bases, 6 tasks, C2/C3, D0_BASELINE/D1_POLICY_GATE/D2_DATAMARKING, and 369 official trials. It's at or below the Gate 1 cap of `R15` and the six-contributor ceiling of `F20`. The non-personal reason category is capacity.
   - The selection margin stays 4, two per primary goal. A 10-base prefix alternates goals, so `W7-T2`'s pool needs at least 7 `secret_disclosure` and 7 `unauthorized_action` candidates with ledger status `evaluation` and a completed source review.
   - `ALL` needs both defenses to pass Section 12's binary readiness checks in the Gate 2 step. Gate 2's recorded "Not passed" doesn't remove those per-defense decisions; Section 11's Gate 2 response already chooses the tier from them.
   - The development instrument stays full scope (C2/C3/C4, ten templates, the 90-cell grid, 15 coverage smokes), as Section 9 requires. Gate 3 still confirms or lowers the tier under Section 12.
   - A pool under 20 can't build the 20- and 15-base prefixes of Section 5 step 8. A selection-prefix decision record is therefore required before `W7-T2`'s pull request on October 15. It's a separate record and not part of this one.
3. **Lattice weeks and club weeks.**

   | Lattice week | Club week | Dates |
   |---|---|---|
   | W7 | 8 | October 12–18 (unchanged) |
   | W8 | 9 | October 19–25; Gate 3 step October 28 |
   | W9 | 10 | October 26–November 1 |
   | W10 | — | Folded |
   | W11 | 11 | November 2–8 (unchanged) |
   | W12 | 12 | November 9–15 (unchanged) |
   | W13 | 13 | November 16–22 (unchanged) |

   At `M10-ALL` the official sweep is one run rather than two halves, so W10 folds into W9 and W11. Every `Depends` cell still names only earlier-week work.
   - **`W10-T3`'s sweep completion and audit, sanitizer run, and generated results:** to `W9-T3`, which runs the whole sweep after the Gate 3 step.
   - **Release-safe payload preparation:** moves from `W9-T2` to `W8-T2`, as a separately mergeable part outside Gate 3's hash set, so `W9-T3`'s sanitizer has it before the sweep week.
   - **`W10-T2`'s provenance, corpus-integrity, and release-licensing audit:** to `W9-T2`.
   - **`W10-T1`'s task-evidence audit:** to `W11-T1`, including its rule that failures are classified against the W5-frozen taxonomy and not by judgment.
   - **`W10-T4`'s enforcement-conformance audit:** to `W11-T4`. Both W11 audits read `W9-T3`'s records.
   - **`W10-T5`'s release-candidate accessibility support and offline media preparation:** to `W9-T5`.
   - **`W10-T5`'s static-page rule** (cut order 1, a four-hour cap, explicit lead authorization): to `W11-T5`'s Defer-first cell.
   - **All five publication-consent submissions:** to the W9 slices, so `W11-T5` and `W12-T5` read them from an earlier week.
   - **The W10 rows stay in the lattice,** because `tests/test_tasks_dependencies.py` requires all 45 slices. They carry no work, a 0-hour estimate, and no dependencies, and they never enter `IN PROGRESS`.
   - **Estimates move with the work.** No member hours are removed.
4. **Two exceptions to the cadence.**
   - **The Gate 3 step's Wednesday date and Tuesday merge cutoff,** in item 1.
   - **`W9-T3`'s sweep** starts on the Gate 3 record, a lead input that lands mid-week. The rest of W9 doesn't use it. `W9-T3`'s pre-sweep part, the sanitizer built and tested on development records, follows the usual Thursday, October 29 pull-request date. Its sweep, audit, and generated-results pull request is due Saturday, October 31, and its standing reviewer reviews it by the morning of Sunday, November 1. The project lead's supported-results decision stays Sunday, November 1.
   - The Gate 3 step copies the Gate 2 step's recorded development-floor counts (Section 10). `TASKS.md`'s rule that no gate step needs another's output is corrected to allow copying an earlier step's recorded result.
5. **Gate 2 step slip rule.**
   - **Trigger:** `W7-T3`'s live-model development-grid records or `W7-T4`'s readiness script isn't merged by Friday, October 16. Mock runs never count.
   - **The slipped step:** the Gate 2 step runs on Saturday, October 24, on work merged by Friday, October 23. The project lead's tier, budget, model, and decoding input moves from Sunday, October 18 to Sunday, October 25. Until it arrives, only the steps of `W8-T2`, `W8-T3`, and `W8-T4` that need the tier are blocked, under the missing-lead-input rule.
   - **No second slip.** If the live-model grid still isn't merged by October 23, no comparable D0_BASELINE baseline is ready, and the Section 11 Gate 2 response makes the Gate 3 choice `ENGINEERING` or `STOP`.
6. **Tool-result delivery is lead scaffold.**
   - In the runner that executes the development grid, each channel's untrusted content reaches the model only in the result of the tool call that retrieved it.
   - It's built on a branch stacked on #31 and #32 and opened as its own pull request once they merge, with a target of Wednesday, October 14.
   - It's listed as due Sunday, October 11, and treated as late under the missing-input rule, so only the `W7-T1` and `W7-T3` paid steps wait for it.
7. **Corpus-record schemas (decision 0009 item 8):** first versions of the `base_case` and `candidate` schemas, built to Section 8's frozen field semantics. They're lead scaffold, due Sunday, October 18, before `W8-T2`'s corpus freeze.
8. **Re-acceptance.** `W8-T2`, `W9-T2`, `W9-T3`, `W9-T5`, `W11-T1`, and `W11-T4` change materially. Each owner re-accepts the changed slice in its Monday issue, as `TASKS.md`'s ownership commitment requires.
9. **"Week 8" in pinned text.** Section 5 step 8 (pinned by decision 0007) and Section 9 "Model selection and pinning" (pinned by decision 0009) say "freeze … in week 8" and "week-8 freeze", and their bytes don't change. A sentence under Section 11's "End of week 8 — full protocol freeze" says those phrases name the Gate 3 freeze, now October 28.
   - Re-dating that freeze changes none of 0007's frozen corpus rules: eligibility, exact quotas, family and source caps, task assignment, deduplication, adaptation, relaxation order, the prefix construction, and the seeded recheck are all unchanged.
   - The freeze still comes before any official outcome is inspected and before any evaluation candidate runs on a live model.
   - The "week-9 … week-10" example in Section 9's drift rule illustrates the no-cross-version rule, which applies to whatever window the sweep runs in.
   - No outcome exists and no frozen artifact changes, so there's nothing to rerun and no `docs/protocol_deviations.md` entry.

## Consequences

- **The Gate 2 slip is the likely path.** No W6 pull request had merged on October 10, and delivery waits on #31 and #32. If the slip fires, the tier-dependent W8 freeze work falls into October 25–27, while its owners are in W9. That includes selection, the corpus-freeze citation audit, the protocol generator, the schedule, and the 20% recheck. Any optional floor rerun under decision 0009 item 7 must also fit there.
- **Delivery is lead-only work.** It makes the grid measure indirect rather than direct injection, and it's a lead pull request with no member review. End-to-end testing probably also needs #34's renders and the #25/#32 conflict in `agent/loop.py` resolved.
- **The sanitizer is reviewed after its first run.** It now runs on official data in the same slice that builds it. A defect its review finds means re-running it.
- **The early audit pass is gone.** The half-sweep audits are gone, so `W11-T1`'s and `W11-T4`'s audits are the first independent reads of the sweep records. That leaves about three days for any symmetric repair before November 8.
- **The pool caps the tier.** A 14-candidate pool makes an M10 row the effective ceiling at Gate 3, and `ALL` still depends on both readiness checks.
- **`W8-T2` grows.** It's gate-critical and takes the release-safe payload preparation.
- **The schemas arrive late.** The corpus-record schemas land after `W7-T2`'s records, so a mismatch becomes `W8-T2` rework.
- **There's no recovery window.** With no backstop, a miss on October 28 almost certainly means `ENGINEERING`, because only October 28 to November 8 remains for a sweep.
- **Capacity stays over.**
  - Club week 10 carries about 23 member hours against 12.5 committed, with `W9-T3` about 7.5 hours (‡, with the project lead pairing) and `W9-T5` about 7.0 hours.
  - W8–W13 carry 93.5 member hours at full `F20` scope against about 62.5; the `M10-ALL` estimates save about 6.5 hours across the whole plan, all in tier-scaled cells. The Defer-first rows and the Section 12 cut order are the only relief.

## Verification

- `tests/test_contract_lock.py` and `tests/test_corpus_rules_freeze.py` pass unchanged, which shows no pinned `SPEC.md` text changed.
- `tests/test_tasks_dependencies.py` passes with all 45 slices and no `Depends` cell naming same-week or later work.
- `tests/test_status_consistency.py` passes against the October 11 rollup.
- `SPEC.md`'s Section 11 Gate 3 row reads October 28, and `TASKS.md`'s lead-inputs table, gate steps, slice tables, and club-week milestones match this record.
