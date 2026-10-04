# CANARY Status — Club Week 6 — October 4, 2026

> This is a dated public summary, not a second task tracker or protocol. `TASKS.md` owns slice owners and states; `protocol/active.json` will own the exact frozen tier and run instance; `SPEC.md` owns scientific and release meaning. If this summary disagrees with one of those authorities, the authority wins and this file must be corrected.

## Current scope and gate

| Field | Current public state |
|---|---|
| Lifecycle state | Team implementation. Week 6 (September 28 – October 4) built toward the development instrument; Week 7 (October 5–11) runs the development grid for Gate 2 |
| Week 6 call | [LEAD: green, yellow, or red, decided at the October 4 checkpoint] |
| Documentation baseline | `v1.0.0` committed in `149a706`; `SPEC.md` is now v1.3.0 through decisions [0004](docs/decisions/0004-week5-measurement-contract-clarifications.md), [0006](docs/decisions/0006-one-vector-reviewer.md), and [0007](docs/decisions/0007-gate1-corpus-rules-freeze.md) |
| Active-contributor count | 6 — five portfolio owners plus the project lead; `F20` is the Section 12 headcount ceiling, and the Gate 1 response below caps it at `R15` |
| Gate 1 result | **Not passed** on September 27. `W5-T3` merged as [#24](https://github.com/marek-sm/CANARY/pull/24) on September 30. A fresh-clone check of `6263576` that day (CI run [36786772073](https://github.com/marek-sm/CANARY/actions/runs/36786772073)) met every `TASKS.md` Gate 1 item except the lead's versioned measurement contract; no manifest exists yet. The `SPEC.md` Section 11 Gate 1 response still applies: integration recovery, an empirical ceiling of `R15` or smaller, and no nonessential corpus or presentation growth |
| Measurement-contract lock | Partly done. The corpus rules are frozen and the development-base task assignment is committed ([decision 0007](docs/decisions/0007-gate1-corpus-rules-freeze.md)). Re-pinning the Week 5 slices and versioning the contract are still open; the event, result, and policy schemas read `0.1.0`. The lock also classifies the provider's content-policy rejection, because Section 11 freezes the error taxonomy at this lock, so the project lead plans to land it before the first Week 7 paid call |
| Active/provisional tier | Provisional build geometry: `R15` — 15 evaluation bases, 8 tasks, and four C1 controls. It carries no claim; Gate 3 confirms or lowers it under Section 12. The selection margin, set October 4, is 4, two per primary goal: `W7-T2`'s pool needs at least 10 `secret_disclosure` and 9 `unauthorized_action` candidates with ledger status `evaluation` and a completed source review, counted in its pull request as merged |
| Current protocol or run ID | Not created; required by Gate 3 |
| Next gate | Gate 2 — development instrument — October 11; likely not passed (risk 6) |
| Last green commit/container | `636c1fe`: CI run [36801713621](https://github.com/marek-sm/CANARY/actions/runs/36801713621), `test` and `docker` jobs, September 30; image [LEAD: digest from that run's `docker` job log] |
| Review | Exactly one reviewer per slice. Standing pairs by portfolio: T4 reviews T1, T3 reviews T2 (including the `SPEC.md` Section 5 source review), T5 reviews T3, T1 reviews T4, and T2 reviews T5 |
| Demo slot and operator | The slot is unconfirmed; no live duration or rehearsal target has been inferred. Demo operator (`SPEC.md` Section 13): [LEAD: name and acceptance date, or "not yet named"] |
| Judging rubric | Received September 26, 2026 from CSAI research leadership as the "Research Expectations" document; the project lead is recused from setting its criteria. Mapped the same day in [`TASKS.md`](TASKS.md#judging-rubric-map), changing presentation emphasis only |

## Evidence snapshot

| Evidence | Current public state |
|---|---|
| Development/model trials | None [LEAD: or the first paid run's date and logical trials, counted against the 15 pilots in `SPEC.md` Section 9]. Development runs otherwise use the no-credit mock provider |
| Official empirical trials | None represented as started |
| `ENGINEERING` validation | Not activated |
| Corpus | One development base, `dev-001`, merged with attack and clean twins through C2/C3/C4; its `reviewed_by` field still reads `PENDING_REVIEW`. The other four development bases (`W6-T2`) had no pull request at the October 2 review cutoff. No evaluation candidate has been opened |
| Spend and funded cap | As of October 4, 2026: project-lead funded, with a $10 prepaid OpenAI development cap and auto-recharge off; the development model candidate is `gpt-6-luna` ([decision 0005](docs/decisions/0005-development-model-and-spend-cap.md)). The provider adapter merged as [#26](https://github.com/marek-sm/CANARY/pull/26) (`636c1fe`) on September 30. [LEAD: "No paid call has been made", or the first paid run's date and spend]. CI stays mock-only. The season cap is set at Gate 2 from measured development cost |
| Open protocol deviation | None; the protocol is not frozen |
| Public result or defense-effect claim | None |

## Owner outcomes

The accepted owner and exact slice state live in [`TASKS.md`](TASKS.md). Week 6 pull requests were due Thursday, October 1, and reviews by Friday, October 2. Week 7 pull requests are due Thursday, October 8, and reviews by Friday, October 9. [LEAD: keep the first names below only with recorded consent; otherwise use `j0hanj`, `samsonchang2028`, and `milesshoe` here and in `TASKS.md`]

| Portfolio | Week 6 outcome at the October 2 review cutoff | Week 7 outcome |
|---|---|---|
| T1 — Chace | `W6-T1`: no pull request | `W7-T1`: the 15 clean coverage smokes and the C1 controls, after `W6-T1`, `W6-T2`, and `W6-T3` |
| T2 — Johan | `W6-T2`: no pull request | `W7-T2`: evaluation intake to 15 plus the selection margin, and the committed selection script, after `W6-T2` |
| T3 — Samson | `W5-T3` merged as [#24](https://github.com/marek-sm/CANARY/pull/24) on September 30, which unblocked `W6-T3`; `W6-T3`: no pull request | `W7-T3`: the 90-cell development grid, forced resume, and the Gate 2 budget equation, after `W6-T1` to `W6-T4` |
| T4 — Dhruv | `W6-T4`: D1_POLICY_GATE and D2_DATAMARKING opened as [#25](https://github.com/marek-sm/CANARY/pull/25) on September 30 with CI green; not reviewed by the cutoff | `W7-T4`: gate-versus-audit differential tests and the readiness-check script, after `W6-T1`, `W6-T3`, and `W6-T4` |
| T5 — Miles | `W6-T5`: started `BLOCKED` until `W5-T3` merged on September 30; known-trace replay opened as [#28](https://github.com/marek-sm/CANARY/pull/28) on October 3, after the cutoff, with CI green | `W7-T5`: two replay runs with the demo operator and the staged demo case, after `W6-T5`, `W6-T2`, and `W6-T3` |
| Project lead — Marek | Provider adapter merged ([#26](https://github.com/marek-sm/CANARY/pull/26), September 30); Gate 1 cross-check on a fresh clone (September 30); no Week 6 issues opened by the lead; [LEAD: the `W6-T3` pairing session's date, or that it did not happen; the `STATUS.md` consistency check's pull request, if merged] | The lock commit before the first paid call; paid-run access; the selection-prefix decision record before `W7-T2`'s script; pairing on `W7-T3`; the Gate 2 step on October 10 |

## Public decisions, risks, and external asks

1. **Project presentation:** use `CANARY` in all caps and make no uniqueness or novelty claim.
2. **Funding/model:** development is project-lead funded under a $10 prepaid cap, with `gpt-6-luna` as the development candidate ([decision 0005](docs/decisions/0005-development-model-and-spend-cap.md)). The official model, its fallback decision, and the season budget are still recorded before Gate 3 from development evidence; no paid or credentialed CI is permitted.
3. **Event inputs:** record the judging-rubric source/date and the confirmed demo slot, Q&A, network, display, and speaker constraints when supplied.
4. **Licensing:** do not accept external contributions or imply reuse rights until code/content licensing is selected.
5. **Process:**
   - The 72-hour slice clock was not enforced in Week 5, and pull-request open times are recorded as facts only.
   - `W5-T1`, `W5-T2`, and `W5-T5` waited on `W5-T3` in the same week. `Depends` cells now name only work merged before a slice's Monday, and `tests/test_tasks_dependencies.py` enforces that.
   - Since October 4, a slice that is `BLOCKED` on Monday starts the day its last input lands, with its dates unchanged ([`TASKS.md`](TASKS.md#dependency-discipline)).
   - The project lead opened no Week 6 issues. That departed from the `TASKS.md` Monday cadence and the September 27 next-seven-days list. `W6-T5`'s owner opened [#27](https://github.com/marek-sm/CANARY/issues/27) on October 3, and weekly issues start in Week 7.
6. **Risk — Gate 2 (decided October 4):**
   - At the October 2 review cutoff, the provider adapter was the only Week 6 input merged. `W6-T4` was open in [#25](https://github.com/marek-sm/CANARY/pull/25) without a review, and `W6-T1`, `W6-T2`, `W6-T3`, and `W6-T5` had no pull request. `W6-T5` opened [#28](https://github.com/marek-sm/CANARY/pull/28) on October 3.
   - Every Gate 2 item depends on that work, and Gate 2 work does not shrink with the tier.
   - The project lead's response is the [`TASKS.md`](TASKS.md#w7--gate-2-development-matrix-and-defense-readiness-october-511) W7 start decision:
     - no reassignment, and no cut beyond each slice's Defer-first row;
     - unmerged Week 6 work is finished first;
     - Week 7 pull requests stay due October 8;
     - Gate 2 is likely to be recorded not passed on October 11, with the `SPEC.md` Section 11 Gate 2 response.
7. **Risk — Week 8:** Gate 3 (October 18) has the same shape: every Week 8 freeze depends on Week 7 work.
8. **Risk — delivery path:** the six-cell runner currently places untrusted content in the user message rather than returning it as a tool result, so it exercises direct rather than indirect injection. `W6-T3` moves delivery to tool results before the Week 7 development grid.
9. **Risk — `dev-001` record:** its `reviewed_by` field is still `PENDING_REVIEW`; the owner corrects it. The `template_sha256` mismatch was fixed in [#24](https://github.com/marek-sm/CANARY/pull/24).
10. **Risk — development trial ceiling:** `SPEC.md` Section 9 allows 120 development trials: the 90-cell grid, 15 coverage smokes, and 15 pilots. A paid grid that fails part-way can't be rerun in full inside that ceiling. Mock-provider runs don't count toward the 90-cell grid or the Gate 2 cost forecast.
11. **Risk — `W7-T2` size:** its 10-hour estimate exceeds one contributor-week. The provisional geometry stays `R15`, and a candidate pool that closes short reaches a lower tier only through `SPEC.md` Section 5 step 7 and the Gate 3 record. With fewer than 20 eligible bases, the Section 5 step 8 selection needs a protocol decision record first.

## Next seven days

- Owners finish and merge their unmerged Week 6 work; `W6-T4` ([#25](https://github.com/marek-sm/CANARY/pull/25)) and `W6-T5` ([#28](https://github.com/marek-sm/CANARY/pull/28)) are reviewed by their standing reviewers.
- The project lead's lock commit lands before the first Week 7 paid call.
- Monday, October 5: open the five Week 7 issues. Each gets one owner, its standing reviewer, an evidence path, the October 8 due date, and any `BLOCKED` producer. Post the list.
- Record paid-run access and the named demo operator.
- Commit a protocol decision record for the Section 5 step 8 selection when fewer than 20 eligible bases exist, before `W7-T2`'s selection script.
- Every Week 7 pull request is open with acceptance evidence by Thursday, October 8, and reviewed by Friday, October 9.
- Saturday, October 10: the Gate 2 step runs `W7-T4`'s readiness checks on `W7-T3`'s grid records.
- Sunday, October 11: the rollup records the Gate 2 result, the season budget, and the tier and model decisions.

## Weekly update rule

Update this file from repository evidence every Sunday during build and internal-release weeks. Report the current gate/tier, evidence links, public risks and asks, and next-seven-day outcomes. Summarize slice state by linking `TASKS.md`; never create a conflicting copy. Before the applicable lock, do not publish evaluation outcomes. At the November 22 release freeze, record the immutable release tag/commit and manifest identifier. Week-15/16 entries may append confirmed logistics, factual submission status, and presentation-only observations without modifying the frozen release. `tests/test_status_consistency.py` checks each rollup against `TASKS.md`, `SPEC.md`, and the repository on every pull request; its docstring lists the rows a rollup keeps. [LEAD: keep this sentence only if that check merged before this rollup]
