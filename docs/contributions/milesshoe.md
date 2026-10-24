# Contributor: milesshoe

- Public-name consent: No — use contributor identifier `milesshoe`.
- Component or research role: T5 demo, replay, accessibility, and release support
- Active interval: September–October 2026

## Verifiable contributions

- Pull request/commit/artifact: [CANARY PR #28](https://github.com/marek-sm/CANARY/pull/28),
  merge commit `60c705c`
  - Work performed: kept terminal replay tied to generated W5-T3 event records;
    added known-trace coverage for display labels and three-valued security
    intersections; generated the first accessible development-output example;
    and added caption and transcript scaffolding.
  - Acceptance evidence: GitHub CI passed; the independent reviewer reproduced
    the corrected infrastructure-error behavior and reported all 1,113 tests
    passing before approval.
  - Independent reviewer: `j0hanj`
- Pull request/commit/artifact: review of
  [CANARY PR #31](https://github.com/marek-sm/CANARY/pull/31)
  - Work performed: reviewed the resumable runner and independent authorization
    audit against the current specification, including path containment,
    interruption recovery, configuration labeling, and preservation of tool-event
    evidence.
  - Acceptance evidence: focused 49-test suite and complete 421-test suite passed
    against current `main`; the GitHub review recorded the remaining required
    changes. PR #31 was later closed and its work continued in PR #47.
  - Independent reviewer: Not applicable to this review activity.
- Pull request/commit/artifact: review of
  [CANARY PR #47](https://github.com/marek-sm/CANARY/pull/47)
  - Work performed: re-reviewed the resumable runner and confirmed that its four
    earlier findings were addressed; reproduced a remaining identity bug where
    resume could silently accept a completed result from the wrong experiment or
    model as the requested logical trial.
  - Acceptance evidence: focused execution, audit, and schedule suite passed (81
    tests); complete suite passed (1,304 tests); the GitHub review records the
    reproduction and requested a wrong-logical-trial regression test.
  - Independent reviewer: Not applicable to this review activity.
- Pull request/commit/artifact: review of
  [CANARY PR #49](https://github.com/marek-sm/CANARY/pull/49)
  - Work performed: reviewed the development-grid orchestration, resume checks,
    usage summary, budget scaffold, defense labeling, and paid-run guard against
    `SPEC.md` and `TASKS.md`; identified that unwired baseline behavior could be
    stored as `D1_POLICY_GATE` and that an environment flag alone could unlock
    the live path before the recorded paid-run condition held.
  - Acceptance evidence: `make grid-check` passed (20 tests plus the 90-cell
    fixture preflight); complete suite passed (1,324 tests); the GitHub review
    records both blocking findings and requests negative regression tests.
  - Independent reviewer: Not applicable to this review activity.

## Approved public description

`milesshoe` contributes to T5 demo, replay, accessibility, and peer review; no
result or defense-efficacy claim is made by this record.

## Final review

- Contributor reviewed this record: Yes
- Review date: 2026-10-18
