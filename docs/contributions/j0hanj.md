# Contributor: j0hanj

- Public-name consent: Pending
- Preferred public name: Pending
- Component or research role: T2 corpus, sources, and C2/C3/C4 adapters
- Active interval: September 2026 onward

## Verifiable contributions

- Pull request/commit/artifact: [#12](https://github.com/marek-sm/CANARY/pull/12) (W5-T2)
  - Work performed: sourced and adapted `dev-001` from InjecAgent; rendered exact attack/clean twins through C2, C3, and C4 with round-trip and structural-diff tests.
  - Acceptance evidence: `tests/test_channels.py`; rendered hash manifest.
  - Independent reviewer: source review pending (`samsonchang2028`).
- Pull request/commit/artifact: W6-T2 pull request, see [the W6-T2 handoff](../W6_T2_HANDOFF.md)
  - Work performed: development bases `dev-002` to `dev-005` from InjecAgent and AgentDojo, rendered through C2/C3/C4; C1 control and demo source records; candidate ID derivation, exact-hash and near-duplicate detection, and ledger checks.
  - Acceptance evidence: `make corpus-check`; `tests/test_dev_corpus.py`; `tests/test_intake.py`.
  - Independent reviewer: `samsonchang2028` (review and Section 5 source review pending).
- Pull request/commit/artifact: review of [#28](https://github.com/marek-sm/CANARY/pull/28) (W6-T5, standing T2→T5 pair)
  - Work performed: ran the branch's tests and generated-example check; found and reproduced a display-label bug where an errored trial with unknown compromise got no `ERROR` label, and a stored `ERROR` label crashed replay; requested changes.
  - Acceptance evidence: GitHub review on #28.
  - Independent reviewer: Not applicable to this review activity.

## Approved public description

Pending.

## Final review

- Contributor reviewed this record: No
- Review date: Pending
