# CANARY Status — Club Week 10 — November 1, 2026

> This is a dated public summary, not a second task tracker or protocol. `TASKS.md` owns slice owners and states; `protocol/active.json` will own the exact frozen tier and run instance; `SPEC.md` owns scientific and release meaning. If this summary disagrees with one of those authorities, the authority wins and this file must be corrected.

**Corrected November 2, 2026.** As first posted on November 1, this rollup gave an `ENGINEERING` tier input under [decision 0024](docs/decisions/0024-engineering-tier-input.md): no official model, no official trials, and no defense result. [Decision 0025](docs/decisions/0025-full-study.md) replaces it the next day, and the target is the full `F20` study. No evidence changed; the change is the project lead's direction. It is a target, not a selection or a result.

## Current scope and gate

| Field | Current public state |
|---|---|
| Lifecycle state | Team implementation. Club week 10 (October 26–November 1) was the W7 week under [decision 0021](docs/decisions/0021-two-week-shift.md). `W6-T2` ([#34](https://github.com/marek-sm/CANARY/pull/34)) merged October 25, with the project lead's tool-result delivery, corpus-record schemas, and `dev-001` re-render after it ([#61](https://github.com/marek-sm/CANARY/pull/61)), so every W6 slice is on `main`. No W7 slice has merged. Four W7 pull requests are open: [#62](https://github.com/marek-sm/CANARY/pull/62) (`W7-T3`), [#63](https://github.com/marek-sm/CANARY/pull/63) (`W7-T1`), [#66](https://github.com/marek-sm/CANARY/pull/66) (`W7-T5`), and [#54](https://github.com/marek-sm/CANARY/pull/54) (`W7-T4`). `W7-T2` has no pull request. W8 runs in club week 11, November 2–8 |
| Documentation baseline | `v1.0.0` committed in `149a706`; `SPEC.md` is v1.17.0. Recent decisions: [0022](docs/decisions/0022-start-on-merge.md), merged October 25 as [#60](https://github.com/marek-sm/CANARY/pull/60) (slices and gate steps start when their inputs merge, and every date is a latest date); [0024](docs/decisions/0024-engineering-tier-input.md), merged November 1 as [#67](https://github.com/marek-sm/CANARY/pull/67) and now superseded; and [0025](docs/decisions/0025-full-study.md). Decision 0023 (the tool sandbox and the paid-run record) is open as [#64](https://github.com/marek-sm/CANARY/pull/64) |
| Active-contributor count | 6 — five portfolio owners plus the project lead, each of whom re-accepted their rows on October 26; `F20` is the Section 12 headcount ceiling. Decision 0025 lifts the Gate 1 response's `R15` cap, and owners accept its rows by a reply or by work on the slice, read at the November 8 tier input ([decision 0027](docs/decisions/0027-acceptance-by-work.md)). A count of 5 sets the ceiling at `R15` |
| Gate 1 result | **Not passed** on September 27. The October 10 recovery check met every [`TASKS.md` Gate 1 item](TASKS.md#gate-1--end-of-week-5) after the deadline, so the result stands. Decision 0025 amends the `SPEC.md` Section 11 Gate 1 response for this run, after it fired, and that check isn't new evidence for doing so |
| Gate 2 result | **Not passed** on October 11, with the `SPEC.md` Section 11 Gate 2 response. Decision 0021's slip rule fired on October 30, with neither `W7-T3`'s live-model grid records nor `W7-T4`'s readiness script merged, and decision 0024 applied it. Decision 0025 reopens the Gate 2 step, which runs by Saturday, November 7. If it hasn't run by then, it closes with no readiness decision, and no `ALL` or `ONE` row is selectable; a `BASE` row remains only if the D0_BASELINE summary merges by November 10 and the project lead records its readiness. This is the third move decision 0021 said there wouldn't be |
| Measurement-contract lock | Done. It merged October 7 as [#35](https://github.com/marek-sm/CANARY/pull/35) under decisions [0008](docs/decisions/0008-content-filter-refusals.md) and [0009](docs/decisions/0009-measurement-contract-lock.md). The corpus-record schemas that 0009 item 8 left open merged October 25 in #61 |
| Active/provisional tier | Provisional build geometry: `F20` — 20 evaluation bases, 10 tasks, C2/C3/C4, both defenses, and four C1 controls, 1,092 official trials, set by [decision 0025](docs/decisions/0025-full-study.md) and replacing `M10-ALL` (decision 0011). It carries no claim. The project lead's tier input comes Sunday, November 8, from the prefix the reviewed pool supports, the readiness decisions, the budget equation, and capacity. The Gate 3 step makes the selection |
| Current protocol or run ID | Not created; required by Gate 3 |
| Next gate | Gate 3 — protocol freeze — Wednesday, November 11, on W8 work merged through Tuesday, November 10. If it misses, the `SPEC.md` Section 11 Gate 3 response applies |
| Last green commit/container | `e2fa7c2`: CI run [41402826746](https://github.com/marek-sm/CANARY/actions/runs/41402826746), November 1 |
| Review | Exactly one reviewer per slice. Standing pairs by portfolio: T4 reviews T1, T3 reviews T2, T5 reviews T3, T1 reviews T4, and T2 reviews T5. The project lead reviews `W7-T2`, including the `SPEC.md` Section 5 source review. Every owner answers review comments, merge conflicts, and questions on their own pull requests within 48 hours, and reviewers review their pair's pull requests within 48 hours of opening (decisions 0021 and 0022) |
| Demo slot and operator | The slot is unconfirmed; no live duration or rehearsal target has been inferred. Demo Day falls in club week 16, December 7–11, after the December 6 release freeze. Demo operator (`SPEC.md` Section 13): Miles (T5), who accepted on October 11 |
| Judging rubric | Received September 26, 2026 from CSAI research leadership as the "Research Expectations" document; the project lead is recused from setting its criteria. Mapped in [`TASKS.md`](TASKS.md#judging-rubric-map), corrected October 7 in [#36](https://github.com/marek-sm/CANARY/pull/36), and re-paraphrased October 10 under [decision 0013](docs/decisions/0013-rubric-framing.md) |

## Evidence snapshot

| Evidence | Current public state |
|---|---|
| Development/model trials | Unchanged since October 10: one live adapter check (`make live-smoke` on `670dd31`), the W5-T1 ticket with no injected content, on `claude-haiku-5-5`, with 2 requests and no key recorded. It counts as 1 of the `SPEC.md` Section 9 ceiling's 15 reliability pilots. No live development-grid trial has run, and mock runs don't count toward the grid |
| Official empirical trials | None represented as started |
| `ENGINEERING` validation | Not activated. `W8-T3` still builds the dormant plan `SPEC.md` Section 11 requires |
| Corpus | Five development bases, four C1 records, and one demo case are on `main` since #34 merged October 25, each with the project lead's completed source review recorded as `marek-sm`. `dev-001` was re-rendered with its task's answer facts in #61. No evaluation candidate is on `main`: 0 of the target 24 |
| Spend and funded cap | As of November 2, 2026: no paid call is recorded in the repository since the October 10 live check, which used about $0.00014. Project-lead funded. [Decision 0010](docs/decisions/0010-anthropic-development-model.md) sets a $10 cap per provider, which the project lead confirms on the Claude Console before the next paid call. The OpenAI $10 prepaid cap is unused. CI stays mock-only. The season budget comes with the tier input on November 8 |
| Repository audit | The October 17 read-only audit found 83 issues, none blocking. Fixes for 21 merged October 18 in [#51](https://github.com/marek-sm/CANARY/pull/51) and [#52](https://github.com/marek-sm/CANARY/pull/52), C-08 in [#56](https://github.com/marek-sm/CANARY/pull/56), and G-02 in [#57](https://github.com/marek-sm/CANARY/pull/57). F-01, the tool sandbox, is decision 0023 in #64. A-01 and B-03 are decided before the paid-run record under decision 0025; the rest are under way |
| Open protocol deviation | None open; the protocol is not frozen |
| Public result or defense-effect claim | None |

## Owner outcomes

The accepted owner and exact slice state live in [`TASKS.md`](TASKS.md). Under [decision 0025](docs/decisions/0025-full-study.md), #54, #63, #66, and #62 merge by Wednesday, November 4, #64 merges by Thursday, November 5, and a W7 slice past its date gets a visible reassignment, cut, or schedule decision that day. Each W8 slice is `BLOCKED` on its W7 producers, and before the Gate 2 step and tier input it may do only the tier-independent work the record lists.

| Portfolio | W7 (as of November 2) | W8 slice (club week 11, November 2–8) |
|---|---|---|
| T1 — Chace | `W7-T1`: [#63](https://github.com/marek-sm/CANARY/pull/63), approved November 1, waiting to merge | `W8-T1`: `BLOCKED` on `W7-T1` and `W7-T3`. It opens within 24 hours of the paid summary merging, and no later than Monday, November 9 |
| T2 — Johan | `W7-T2`: no pull request. A draft is due Tuesday, November 3, and intake closes Thursday, November 5 | `W8-T2`: `BLOCKED` on `W7-T2`. Its first step runs Sunday, November 8 |
| T3 — Samson | `W7-T3`: [#62](https://github.com/marek-sm/CANARY/pull/62), opened October 26, replaces #49 (closed that day) with the slice owner's commits and the review fixes; in review | `W8-T3`: `BLOCKED` on `W7-T3`; its pool steps wait for `W7-T2`. It opens by Monday, November 9 |
| T4 — Dhruv | `W7-T4`: [#54](https://github.com/marek-sm/CANARY/pull/54), fixes pushed November 1, in re-review | `W8-T4`: `BLOCKED` on `W7-T4`; its pool steps wait for `W7-T2`. It opens by Monday, November 9 |
| T5 — Miles | `W7-T5`: [#66](https://github.com/marek-sm/CANARY/pull/66), opened October 29, in review | `W8-T5`: `BLOCKED` on `W7-T5`. Pull request by Thursday, November 5, and review by Friday, November 6 |
| Project lead — Marek | After the October 25 rollup, merged #34 after re-approving it, #60 (decision 0022, `SPEC.md` v1.16.0), and #61 (tool-result delivery, the corpus-record schemas, and `dev-001`'s re-render), all October 25. Opened #62 on October 26 and #64 (decision 0023) on October 28; #64 carries the grid-usage and decoding fixes. Merged decision 0024 on November 1 and replaced it with decision 0025 | Still open: the price bound, A-01 and B-03, and the Claude Console workspace before any paid call; merge #64 after #62, then the paid-run record and the paid runs; the ten task variants after #63 and before the mock grid and paid-run record; source review and the Gate 2 step by November 7; the tier input, gap sentence, license choice, and author order on November 8; the C1 schema change by November 8; the record superseding decision 0018's pilot example and decision 0012's wiring by November 10; and the Gate 3 step on November 11 |

## Public decisions, risks, and external asks

1. **Project presentation:** use `CANARY` in all caps and make no uniqueness or novelty claim. Under decisions [0016](docs/decisions/0016-practitioner-relevance.md) and [0017](docs/decisions/0017-applied-purpose.md), CANARY is applied research for teams choosing prompt-injection safeguards. It claims a gap in published work only in a sentence scoped to sources the project lead has opened, due November 8, and never a market gap.
2. **Tier and model:** under [decision 0025](docs/decisions/0025-full-study.md), the target is `F20`. `claude-haiku-5-5` is the expected model and `gpt-6-luna` the declared fallback; a missed date never activates it. Both are confirmed with the tier input. No paid or credentialed CI is permitted. No result exists, and none is promised.
3. **Event inputs:** record the confirmed demo slot, Q&A, network, display, and speaker constraints when supplied. The paper leads' dates don't change: draft November 16, final claim language December 1, and final draft December 3. The tier they draft against is set November 8.
4. **Licensing:** do not accept external contributions or imply reuse rights until code/content licensing is selected, due November 8.
5. **Process:**
   - On Monday, November 2, the project lead told each owner their work, reviews, and latest dates directly, in place of that week's team-channel post ([decision 0027](docs/decisions/0027-acceptance-by-work.md)). An owner accepts decision 0025's rows by a reply or by work on the slice.
   - Every owner answers review comments, merge conflicts, and questions within 48 hours, and reviewers review within 48 hours of opening (decisions 0021 and 0022).
6. **Risk — evaluation candidates, the largest:**
   - `F20` needs 24 source-reviewed candidates that fit `SPEC.md` Section 5's caps, and 0 are on `main`.
   - Section 5 step 8 builds only the prefix the reviewed pool supports (20, 15, 10, 8, or 6). Under six bases there is no empirical prefix.
7. **Risk — W7 and new work:**
   - #62 and #66 are waiting for review, #63 is waiting to merge, and #54 is in re-review.
   - No paid grid or smoke call runs until #62, #54, #63, and #64 have merged and the price bound, A-01 and B-03, and the Console workspace are done.
   - Ten task variants and the official C1 schema change are new lead work that no slice owned.
8. **Risk — capacity:** decision 0024 found on November 1 that capacity doesn't support an empirical row, and nothing measured has changed. The tier input records capacity against merged work, and a row it doesn't support isn't selected.
9. **Risk — budget:** `SPEC.md` Section 9's equation can't be evaluated until the price bound is frozen and the grid has run. If it fails at `F20`, the tier drops, or the project lead raises the funded cap and records it here first.
10. **Risk — development trial ceiling:** `SPEC.md` Section 9 allows 120 development trials. The planned paid runs would bring the total to 106, more with live checks of the new variants or a C1-cost pilot and never over 120, so a paid grid that fails part-way couldn't be rerun in full. Mock-provider runs don't count.
11. **Sweep environment:** once #64 merges, the official sweep runs on the project lead's machine under the tool sandbox, outside the CI container. The manifest and the paper state that limit.
12. **Risk — turnaround:** decision 0021 found the binding constraint is turnaround, not the size of the work. Decision 0025 adds dated tripwires, and no improvement has been measured. A missed date takes its tripwire or the `SPEC.md` response, with no further move.

## Next seven days

- Monday, November 2: the correction, and each owner's work and dates sent directly.
- Tuesday, November 3: `W7-T2`'s draft pull request, the review of #62 or its move to T1, the price bound, and A-01 and B-03.
- Wednesday, November 4: #54, #63, #66, and #62 merged.
- Thursday, November 5: #64 and the ten task variants merged, the variants after #63. Then the mock grid, the paid-run record, and the paid grid and smokes.
- Also Thursday, November 5: `W7-T2`'s intake closes, and `W8-T5`'s pull request is due.
- Friday, November 6: the summary of the paid runs merged, and `W8-T5` reviewed.
- Saturday, November 7: source sign-off and the Gate 2 step.
- Sunday, November 8: `W7-T2` merges by noon, `W8-T2` posts `P`, and then the tier input, C1 schema change, gap sentence, license choice, and author order.
- Then: `W8-T1`, `W8-T2`, `W8-T3`, and `W8-T4` open by the morning of November 9, and decision 0012's wiring and the last W8 merge land by November 10, with the Gate 3 step on November 11.

## Weekly update rule

Update this file from repository evidence every Sunday during build and internal-release weeks. Report the current gate/tier, evidence links, public risks and asks, and next-seven-day outcomes. Summarize slice state by linking `TASKS.md`; never create a conflicting copy. Before the applicable lock, do not publish evaluation outcomes. At the December 6 release freeze ([decision 0021](docs/decisions/0021-two-week-shift.md)), record the immutable release tag/commit and manifest identifier. Week-15/16 entries may append confirmed logistics, factual submission status, and presentation-only observations without modifying the frozen release. `tests/test_status_consistency.py` checks each rollup against `TASKS.md`, `SPEC.md`, and the repository on every pull request; its docstring lists the rows a rollup keeps.
