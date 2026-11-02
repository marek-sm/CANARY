# CANARY Status — Club Week 10 — November 1, 2026

> This is a dated public summary, not a second task tracker or protocol. `TASKS.md` owns slice owners and states; `protocol/active.json` will own the exact frozen tier and run instance; `SPEC.md` owns scientific and release meaning. If this summary disagrees with one of those authorities, the authority wins and this file must be corrected.

## Current scope and gate

| Field | Current public state |
|---|---|
| Lifecycle state | Team implementation. Club week 10 (October 26–November 1) was the W7 week under [decision 0021](docs/decisions/0021-two-week-shift.md). `W6-T2` ([#34](https://github.com/marek-sm/CANARY/pull/34)) merged October 25, with the project lead's tool-result delivery, corpus-record schemas, and `dev-001` re-render after it ([#61](https://github.com/marek-sm/CANARY/pull/61)), so every W6 slice is on `main`. No W7 slice merged this week. Four W7 pull requests are open: [#62](https://github.com/marek-sm/CANARY/pull/62) (`W7-T3`), [#63](https://github.com/marek-sm/CANARY/pull/63) (`W7-T1`), [#66](https://github.com/marek-sm/CANARY/pull/66) (`W7-T5`), and [#54](https://github.com/marek-sm/CANARY/pull/54) (`W7-T4`). `W7-T2` has no pull request. W8 runs in club week 11, November 2–8 |
| Documentation baseline | `v1.0.0` committed in `149a706`; `SPEC.md` is v1.16.0. Recent decisions: [0022](docs/decisions/0022-start-on-merge.md), merged October 25 as [#60](https://github.com/marek-sm/CANARY/pull/60) (slices and gate steps start when their inputs merge, and every date is a latest date), and [0024](docs/decisions/0024-engineering-tier-input.md) (the Gate 2 step's close and the `ENGINEERING` tier input). Decision 0023 (the tool sandbox and the paid-run record) is open as [#64](https://github.com/marek-sm/CANARY/pull/64) |
| Active-contributor count | 6 — five portfolio owners plus the project lead, each of whom re-accepted their rows on October 26; `F20` is the Section 12 headcount ceiling, and the Gate 1 response caps it at `R15` |
| Gate 1 result | **Not passed** on September 27. The October 10 recovery check met every [`TASKS.md` Gate 1 item](TASKS.md#gate-1--end-of-week-5) after the deadline, so the result stands, and the `SPEC.md` Section 11 Gate 1 response still applies |
| Gate 2 result | **Not passed** on October 11, with the `SPEC.md` Section 11 Gate 2 response. The Gate 2 step closed on its latest date, Saturday, October 31, against `main` at `029b4eb`, with neither `W7-T3`'s live-model grid records nor `W7-T4`'s readiness script merged ([decision 0024](docs/decisions/0024-engineering-tier-input.md)). It recorded no readiness decision, so neither defense passes Gate 2. Decision 0021's slip rule fired: the November 11 Gate 3 choice is `ENGINEERING` or `STOP`. No later Gate 2 step runs |
| Measurement-contract lock | Done. It merged October 7 as [#35](https://github.com/marek-sm/CANARY/pull/35) under decisions [0008](docs/decisions/0008-content-filter-refusals.md) and [0009](docs/decisions/0009-measurement-contract-lock.md). The corpus-record schemas that 0009 item 8 left open merged October 25 in #61 |
| Active/provisional tier | Tier input `ENGINEERING`, given November 1 by [decision 0024](docs/decisions/0024-engineering-tier-input.md): no official model, with a readiness reason; 0 official trials; a $0 official budget cap. It replaces the provisional build geometry `M10-ALL` (decision 0011). It is provisional until the Gate 3 step's `protocol/active.json` makes the selection, and it holds even if readiness evidence lands before then. Gate 2 is closed with neither defense passing, and capacity doesn't support an empirical row's corpus, prefix, and provenance work by November 10 (`SPEC.md` Sections 9, 11, and 12). It carries no claim |
| Current protocol or run ID | Not created; required by Gate 3 |
| Next gate | Gate 3 — protocol freeze — Wednesday, November 11, on W8 work merged through Tuesday, November 10. At `ENGINEERING` it needs a zero-trial manifest and a frozen validation plan (`SPEC.md` Section 11). If it misses, the Section 11 Gate 3 response applies |
| Last green commit/container | `029b4eb`: CI run [40268616148](https://github.com/marek-sm/CANARY/actions/runs/40268616148), `test` and `docker` jobs, October 25 |
| Review | Exactly one reviewer per slice. Standing pairs by portfolio: T4 reviews T1, T3 reviews T2, T5 reviews T3, T1 reviews T4, and T2 reviews T5. The project lead reviews `W7-T2`, including the `SPEC.md` Section 5 source review. Every owner answers review comments, merge conflicts, and questions on their own pull requests within 48 hours, and reviewers review their pair's pull requests within 48 hours of opening (decisions 0021 and 0022) |
| Demo slot and operator | The slot is unconfirmed; no live duration or rehearsal target has been inferred. Demo Day falls in club week 16, December 7–11, after the December 6 release freeze. At `ENGINEERING` the presentation is replay-first (`SPEC.md` Section 13). Demo operator: Miles (T5), who accepted on October 11 |
| Judging rubric | Received September 26, 2026 from CSAI research leadership as the "Research Expectations" document; the project lead is recused from setting its criteria. Mapped in [`TASKS.md`](TASKS.md#judging-rubric-map), corrected October 7 in [#36](https://github.com/marek-sm/CANARY/pull/36), and re-paraphrased October 10 under [decision 0013](docs/decisions/0013-rubric-framing.md) |

## Evidence snapshot

| Evidence | Current public state |
|---|---|
| Development/model trials | Unchanged since October 10: one live adapter check (`make live-smoke` on `670dd31`), the W5-T1 ticket with no injected content, on `claude-haiku-5-5`, with 2 requests and no key recorded. It counts as 1 of the `SPEC.md` Section 9 ceiling's 15 reliability pilots. No live development-grid trial has run, and mock runs don't count toward the grid |
| Official empirical trials | None represented as started |
| `ENGINEERING` validation | Not activated; the Gate 3 step activates it |
| Corpus | Five development bases, four C1 records, and one demo case are on `main` since #34 merged October 25, each with the project lead's completed source review recorded as `marek-sm`. `dev-001` was re-rendered with its task's answer facts in #61. No evaluation candidate is on `main` |
| Spend and funded cap | As of November 1, 2026: no paid call is recorded in the repository since the October 10 live check, which used about $0.00014. Project-lead funded. [Decision 0010](docs/decisions/0010-anthropic-development-model.md) sets a $10 cap per provider, which the project lead confirms on the Claude Console before the next paid call. The OpenAI $10 prepaid cap is unused. CI stays mock-only. Under decision 0024 the official budget cap is $0, and the season budget is $10, decision 0010's Anthropic development cap, for development runs only |
| Repository audit | The October 17 read-only audit found 83 issues, none blocking. Fixes for 21 merged October 18 in [#51](https://github.com/marek-sm/CANARY/pull/51) and [#52](https://github.com/marek-sm/CANARY/pull/52), C-08 in [#56](https://github.com/marek-sm/CANARY/pull/56), and G-02 in [#57](https://github.com/marek-sm/CANARY/pull/57). F-01, the tool sandbox, is decision 0023 in #64; the rest are under way |
| Open protocol deviation | None open; the protocol is not frozen |
| Public result or defense-effect claim | None |

## Owner outcomes

The accepted owner and exact slice state live in [`TASKS.md`](TASKS.md). Under [decision 0024](docs/decisions/0024-engineering-tier-input.md), each W7 slice lands for W8 when its pull request merges with its named reviewer's approval, and a W7 slice not merged by the end of Wednesday, November 4 gets a visible reassignment, cut, or schedule decision in `TASKS.md` that day. Each W8 slice is `BLOCKED` until its W7 producers land, and its dates don't change: pull requests by Thursday, November 5, reviews by Friday, November 6, and last merge Tuesday, November 10.

| Portfolio | W7 (as of November 1) | W8 slice (club week 11, November 2–8) |
|---|---|---|
| T1 — Chace | `W7-T1`: [#63](https://github.com/marek-sm/CANARY/pull/63), opened October 26, in review | `W8-T1`: `BLOCKED` on `W7-T1` and `W7-T3` |
| T2 — Johan | `W7-T2`: no pull request. Under decision 0024 its intake closes when its pull request opens, no later than Wednesday, November 4 | `W8-T2`: `BLOCKED` on `W7-T2`. At `ENGINEERING` it freezes the source ledger |
| T3 — Samson | `W7-T3`: [#62](https://github.com/marek-sm/CANARY/pull/62), opened October 26, replaces #49 (closed that day) with the slice owner's commits and the review fixes; in review | `W8-T3`: `BLOCKED` on `W7-T3` and `W7-T2` |
| T4 — Dhruv | `W7-T4`: [#54](https://github.com/marek-sm/CANARY/pull/54), in review with a change request | `W8-T4`: `BLOCKED` on `W7-T4` and `W7-T2` |
| T5 — Miles | `W7-T5`: [#66](https://github.com/marek-sm/CANARY/pull/66), opened October 29, in review | `W8-T5`: `BLOCKED` on `W7-T5` |
| Project lead — Marek | After the October 25 rollup, merged #34 after re-approving it, #60 (decision 0022, `SPEC.md` v1.16.0), and #61 (tool-result delivery, the corpus-record schemas, and `dev-001`'s re-render), all October 25. Opened #62 on October 26 and #64 (decision 0023) on October 28; #64 carries the grid-usage and decoding fixes. Gave the tier input in decision 0024 | Still open: merge #64 after #62, then the paid-run record and the paid development runs; the gap sentence, license choice, and author order on November 8; the later rows' `ENGINEERING` text by November 8; decision 0012's wiring by November 10; and the Gate 3 step on November 11 |

## Public decisions, risks, and external asks

1. **Project presentation:** use `CANARY` in all caps and make no uniqueness or novelty claim. Under decisions [0016](docs/decisions/0016-practitioner-relevance.md) and [0017](docs/decisions/0017-applied-purpose.md), CANARY is applied research for teams choosing prompt-injection safeguards. It claims a gap in published work only in a sentence scoped to sources the project lead has opened, due November 8, and never a market gap.
2. **Tier and model:** under [decision 0024](docs/decisions/0024-engineering-tier-input.md), the tier input is `ENGINEERING`. There is no official model; the declared fallback `gpt-6-luna` isn't activated. The release is an instrument-validation package, with no official model estimate and no defense-effect claim. Development stays project-lead funded under decision 0010's cap. No paid or credentialed CI is permitted.
3. **Event inputs:** record the confirmed demo slot, Q&A, network, display, and speaker constraints when supplied. The paper leads' dates don't change: draft November 16, final claim language December 1, and final draft December 3. At `ENGINEERING` the paper is an instrument-validation report.
4. **Licensing:** do not accept external contributions or imply reuse rights until code/content licensing is selected, due November 8.
5. **Process:**
   - The Monday, November 2 post lists each W8 slice's owner, reviewer, latest dates, and `BLOCKED` producers ([decision 0015](docs/decisions/0015-cut-process-rules.md)). Each owner re-accepts the W8 rows that decision 0024 changed by replying to it.
   - Every owner answers review comments, merge conflicts, and questions within 48 hours, and reviewers review within 48 hours of opening (decisions 0021 and 0022).
6. **Risk — W7 merges by November 4:**
   - Every W8 slice waits on a W7 producer.
   - Three W7 pull requests are waiting for review: #62 and #63 since October 26, and #66 since October 29.
   - #54's change request has been open since October 25, and `W7-T2` has no pull request.
   - A W7 slice not merged by the end of Wednesday, November 4 gets a visible reassignment, cut, or schedule decision that day.
7. **Risk — Gate 3 (November 11):**
   - At `ENGINEERING`, the Gate 3 step needs every W8 freeze merged by Tuesday, November 10, a zero-trial `protocol/active.json`, and a frozen validation plan.
   - W8 has six days from the November 4 W7 date to its last merge.
8. **Paid development runs:**
   - Once #62 and #64 merge, the project lead runs the 90-cell mock grid, writes the paid-run record, and runs the paid grid and the 15 paid smokes, on development bases only.
   - They stay development evidence: no rate or count from them appears in a public artifact or the validation bundle.
   - They feed `W8-T1` only if their records merge by Friday, November 6.
9. **Risk — development trial ceiling:** `SPEC.md` Section 9 allows 120 development trials. The planned paid runs would use 105 more, for 106 in total, so a paid grid that fails part-way couldn't be rerun in full. Mock-provider runs don't count.
10. **Risk — turnaround:** decision 0021 found the binding constraint is turnaround, not the size of the work. A missed date on the critical path takes the slip rule or the Gate 3 response, never another move.

## Next seven days

- Monday, November 2: the W8 Monday post, with every W8 slice `BLOCKED` on its W7 producer. Owners re-accept the changed W8 rows by replying.
- W7 reviews and merges. Each W8 slice starts the day its producers land. Wednesday, November 4 is the latest W7 merge date.
- After #62 merges: #64 merges, then the mock grid, the paid-run record, and the paid development grid and smokes.
- Thursday, November 5: W8 pull requests are due. Friday, November 6: the review cutoff, and the last day paid records can feed `W8-T1`.
- Sunday, November 8: the gap sentence, the license choice, the author order, and the later rows' `ENGINEERING` text.
- Then: decision 0012's wiring and the last W8 merge by Tuesday, November 10, and the Gate 3 step on Wednesday, November 11.

## Weekly update rule

Update this file from repository evidence every Sunday during build and internal-release weeks. Report the current gate/tier, evidence links, public risks and asks, and next-seven-day outcomes. Summarize slice state by linking `TASKS.md`; never create a conflicting copy. Before the applicable lock, do not publish evaluation outcomes. At the December 6 release freeze ([decision 0021](docs/decisions/0021-two-week-shift.md)), record the immutable release tag/commit and manifest identifier. Week-15/16 entries may append confirmed logistics, factual submission status, and presentation-only observations without modifying the frozen release. `tests/test_status_consistency.py` checks each rollup against `TASKS.md`, `SPEC.md`, and the repository on every pull request; its docstring lists the rows a rollup keeps.
