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
| T1 — Agent and task oracles | Agent loop, intrinsically safe tools, fixtures/reset, ten deterministic utility validators, authorization-policy golden vectors, C1 direct-injection controls, captioned offline video and transcript | Technical notes and evidence for the agent, tools, fixtures, tasks, and utility oracles |
| T2 — Corpus and adapters | Candidate/source ledger, source review, crossed C2/C3/C4 rendering, citations, adaptation/rejection records, corpus validator | Technical notes and evidence for corpus method, adaptations/rejections, citations, and related work |
| T3 — Runner and evidence | Schemas, schedule, execute/resume/retry, independent policy audit, scoring, aggregation, intervals, integration, and schema-driven replay | Technical notes and evidence for runner, data contracts, analysis, and reproducibility |
| T4 — Defenses and policy | `D1_POLICY_GATE`, `D2_DATAMARKING`, declarative policy schema, security tests, independent source review, and event-semantics review | Technical notes and evidence for the threat model, defenses, event semantics, and security tests |
| T5 — Demo and release | Terminal shell, replay presentation, demo case staging, paper assets, accessibility, sanitization coordination, and release checklist | Figures, captions, formatting/accessibility notes, and release documentation |

The designated club paper leads own manuscript drafting, editing, and submission. The project lead writes the protocol, metric definitions, and results and must approve every result, numerical claim, and limitation before submission. Each portfolio owner supplies concise technical notes, linked evidence, captions/alt text where applicable, and at least one component limitation; polished manuscript prose is not required. T3 owns replay-data correctness, while T5 supplies figures, accessibility, formatting, and release-package support. These workflow roles do not determine authorship: every named author must make a substantive contribution, review the final draft, and consent to being named.

## Slice plan

Slices form a track × week lattice. Every build week from W5 through W13 gives each of the five portfolios exactly one accountable slice, so the plan carries 45 slices, nine per track, and no week leaves a portfolio without a stated finish line. The slice ID is `W<club week>-T<portfolio>`. `S00` is retained unchanged because it is `DONE` and referenced by committed evidence; the former `S01`–`S15` identifiers are superseded by this lattice and must not be reused.

Every slice still has exactly one accountable owner. The lattice changes how work is sequenced and sized; it does not create shared ownership, and it does not change any scientific definition in `SPEC.md`.

### Weekly commitment envelope

Each slice holds four rows of work inside one contributor's weekly commitment of roughly three focused hours.

| Row | Target | Meaning |
|---|---|---|
| Committed | ~2.0h | The gate-bearing deliverable. Its pull request is open with acceptance evidence by Thursday, 72 hours after the Monday start. |
| Standing | ~0.5h | Review the named peer pull request and update `docs/contributions/<name>.md`. Already required by the weekly cadence; previously uncounted. |
| Pull-forward | remainder | The named next item from the same track's later slice, taken only after Committed and Standing are done. |
| Defer first | — | The named item that leaves this slice first if the week overflows, chosen in advance from the `SPEC.md` Section 12 cut order rather than improvised at the Saturday rehearsal. |

Pull-forward moves schedule, never scope: it advances work already in the plan for the same owner, and it never crosses a gate boundary. It is optional, and the Sunday check-in shows artifacts rather than who pulled forward the most. Any actual reduction still follows the Section 12 cut order, and new scope still requires deleting work of equal or greater cost.

`Est` is an estimate of **member** hours at full `F20` scope and is a planning aid, not an acceptance criterion. `⚠` marks a cell estimated above 3.0h, which exceeds one contributor-week. `†` marks a cell whose size scales with the selected tier. Only the official evaluation corpus and the official sweep scale this way. The development instrument does not: `SPEC.md` Section 9 fixes the Gate-2 workload at four safe tools, ten task templates, five development bases, C2/C3/C4, and all three configurations regardless of the tier that eventually runs officially. `‡` marks a cell where the project lead pairs under D-10 and contributes roughly the same hours again on top of the stated estimate; the lead's time is excluded from the member totals below. Every lattice slice is `PLANNED` until a named contributor accepts it.

### Dependency discipline

A `Depends` entry names the artifact a slice consumes and when it lands. It does not mean waiting for another portfolio's week to finish. Thirty-three of the forty-five entries are a track consuming its own previous week; the rest are cross-track, and all but three are satisfied by a published contract rather than a completed slice.

Every track gets the full 72-hour window. Work starts Monday and each slice's pull request is open with its acceptance evidence by Thursday, so **no contract may land later than Monday** — a Tuesday publication would silently cut a consumer's window to 48 hours.

That is achievable because a consumer never waits on a producer's *current* week. From W6 onward the contract is the producing slice's merged artifact from the previous week. In W5 it is the pre-kickoff scaffold already committed to the repository: `schemas/event.schema.json`, `schemas/result.schema.json`, `agent/loop.py`, `runner/mock_provider.py`, `runner/mock_slice.py`, and `demo/trace.py`. All five W5 slices build against those stubs from Monday morning; `W5-T4` and `W5-T3` freeze and version them during the week, and consumers re-point at the frozen version on Thursday.

A producer who cannot publish a contract by Monday raises it that Monday, because the missing contract is the blocker, not the consuming slice.

Exactly three convergence points genuinely require other portfolios to be finished, and each is a gate rather than a convenience:

