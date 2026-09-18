# Pull request

## Scope

- Task slice or issue:
- Accountable owner:
- Specification sections:
- Active tier impact: None | Compatible | Tier decision required
- Frozen or claim-bearing artifact touched: No | Yes — explain below

## Change

Describe the smallest coherent behavior changed and why it is needed.

## Safety boundary

- [ ] No real email, arbitrary network access, unrestricted filesystem/database access, shell tool, real credential, personal data, or public arbitrary-input surface was introduced.
- [ ] Intrinsic capability checks remain active under D0_BASELINE, D1_POLICY_GATE, and D2_DATAMARKING.
- [ ] Tests exercise denial, malformed input, and boundary escape where applicable.

## Evidence

- [ ] The accountable owner has satisfied every acceptance condition; review has not transferred delivery ownership.
- Commands run:
- Observed results:
- Fixtures, records, or generated artifacts:
- Independent reviewer required: No | Yes — name a consented public identifier

## Measurement and data contracts

- [ ] Requested, authorized, blocked, dispatched, execution, effect, sink, disclosure, utility, and infrastructure states remain distinct.
- [ ] Unknown evidence remains `null`; no result or reported number was hand-edited.
- [ ] Schema, identifier, version, hash, and raw-to-result checks pass where applicable.
- [ ] D1_POLICY_GATE is described as enforcement and D2_DATAMARKING as behavioral guidance; ambiguous bare condition aliases were not introduced.

## Documentation and release

- [ ] `SPEC.md` remains authoritative and every affected companion document links to the canonical rule.
- [ ] `TASKS.md` status changed only after acceptance evidence existed.
- [ ] `STATUS.md` was updated only if the dated weekly summary changed and does not redefine task or protocol state.
- [ ] Any material post-freeze change followed Section 11 and added a protocol-deviation record.
- [ ] No private, provider-only, license-restricted, or unsanitized material enters public history.
- [ ] Public wording does not claim completed results, efficacy, representativeness, peer review, acceptance, or publication without evidence.

## Remaining risks or decisions

List unresolved items, or write `None`.