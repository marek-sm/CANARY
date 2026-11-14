# 0025: Replace decision 0024 and target the full `F20` study

- Status: Accepted. Approved by the project lead on 2026-11-02; drafted with AI assistance. Dates and the sentences it names amended by [decision 0029](0029-gate-chain-shift.md), and, for review sentences, by [decision 0031](0031-merge-on-green.md).
- Date: 2026-11-02
- Decision scope: Protocol
- Secondary scopes: Governance
- Related specification sections: Sections 4, 5, 9, 10, 11, 12, 15, and 16
- Supersedes:
  - Decision 0024, except the rules item 2 carries forward.
  - Decision 0021 items 3 and 7's Gate 2 step and tier-input dates, and item 6's "There is no third move" and its first two bullets. Its other three bullets stand.
  - Decision 0022 item 1's W8 line, item 3's last two sentences, and item 4's Gate 2 and tier dates and "No date moves later" for those two dates.
  - Decision 0011's provisional build geometry `M10-ALL`.

## Context

Decision 0021 item 6 fired on October 30 and said there would be no third move. Decision 0024 applied it on November 1, chose `ENGINEERING`, and merged as #67. **This record is a third move.**

No evidence changed between them. On November 2, `main` holds 0 of 24 evaluation candidates, no W7 slice has merged, and no paid grid call has run. The change is the project lead's direction: `ENGINEERING` gives no evidence about either defense, which is the purpose decisions 0016 and 0017 set, and decision 0021 option 1 rejected it for that reason. This record's only new mechanism is dated tripwires. No improvement in turnaround has been measured.

`F20` is a target, not a selection. Gates 1 and 2 stay "Not passed". No result exists, and none is promised.

Reviewing this direction also found work no slice owned:

- **Task variants.** `F20` runs 10 tasks through C2, C3, and C4, and five templates declare one adapter each, so ten variants don't exist. Every empirical row needs some of them.
- **Official C1 records.** The locked result schema rejects them.
- **The maximum-token price bound.** `SPEC.md` Section 9's budget equation uses it, and nothing defines it.
- **Grid records.** Raw provider bodies can't enter Git under `docs/DATA_RELEASE.md`, so "merged records" had no lawful content.

## Options considered

1. **Keep decision 0024.** Rejected by the project lead. It removes the defense comparison that gives CANARY its purpose.
2. **Reopen only a smaller empirical tier.** Rejected by the project lead, who directed the study as first planned.
3. **Target `F20`, under dated tripwires and `SPEC.md`'s own downgrade rules.** Chosen.

## Decision

1. **The target is `F20`:** 20 bases, 10 tasks, C2/C3/C4, attack and clean, D0_BASELINE/D1_POLICY_GATE/D2_DATAMARKING, n = 3, and four C1 controls, or 1,080 + 12 = 1,092 official trials, with `K` = 3, 30 rehearsal trials, and 3 stage trials. It is the provisional geometry. The Gate 3 step makes the selection under Section 12.

2. **Carried forward from decision 0024.**
   - `W7-T1` and `W7-T3` land for W8's tier-independent work when #63 and #62 merge. That work doesn't use `W7-T2`'s pool, so `W8-T3`'s and `W8-T4`'s `W7-T2` input holds only their pool steps, each recorded as one blocked step. Their paid records follow in their own pull request, under each slice's one reviewer, and aren't a new open slice.
   - A W7 slice past its date gets a visible reassignment, cut, or schedule decision that day.
   - Before the first paid call, the project lead confirms the cap and estimates cost against the balance.
   - Development runs total at most 106 of Section 9's 120 trials, plus any pilots item 7, a C1-cost pilot, or a fallback smoke uses, and never over 120.
   - No security, utility, readiness, or floor rate from development runs is reported as a result.
   - Decision 0012's wiring stays, due Tuesday, November 10.
   - If the tier input or Gate 3 is `ENGINEERING`, decision 0024 items 5 and 7 apply to W8 and the later rows, with this record's dates.
   - Decision 0024's status becomes "Superseded by 0025", and its body doesn't change.