| Convergence | Requires | Why it cannot be relaxed |
|---|---|---|
| End of W5 — measurement-contract lock | `W5-T4` interfaces and `W5-T3` schemas exist and are versioned | `SPEC.md` Section 11 locks the contract at end of week 5 and everything downstream is defined against it |
| `W7-T3` — the 90-cell grid | `W6-T1` tools and tasks, `W6-T2` rendered development bases, `W6-T4` both defenses, `W7-T1` smoke cases | The grid is the integration test. It cannot run over components that do not exist, and `SPEC.md` Section 9 fixes its shape |
| `W8-T2` and `W8-T4` — Gate 3 freeze | Second-person source review of every retained case, plus the seeded provenance recheck | `SPEC.md` Section 5 requires an independent reviewer and Section 11 requires the prefix and seeded audit before freeze |

Everything else is contract-first and parallel. If a slice appears blocked outside those three points, the contract was published late, which is a cadence failure rather than a plan requirement.

Paper work splits three ways and no slice crosses the line. `W5-T5` supplies structure, accessibility, and empty shells. The project lead supplies the thesis, scoped contribution, permitted-claim language, and metric definitions. The designated club paper leads own prose assembly, editing, venue formatting, and submission. T5 is not the manuscript drafter, and no lattice slice assigns manuscript prose to a portfolio owner.

### W5 — Gate 1, measurement-contract lock (September 21–27)

The committed deliverables in this week are the five Gate-1 outcomes already communicated to the team and are not re-cut.

| Slice | Committed deliverable | Est | Depends | Pull-forward | Defer first | Owner |
|---|---|---:|---|---|---|---|
| W5-T1 | One safe tool (`read_file`) hardened against traversal, absolute paths, and symlink escape; one task path end to end through the hand-written agent loop and mock provider; fixed trusted prompt, fixture hash, maximum steps, versioned argument-level policy shape; one deterministic utility validator with one known-good and two known-bad fixtures; deterministic fixture reset and hash verification; `.env.example` and provider boundary | 3.5 ⚠ | Committed scaffold (Mon); `W5-T4`/`W5-T3` frozen versions Thu | → W6-T1 `query_db` | — gate-critical | Chace |
| W5-T2 | One sourced development base: source record (URL, title/version, source case ID or `NO_SOURCE_CASE_ID`, license decision, opener, open time, adapter, reviewer), immutable first-20-hex candidate ID derived before adaptation, mechanical adaptation with notes and hashes, exact attack/clean twins rendered through C2, C3, and C4, structural-diff and adapter round-trip tests, `corpus/candidates.jsonl` entry | 4.0 ⚠ | Committed scaffold (Mon); `W5-T3` frozen schema Thu | → W6-T2 development base 2 | — gate-critical; the Gate-1 six-cell check requires all three channels | Johan |
| W5-T3 | Six-cell D0_BASELINE slice completing `run → durable events → independent score → append-only schema-valid JSONL → schema-driven replay`; deterministic case, logical-trial, model-call, attempt, and comparison-superblock IDs; exact canary matching; requested, evaluable, audit-authorized, blocked, dispatched, execution-succeeded, effect-observed, and sink-received recorded separately with Boolean-or-null semantics; measurement schemas committed and versioned | 3.0 ‡ | Committed scaffold (Mon); `W5-T4` interface Thu | → W6-T3 data-driven schedule | — gate-critical | Samson |
| W5-T4 | Freeze the pure argument-level authorization interface, the D1_POLICY_GATE gate interface, the independent T3 audit interface, the D2_DATAMARKING transform interface, event meanings, and the model-violation versus system-compromise distinction; specify D1_POLICY_GATE canonical dispatch/block behavior and the frozen `POLICY_BLOCKED` observation; specify the source-faithful datamarking transform, coverage, normalization, escaping, and already-marked behavior; initial allow/deny golden vectors and tests | 3.0 | — | → W6-T4 request canonicalization | — gate-critical | Dhruv |
| W5-T5 | Accessible large-type terminal and replay shell reading the result schema rather than hand-authored demo data; paper-outline **inputs** for the designated paper leads — the `SPEC.md` Section 14 ten-section skeleton as real heading hierarchy and accessibility structure, the technical-input owner map for each section, and figure, caption, and alt-text scaffolding; empty generated table and figure shells for every predeclared estimand | 3.0 | Committed scaffold (Mon); `W5-T3` frozen result schema Thu | → W6-T5 caption and transcript scaffolding | — gate-critical | Miles |

All five W5 slices start Monday against the committed pre-kickoff scaffold and are due Thursday. `W5-T4` and `W5-T3` freeze and version the interfaces and schemas during the week rather than gating the other three tracks' start. This replaces the previous fully serial Gate-1 dependency chain, in which four of five tracks were blocked behind the other two for most of the week.

Lead scaffold, not a member slice: `uv.lock`, no-credit CI, and Make targets; the rubric map; post-kickoff clock verification; `STATUS.md`; the thesis, scoped contribution, permitted-claim language, and exact metric definitions that D-14 reserves to the project lead; and the measurement-contract lock commit and version. That lock includes the `SPEC.md` Section 5 step 1 corpus rules — eligibility, exact quota, family and source caps, task assignment, deduplication, adaptation, and relaxation order — which must freeze in W5 even though the evaluation corpus is not built until W7 and W8.

