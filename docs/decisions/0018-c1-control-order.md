# 0018: Fix the order in which tiers take C1 controls

- Status: Accepted. Approved by the project lead on 2026-10-16; drafted with AI assistance.
- Date: 2026-10-16
- Decision scope: Protocol
- Secondary scopes: None
- Related specification sections: Sections 3, 5, 11, and 12
- Supersedes: None

## Context

`SPEC.md` Section 12 runs four C1 controls at `F20` and `R15`, three at every `M10` row, and two at `L8` and `R6`. Nothing says which ones a smaller tier keeps. The provisional build geometry is `M10-ALL` ([decision 0011](0011-week8-replan.md)), and `W6-T2`'s pull request [#34](https://github.com/marek-sm/CANARY/pull/34) adds four C1 source records, so some rule has to pick three. Left open, someone would pick them later, possibly after C1 results exist. [Decision 0014](0014-selection-prefixes-and-task-order.md) closed the same kind of gap for evaluation bases.

Verified constraints:

- No C1 control has been built or run, and #34 hasn't had its `SPEC.md` Section 5 source review, which the project lead does under the October 15 T3 capacity reassignment in `TASKS.md`.
- Two of the four records are weak:
  - `c1-001` is a `secret_disclosure` payload asking for "saved addresses", which is neither canary location in Section 3.
  - `c1-004` forwards an email the four-tool surface has no way to read.
  
  The source review decides whether each is fixed or rejected.
- A record's `candidate_id` comes from its source and original payload (Section 5 step 2), so fixing an adaptation doesn't change it.
- Section 12 isn't pinned ([decision 0009](0009-measurement-contract-lock.md) item 1). Section 3, which says "Four C1 examples run", and Section 5 step 4 are pinned. Section 5's units table already lets a lower tier replace the C1 count with its Section 12 row.

## Options considered

1. **Pick three by hand now.** Rejected:
   - It picks before the source review settles which records are eligible.
   - It leaves a shortfall undefined.
   - The person who picks would also pass or fail the records.
   - [Decision 0007](0007-gate1-corpus-rules-freeze.md) treats a human pick made while candidates are visible as outcome-based selection.
2. **A mechanical order over the records that pass source review, with the removal path closed before any C1 outcome.** Chosen. It reuses Section 5 step 8's goal alternation and selection hash, so no new rule is invented.

## Decision

1. **Order.**
   - Take every C1 record that passed its Section 5 source review.
   - Alternate primary goals, beginning with `secret_disclosure`.
   - Within each goal, order records by ascending `SHA256("CANARY-2026|" + candidate_id)`, breaking any tie by `candidate_id`.
   - A tier with k C1 controls uses the first k.
2. **Shortfall.**
   - If fewer than k records are eligible, an `M10`, `L8`, or `R6` row uses all of them, and its official trial count falls by 3 per missing control. `protocol/active.json` records the count at Gate 3.
   - At `F20` or `R15`, a shortfall needs Section 11 change control, because pinned Section 3 says four run.
3. **Eligibility closes before any C1 outcome.**
   - The source review of #34 sets eligibility. A record that fails gets a Section 5 status and reason, so nothing is dropped silently.
   - After that, a record leaves only with a Section 5 status found by building or mock-checking it, never because of a live result.
   - That path closes at the first live call on any C1 record, such as a C1-cost pilot under Section 9. After that, the set is fixed.
4. **Reserved bases.**
   - All four C1 candidates stay reserved bases for Section 5 step 4's duplicate rule, whatever their status and whether or not a tier runs them: `06f559e4921d4e9df589`, `3b09691424519c6194fc`, `b8185dcef6f61e976329`, and `bc268463fabd23eb78f0`.
   - This reads pinned step 4's "C1-control base" conservatively and changes no frozen text.
5. **`W7-T1` builds every eligible C1 control at every tier,** as `TASKS.md`'s scope note and T1's capacity row already said. The tier decides only which ones run officially.
6. **Where it lives.** `SPEC.md` Section 12 carries items 1–3, and `SPEC.md` moves to v1.12.0. `TASKS.md` changes the `W7-T1` row to match item 5, says `W6-T2` creates four C1 source records, and says the provisional geometry sets the official C1 count.

With the IDs in #34 at `4e7c769`:

| Goal | Order |
|---|---|
| `secret_disclosure` | `c1-002` (`b6922d80…`), then `c1-001` (`f2408ef6…`) |
| `unauthorized_action` | `c1-003` (`4d457558…`), then `c1-004` (`e9850b02…`) |

*Corrected October 18 under [decision 0019](0019-audit-doc-reconciliations.md): `c1-003`'s prefix was misprinted as `4d455758…`. The order didn't change.*

- Full order: `c1-002`, `c1-003`, `c1-001`, `c1-004`.
- An `M10` row takes `c1-002`, `c1-003`, and `c1-001` if all four pass, or `c1-002`, `c1-003`, and `c1-004` if `c1-001` fails.
- `L8` and `R6` take `c1-002` and `c1-003` either way.

## Consequences

- No pinned text changes, so Section 11 change control and a deviation entry aren't needed. A shortfall at `F20` or `R15` would need them.
- Which C1 controls run depends only on source records and their review, never on a result.
- `W7-T1`'s owner re-accepts the changed row by replying to the Monday post.
- `W8-T3`'s `protocol/active.json` generator applies the order and the shortfall count from `SPEC.md` Section 12. This record has to merge before W8's Monday, October 19, for `W8-T3` to use it.
- `STATUS.md` keeps its dated October 11 text. The October 18 rollup cites v1.12.0 and this record.

## Verification

- `tests/test_contract_lock.py` and `tests/test_corpus_rules_freeze.py` pass unchanged, which shows no pinned text moved.
- `tests/test_tasks_dependencies.py` and `tests/test_status_consistency.py` pass with the `TASKS.md` and `SPEC.md` changes.
- The full no-credit suite passes with no provider call.
