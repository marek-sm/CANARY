# W9-T5 pre-results paper handoff

> **No results.** This handoff routes frozen technical evidence to the
> designated paper leads. It contains no empirical value, result sentence,
> defense-effect claim, or new scientific definition. `SPEC.md` and
> `protocol/active.json` remain authoritative.

## Active study identity

Gate 3 froze protocol `CANARY-2026-F20` at `F20` on November 15, 2026. The
protocol schedules 1,092 official trials: 1,080 primary-indirect trials and 12
C1 controls. These are planned counts, not completed results. The Gate 3 date
was missed on November 14 and moved to November 15 under decision 0040; the
paper must not present the original date as met.

Canonical sources:

- [`protocol/active.json`](../protocol/active.json) — selected tier, model,
  identifiers, schedule, hashes, and planned counts;
- [Gate 3 evidence](../docs/evidence/gate3-2026-11-15/README.md) — the recorded
  freeze checks and date boundary; and
- [`SPEC.md`](../SPEC.md) Sections 10, 11, and 14 — analysis, freeze, claims,
  limitations, and release rules.

## Component methods and related-work inputs

| Paper input | Frozen or reviewed source | What the paper leads may take from it | Required boundary |
|---|---|---|---|
| Agent, safe tools, tasks, utility oracles, and component identities | [`paper/w8-t1-method-notes.md`](w8-t1-method-notes.md), [`docs/W8_T1_FREEZE.md`](../docs/W8_T1_FREEZE.md) | Linked implementation evidence, deterministic task/oracle structure, and the component limitation | Mock and test evidence is engineering evidence, not model efficacy |
| Corpus, adapters, provenance, adaptation, citations, and related work | [`docs/W8_T2_HANDOFF.md`](../docs/W8_T2_HANDOFF.md), [`docs/audits/2026-11-11-w8-t2-citation-audit.md`](../docs/audits/2026-11-11-w8-t2-citation-audit.md) | Source-derived corpus method, C2/C3/C4 adapter description, verified citations, overlap descriptions, and the capability-coverage limitation | CANARY reuses payloads, not prior harnesses or results; make no novelty or market-gap claim |
| Frozen protocol, schemas, estimands, missingness, and report generation | [`protocol/active.json`](../protocol/active.json), [`paper/lead-inputs.md`](lead-inputs.md), [`paper/estimand_manifest.json`](estimand_manifest.json), [`analysis/report.py`](../analysis/report.py) | Exact protocol identity and links to generated, rather than retyped, output structures | Do not copy a planned count into prose as a completed outcome; do not hand-enter any result |
| Threat model, defenses, authorization, event semantics, and security-test evidence | [`docs/W8_T4_HANDOFF.md`](../docs/W8_T4_HANDOFF.md), [`docs/DEFENSES_AND_POLICY.md`](../docs/DEFENSES_AND_POLICY.md) | Canonical distinction between model behavior and system effects, plus the fixed-defense limitation | `D1_POLICY_GATE` is enforcement; `D2_DATAMARKING` is behavioral guidance |
| Accessible output and replay structure | [`docs/W8_T5_HANDOFF.md`](../docs/W8_T5_HANDOFF.md), [`paper/output_pipeline_freeze.json`](output_pipeline_freeze.json), [`docs/W7_T5_HANDOFF.md`](../docs/W7_T5_HANDOFF.md) | Generated table equivalents, caption/alt-text structure, and the read-only illustrative replay | A single replay is illustrative and excluded from every estimate |

## Pre-results assets ready for assembly

- [`outline.md`](outline.md) supplies the ten-section reading order and owner
  map.
- [`generated/estimand_shells.md`](generated/estimand_shells.md) and
  [`generated/report.md`](generated/report.md) are empty accessible structures;
  no value should be typed into either by hand.
- [`venue-checklists.md`](venue-checklists.md) routes accessibility and reporting
  checks without claiming a venue or review status.
- [`demo/caption_scaffold.md`](../demo/caption_scaffold.md) and
  [`demo/transcript_scaffold.md`](../demo/transcript_scaffold.md) reserve caption,
  alt-text, table-equivalent, and fallback language.
- [`demo/offline_media_plan.md`](../demo/offline_media_plan.md) defines the
  result-independent recording and verification plan without inventing a slot
  duration.

## Component limitations for the paper leads

1. Accessible structure can prevent some presentation barriers, but it does not
   validate a numerical result or its interpretation.
2. The terminal replay shows one excluded, fictional trace. It is not aggregate
   evidence and cannot establish defense efficacy.
3. The output pipeline detects drift in committed accessible artifacts; it does
   not replace source, statistical, claim, or human accessibility review.
4. The Demo Day slot and hardware remain unconfirmed, so this handoff sets no
   runtime and makes no live-first promise.

## T5 handoff to the designated paper leads

Use the linked sources rather than copying their rules into the manuscript.
Insert figures and values only from the final generated artifacts built from the
frozen sanitized bundle, after the project lead records which results are
supported. Preserve a table equivalent for every chart, repeat headers in long
tables, keep heading levels sequential, and never rely on color alone.
