# 0032: Give the November 11 tier input: `F20` on `claude-haiku-5-5`, with dated `W8-T2` and `W8-T4` fallbacks

- Status: Accepted. Approved by the project lead on 2026-11-11 by merging this record; drafted with AI assistance.
- Date: 2026-11-11
- Decision scope: Protocol
- Secondary scopes: Governance
- Related specification sections: Sections 5, 9, 10, 11, 12, and 17
- Supersedes, for the parts named here only: decision 0030 item 9's first bullet (item 8); and, only for the corpus-record pushes of item 5's `W8-T2` fallback, decision 0031 item 3's rule that a source record's approver is its Section 5 source reviewer, the lead-side review's matching mismatch check, and the matching Consequences sentence on `W8-T2` freeze pushes. Every other part of decisions 0030 and 0031 stays in force. Item 4 also reads decision 0025 item 10's "by November 10" as November 13, this record's own reading, because decision 0029 moved the W8 freezes to November 11–13 without naming that sentence.

## Context

**What this record costs, first.**

- **`F20` carries a capacity risk that no lower row removes.** `W8-T2` and `W8-T4` have no pull request. Both missed their opening on the morning of Monday, November 9, and both are needed at every empirical row: `W8-T2` freezes the corpus and renders the evaluation fixtures, and `W8-T4` rechecks them and freezes the defenses. Dropping to `R15` wouldn't remove that risk. Items 5 and 6 set dated fallbacks. If the owners' work and the fallbacks miss November 13, the outcome is the Section 11 Gate 3 response, in practice `ENGINEERING` or `STOP`.
- **The count of 6 rests in part on one owner's reply.** Item 3 sets the disclaimer path.
- **The spend limit stays at $10.** The equation passes on observed cost, but a run near the price bound would hit the cap mid-sweep (item 8).
- **The development floor applies.** The headline takes Section 1's floor form whatever evaluation shows (`SPEC.md` Section 10). This record doesn't change the model because of it. [Decision 0009](0009-measurement-contract-lock.md) rejected that switch as its third option considered, because choosing a model by whether injections succeed on it biases the study.

**Why now.** Decision 0029 item 3 moved the tier input to Wednesday, November 11, after the Gate 2 step and after every W7 slice had merged. Its contents are decision 0025 item 10's. The Gate 2 step ran on November 10 ([`docs/evidence/gate2-2026-11-10/`](../evidence/gate2-2026-11-10/README.md)). `W7-T2` merged as #73 on November 10, `W7-T1`, `W7-T3`, and `W7-T4` merged earlier, and `W7-T5` (#66) merged on November 11 as `42271c8`, before this record (`TASKS.md`, recorded November 11).

## Options considered

1. **`R15`, counting 5.** Rejected by the project lead. The count is 6 under decision 0027 item 1 (item 3), and `R15` keeps the same `W8-T2` and `W8-T4` risk.
2. **Wait for `W8-T2` and `W8-T4` before giving the input.** Rejected. Decision 0029 item 3 dates the input, and both slices need the selected tier to select and draw the recheck.
3. **`F20`, with dated `W8-T2` and `W8-T4` fallbacks and the cap kept at $10.** Chosen.

## Decision

1. **Inputs, reproducible from merged code and evidence.**
   - **`P` = 20.** `uv run make select` on `main` at `f0f3f3b` gives `pool_hash` `864b46148d9818e0c48fed522b87b1c617ced4dcc5f0054d5959881d71914425`, 13 eligible `secret_disclosure` and 14 eligible `unauthorized_action` bases, no relaxation, and nested 15-, 10-, 8-, and 6-base prefixes. That rerun is the `P` of record. A post on #73 on November 8, before #73 merged, also gave `P` = 20; the rerun on merged code agrees. If a Section 5 step 6 rejection later lowers `P`, decision 0025 item 10's rule applies: `W8-T2` records it, the project lead lowers the tier, and `W8-T4` redraws the recheck.
   - **The recheck sample at `N` = 20** is `ceil(0.20 × 20)` = 4 cases, drawn by the committed script: `88653772cbbd557c33f0`, `eedb6d91a0f709796081`, `901bdcccb51d43ff5c5c`, and `2b467a07bc6b378fddfd`.
   - **The lead-side review of `corpus/select.py`** ([`docs/reviews/2026-11-11-w7-t2-t5.md`](../reviews/2026-11-11-w7-t2-t5.md)) has 0 blocking findings: on November 11 the project lead classified every finding, accepting each class as proposed (0 blocking, 0 safety, 11 non-blocking). An independent implementation reproduced the 20-base vector, `pool_hash`, and every recheck sample. Open call Q-73-1, how a relaxation applies to the nested prefixes, doesn't bind at `P` = 20 with no relaxation.
   - **Readiness (Gate 2 step):** D1_POLICY_GATE ready and D2_DATAMARKING ready.
   - **The development floor applies:** 0 of 15 D0_BASELINE attack cells count (0 true, 15 false, 0 null, 0 missing).
   - **Budget:** the Section 9 equation at `F20` needs $4.5737051 against a $9.96 remaining balance (`gate2-budget.json`), computed by `analysis/gate2_budget.py` and not typed. It includes 12 C1 trials and the reserve at the frozen bound of $0.0641216: 13 development trials (the figure [decision 0026](0026-malformed-calls-and-price-bound.md) set), 30 rehearsal trials, and 3 stage trials, a reserve of $2.9495936.

