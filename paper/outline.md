# CANARY Accessible Paper Outline Inputs

> **Pre-results structure only.** This file supplies hierarchy, input routing,
> and accessibility prompts for the designated paper leads. It contains no
> empirical result and does not authorize a claim.

## Technical-input owner map

| Paper section | Required technical input | Input owner(s) | T5 handoff |
|---|---|---|---|
| 1. Abstract | Active tier, approved claim, model/counts or `ENGINEERING` validation summary | Project lead and T3 | Accessible summary layout after approval |
| 2. Introduction and scoped contribution | Thesis, scope, permitted contribution language | Project lead | Heading and reading-order check |
| 3. Related work | Prior benchmarks, defenses, citations, and overlap statement | T2, with T4 defense input | Citation/figure accessibility check |
| 4. Threat model and safety boundary | Threat model, authority boundary, enforcement semantics | T4 and project lead | Safety-boundary diagram caption and alt text |
| 5. Corpus and adapters | Selection, provenance, adaptation, rejection ledger, C2/C3/C4 | T2 | Corpus-flow caption, alt text, and table formatting |
| 6. Agent, tasks/oracles, and defenses | Agent/tools/tasks/oracles; D1_POLICY_GATE and D2_DATAMARKING | T1 and T4 | Architecture caption, alt text, and table formatting |
| 7. Frozen protocol and analysis plan | Protocol, schemas, estimands, missingness, uncertainty | T3 and project lead | Accessible protocol/analysis tables |
| 8. Results or validation evidence | Generated frozen results or `ENGINEERING` validation only | T3 and project lead | Integrate generated figures and table equivalents without retyping values |
| 9. Limitations, ethics, and release safety | Required limitations, ethics, release boundary | Project lead with T1–T5 component inputs | Accessibility and release-safety review |
| 10. Reproducibility and contributions | Reproduction commands, manifest, hashes, consented contribution records | T3, T5, and all owners | Release links, contribution table, and document accessibility check |

## 1. Abstract

Input checklist:

- [ ] State the exact active tier.
- [ ] Use only the project-lead-approved problem/result sentence.
- [ ] At an empirical tier, insert generated model, case counts, supported primary effects/intervals, retained defenses, and the one-model limitation.
- [ ] At `ENGINEERING`, state that no official model experiment ran and summarize only frozen validation evidence.

## 2. Introduction and scoped contribution

Input checklist:

- [ ] Insert the project-lead-approved thesis and scoped contribution.
- [ ] Distinguish measurement, model resistance, and external enforcement.
- [ ] Avoid novelty, venue, peer-review, or publication claims without a public record.

## 3. Related work and explicit overlap

Input checklist:

- [ ] Receive the sourced related-work notes and citations from T2.
- [ ] State overlap with prior agent-security benchmarks and defenses explicitly.
- [ ] Keep case-level provenance separate from bibliography entries.

## 4. Threat model and real-world safety boundary

Input checklist:

- [ ] Receive the canonical threat/policy explanation from T4 and the project lead.
- [ ] Explain that D1_POLICY_GATE is enforcement and D2_DATAMARKING is behavioral guidance.
- [ ] Describe fictional local fixtures, fake sinks, and the absence of a public arbitrary-input surface.

## 5. Corpus selection, adaptation, rejection ledger, and crossed adapters

Input checklist:

- [ ] Receive source, eligibility, adaptation, rejection, deduplication, and audit evidence from T2.
- [ ] Identify C1 controls and crossed C2/C3/C4 adapters without treating renders as independent attacks.
- [ ] Link exact corpus records rather than retyping counts.

## 6. Agent, deterministic tasks/oracles, and defenses

Input checklist:

- [ ] Receive agent, tool, task, fixture, and utility-oracle notes from T1.
- [ ] Receive frozen defense and authorization semantics from T4.
- [ ] Preserve the distinction between unsafe model proposals and realized system effects.

## 7. Frozen protocol and analysis plan

Input checklist:

- [ ] Receive the frozen protocol, schemas, missingness rules, estimands, and analysis evidence from T3 and the project lead.
- [ ] State Boolean-or-null rules and the conditional cluster-resampling interval label exactly.
- [ ] Link `protocol/active.json` and generated analysis rather than duplicating authority.

## 8. Results or engineering-validation evidence

Input checklist:

- [ ] Insert only generated artifacts from the frozen sanitized bundle.
- [ ] At an empirical tier, cover model violations, system compromises, clean utility, background violations, uncertainty, failures, and disagreement.
- [ ] At `ENGINEERING`, show validation evidence and the explicit absence of empirical estimates.
- [ ] Keep every chart paired with meaningful alt text and a table equivalent.

## 9. Limitations, ethics, and release safety

Input checklist:

- [ ] Include every mandatory limitation from `SPEC.md` Section 14.
- [ ] Receive at least one component limitation from each portfolio owner.
- [ ] Describe sanitization, licensing, privacy, and release boundaries accurately.

## 10. Reproducibility and contribution statement

Input checklist:

- [ ] Provide no-key report/replay commands and frozen manifest/hash links.
- [ ] Link contribution statements backed by evidence and publication consent.
- [ ] Identify the immutable release tag/commit only after it exists.

## Accessibility handoff checklist

- [ ] Heading levels remain sequential and preserve logical reading order.
- [ ] Every chart has final alt text and a table equivalent.
- [ ] No chart is an image of text; color is never the only carrier of meaning.
- [ ] Tables repeat headers and avoid merged cells where practical.
- [ ] Links use descriptive text rather than “click here.”
- [ ] Captions and transcript are edited before release.
- [ ] The final PDF/document passes the current institutional accessibility checklist.
