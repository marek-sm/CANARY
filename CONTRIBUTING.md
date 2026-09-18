# Contributing to CANARY

CANARY welcomes work that strengthens its bounded measurement instrument. Contributions must preserve the safety, evidence, and claim rules in [`SPEC.md`](SPEC.md).

## Before contributing

Read, in order:

1. [`SPEC.md`](SPEC.md), especially the sections cited by your task;
2. [`AGENTS.md`](AGENTS.md);
3. the active slice in [`TASKS.md`](TASKS.md); and
4. the relevant guide under `docs/`.

Until a `LICENSE` and contribution terms are committed, external contributions are not accepted. Authorized project participants should confirm applicable club or university contribution terms with project leadership; this document does not create or alter ownership, and public availability alone does not grant reuse rights.

## Ownership commitment

Before a retained slice enters `IN PROGRESS`, it has exactly one accountable owner and no standing deputy. Accept a slice only after reviewing its full scope, dependencies, deadline, and acceptance evidence; acceptance means delivering every criterion. Reviewers and pairing partners support and verify the work but do not inherit it. Report emerging blockers early. If circumstances genuinely change capacity, the project records an explicit reassignment, tier, cut, or schedule decision before work proceeds; ownership never changes by implication.

## Change workflow

1. Start from an issue or `TASKS.md` slice with explicit acceptance evidence.
2. Keep each change small enough for one reviewer to understand.
3. Add or update tests with the implementation.
4. Record whether the change touches a frozen or claim-bearing artifact.
5. Open a pull request describing scope, safety impact, evidence, and documentation impact.
6. Obtain review from someone other than the primary implementer for oracle, corpus, defense, sanitizer, and release changes.

## Pull-request checklist

Use [`.github/pull_request_template.md`](.github/pull_request_template.md) as the single current per-change checklist. This guide owns the contribution workflow; the template owns the prompts applied to each pull request. Update the template rather than maintaining a second checklist here.

## Corpus contributions

A corpus item requires a stable source record, human opener, different human reviewer, license or permission decision, original/adapted hashes, adaptation notes, deterministic oracle, clean twin, and one ledger status. Never add a payload solely because it produces a useful or dramatic outcome. Evaluation candidates receive no live-model exposure before freeze.

## Scientific and frozen changes

Before freeze, a semantic change must update `SPEC.md`, schemas, tests, and relevant guides together. After freeze, material changes follow Section 11 of `SPEC.md`: preserve old evidence, increment the protocol, create a new experiment or validation identity, rerun symmetrically, and add a dated `docs/protocol_deviations.md` entry.

## Results and claims

Generated data is authoritative over narrative summaries. Pull requests must not claim that D1_POLICY_GATE changed model behavior, that D2_DATAMARKING enforces authorization, that a small curated corpus is representative, or that a report is peer reviewed or published without supporting records.
