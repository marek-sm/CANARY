# 0001: Public document authority

- Status: Accepted
- Date: 2026-09-13
- Decision scope: Governance
- Secondary scopes: Architecture, Protocol, Release, Tooling
- Related specification sections: Sections 0, 11, and 17
- Supersedes: None

Metadata correction (2026-09-14): the original pipe-delimited scope menu was normalized into primary and secondary fields; the decision itself was not rewritten. Decision 0003 later supersedes only this record's assignment of all mutable status to `TASKS.md`.

## Context

CANARY needs enough public documentation to guide implementation, preserve scientific meaning, and support safe collaboration. It also needs to avoid duplicated rules, stale summaries, private organizational history, and a catch-all document whose authority is unclear.

## Options considered

1. Keep only one large specification. This minimizes file count but gives changing work status, implementation guidance, release handling, and contribution process no appropriate home.
2. Keep the specification plus a broad background/context document. This preserves more narrative but risks duplicated authority and mixing public technical rationale with private or temporary organizational material.
3. Keep one authoritative scientific specification plus narrowly scoped companion documents. This adds a bounded document set while giving each changing or implementation-facing fact one clear home.

## Decision

Use option 3. `SPEC.md` owns scientific and release meaning. Versioned schemas own exact serialization while remaining consistent with the specification. `protocol/active.json` owns the exact frozen instance. `TASKS.md` owns mutable work sequencing and status. `AGENTS.md` owns shared coding-session instructions, and `CLAUDE.md` is only a thin entry point to those instructions. Narrow guides explain architecture, interfaces, data contracts, demo design, and data release without redefining their governing semantics.

No catch-all context document is part of the public repository. Durable technical rationale belongs in numbered decision records; post-freeze scientific defects belong in the protocol-deviation log; completed contribution evidence belongs in contribution records; and private organizational or personnel material remains outside public Git history.

## Consequences

- A conflict cannot be resolved by choosing the most convenient document; the affected work or release blocks until the canonical artifacts are reconciled.
- Companion documents must link or defer to their canonical owner instead of copying protocol rules as independent authority.
- Mutable status can change without silently changing the experiment.
- Additional documents require a distinct durable purpose; otherwise they are not added.
- Fact-dependent files such as the license, citation metadata, schemas, active protocol, CI, environment example, and dependency lock are created only when their contents can be accurate.

## Verification

- The Section 17 authority table assigns one purpose and explicit non-purpose to every companion document.
- `README.md` links the public document set.
- `TASKS.md` makes the documentation baseline the pre-coding slice.
- Internal Markdown links and the absence of a catch-all context-file reference are checked before the documentation baseline is marked complete.
