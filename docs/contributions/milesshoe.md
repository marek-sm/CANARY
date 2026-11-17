# Contributor: milesshoe

- Public-name consent: No — use contributor identifier `milesshoe`.
- Publication consent: Yes — this evidence-backed record and its approved
  public description may appear in CANARY's public release under `milesshoe`.
- Preferred attribution: `milesshoe`; do not publish a legal or personal name.
- Component or research role: T5 demo, replay, accessibility, and release support
- Active interval: September–November 2026

## Verifiable contributions

- Pull request/commit/artifact: [CANARY PR #28](https://github.com/marek-sm/CANARY/pull/28),
  merge commit `60c705c`
  - Work performed: kept terminal replay tied to generated event records; added
    known-trace coverage for display labels and three-valued security
    intersections; generated the first accessible development-output example;
    and added caption and transcript scaffolding.
  - Acceptance evidence: GitHub CI passed; the independent reviewer reproduced
    the corrected infrastructure-error behavior and reported all 1,113 tests
    passing before approval.
  - Independent reviewer: `j0hanj`
- Pull request/commit/artifact: [CANARY PR #66](https://github.com/marek-sm/CANARY/pull/66),
  owner commit `64884e6`
  - Work performed: added the one-command read-only replay fallback, staged the
    excluded demo case through C2/C3/C4 attack and clean fixtures, and added the
    plain-language replay explanation while preserving exact stored outcomes.
  - Acceptance evidence: two no-notes replay starts produced identical output;
    the pull request records 1,781 passing tests and the corpus, demo-example,
    paper-shell, and replay checks.
  - Independent reviewer: `j0hanj`; code-owner approval and the final README-only
    conflict resolution were supplied by the project lead.
- Pull request/commit/artifact: [CANARY PR #109](https://github.com/marek-sm/CANARY/pull/109),
  owner commit `d3b1910`
  - Work performed: froze the accessible pre-results output pipeline against the
    estimand manifest, deterministic shell renderer, generated table equivalents,
    and focused test evidence.
  - Acceptance evidence: output-freeze, engineering-report, lead-output, and
    report checks passed on the merged tree; the focused suite passed 10 tests.
  - Independent reviewer: lead-side review under decision 0031.
- Pull request/commit/artifact: reviews of
  [PR #31](https://github.com/marek-sm/CANARY/pull/31),
  [PR #47](https://github.com/marek-sm/CANARY/pull/47), and
  [PR #49](https://github.com/marek-sm/CANARY/pull/49)
  - Work performed: reviewed interruption recovery, logical-trial identity,
    evidence preservation, development-grid orchestration, defense labeling,
    and paid-run gating; recorded reproducible blocking findings and rechecked
    fixes.
  - Acceptance evidence: the GitHub reviews link the focused and complete test
    runs and the requested negative regression coverage.
  - Independent reviewer: Not applicable to review activity.

## Approved public description

`milesshoe` contributes CANARY's terminal demo and replay, accessible output
structure, and release support, and reviewed runner and grid safety behavior.
This statement makes no result or defense-efficacy claim.

## Final review

- Contributor reviewed the original record through PR #49: Yes
- Original review date: 2026-10-18
- Contributor review of the PR #66, PR #109, and W9-T5 additions: Pending
