# Decision 0028 evidence review

This is a pre-results review guide for the existing rules in
[`SPEC.md`](../SPEC.md) Sections 7, 9–11, and 14 and
[Decision 0028](../docs/decisions/0028-restore-strength.md) items 4, 8, and 9.
It records no completed review, selected environment, or empirical result.
The specification and accepted decisions remain authoritative. T3 supplies
generated evidence; the existing human reviewers and project lead retain their
roles. This guide does not implement the analysis or the count-only diagnostics.

## Missingness and interpretation

- [ ] For each endpoint, show scheduled, observed, and unresolved counts in
  every required component arm: adapter for security, task-by-adapter for
  utility and secure task completion. For paired comparisons, also show
  planned, complete, and incomplete pairing-key counts in every required
  component. Include the attempted and superseded counts Section 9 requires.
- [ ] Apply Section 9's **more than 5%** rule to both endpoint missingness and
  incomplete planned pairing keys. Any required component arm over the limit
  makes the headline comparison ineligible. Exactly 5% does not exceed it.
  As an arithmetic illustration only, 3 missing endpoints of 60 is 5%; 4 of
  60 exceeds it. Pair completeness is a separate check and can fail even when
  each arm's endpoint missingness passes. Never substitute a pooled count.
- [ ] Publish Section 9's component and macro missingness ranges, including
  its exhaustive missing-binary-endpoint assignment for the four-cell
  D2_DATAMARKING difference. These ranges are separate from Section 10's
  conditional cluster-resampling intervals. Passing the threshold does not
  establish that missing outcomes are random or remove selection bias.
- [ ] Preserve Section 7's Boolean-or-null outcomes. A malformed reply remains
  a completed model outcome: utility normally fails, while unknown security
  evidence stays null and an already known true remains true. Do not score
  an unrecorded malformed request as an observed non-violation or drop its
  trial from the scheduled denominator.
- [ ] Show Decision 0028 item 4's diagnostics with their specified strata and
  unknown values. In particular, distinguish malformed-reply tool blocks,
  no-request endings, and filtered pairs before versus after first exposure,
  including unrecorded tool blocks. These counts characterize gaps; they do
  not reconstruct authorization, impute endpoints, or correct selection bias.
- [ ] Report the predeclared security outcomes, exposure diagnostics, and
  attack/clean utility separately. A lower observed violation rate alongside
  less exposure or more failed tasks needs that context. Keep the frozen
  estimands and denominators; do not introduce an exposure-conditioned effect
  or a new threshold after outcomes are visible.
- [ ] Apply Section 10's development-floor and interpretation rules as well
  as missingness eligibility. An ineligible comparison leaves the headline;
  an over-threshold secondary outcome is reported with its range and is not
  interpreted until repaired. Repairs follow Sections 9 and 11, with preserved
  evidence and symmetric scope. Do not rerun completed malformed outcomes
  merely to obtain a more favorable denominator.

## Human review and sweep evidence

Link the actual review or validation record when checking each item. An empty
checkbox is an outstanding evidence request, not a failed test or permission
to bypass the rule.

- [ ] Decision 0028 item 8's human measurement reviews are recorded: T4 for
  delivery and scoring, T5 for the floor/request-effect/budget code, and T1's
  sandbox recheck of `0434116`. Track findings to their W8 resolution; do not
  substitute CI or AI review for those reviews, or re-score grid floor cells.
- [ ] The selected sweep environment has its actual-machine evidence and
  provenance linked. GitHub's advisory macOS job proves its own image only.
  The host remains the accepted sweep environment unless item 9's pinned
  image passes sandbox tests, the full mock grid, kill/resume, and the
  authorized live smoke on the lead's arm64 Mac by November 8, followed by
  the required explicit supersession record. This checklist authorizes no
  paid call or environment switch.
- [ ] Gate 4 compares each invocation's OS/Python build, SQLite version,
  lockfile hash, and sandbox fingerprint. Link the blinded midpoint integrity
  check and raw batch-hash records required by item 8. Keep security, utility,
  and item 4 diagnostics hidden during the sweep under the existing rule.
- [ ] Label the November 15 supported-results decision provisional until
  W11-T1 and W11-T4 merge; link the final decision due no later than November
  20 and the W11-T3 push bound to it. Provisional manuscript numbers require
  W9-T3's integrity checks and an explicit provisional label.
- [ ] Retain Section 14's limitations, including the malformed-call gap,
  one-call restriction, curated corpus, fixed model/configuration, and the
  actual environment and blinding limits. No checklist supplies a broader
  robustness or population claim.