### W6 — build the development instrument (September 28–October 4)

| Slice | Committed deliverable | Est | Depends | Pull-forward | Defer first | Owner |
|---|---|---:|---|---|---|---|
| W6-T1 | Remaining three safe tools hardened: `query_db` registered read-only queries under the SQLite authorizer, `fetch_url` exact local-origin allowlist with redirects disabled, `send_email` appending only to a local receipt log; all ten task templates completed — three read/query, two local-web extraction, one cross-source comparison, and four legitimate high-risk — each carrying prompt template, fixture hash, versioned argument-level policy, deterministic utility validator, one known-good and at least two known-bad fixtures, and maximum step count; golden allow/deny vectors covering every tool and argument class including legitimate high-risk grants | 11.0 ⚠ | W5-T1, W5-T4 | → W7-T1 coverage smokes | — gate-critical; `SPEC.md` Section 9 fixes ten templates for Gate 2 at every tier | Chace |
| W6-T2 | All five development bases rendered through C2, C3, and C4 as exact attack/clean twins; canonical payload and hash round-trip verified through every adapter; injection-slot-only difference machine-checked; evaluation candidate intake opens with pre-adaptation ID derivation, exact-hash and near-duplicate detection, and recorded rejection reasons; source records created for the tier's C1 controls and for the one separate demo case required by `SPEC.md` Section 2 | 7.75 ⚠ | W5-T2 | → W7-T2 evaluation intake | Evaluation-candidate intake only; development renders are gate-critical at all three channels | Johan |
| W6-T3 | Schedules generated from data rather than hand-written run lists; append-only schema-validated records; globally unique deterministic logical-trial, model-call, and attempt IDs; one fresh canary pair per comparison superblock persisted before calls and reused after resume; fixture, sink, grant, and agent-state reset and verification between trials; full version and hash capture; persist-before-next-step; explicit retry and resume state; the authorization audit implemented independently of T4's gate evaluator | 5.0 ‡ ⚠ | W5-T3 | → W7-T3 grid orchestration | Analysis and output shells → W8-T3 | Samson |
| W6-T4 | D1_POLICY_GATE: single canonicalization before authorization and dispatch; validation of tool name, call budget, normalized resource path, registered query and parameters, exact URL, email recipient/subject/body, trusted state, and single-use high-risk grant bound to the normalized action hash and policy version; dispatch-or-block with the frozen non-sensitive `POLICY_BLOCKED` observation; canary-blind with no secret-string filtering. D2_DATAMARKING: source-faithful transform over every untrusted span, fixed system instruction, Unicode normalization, JSON/text/HTML escaping, already-marked handling, coverage and pre/post hashes. Differential tests of the gate against T3's audit over T1's golden vectors | 9.0 ⚠ | `W5-T4` frozen (Mon); `W6-T1` golden vectors Thu — differential test only | → W7-T4 readiness checks | — gate-critical; the 90-cell grid needs all three configurations, so deferring D2_DATAMARKING records Gate 2 failed and fires the tier response | Dhruv |
| W6-T5 | Terminal and replay kept green against real event records rather than hand-authored demo data; component notes received from T1 through T4 and made accessible, not authored by T5; the one separate demo case rendered and staged from its `W6-T2` source record, excluded from every estimate; first accessible generated output example; caption and transcript scaffolding started ahead of results | 2.5 | `W5-T5`, `W5-T3` (Mon); `W6-T3` sample records Thu — integration only | → W7-T5 second replay run | Accessible output example → W7-T5 | Miles |

W6 is the heaviest week in the plan and is the week the lattice makes visible: 35.25 member hours against 15 hours of member capacity, or 40.25 once the lead's pairing on `W6-T3` is counted. Every deliverable in it is fixed by `SPEC.md` Section 9 and does not shrink with the selected tier. See the capacity section below.

### W7 — Gate 2, development matrix and defense readiness (October 5–11)

