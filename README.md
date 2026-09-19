# CANARY: Prompt-Injection Measurement and Containment for Tool-Using LLM Agents

CANARY is a controlled engineering evaluation of indirect prompt injection in a deliberately vulnerable but intrinsically safe local tool-using LLM agent. It separates two questions that are often collapsed: what unsafe behavior the model proposes, and what effects the surrounding system permits.

This is a Cal Poly SLO CS + AI Club project. `CANARY` in all caps refers to this project. CANARY builds on established work; its contribution is its scoped implementation, measurement design, execution, and findings.

## Current status

Current slice owners and states live in [`TASKS.md`](TASKS.md). The dated weekly gate, evidence, risk, and next-outcome summary lives in [`STATUS.md`](STATUS.md). Planned sample sizes, trial counts, result-sentence placeholders, and defense names are protocol commitments—not completed findings. Do not describe an experiment as run, a defense as effective, or an artifact as published until frozen evidence supports that statement.

Before work starts, each retained slice receives one accountable owner who commits to all of its acceptance checks. Review is independent verification, not deputy ownership; the full rule is in [`TASKS.md`](TASKS.md).

## Development setup

Requires Git and Python 3.11 (`SPEC.md` Section 4). `make` is optional.

```sh
git clone https://github.com/marek-sm/CANARY.git
cd CANARY
python3 -m venv .venv                # Windows: py -3.11 -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install jsonschema pytest        # TEMPORARY WORKAROUND, see note below
make test                            # no make: python -m pytest -q
make trace                           # no make: python -m runner.mock_slice
```

`make trace` runs one no-credit mock trial and writes it under `results/development/mock/`, which Git ignores.
d

> **Temporary workaround:** `pip install -e ".[dev]"` should be the install command, but it currently fails because setuptools' automatic package discovery finds multiple top-level packages. Until `pyproject.toml` is fixed (see the open packaging issue), install the two dependencies directly, as CI does. Delete this note and the workaround line in the PR that fixes packaging.

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

| File                                                                                             | Read it for                                                                              |
| ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| [`SPEC.md`](SPEC.md)                                                                             | Authoritative scientific and release requirements                                        |
| [`TASKS.md`](TASKS.md)                                                                           | Work slices, owners, dependencies, gates, and current slice states                       |
| [`STATUS.md`](STATUS.md)                                                                         | Dated weekly gate, evidence, public-risk, and next-outcome rollup                        |
| [`AGENTS.md`](AGENTS.md)                                                                         | Ambient rules for human and automated coding work                                        |
| [`CLAUDE.md`](CLAUDE.md)                                                                         | Thin Claude-specific entry point to the same rules                                       |
| [`CONTRIBUTING.md`](CONTRIBUTING.md)                                                             | Contribution, review, testing, and protocol-change process                               |
| [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)                                                       | Professional conduct, privacy, consent, and reporting expectations                       |
| [`SECURITY.md`](SECURITY.md)                                                                     | Vulnerability reporting and prohibited testing                                           |
| [`.github/pull_request_template.md`](.github/pull_request_template.md)                           | Scope, safety, evidence, and documentation checks for each change                        |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)                                                   | Components, flow, and trust boundaries                                                   |
| [`docs/INTERFACES.md`](docs/INTERFACES.md)                                                       | Provider, tool, oracle, runner, and event boundaries                                     |
| [`docs/DATA_CONTRACTS.md`](docs/DATA_CONTRACTS.md)                                               | Schema ownership, identifiers, hashes, and null semantics                                |
| [`docs/DEMO_DESIGN.md`](docs/DEMO_DESIGN.md)                                                     | Terminal, replay, video, and accessibility rules                                         |
| [`docs/DATA_RELEASE.md`](docs/DATA_RELEASE.md)                                                   | Public/private classification and release pipeline                                       |
| [`docs/decisions/README.md`](docs/decisions/README.md)                                           | How to record durable decisions without rewriting history                                |
| [`docs/decisions/0001-document-authority.md`](docs/decisions/0001-document-authority.md)         | Why this bounded document set has one scientific authority and no catch-all context file |
| [`docs/decisions/0002-single-owner-model.md`](docs/decisions/0002-single-owner-model.md)         | Why every retained slice has one accountable owner and no standing personnel deputy      |
| [`docs/decisions/0003-weekly-status-artifact.md`](docs/decisions/0003-weekly-status-artifact.md) | Why weekly status is a bounded summary rather than a second task tracker                 |
| [`docs/contributions/README.md`](docs/contributions/README.md)                                   | Evidence and consent format for accurate public credit                                   |
| [`docs/protocol_deviations.md`](docs/protocol_deviations.md)                                     | Append-only record of material post-freeze defects and responses                         |

## Reproduction contract

By release, a fresh clone must run `make report` and `make replay` without a model key or network in under five minutes. A credentialed development smoke test must be explicit and must never run in CI. Commands are added only when implemented and tested; this README does not advertise fictional setup steps.

## Claims boundary

CANARY does not claim to solve prompt injection, establish general security, rank models, or create a representative universal benchmark. Results, if an empirical tier runs, apply only to the frozen model/version, harness, source-derived corpus, retained adapters, task policies, and defenses. An `ENGINEERING` release reports instrument validation and no empirical defense estimate.

## License and citation

No reuse license is implied until a `LICENSE` file is committed. License selection is a tracked pre-release task. `CITATION.cff` is created only after the consented author list is stable.
