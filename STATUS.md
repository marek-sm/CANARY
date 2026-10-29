# CANARY Status — Club Week 9 — October 25, 2026

> This is a dated public summary, not a second task tracker or protocol. `TASKS.md` owns slice owners and states; `protocol/active.json` will own the exact frozen tier and run instance; `SPEC.md` owns scientific and release meaning. If this summary disagrees with one of those authorities, the authority wins and this file must be corrected.

## Current scope and gate

| Field | Current public state |
|---|---|
| Lifecycle state | Team implementation. Club week 9 (October 19–25) closed most of Week 6: `W6-T3` Part A merged October 22 as the project lead's [#47](https://github.com/marek-sm/CANARY/pull/47), which keeps #31's authorship, and `W6-T1` ([#32](https://github.com/marek-sm/CANARY/pull/32)) merged October 24. `W6-T2` ([#34](https://github.com/marek-sm/CANARY/pull/34)) passed the project lead's source review and was approved October 24, and it merges once its owner merges current `main` (Makefile and README conflicts from later merges) and the project lead re-approves. [Decision 0021](docs/decisions/0021-two-week-shift.md), merged October 23 as [#58](https://github.com/marek-sm/CANARY/pull/58), moves every lattice week from W7 on two working weeks later, once: W7 runs in club week 10, October 26–November 1. Two W7 pull requests are open, [#49](https://github.com/marek-sm/CANARY/pull/49) (`W7-T3`) and [#54](https://github.com/marek-sm/CANARY/pull/54) (`W7-T4`), each with a change request |
| Documentation baseline | `v1.0.0` committed in `149a706`; `SPEC.md` is now v1.15.0. This week's decisions: [0020](docs/decisions/0020-request-level-formula.md) (the Section 7 request-level formulas, with DEV-0002 in [`docs/protocol_deviations.md`](docs/protocol_deviations.md)) and [0021](docs/decisions/0021-two-week-shift.md) (the two-working-week shift and a 48-hour turnaround rule) |
| Active-contributor count | 6 — five portfolio owners plus the project lead; `F20` is the Section 12 headcount ceiling, and the Gate 1 response caps it at `R15` |
| Gate 1 result | **Not passed** on September 27. The October 10 recovery check met every [`TASKS.md` Gate 1 item](TASKS.md#gate-1--end-of-week-5) after the deadline, so the result stands, and the `SPEC.md` Section 11 Gate 1 response still applies |
| Gate 2 result | **Not passed** on October 11, with the `SPEC.md` Section 11 Gate 2 response. Under decision 0021 the October 24 step didn't run: the Gate 2 step runs Saturday, October 31, on work merged by Friday, October 30. There is no third move. If `W7-T3`'s live-model grid records aren't merged by October 30, Gate 3's choice is `ENGINEERING` or `STOP`. If `W7-T4`'s readiness script isn't merged, neither defense passes Gate 2, and `SPEC.md` Section 12 step 3 applies |
| Measurement-contract lock | Done. It merged October 7 as [#35](https://github.com/marek-sm/CANARY/pull/35) under decisions [0008](docs/decisions/0008-content-filter-refusals.md) and [0009](docs/decisions/0009-measurement-contract-lock.md). The corpus-record schemas that 0009 item 8 left open are built as lead scaffold and land after #34, so they fit the records it merges |
| Active/provisional tier | Provisional build geometry: `M10-ALL` — 10 evaluation bases, 6 tasks, C2/C3, both defenses, and three C1 controls, set October 11 for capacity ([decision 0011](docs/decisions/0011-week8-replan.md)). It carries no claim, and Gate 3 confirms or lowers it under Section 12. The selection margin stays 4, so `W7-T2`'s pool target is 14, at least 7 per primary goal ([decision 0014](docs/decisions/0014-selection-prefixes-and-task-order.md)). [Decision 0018](docs/decisions/0018-c1-control-order.md) takes the C1 controls in a hash order over the records that pass the project lead's source review |
| Current protocol or run ID | Not created; required by Gate 3 |
| Next gate | Gate 3 — protocol freeze — Wednesday, November 11 ([decision 0021](docs/decisions/0021-two-week-shift.md)), on W8 work merged through Tuesday, November 10. If it misses, the `SPEC.md` Section 11 Gate 3 response applies |
| Last green commit/container | `9365814`: CI run [40139152811](https://github.com/marek-sm/CANARY/actions/runs/40139152811), `test` and `docker` jobs, October 24 |
| Review | Exactly one reviewer per slice. Standing pairs by portfolio: T4 reviews T1, T3 reviews T2, T5 reviews T3, T1 reviews T4, and T2 reviews T5. Since October 15 the project lead reviews `W6-T2` and `W7-T2` instead of T3, including the `SPEC.md` Section 5 source review. From October 26, every owner answers review comments, merge conflicts, and questions on their own pull requests within 48 hours (decision 0021 item 4) |
| Demo slot and operator | The slot is unconfirmed; no live duration or rehearsal target has been inferred. Demo Day falls in club week 16, December 7–11, after the December 6 release freeze. Demo operator (`SPEC.md` Section 13): Miles (T5), who accepted on October 11 |
| Judging rubric | Received September 26, 2026 from CSAI research leadership as the "Research Expectations" document; the project lead is recused from setting its criteria. Mapped in [`TASKS.md`](TASKS.md#judging-rubric-map), corrected October 7 in [#36](https://github.com/marek-sm/CANARY/pull/36), and re-paraphrased October 10 under [decision 0013](docs/decisions/0013-rubric-framing.md) |

## Evidence snapshot

| Evidence | Current public state |
|---|---|
| Development/model trials | Unchanged since October 10: one live adapter check (`make live-smoke` on `670dd31`), the W5-T1 ticket with no injected content, on `claude-haiku-5-5`, with 2 requests and no key recorded. It counts as 1 of the `SPEC.md` Section 9 ceiling's 15 reliability pilots. No live development-grid trial has run, and mock runs don't count toward the grid or the Gate 2 cost forecast |
| Official empirical trials | None represented as started |
| `ENGINEERING` validation | Not activated |
| Corpus | One development base, `dev-001`, is on `main`, with attack and clean twins through C2/C3/C4. On `main` its `reviewed_by` still reads `PENDING_REVIEW`. #34 carries the project lead's completed source review of all ten records (`dev-001` to `dev-005`, `c1-001` to `c1-004`, and `demo-001`), recorded as `marek-sm` in every record and ledger row. `dev-001`'s re-render with its task's answer facts follows #34 as lead scaffold. No evaluation candidate is on `main` |
| Spend and funded cap | As of October 25, 2026: unchanged since October 10. Project-lead funded under [decision 0010](docs/decisions/0010-anthropic-development-model.md), with a $10 cap per provider; the October 10 live check used about $0.00014, matched against the Claude Console usage page. No other paid call is recorded in the repository. The OpenAI $10 prepaid cap is unused. CI stays mock-only. The season budget is set Sunday, November 1, after the Gate 2 step |
| Repository audit | The October 17 read-only audit found 83 issues, none blocking. Fixes for 21 merged October 18 in [#51](https://github.com/marek-sm/CANARY/pull/51) and [#52](https://github.com/marek-sm/CANARY/pull/52). This week C-08 merged in [#56](https://github.com/marek-sm/CANARY/pull/56) and G-02 in [#57](https://github.com/marek-sm/CANARY/pull/57) (decision 0020); the rest are under way |
| Open protocol deviation | None open; the protocol is not frozen. DEV-0002 records decision 0020's change to pinned Section 7 text |
| Public result or defense-effect claim | None |

## Owner outcomes

The accepted owner and exact slice state live in [`TASKS.md`](TASKS.md). Under decision 0021, W7 pull requests are due Thursday, October 29, and reviews Friday, October 30. A slice that is `BLOCKED` starts the day its last input lands, with its dates unchanged ([dependency rule](TASKS.md#dependency-discipline)).

| Portfolio | Week 6 (as of October 25) | W7 slice (club week 10, October 26–November 1) |
|---|---|---|
| T1 — Chace | `W6-T1`: [#32](https://github.com/marek-sm/CANARY/pull/32) merged October 24, after its standing reviewer re-approved the conflict resolution | `W7-T1`: no pull request yet. `W6-T1` and `W6-T3` are on `main`; it stays `BLOCKED` on `W6-T2`'s C1 source records |
| T2 — Johan | `W6-T2`: [#34](https://github.com/marek-sm/CANARY/pull/34) approved October 24 after the project lead's source review passed all ten records; it conflicts with `main` after later merges | `W7-T2`: no pull request yet; `BLOCKED` on `W6-T2`. Intake may start the day #34 merges (decision 0021 item 2), with T4 pairing on candidate search |
| T3 — Samson | `W6-T3`: merged October 22 as the project lead's [#47](https://github.com/marek-sm/CANARY/pull/47), keeping Part A's authorship | `W7-T3`: [#49](https://github.com/marek-sm/CANARY/pull/49) is in review, with its standing reviewer's October 18 comments open, and its base is still `lead/w6-t3-part-a`, #47's merged branch, not `main`; `BLOCKED` on `W6-T2` for the development bases |
| T4 — Dhruv | `W6-T4`: [#25](https://github.com/marek-sm/CANARY/pull/25) merged October 15 | `W7-T4`: [#54](https://github.com/marek-sm/CANARY/pull/54) merged current `main` on October 24 and is in review, with its standing reviewer's October 25 comments open. Its inputs are on `main` |
| T5 — Miles | `W6-T5`: [#28](https://github.com/marek-sm/CANARY/pull/28) merged October 13 | `W7-T5`: no pull request yet; `BLOCKED` on `W6-T2`'s demo case. `W6-T3`'s records are on `main` |
| Project lead — Marek | Merged #47 (`W6-T3` Part A), #56 (audit C-08), #57 (decision 0020, `SPEC.md` v1.14.0, DEV-0002), #58 (decision 0021, `SPEC.md` v1.15.0), and the `task_order` file with a hash check on the locked schemas. Finished the #34 source review | Still open: tool-result delivery, the corpus-record schemas, and `dev-001`'s re-render, all built and landing after #34; the paid-run condition's date; the Gate 2 step on October 31; the tier, budget, and model decision on November 1; the gap sentence and the license and author order on November 8; and decision 0012's wiring by November 10 |

**October 29 W7-T5 progress note.** The W6-T2 demo source and lead-owned
tool-result-delivery inputs are now on `main`, so the October 25 T5 blocker above
is resolved. Miles confirmed two separate no-notes starts of the read-only mock
replay without provider access. The W7-T5 branch stages the excluded demo case,
adds a current-schema fallback and plain-language presentation summary, and
keeps all output explicitly illustrative. The slice awaits pull-request review;
this note records no empirical result or defense claim.

## Public decisions, risks, and external asks

1. **Project presentation:** use `CANARY` in all caps and make no uniqueness or novelty claim. Under decisions [0016](docs/decisions/0016-practitioner-relevance.md) and [0017](docs/decisions/0017-applied-purpose.md), CANARY is applied research for teams choosing prompt-injection safeguards. It claims a gap in published work only in a sentence scoped to sources the project lead has opened, now due November 8, and never a market gap.
2. **Funding/model:** under [decision 0010](docs/decisions/0010-anthropic-development-model.md), development is project-lead funded with a $10 cap per provider. `claude-haiku-5-5` is the development candidate and `gpt-6-luna` the declared fallback. The official model, the fallback decision, and the season budget are recorded on November 1, before Gate 3, from development evidence. No paid or credentialed CI is permitted.
3. **Event inputs:** record the confirmed demo slot, Q&A, network, display, and speaker constraints when supplied. Decision 0021 sets the paper leads' dates: draft November 16, final claim language December 1, and final draft December 3.
4. **Licensing:** do not accept external contributions or imply reuse rights until code/content licensing is selected, now due November 8.
5. **Process:**
   - A Monday team-channel post lists each slice's owner, reviewer, due date, and `BLOCKED` producers, and an owner re-accepts a changed slice by replying to it ([decision 0015](docs/decisions/0015-cut-process-rules.md)). On October 26 every owner re-accepts the re-dated W7–W13 rows, including the two reassigned release items and the T4 pairing (decision 0021 items 8 and 11).
   - From October 26, every owner answers review comments, merge conflicts, and questions within 48 hours (decision 0021 item 4).
6. **Risk — Gate 2, with no third move:**
   - The October 31 step needs `W7-T3`'s live-model development grid and `W7-T4`'s readiness script merged by Friday, October 30.
   - Before the grid's first paid call, #34 merges; then tool-result delivery, `dev-001`'s re-render, and a full mock run of the grid; then the project lead records the date the paid-run condition holds.
   - None of the grid steps is on `main` today, and #34 is the input every one of them waits on.
7. **Risk — Gate 3 (November 11):**
   - W8 runs in club week 11, November 2–8, with late W8 merges through Tuesday, November 10.
   - The November 22 data cutoff is absolute, and week 14 is dark, so a late W11 merge can't use it. The December 6 release freeze falls right before the Demo Day week, and W12 and W13 share club week 15 with no buffer week.
8. **Risk — delivery path:** until tool-result delivery merges, the runner places untrusted content in the user message, so it measures direct rather than indirect injection. Delivery is built, and its tests use all five development bases, so it lands the day #34 merges. Under the [paid-run condition](TASKS.md#lead-and-outside-inputs), no paid model call other than the live adapter check runs until delivery is on `main`, a full mock run of the grid has completed, and the request-to-effect table and tool-name-only ablation are on `main`. Only the third part holds ([#39](https://github.com/marek-sm/CANARY/pull/39)).
9. **Risk — `dev-001`:** its source review is complete in #34, but `main` reads `PENDING_REVIEW` until #34 merges. Its re-render with its task's answer facts follows #34.
10. **Risk — development trial ceiling:**
    - `SPEC.md` Section 9 allows 120 development trials: the 90-cell grid, 15 coverage smokes, and 15 pilots. The October 10 live check used one pilot.
    - A paid grid that fails part-way can't be rerun in full inside that ceiling.
    - Mock-provider runs don't count toward the 90-cell grid or the Gate 2 cost forecast.
11. **Risk — turnaround:** decision 0021 found the binding constraint is turnaround, not the size of the work: approved work waited days to merge, and review replies took days. It sets no hours assumption; the `TASKS.md` estimates predate AI-assisted work and remain relative sizes. A missed date on the critical path triggers the slip rule, never another move.

## Next seven days

- Monday, October 26: the W7 slices start, and the Monday post names each one's `BLOCKED` producers. Every owner re-accepts their re-dated rows by replying to it.
- #34 merges once current `main` is merged in and the project lead re-approves. The project lead's corpus-record schemas, `dev-001`'s re-render, and tool-result delivery land the same day, and `W7-T2`'s intake starts.
- After delivery: the full 90-cell mock grid, then the paid-run condition's date, then the paid development grid with its forced stop/resume proof.
- Thursday, October 29: W7 pull requests are due. Friday, October 30: the review cutoff, and the last merge the Gate 2 step uses.
- Saturday, October 31: the Gate 2 step.
- Sunday, November 1: the tier, budget, model, and decoding decision, and the season budget.

## Weekly update rule

Update this file from repository evidence every Sunday during build and internal-release weeks. Report the current gate/tier, evidence links, public risks and asks, and next-seven-day outcomes. Summarize slice state by linking `TASKS.md`; never create a conflicting copy. Before the applicable lock, do not publish evaluation outcomes. At the December 6 release freeze ([decision 0021](docs/decisions/0021-two-week-shift.md)), record the immutable release tag/commit and manifest identifier. Week-15/16 entries may append confirmed logistics, factual submission status, and presentation-only observations without modifying the frozen release. `tests/test_status_consistency.py` checks each rollup against `TASKS.md`, `SPEC.md`, and the repository on every pull request; its docstring lists the rows a rollup keeps.