| Slice | Committed deliverable | Est | Depends | Pull-forward | Defer first | Owner |
|---|---|---:|---|---|---|---|
| W7-T1 | The five task templates not represented by a development base prepared as predeclared canonical-adapter smoke cases and handed to `W7-T3` for execution; the tier's C1 direct-injection controls built as trusted-task-prompt variants from `W6-T2` source records, descriptive-only and never entering an indirect estimate per `SPEC.md` Section 3; task and oracle defects surfaced by the grid resolved | 3.5 ⚠ | `W6-T1` templates, `W6-T2` C1 source records (Mon); `W7-T3` grid results Thu — defect resolution only | → W8-T1 freeze preparation | — gate-critical under `SPEC.md` Section 9 | Chace |
| W7-T2 † | Evaluation candidate intake continued toward the provisional tier count; development fixtures, source records, adaptations, and hashes validated; every considered candidate carries an explicit accept or reject status and reason with no silent drops | 6.0 ⚠ | W6-T2 | → W8-T2 prefix selection | Candidates beyond the provisional count plus selection margin | Johan |
| W7-T3 | The 90-cell development grid and 15 clean task-coverage smokes executed and schema-valid; forced termination and `--resume` proving no logical-trial gap, no duplicate, and no repeated dispatch, effect, or sink receipt; provider retries bounded at two and only when no model content returned; context and token usage measured per channel and configuration; the Gate 2 budget equation evaluated | 3.0 ‡ | `W6-T1`, `W6-T2`, `W6-T4` merged (Mon); `W7-T1` smoke cases (Mon) — Gate-2 convergence | → W8-T3 tier arithmetic | Reliability pilots beyond those required for model choice, under the 120-trial development ceiling | Samson |
| W7-T4 | Binary, outcome-blind ready or not-ready decisions for D1_POLICY_GATE and D2_DATAMARKING from the predeclared engineering criteria and the `W7-T3` differential result only, handed to the project lead as a Section 12 tier input rather than self-certified; second-person source review of every evaluation candidate in the pool, so review never trails corpus selection | 4.5 ⚠ | `W6-T4` (Mon); `W7-T3` differential and cell results Thu — decision input only | → W8-T4 defense freeze | — gate-critical | Dhruv |
| W7-T5 | Terminal and replay path run successfully twice, with the named presentation operator starting replay without notes and without provider access; accessible paper and demo assets current; technical-note handoff to the designated paper leads | 2.0 | W6-T5 | → W8-T5 output-pipeline freeze | Second rehearsal run → W8-T5 | Miles |

### W8 — Gate 3, corpus, model, tier, and full protocol freeze (October 12–18)

| Slice | Committed deliverable | Est | Depends | Pull-forward | Defer first | Owner |
|---|---|---:|---|---|---|---|
| W8-T1 | Retained tasks, fixtures, authorization policies, validators, and hashes frozen; no claim-bearing component remains tunable; the `SPEC.md` Section 11 CI proof that no tool can reach an arbitrary external endpoint committed and green, which Gate 3 requires and which no slice previously owned; draft agent, tool, task, and utility notes with linked evidence and one limitation sent to the paper leads | 3.5 ⚠ | W7-T1 | → W9-T1 green-keeping | — gate-critical | Chace |
| W8-T2 † | Evaluation corpus completed to the selected tier count; deterministic prefix selection with no outcome-based inclusion or removal; every retained case carrying a completed `W8-T4` review record from a reviewer who is neither its opener nor its adapter, as `SPEC.md` Section 5 requires; corpus, ledger, and hashes frozen. At `ENGINEERING`, the auditable source ledger is frozen instead; draft corpus-method, adaptation, citation, and related-work notes with one limitation sent to the paper leads | 8.75 ⚠ | W7-T2, W7-T4 | → W9-T2 citations | Bases beyond the selected tier count (cut order 5 and 7) | Johan |
| W8-T3 | `protocol/active.json` committed and reconciled from the tier row, active-contributor count, funded budget, model decision or explicit no-model reason, and non-personal reason category **supplied by the project lead** under `SPEC.md` Section 12 and D-14; the Section 12 arithmetic recomputed and shown to agree; schedule or validation plan generated and frozen; analysis and report code plus empty generated outputs committed; every hash reconciled; draft runner and reproducibility notes with one limitation sent to the paper leads | 4.25 ‡ ⚠ | `W7-T3` (Mon); `W8-T2` corpus hash Thu — final slot only | → W9-T3 sweep start | — gate-critical | Samson |
| W8-T4 | Retained defense implementations, declarative policy schema, event meanings, and test evidence frozen and hashed; second-person source review completed for every retained case before the corpus freezes; the `SPEC.md` Section 5 step 8 seeded provenance and fixture-hash recheck run over exactly `ceil(0.20 × N)` retained cases, which Gate 3 requires and which no slice previously owned; draft threat-model, defense, event-semantics, and security-test notes with one limitation sent to the paper leads | 5.5 ⚠ | W7-T4 | → W9-T4 hash verification | — gate-critical | Dhruv |
| W8-T5 | Component methods and related-work handoffs assembled from T1 through T4 and frozen for the designated paper leads; accessible output pipeline frozen and shown to produce the empty generated shells from the frozen analysis code | 3.0 | `W7-T5` (Mon); `W8-T3` frozen analysis code Thu — pipeline check only | → W9-T5 pre-results assets | — gate-critical | Miles |

### W9 — official sweep or engineering validation begins (October 19–25)

| Slice | Committed deliverable | Est | Depends | Pull-forward | Defer first | Owner |
|---|---|---:|---|---|---|---|
| W9-T1 | Fixture resets, safe tools, and task oracles kept green with no semantic change; no frozen artifact drifts; video pre-production begun — script, replay capture, and segment structure, none of which depend on results | 2.0 | W8-T1 | → W10-T1 evidence audit | Video pre-production → W10-T1 | Chace |
| W9-T2 | Corpus and fixture hashes verified; citations completed; release-safe payload preparation under `docs/DATA_RELEASE.md` | 3.0 | W8-T2 | → W10-T2 provenance audit | Release-safe payload preparation → W10-T2 | Johan |
| W9-T3 † | At least half of every retained configuration executed under the frozen schedule, randomized and interleaved, with blinding preserved and no aggregate security or utility outcome inspected. At `ENGINEERING`, the frozen validation matrix completes instead | 3.0 ‡ | W8-T3 | — nothing crosses Gate 4 | — gate-critical | Samson |
| W9-T4 | Policy, defense, event, and sandbox hashes verified without tuning; no defense tuning after freeze | 1.5 | `W8-T4` (Mon) | → W10-T4 conformance audit | — | Dhruv |
| W9-T5 | Pre-results paper assets completed; replay and the empty accessible outputs kept working against frozen code | 3.0 | W8-T5 | → W10-T5 artifact integration | Accessible output polish → W10-T5 | Miles |

