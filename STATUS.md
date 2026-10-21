# CANARY Status — Club Week 8 — October 18, 2026

> This is a dated public summary, not a second task tracker or protocol. `TASKS.md` owns slice owners and states; `protocol/active.json` will own the exact frozen tier and run instance; `SPEC.md` owns scientific and release meaning. If this summary disagrees with one of those authorities, the authority wins and this file must be corrected.

## Current scope and gate

| Field | Current public state |
|---|---|
| Lifecycle state | Team implementation. Club week 8 (October 12–18) ran the W7 slices. Two Week 6 pull requests merged: `W6-T5` ([#28](https://github.com/marek-sm/CANARY/pull/28)) on October 13 and `W6-T4` ([#25](https://github.com/marek-sm/CANARY/pull/25)) on October 15. `W6-T1` ([#32](https://github.com/marek-sm/CANARY/pull/32)) and `W6-T2` ([#34](https://github.com/marek-sm/CANARY/pull/34)) are still open, and `W6-T3` passed to the project lead on October 15 under the [T3 capacity reassignment](TASKS.md#w7--gate-2-development-matrix-and-defense-readiness-october-1218). One W7 pull request is open, `W7-T3`'s [#49](https://github.com/marek-sm/CANARY/pull/49). Every W7 slice is `BLOCKED` on a Week 6 producer that isn't on `main`. W8 runs October 19–25 under [decision 0011](docs/decisions/0011-week8-replan.md) |
| Documentation baseline | `v1.0.0` committed in `149a706`; `SPEC.md` is now v1.13.0. This week's decisions: [0014](docs/decisions/0014-selection-prefixes-and-task-order.md) (selection prefixes for a pool under 20, and the task order), [0015](docs/decisions/0015-cut-process-rules.md) (cut process rules that don't protect the research), [0016](docs/decisions/0016-practitioner-relevance.md) and [0017](docs/decisions/0017-applied-purpose.md) (CANARY is applied research for teams choosing safeguards), [0018](docs/decisions/0018-c1-control-order.md) (C1 control order), and [0019](docs/decisions/0019-audit-doc-reconciliations.md) (documentation fixes from the October 17 audit) |
| Active-contributor count | 6 — five portfolio owners plus the project lead; `F20` is the Section 12 headcount ceiling, and the Gate 1 response caps it at `R15` |
| Gate 1 result | **Not passed** on September 27. The October 10 recovery check met every [`TASKS.md` Gate 1 item](TASKS.md#gate-1--end-of-week-5) after the deadline, so the result stands, and the `SPEC.md` Section 11 Gate 1 response still applies |
| Gate 2 result | **Not passed** on October 11, with the `SPEC.md` Section 11 Gate 2 response. Neither `W7-T3`'s live-model grid records nor `W7-T4`'s readiness script merged by Friday, October 16, so under the [slip rule](TASKS.md#gate-steps) the Gate 2 step runs Saturday, October 24, on work merged by Friday, October 23. There is no second slip |
| Measurement-contract lock | Done. It merged October 7 as [#35](https://github.com/marek-sm/CANARY/pull/35) under decisions [0008](docs/decisions/0008-content-filter-refusals.md) and [0009](docs/decisions/0009-measurement-contract-lock.md). The corpus-record schemas that 0009 item 8 left open were due October 18 as lead scaffold and wait on #34, so they fit the records it merges |
| Active/provisional tier | Provisional build geometry: `M10-ALL` — 10 evaluation bases, 6 tasks, C2/C3, both defenses, and three C1 controls, set October 11 for capacity ([decision 0011](docs/decisions/0011-week8-replan.md)). It carries no claim, and Gate 3 confirms or lowers it under Section 12. The selection margin stays 4, so `W7-T2`'s pool target is 14, at least 7 per primary goal; [decision 0014](docs/decisions/0014-selection-prefixes-and-task-order.md) sets the selection for a pool under 20. [Decision 0018](docs/decisions/0018-c1-control-order.md) takes the C1 controls in a hash order over the records that pass the project lead's source review |
| Current protocol or run ID | Not created; required by Gate 3 |
| Next gate | Gate 3 — protocol freeze — Wednesday, October 28, with no backstop ([decision 0011](docs/decisions/0011-week8-replan.md)). If it misses, the `SPEC.md` Section 11 Gate 3 response applies |
| Last green commit/container | `275d1c6`: CI run [39156716943](https://github.com/marek-sm/CANARY/actions/runs/39156716943), `test` and `docker` jobs, October 18 |
| Review | Exactly one reviewer per slice. Standing pairs by portfolio: T4 reviews T1, T3 reviews T2, T5 reviews T3, T1 reviews T4, and T2 reviews T5. Since October 15 the project lead reviews `W6-T2` and `W7-T2` instead of T3, including the `SPEC.md` Section 5 source review |
| Demo slot and operator | The slot is unconfirmed; no live duration or rehearsal target has been inferred. Demo operator (`SPEC.md` Section 13): Miles (T5), who accepted on October 11. *Correction: the October 11 rollup said no operator was named and listed the project lead's pairing on `W7-T3`. Miles had accepted, and the pairing was dropped, that same day, as [`TASKS.md`](TASKS.md#lead-and-outside-inputs) records* |
| Judging rubric | Received September 26, 2026 from CSAI research leadership as the "Research Expectations" document; the project lead is recused from setting its criteria. Mapped in [`TASKS.md`](TASKS.md#judging-rubric-map), corrected October 7 in [#36](https://github.com/marek-sm/CANARY/pull/36), and re-paraphrased October 10 under [decision 0013](docs/decisions/0013-rubric-framing.md) |

## Evidence snapshot

| Evidence | Current public state |
|---|---|
| Development/model trials | Unchanged since October 10: one live adapter check (`make live-smoke` on `670dd31`), the W5-T1 ticket with no injected content, on `claude-haiku-5-5`, with 2 requests and no key recorded. It counts as 1 of the `SPEC.md` Section 9 ceiling's 15 reliability pilots. No live development-grid trial has run. #49, not yet merged, adds a mock 90-cell orchestration check on fixture data to CI on the current runner, which places untrusted content in the user message. It is not the paid-run condition's full mock run, which needs tool-result delivery, and mock runs don't count toward the grid or the Gate 2 cost forecast |
| Official empirical trials | None represented as started |
| `ENGINEERING` validation | Not activated |
| Corpus | One development base, `dev-001`, is on `main` with attack and clean twins through C2/C3/C4. Its `reviewed_by` field still reads `PENDING_REVIEW`, and its renders don't carry the star rating and verified-purchase flag its assigned task asks for; the project lead re-renders it as lead scaffold once #32 and #34 merge. The other four development bases, the four C1 source records, and the demo case are in #34, where the project lead requested changes on October 16. No evaluation candidate is on `main` |
| Spend and funded cap | As of October 18, 2026: unchanged since October 10. Project-lead funded under [decision 0010](docs/decisions/0010-anthropic-development-model.md), with a $10 cap per provider; the October 10 live check used about $0.00014, matched against the Claude Console usage page. No other paid call is recorded in the repository. The OpenAI $10 prepaid cap is unused. CI stays mock-only. The season budget is set Sunday, October 25, after the Gate 2 step |
| Repository audit | A read-only audit of `main` at `31b9399` on October 17 found 83 issues, none blocking. Fixes for 21 merged October 18 in [#51](https://github.com/marek-sm/CANARY/pull/51) and [#52](https://github.com/marek-sm/CANARY/pull/52) ([decision 0019](docs/decisions/0019-audit-doc-reconciliations.md)); the rest are under way |
| Open protocol deviation | None; the protocol is not frozen |
| Public result or defense-effect claim | None |

## Owner outcomes

The accepted owner and exact slice state live in [`TASKS.md`](TASKS.md). W7 pull requests were due Thursday, October 15, and reviews Friday, October 16. A slice that is `BLOCKED` starts the day its last input lands, with its dates unchanged ([dependency rule](TASKS.md#dependency-discipline)).

| Portfolio | Week 6 (as of October 18) | W7 slice (October 12–18) |
|---|---|---|
| T1 — Chace | `W6-T1`: [#32](https://github.com/marek-sm/CANARY/pull/32) was approved by its standing reviewer on October 12 and hasn't merged; it conflicts with `main` | `W7-T1`: no pull request; `BLOCKED` on `W6-T1`, `W6-T2`, and `W6-T3`. Its row changed under [decision 0018](docs/decisions/0018-c1-control-order.md): it builds every C1 control that passes source review, and Chace re-accepts it by replying to the Monday post |
| T2 — Johan | `W6-T2`: [#34](https://github.com/marek-sm/CANARY/pull/34) is open; its reviewer, the project lead, requested changes on October 16, and it conflicts with `main` | `W7-T2`: no pull request; `BLOCKED` on `W6-T2` |
| T3 — Samson | `W6-T3` passed to the project lead on October 15. Samson's Part A, [#31](https://github.com/marek-sm/CANARY/pull/31), closed October 16, and its work continues in the project lead's [#47](https://github.com/marek-sm/CANARY/pull/47), which keeps its authorship and waits for its standing reviewer, Miles | `W7-T3`: Samson keeps it (decided October 18). [#49](https://github.com/marek-sm/CANARY/pull/49) opened October 16, stacked on #47, with CI green and its review requested from Miles; `BLOCKED` on `W6-T1`, `W6-T2`, and `W6-T3` |
| T4 — Dhruv | `W6-T4`: [#25](https://github.com/marek-sm/CANARY/pull/25) merged October 15 | `W7-T4`: no pull request; `BLOCKED` on `W6-T1` and `W6-T3` |
| T5 — Miles | `W6-T5`: [#28](https://github.com/marek-sm/CANARY/pull/28) merged October 13 | `W7-T5`: no pull request; `BLOCKED` on `W6-T2` and `W6-T3` |
| Project lead — Marek | Merged decisions 0014 to 0019 ([#41](https://github.com/marek-sm/CANARY/pull/41), [#45](https://github.com/marek-sm/CANARY/pull/45), [#46](https://github.com/marek-sm/CANARY/pull/46), [#50](https://github.com/marek-sm/CANARY/pull/50), [#52](https://github.com/marek-sm/CANARY/pull/52)), the end of the T3 pairing and the NeurIPS and IEEE checklist map ([#42](https://github.com/marek-sm/CANARY/pull/42)), the floor-count script ([#43](https://github.com/marek-sm/CANARY/pull/43)), the T3 capacity reassignment ([#48](https://github.com/marek-sm/CANARY/pull/48)), and the audit's code fixes ([#51](https://github.com/marek-sm/CANARY/pull/51)). Opened #47 and reviewed #34 | Still open: tool-result delivery, after #47 and #32; the `task_order` file after #32 and the corpus-record schemas after #34, both due October 18 and late, so `W8-T2` records those steps as blocked; `dev-001`'s answer facts, after #32 and #34; the #34 source review once its fixes land; the papers and reference 15 by October 25; the Gate 2 step on October 24; and the tier, budget, and model decision on October 25 |

## Public decisions, risks, and external asks

1. **Project presentation:** use `CANARY` in all caps and make no uniqueness or novelty claim. Under decisions [0016](docs/decisions/0016-practitioner-relevance.md) and [0017](docs/decisions/0017-applied-purpose.md), CANARY is applied research for teams choosing prompt-injection safeguards. It claims a gap in published work only in a sentence scoped to sources the project lead has opened, due October 25, and never a market gap.
2. **Funding/model:** under [decision 0010](docs/decisions/0010-anthropic-development-model.md), development is project-lead funded with a $10 cap per provider. `claude-haiku-5-5` is the development candidate and `gpt-6-luna` the declared fallback. The official model, the fallback decision, and the season budget are recorded before Gate 3 from development evidence. No paid or credentialed CI is permitted.
3. **Event inputs:** record the confirmed demo slot, Q&A, network, display, and speaker constraints when supplied.
4. **Licensing:** do not accept external contributions or imply reuse rights until code/content licensing is selected.
5. **Process:**
   - Since October 12 ([decision 0015](docs/decisions/0015-cut-process-rules.md)), a Monday team-channel post lists each slice's owner, reviewer, due date, and `BLOCKED` producers, and an owner re-accepts a changed slice by replying to it.
   - Each owner whose pull request merged that week explains it in about three minutes at the Sunday check-in: on October 18, Miles (#28) and Dhruv (#25).
   - On October 15 the project lead took `W6-T3` and T2's review, and on October 18 left `W7-T3` with Samson ([`TASKS.md`](TASKS.md#w7--gate-2-development-matrix-and-defense-readiness-october-1218)).
6. **Risk — Gate 2, with no second slip:**
   - The October 24 step needs the live-model development grid and `W7-T4`'s readiness script merged by Friday, October 23. Before the grid's first paid call, `W6-T1`, `W6-T2`, and `W6-T3` must merge, then tool-result delivery, then a full mock run of the grid; `dev-001`'s re-render must also land before that call.
   - None of these is on `main` today.
   - Without a merged live-model grid by October 23, Gate 3's choice is `ENGINEERING` or `STOP`.
7. **Risk — Gate 3 (October 28):**
   - All five W8 slices start Monday, October 19, `BLOCKED` on W7 producers that aren't on `main`.
   - W8 work not merged by Friday, October 23 may merge through Tuesday, October 27. A miss on October 28 almost certainly means `ENGINEERING`.
   - The November 8 data cutoff and the November 22 release freeze don't move.
8. **Risk — delivery path:** until tool-result delivery merges, the runner places untrusted content in the user message, so it measures direct rather than indirect injection. It is lead scaffold built on #47 and #32. Under the [paid-run condition](TASKS.md#lead-and-outside-inputs), no paid model call other than the live adapter check runs until it is on `main`, a full mock run of the grid has completed, and the request-to-effect table and tool-name-only ablation are on `main`. Only the third part holds ([#39](https://github.com/marek-sm/CANARY/pull/39)).
9. **Risk — `dev-001`:** its `reviewed_by` still reads `PENDING_REVIEW`; its source review is part of the project lead's review of #34. Its re-render with its task's answer facts follows #32 and #34.
10. **Risk — development trial ceiling:**
    - `SPEC.md` Section 9 allows 120 development trials: the 90-cell grid, 15 coverage smokes, and 15 pilots. The October 10 live check used one pilot.
    - A paid grid that fails part-way can't be rerun in full inside that ceiling.
    - Mock-provider runs don't count toward the 90-cell grid or the Gate 2 cost forecast.
11. **Risk — capacity:**
    - W8–W13 carry 93.5 estimated member hours at full `F20` scope, against about 62.5 hours of committed member capacity. The `M10-ALL` estimates save about 6.5 hours across the whole plan: 5.5 in tier-scaled cells and 1.0 in T5.
    - Club week 10 is the binding week, with the whole sweep in `W9-T3` and the folded release-candidate preparation in `W9-T5`.
    - The Defer-first rows and the `SPEC.md` Section 12 cut order are the only relief.

## Next seven days

- Monday, October 19: the W8 slices start, and the Monday post names each one's `BLOCKED` producers. Chace re-accepts `W7-T1`'s changed row, and Johan re-accepts `W8-T2`, changed by [decision 0011](docs/decisions/0011-week8-replan.md), by replying to it.
- #32, #34, and #47 take their reviews and merge; each W7 slice starts the day its last input lands.
- The project lead builds tool-result delivery after #47 and #32, the `task_order` file after #32, the corpus-record schemas after #34, and `dev-001`'s re-render after both, then records the date the paid-run condition holds.
- Thursday, October 22: W8 pull requests are due. Friday, October 23: the review cutoff, and the last merge the Gate 2 step uses.
- Saturday, October 24: the Gate 2 step.
- Sunday, October 25: the tier, budget, model, and decoding decision; the gap sentence or its absence, with reference 15 resolved ([decision 0017](docs/decisions/0017-applied-purpose.md)); and the judge-drill practice round at the check-in.

## Weekly update rule

Update this file from repository evidence every Sunday during build and internal-release weeks. Report the current gate/tier, evidence links, public risks and asks, and next-seven-day outcomes. Summarize slice state by linking `TASKS.md`; never create a conflicting copy. Before the applicable lock, do not publish evaluation outcomes. At the November 22 release freeze, record the immutable release tag/commit and manifest identifier. Week-15/16 entries may append confirmed logistics, factual submission status, and presentation-only observations without modifying the frozen release. `tests/test_status_consistency.py` checks each rollup against `TASKS.md`, `SPEC.md`, and the repository on every pull request; its docstring lists the rows a rollup keeps.
