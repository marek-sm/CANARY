# CANARY Build Slices

This is the mutable implementation plan. It records work status and dependencies; it cannot change the scientific contract in `SPEC.md`.

## Status values

- `PLANNED`: defined but not started.
- `IN PROGRESS`: active work has an accountable assignee and branch or issue.
- `BLOCKED`: cannot proceed; the blocker and decision owner are recorded.
- `DONE`: acceptance evidence is linked and independently reviewable.
- `CUT`: removed by the active tier or cut order; not silently deferred.

Do not mark a slice `DONE` because code exists. Mark it `DONE` only when every acceptance check passes against a named commit.

## Ownership commitment

- Before a retained slice enters `IN PROGRESS`, record exactly one accountable owner in the slice plan.
- A contributor accepts a slice only after reviewing its scope, dependencies, deadline, and acceptance evidence. Acceptance is a commitment to complete every check, not merely to attempt the work.
- Reviewers, pairing partners, and project leads may advise or verify, but they are not deputies and do not silently inherit delivery ownership.
- Raise a risk or blocker as soon as it is known. The owner remains accountable for driving it to an explicit decision and keeping this file accurate.
- If actual capacity changes, mark the slice `BLOCKED` and make a visible reassignment, tier, cut, or schedule decision before work proceeds. Never leave ownership ambiguous or assume that another contributor has taken it over.

Use a stable contributor identifier until a person consents to public attribution. Replace `—` in the owner column only after that contributor explicitly accepts the full slice.

## Component portfolios

Portfolios make the five contributor-sized areas legible; they do not create shared ownership. Every active slice in the plan below still has exactly one accountable owner.

| Portfolio | Core outputs | Required paper handoff |
|---|---|---|
| T1 — Agent and task oracles | Agent loop, intrinsically safe tools, fixtures/reset, ten deterministic utility validators, authorization-policy golden vectors | Technical notes and evidence for the agent, tools, fixtures, tasks, and utility oracles |
| T2 — Corpus and adapters | Candidate/source ledger, source review, crossed C2/C3/C4 rendering, citations, adaptation/rejection records, corpus validator | Technical notes and evidence for corpus method, adaptations/rejections, citations, and related work |
| T3 — Runner and evidence | Schemas, schedule, execute/resume/retry, independent policy audit, scoring, aggregation, intervals, integration, and schema-driven replay | Technical notes and evidence for runner, data contracts, analysis, and reproducibility |
| T4 — Defenses and policy | `D1_POLICY_GATE`, `D2_DATAMARKING`, declarative policy schema, security tests, and event-semantics review | Technical notes and evidence for the threat model, defenses, event semantics, and security tests |
| T5 — Demo and release | Terminal shell, replay presentation, video, paper assets, accessibility, sanitization coordination, and release checklist | Figures, captions, formatting/accessibility notes, and release documentation |

The designated club paper leads own manuscript drafting, editing, and submission. The project lead writes the protocol, metric definitions, and results and must approve every result, numerical claim, and limitation before submission. Each portfolio owner supplies concise technical notes, linked evidence, captions/alt text where applicable, and at least one component limitation; polished manuscript prose is not required. T3 owns replay-data correctness, while T5 supplies figures, accessibility, formatting, and release-package support. These workflow roles do not determine authorship: every named author must make a substantive contribution, review the final draft, and consent to being named.

## Slice plan

The target week is the planned acceptance week, not necessarily the week work begins. Portfolio identifies the primary accountable area; dependencies still require cross-portfolio review without creating shared ownership.

