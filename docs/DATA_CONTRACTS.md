# CANARY Data-Contract Guide

This is a readable index, not a duplicate schema. `SPEC.md` Section 8 owns field meaning; versioned JSON Schemas in `schemas/` own the exact serialized structure; `protocol/active.json` binds the versions and hashes used by one experiment or validation release.

## Required schema families

| Planned schema | Represents | Primary invariants |
|---|---|---|
| `base_case.schema.json` | Accepted development/evaluation/demo case | Immutable case ID, source provenance, goal/family, canonical payload hash, task/oracle references, adapter fixtures, clean twin, license decision |
| `candidate.schema.json` | Accepted or rejected source candidate | Deterministic candidate ID, source record, selection stratum/rank, adaptation record, one explicit ledger status and reason |
| `event.schema.json` | Append-only provider, model, authorization, dispatch, tool, effect, sink, and final-output event | Globally unique hierarchical IDs, durable ordering, raw evidence reference, component versions |
| `result.schema.json` | One logical empirical trial and derived endpoints | Exact schedule keys, requested/resolved model, canaries or references, Boolean-or-null facts, utility, infrastructure status, attempts |
| `engineering_validation.schema.json` | One frozen `ENGINEERING` check | Validation ID, check ID, deterministic evidence, Boolean-or-null `passed`, failure/indeterminate reasons, versions and hashes; no empirical model estimate |
| `active_protocol.schema.json` | Machine-readable active tier | Active-contributor count, exact tier, ordered cases, channels, conditions, configurations, repeats, counts, seeds, hashes, cutoffs, model or null-with-reason fields |
| `manifest.schema.json` | Raw, sanitized, validation, report, or release bundle | File paths, sizes, hashes, producing commit/configuration, bundle type, sanitizer version |

Names may change before the first schema commit, but the families and semantics may not disappear. Once referenced by frozen data, filenames and schema IDs are versioned rather than silently repurposed.

## Identifier rules

- `candidate_id` follows the deterministic formula in `SPEC.md` Section 5.
- `base_case_id` is immutable and is the clustering/resampling unit.
- `logical_trial_id` uniquely binds experiment, case, channel, condition, configuration, repeat, model, and protocol.
- `model_call_id` adds the agent step to the full logical-trial ID.
- `attempt_id` adds the attempt index to the full model-call ID.
- Empirical experiment IDs and `ENGINEERING` validation IDs occupy distinct namespaces.
- A repair or rerun receives a new experiment/validation ID; it never overwrites prior evidence.
- The configuration enum uses exactly `D0_BASELINE`, `D1_POLICY_GATE`, and `D2_DATAMARKING`; bare numeric aliases are invalid for this project.

## Null and applicability rules

Security and evidence fields use three values:

- `true`: evidence establishes the event;
- `false`: evidence establishes that the event did not occur; and
- `null`: required evidence is missing, corrupt, unevaluable, or genuinely unavailable.

Not-applicable and unknown are distinguished by surrounding disposition fields. For example, a durably blocked request has `dispatched = false`, `execution_succeeded = null`, and `effect_observed = false`; a dispatched request with lost postcondition evidence has `effect_observed = null`.

## Canonicalization and hashes

- Canonical JSON uses one committed normalization and serialization rule before hashing.
- Payload records retain canonical, rendered, pre-D2_DATAMARKING, and post-D2_DATAMARKING hashes as applicable.
- Fixture hashes are verified before paired trials.
- The sanitizer produces a new bundle manifest but may not alter scored fields.
- All public tables and claims bind to the sanitized-bundle manifest, active protocol, and generating commit.

## Version namespaces

CANARY carries several independent version identifiers. They advance on different triggers and are never aligned to one another; equal or differing numbers across namespaces imply nothing.

| Namespace | Where it lives | Advances when |
|---|---|---|
| Specification version | `SPEC.md` header | The specification document is re-baselined; after freeze, only through `SPEC.md` Section 11 |
| `protocol_version` | Result records and `protocol/active.json` | The claim-bearing protocol changes; a material change after freeze requires the Section 11 increment |
| `schema_version` and schema `$id` | `schemas/*.schema.json` and every record they validate | A schema's serialized structure changes; schemas stay `0.x` until the measurement-contract lock and become `1.0.0` as part of that lock |
| Package version | `pyproject.toml` | A tagged software release is cut; it does not track the specification or protocol |
| Component versions | Constants such as `RUNNER_VERSION`, `LOOP_VERSION`, and `PROVIDER_ADAPTER_VERSION`, recorded in events and results | That component's behavior changes (see `docs/INTERFACES.md`); `-v0` and `placeholder` values mark pre-freeze or mock implementations |

Version-shaped values inside `SPEC.md` example records illustrate post-freeze data and are not the repository's current versions. Never bump a version only to make it match another namespace: every recorded version is evidence of what produced a record.

## Evolution rules

Before measurement-contract lock, an additive field is allowed only when its semantics, schema, fixtures, and tests land together. After lock, reinterpretation, type changes, new required fields, changed nullability, changed identifiers, or changed endpoint derivations are material protocol changes.

Implementations may add diagnostic fields, but they may not remove required evidence, collapse event states, or serialize unknown as false.

## Schema acceptance checklist

- [ ] Positive and negative fixtures validate as expected.
- [ ] Unknown, false, and not-applicable cases are independently exercised.
- [ ] Duplicate global IDs fail validation.
- [ ] Every content-addressed reference resolves and matches its hash.
- [ ] Extra diagnostic fields cannot alter frozen derived endpoints.
- [ ] Raw-to-result recomputation produces identical Boolean-or-null values.
- [ ] `ENGINEERING` records cannot carry an official model estimate or empirical interval.
- [ ] Active-tier arithmetic matches the named row in `SPEC.md` Section 12.