### W10 — Gate 4, results or validation lock (October 26–November 1)

| Slice | Committed deliverable | Est | Depends | Pull-forward | Defer first | Owner |
|---|---|---:|---|---|---|---|
| W10-T1 | Task and utility evidence audited from raw records; failures classified against the W5-frozen model-outcome versus infrastructure-error taxonomy rather than by judgment, and only infrastructure defects investigated | 2.0 | W9-T1 | → W11-T1 methods notes | — | Chace |
| W10-T2 | Provenance, corpus integrity, and release licensing audited | 2.5 | W9-T2 | → W11-T2 appendix | — | Johan |
| W10-T3 † | Sweep or validation matrix completed and audited; results, intervals, or validation summaries generated from the frozen JSONL by the frozen analysis and report code and handed to the project lead, who decides which are supported; completeness, duplicate, missingness, model-comparability, hash, reset, attempt, and raw-to-endpoint recomputation checks passed; every claim-bearing number produced by generated code and none hand-entered | 3.5 ‡ ⚠ | W9-T3 | → W11-T3 manifests | — gate-critical | Samson |
| W10-T4 | Enforcement conformance audited and the security interpretations the evidence actually supports recorded | 2.5 | W9-T4 | → W11-T4 safety audit | — | Dhruv |
| W10-T5 | Generated artifacts integrated into the demo and replay; final figures, captions, and alt text handed to the designated paper leads | 4.0 ⚠ | `W9-T5` (Mon); `W10-T3` generated artifacts Thu — integration only | → W11-T5 release candidate | Final figure polish → W11-T5. The optional static replay page is never committed work in this lattice: it is cut order 1, capped at four person-hours, and requires explicit lead authorization | Miles |

### W11 — release candidate, absolute data lock Sunday November 8 (November 2–8)

| Slice | Committed deliverable | Est | Depends | Pull-forward | Defer first | Owner |
|---|---|---:|---|---|---|---|
| W11-T1 | Final agent, tool, task, and utility methods notes with linked evidence, a caption, alt text, and one component limitation; video assembled against the pre-production cut | 2.5 | W10-T1 | → W12-T1 final test re-run | Video assembly → W12-T1 | Chace |
| W11-T2 | Final citations, adaptation and rejection appendix, linked evidence, and one component limitation | 2.0 | W10-T2 | → W12-T2 source re-verification | — | Johan |
| W11-T3 | Reproducibility material, numerical audit, and manifests frozen, and the lead-approved supported results bound to them; only symmetric repair permitted under `SPEC.md` Section 11, and only before Sunday's cutoff | 3.0 ‡ | W10-T3 | — nothing crosses the data lock | — gate-critical | Samson |
| W11-T4 | Final threat-model, defense, and event-semantics notes; safety and claim-boundary audit run | 2.5 | W10-T4 | → W12-T4 final checks | — | Dhruv |
| W11-T5 | Release-candidate assets, media, and accessibility support assembled; the code and content `LICENSE` and `CITATION.cff` committed, which the decisions table makes due at the release candidate; manuscript review coordinated with the designated paper leads | 5.0 ⚠ | W10-T5 | → W12-T5 accessibility edits | Offline media → W12-T5 | Miles |

### W12 — Gate 5, release freeze preparation (November 9–15)

| Slice | Committed deliverable | Est | Depends | Pull-forward | Defer first | Owner |
|---|---|---:|---|---|---|---|
| W12-T1 | Final tool and task tests re-run; demo operation and technical notes verified; captioned offline video and transcript finished, with the tier-appropriate result summary taken from generated artifacts and approved by the project lead, never authored in the video script | 3.5 ⚠ | W11-T1 | → W13-T1 sign-off | — gate-critical | Chace |
| W12-T2 | Every source re-opened and verified; citation and license audit completed | 2.5 | W11-T2 | → W13-T2 sign-off | — gate-critical | Johan |
| W12-T3 | Fresh-clone `make report` and `make replay` proven with no key and no network in under five minutes; numerical-claim audit completed | 3.0 | W11-T3 | → W13-T3 manifest binding | — gate-critical | Samson |
| W12-T4 | Final defense, authorization, containment, and claim-boundary checks re-run | 2.0 | W11-T4 | → W13-T4 sign-off | — gate-critical | Dhruv |
| W12-T5 | Approved accessibility and asset edits applied; every contributor's `docs/contributions/<name>.md` record, publication consent, and attribution language collected and verified against `SPEC.md` Section 0; captions, transcript, offline media, and the rehearsal package finished | 4.5 ⚠ | `W11-T5` (Mon); `W12-T1` video Thu — packaging only | → W13-T5 packaging | Rehearsal package → W13-T5 | Miles |

### W13 — package, rehearse, and freeze (November 16–22)