3. **The Gate 1 cap is lifted, and this record says what that is.**
   - It amends Section 11's Gate 1 response and Section 16's integration row after they fired.
   - Decision 0011 and the November 1 rollup applied the cap after the October 10 recovery check, so that check isn't new evidence.
   - The project lead chooses to target `F20` while no paid grid call, evaluation candidate, or evaluation outcome exists.
   - The Gate 1 response's stop on nonessential corpus growth is lifted for `W7-T2`'s evaluation-candidate target only.
   - Gate 1 stays "Not passed".
   - This takes effect only if merged before the first paid grid call.

4. **The Gate 2 step reopens.**
   - It runs the day `W7-T3`'s summary and `W7-T4` are merged with reviewer approval, no later than Saturday, November 7.
   - Gate 2's October 11 "Not passed" stays. Section 12 step 3's "pass Gate 2" means passing the binary readiness checks in this step (decision 0011 item 2), so `ALL` is possible again.
   - **Order.** `W7-T4`'s script and `W7-T1`'s smoke code merge before the paid-run record is written, and no paid grid or smoke call runs before that record. The script first runs on the mock grid to show it works, and that output decides nothing. Its checks and thresholds don't change after the first paid call. A later change leaves the affected defense not ready under Section 12, and its output is development evidence only.
   - **Floor.** No committed code evaluated the floor on October 31. Decision 0024 item 1's "15 of 15 cells missing" isn't a Section 10 evaluation. The reopened step is the one evaluation.
   - **If the step hasn't run by the end of November 7,** it closes with no readiness decision and doesn't move again. Committed code still evaluates the floor once at that close, over whatever grid records exist, with absent cells counted as missing, so a `BASE` row has counts to copy (Section 10). No `ALL` or `ONE` row is then selectable. A `BASE` row remains only if the summary of the D0_BASELINE grid cells and smokes merges by November 10 and the project lead records D0_BASELINE readiness against it (Section 12 step 3).

5. **W7 dates.**
   - #54, #63, #66, and #62 merge by Wednesday, November 4, each reviewed within 24 hours, and #64 merges by Thursday, November 5.
   - If no review of #62 has posted by the end of Tuesday, November 3, `W7-T3`'s one reviewer becomes T1 for #62 and the grid-summary pull request, a date-triggered schedule change. Each is then reviewed within 24 hours.
   - The paid grid and smokes need #62, #54, #63, decision 0023 (open as #64), and the Claude Console steps in item 11. Until #64 merges, the paid-run condition has three items, and no paid call runs.
   - What merges from the paid runs by Friday, November 6 is a summary under `docs/evidence/`: the output of `python -m runner.grid_dev summary`, the matching check for the smokes, the paid-run record's commit, and a SHA-256 manifest of every raw results and events file. It holds no raw provider bodies. Raw records stay outside Git, in access-controlled storage open to the project lead, `W7-T1`'s and `W7-T3`'s reviewers, and `W8-T1`'s owner. Mock runs never count.

6. **Evaluation candidates (`W7-T2`).**
   - **Target:** 24 candidates with ledger status `evaluation` and a completed source review, at least 12 per primary goal, none near-identical to a development, C1, or demo base.
   - **Fit:** counting at most 10 per source and 8 per family, the pool must still fill 20 bases with 10 per goal, from at least three sources and four families, and each must port to C2, C3, and C4. Meeting the count doesn't guarantee `P` = 20; the script decides.
   - **Dates:** a draft pull request by the end of Tuesday, November 3. Intake closes Thursday, November 5, which fixes `pool_hash`. With no pull request by then, T4 takes intake that day under a visible reassignment, intake stays open through Friday, November 6, and T2 keeps the rest of the slice.
   - **Source review:** the project lead signs off by the end of Saturday, November 7, and `W7-T2` merges by noon on Sunday, November 8. One worksheet per case-level record, with no check pre-answered, and the human opens each source. If T4 takes intake, the project lead stays the reviewer and opens and adapts no source (Section 5). `W8-T4`'s recheck of any sampled case T4 opened or adapted, under this takeover or decision 0021's pairing, moves to T5 by visible reassignment, so nobody rechecks a case they opened or adapted.
   - **Shortfall:** Section 5 step 8 builds the largest prefix the reviewed pool supports, and nobody fills it by hand. Under six bases there is no empirical prefix, and Gate 3 is `ENGINEERING` or `STOP`.

