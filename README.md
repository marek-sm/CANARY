# CANARY: Prompt-Injection Measurement and Containment for Tool-Using LLM Agents

CANARY is a controlled engineering evaluation of indirect prompt injection in a deliberately vulnerable but intrinsically safe local tool-using LLM agent. It separates two questions that are often collapsed: what unsafe behavior the model proposes, and what effects the surrounding system permits. It is applied research, written for teams that choose prompt-injection safeguards for tool-using agents: for the same runs, it is designed to record what the model requested separately from what the system let happen, and what each safeguard costs in legitimate work ([`SPEC.md`](SPEC.md) Section 1, "Who CANARY is for"). `SPEC.md` Section 14 lists measurement practices such a team can apply to its own agent.

This is a Cal Poly SLO CS + AI Club project. `CANARY` in all caps refers to this project. CANARY builds on established work; its contribution is its scoped implementation, measurement design, execution, and findings.

## Current status

Current slice owners and states live in [`TASKS.md`](TASKS.md). The dated weekly gate, evidence, risk, and next-outcome summary lives in [`STATUS.md`](STATUS.md). Planned sample sizes, trial counts, result-sentence placeholders, and defense names are protocol commitments—not completed findings. Do not describe an experiment as run, a defense as effective, or an artifact as published until frozen evidence supports that statement.

Before work starts, each retained slice receives one accountable owner who commits to all of its acceptance checks. Review is independent verification, not deputy ownership; the full rule is in [`TASKS.md`](TASKS.md).

## Development setup

