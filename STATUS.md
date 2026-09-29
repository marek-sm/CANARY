# CANARY Status — Club Week 5 — September 27, 2026

> This is a dated public summary, not a second task tracker or protocol. `TASKS.md` owns slice owners and states; `protocol/active.json` will own the exact frozen tier and run instance; `SPEC.md` owns scientific and release meaning. If this summary disagrees with one of those authorities, the authority wins and this file must be corrected.

## Current scope and gate

| Field | Current public state |
|---|---|
| Lifecycle state | Team implementation. Week 5 is closed; Week 6 (September 28 – October 4) builds the development instrument |
| Documentation baseline | `v1.0.0` committed in `149a706`; `SPEC.md` is now v1.3.0 through decisions [0004](docs/decisions/0004-week5-measurement-contract-clarifications.md), [0006](docs/decisions/0006-one-vector-reviewer.md), and [0007](docs/decisions/0007-gate1-corpus-rules-freeze.md) |
| Active-contributor count | 6 — five portfolio owners plus the project lead; `F20` is the Section 12 headcount ceiling, and the Gate 1 response below caps it at `R15` |
| Gate 1 result | **Not passed** on September 27. Four of five Week 5 slices merged: `W5-T1` ([#19](https://github.com/marek-sm/CANARY/pull/19)), `W5-T2` ([#12](https://github.com/marek-sm/CANARY/pull/12)), `W5-T4` ([#9](https://github.com/marek-sm/CANARY/pull/9)), and `W5-T5` ([#7](https://github.com/marek-sm/CANARY/pull/7)). `W5-T3` ([#20](https://github.com/marek-sm/CANARY/pull/20)) is open. Three Gate 1 items are unmet on `main`: all six D0_BASELINE cells through replay, the result schema's `split` field, and a versioned measurement contract. The `SPEC.md` Section 11 response applies: Week 6 is integration recovery, the empirical ceiling is `R15` or smaller, and nonessential corpus and presentation growth stops |
| Measurement-contract lock | Partly done. The corpus rules are frozen and the development-base task assignment is committed ([decision 0007](docs/decisions/0007-gate1-corpus-rules-freeze.md)). Re-pinning the Week 5 slices to the frozen `W5-T3` schemas and `W5-T4` interfaces, and versioning the contract, follow the `W5-T3` merge |
| Active/provisional tier | Provisional build geometry: `R15` — 15 evaluation bases, 8 tasks, and four C1 controls. It carries no claim; Gate 3 confirms or lowers it under Section 12. The evaluation-candidate target is 15 plus a selection margin, set before Week 7 |
| Current protocol or run ID | Not created; required by Gate 3 |
| Next gate | Gate 2 — development instrument — October 11 |
| Last green commit/container | `eb2a0a0`: CI run [36351252703](https://github.com/marek-sm/CANARY/actions/runs/36351252703), `test` and `docker` jobs, September 27; image `sha256:f47909971b27b364a78074579119d6b3b650d0a7c895be0b98090b381ecea52d` |
| Review | Exactly one reviewer per slice. Standing pairs by portfolio: T4 reviews T1, T3 reviews T2 (including the `SPEC.md` Section 5 source review), T5 reviews T3, T1 reviews T4, and T2 reviews T5 |
| Demo slot | Unconfirmed; no live duration or rehearsal target has been inferred |
| Judging rubric | Received September 26, 2026 from CSAI research leadership as the "Research Expectations" document; the project lead is recused from setting its criteria. Mapped the same day in [`TASKS.md`](TASKS.md#judging-rubric-map), changing presentation emphasis only |

## Evidence snapshot

| Evidence | Current public state |
|---|---|
| Development/model trials | None. Development runs use the no-credit mock provider only |
| Official empirical trials | None represented as started |
| `ENGINEERING` validation | Not activated |
| Corpus | One development base, `dev-001`, merged with attack and clean twins through C2/C3/C4; its source-review field still reads `PENDING_REVIEW`. No evaluation candidate has been opened |
| Spend and funded cap | As of September 27, 2026: project-lead funded, with a $10 prepaid OpenAI development cap and auto-recharge off; the development model candidate is `gpt-6-luna` ([decision 0005](docs/decisions/0005-development-model-and-spend-cap.md)). No paid call has been made; development stays on the mock provider until the provider adapter merges, and CI stays mock-only. The season cap is set at Gate 2 from measured development cost |
| Open protocol deviation | None; the protocol is not frozen |
| Public result or defense-effect claim | None |

## Owner outcomes

The accepted owner and exact slice state live in [`TASKS.md`](TASKS.md). Week 6 pull requests are due Thursday, October 1, and reviews by Friday, October 2.

| Portfolio | Week 5 outcome | Week 6 outcome |
|---|---|---|
| T1 — Chace | `W5-T1` merged: a hardened `read_file` task runs end to end on the mock provider | `W6-T1`: the remaining three safe tools, all ten task templates, and golden vectors for every tool |
| T2 — Johan | `W5-T2` merged: `dev-001` rendered through C2/C3/C4 as exact twins | `W6-T2`: all five development bases rendered; evaluation intake opens; C1-control and demo-case source records |
| T3 — Samson | `W5-T3` open: six cells run end to end on its branch; Gate 1 items outstanding | Merge `W5-T3`, then `W6-T3`: data-driven schedules, resume, and the independent authorization audit; source review of T2's pull requests |
| T4 — Dhruv | `W5-T4` merged: authorization, D1_POLICY_GATE, D2_DATAMARKING, and event contracts, with reviewed vectors | `W6-T4`: D1_POLICY_GATE and D2_DATAMARKING implementations tested over the Week 5 vectors |
| T5 — Miles | `W5-T5` merged: accessible replay shell and empty report shells; three review findings are due before the Week 8 shell freeze | `W6-T5`: replay kept green on real `W5-T3` records, and known-trace tests |
| Project lead — Marek | Dependency rules, reviewer pairs, corpus-rules freeze, and development-base task assignment committed | Finish the lock after `W5-T3` merges; merge the provider adapter by October 2; paid-run access and the demo operator by October 4; pair on `W6-T3` |

## Public decisions, risks, and external asks

1. **Project presentation:** use `CANARY` in all caps and make no uniqueness or novelty claim.
2. **Funding/model:** development is project-lead funded under a $10 prepaid cap, with `gpt-6-luna` as the development candidate ([decision 0005](docs/decisions/0005-development-model-and-spend-cap.md)). The official model, its fallback decision, and the season budget are still recorded before Gate 3 from development evidence; no paid or credentialed CI is permitted.
3. **Event inputs:** record the judging-rubric source/date and the confirmed demo slot, Q&A, network, display, and speaker constraints when supplied.
4. **Licensing:** do not accept external contributions or imply reuse rights until code/content licensing is selected.
5. **Week 5 process:** the 72-hour slice clock was not enforced in Week 5, and pull-request open times are recorded as facts only. `W5-T1`, `W5-T2`, and `W5-T5` waited on `W5-T3` in the same week. The re-pin to frozen contracts moved into the project lead's lock commit, and `tests/test_tasks_dependencies.py` now enforces that a slice uses only work merged before its Monday.
6. **Risk — Week 6 load:** the five Week 6 slices total 34.75 member hours against about 15 hours of capacity, and none of it shrinks with the tier. Each slice's Defer-first row is the planned relief; Gate 2 is at risk if the development instrument slips.
7. **Risk — blocked starts:** `W6-T3` and `W6-T5` need `W5-T3` merged and start `BLOCKED` until it is.
8. **Risk — delivery path:** the six-cell runner currently places untrusted content in the user message rather than returning it as a tool result, so it exercises direct rather than indirect injection. `W6-T3` moves delivery to tool results before the Week 7 development grid.
9. **Risk — `dev-001` record:** its `reviewed_by` field is still `PENDING_REVIEW`, and its recorded `template_sha256` is not the hash of the committed template file. The owner corrects both.

## Next seven days

- Merge `W5-T3` with its Gate 1 items; the project lead then re-pins the Week 5 slices and versions the measurement contract.
- Open the five Week 6 issues Monday with one owner, one reviewer, an evidence path, and a due date each.
- Every Week 6 pull request is open with acceptance evidence by Thursday, October 1, and reviewed by Friday, October 2.
- Merge the OpenAI provider adapter by Friday, October 2.
- Grant paid-run access under the cap and name the demo operator by Sunday, October 4.
- The Sunday, October 4 check-in shows Week 6 artifacts, and the next dated rollup follows.

## Weekly update rule

Update this file from repository evidence every Sunday during build and internal-release weeks. Report the current gate/tier, evidence links, public risks and asks, and next-seven-day outcomes. Summarize slice state by linking `TASKS.md`; never create a conflicting copy. Before the applicable lock, do not publish evaluation outcomes. At the November 22 release freeze, record the immutable release tag/commit and manifest identifier. Week-15/16 entries may append confirmed logistics, factual submission status, and presentation-only observations without modifying the frozen release.