2. **The tier input is `F20`.**
   - Section 12 step 3: the D0_BASELINE development cells completed, the 15 clean coverage smokes completed, and the runner and measurement baseline passed the Gate 2 step, so an empirical row is open. Both defenses passed the Gate 2 step's readiness checks, so the `ALL` suffix is selectable. `F20` has no `ONE` or `BASE` form (`SPEC.md` Section 12 step 4).
   - Section 12 step 2: `F20` needs 20 bases, and `P` = 20.
   - **Arithmetic:** 20 bases × C2/C3/C4 × attack/clean × D0_BASELINE/D1_POLICY_GATE/D2_DATAMARKING × n=3 = 1,080 primary trials, plus four C1 controls × D0_BASELINE × n=3 = 12, for 1,092 official trials. The 20 bases cover the 10 task templates in `tasks/task_order.json`.
   - **Non-personal reason category:** headcount ceiling. `F20` is the largest row the count allows, and the prefix, readiness, and budget support it.
   - It is an input and a provisional geometry. The Gate 3 step's `protocol/active.json` makes the selection.

3. **The active-contributor count is 6.**
   - It counts the project lead and the five portfolio owners, each of whom has accepted at least one row under [decision 0027](0027-acceptance-by-work.md) item 1:
     - T1, by commits and #74 on `W8-T1`;
     - T2, by #73 on `W7-T2`;
     - T3, by #77 on `W8-T3`;
     - T5, by its pushes to #66 on `W7-T5`;
     - T4, by a November 9 reply to the project lead, under 0027 item 1, which commits T4 to the whole `W8-T4` row. The project lead's November 8 push to `W7-T4` was the lead's own work and isn't counted for T4.
   - **If T4 says the reply wasn't acceptance of the whole row:**
     - Before the Gate 3 freeze: T4 isn't counted, the count is restated as 5, the ceiling is `R15`, final for this run (decision 0029 item 3), and `W8-T4` goes to decision 0027 item 3's visible decision.
     - After the freeze: the frozen count was a wrong input. It is recorded as a material post-freeze defect under Section 11 change control, with a `docs/protocol_deviations.md` entry, and the paper states it. Nothing is relabelled silently.
   - **A reassignment under item 5 or 6 doesn't restate the count.** The count is read once, at this input (decision 0027 item 3; decision 0029 item 3). That is a limitation the paper states with the review method.
   - `protocol/active.json` records only the number and the reason category. Names, personal circumstances, and commentary aren't protocol fields (Section 12 step 1).

