# 0002: Single-owner completion model

- Status: Accepted
- Date: 2026-09-14
- Decision scope: Governance
- Secondary scopes: Release, Tooling
- Related specification sections: Sections 11, 12, 13, and 17
- Supersedes: None

Metadata correction (2026-09-14): the original pipe-delimited scope menu was normalized into primary and secondary fields; the decision itself was not rewritten.

## Context

The pre-public planning baseline assigned deputies and required personnel-handoff notes for critical components. That model could make delivery ownership appear shared or imply that an unfinished obligation would automatically pass to someone else. The team instead wants each contributor to begin with a complete, reviewable commitment and for everyone to know who owns delivery.

This decision concerns people and work ownership. It does not remove technical reliability measures for provider, network, media, or device failures, and it does not remove independent review requirements.

## Options considered

1. Keep a primary owner plus a standing deputy for each component. This supplies a named understudy but divides attention and can blur who is accountable for completion.
2. Use shared ownership for critical work. This increases nominal coverage but makes it easier for each person to assume that someone else will close the remaining work.
3. Give every retained slice one accountable owner, keep review independent, and respond to a real capacity change through an explicit project decision.

## Decision

Use option 3. Before a retained slice enters `IN PROGRESS`, it has exactly one accountable owner. Before accepting it, that contributor reviews the full scope, dependencies, deadline, and acceptance evidence. Acceptance means owning every criterion through verified completion, not merely contributing an attempt.

There are no standing deputies, backup owners, or required personnel-handoff notes. Reviewers and pairing partners support and verify the work but do not inherit delivery responsibility. The owner raises risks and blockers early and drives each one to an explicit resolution. If capacity actually changes, the project records a visible reassignment, tier, cut, or schedule decision before work proceeds; ownership never changes by implication.

Replay, offline media, and a second tested device remain technical contingencies. They protect the demonstration from system failures and are not substitutes for an accountable person.

## Consequences

- Every active obligation has one unambiguous completion owner.
- Contributors must assess the whole commitment before accepting work.
- Independent review remains mandatory where the specification requires it, without creating shared delivery ownership.
- The repository no longer contains `docs/handoffs/` or a deputy map.
- A real change in availability becomes an explicit scope or ownership decision instead of an assumed rescue by another contributor.
- Confidence comes from explicit acceptance, visible ownership, and completion evidence while any real availability change remains governed and visible.

## Verification

- `TASKS.md` records exactly one accountable owner for every active slice before it becomes `IN PROGRESS`.
- Pull requests name that owner and link evidence for every acceptance condition.
- Repository checks find no standing deputy, backup-owner, or personnel-handoff requirement.
- Demo checks retain replay, offline-media, and second-device coverage without assigning a backup operator.
