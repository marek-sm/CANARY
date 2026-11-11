# CANARY Status — Club Week 11 — November 8, 2026

> This is a dated public summary, not a second task tracker or protocol. `TASKS.md` owns slice owners and states; `protocol/active.json` will own the exact frozen tier and run instance; `SPEC.md` owns scientific and release meaning. If this summary disagrees with one of those authorities, the authority wins and this file must be corrected.

**This week's dates.**

- [Decision 0029](docs/decisions/0029-gate-chain-shift.md), merged November 6, moved the Gate 2 step's close to the end of Tuesday, November 10, the tier input to Wednesday, November 11, and Gate 3 to Saturday, November 14. It is the Gate 2 step's fourth move, and it allows no fifth.
- [Decision 0030](docs/decisions/0030-done-by-november-30.md), approved November 7, finishes CANARY by Monday, November 30:
  - Thanksgiving week, November 23–29, is an unnumbered break and now working time.
  - W12, Gate 5 (November 26), W13, and the release freeze (noon on November 29) move into that week.
  - Club week 14 is November 30–December 6, so the Demo Day window is November 30–December 11.
  - Nothing before the November 22 data cutoff moves.
- No result exists, and none is promised.

## Current scope and gate

| Field | Current public state |
|---|---|
| Lifecycle state | Team implementation. Club week 11 (November 2–8) was the W8 week, but W8 can freeze only after the Gate 2 step and the tier input. `W7-T3` ([#62](https://github.com/marek-sm/CANARY/pull/62)) and `W7-T1` ([#63](https://github.com/marek-sm/CANARY/pull/63)) merged November 3. Their paid steps run Monday, November 9. [#54](https://github.com/marek-sm/CANARY/pull/54) (`W7-T4`) merged November 9 as `f1907ef`, after the project lead's November 8 fallback push and November 9 readiness fixes. Two W7 pull requests are open: [#73](https://github.com/marek-sm/CANARY/pull/73) (`W7-T2`; the project lead's source review posted November 8, and it waits on the owner's fix push and a code owner's approval) and [#66](https://github.com/marek-sm/CANARY/pull/66) (`W7-T5`, its `main` merge due November 8). Open W8 work: [#74](https://github.com/marek-sm/CANARY/pull/74) (`W8-T1` CI proof notes) and [#77](https://github.com/marek-sm/CANARY/pull/77) (`W8-T3` generator and dormant plan) |
| Documentation baseline | `v1.0.0` committed in `149a706`; `SPEC.md` is v1.22.0 from [decision 0031](docs/decisions/0031-merge-on-green.md) (v1.21.0 at this rollup). Decisions merged this week: [0025](docs/decisions/0025-full-study.md) (#68, the `F20` target), [0026](docs/decisions/0026-malformed-calls-and-price-bound.md) (#69, malformed calls and the price bound), [0027](docs/decisions/0027-acceptance-by-work.md) (#72, acceptance by work), [0023](docs/decisions/0023-tool-sandbox.md) (#64, the tool sandbox and the paid-run record), [0028](docs/decisions/0028-restore-strength.md) (#75), [0029](docs/decisions/0029-gate-chain-shift.md) (#81), and [0030](docs/decisions/0030-done-by-november-30.md) (#84) |
| Active-contributor count | 6 — five portfolio owners plus the project lead; `F20` is the Section 12 headcount ceiling. Under [decision 0027](docs/decisions/0027-acceptance-by-work.md), read at the Wednesday, November 11 tier input, four owners have authored work on their rows since November 3. One owner has no counted reply or work yet. If that holds on November 11, the count is 5 and the ceiling is `R15`, final for this run (decision 0029 item 3) |
| Gate 1 result | **Not passed** on September 27. The October 10 recovery check met every [`TASKS.md` Gate 1 item](TASKS.md#gate-1--end-of-week-5) after the deadline, so the result stands. Decision 0025 amends the `SPEC.md` Section 11 Gate 1 response for this run, after it fired, and that check isn't new evidence for doing so |
| Gate 2 result | **Not passed** on October 11, with the `SPEC.md` Section 11 Gate 2 response. Decision 0025 reopened the Gate 2 step, and decision 0029 moved its close to the end of Tuesday, November 10, with no fifth move. If it hasn't run by then, no `ALL` or `ONE` row is selectable, and `M10-BASE` remains only if the D0_BASELINE summary and readiness record merge by Thursday, November 12. The run-wide stop rule ([#82](https://github.com/marek-sm/CANARY/pull/82)) merged November 6. Its only reviews were the project lead's and an AI review, with no portfolio owner's, and the Gate 2 record states that limitation |
| Measurement-contract lock | Done. It merged October 7 as [#35](https://github.com/marek-sm/CANARY/pull/35) under decisions [0008](docs/decisions/0008-content-filter-refusals.md) and [0009](docs/decisions/0009-measurement-contract-lock.md). The corpus-record schemas that 0009 item 8 left open merged October 25 in #61 |
| Active/provisional tier | Provisional build geometry: `F20` — 20 evaluation bases, 10 tasks, C2/C3/C4, both defenses, and four C1 controls, 1,092 official trials ([decision 0025](docs/decisions/0025-full-study.md)). It carries no claim. The project lead's tier input comes Wednesday, November 11, from the prefix the reviewed pool supports, the readiness decisions, the budget equation, and capacity. The Gate 3 step makes the selection |
| Current protocol or run ID | Not created; required by Gate 3 |
| Next gate | Gate 3 — protocol freeze — Saturday, November 14, on W8 work merged through Friday, November 13 ([decision 0029](docs/decisions/0029-gate-chain-shift.md)). If it misses, the `SPEC.md` Section 11 Gate 3 response applies |
| Last green commit/container | `0e26ca5`: CI run [42322124916](https://github.com/marek-sm/CANARY/actions/runs/42322124916), November 7 |
| Review | Under [decision 0031](docs/decisions/0031-merge-on-green.md), from November 9: owners merge their own pull requests once `test` passes, with no approval required, and member reviews are optional. A member's change request blocks the merge until the owner answers it. A record or CI change still needs approval from a contributor other than its author (`.github/CODEOWNERS`), and the project lead reviews `W7-T2`'s sources under `SPEC.md` Section 5. Results and release code is reviewed on the lead side, an AI review whose every finding the project lead classifies, before every paid run, freeze, and gate step that uses it; the paper states that results code had no independent human review. Every owner answers review comments, merge conflicts, and questions on their own pull requests within 48 hours, through November 29 under decision 0030. **Ruleset, changed November 8 after #86 merged and checked through the GitHub API (corrected November 9):** `protect-main` requires 0 approvals and a code owner's review, last-push approval is off, `test` is the only required check, and no one can bypass it. #74 and #77 then showed as mergeable, and #66 and #73 as blocked. Decision 0031 item 11 expected #66 to be mergeable, which was wrong: #66 changes `corpus/demo/demo-001.json`, a record file, so it needs a code owner's approval. An open change request also still blocks a merge with 0 approvals, so under decision 0031 item 2 the project lead dismisses it after the owner's answer, as on #54 on November 9 |
| Demo slot and operator | The slot is unconfirmed; no live duration or rehearsal target has been inferred. Under [decision 0030](docs/decisions/0030-done-by-november-30.md), Demo Day falls November 30–December 11. November 30 is the earliest date, and the release freezes by noon on November 29. The project lead has asked the organizers for the date, slot, time limit, and hardware access by Monday, November 23. Demo operator (`SPEC.md` Section 13): Miles (T5), who accepted on October 11 |
| Judging rubric | Received September 26, 2026 from CSAI research leadership as the "Research Expectations" document; the project lead is recused from setting its criteria. Mapped in [`TASKS.md`](TASKS.md#judging-rubric-map), corrected October 7 in [#36](https://github.com/marek-sm/CANARY/pull/36), and re-paraphrased October 10 under [decision 0013](docs/decisions/0013-rubric-framing.md) |

## Evidence snapshot

| Evidence | Current public state |
|---|---|
| Development/model trials | Unchanged since October 10: one live adapter check (`make live-smoke` on `670dd31`), the W5-T1 ticket with no injected content, on `claude-haiku-5-5`, with 2 requests and no key recorded. It counts as 1 of the `SPEC.md` Section 9 ceiling's 15 reliability pilots. No live development-grid trial has run, and mock runs don't count toward the grid |
| Official empirical trials | None represented as started |
| `ENGINEERING` validation | Not activated. `W8-T3` ([#77](https://github.com/marek-sm/CANARY/pull/77)) builds the dormant plan `SPEC.md` Section 11 requires |
| Corpus | Five development bases, four C1 records, and one demo case are on `main` since October 25. No evaluation candidate is on `main`: 0 of the target 24. `W7-T2`'s intake closed November 5 and is in [#73](https://github.com/marek-sm/CANARY/pull/73). The project lead's Section 5 source sign-off, due November 7, slipped and was posted on #73 on November 8 (corrected November 9). `W7-T2` merges no later than November 10 (`TASKS.md`, recorded November 8) |
| Spend and funded cap | As of November 8, 2026: no paid call is recorded in the repository since the October 10 live check, which used about $0.00014. Project-lead funded, in a CANARY-only Claude Console workspace with a $10 monthly limit (decision 0028 item 7). At the decision 0028 bound, `F20`'s Section 9 budget equation needs about $90.50 of funded balance. The project lead raises the workspace limit and the spend cap by Tuesday, November 10, before the tier input, and records the new figures here first (decision 0030 item 9). The OpenAI $10 prepaid cap is unused. CI stays mock-only |
| Repository audit | The October 17 read-only audit found 83 issues, none blocking. F-01, the tool sandbox, merged as decision 0023 (#64) on November 4. A-01 and B-03 were decided by decision 0026 (#69). The stack audit's gaps closed in [#78](https://github.com/marek-sm/CANARY/pull/78), and the sandbox death-signal fixes merged in [#80](https://github.com/marek-sm/CANARY/pull/80) and [#83](https://github.com/marek-sm/CANARY/pull/83) |
| Open protocol deviation | None open; the protocol is not frozen |
| Public result or defense-effect claim | None |

## Owner outcomes

The accepted owner and exact slice state live in [`TASKS.md`](TASKS.md). Each W8 slice freezes November 11–13, after the Gate 2 step and the tier input. Every W8 slice's last merge is Friday, November 13 ([decision 0029](docs/decisions/0029-gate-chain-shift.md)). W12 and W13 owners re-accept their rows, re-dated by [decision 0030](docs/decisions/0030-done-by-november-30.md), by a reply read Sunday, November 15.

| Portfolio | W7 (as of November 8) | W8 slice |
|---|---|---|
| T1 — Chace | `W7-T1`: #63 merged November 3. Its paid smokes run on the project lead's Mac on Monday, November 9. Chace approved the project lead's task variants ([#71](https://github.com/marek-sm/CANARY/pull/71)) on November 7 | `W8-T1`: [#74](https://github.com/marek-sm/CANARY/pull/74) open; last merge by Friday, November 13 |
| T2 — Johan | `W7-T2`: [#73](https://github.com/marek-sm/CANARY/pull/73), out of draft November 6, one fix pushed November 8. The project lead's source review posted November 8 (corrected November 9); it waits on the owner's fix push, then a code owner's approval | `W8-T2`: posts `P` the day `W7-T2` merges, then merges first in the November 11–13 freezes |
| T3 — Samson | `W7-T3`: #62 merged November 3. Its paid grid runs on the project lead's Mac on Monday, November 9 | `W8-T3`: [#77](https://github.com/marek-sm/CANARY/pull/77) open; last push in the November 11–13 freezes, merged on green and reviewed on the lead side within 24 hours |
| T4 — Dhruv | `W7-T4`: [#54](https://github.com/marek-sm/CANARY/pull/54). The slice owner's last push was November 1. The project lead made decision 0029's fallback push on November 8, a visible scope change recorded in `TASKS.md`. T4 keeps the slice. Under decision 0031, T4's November 1 tests cover T1's four October 25 gaps. The lead-side review found seven more readiness defects, which the project lead fixes in a November 9 push, a visible scope change recorded in `TASKS.md`. #54 merged on green on November 9, after that push and the change-request answer | `W8-T4`: opens by the morning of Monday, November 9; its pool steps wait for `W7-T2` |
| T5 — Miles | `W7-T5`: [#66](https://github.com/marek-sm/CANARY/pull/66), its `main` merge due by the end of November 8; it changes `corpus/demo/demo-001.json`, a record file, so it merges on green once a code owner approves (decision 0031) | `W8-T5`: opens the day `W7-T5` merges |
| Project lead — Marek | Merged this week: decisions 0025, 0026, 0027, 0023, 0028, 0029, and 0030; the price bound (#70); D2 marking of every text-bearing HTML construct (#76); the stack-audit fixes (#78); the sandbox death-signal fixes (#80, #83); and the run-wide stop rule (#82). Done November 8 (corrected November 9): the task variants (#71, merged), the `W7-T2` source review (posted on #73), the `W7-T4` fallback push, and decision 0031 (#86). Open: the paid runs Monday, November 9; the summary and Gate 2 step by November 10 | Tier input November 11. Slipped from November 8, still open: the gap sentence, license choice and author order, and the official C1 records through Section 11 change control. The record superseding decision 0018's pilot example by November 10, then decision 0012's wiring and the demo-rehearsal command by November 13 |

## Public decisions, risks, and external asks

1. **Project presentation:** use `CANARY` in all caps and make no uniqueness or novelty claim. Under decisions [0016](docs/decisions/0016-practitioner-relevance.md) and [0017](docs/decisions/0017-applied-purpose.md), CANARY is applied research for teams choosing prompt-injection safeguards. It claims a gap in published work only in a sentence scoped to sources the project lead has opened, and never a market gap. That sentence, due November 8, slipped. If it isn't in `SPEC.md` before the November 14 Gate 3 freeze, no gap sentence enters.
2. **Tier and model:** under [decision 0025](docs/decisions/0025-full-study.md), the target is `F20`. `claude-haiku-5-5` is the expected model and `gpt-6-luna` the declared fallback; a missed date never activates it. Both are confirmed with the tier input on November 11. No paid or credentialed CI is permitted. No result exists, and none is promised.
3. **Event inputs:** asked of club research leadership on November 7, by Monday, November 23: the confirmed Demo Day date, slot, time limit, and hardware access. The paper leads' dates under decision 0030:
   - the manuscript draft November 16, with no result numbers;
   - a results-bearing draft November 23;
   - final claim language November 24;
   - the final draft November 25.

   At the November 7–12 midpoint check-in, CANARY supplies methods only, marked draft until the November 14 Gate 3 freeze.
4. **Licensing:** do not accept external contributions or imply reuse rights until code/content licensing is selected. That choice, due November 8, slipped, and `W11-T5`'s `LICENSE` depends on it.
5. **Process:**
   - On November 8, the team channel and each owner hear decision 0030's dates directly. Owners re-accept their W12 and W13 rows by a reply, read November 15.
   - Every owner answers review comments, merge conflicts, and questions within 48 hours. Reviewer turnaround ended with [decision 0031](docs/decisions/0031-merge-on-green.md).
6. **Risk — the Gate 2 chain, the largest:**
   - The paid grid on Monday, November 9 needs `W7-T4` (#54) and the task variants (#71) merged first (decision 0025 item 4; decision 0028).
   - Then the paid summary and the Gate 2 step come by the end of November 10. A slip anywhere in the chain ends the defense comparison, and there is no fifth move.
7. **Risk — evaluation candidates:** `F20` needs 20 bases from the reviewed pool. Section 5 step 8 builds only the prefix the reviewed pool supports (20, 15, 10, 8, or 6), and a candidate whose source can't be verified doesn't merge.
8. **Risk — budget:** the Section 9 equation is evaluated at the tier input from the paid grid's observed cost. If it fails at `F20`, the project lead raises the funded cap and records it here first rather than drop the tier (decision 0028 item 7).
9. **Risk — development trial ceiling:** `SPEC.md` Section 9 allows 120 development trials. The planned total is 107: the October 10 check, decision 0026's live check, the 90-cell grid, and the 15 coverage smokes. The ten live task-variant checks would bring it to 117, the figure decision 0026 set, so a paid grid that fails part-way can't be rerun in full. Mock-provider runs don't count.
10. **Sweep environment:** the official sweep runs on the project lead's machine under the tool sandbox, outside the CI container, and `protocol/active.json` names that host environment at Gate 3 (decision 0029 item 6). The manifest and the paper state that limit.
11. **Risk — Thanksgiving work:** decision 0030 moves W12 and W13 into November 23–29. An owner who can't work that week says so by November 15, and the row is reassigned that day, never to the project lead for `W12-T3` or `W12-T4`.

## Next seven days

- **Sunday, November 8:**
  - `W7-T4`'s fallback push.
  - The task variants (#71) merge once their CI is green.
  - `W7-T5`'s `main` merge.
  - Decision 0030's notices.
- **Monday, November 9:**
  - The project lead's `W7-T2` source review. Decision 0031's lead-side review of `W7-T4` and the code the paid run uses ([`docs/reviews/2026-11-09-paid-run.md`](docs/reviews/2026-11-09-paid-run.md)), the project lead's readiness fixes in #54, then `W7-T4`'s merge (done, `f1907ef`).
  - Raw-record storage: a private folder outside Git, shared with Dhruv, Miles, and Chace before the first paid call on November 9 (corrected November 10: the slip `TASKS.md` recorded that day didn't happen). The four raw run folders were copied in by November 10, and the copies match the paid clone.
  - Then a fresh checkout at the reviewed commit, the spend ledger and cap, the live smoke, the mock grid, the paid-run record, and the paid grid and smokes.
  - `W8-T2` and `W8-T4` open, and `W7-T5` may merge on green once a code owner approves.
- **Tuesday, November 10:**
  - `W7-T2` merges, and `W8-T2` posts `P`.
  - The workspace limit and cap are raised.
  - The paid summary merges on green after its lead-side review.
  - The record superseding decision 0018's pilot example.
  - The Gate 2 step by the end of the day.
- **Wednesday, November 11:** the tier input and the decision 0027 acceptance read. Then the W8 freezes, `W8-T2` first.
- **Friday, November 13:** every W8 slice's last merge, decision 0012's wiring, the count-only outputs, and the demo-rehearsal command.
- **Saturday, November 14:** the Gate 3 step; then the sweep runs November 14–17.
- **Sunday, November 15:** `W9-T3`'s sanitizer pull request and the W12/W13 acceptance read.

## Weekly update rule

Update this file from repository evidence every Sunday during build and internal-release weeks. Report the current gate/tier, evidence links, public risks and asks, and next-seven-day outcomes. Summarize slice state by linking `TASKS.md`; never create a conflicting copy. Before the applicable lock, do not publish evaluation outcomes. At the release freeze, by noon on November 29 ([decision 0030](docs/decisions/0030-done-by-november-30.md); December 6 under decision 0021), record the immutable release tag/commit and manifest identifier. Entries from club week 14 (November 30) on may append confirmed logistics, factual submission status, and presentation-only observations without modifying the frozen release. `tests/test_status_consistency.py` checks each rollup against `TASKS.md`, `SPEC.md`, and the repository on every pull request; its docstring lists the rows a rollup keeps.