7. **Ten task variants.**
   - C2 and C4 for `read-ticket-status`, `invoice-receipt-email`, and `maintenance-confirm-email`; C3 and C4 for `open-ticket-ids`; C2 and C3 for `service-hours-extract`.
   - Each needs its Section 4 policy, validator, and oracle fixtures.
   - They land as lead scaffold by Friday, November 6, a visible scope addition that T1 reviews and `W8-T1` then freezes.
   - They must merge by Sunday, November 8, before `W8-T2` renders, or no row needing them can be selected: `R6` and `L8` need 2, `M10` needs 3, and `R15` and `F20` need all 10. With none merged, Gate 3 is `ENGINEERING` or `STOP`.
   - Each may take one live clean check from Section 9's remaining pilots, on coverage content only, which raises the development total to at most 116 of 120. That needs a new mock grid and paid-run record, because the record hashes the task files.

8. **Records this one requires.** Each is its own record:
   - **Before the paid-run record:** decisions on audit items A-01 and B-03, as built with a stated limitation or changed, because the floor is scored once.
   - **By Sunday, November 8:** the official C1 result-schema change, through Section 11 change control, with a deviation entry and re-pin.
   - **Before any C1-cost pilot, and by November 10:** a record superseding decision 0018's pilot example. Any C1-cost pilot uses development-base material only (Section 5).

9. **W8 before and after the Gate 2 step.**
   - This partly reverses decision 0022's rejected option 2, whose reason still holds for grid-derived work.
   - Before the Gate 2 step and tier input, W8 may do only this: `W8-T1`'s CI proof and notes; `W8-T2`'s release-safe payloads, notes, and first step (item 10); `W8-T3`'s generator, dormant `ENGINEERING` plan, report code, and sanitizer; `W8-T4`'s notes; and all of `W8-T5`. Apart from `W8-T5`'s pipeline freeze, no W8 work computes a freeze hash, marks a component frozen, or selects at a tier. Owners still hold one open slice at a time.
   - **Dates.** `W8-T5` keeps November 5 and 6. `W8-T1` opens within 24 hours of the paid summary merging, and no later than the morning of Monday, November 9. `W8-T2`, `W8-T3`, and `W8-T4` open by the morning of Monday, November 9, with reviews within 24 hours and last merge Tuesday, November 10.
   - `W8-T2` renders evaluation fixtures after its final search. A named same-week exception in `TASKS.md`'s dependency list, not a `Depends` cell, lets `W8-T4`'s recheck and `W8-T3`'s context-window check use `W8-T2`'s merged fixtures. `W8-T2` merges first, and each check lands in a last push its reviewer approves by the end of Tuesday, November 10.
   - Owners re-accept these rows by replying to the Monday, November 2 post by the end of Tuesday, November 3. A row not re-accepted by then is `BLOCKED` until a visible reassignment, tier, cut, or schedule decision (decision 0021 item 11).

10. **The tier input comes Sunday, November 8.**
    - That day `W8-T2`'s first step runs the selection script over the reviewed pool, which needs no tier, and posts `P` and the built prefixes.
    - The input cites `P`, the Gate 2 step's readiness decisions, the budget equation, and capacity, and it can't exceed `P`. "At the selected tier" in `W8-T2` and `W8-T4` means choosing `N` from the built prefixes. If a step 6 rejection lowers `P`, `W8-T2` records it, the project lead lowers the tier, and `W8-T4` redraws the recheck.
    - **Capacity.** On November 1, decision 0024 found capacity doesn't support an empirical row, and nothing measured has changed. This record targets `F20` anyway. The input records capacity against merged work and W8 work open that day, and lists what must still merge by November 10. A row that list doesn't support isn't selected.
    - **Count.** It counts only owners who re-accept this record's rows. A count of 5 sets the ceiling at `R15`.
    - **Fields.** Reason category, funded budget cap, season budget, accountable roles, and the Section 12 arithmetic. `claude-haiku-5-5` is expected, confirmed from Section 9's criteria 3 and 4. A missed date never activates `gpt-6-luna`. A changed decoding needs its own record.