4. **Capacity: what must merge by Friday, November 13, in order.**

   | Item | State on November 11 | Order and use |
   |---|---|---|
   | `W7-T5` (#66) | Merged November 11 (`42271c8`) after the project lead's README-only conflict fix | Merged before this record (decision 0029 item 3) |
   | `W8-T2` | No pull request; missed its November 9 opening | Merges first, by the end of Thursday, November 12 (item 5): the selection at `N` = 20, its Section 15 citation audit, and the evaluation fixtures that `W8-T4`'s recheck and `W8-T3`'s context-window check read |
   | `W8-T4` | No pull request; missed its November 9 opening | The defense freeze and notes, with item 6's trigger at the end of November 12; the four-case recheck after `W8-T2` merges, by the end of November 13 |
   | `W8-T1` (#74) | Open, CI green | The task and oracle freeze. It also takes item 7's routed defect check |
   | `W8-T3` (#77) | Open, CI green | The generator, dormant plan, report code, and sanitizer. Its C1 step waits for the C1 result-schema record (below) |
   | `W8-T5` | Opens the day `W7-T5` merges | The output-pipeline freeze |
   | Project lead | | The official C1 result-schema record, through Section 11 change control with a `docs/protocol_deviations.md` entry and a re-pin of the locked result schema (decision 0025 item 8), merged by noon on Thursday, November 12, more than 24 hours before `W8-T3`'s last merge; `runner/lead_review.py` and the `paid_run` refusal; the count-only outputs; decision 0012's wiring; the demo-rehearsal command; decision 0031 item 7's whole-tree review; the rolling 24-hour reviews; and the code-owner approval of `W8-T2`'s corpus-record push as its Section 5 reviewer |

   - **The project lead's added time, November 11–14 (Claude's estimate):** about 6.5 hours without a fallback. That is the #66 record check and approval, classifying two findings files, reviewing this record and the C1 record, approving `W8-T2`'s record push, reviewing the November 13 lead items Claude builds, and the Gate 3 step on November 14. It is in addition to decision 0031 item 9's 3.5 hours for November 9–15, about 10 hours in all. Item 6's `W8-T4` fallback adds about 2.5 hours, and item 5's `W8-T2` fallback about 3 more. Decision 0031 item 9's rule on the license and author order applies to the week's total.
   - **`W8-T2` and `W8-T4` are needed at every empirical row.** `W8-T4` is 4.5 hours at every row (`TASKS.md`), and `W8-T2`'s selection and fixtures are needed at any `N`. So their state doesn't make `F20` less supported than `R15`. The list supports `F20` if `W8-T2` merges by November 12 (or its fallback by November 13) and `W8-T4` or its fallback merges by November 13.

5. **`W8-T2`: a visible schedule decision and a fallback.**
   - **The decision.** `W8-T2`'s row wasn't accepted by its latest open date, the morning of November 9. Decision 0027 item 3 then requires a visible reassignment, tier, cut, or schedule decision. This is that decision, recorded two days late. It is a schedule decision: T2 keeps `W8-T2`, and its latest merge is the end of Thursday, November 12.
   - **Acceptance.** Any commit or pull request T2 authors on `W8-T2`'s work is acceptance under 0027 item 1. The November 8 `P` post on #73 isn't counted as acceptance of `W8-T2`.
   - **Fallback.** If `W8-T2` hasn't merged by the end of November 12, the project lead takes it by visible reassignment, recorded in `TASKS.md` that day. Claude builds the selection run, fixtures, and freeze code. The project lead owns the Section 15 citation audit and source verification.
   - **Approver.** The project lead can't approve their own corpus-record push (decision 0031 item 3), so T3 is named on November 11 as the code-owner approver of the fallback's corpus-record pushes, more than 24 hours before November 13. Because the Section 5 source reviewer would then be the push's author, decision 0031 item 3's approver rule and mismatch check don't apply to those pushes (Supersedes line). This record and the paper state it as a limitation: the source reviewer authored the freeze push, and a member who isn't the source reviewer approved it.
   - **Independence.** If the project lead both renders `W8-T2`'s fixtures and does `W8-T4`'s fallback recheck, the recheck isn't independent of the renderer. This record and the paper then state it as a limitation.
   - **If `W8-T2` still misses November 13:** the Gate 3 step takes the Section 11 Gate 3 response, in practice `ENGINEERING` or `STOP`.

6. **`W8-T4`'s fallback.**
   - **Trigger:** no `W8-T4` push containing the defense freeze by the end of Thursday, November 12. The four-case recheck runs after `W8-T2` merges, by the end of November 13, under whichever owner then holds `W8-T4`.
   - **Then:** the project lead takes `W8-T4` by visible reassignment, recorded in `TASKS.md` that day. The project lead personally reopens the four sampled sources and owns the threat-model, defense, event-semantics, and security-test notes, because `AGENTS.md` keeps the threat model and source verification human-owned. Claude builds only the hash and freeze code and drafts the notes.
   - **Independence, stated as a limitation.** All four sampled cases were opened and adapted by T2 and source-reviewed by the project lead. A lead recheck is the original reviewer rechecking their own sign-off. That meets Section 5 step 8, which forbids only the opener and adapter, and the paper states it. T4 opened none of the four, so decision 0025 item 6's move of a recheck to T5 doesn't fire.
   - **Approver:** if the fallback pull request changes a `.github/CODEOWNERS` path, T1, the decision 0006 vector reviewer, is its code-owner approver. T1 is told on November 11, more than 24 hours before the November 13 merge.
   - **If the fallback also misses November 13:** the Gate 3 step takes the Section 11 Gate 3 response, in practice `ENGINEERING` or `STOP`. It isn't a lower row, because no smaller prefix will have been rechecked (Section 5 step 8; Section 11 Gate 3 pass evidence).

7. **Model and decoding: `claude-haiku-5-5`, confirmed against Section 9's criteria.** Every figure below is development evidence, excluded from estimates (Section 9; decision 0025 item 2).
   - **Criterion 1:** native structured tool calling through the Messages API ([decision 0010](0010-anthropic-development-model.md)).
   - **Criterion 2:** a pinned snapshot. Every Claude model ID is one (decision 0010).
   - **Criterion 3, development completion and reliability:**
     - The 90-cell grid: 90 of 90 trials found and complete, with no infrastructure failure, no run-wide stop, and usage recorded for every trial.
     - The 15 clean coverage smokes: 15 of 15 completed, and 8 passed utility. The 7 failures: `open-ticket-ids` in all three configurations, `invoice-receipt-email` under D0_BASELINE and D1_POLICY_GATE, and `maintenance-confirm-email` and `service-hours-extract` under D1_POLICY_GATE. They fall in `W8-T1`'s existing scope, task and oracle defects surfaced by the smokes, before its freeze. A failure under D1_POLICY_GATE alone may be the defense's real utility cost, which is recorded, not tuned away.
     - The Gate 2 step's 0 gate/audit disagreements are D1_POLICY_GATE readiness evidence, not model reliability, and aren't cited here.
   - **Criterion 4:** measured cost under the funded cap: $0.039647 for 107 development trials, and the equation passes at `F20` (item 1).
   - **Criterion 5:** relevance to deployed agent workflows (decision 0010).
   - **Not chosen on evaluation attack success.** No evaluation outcome exists. The development floor was visible when this record was written, and the model doesn't change because of it.
   - **Frozen decoding, as the grid ran:** the Messages endpoint, `thinking` disabled, `effort` medium, `max_tokens` 4,096, and the one-call `tool_choice` setting (`disable_parallel_tool_use: true`) that `floor-count.json` records and decision 0028 item 5 requires. A changed decoding needs its own record (decision 0025 item 10).
   - **Fallback:** `gpt-6-luna` stays declared and inactive. A missed date never activates it.

8. **Funded cap and season budget.**
   - **Funded budget cap:** the CANARY-only Claude Console workspace's $10 monthly limit, with the ledger cap slightly below it (decision 0028 item 7). It covers the development trials, the official sweep, and the November rehearsals.
   - **Season budget:** $10 for November, the same limit. The equation needs $4.5737051 of it. The three stage trials fall on Demo Day; if that is in December, December's limit covers only them (decision 0030 item 9).
   - **This replaces decision 0030 item 9's first bullet,** which raised the limit and the cap by November 10. On November 10 the project lead left the limit at $10, because the equation passes on observed cost. Decision 0028 item 7's default, to raise the limit if the equation fails at `F20`, still stands.
   - **The risk that remains.** At the price bound, the sweep plus the reserve, 1,138 trials, would cost about $72.97, against $9.96. A sweep that reached the cap would stop with missing cells, and the 5% rule would make the headline comparisons ineligible (`SPEC.md` Section 9, the missing-data threshold). The observed development cost is at most about $0.00055 per trial (mean about $0.0004), under 1% of the bound.
   - **Re-evaluated before Gate 3** if `W8-T3`'s Section 9 count over evaluation renders finds a larger request, because the bound then rises (decision 0025 item 11). If the equation then fails, decision 0028 item 7's default applies.
   - **Console reconciliation.** On November 11 the project lead read $0.04 of spend in the Console, which matches the ledger's $0.039647 at the Console's cent precision. The Gate 2 budget equation in item 1 therefore stands without a rerun.

9. **Accountable roles.** The owner of each W8–W13 slice in `TASKS.md`, and the project lead for the lead inputs, the Gate 3 step, and the sweep's execution.

10. **Unchanged.** The Gate 3 date of Saturday, November 14, and the November 22 data cutoff (decisions 0029 and 0030). The development floor. Decision 0018's C1 order, except the example decision 0033 supersedes. `SPEC.md` doesn't change.

11. **Numbering.** This record takes 0032, and the record superseding decision 0018's example takes 0033.

## Consequences

- **The geometry is the full study.** 1,092 official trials, both defenses, and four C1 controls, if `W8-T2` and `W8-T4`, or their fallbacks, land by November 13.
- **The headline takes the floor form.** RQ1's paired differences are reported as exact counts with no interpretation (`SPEC.md` Section 10).
- **The project lead's November 12–13 load rises** if either fallback fires, by up to about 5.5 hours.
- **A cap hit is the one funding path to missing cells.** It is improbable on observed cost, and item 8 states it.

## Verification

- `uv run make select` on `main` reproduces item 1's `P`, `pool_hash`, and recheck sample. `tests/test_selection_rules_independent.py` recomputes the recheck samples, pool hash, task vector, and goal order from the rule text.
- `gate2-budget.json` holds item 1's figures.
- `tests/test_status_consistency.py` checks `STATUS.md` against `SPEC.md`'s tier and headcount rules.
- `tests/test_tasks_dependencies.py` passes with the November 11 `TASKS.md` notes.
