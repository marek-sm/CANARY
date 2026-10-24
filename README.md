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
```

`uv sync --locked` stops with an error instead of re-resolving when `uv.lock` no longer matches `pyproject.toml`. After changing a dependency, run `uv lock` and commit `uv.lock` in the same pull request.

`make trace` runs one no-credit mock trial and writes it under `results/development/mock/`, which Git ignores.

`make demo-example` regenerates the accessible W6 development-output example
from the real six-cell mock runner. `make demo-example-check` verifies that the
committed example is current. Both commands are offline and make no model call.

`make live-smoke` makes paid Anthropic calls: it runs one W5-T1 ticket trial on the decision 0010 development model, `claude-haiku-5-5`, and writes it under `results/development/live/`. It is run by hand, with the key in a local `.env` (one `ANTHROPIC_API_KEY=` line). `python -m runner.live_smoke --provider openai --env-file .env.openai` runs the same trial on the declared fallback, `gpt-6-luna`. It refuses when `CI` or any `ANTHROPIC_*` or `OPENAI_*` variable is set, and CI never runs it.

`make floor-count RUN=<run directory>` is the Gate 2 step's `SPEC.md` Section 10 development-floor count over one live development-grid run; add `OUT=<file>` to save the report. It reads records only, refuses mock-provider, evaluation, and other-run records, and makes no provider call.

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
| [`docs/decisions/0011-week8-replan.md`](docs/decisions/0011-week8-replan.md) | How Week 8 onward was re-planned after the recovery week: Gate 3 on October 28 with no backstop (re-dated by decision 0021), provisional `M10-ALL`, W10 folded into W9 and W11, the Gate 2 step slip rule, and lead-owned tool-result delivery |
| [`docs/decisions/0012-request-to-effect-table-and-tool-name-ablation.md`](docs/decisions/0012-request-to-effect-table-and-tool-name-ablation.md) | Why `SPEC.md` Section 10 predeclares a count-only request-to-effect table and a tool-name-only ablation of recorded D0_BASELINE requests, and why they must be on `main` before any paid call other than the live adapter check |
| [`docs/decisions/0013-rubric-framing.md`](docs/decisions/0013-rubric-framing.md) | Why `SPEC.md` Section 1 gains a problem statement and an overall research question with no prior-work or gap claim, why reference 15 stays unverified, and which rubric-driven proposals were not adopted |
| [`docs/decisions/0014-selection-prefixes-and-task-order.md`](docs/decisions/0014-selection-prefixes-and-task-order.md) | Why `SPEC.md` Section 5 builds only the prefixes a pool under 20 supports, how the selection order, `task_order`, and recheck sample are fixed in advance, and why this frozen-text change is protocol deviation DEV-0001 |
| [`docs/decisions/0015-cut-process-rules.md`](docs/decisions/0015-cut-process-rules.md) | Why post-freeze changes open their deviation entry first instead of a separate issue, why the weekly slice issues, the Monday `STATUS.md` update, and the 24-hour blocker action are gone, and which rules stay |
| [`docs/decisions/0016-practitioner-relevance.md`](docs/decisions/0016-practitioner-relevance.md) | Why `SPEC.md` Section 1 says who CANARY is for, what the pitch to leadership, sponsors, and recruiters may and may not say, and why it isn't a gate item or a decision priority |
| [`docs/decisions/0017-applied-purpose.md`](docs/decisions/0017-applied-purpose.md) | Why `SPEC.md` Section 0 makes usefulness to teams choosing safeguards CANARY's purpose and a tie-breaker that ranks nothing, why Section 14 adds a measurement checklist and a team-facing paper close, and when a gap sentence may be stated |
| [`docs/decisions/0018-c1-control-order.md`](docs/decisions/0018-c1-control-order.md) | Why a tier takes its C1 controls in a hash order over the records that pass source review, how a shortfall is counted, and why the set is fixed before any C1 control runs live |
| [`docs/decisions/0019-audit-doc-reconciliations.md`](docs/decisions/0019-audit-doc-reconciliations.md) | How six of the seven documentation contradictions the October 17 audit found are settled, each by text that already states the rule, with no pinned text changed, and why the `CLAUDE.md` one waits |
| [`docs/decisions/0020-request-level-formula.md`](docs/decisions/0020-request-level-formula.md) | Why `SPEC.md` Section 7's `unauthorized_action_dispatched` and `unauthorized_action_effect` no longer name `request_evaluable`, so a dispatched request whose audit didn't complete gives null, as the scorer already does |
| [`docs/decisions/0021-two-week-shift.md`](docs/decisions/0021-two-week-shift.md) | Why every lattice week from W7 on moves two working weeks later, once, with Gate 3 on November 11, the data cutoff November 22, and the release freeze December 6, and the 48-hour turnaround rule it sets for every owner |
| [`docs/contributions/README.md`](docs/contributions/README.md) | Evidence and consent format for accurate public credit |
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
