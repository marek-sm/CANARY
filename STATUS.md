# CANARY Status — Club Week 7 — October 11, 2026

> This is a dated public summary, not a second task tracker or protocol. `TASKS.md` owns slice owners and states; `protocol/active.json` will own the exact frozen tier and run instance; `SPEC.md` owns scientific and release meaning. If this summary disagrees with one of those authorities, the authority wins and this file must be corrected.

## Current scope and gate

| Field | Current public state |
|---|---|
| Lifecycle state | Team implementation. Week 7 (October 5–11) was the recovery week. The lead's lock and the Anthropic adapter merged, but no Week 6 pull request merged by the October 9 deadline. The W7 slices run October 12–18. Week 8 onward was re-planned on October 11 ([decision 0011](docs/decisions/0011-week8-replan.md)): W8 runs October 19–25, W9 October 26–November 1, W10 is folded into W9 and W11, and W11–W13 keep their dates |
| Documentation baseline | `v1.0.0` committed in `149a706`; `SPEC.md` is now v1.7.0 through decisions [0008](docs/decisions/0008-content-filter-refusals.md), [0009](docs/decisions/0009-measurement-contract-lock.md), [0011](docs/decisions/0011-week8-replan.md), [0012](docs/decisions/0012-request-to-effect-table-and-tool-name-ablation.md), and [0013](docs/decisions/0013-rubric-framing.md) |
| Active-contributor count | 6 — five portfolio owners plus the project lead; `F20` is the Section 12 headcount ceiling, and the Gate 1 response caps it at `R15` |
| Gate 1 result | **Not passed** on September 27. The October 10 recovery check, on a fresh clone of `670dd31` with CI run [38078693195](https://github.com/marek-sm/CANARY/actions/runs/38078693195), met every [`TASKS.md` Gate 1 item](TASKS.md#gate-1--end-of-week-5), including the lock. The items were met after the deadline, so the result stands, and the `SPEC.md` Section 11 Gate 1 response still applies |
| Gate 2 result | **Not passed** on October 11, as the Week 7 recovery decision recorded in advance. The `SPEC.md` Section 11 Gate 2 response applies: no evaluation freeze until idempotent resume and D0_BASELINE readiness pass, and only a tier the binary defense checks, budget, and capacity support. The Gate 2 step runs Saturday, October 17, or Saturday, October 24 under the [slip rule](TASKS.md#gate-steps) |
| Measurement-contract lock | Done. It merged October 7 as [#35](https://github.com/marek-sm/CANARY/pull/35) under decisions [0008](docs/decisions/0008-content-filter-refusals.md) and [0009](docs/decisions/0009-measurement-contract-lock.md): the contract is at `1.0.0` and the locked `SPEC.md` text is hash-pinned. The corpus-record schemas left open by 0009 item 8 are lead scaffold, due October 18 |
| Active/provisional tier | Provisional build geometry: `M10-ALL` — 10 evaluation bases, 6 tasks, C2/C3, both defenses, and three C1 controls, set October 11 for capacity ([decision 0011](docs/decisions/0011-week8-replan.md)). It carries no claim, and Gate 3 confirms or lowers it under Section 12. The selection margin stays 4, two per primary goal, so `W7-T2`'s pool needs at least 7 `secret_disclosure` and 7 `unauthorized_action` candidates with ledger status `evaluation` and a completed source review. A pool under 20 needs a selection-prefix decision record before `W7-T2`'s pull request on October 15 |
| Current protocol or run ID | Not created; required by Gate 3 |
| Next gate | Gate 3 — protocol freeze — Wednesday, October 28, moved from October 18 by [decision 0011](docs/decisions/0011-week8-replan.md), with no backstop. If it misses, the `SPEC.md` Section 11 Gate 3 response applies |
| Last green commit/container | `670dd31`: CI run [38078693195](https://github.com/marek-sm/CANARY/actions/runs/38078693195), `test` and `docker` jobs, October 10 |
| Review | Exactly one reviewer per slice. Standing pairs by portfolio: T4 reviews T1, T3 reviews T2 (including the `SPEC.md` Section 5 source review), T5 reviews T3, T1 reviews T4, and T2 reviews T5 |
| Demo slot and operator | The slot is unconfirmed; no live duration or rehearsal target has been inferred. Demo operator (`SPEC.md` Section 13): not yet named, though it was due October 11. Until one is named, `W7-T5`'s replay runs with the operator are blocked |
| Judging rubric | Received September 26, 2026 from CSAI research leadership as the "Research Expectations" document; the project lead is recused from setting its criteria. Mapped the same day in [`TASKS.md`](TASKS.md#judging-rubric-map) and corrected October 7 in [#36](https://github.com/marek-sm/CANARY/pull/36), changing presentation emphasis only; re-paraphrased October 10 under [decision 0013](docs/decisions/0013-rubric-framing.md), with the separate Week 1–2 expectations noted in `TASKS.md` |

## Evidence snapshot

| Evidence | Current public state |
|---|---|
| Development/model trials | One live adapter check on October 10 (`make live-smoke` on `670dd31`), the W5-T1 ticket with no injected content. It ran on `claude-haiku-5-5`, made 2 requests, and recorded no key. It counts as 1 of the `SPEC.md` Section 9 ceiling's 15 reliability pilots. No development-grid trial has run |
| Official empirical trials | None represented as started |
| `ENGINEERING` validation | Not activated |
| Corpus | One development base, `dev-001`, merged with attack and clean twins through C2/C3/C4; its `reviewed_by` field still reads `PENDING_REVIEW`. The other four development bases are in `W6-T2`'s [#34](https://github.com/marek-sm/CANARY/pull/34), which hasn't merged. No evaluation candidate is on `main` |
| Spend and funded cap | As of October 11, 2026: project-lead funded under [decision 0010](docs/decisions/0010-anthropic-development-model.md), with a $10 cap per provider. The Anthropic account is prepaid, and its CANARY workspace had its $10 limit before the first call. The October 10 live check used 1,019 input and 80 output tokens, about $0.00014, and matched the Claude Console usage page. The OpenAI $10 prepaid cap is unused. CI stays mock-only. The season budget is set after the Gate 2 step |
| Open protocol deviation | None; the protocol is not frozen |
| Public result or defense-effect claim | None |

## Owner outcomes

The accepted owner and exact slice state live in [`TASKS.md`](TASKS.md). The recovery week required every Week 6 pull request to be reviewed and merged by Friday, October 9; none was. Each open pull request below is a blocker, with its owner and a 24-hour next action. Week 7 slices start Monday, October 12; their pull requests are due Thursday, October 15, and reviews by Friday, October 16. A W7 slice whose Week 6 input isn't on `main` that Monday starts `BLOCKED` under the [dependency rule](TASKS.md#dependency-discipline).

| Portfolio | Week 6 at the end of the recovery week (October 11) | W7 slice (October 12–18) |
|---|---|---|
| T1 — Chace | `W6-T1`: [#32](https://github.com/marek-sm/CANARY/pull/32) is open with its review requested and not given, and it conflicts with `main`. Next action: resolve the conflict and get the standing review | `W7-T1`: the 15 clean coverage smokes and the C1 controls, after `W6-T1`, `W6-T2`, and `W6-T3`. Its paid smokes wait on the paid-run condition |
| T2 — Johan | `W6-T2`: [#34](https://github.com/marek-sm/CANARY/pull/34) is open with its review and source review requested and not given, and it conflicts with `main`. Next action: resolve the conflict and get the standing review | `W7-T2`: evaluation intake to the 14-candidate pool and the committed selection script, after `W6-T2`. Early intake may start once `W6-T2` merges |
| T3 — Samson | `W6-T3`: Part A, [#31](https://github.com/marek-sm/CANARY/pull/31), is still a draft with no review; the rest of `W6-T3` has no pull request. Next action: mark Part A ready and request the standing review | `W7-T3`: a mock run of the full grid with the tool-result runner first, then the 90-cell development grid, forced resume, and the Gate 2 budget equation, after `W6-T1` to `W6-T4` |
| T4 — Dhruv | `W6-T4`: [#25](https://github.com/marek-sm/CANARY/pull/25) was approved by its standing reviewer on October 9 and hasn't merged. Next action: merge it | `W7-T4`: gate-versus-audit differential tests and the readiness-check script, after `W6-T1`, `W6-T3`, and `W6-T4` |
| T5 — Miles | `W6-T5`: [#28](https://github.com/marek-sm/CANARY/pull/28) has had a change request from its standing reviewer since October 5. Next action: address it and request re-review | `W7-T5`: two replay runs with the demo operator and the staged demo case, after `W6-T5`, `W6-T2`, and `W6-T3`. The operator step is blocked until one is named |
| Project lead — Marek | Merged the lock ([#35](https://github.com/marek-sm/CANARY/pull/35)), the `TASKS.md` paid-run condition and rubric fixes ([#36](https://github.com/marek-sm/CANARY/pull/36)), and the Anthropic adapter ([#37](https://github.com/marek-sm/CANARY/pull/37)). Ran the live adapter check and the Gate 1 recovery check, and gave paid-run access. Re-planned Week 8 onward | Tool-result delivery, as lead scaffold, once #31 and #32 merge; the request-to-effect table and tool-name-only ablation ([decision 0012](docs/decisions/0012-request-to-effect-table-and-tool-name-ablation.md)) before any paid call other than the live adapter check; the floor-count script before the grid's first paid call; the selection-prefix record before October 15; pairing on `W7-T3`; the demo operator; the Gate 2 step on October 17; the tier, budget, and model decision (October 25 under the slip rule) and the corpus-record schemas by October 18 |

## Public decisions, risks, and external asks

1. **Project presentation:** use `CANARY` in all caps and make no uniqueness or novelty claim.
2. **Funding/model:** under [decision 0010](docs/decisions/0010-anthropic-development-model.md), development is project-lead funded with a $10 cap per provider. `claude-haiku-5-5` is the development candidate and `gpt-6-luna` the declared fallback. The official model, the fallback decision, and the season budget are recorded before Gate 3 from development evidence. No paid or credentialed CI is permitted.
3. **Event inputs:** record the confirmed demo slot, Q&A, network, display, and speaker constraints when supplied.
4. **Licensing:** do not accept external contributions or imply reuse rights until code/content licensing is selected.
5. **Process:**
   - Since October 4, a slice that is `BLOCKED` on Monday starts the day its last input lands, with its dates unchanged ([`TASKS.md`](TASKS.md#dependency-discipline)).
   - Since October 7, the only exception to the recovery week's no-W7-work rule is early evaluation intake for `W7-T2`, once `W6-T2` merges.
   - From October 11, each owner whose pull request merged that week explains it in about three minutes at the Sunday check-in.
   - Weekly slice issues start with the W7 slices on October 12. *Replaced October 12 by the project lead under [decision 0015](docs/decisions/0015-cut-process-rules.md): a Monday team-channel post lists each slice's owner, reviewer, due date, and `BLOCKED` producers, with a link to its `TASKS.md` row.*
6. **Risk — W7 starts blocked:** every W7 slice depends on Week 6 work, and none of it is on `main`. Unless a producer merges by Monday, October 12, its consumers start `BLOCKED` and lose days from a week whose pull requests are due Thursday.
7. **Risk — Gate 2 evidence:**
   - Gate 2 is recorded not passed. Its step needs the live-model development grid, which needs `W6-T1` to `W6-T4` on `main`, tool-result delivery, and a full mock run first.
   - If the grid or the readiness script isn't merged by Friday, October 16, the step moves to October 24, and the tier, budget, and model decision moves from October 18 to October 25.
   - There is no second slip. Without a merged live-model grid by October 23, Gate 3's choice is `ENGINEERING` or `STOP`.
8. **Risk — Gate 3 (October 28):**
   - [Decision 0011](docs/decisions/0011-week8-replan.md) moved only Gate 3, with no backstop.
   - W8 work not merged by Friday, October 23 may merge through Tuesday, October 27. The sweep then has October 28 to November 1 for Gate 4's target, with November 8 as the absolute cutoff.
   - A miss on October 28 almost certainly means `ENGINEERING`.
   - The November 8 data cutoff and the November 22 release freeze don't move.
9. **Risk — delivery path:** the six-cell runner places untrusted content in the user message, so it measures direct rather than indirect injection. No slice row owned moving it into tool results, and `W6-T3`'s pull request doesn't do it. Since October 11 it is lead scaffold, built on top of [#31](https://github.com/marek-sm/CANARY/pull/31) and [#32](https://github.com/marek-sm/CANARY/pull/32) once they merge. Under the [paid-run condition](TASKS.md#lead-and-outside-inputs), no paid model call other than the project lead's live adapter check runs until it is on `main`, a full mock run of the grid has completed, and the request-to-effect table and tool-name-only ablation are on `main`. *The third part was added October 10 by the project lead under [decision 0012](docs/decisions/0012-request-to-effect-table-and-tool-name-ablation.md).*
10. **Risk — `dev-001` record:** its `reviewed_by` field is still `PENDING_REVIEW`; the owner corrects it, and T3 does the review.
11. **Risk — development trial ceiling:**
    - `SPEC.md` Section 9 allows 120 development trials: the 90-cell grid, 15 coverage smokes, and 15 pilots. The October 10 live check used one pilot.
    - A paid grid that fails part-way can't be rerun in full inside that ceiling.
    - Mock-provider runs don't count toward the 90-cell grid or the Gate 2 cost forecast.
12. **Risk — capacity:**
    - W8–W13 carry 93.5 estimated member hours at full `F20` scope, against about 62.5 hours of committed member capacity. The `M10-ALL` estimates save about 6.5 hours across the whole plan, all in tier-scaled cells.
    - Club week 10 is now the binding week, with the whole sweep in `W9-T3` and the folded release-candidate preparation in `W9-T5`.
    - A 14-candidate pool makes an M10 row the effective ceiling at Gate 3.
    - The Defer-first rows and the `SPEC.md` Section 12 cut order are the only relief.

## Next seven days

- Monday, October 12: the W7 slices start, and the project lead opens the five W7 issues, each recording its `BLOCKED` producers. The owners of `W8-T2`, `W9-T2`, `W9-T3`, `W9-T5`, `W11-T1`, and `W11-T4` re-accept their changed slices when those slices' Monday issues open. *Changed October 12 by the project lead under [decision 0015](docs/decisions/0015-cut-process-rules.md): the W7 slices go out in the Monday team-channel post instead of issues, and a changed slice is re-accepted by replying to that week's post.*
- Each open Week 6 pull request takes its next action above and merges as soon as it is reviewed.
- Tool-result delivery merges once #31 and #32 do (target Wednesday, October 14). The project lead records the date all three parts of the paid-run condition hold. No paid call other than the live adapter check runs before then. *The third part, the request-to-effect table and tool-name-only ablation, was added October 10 by the project lead under [decision 0012](docs/decisions/0012-request-to-effect-table-and-tool-name-ablation.md) and targets Tuesday, October 13.*
- The selection-prefix decision record lands before `W7-T2`'s pull request on Thursday, October 15.
- Thursday, October 15: W7 pull requests are open with their acceptance evidence. Friday, October 16: the review cutoff.
- Saturday, October 17: the Gate 2 step, if the live-model grid and readiness script are merged; otherwise the slip rule applies.
- Sunday, October 18: the rollup, the tier, budget, model, and decoding decision (October 25 under the slip rule), and the corpus-record schemas.

## Weekly update rule

Update this file from repository evidence every Sunday during build and internal-release weeks. Report the current gate/tier, evidence links, public risks and asks, and next-seven-day outcomes. Summarize slice state by linking `TASKS.md`; never create a conflicting copy. Before the applicable lock, do not publish evaluation outcomes. At the November 22 release freeze, record the immutable release tag/commit and manifest identifier. Week-15/16 entries may append confirmed logistics, factual submission status, and presentation-only observations without modifying the frozen release. `tests/test_status_consistency.py` checks each rollup against `TASKS.md`, `SPEC.md`, and the repository on every pull request; its docstring lists the rows a rollup keeps.
