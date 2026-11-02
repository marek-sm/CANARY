# 0024: Close the Gate 2 step and give the `ENGINEERING` tier input

- Status: Accepted. Approved by the project lead on 2026-11-01; drafted with AI assistance.
- Date: 2026-11-01
- Decision scope: Protocol
- Secondary scopes: Governance
- Related specification sections: Sections 1, 5, 9, 10, 11, 12, and 13
- Supersedes:
  - Decision 0022 item 2 as it applies to the Gate 2 step.
  - Decision 0011's provisional build geometry `M10-ALL`.
  - In `TASKS.md`, the two-week-shift note's "the Gate 2 step runs the day `W7-T3` and `W7-T4` are merged and reviewed, and the tier input follows once every W7 slice has merged".
  - In `TASKS.md`, the Gate 2 checklist's rule that its items "are ticked when their evidence lands" for the readiness item only.

## Context

On Sunday, November 1, `main` is at `029b4eb`, and no W7 slice has merged:

- `W7-T1` ([#63](https://github.com/marek-sm/CANARY/pull/63)), `W7-T3` ([#62](https://github.com/marek-sm/CANARY/pull/62)), and `W7-T5` ([#66](https://github.com/marek-sm/CANARY/pull/66)) are open and waiting for review.
- `W7-T4` ([#54](https://github.com/marek-sm/CANARY/pull/54)) is open with a change request.
- `W7-T2` has no pull request.
- No paid grid call has run. The tool sandbox and paid-run record (decision 0023, open as [#64](https://github.com/marek-sm/CANARY/pull/64)) are stacked on #62.

Decision 0021 item 6 fired on Friday, October 30. Neither `W7-T3`'s live-model grid records nor `W7-T4`'s readiness script was merged, so no comparable D0_BASELINE baseline is ready, neither defense passes Gate 2, and the November 11 Gate 3 choice is `ENGINEERING` or `STOP`. "There is no third move."

Two committed rules now pull against that:

- **Decision 0022 item 2** runs a gate step "on the first day every slice it uses is merged". Read literally, the Gate 2 step hasn't run, and it would run whenever `W7-T3` and `W7-T4` merge. That would be a third move in all but name, and W8, which "starts only after the Gate 2 step" (0022 item 1), would wait for it.
- **Several W8 rows** were written for an empirical tier. `W8-T4`'s provenance recheck, `W8-T3`'s context-window check, and the Gate 3 step's empty shells have no `ENGINEERING` form, and no rule says when an unmerged W7 slice counts as landed for W8.

Decision 0022 item 3 already dates the tier input: "If a W7 slice hasn't merged by November 1, the input comes November 1 from the merged evidence."

## Options considered

1. **Wait for W7, then run the Gate 2 step and give the tier input.** Rejected. No W7 result can change the Gate 3 choice (0021 item 6), so W8 would wait on a step with no effect.
2. **`STOP`.** Rejected. `ENGINEERING` keeps the safe tools, schemas, source ledger, replay, and a validation report (`SPEC.md` Section 12). A governed stop keeps the repository but adds nothing.
3. **Reopen an empirical tier through another move.** Rejected. Decision 0021 item 6 rules it out, and item 2 below shows capacity doesn't support one by Gate 3.
4. **Close the Gate 2 step today, give the `ENGINEERING` input, and write the `ENGINEERING` forms W7 and W8 lack.** Chosen.

## Decision

1. **The Gate 2 step is closed.**
   - It closed on its latest date, Saturday, October 31, against `main` at `029b4eb`. Neither input was on `main`, so it recorded no D1_POLICY_GATE or D2_DATAMARKING readiness decision. With no grid records, the Section 10 development-floor record is 15 of 15 cells missing, which matters only at an empirical tier.
   - No later Gate 2 step runs. A readiness check run later is development evidence (item 4), not a Gate 2 decision or a Section 12 tier input, and the Gate 2 checklist's readiness item is never ticked.
   - Gate 2 stays "Not passed". Neither defense passes Gate 2, and the Section 11 Gate 2 response applies.
   - Its closing is the Gate 2 step that decision 0022 items 1 and 3 wait for.

2. **The tier input is `ENGINEERING`.**
   - It is the project lead's tier, budget, model, and decoding input, given November 1 from the merged evidence (0022 item 3). It is an input and a provisional geometry, replacing `M10-ALL`. The Gate 3 step's `protocol/active.json` makes the selection.
   - It holds even if D0_BASELINE readiness evidence lands before November 11:
     - **No `ALL` row.** Section 12 step 3 says "`ALL` requires both D1_POLICY_GATE and D2_DATAMARKING to pass Gate 2." Gate 2 closed with neither passing, so no `ALL` row is selectable, whatever merges later.
     - **No capacity for a `ONE` or `BASE` row.** Those rows turn on readiness at Gate 3, so the clause that carries the input is capacity. The Section 11 Gate 2 response says to "choose only a tier supported by the binary defense checks, budget, and capacity". Section 9 activates `ENGINEERING` or `STOP` when no model meets the "implementation-capacity criteria" by Gate 3. On November 1, with no W7 slice merged, an empirical row would need all of these merged by November 10, six days after the November 4 W7 date:
       - the paid grid and coverage smokes, reviewed;
       - `W7-T2`'s reviewed pool and selection script;
       - `W8-T2`'s Section 5 step 8 prefix freeze and its Section 15 citation audit;
       - `W8-T4`'s seeded provenance recheck;
       - a frozen model and decoding configuration.

       This week's turnaround doesn't support that. The judgment is about capacity, recorded before any development or evaluation outcome exists.
     - **No empirical prefix at Gate 3.** Section 5 step 8 computes `P` when the selection script runs over the reviewed pool in week 8. Under item 5, `W8-T2` freezes the source ledger and doesn't run the script at a tier, and `W8-T4` runs no seeded recheck. So no empirical prefix or provenance audit exists at the Gate 3 step (Section 12 step 2; Section 11 Gate 3 pass evidence), and the Section 11 Gate 3 response leaves `ENGINEERING` or `STOP`. This follows from this input, not from what `main` holds today.
   - Its fields:
     - **Active contributors:** 6, the project lead and the five owners who re-accepted their rows on the Monday, October 26 post (0021 item 11).
     - **Non-personal reason category:** readiness, because no comparable D0_BASELINE baseline was ready by the Gate 2 slip date. Capacity is what holds it through Gate 3.
     - **Official model:** none, for the same reason. The declared fallback, `gpt-6-luna` (decision 0010), isn't activated, and a missed date never activates it.
     - **Official endpoint, `thinking`, `effort`, and `max_tokens`:** null, because no official model is frozen at `ENGINEERING`.
     - **Arithmetic:** 0 official trials, `K = 0`, and empty base, channel, C1-control, condition, configuration, run-index, schedule, and `stage_configurations` lists (Section 10).
     - **Official budget cap:** $0. It follows from zero official trials and isn't a second, funding reason.
     - **Season budget:** $10, decision 0010's Anthropic development cap, for development runs only. The OpenAI $10 cap stays unused. The measured development cost is the paid runs' recorded usage, about $0.00014 so far.
     - **Accountable roles:** the owner of each W8–W13 slice in `TASKS.md`, and the project lead.

3. **W7 still finishes, `W7-T2` included.**
   - **When a W7 slice lands.** It lands for its W8 consumers when its pull request merges with its named reviewer's approval. A paid step that hasn't run by then is recorded as blocked under the missing-input rule in `TASKS.md`. For `W7-T1` and `W7-T3`, that means the mock-run work in #63 and #62, with their paid records following in their own pull request (item 4). `W7-T3`'s Gate 2 budget equation is evaluated on whatever paid records exist and sets no official budget.
   - **`W7-T2` at `ENGINEERING`.**
     - Its committed row stands, except that intake closes when its pull request opens, no later than Wednesday, November 4. That close fixes `pool_hash` (Section 5 step 8).
     - The `ENGINEERING` input doesn't lower its pool target of 14, at least 7 per primary goal.
     - Every candidate it considered enters the source ledger with an explicit status and reason, with no silent drops (Section 5).
     - Its selection script is committed and tested on synthetic template IDs, and the project lead reviews each new source in its pull request.
     - No candidate ever enters a live model run (Section 11).
     - Its owner re-accepts the changed row by replying to the Monday, November 2 post.
   - **Latest W7 merge date: Wednesday, November 4.** If a W7 slice hasn't merged by the end of that day, the project lead records a visible reassignment, cut, or schedule decision for it in `TASKS.md` that day, under the ownership rule. An owner still holds one open slice at a time (0022 item 6), so each W8 slice starts after its owner's W7 slice merges.

4. **Paid development runs still happen, and stay development.**
   - **When and under what rule.** After #62 and #64 merge, the paid grid and the paid smokes run under the paid-run condition as it then reads on `main`. Before the first paid call, the project lead confirms decision 0010 item 4's spending cap on the Claude Console and estimates the grid and smokes together against the remaining balance.
   - **Who and what.**
     - The project lead opens the pull request that adds their records. Each slice's named reviewer reviews it.
     - It belongs to `W7-T3` and `W7-T1`, and isn't a new open slice.
     - They use development bases and coverage templates only. With the earlier live check, that's 1 + 90 grid trials + 15 smokes, or 106 of Section 9's 120.
   - **What they can feed.**
     - No security, utility, readiness, or floor rate or count from them appears in `STATUS.md`, the paper, the README, the demo, or the `ENGINEERING` validation bundle. Trial counts against the Section 9 ceiling and spend are still recorded.
     - They feed `W8-T1`'s defect fixes only if their records merge by Friday, November 6. Records merged after that feed no W8 slice.
     - After the Gate 3 freeze, a defect they reveal goes through Section 11 "After freeze".
   - **Readiness output.** `W7-T4`'s readiness script may run on these records once it merges. Its output is development evidence, labeled with whether the script merged before the first paid grid record existed. No artifact says a defense passed readiness or Gate 2.

5. **W8 at `ENGINEERING`.**
   - **Start and dates.** Every W8 slice starts when its W7 producers land (item 3) and is `BLOCKED` until then. Its dates don't change: pull request by Thursday, November 5, review by Friday, November 6, and last merge Tuesday, November 10 for the Gate 3 step.
   - **Rows.** Rows keep their existing `ENGINEERING` text. This record adds the rest:
     - **`W8-T1`:** "defects surfaced by the `W7-T3` grid and the `W7-T1` smokes" means the merged records: the mock records, plus paid records merged by November 6.
     - **`W8-T2`:** freezes the auditable source ledger instead of running the selection script at a tier, as its row already says. The Section 15 citation audit reopens every source the frozen ledger cites, accepted or rejected. Release-safe payload preparation still lands as its own part for `W9-T3`.
     - **`W8-T3`:** the `ENGINEERING` validation plan, schema, empty report shell, and generator become the active plan rather than the dormant fallback.
       - The empirical analysis and report code is still committed. Decision 0012's wiring lands in it, and it is frozen in the code commit, with the manifest's analysis hash null with a reason.
       - The Section 11 context-window check runs over the development bases' renders under every configuration, against `claude-haiku-5-5`'s context window with decision 0010's `max_tokens` reserved, as a named validation check.
     - **`W8-T4`:** D1_POLICY_GATE and D2_DATAMARKING freeze as named validation targets (Section 11). No Section 5 step 8 recheck runs, because no empirical prefix exists.
     - **`W8-T5`:** unchanged. It uses no W8 work.
     - **The Gate 3 step:** generates a zero-trial `protocol/active.json` with the frozen validation plan. `make report` produces the empty engineering-validation report from `W8-T3`'s frozen generator, not the empirical shells.
   - **Re-acceptance.** Owners re-accept the changed rows by replying to the Monday, November 2 post (decision 0015).
   - **Estimates.** `Est` stays at full `F20` scope, as `TASKS.md` defines it. The capacity table is updated when Gate 3 makes the tier active.

6. **Decision 0012's wiring is kept.**
   - The project lead lands it in `W8-T3`'s merged report code by Tuesday, November 10 (0021 item 5).
   - Its outputs read only official records, so at `ENGINEERING` they stay dormant, frozen in the code commit.
   - Nothing is withdrawn unless the wiring misses November 10 (0021 item 5). There is no pinned `SPEC.md` change, and paid-run condition item 3 stays met.

7. **Later rows take `SPEC.md`'s `ENGINEERING` forms.**
   - `W9-T3` already says "at `ENGINEERING`, the frozen validation matrix completes instead".
   - At `ENGINEERING`, Section 13's replay-first presentation replaces the live-first wording in these places. Their `TASKS.md` text is updated by Sunday, November 8, before W9 starts:
     - the `W13-T5` row;
     - the W12 and W13 rehearsal paragraph;
     - the club week 16 milestone and contribution rows;
     - decision 0021 item 9.
   - Decision 0022 item 2's optional Gate 3 hold for decision 0009 item 7's floor rerun is moot, because there is no development floor to rerun.

8. **Unchanged.**
   - Gate 3 on Wednesday, November 11.
   - The project lead's November 8 inputs.
   - The November 22 data cutoff and the December 6 release freeze.
   - The paid-run condition.
   - One reviewer per slice.
   - The 48-hour turnaround.
   - No evaluation candidate on a live model.

9. **Numbering.** This record takes 0024. Decision 0023 is the open sandbox record (#64), and it keeps its number. `SPEC.md` doesn't change.

## Consequences

- **The release is an instrument-validation package.** It has no official model estimate and no defense-effect claim (`SPEC.md` Sections 1 and 12). The paper leads draft an `ENGINEERING` report against their November 16 date.
- **The critical path is W7's reviews and merges by November 4.**
  - Each W8 slice starts the day its producer lands, and the paid runs no longer sit on that path.
  - `W8-T3` and `W8-T4` still wait on `W7-T2` under their `Depends` cells, though neither uses its pool at `ENGINEERING`. So `W7-T2`'s merge, or the November 4 decision about it, gates them too.
- **The paid runs are small and optional evidence.** They can surface a defect before the freeze, but they can't move the tier or appear as a result.
- **The project lead adds work before November 10:** the decision 0012 wiring and the later rows' `ENGINEERING` text.

## Verification

- `tests/test_tasks_dependencies.py` passes unchanged, because no `Depends` cell changes.
- `tests/test_contract_lock.py`, `tests/test_corpus_rules_freeze.py`, and `tests/test_request_effect.py` pass unchanged, which shows no pinned `SPEC.md` text changed.
- `tests/test_status_consistency.py` passes against the November 1 rollup, whose tier row names `ENGINEERING`.
- At Gate 3, `protocol/active.json` names `ENGINEERING` (Section 10) with:
  - 0 official trials;
  - null official-model fields, and a null `experiment_id` and schedule seed, each with its reason;
  - a non-null `validation_id` and source-ledger hash;
  - the frozen validation-plan hashes.