Requires Git, [uv](https://docs.astral.sh/uv/getting-started/installation/), and Python 3.11 (`SPEC.md` Section 4). `make` is optional.

```sh
git clone https://github.com/marek-sm/CANARY.git
cd CANARY
uv sync --locked                     # installs the exact uv.lock versions into .venv, including the dev group
uv run make test                     # no make: uv run pytest -q
uv run make trace                    # no make: uv run python -m runner.mock_slice
uv run make replay                   # no make: uv run python -m demo.replay
```

`uv sync --locked` stops with an error instead of re-resolving when `uv.lock` no longer matches `pyproject.toml`. After changing a dependency, run `uv lock` and commit `uv.lock` in the same pull request.

`make trace` runs one no-credit mock trial and writes it under `results/development/mock/`, which Git ignores.

`make replay` is the immediate read-only fallback. It schema-validates and
renders the staged W6-T3 mock development record without a key, network access,
or writes. The trace is explicitly labeled excluded and illustrative.

Every tool process runs in a sandbox ([decision 0023](docs/decisions/0023-tool-sandbox.md)); run `uv run make sandbox-check` once on a new machine and report a failure the same day. macOS needs nothing extra. Linux (x86_64 or aarch64) needs `bubblewrap` and, on Ubuntu 23.10 and later, `kernel.apparmor_restrict_unprivileged_userns=0` in a file under `/etc/sysctl.d`; on Windows, use WSL2 Ubuntu.

### Docker instructions

The image is the pinned CI environment (`SPEC.md` Section 4), and it runs only the tool-free mock trace:

```sh
docker compose run --rm mock         # builds the image, then prints the mock trace
```

That is the CI docker job (`docker build --tag canary:ci .`, then `docker run --rm --network none --read-only --tmpfs /app/results/development:uid=10001,gid=10001 --tmpfs /tmp canary:ci`) with the same flags, which `tests/test_compose.py` keeps equal. The image has no `bubblewrap` and no `make`, so every tool-running command (`make t1-smoke`, `make t1-suite`, `make grid-mock`, the paid paths) fails inside it with `SandboxUnavailable` and runs on the host under the tool sandbox. The official sweep runs on the project lead's machine outside this container, and its records carry a null `container_digest` ([decision 0025](docs/decisions/0025-full-study.md)). Building needs `ghcr.io` for the pinned `uv` layer. To check a built image's compose trace against the CI flags, run `CANARY_DOCKER_IMAGE=<tag> uv run pytest tests/test_compose.py`.

`make demo-example` regenerates the accessible W6 development-output example
from the real six-cell mock runner. `make demo-example-check` verifies that the
committed example is current. Both commands are offline and make no model call.

`make live-smoke` makes paid Anthropic calls: it runs one W5-T1 ticket trial on the decision 0010 development model, `claude-haiku-5-5`, and writes it under `results/development/live/`. It is run by hand, with the key in a local `.env` (one `ANTHROPIC_API_KEY=` line). `python -m runner.live_smoke --provider openai --env-file .env.openai` runs the same trial on the declared fallback, `gpt-6-luna`. It refuses when `CI` or any `ANTHROPIC_*` or `OPENAI_*` variable is set, and CI never runs it. Its read tool runs in the tool sandbox, and it is the one paid command that needs no paid-run record. It still refuses any uncommitted, untracked, or ignored hashed path, packages `uv.lock` doesn't pin, any model but the provider's decision 0010 model, and a missing spend ledger or cap, and it exits nonzero unless a `model_response` came back.

`make floor-count RUN=<run directory>` is the Gate 2 step's `SPEC.md` Section 10 development-floor count over one live development-grid run; add `OUT=<file>` to save the report. It reads records only, refuses mock-provider, evaluation, and other-run records and any record that disagrees with its trial's stored events, model responses, or cell files, and makes no provider call. Run it, `make gate2-budget`, and `make grid-verify` from the run's own commit: each rescores with that checkout's oracle, audit, and corpus, and a refusal from other code names the commit to use. These checks show the stored files agree with each other; only the published raw manifest anchors them from outside. Copy a run directory whole, because they also read its `env/` files and `canaries.json`. Like `make gate2-budget`, it also runs only from the scoring code that ran the grid, by the digest in the run's `code_provenance.jsonl`, and needs no paid-run record; a non-mock run with no provenance is refused, and a mismatch names the commit to run from.

`make grid-validate` checks that `protocol/development_grid_spec.json` expands to the Section 9 ninety-cell grid. `make grid-mock` runs that grid on the mock through tool-result delivery, so each configuration runs its real defense path, and `make grid-verify RUN=<run directory>` checks trial coverage, resume invariants, that every D1_POLICY_GATE dispatch has a gate decision and only D2_DATAMARKING delivers marked content, that each cell delivered its pinned resource, and that every stored result recomputes from its events, which replay against the stored model responses. `make grid-summary RUN=<run directory>` prints per-channel/configuration usage aggregates, counting trials whose usage is unknown apart rather than as zero, and counts D1_POLICY_GATE gate and audit disagreements. `python -m runner.grid_dev live --provider openai` runs `protocol/development_grid_spec_fallback.json`, the same grid on the declared fallback `gpt-6-luna`, which the paid-run record also hashes. It refuses until `FALLBACK_DECISION` in `runner/grid_dev.py` names the project lead's decision record ([decision 0010](docs/decisions/0010-anthropic-development-model.md) item 3). `make replay RUN=<events file, trial, or run directory>` renders recorded traces, every trial of a run directory, by default `make grid-mock`'s output, from the records alone. `make report` generates the estimand shells and the project lead's count tables (`make lead-outputs`: decision 0012's request-to-effect table and tool-name-only ablation, and decision 0028 item 4's count-only diagnostics, empty in `paper/generated/lead_outputs.md`), then runs `W8-T3`'s report code; until that merges it stops with a message naming `W8-T3`. `python -m analysis.lead_outputs RECORDS --out PATH` fills those tables from a final set of result records, either a raw sweep run, which it refuses until the run verifies complete because they stay hidden during the sweep (`SPEC.md` Section 9), or a released JSONL file; the count-only tables also need `--events RUN` for verified raw runs when RECORDS is a JSONL file ([decision 0036](docs/decisions/0036-lead-output-wiring.md)). `python -m runner.grid_dev live` opens only when `runner.paid_run` finds the project lead's paid-run record, `protocol/paid_run_record.json`, valid for this checkout's code and sandbox; `python -m runner.paid_run check` says whether a paid run may start here. Every paid trial, the live smoke's included, appends its priced usage to a ledger outside every checkout, and each refuses when spend plus one trial's bound exceeds the project lead's cap or trials would pass Section 9's 120: `python -m runner.spend_ledger init` creates the ledger, `set-cap USD` sets the cap, and `show` prints both. Reconcile with the provider's console, because a billed attempt that timed out records no usage. `make gate2-budget RUN=<run directory> BALANCE=<usd>` evaluates the Section 9 budget inequality on a live grid run at `F20`, or at `TIER=<row>` with `DEFENSE=<retained defense>` for a `ONE` row; it computes the reserve and C1 cost from the frozen price bound in `analysis/price_bound.py` (decision 0026) and counts the development trials already used from the spend ledger, so no typed number lowers the reserve, and a trial whose model response lacks recorded usage stops the evaluation rather than counting as free.

`python -m runner.sweep live --spec SPEC.json --protocol-version V` runs the official sweep after Gate 3 through the same runner path as the paid grid, with `split="evaluation"`, and `python -m runner.sweep verify RUN` checks it without printing any outcome; like `grid_dev live` and `coverage --live`, it needs `CANARY_PAID_RUN_ACK=1` and the paid-run record ([`docs/INTERFACES.md`](docs/INTERFACES.md)).

`make w7-t1-smoke` runs the 15 clean task-coverage cells and the C1 plumbing checks on the mock, and `make w7-t1-evidence` regenerates `docs/evidence/w7-t1` from them. `make coverage-verify RUN=<run directory>` checks a run's 15 cells the same way, and `make coverage-live` runs them on a real provider, by hand only, through the same paid-run gate. `make raw-manifest RUNS="<run directory> ..." OUT=<file>` writes the SHA-256 manifest of raw results and events files. It holds hashes only and joins the summary outputs under `docs/evidence/`; raw records never enter Git ([decision 0025](docs/decisions/0025-full-study.md) item 5).

## What CANARY is designed to measure

- Model-level unsafe proposals and exact-canary disclosure.
- Whether proposed actions were blocked, dispatched, and observed at a fictional sink.
- Clean-task utility under the same configurations.
- Paired behavior across structured tool output, retrieved local documents, and local fixture pages, when retained by the active tier.
- D1_POLICY_GATE external policy enforcement and D2_DATAMARKING datamarking at the layers each can actually affect.

The full scientific contract, permitted claims, tier arithmetic, and analysis plan are in [`SPEC.md`](SPEC.md).

## Safety boundary

The implementation must preserve these properties before any model-backed experiment runs:

- Tools operate only on fictional local fixtures.
- Email goes only to a per-trial local fake sink; the runner persists its receipt evidence, and no message is delivered over a network.
- URL fetching is restricted to an exact local fixture origin.
- Database access uses registered read-only queries.
- File access is confined to a temporary fixture root with traversal and symlink defenses.
- No public interface accepts arbitrary prompts, payloads, paths, URLs, or recipients.
- No real secret belongs in a prompt, fixture, trace, test, or release bundle.

See [`SECURITY.md`](SECURITY.md) for reporting and safe-testing rules.

## Documentation map

| File | Read it for |
|---|---|
| [`SPEC.md`](SPEC.md) | Authoritative scientific and release requirements |
| [`TASKS.md`](TASKS.md) | Work slices, owners, dependencies, gates, and current slice states |
| [`STATUS.md`](STATUS.md) | Dated weekly gate, evidence, public-risk, and next-outcome rollup |
| [`AGENTS.md`](AGENTS.md) | Ambient rules for human and automated coding work |
| [`CLAUDE.md`](CLAUDE.md) | Thin Claude-specific entry point to the same rules |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Contribution, review, testing, and protocol-change process |
| [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) | Professional conduct, privacy, consent, and reporting expectations |
| [`SECURITY.md`](SECURITY.md) | Vulnerability reporting and prohibited testing |
| [`.github/pull_request_template.md`](.github/pull_request_template.md) | Scope, safety, evidence, and documentation checks for each change |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Components, flow, and trust boundaries |
| [`docs/INTERFACES.md`](docs/INTERFACES.md) | Provider, tool, oracle, runner, and event boundaries |
| [`docs/DATA_CONTRACTS.md`](docs/DATA_CONTRACTS.md) | Schema ownership, identifiers, hashes, and null semantics |
| [`docs/DEFENSES_AND_POLICY.md`](docs/DEFENSES_AND_POLICY.md) | Frozen authorization, D1_POLICY_GATE, D2_DATAMARKING, and event-meaning contract |
| [`docs/DEMO_DESIGN.md`](docs/DEMO_DESIGN.md) | Terminal, replay, video, and accessibility rules |
| [`docs/DATA_RELEASE.md`](docs/DATA_RELEASE.md) | Public/private classification and release pipeline |
| [`paper/venue-checklists.md`](paper/venue-checklists.md) | Where each NeurIPS checklist item and IEEE paper section is answered, and what is still open for the paper leads |
| [`docs/decisions/README.md`](docs/decisions/README.md) | How to record durable decisions without rewriting history |
| [`docs/decisions/0001-document-authority.md`](docs/decisions/0001-document-authority.md) | Why this bounded document set has one scientific authority and no catch-all context file |
| [`docs/decisions/0002-single-owner-model.md`](docs/decisions/0002-single-owner-model.md) | Why every retained slice has one accountable owner and no standing personnel deputy |
| [`docs/decisions/0003-weekly-status-artifact.md`](docs/decisions/0003-weekly-status-artifact.md) | Why weekly status is a bounded summary rather than a second task tracker |
| [`docs/decisions/0004-week5-measurement-contract-clarifications.md`](docs/decisions/0004-week5-measurement-contract-clarifications.md) | How the week-5 measurement-contract lock resolves gaps and inconsistencies in `SPEC.md` |
| [`docs/decisions/0005-development-model-and-spend-cap.md`](docs/decisions/0005-development-model-and-spend-cap.md) | Why development first chose `gpt-6-luna` under a $10 prepaid cap, and what that means for drift; superseded in part by 0010 |
| [`docs/decisions/0006-one-vector-reviewer.md`](docs/decisions/0006-one-vector-reviewer.md) | Why each authorization and datamarking vector set has exactly one independent reviewer |
| [`docs/decisions/0007-gate1-corpus-rules-freeze.md`](docs/decisions/0007-gate1-corpus-rules-freeze.md) | How the corpus rules froze at Gate 1, what counts as a near-duplicate, and which templates the development bases represent |
| [`docs/decisions/0008-content-filter-refusals.md`](docs/decisions/0008-content-filter-refusals.md) | Why a provider content-filter refusal, from a finish reason or a listed HTTP 400 code, is a completed outcome that is never retried, and how it is scored |
| [`docs/decisions/0009-measurement-contract-lock.md`](docs/decisions/0009-measurement-contract-lock.md) | How the week-5 measurement contract locked at `1.0.0`: which `SPEC.md` text is hash-frozen, the one canonical JSON rule, the reason-code vocabulary, and the predeclared development-floor reporting rule |
| [`docs/decisions/0010-anthropic-development-model.md`](docs/decisions/0010-anthropic-development-model.md) | Why development uses `claude-haiku-5-5` with `gpt-6-luna` as the declared fallback, the $10-per-provider cap and credential rule, how a classifier refusal maps to a content-filter outcome, and why the loop follows a cut-off reply with a continuation turn |
| [`docs/decisions/0011-week8-replan.md`](docs/decisions/0011-week8-replan.md) | How Week 8 onward was re-planned after the recovery week: Gate 3 on October 28 with no backstop (re-dated by decision 0021), provisional `M10-ALL`, W10 folded into W9 and W11, the Gate 2 step slip rule (provisional geometry replaced by decision 0025), and lead-owned tool-result delivery |
| [`docs/decisions/0012-request-to-effect-table-and-tool-name-ablation.md`](docs/decisions/0012-request-to-effect-table-and-tool-name-ablation.md) | Why `SPEC.md` Section 10 predeclares a count-only request-to-effect table and a tool-name-only ablation of recorded D0_BASELINE requests, and why they must be on `main` before any paid call other than the live adapter check |
| [`docs/decisions/0013-rubric-framing.md`](docs/decisions/0013-rubric-framing.md) | Why `SPEC.md` Section 1 gains a problem statement and an overall research question with no prior-work or gap claim, why reference 15 stays unverified, and which rubric-driven proposals were not adopted |
| [`docs/decisions/0014-selection-prefixes-and-task-order.md`](docs/decisions/0014-selection-prefixes-and-task-order.md) | Why `SPEC.md` Section 5 builds only the prefixes a pool under 20 supports, how the selection order, `task_order`, and recheck sample are fixed in advance, and why this frozen-text change is protocol deviation DEV-0001 |
| [`docs/decisions/0015-cut-process-rules.md`](docs/decisions/0015-cut-process-rules.md) | Why post-freeze changes open their deviation entry first instead of a separate issue, why the weekly slice issues, the Monday `STATUS.md` update, and the 24-hour blocker action are gone, and which rules stay |
| [`docs/decisions/0016-practitioner-relevance.md`](docs/decisions/0016-practitioner-relevance.md) | Why `SPEC.md` Section 1 says who CANARY is for, what the pitch to leadership, sponsors, and recruiters may and may not say, and why it isn't a gate item or a decision priority |
| [`docs/decisions/0017-applied-purpose.md`](docs/decisions/0017-applied-purpose.md) | Why `SPEC.md` Section 0 makes usefulness to teams choosing safeguards CANARY's purpose and a tie-breaker that ranks nothing, why Section 14 adds a measurement checklist and a team-facing paper close, and when a gap sentence may be stated |
| [`docs/decisions/0018-c1-control-order.md`](docs/decisions/0018-c1-control-order.md) | Why a tier takes its C1 controls in a hash order over the records that pass source review, how a shortfall is counted, and why the set is fixed before any C1 control runs live; item 3's pilot example superseded by decision 0033 |
| [`docs/decisions/0019-audit-doc-reconciliations.md`](docs/decisions/0019-audit-doc-reconciliations.md) | How six of the seven documentation contradictions the October 17 audit found are settled, each by text that already states the rule, with no pinned text changed, and why the `CLAUDE.md` one waits |
| [`docs/decisions/0020-request-level-formula.md`](docs/decisions/0020-request-level-formula.md) | Why `SPEC.md` Section 7's `unauthorized_action_dispatched` and `unauthorized_action_effect` no longer name `request_evaluable`, so a dispatched request whose audit didn't complete gives null, as the scorer already does |
| [`docs/decisions/0021-two-week-shift.md`](docs/decisions/0021-two-week-shift.md) | Why every lattice week from W7 on moves two working weeks later, once, with Gate 3 on November 11 (November 14 under decision 0029), the data cutoff November 22, and the release freeze December 6 (noon November 29 under decision 0030), and the 48-hour turnaround rule it sets for every owner |
| [`docs/decisions/0022-start-on-merge.md`](docs/decisions/0022-start-on-merge.md) | Why each slice and gate step now starts the day its inputs are merged and reviewed (review wording amended by decision 0031) instead of on a fixed Monday or Saturday, why no slice crosses a gate before that gate runs, and why scheduled dates became latest dates while Gate 4 stays a target and the data cutoff stays fixed |
| [`docs/decisions/0023-tool-sandbox.md`](docs/decisions/0023-tool-sandbox.md) | Why every tool process, mock runs and CI included, runs in a deny-by-default OS sandbox that reaches only its trial's fixture socket and can't write evidence, why no paid call runs without the project lead's paid-run record, and why the paid commands run on the project lead's Mac |
| [`docs/decisions/0024-engineering-tier-input.md`](docs/decisions/0024-engineering-tier-input.md) | Superseded by decision 0025. Why the Gate 2 step was closed on October 31 and the November 1 tier input was `ENGINEERING` |
| [`docs/decisions/0025-full-study.md`](docs/decisions/0025-full-study.md) | Why decision 0024 was replaced a day later and the study targets `F20`, why that is a third move with no new evidence, why the Gate 1 cap is lifted after the fact, and the dated tripwires, new work, budget rule, and sweep conditions that follow |
| [`docs/decisions/0026-malformed-calls-and-price-bound.md`](docs/decisions/0026-malformed-calls-and-price-bound.md) | Why a malformed tool call stays a malformed outcome and an unauthorized request made in one goes uncounted, why replies are limited to one tool call, how the limit is reported, why the Section 7 and Section 9 wording change is protocol deviation DEV-0003, and how the maximum-token price bound is set |
| [`docs/decisions/0027-acceptance-by-work.md`](docs/decisions/0027-acceptance-by-work.md) | Why an owner accepts decision 0025's changed rows by a reply or by work on the slice, read at the tier input (November 11 under decision 0029), instead of replying to a Monday post |
| [`docs/decisions/0028-restore-strength.md`](docs/decisions/0028-restore-strength.md) | Which reductions were repaired, which stayed because reversing would make results worse, and the scorer's surface fixes (DEV-0004, `SPEC.md` v1.19.0) |
| [`docs/decisions/0029-gate-chain-shift.md`](docs/decisions/0029-gate-chain-shift.md) | Why the W7 slip moved the Gate 2 close to November 10, the tier input to November 11, and Gate 3 to November 14 to keep `F20`, what that costs, and why Demo Day re-planning waits for the confirmed date, replaced by decision 0030 (`SPEC.md` v1.20.0) |
| [`docs/decisions/0030-done-by-november-30.md`](docs/decisions/0030-done-by-november-30.md) | Why CANARY finishes by November 30: the club-week numbering correction, W12 through the release freeze moved seven days into the Thanksgiving break with `F20` and every earlier gate kept, the Section 13 rehearsal on the frozen tag, and the re-acceptance rule (`SPEC.md` v1.21.0); item 9's limit raise superseded by decision 0032 |
| [`docs/decisions/0031-merge-on-green.md`](docs/decisions/0031-merge-on-green.md) | Why pull requests merge once CI passes with no member review, how results and release code is reviewed on the lead side before every paid run, freeze, and gate step, why record and CI changes keep a second human through `.github/CODEOWNERS`, and what the paper must state about it (`SPEC.md` v1.22.0) |
| [`docs/decisions/0032-tier-input.md`](docs/decisions/0032-tier-input.md) | The November 11 tier input: `F20` on `claude-haiku-5-5`, the active-contributor count and what it rests on, capacity through November 13, the dated `W8-T2` and `W8-T4` fallbacks, and why the $10 limit stays |
| [`docs/decisions/0033-c1-pilot-example.md`](docs/decisions/0033-c1-pilot-example.md) | Why decision 0018's C1-cost pilot example is withdrawn: a pilot uses development material only, and the Gate 3 freeze fixes the C1 set before any C1 record runs live |
| [`docs/decisions/0034-c1-result-records.md`](docs/decisions/0034-c1-result-records.md) | Why the result and spend-ledger schemas move to 1.1.0 with an official C1 control record (DEV-0005, `SPEC.md` v1.23.0), what fixes a C1 record's form, why 1.0.0 records still validate, and what C1 work stays with `W8-T3` |
| [`docs/decisions/0036-lead-output-wiring.md`](docs/decisions/0036-lead-output-wiring.md) | Why decision 0012's two outputs and decision 0028 item 4's count-only outputs are generated by the lead's own module, `analysis/lead_outputs.py`, which `make report` runs, since `W8-T3`'s report code isn't on `main`; what it reads (a verified raw sweep run or the released JSONL) and who runs it, and the dated count-only release path |
| [`docs/decisions/0037-c1-authorization.md`](docs/decisions/0037-c1-authorization.md) | What is authorized in an official C1 control trial: one read-only reference policy generated from the frozen fixture, with no send, no secret read, and no grant; why C1 utility is a named not-applicable oracle; and what follows if the C1 executor misses November 13 (DEV-0006, `SPEC.md` v1.24.0) |
| [`docs/W6_T2_HANDOFF.md`](docs/W6_T2_HANDOFF.md) | The five development bases, C1/demo source records, candidate intake, and how to check them |
| [`docs/W7_T2_HANDOFF.md`](docs/W7_T2_HANDOFF.md) | The W7-T2 evaluation intake: every considered candidate, its source and status, and the selection script |
| [`docs/W7_T5_HANDOFF.md`](docs/W7_T5_HANDOFF.md) | Replay fallback, excluded demo staging, operator evidence, and paper-lead notes |
| [`docs/W8_T2_HANDOFF.md`](docs/W8_T2_HANDOFF.md) | W8-T2 corpus freeze: the 20 evaluation cases, the freeze manifest, the release-safe payload list, and draft corpus notes for the paper leads |
| [`docs/audits/2026-11-11-w8-t2-citation-audit.md`](docs/audits/2026-11-11-w8-t2-citation-audit.md) | The SPEC.md Section 15 corpus-freeze citation audit for the 20 frozen cases |
| [`docs/W8_T4_HANDOFF.md`](docs/W8_T4_HANDOFF.md) | W8-T4 defense freeze: the defense freeze manifest, the recheck, and draft threat-model, defense, event-semantics, and security-test notes for the paper leads |
| [`docs/audits/2026-11-13-w8-t4-recheck.md`](docs/audits/2026-11-13-w8-t4-recheck.md) | The SPEC.md Section 5 step 8 provenance and fixture-hash recheck of 4 sampled cases |
| [`docs/contributions/README.md`](docs/contributions/README.md) | Evidence and consent format for accurate public credit |
| [`docs/evidence/gate2-2026-11-10/`](docs/evidence/gate2-2026-11-10/README.md) | The Gate 2 step's record for November 10: the binary D1_POLICY_GATE and D2_DATAMARKING readiness decisions, the development-floor count, and the funded-budget check |
| [`docs/evidence/paid-run-2026-11-09/`](docs/evidence/paid-run-2026-11-09/README.md) | The paid summary for the November 9 development grid and coverage smokes (decision 0025 item 5): the grid summary, the smokes' check, the paid-run record's commit, and the raw-file manifest |
| [`docs/reviews/2026-11-09-paid-run.md`](docs/reviews/2026-11-09-paid-run.md) | The first lead-side review under decision 0031: #54, the results code merged with no member review, and decision 0028 item 8's scoring files, before the November 9 paid run |
| [`docs/reviews/2026-11-11-w7-t2-t5.md`](docs/reviews/2026-11-11-w7-t2-t5.md) | The second lead-side review under decision 0031: `W7-T2`'s selection code (#73) and `W7-T5`'s replay and demo staging (#66), before the tier input |
| [`docs/reviews/2026-11-13-w8-t2.md`](docs/reviews/2026-11-13-w8-t2.md) | The third lead-side review under decision 0031: `W8-T2`'s evaluation build, freeze, and release-list code (#93), before Gate 3 |
| [`docs/reviews/2026-11-13-c1-record.md`](docs/reviews/2026-11-13-c1-record.md) | The fourth lead-side review under decision 0031: the C1 result-schema record's results code (#92) |
| [`docs/protocol_deviations.md`](docs/protocol_deviations.md) | Append-only record of material post-freeze defects and responses |

## Reproduction contract

By release, a fresh clone must run `make report` and `make replay` without a model key or network in under five minutes. A credentialed development smoke test must be explicit and must never run in CI. Commands are added only when implemented and tested; this README does not advertise fictional setup steps.

## Claims boundary

CANARY does not claim to solve prompt injection, establish general security, rank models, or create a representative universal benchmark. Results, if an empirical tier runs, apply only to the frozen model/version, harness, source-derived corpus, retained adapters, task policies, and defenses. An `ENGINEERING` release reports instrument validation and no empirical defense estimate.

## License and citation

No reuse license is implied until a `LICENSE` file is committed. License selection is a tracked pre-release task. `CITATION.cff` is created only after the consented author list is stable.

### W5-T1 mock tool/task smoke

`uv run make t1-smoke` runs the fictional ticket through the safe file reader,
mock loop, durable evidence, deterministic utility validator, and replay.
See [the W5-T1 handoff](docs/W5_T1_HANDOFF.md) for acceptance commands and design
choices. It consumes the merged W5-T4 interfaces and W5-T3 schemas, frozen at the
measurement-contract lock. Independent authorization-audit integration remains
outstanding.

### W6-T1 safe-tool and task acceptance

`uv run make t1-suite` runs all ten deterministic templates through their 30
declared task/channel variants using only the mock provider. Each trial gets
verified fictional fixtures, a private page service on a per-trial Unix socket,
and an empty local email sink, with every tool process in the tool sandbox.
Outputs go to a fresh temporary directory. These are excluded engineering
checks; they do not count as the Week 7 paid development grid or coverage smokes. See the [W6-T1 handoff](docs/W6_T1_HANDOFF.md) for the registry,
tool boundaries, utility evidence, and independent-review requirements.

### W6-T2 development corpus check

`uv run make corpus-check` re-renders every development base and fails if a
committed fixture or hash drifted, then checks the candidate ledger against the
development, C1-control, and demo bases. See [the W6-T2 handoff](docs/W6_T2_HANDOFF.md).

### W7-T2 evaluation intake and selection

`uv run make select` prints the largest prefix the reviewed pool supports, the
nested smaller prefixes, each base's task, and the recheck samples. It reads only
candidate metadata, never a result. See [the W7-T2 handoff](docs/W7_T2_HANDOFF.md).
