# 0006: One independent reviewer for authorization and datamarking vectors

- Status: Accepted. Approved by the project lead on 2026-09-26; drafted with AI assistance.
- Date: 2026-09-26
- Decision scope: Protocol
- Secondary scopes: Governance
- Related specification sections: Sections 6 and 11
- Supersedes: None

## Context

`SPEC.md` v1.1.0 Section 6 required one contributor to author the allow/deny golden vectors and a different contributor to review them. When three or more contributors are active, a second independent reviewer also had to check them. Six contributors are active (`STATUS.md`), so that rule required two reviewers. `docs/DEFENSES_AND_POLICY.md` applied the same rule to the datamarking vectors. `review_complete` in `oracles/authorization/conformance.py` enforced it with `REQUIRED_REVIEWERS = 2`.

On 2026-09-26 the project lead set the working rule that every slice has exactly one reviewer. Both W5-T4 vector sets record one reviewer (`reviewed_by: ["Chace"]`). Under v1.1.0, no differential result over them could be trusted until a second reviewer signed.

The change comes before the week-5 measurement-contract lock and before any freeze. Under `AGENTS.md` change classification it therefore needs every affected authority and test updated together, not a protocol-deviation record.

## Options considered

1. **Keep two reviewers as an exception.** This keeps the extra check on vector expectations, but breaks the one-reviewer rule and needs a second reviewer before W7-T4's differential tests can be trusted.
2. **Require exactly one independent reviewer.** This matches the one-reviewer rule and the `R6` arrangement Section 6 already accepts for two active contributors. It drops the extra check.

## Decision

Use option 2. A vector set has exactly one reviewer, who is not its author, at every contributor count. That review is enough for its differential results to be trusted.

- `SPEC.md` Section 6 now says so, and the specification moves to v1.2.0.
- `schemas/authorization_vectors.schema.json` limits `reviewed_by` to one entry.
- `REQUIRED_REVIEWERS` is 1.

## Consequences

- Independence rests on two things: a reviewer who is not the author, and the gate and audit evaluators, which are implemented independently and checked against each other by differential tests. Any gate/scorer disagreement still invalidates the affected block.
- Residual risk: suppose the author and the single reviewer both miss a wrong expected outcome, and both evaluators agree with it. Then no check catches it. A second reviewer would have been one more chance to catch it. The threat-model and defense notes (W8-T4 and W11-T4) should state this as a limitation.
- The W5-T4 vector sets meet the rule now, so W7-T4 needs no additional reviewer.
- Recording a second reviewer is now a schema validation error, not extra assurance.

## Verification

- `tests/test_defense_contracts.py::test_review_complete_needs_one_independent_reviewer` checks the three cases: no reviewer and author-only fail; one independent reviewer passes.
- `tests/test_defense_contracts.py::test_vector_schema_rejects_a_second_reviewer` checks that the schema rejects a second reviewer.
- `tests/test_defense_contracts.py::test_vector_reviewers_are_independent` checks both committed vector sets: at most one reviewer, never the author.
