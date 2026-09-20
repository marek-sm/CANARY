# CANARY Status — Club Week 4 — September 14, 2026

> This is a dated public summary, not a second task tracker or protocol. `TASKS.md` owns slice owners and states; `protocol/active.json` will own the exact frozen tier and run instance; `SPEC.md` owns scientific and release meaning. If this summary disagrees with one of those authorities, the authority wins and this file must be corrected.

## Current scope and gate

| Field | Current public state |
|---|---|
| Lifecycle state | Pre-implementation documentation and kickoff preparation |
| Documentation baseline | `v1.0.0` committed in `149a706`; S00 `DONE` in `TASKS.md` |
| Active-contributor count | 6 — five portfolio owners plus the project lead; `F20` is the resulting Section 12 ceiling, subject to funding and gates |
| Active/provisional tier | Not yet selected; Section 12 headcount, funding, and readiness ceilings apply. A provisional build geometry is due at the end of Week 5 and carries no claim |
| Current protocol or run ID | Not created; required by Gate 3 |
| Next gate | Gate 1 — vertical slice and measurement-contract lock — September 27 |
| Last green commit/container | `65288d3`: CI run [35318133761](https://github.com/marek-sm/CANARY/actions/runs/35318133761), Python 3.11, `make test` and `make trace`, September 18; no container built yet |
| Demo slot | Unconfirmed; no live duration or rehearsal target has been inferred |
| Judging rubric | No receipt source or date is recorded yet |

## Evidence snapshot

| Evidence | Current public state |
|---|---|
| Development/model trials | None represented as completed |
| Official empirical trials | None represented as started |
| `ENGINEERING` validation | Not activated |
| Spend and funded cap | No approved value recorded yet |
| Open protocol deviation | None; the protocol is not frozen |
| Public result or defense-effect claim | None |

## Owner outcomes

The accepted owner and exact slice state live in [`TASKS.md`](TASKS.md). Replace each dash there only after explicit acceptance; do not record private selection or performance discussion here.

| Portfolio | This week's public outcome |
|---|---|
| T1 — Chace | Accept `W5-T1` through `W13-T1` and identify first Gate-1 evidence |
| T2 — Johan | Accept `W5-T2` through `W13-T2`, complete core reading, and identify source-review evidence |
| T3 — Samson | Accept `W5-T3` through `W13-T3` and identify schema/replay evidence |
| T4 — Dhruv | Accept `W5-T4` through `W13-T4` and identify policy/defense test evidence |
| T5 — Miles | Accept `W5-T5` through `W13-T5` and identify demo/accessibility evidence |
| Project lead — Marek | Complete kickoff, assignment, paper-workflow, external-dependency, and Gate-1 readiness decisions; own the `uv.lock`, no-credit CI, and Make-target scaffold |

## Public decisions, risks, and external asks

1. **Project presentation:** use `CANARY` in all caps and make no uniqueness or novelty claim.
2. **Funding/model:** the approved budget and eligible model path must be recorded before Gate 3; no paid or credentialed CI is permitted.
3. **Event inputs:** record the judging-rubric source/date and the confirmed demo slot, Q&A, network, display, and speaker constraints when supplied.
4. **Licensing:** do not accept external contributions or imply reuse rights until code/content licensing is selected.

## Next seven days

- Commit the complete S00 documentation baseline, including this file and decision record 0003.
- Complete kickoff and the core reading in `TASKS.md`.
- Record exactly one accepted owner for every slice that enters `IN PROGRESS`.
- Queue the five `W5-T*` slices as issues with a reviewer, evidence path, and due date.
- Confirm that all five Week-5 slices start Monday, September 21 against the committed pre-kickoff scaffold and are due Thursday, September 24, giving every track the full 72-hour window; no slice waits on another track's current week.
- If the judging rubric arrives, map it to existing demo/release artifacts within 24 hours without changing scientific definitions.
- If event timing arrives, record all five timing fields required by `docs/DEMO_DESIGN.md`; otherwise keep the live duration unconfirmed.

## Weekly update rule

Update this file from repository evidence every Sunday during build and internal-release weeks. Report the current gate/tier, evidence links, public risks and asks, and next-seven-day outcomes. Summarize slice state by linking `TASKS.md`; never create a conflicting copy. Before the applicable lock, do not publish evaluation outcomes. At the November 22 release freeze, record the immutable release tag/commit and manifest identifier. Week-15/16 entries may append confirmed logistics, factual submission status, and presentation-only observations without modifying the frozen release.
