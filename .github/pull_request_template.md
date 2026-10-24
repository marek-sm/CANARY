# Pull request

## Scope

- Task slice:
- Accountable owner:
- Reviewer (consented public identifier):
- Frozen or claim-bearing artifact touched: No | Yes — `SPEC.md` Section 11 deviation entry:

## Change

What changed and why.

## Evidence

- Commands run:
- Observed results:

## Checks

- [ ] Safety: no real email, arbitrary network access, unrestricted filesystem/database access, shell tool, real credential, personal data, or public arbitrary-input surface was introduced; intrinsic capability checks stay active under D0_BASELINE, D1_POLICY_GATE, and D2_DATAMARKING; tests exercise denial, malformed input, and boundary escape where applicable.
- [ ] Measurement: requested, authorized, blocked, dispatched, execution, effect, sink, disclosure, utility, and infrastructure states stay distinct; unknown evidence stays `null`; no result or reported number was hand-edited; schema, identifier, version, hash, and raw-to-result checks pass where applicable.
- [ ] Release and claims: no private, provider-only, license-restricted, or unsanitized material enters public history; public wording claims no completed results, efficacy, representativeness, peer review, acceptance, or publication without evidence; D1_POLICY_GATE is described as enforcement and D2_DATAMARKING as behavioral guidance, with no bare condition aliases.
- [ ] Documentation: `SPEC.md` stays authoritative; every document that states a rule this pull request changes is updated in it and links to the canonical rule; `TASKS.md` status changed only after acceptance evidence existed; `STATUS.md` changed only if the dated weekly summary did.

## Open items

List unresolved items, or write `None`.
