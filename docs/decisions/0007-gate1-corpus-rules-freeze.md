# 0007: Freeze the corpus rules at Gate 1, define near-duplicates, and assign development-base tasks

- Status: Proposed. Drafted with AI assistance for the project lead on 2026-09-27.
- Date: 2026-09-27
- Decision scope: Protocol
- Secondary scopes: None
- Related specification sections: Sections 4, 5, 9, and 11
- Supersedes: None

## Context

`SPEC.md` Section 5 step 1 requires the eligibility, exact quota, family and source cap, task-assignment, deduplication, adaptation, and relaxation rules to freeze in week 5, before any evaluation candidate is selected. `TASKS.md` makes that freeze part of the project lead's Gate 1 lock. It also lists the development-base task assignment as a lead input due September 27, which W6-T1 and W6-T2 both build against from Monday.

Checking the rules for the freeze found one gap. Step 4 says to deduplicate "near-identical templates," and the composition rules forbid "near-duplicate" payloads, but nothing defines either term. W6-T2 starts near-duplicate detection on Monday. Without a definition, the rule would be decided in code, one case at a time, while candidates are visible.

## Options considered

1. **Leave near-duplicates to W6-T2's judgment.** Rejected: a human call made while candidates are visible is the outcome-based selection Section 5 forbids.
2. **Deduplicate exact hashes only.** Rejected: this misses mechanical variants of one payload, such as a different recipient, path, or number, which the permitted adaptations themselves create.
3. **Write a fixed, mechanical definition into `SPEC.md` before any candidate is ranked.** Chosen.

## Decision

1. **Freeze.** The frozen corpus rules are the `SPEC.md` v1.3.0 Section 5 text from `### Corpus composition` up to `### Crossed indirect-delivery design`:
   - the composition quotas, minima, and caps;
   - source eligibility and human review;
   - the eight selection steps, including task assignment and the relaxation order;
   - adaptation fidelity;
   - the candidate status list.

   That text's SHA-256 at the freeze is `ed11c65c87bd0f0ab4f7fc2e0bc3652fd3061eb1967f56ab569509fa6afc48b0`. Any later change to it follows `SPEC.md` Section 11 change control.
2. **Near-duplicates.** `SPEC.md` Section 5 step 4 now defines near-identical payloads:
   - Two canonical payloads are near-identical when their deduplication keys are equal, or when the Jaccard similarity of their word 3-gram sets is at least 0.8.
   - The key is the payload after NFKC normalization and case folding, with every URL, email address, file path, and run of digits replaced by one fixed placeholder per kind, punctuation removed, and whitespace collapsed.
   - In each duplicate group, the candidate with the lowest `SHA256("CANARY-2026|" + candidate_id)` stays eligible, and every other member is recorded as `duplicate`, naming the kept candidate.
   - A candidate near-identical to a development, C1-control, or demo base is recorded as `duplicate` and never enters evaluation, so development tuning cannot leak into the evaluation set.

   `SPEC.md` moves to v1.3.0.
3. **Development-base task assignment.** `corpus/development/task-assignment.json` assigns the five development bases to five of the ten Section 4 templates, with template IDs and per-channel resources:

   | Base | Template ID | Category |
   |---|---|---|
   | `dev-001` | `review-field-lookup` | Read/query |
   | `dev-002` | `order-status-extract` | Local-web extraction |
   | `dev-003` | `supplier-quote-compare` | Cross-source comparison |
   | `dev-004` | `shipping-notice-email` | Legitimate high-risk |
   | `dev-005` | `meeting-confirm-email` | Legitimate high-risk |

   `dev-001` keeps the resources already committed in its record. The other five templates (two read/query, one local-web extraction, and two legitimate high-risk) are W6-T1's to name and build and W7-T1's coverage smokes. This split puts every template category in the 90-cell development grid. It also puts two high-risk templates there, so D1_POLICY_GATE readiness can show that authorized email still goes through.

## Consequences

- The 0.8 threshold and the placeholder list are choices, not derived values. They are fixed before any candidate is ranked, so they cannot be tuned to outcomes.
- A near-duplicate of a development base is lost to evaluation even when it would otherwise be selected. That is intended.
- W6-T1 builds the five development templates to these IDs and owns their prompt wording, validators, fixtures, authorization policies, and versions. W6-T2 names the template IDs in `dev-002` to `dev-005` and fills `dev-001`'s `task` once W6-T1's task registry lands.
- The evaluation task assignment is unaffected: the Section 5 step 8 script still freezes it in week 8.

## Verification

- `tests/test_corpus_rules_freeze.py` recomputes the SHA-256 of the frozen Section 5 text and fails if it changed.
- `tests/test_task_assignment.py` checks five distinct templates, category counts that fit Section 4's ten, per-channel tools and resources, local fixture origins, relative read paths, and that `dev-001` matches its committed record.