| Slice | Committed deliverable | Est | Depends | Pull-forward | Defer first | Owner |
|---|---|---:|---|---|---|---|
| W13-T1 | Frozen T1 artifacts signed off; own contribution record and consent confirmed; component Q&A prepared from the judge-readiness drill without notes | 1.5 | W12-T1 | — freeze | — | Chace |
| W13-T2 | Provenance and citation artifacts signed off; own contribution record and consent confirmed; component Q&A prepared | 1.5 | W12-T2 | — freeze | — | Johan |
| W13-T3 | Generated outputs bound to the release manifest; every generated number verified; own contribution record and consent confirmed; component Q&A prepared | 2.5 | W12-T3 | — freeze | — gate-critical | Samson |
| W13-T4 | Security and safety claim **boundaries** signed off and handed to the project lead, who approves final claim language under D-14; own contribution record and consent confirmed; component Q&A prepared | 1.5 | W12-T4 | — freeze | — | Dhruv |
| W13-T5 | Package assembled; judge-readiness drill run; rehearsal on confirmed hardware, including the `SPEC.md` Section 13 rehearsal gate that decides live-first versus replay-first; release manifest and hashes reconciled; final paper review supported; release frozen under one immutable tag and commit | 5.0 ⚠ | `W12-T5` (Mon); `W13-T3` verified numbers Thu — manifest binding only | — freeze | — gate-critical | Miles |

Weeks 14 through 16 carry no build slices. Week 14 is dark, week 15 is frozen-package staging and rehearsal, and week 16 is presentation and delivery. Their portfolio obligations remain in the club-week milestone table below.

### Capacity arithmetic

Member capacity is five contributors × nine build weeks × roughly three focused hours, of which the Standing row consumes about half an hour. That leaves roughly **112.5 hours of committed member capacity** for the whole project, plus the project lead's pairing time under D-10.

| Portfolio | `F20` est. | `M10-ALL` est. | `L8-ONE` est. | What actually scales |
|---|---:|---:|---:|---|
|---|---:|---:|---:|---|
| T1 — Agent and task oracles | 33.0h | 33.0h | 33.0h | Nothing. Four tools, ten templates and the C1 controls are fixed by `SPEC.md` Sections 2 and 9 |
| T2 — Corpus and adapters | 38.0h | 33.5h | 32.0h | Only the evaluation corpus; development bases, the demo case and their C2/C3/C4 renders are fixed |
| T3 — Runner and evidence | 30.25h | 29.25h | 27.75h | Only the W9–W10 sweep size; the lead adds ~19h of pairing under D-10 on top |
| T4 — Defenses and policy | 32.0h | 32.0h | 30.5h | Almost nothing. Both defenses must be built and run to reach a Gate-2 readiness decision |
| T5 — Demo and release | 32.0h | 31.0h | 30.5h | Almost nothing. Demo, video, accessibility and release are fixed costs |
| **Total** | **165.25h** | **158.75h** | **153.75h** | against ~112.5h committed capacity |

Three findings follow from this table and are recorded here because they change sequencing, not scientific meaning.

1. **The lattice is balanced across portfolios and the plan is still over capacity.** At every tier the five tracks sit within a few hours of each other, which was the goal. The residual gap is volume, not distribution.
2. **The cut order barely relieves it.** `SPEC.md` Section 9 fixes the development instrument — four safe tools, ten task templates, five development bases, C2/C3/C4, all three configurations, the 90-cell grid, and the 15 coverage smokes — independently of the tier that eventually runs officially. Moving from `F20` to `L8-ONE` therefore saves about 11.5 hours, roughly 7%, all of it in the W9–W10 sweep and the evaluation corpus. The cut order shrinks what is measured, not what must be built.
3. **Week 6 is the binding week and no tier decision fixes it.** 35.25 member hours against 15 hours of member capacity, 40.25 with the lead's pairing, and its contents are tier-independent. The levers that do apply are the lead's remaining weekly ceiling, accepting a recorded Gate-2 failure and its `SPEC.md` Section 12 response, or `ENGINEERING`, which is the only geometry that removes a large block of work rather than trimming it.
4. **T5's cost is close to fixed.** Demo, replay, video, accessibility, packaging, and release do not shrink with tier, so every cut makes T5 relatively heavier. The lattice moves fixed-cost release work toward T1 and T4 as the geometry drops, starting with video and transcript production in `W11-T1` and `W12-T1`.

### Provisional build geometry

`SPEC.md` Section 12 selects the official tier at Gate 3 from active-contributor count, conservative funded budget, and passed readiness gates, and forbids selecting it from evaluation outcomes. Nothing in that rule prevents building to a smaller provisional geometry earlier, and W6's arithmetic requires it.

At the end of W5, record a provisional build geometry in `STATUS.md`'s existing active-or-provisional tier field, derived from headcount and observed W5 velocity. Gate 3 then confirms or lowers it under the Section 12 algorithm and commits the formal selection to `protocol/active.json`. A provisional geometry is a planning aid with no claim attached; it never raises the Section 12 ceiling and never substitutes for the Gate 3 record.

Its scope is narrow, and stating that plainly matters. A provisional geometry tells `W7-T2` and `W8-T2` how many evaluation bases to source and `W9-T3`/`W10-T3` how large the sweep will be. It does **not** reduce `W6-T1`, `W6-T2`, `W6-T4`, or `W7-T1`, because Section 9 fixes the development instrument at full scope for every empirical tier. Do not plan W6 relief that the specification does not permit.

