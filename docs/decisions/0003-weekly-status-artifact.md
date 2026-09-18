# 0003: Bounded weekly status artifact

- Status: Accepted
- Date: 2026-09-14
- Decision scope: Governance
- Secondary scopes: Release, Tooling
- Related specification sections: Sections 0, 11, 12, and 17
- Supersedes: 0001, only its assignment of all mutable status to `TASKS.md`

## Context

The original operating plan used one repository `STATUS.md` for the internal artifact check, biweekly sprint review, and weekly leadership update. The initial public-document baseline instead assigned all mutable status to `TASKS.md` and omitted `STATUS.md`. Keeping only `TASKS.md` loses the dated gate, risk, external-ask, and next-seven-day summary; restoring the old status contract unchanged would create two authorities for work state.

## Options considered

1. Use only `TASKS.md`. This keeps one file but makes a detailed task plan serve as the recurring leadership and gate summary.
2. Make `STATUS.md` the sole status authority. This recreates the earlier workflow but duplicates or displaces slice ownership and acceptance state.
3. Keep current slice state in `TASKS.md` and add a bounded, dated `STATUS.md` that summarizes and links to canonical evidence.

## Decision

Use option 3. `TASKS.md` owns slice owners, dependencies, acceptance checks, and current slice states. `STATUS.md` owns one dated weekly rollup of the current gate and tier, evidence links, public risks and external asks, and next-seven-day outcomes. `protocol/active.json` continues to own the exact frozen protocol instance and official counts; `SPEC.md` continues to own scientific and release meaning.

`STATUS.md` never independently changes a slice state, protocol value, scientific definition, or frozen result. It links to the canonical source and states its update date. The same public-safe artifact may support the internal meeting, sprint review, and leadership check-in, avoiding duplicate reports. Private personnel explanations do not enter it.

## Consequences

- `STATUS.md` is committed in the pre-coding documentation baseline and linked from the README and authority map.
- A weekly summary can be pinned or shared without turning chat or presentation slides into another source of truth.
- `TASKS.md` remains the only mutable owner of slice-level state.
- A mismatch is corrected in `STATUS.md`; it never overrides the underlying authority.
- Post-freeze event metadata may be appended only under the bounded administrative-continuation rule in the specification.

## Verification

- S00 cannot pass unless `STATUS.md` and this record are committed.
- `README.md`, `AGENTS.md`, and `SPEC.md` route readers to the bounded status artifact.
- Every weekly entry links task, protocol, commit, or generated-evidence sources rather than copying their authority.
- Repository checks reject a `STATUS.md` claim that conflicts with `TASKS.md`, `protocol/active.json`, generated results, or `SPEC.md`.
