# CANARY Decision Records

Use this directory for durable technical or protocol rationale that would otherwise be lost in chat, issues, or pull requests. Decision records explain why; they do not override `SPEC.md`, schemas, or `protocol/active.json`.

## What deserves a record

- architecture or dependency choices with meaningful alternatives;
- provider/model selection criteria application;
- an interface or canonicalization choice;
- a defense implementation interpretation;
- a corpus-selection or license-policy interpretation;
- a selected tier or outcome-blind scope reduction;
- a public naming/disambiguation decision;
- a governance or document-authority choice that affects how the team executes work; and
- a superseding decision that changes earlier rationale.

Routine coding details, personal assignments, individual performance, private conversations, and temporary status do not belong here. Current slice state belongs in `TASKS.md`; the dated weekly rollup belongs in `STATUS.md`; post-freeze scientific deviations belong in `docs/protocol_deviations.md`.

## Filename and lifecycle

Use `NNNN-short-title.md`, beginning with `0001`. A record has one status:

- `Proposed`
- `Accepted`
- `Superseded by NNNN`
- `Rejected`

Never edit an accepted record to make history appear cleaner. Correct typographical errors transparently; otherwise add a new record that supersedes it.

Choose exactly one primary decision scope: `Architecture`, `Protocol`, `Release`, `Tooling`, or `Governance`. Put any genuinely relevant additional categories in `Secondary scopes`; do not leave the template menu in a completed record. A later record may supersede a precisely named part of an earlier decision while leaving the rest accepted.

## Template

```markdown
# NNNN: Short decision title

- Status: Proposed
- Date: YYYY-MM-DD
- Decision scope: [choose one: Architecture / Protocol / Release / Tooling / Governance]
- Secondary scopes: [optional; otherwise None]
- Related specification sections: Section X
- Supersedes: None

## Context

What durable technical problem requires a decision? State verified constraints and distinguish assumptions.

## Options considered

1. Option and principal tradeoff.
2. Option and principal tradeoff.

## Decision

State the chosen option precisely.

## Consequences

List operational, safety, measurement, reproducibility, and maintenance consequences.

## Verification

Identify tests, evidence, or a future checkpoint that will confirm the decision works as intended.
```

## Initial records

[`0001-document-authority.md`](0001-document-authority.md) records the initial authority model adopted before coding. [`0002-single-owner-model.md`](0002-single-owner-model.md) records the one-owner commitment model and removal of standing personnel deputies. [`0003-weekly-status-artifact.md`](0003-weekly-status-artifact.md) supersedes only 0001's assignment of all mutable status to `TASKS.md` and establishes the bounded weekly `STATUS.md` role. Record the final public-name/disambiguation choice when that choice is confirmed. Do not create speculative records for decisions that have not actually been made.