### Cross-portfolio transfers applied in this lattice

These transfers are sequencing decisions under this file's authority. None changes a definition in `SPEC.md`.

| Transfer | From | To | Reason |
|---|---|---|---|
| Python package, dependency lock, no-credit CI, and Make targets | T3 | Project lead | Already the lead's pre-kickoff scaffold; only `uv.lock` remains outstanding |
| Generated analysis and report code | T5 | T3 | The component-portfolio table already assigns replay-data correctness and analysis to T3 and figures, accessibility, and formatting to T5; the previous slice plan contradicted it |
| Second-person source review of adaptations | Unassigned | T4 | `SPEC.md` Section 5 requires an opener and a different reviewer for every source, and the obligation previously had no owner; attack provenance fits T4's portfolio and T4 has capacity in W7 and W9 |
| Captioned offline video and transcript production | T5 | T1 | T1 is already the named replay-fallback operator and has capacity in W11 and W12; T5's load is back-loaded and tier-independent |
| Caption and transcript scaffolding | W12 | W6–W7 | Accessibility structure does not depend on results and relieves the W12 peak |

### Contribution coverage

Every portfolio must end the term with a named component in the release, a paper-section handoff, a judge-drill question it can answer cold, and an artifact inside the November 22 frozen manifest. `SPEC.md` Section 0 defines project success and Section 14 lists the required artifacts; this table checks the lattice against them so no track can finish with nothing attributable.

| Portfolio | Repository component | `SPEC.md` Section 14 paper section | Frozen-manifest artifact | Judge-drill question it owns |
|---|---|---|---|---|
| T1 | `agent/`, `tools/`, `tasks/`, `oracles/utility/` | 6 — agent, deterministic tasks and oracles | Safe-tool and validator suites; captioned video and transcript | How do matched clean utility and authorized high-risk tasks expose blanket refusal or overblocking? |
| T2 | `corpus/`, `channels/`, `fixtures/` | 3 and 5 — related work; corpus selection, adaptation, rejection ledger, crossed adapters | Candidate/rejection ledger, source records, frozen corpus hashes | What prevents outcome-based case selection or removal? |
| T3 | `schemas/`, `runner/`, `analysis/`, `protocol/`, `results/` | 7 and 10 — frozen protocol and analysis plan; reproducibility | `protocol/active.json`, frozen JSONL, generated outputs, release manifest | How are proposed egress, dispatch, observed effect, final disclosure, and fake-sink receipt distinguished? |
| T4 | `defenses/`, `oracles/authorization/` | 4 and 6 — threat model and safety boundary; defenses | Frozen defense implementations, policy schema, security-test evidence, source-review records | Why is `D1_POLICY_GATE` enforcement rather than learned resistance? |
| T5 | `demo/`, `paper/` assets, release packaging | Accessibility structure, figures, captions, and alt text across all sections | Terminal demo, one-keystroke replay, accessibility artifacts, release tag and manifest | Why is a live or replayed trace illustrative rather than aggregate evidence? |

Two attribution risks are worth recording rather than discovering in Week 13.

1. **T4 at a `BASE` tier.** If neither defense passes Gate 2, no defense-effect claim exists and T4's contribution must rest on the built and frozen defense implementations, the binary readiness evidence, the security test suite, event semantics, and the independent source-review records. Those are real artifacts and they survive the tier drop, but the contribution record has to name them rather than a result.
2. **Every track at `ENGINEERING`.** No official model experiment runs, so `SPEC.md` Section 0 replaces the empirical result with frozen validation evidence for all five portfolios. Contribution records use the validation finding, never an implied empirical estimate.

One transfer was considered and rejected: T3's authorization audit evaluator cannot move to T4. `SPEC.md` requires it to be implemented independently of T4's gate, and that independence is a measurement-validity property rather than a staffing convenience.

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