| ID | Slice | Portfolio | Target week | Accountable owner | Depends on | Gate | Initial status |
|---|---|---|---|---|---|---|---|
| S00 | Repository policy and documentation baseline | T5 | W4 | Marek | — | Before coding | `DONE` (`149a706`, `65288d3`) |
| S01 | Python package, dependency lock, no-credit CI, and Make targets | T3 | W5 | — | S00 | Gate 1 | `PLANNED` |
| S02 | Initial schemas, identifiers, canonical JSON, and hash utilities | T3 | W5 | — | S00–S01 | Gate 1 | `PLANNED` |
| S03 | Safe-tool framework, minimal fictional fixture, and boundary tests | T1 | W5 | — | S01–S02 | Gate 1 | `PLANNED` |
| S04 | Hand-written agent loop, mock provider, and provider boundary | T1 | W5 | — | S01–S03 | Gate 1 | `PLANNED` |
| S05 | Initial task registry, authorization policies, grants, and utility oracles | T1 | W5 | — | S02–S04 | Gate 1 | `PLANNED` |
| S06 | Append-only event pipeline, scoring, resume, and schema-driven replay | T3 | W5 | — | S02–S05 | Gate 1 | `PLANNED` |
| S07 | C2/C3/C4 renderers, exact clean twins, and round-trip/diff tests | T2 | W5 | — | S03, S05–S06 | Gate 1 | `PLANNED` |
| S08 | D1_POLICY_GATE policy gate and independently implemented audit evaluator | T4 | W7 | — | S05–S07 | Gate 2 | `PLANNED` |
| S09 | D2_DATAMARKING source-faithful datamarking transform and coverage tests | T4 | W7 | — | S04, S07 | Gate 2 | `PLANNED` |
| S10 | Development cases, source ledger, and corpus-candidate workflow | T2 | W7 | — | S05, S07 | Gate 2 | `PLANNED` |
| S11 | Full development matrix, interruption recovery, context, and budget evidence | T3 | W7 | — | S06, S08–S10 | Gate 2 | `PLANNED` |
| S12 | Deterministic corpus selection, active tier, model, and full protocol freeze | T3 | W8 | — | S11 | Gate 3 | `PLANNED` |
| S13 | Randomized official sweep or frozen `ENGINEERING` validation | T3 | W10 | — | S12 | Gate 4 | `PLANNED` |
| S14 | Generated analysis/report, terminal demo, replay, video, and accessibility | T5 | W12 | Miles | S06 for shell/replay; S13 for final evidence | Gates 4–5 | `IN PROGRESS` ([#6](https://github.com/marek-sm/CANARY/issues/6)) |
| S15 | Sanitized release, citations/licenses, contribution records, manifest, and tag | T5 | W13 | Miles | S14 | Release | `PLANNED` |

## Club-week milestones

The scientific gate definitions and mandatory responses remain canonical in `SPEC.md` Section 11. This table owns the operating cadence between those gates.

| Club week | Dates | Team outcome |
|---:|---|---|
| 4 | Sep 14–20 | Kickoff and bootcamp; accept portfolios/slices; complete core reading; confirm rubric and demo-logistics status; queue Gate-1 issues |
| 5 | Sep 21–27 | Begin team implementation; complete the vertical slice and measurement-contract lock; create paper outline and empty generated-result shells; pass Gate 1 |
| 6 | Sep 28–Oct 4 | Build safe tools, deterministic tasks, development bases, defense prototypes, and resumable runner components |
| 7 | Oct 5–11 | Complete the development grid, coverage smokes, interruption recovery, and stageable replay; pass Gate 2 |
| 8 | Oct 12–18 | Select and review the empirical prefix or `ENGINEERING` plan; freeze protocol, methods, and accessible output pipeline; pass Gate 3 |
| 9 | Oct 19–25 | Begin the interleaved official sweep or execute the frozen engineering-validation plan; complete the pre-results paper draft |
| 10 | Oct 26–Nov 1 | Complete and audit the official sweep or validation bundle; target Gate 4 lock |
| 11 | Nov 2–8 | Perform only allowed symmetric repair/validation recovery; otherwise build the release candidate; enforce the November 8 absolute data cutoff |
| 12 | Nov 9–15 | Complete report, replay, external edits, accessibility, offline/fresh-machine checks, and final video; pass Gate 5 |
| 13 | Nov 16–22 | Package, run the judge-readiness drill, rehearse on confirmed hardware, reconcile the release manifest, and freeze the submission-ready package |
| 14 | Nov 23–29 | No scheduled project work |
| 15 | Nov 30–Dec 6 | Stage only the frozen package; rehearse to the organizer-confirmed slot and practice Q&A; no new build, data, analysis, or claims |
| 16 | Dec 7–13 | Present and submit on the confirmed date within the Dec 7–11 window; use only the November 22 frozen package |

## Portfolio outcomes by club week

This matrix gives each portfolio its visible weekly finish line without duplicating the detailed acceptance checks below or the scientific rules in `SPEC.md`. When a paper handoff is named, the owner sends concise notes plus links to evidence, a supported claim, and a limitation; the designated club paper leads turn those inputs into manuscript prose.

| Week | T1 — Agent/tasks | T2 — Corpus/adapters | T3 — Runner/evidence | T4 — Defenses/policy | T5 — Demo/release |
|---:|---|---|---|---|---|
| 4 | Run the mock; accept T1 slices; scope the first safe-tool/task issue | Complete core reading; accept T2 slices; identify the first source record | Run mock/replay; accept T3 slices; scope the first schema/evidence path | Confirm threat/policy boundaries; accept T4 slices; draft initial test vectors | Run the demo shell; accept T5 slices; initialize accessibility and paper handoffs |
| 5 | Deliver one safe tool/task path, reset, policy shape, and deterministic utility oracle | Deliver one sourced base as exact attack/clean twins across C2/C3/C4 | Deliver the six-cell D0_BASELINE vertical slice through events, scoring, JSONL, and replay; lock measurement schemas | Freeze policy/event interfaces and initial D1_POLICY_GATE/D2_DATAMARKING specifications and tests | Deliver the accessible replay shell, paper-outline inputs, and empty generated table/figure shells |
| 6 | Complete all four safe tools, ten task validators, reset tests, and golden authorization vectors | Complete five excluded development bases and validated C2/C3/C4 renders | Complete durable IDs/events, scoring, resume behavior, and analysis/report shells | Integrate D1_POLICY_GATE/D2_DATAMARKING prototypes and complete differential, coverage, and round-trip tests | Keep terminal/replay green; deliver current methods/related-work notes and accessible output examples |
| 7 | Complete clean coverage smokes and resolve task/oracle defects | Validate development fixtures, source records, adaptations, and hashes | Run the 90-cell grid plus 15 smokes; prove interruption recovery and budget/context readiness | Issue binary readiness decisions for D1_POLICY_GATE and D2_DATAMARKING from predeclared engineering checks | Run replay twice; keep accessible paper/demo assets current; hand off technical notes |
| 8 | Freeze retained tasks, fixtures, policies, validators, and hashes | Select and independently audit the eligible corpus prefix or freeze the validation ledger | Select tier/model; freeze schedule or validation plan, analysis, protocol, and hashes | Freeze retained defense implementations, policy schema, event meanings, and test evidence | Freeze methods/related-work handoffs and the accessible output pipeline |
| 9 | Keep fixture resets, safe tools, and task oracles green without semantic changes | Verify corpus/fixture hashes; finish citations and release-safe payload preparation | Complete at least half of each retained configuration or the frozen validation matrix while preserving blinding | Verify policy, defense, event, and sandbox hashes without tuning | Complete pre-results paper assets; keep replay and empty accessible outputs working |
| 10 | Audit task/utility evidence and investigate only infrastructure defects | Audit provenance, corpus integrity, and release licensing | Complete and audit the sweep/validation; generate results, intervals, or validation summaries | Audit enforcement conformance and supported security interpretations | Integrate generated artifacts into demo/replay and hand final assets to the paper leads |
| 11 | Finalize agent/task methods notes, evidence, captions, and limitation | Finalize citations, adaptation/rejection appendix, evidence, and limitation | Freeze supported results, reproducibility material, numerical audit, and manifests | Finalize threat/defense/event notes and run the safety/semantics audit | Assemble release-candidate assets, media, and accessibility support; coordinate manuscript review |
| 12 | Re-run final tool/task tests; verify demo operation and technical notes | Re-open and verify every source; finish citation/license audit | Prove fresh-clone report/replay reproduction and complete the numerical-claim audit | Re-run final defense, authorization, containment, and claim-boundary checks | Apply approved accessibility/asset edits; finish captions, transcript, offline media, and rehearsal package |
| 13 | Sign off frozen T1 artifacts and prepare component Q&A | Sign off provenance/citation artifacts and prepare component Q&A | Bind outputs to the release manifest; verify generated numbers and prepare Q&A | Sign off safety/claim language and prepare component Q&A | Package, rehearse, reconcile hashes, support final paper review, and freeze the release |
| 14 | No scheduled work | No scheduled work | No scheduled work | No scheduled work | No scheduled work |
| 15 | Stage the frozen T1 artifact and rehearse assigned Q&A only | Stage the frozen T2 artifact and rehearse assigned Q&A only | Verify the frozen replay/results package; no analysis changes | Rehearse security/limitations Q&A from frozen evidence | Stage the frozen presentation/package and fit it to confirmed logistics |
| 16 | Present or answer T1 questions as assigned | Present or answer T2 questions as assigned | Operate evidence/replay or answer T3 questions as assigned | Answer defense/safety questions as assigned | Operate the demo/replay and support delivery/submission of the frozen package |

## Weekly operating cadence

- **Monday:** update `STATUS.md`; translate the week's outcomes into bounded issues; confirm one owner, reviewer, evidence path, and due date for each active issue.
- **Tuesday–Thursday:** implement the smallest reviewable vertical changes first and keep integration continuous.
- **Friday:** open every gate-critical pull request; run the applicable mock CI, schema, safety, and replay checks; record blockers with a next action.
- **Saturday:** rehearse the exact gate checklist and prepare current evidence. Invoke a required cut before the deadline rather than assuming extra time.
- **Sunday:** show artifacts instead of reciting status; decide green/yellow/red from evidence; commit the dated `STATUS.md`, task-state changes, and next-week outcomes.

A yellow item requires an owner and repair deadline and never extends the November 8 data cutoff or November 22 release freeze. A missed gate uses the mandatory response in `SPEC.md` Section 11.

## Kickoff and core reading

- Every contributor reads `README.md`, `AGENTS.md`, `SECURITY.md`, this file, and the sections assigned by the reading guide in `SPEC.md` Section 0.
- The shared Week-4 reading is references 1–2, an overview of reference 3, and the task/threat-model overview of reference 4 in `SPEC.md` Section 18.
- By the end of Week 5, the T2 and T4 owners and project lead read the relevant methods in references 5–10 and inspect reference 15's architecture, conditions, scoring, and limitations.
- Each contributor runs the mock vertical slice, accepts one bounded first issue, identifies its acceptance evidence, and practices the Git workflow before team implementation begins.
- The judging rubric, when received, is mapped to the fixed demo and required artifacts within 24 hours. It may change presentation emphasis, never scientific definitions.

## Acceptance checks

### S00 — documentation baseline

- [x] `SPEC.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `TASKS.md`, `STATUS.md`, `SECURITY.md`, `CONTRIBUTING.md`, and `CODE_OF_CONDUCT.md` are committed.
- [x] `.github/pull_request_template.md` is committed and routes every change through the scope, safety, evidence, and documentation checks.
- [x] `docs/ARCHITECTURE.md`, `docs/INTERFACES.md`, `docs/DATA_CONTRACTS.md`, `docs/DEMO_DESIGN.md`, `docs/DATA_RELEASE.md`, `docs/decisions/README.md`, `docs/decisions/0001-document-authority.md`, `docs/decisions/0002-single-owner-model.md`, `docs/decisions/0003-weekly-status-artifact.md`, `docs/contributions/README.md`, and `docs/protocol_deviations.md` are committed.
- [x] No catch-all organizational context file exists; durable rationale uses decision records.
- [x] Links resolve and each rule has one canonical owner.
- [x] Public project slug/name treatment is recorded.
- [x] `D0_BASELINE`, `D1_POLICY_GATE`, and `D2_DATAMARKING` are the only CANARY configuration identifiers; bare `D0`, `D1`, and `D2` appear only when comparing another project's terminology.

### S01–S07 — Gate 1

- [ ] One excluded base renders into attack and exact clean twins through C2/C3/C4.
- [ ] All six D0_BASELINE attack/clean cells complete `run → events → score → JSONL → replay`.
- [ ] Schema, structural-diff, canonical-payload, deterministic-score, and no-key replay checks pass.
- [ ] Mock CI uses no credits and exercises the containment tests available at this gate; the complete arbitrary-endpoint proof is required by Gate 3.
- [ ] S01: `uv.lock` resolves the `pyproject.toml` dependencies; README setup, CI, and the Dockerfile install from it, and the Dockerfile base image is pinned by digest.
- [ ] S02: `result.schema.json` carries the case `split`, and when `split` is `evaluation` it requires non-null `protocol_version`, `channel`, `condition`, and `comparison_superblock_id`; positive and negative fixtures cover both splits.
- [ ] S04: `.env.example` lists only provider variable names with empty values, is read only by the outer runner, and is never read by CI or the mock provider.

### S08–S11 — Gate 2

- [ ] All four intrinsically safe tools and all ten deterministic task templates pass their required validators, including the four authorized high-risk clean templates.
- [ ] The 90-cell development grid completes, followed by one clean D0_BASELINE/D1_POLICY_GATE/D2_DATAMARKING smoke in one predeclared canonical adapter for each of the five task templates not represented by the development bases: 15 clean task-coverage smokes total, as defined in `SPEC.md` Section 9.
- [ ] Forced stop/resume creates no gaps, duplicates, or repeated tool effects.
- [ ] D1_POLICY_GATE and D2_DATAMARKING receive binary, outcome-blind readiness decisions.
- [ ] Context and conservative funded-budget checks support the proposed tier.

### S12 — Gate 3

- [ ] The source-audited empirical prefix is selected deterministically, or a zero-trial `ENGINEERING` plan is frozen.
- [ ] Selected model/configuration or explicit no-model reason is recorded.
- [ ] `protocol/active.json`, applicable artifacts, schedule/validation plan, and hashes reconcile.
- [ ] No evaluation candidate has been exposed to a live model.

### S13 — Gate 4

- [ ] Scheduled cells or validation checks complete under the frozen plan.
- [ ] Missingness, model comparability, hashes, resets, attempts, raw-to-endpoint recomputation, and generated outputs pass.
- [ ] Any repair follows the full symmetric-block rule before the absolute cutoff.

### S14–S15 — Gate 5 and release

- [ ] `make report` and `make replay` work from a fresh clone without a key or network in under five minutes.
- [ ] Demo runtime is based on the organizer-confirmed slot; no duration is invented.
- [ ] Replay, offline video, transcript, captions, accessibility, and failure-mode checks pass.
- [ ] Public results contain only sanitized release data and reproduce every displayed number.
- [ ] License, `CITATION.cff`, contribution consent, security policy, links, hashes, and tag agree.
- [ ] The designated club paper leads received the technical handoffs and completed drafting/editing; the project lead wrote protocol/metrics/results and approved every result, number, and limitation before submission.
- [ ] Every portfolio owner completes the judge-readiness drill below without notes and can point to the named canonical evidence.

## Judge-readiness drill

The questions are operating checks; the linked `SPEC.md` sections remain the canonical answers. Do not copy scientific definitions into this file.

| Question every relevant owner must answer | Canonical source |
|---|---|
| What independently counts as model violation and system compromise? | Sections 7 and 10 |
| Can disclosure and unauthorized action co-occur, and how is their union counted? | Sections 7 and 10 |
| How do matched clean utility and authorized high-risk tasks expose blanket refusal or overblocking? | Sections 7 and 10 |
| Would the agent violate policy without injection, and how is injection-specific risk separated? | Sections 9 and 10 |
| Why is `D1_POLICY_GATE` enforcement rather than learned resistance? | Sections 6, 7, and 10 |
| How does the policy gate detect an allowed tool used with unauthorized arguments? | Sections 6 and 7 |
| How are proposed egress, dispatch, observed effect, final disclosure, and fake-sink receipt distinguished? | Section 7 |
| Why are channel findings paired and conditional rather than universal rankings? | Sections 5 and 10 |
| What prevents outcome-based case selection or removal? | Sections 5, 9, and 11 |
| Why are logical trials and repeats nested under base cases rather than independent attacks? | Sections 9 and 10 |
| What prevents tuning on evaluation cases? | Sections 5, 9, and 11 |
| How is hosted-model drift detected and handled? | Sections 9–11 |
| Why does the project use one model—or no official model at `ENGINEERING`? | Sections 2, 9, and 12 |
| What is the scoped contribution relative to prior work | Sections 1 and 18 |
| Why might adaptive attacks defeat `D2_DATAMARKING`? | Sections 2, 6, 15, and 16 |
| Why is a live or replayed trace illustrative rather than aggregate evidence? | Sections 10 and 13 |
| Why can no real email, website, person, account, or secret be affected? | Sections 3 and 13 |
| What did each contributor personally build and validate? | Component portfolios above; Sections 14 and 17; `docs/contributions/` |

## Decisions that must not be forgotten

| Decision | Due before | Rule |
|---|---|---|
| Public project presentation | First public announcement | Use `CANARY` in all caps, make no uniqueness or novelty claim |
| Semantic configuration identifiers | Before the Week-5 measurement-contract lock | Use `D0_BASELINE`, `D1_POLICY_GATE`, and `D2_DATAMARKING` everywhere; never expose ambiguous bare aliases for this project |
| Code/content license | External contributions or release, whichever comes first | Do not publish a placeholder license or imply reuse rights |
| Contributor and citation metadata | Release candidate | Include only consented, verified names and roles |
| Paper workflow | Week-5 outline; final review before submission | Designated club paper leads draft, edit, and submit; portfolio owners provide technical notes; the project lead writes protocol/metrics/results and approves results, numbers, and limitations |
| Exact provider/model and hard budget | Gate 3 | Select from development evidence, never evaluation outcomes |
| Judging rubric and artifact mapping | Within 24 hours of receipt | Record receipt date/source in `STATUS.md` and map fixed criteria to the demo and release artifacts without changing scientific definitions |
| Demo slot and rehearsal plan | Before timed rehearsal | Record all five fields required by `docs/DEMO_DESIGN.md`: hard limit, shorter target, buffer, confirmation date/source, and first-cut sequence |
| Paper outline in Week 5; complete by release candidate | Assign an owner and satisfy the explicit S14–S15 comparison check above |
| Intended publication venue language | Release candidate | State only publicly or authoritatively verified facts |

## Maintenance rule

Update this file in the same pull request that changes slice status, owner, dependency, or cut state. Update `STATUS.md` as the dated weekly summary and link back here rather than redefining slice state. Put durable rationale in `docs/decisions/`; put post-freeze scientific deviations in `docs/protocol_deviations.md`. Never store individual performance commentary or private staffing deliberation here.