11. **Budget and cap.**
    - **Bound.** Before any paid grid call, one trial's frozen maximum-token price bound is `MAX_STEPS × (I × input_rate + max_tokens × output_rate)`, with `MAX_STEPS` 8, `max_tokens` 4096, and decision 0010's rates. `I` is a number the project lead fixes with the bound, before any paid grid call, from the development renders and their tool-loop growth, because the Section 9 count over evaluation renders runs later in `W8-T3`. A request over 100,000 tokens uses the higher rates. If that count finds a larger request, the bound only rises, and the equation is re-evaluated before Gate 3. If the bound isn't frozen, the paid grid doesn't start. If it's undefined at the tier input, the equation can't be evaluated, no empirical row is supported, and the input is `ENGINEERING` or `STOP`.
    - **Reserve at `F20`.** (14 development + 30 rehearsal + 3 stage trials) × the frozen bound, computed by `analysis/gate2_budget.py` and not typed. The script is fixed before first use: thin strata and the C1 cost take the larger of the observed maximum and the bound (Section 9), lower tiers read their row, and a request over 100,000 tokens uses the higher rates.
    - **Cap.** Before the first paid call, a CANARY-only workspace with a $10 limit exists, every earlier Anthropic key that can draw on this balance is deleted, and Claude Console spend is reconciled with recorded usage. `remaining_funded_balance_at_gate_2` is the lesser of the credit and the workspace's remaining limit. If the October 10 check ran outside such a workspace, the Gate 2 step's record says so, and it stays one pilot with no injected content.
    - **If the equation fails at `F20`,** the tier drops, or the project lead loads credit, raises the workspace limit, records it in `STATUS.md` first, and re-evaluates.

12. **The sweep.**
    - It runs Wednesday, November 11 through Saturday, November 14 under `W9-T3`, whose owner keeps the slice and re-accepts by reply. The project lead's machine executes it. This takes effect when #64 merges.
    - After the Gate 3 step, the project lead reruns the mock grid on the frozen commit on the same machine and writes a new paid-run record before the first official call.
    - It runs on the host under the tool sandbox, not in the CI container. Its records carry a null `container_digest`, and Section 4, the manifest, and the paper state that limit.
    - The project lead sees only completeness, schema validity, cost, latency, provider errors, and safety logs until integrity checks pass. Raw records stay outside Git and reach `W9-T3`'s, `W11-T1`'s, and `W11-T4`'s owners through access-controlled storage the project lead sets up before the sweep.

13. **Misses follow `SPEC.md`, with no further move.**
    - No D0_BASELINE readiness at Gate 3: `ENGINEERING` or `STOP`.
    - A short pool or failed audit: a smaller verified prefix (Section 11 Gate 3 response).
    - `W8-T3` still builds the dormant `ENGINEERING` plan that Section 11 requires.

14. **Unchanged.**
    - Gate 3 on Wednesday, November 11, the November 22 data cutoff, and the December 6 release freeze.
    - The project lead's November 8 inputs, one reviewer per slice, and the 48-hour turnaround, except the 24-hour reviews items 5 and 9 name.
    - No evaluation candidate on a live model before the freeze.
    - W10 stays folded at `F20`; one interleaved sweep runs in `W9-T3`.

15. **Numbering.** This record takes 0025. Decision 0023 keeps its number on #64. `SPEC.md` moves to v1.17.0, with unpinned text changes only.

## Consequences

- **The tier isn't settled until November 8, and Gate 3 selects it.** Public posts lead with this reversal and promise no results.
- **The paper leads' November 16 draft depends on a tier set eight days earlier.** They hear this directly.
- **The project lead's load rises sharply:** source review of up to 24 records, the paid runs, the Gate 2 step, and the tier input, all by November 8, on top of the November 8 inputs.
- **T1 carries the most review load:** #54, #64, the task variants, and possibly #62 and the grid summary, on top of its own `W8-T1`.
- **A second reversal has a cost.** Decision 0024 was public for a day, and the record of both stays in `STATUS.md` and Git.

## Verification

- `tests/test_tasks_dependencies.py` passes unchanged, because no `Depends` cell changes.
- `tests/test_contract_lock.py`, `tests/test_corpus_rules_freeze.py`, and `tests/test_request_effect.py` pass unchanged, which shows no pinned `SPEC.md` text changed.
- `tests/test_status_consistency.py` passes against the corrected rollup, whose tier row names `F20`, and still rejects `F20` on a `SPEC.md` without the Gate 1 sentence.
- At Gate 3, `protocol/active.json` records the selected row, its arithmetic, and the cited `P`.