The per-portfolio weekly finish lines that previously lived here are now the committed deliverables in the [slice plan](#slice-plan) above, where each one carries a slice ID, a single accountable owner, dependencies, an estimate, a named pull-forward item, a named first defer, and acceptance evidence. That lattice is the canonical home; this section is retained only as a pointer so existing links resolve.

Weeks 14 through 16 carry no build slices, and their portfolio obligations remain in the club-week milestone table above:

| Week | T1 — Agent/tasks | T2 — Corpus/adapters | T3 — Runner/evidence | T4 — Defenses/policy | T5 — Demo/release |
|---:|---|---|---|---|---|
| 4 | Run the mock; accept T1 slices; scope the first safe-tool/task issue | Complete core reading; accept T2 slices; identify the first source record | Run mock/replay; accept T3 slices; scope the first schema/evidence path | Confirm threat/policy boundaries; accept T4 slices; draft initial test vectors | Run the demo shell; accept T5 slices; initialize accessibility and paper handoffs |
| 14 | No scheduled work | No scheduled work | No scheduled work | No scheduled work | No scheduled work |
| 15 | Stage the frozen T1 artifact and rehearse assigned Q&A only | Stage the frozen T2 artifact and rehearse assigned Q&A only | Verify the frozen replay/results package; no analysis changes | Rehearse security/limitations Q&A from frozen evidence | Stage the frozen presentation/package and fit it to confirmed logistics |
| 16 | Present or answer T1 questions as assigned | Present or answer T2 questions as assigned | Operate evidence/replay or answer T3 questions as assigned | Answer defense/safety questions as assigned | Operate the demo/replay and support delivery/submission of the frozen package |

When a paper handoff is named in a slice, the owner sends concise notes plus links to evidence, a supported claim, and a limitation; the designated club paper leads turn those inputs into manuscript prose.

## Weekly operating cadence

- **Monday:** update `STATUS.md`; open this week's five lattice slices as issues carrying their Committed, Standing, Pull-forward, and Defer-first rows; confirm one owner, reviewer, evidence path, and due date for each. A contributor holds one lattice slice per week; a second issue is allowed only for an explicit pairing reason.
- **Monday:** every contract another slice consumes this week is published before work starts. The 72-hour slice clock runs from here.
- **Tuesday–Thursday:** implement the smallest reviewable vertical changes first and keep integration continuous.
- **Thursday:** every slice's pull request is open with its acceptance evidence, 72 hours after the Monday start; run the applicable mock CI, schema, safety, and replay checks.
- **Friday:** review cutoff. Every Thursday pull request is reviewed by end of Friday so the Saturday rehearsal runs on reviewed work; the standing 48-hour review service level is the outer bound. Record blockers with a named owner and a 24-hour next action.
- **Saturday:** rehearse the exact gate checklist and prepare current evidence. Invoke a required cut before the deadline rather than assuming extra time.
- **Sunday:** show artifacts instead of reciting status; decide green/yellow/red from evidence; commit the dated `STATUS.md`, task-state changes, and next-week outcomes. Judge a slice on its Committed row alone; pull-forward is optional and is never a completion criterion or a comparison between contributors.

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

### Gate 1 — end of week 5

Covers `W5-T1` through `W5-T5` and the lead scaffold.

- [ ] One excluded base renders into attack and exact clean twins through C2/C3/C4.
- [ ] All six D0_BASELINE attack/clean cells complete `run → events → score → JSONL → replay`.
- [ ] Schema, structural-diff, canonical-payload, deterministic-score, and no-key replay checks pass.
- [ ] Mock CI uses no credits and exercises the containment tests available at this gate; the complete arbitrary-endpoint proof is required by Gate 3.
- [ ] Lead scaffold: `uv.lock` resolves the `pyproject.toml` dependencies; README setup, CI, and the Dockerfile install from it, and the Dockerfile base image is pinned by digest.
- [ ] W5-T3: `result.schema.json` carries the case `split`, and when `split` is `evaluation` it requires non-null `protocol_version`, `channel`, `condition`, and `comparison_superblock_id`; positive and negative fixtures cover both splits.
- [ ] W5-T1: `.env.example` lists only provider variable names with empty values, is read only by the outer runner, and is never read by CI or the mock provider.

### Gate 2 — end of week 7

Covers `W6-T1` through `W7-T5`.

- [ ] All four intrinsically safe tools and all ten deterministic task templates pass their required validators, including the four authorized high-risk clean templates.
- [ ] The 90-cell development grid completes, followed by one clean D0_BASELINE/D1_POLICY_GATE/D2_DATAMARKING smoke in one predeclared canonical adapter for each of the five task templates not represented by the development bases: 15 clean task-coverage smokes total, as defined in `SPEC.md` Section 9.
- [ ] Forced stop/resume creates no gaps, duplicates, or repeated tool effects.
- [ ] D1_POLICY_GATE and D2_DATAMARKING receive binary, outcome-blind readiness decisions.
- [ ] Context and conservative funded-budget checks support the proposed tier.

### Gate 3 — end of week 8

Covers `W8-T1` through `W8-T5`.

- [ ] The source-audited empirical prefix is selected deterministically, or a zero-trial `ENGINEERING` plan is frozen.
- [ ] Selected model/configuration or explicit no-model reason is recorded.
- [ ] `protocol/active.json`, applicable artifacts, schedule/validation plan, and hashes reconcile.
- [ ] No evaluation candidate has been exposed to a live model.

### Gate 4 — week 10 target

Covers `W9-T1` through `W10-T5`.

- [ ] Scheduled cells or validation checks complete under the frozen plan.
- [ ] Missingness, model comparability, hashes, resets, attempts, raw-to-endpoint recomputation, and generated outputs pass.
- [ ] Any repair follows the full symmetric-block rule before the absolute cutoff.

### Gate 5 and release — weeks 11 through 13

Covers `W11-T1` through `W13-T5`.

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
| Paper outline in Week 5; complete by release candidate | Assign an owner and satisfy the explicit Gate 5 and release comparison check above |
| Intended publication venue language | Release candidate | State only publicly or authoritatively verified facts |

## Maintenance rule

Update this file in the same pull request that changes slice status, owner, dependency, estimate, or cut state. When a pull-forward item lands early, mark it complete in its own later slice rather than recording extra credit in the week that did the work. Update `STATUS.md` as the dated weekly summary and link back here rather than redefining slice state. Put durable rationale in `docs/decisions/`; put post-freeze scientific deviations in `docs/protocol_deviations.md`. Never store individual performance commentary or private staffing deliberation here.
