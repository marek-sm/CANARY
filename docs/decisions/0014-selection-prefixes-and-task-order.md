# 0014: Select from a pool under 20, fix the selection order, and set the task order

- Status: Accepted. Approved by the project lead on 2026-10-11; drafted with AI assistance.
- Date: 2026-10-11
- Decision scope: Protocol
- Secondary scopes: Governance
- Related specification sections: Sections 4, 5, 10, 11, and 12
- Supersedes: None

## Context

[Decision 0011](0011-week8-replan.md) set the provisional build geometry to `M10-ALL`, so `W7-T2`'s evaluation pool targets 14 candidates, at least 7 per primary goal. `SPEC.md` Section 5 step 8 builds nested 20-, 15-, 10-, 8-, and 6-base prefixes from 20 ordered bases, so it can't run on a pool of 14. Decision 0011 required a separate selection-prefix record before `W7-T2`'s pull request on October 15. Under the `TASKS.md` dependency rule, `W7-T2` can build to it only if it merges before the W7 Monday, October 12.

Steps 5–8 have been frozen since Gate 1 ([decision 0007](0007-gate1-corpus-rules-freeze.md)). Reviewing them for this change found three more gaps that would leave choices to the selection script's author while the candidates are visible, which decision 0007 rejected for near-duplicates:

- Step 5 ranks candidates within goal/family strata, so candidates of different families share ranks 1, 2, and so on. Step 8's "lexicographically earliest feasible vector of selection ranks" then doesn't name one set of bases.
- Step 8 requires a committed `task_order` but no rule or owner sets it. At an `M10` row its first six entries are the study's six tasks, and the development grid's paid calls run this week, so an order chosen later could be chosen with development results in view.
- Step 8 asks for a "committed seeded sample" for the provenance recheck but fixes no seed.

Verified constraints:

- No evaluation candidate exists on `main`, and no outcome of any kind has been recorded for one.
- The tier table fixes `M10` at 6 tasks, `L8` at 5, and `R6` at 4, which the first 10, 8, and 6 entries of step 8's index vector already give.
- Section 4 fixes the ten templates as three read/query, two local-web extraction, one cross-source comparison, and four legitimate high-risk. `W6-T1` owns their IDs and content; five of the IDs are in its unmerged pull request.
- Section 10's "Active-protocol manifest" also names the 20- and 15-base prefixes. It isn't hash-pinned, and neither is Section 12.

## Options considered

1. **Source 20 candidates anyway.** Rejected. `W7-T2` is already a 10-hour slice against one contributor-week of roughly three focused hours, and decision 0011 lowered the target for capacity.
2. **Let the script build only the 10-, 8-, and 6-base prefixes, and change nothing else.** Rejected. The rank, task-order, and seed gaps would remain, and the script's author would settle them in code.
3. **Build the largest prefix the pool supports, and close the three gaps in the same change.** Chosen. All of it edits the one block decision 0007 pinned, so it takes one hash update and one deviation entry.

## Decision

1. **Prefixes the pool supports (step 8).** The script builds the largest of the 20-, 15-, 10-, 8-, and 6-base prefixes for which a feasible vector exists, called `P`, and every smaller one.
   - It computes `P` when it runs over the reviewed pool in week 8, not when intake closes.
   - Larger prefixes aren't built, and their tiers can't be selected. If no size is feasible, there is no empirical prefix, and the Section 11 Gate 3 response applies.
   - Below 20, the search applies the step 8 minima to every prefix it builds, the per-source and per-family caps, and every per-case rule. It drops only the full tier's counts of goals, sources, families, legitimate high-risk cases, and bases per task.
   - The caps can bind only at 15 or 20 bases. An `M10` corpus is always the first ten bases of the `P`-length search.
   - With 14 candidates, at least 7 per goal, from at least three sources and three families, the search can build `P` = 10. That gives 6 tasks, 4 legitimate high-risk bases, and a 5/5 goal split, and the 8- and 6-base prefixes nest inside it.
2. **Selection order (steps 5 and 6).**
   - `selection_rank` stays the rank within the goal/family stratum, as Section 8's candidate record shows.
   - For selection, each primary goal's eligible candidates are ordered by ascending `SHA256("CANARY-2026|" + candidate_id)`, with ties broken by `candidate_id`.
   - The search vector is of goal positions. The alternation fixes each position's goal, so the earliest feasible vector names one set of bases.
   - A rejected candidate is preserved, and the search reruns without it.
3. **Relaxation (step 7).** Unchanged, except that "activate the next lower tier" becomes "move to the next smaller prefix size", since an `M10-ALL` to `M10-ONE` change keeps the same bases.
4. **`task_order` rule (step 8).**
   - The legitimate high-risk templates take indices 1, 4, 7, and 9.
   - Read/query templates take 2, 6, and 10; local-web extraction templates take 3 and 8; and cross-source comparison takes 5.
   - Within a category, the lowest `SHA256("CANARY-2026-task|" + template_id)` takes the lowest index.
   - Once committed, a template keeps its ID and index through any later fix, so a `W8-T1` defect fix can't reorder the tasks.
   - The project lead computes the order from `W6-T1`'s merged templates and commits it as lead scaffold before the date the paid-run condition holds is recorded, so it exists before any paid grid call. `W7-T2`'s script reads that file and is tested on synthetic IDs.
5. **Recheck sample (step 8).** The `ceil(0.20 × N)` retained cases with the lowest `SHA256("CANARY-2026-recheck|" + pool_hash + "|" + candidate_id)`.
   - `pool_hash` is the SHA-256 of the newline-joined, sorted `candidate_id` values of every record in `corpus/candidates.jsonl` once evaluation intake has closed.
   - It can't be computed while candidates are still being sourced, and `W8-T4` can compute it from work merged before its Monday.
6. **Other `SPEC.md` text.**
   - Section 10's "Active-protocol manifest" now refers to "the nested case prefixes built under Section 5 step 8".
   - Section 12's tier step 2 says no row may need more bases than the largest prefix built.
   - `SPEC.md` moves to v1.8.0.
7. **Change control.** Section 11 applies because decision 0007 froze this text:
   - an issue describing the change;
   - the version increment;
   - the new pin in `tests/test_corpus_rules_freeze.py`;
   - entry DEV-0001 in `docs/protocol_deviations.md`.

   No experiment ID or data exists, so no new ID is issued and nothing is rerun.
8. **`TASKS.md`.**
   - `W7-T2`'s row carries the rule, the three-source, three-family pool floor, and the `task_order` input.
   - Its `Depends` cell names the selection-prefix rule.
   - The lead-inputs table lists this record and the `task_order` file.
   - `W8-T2`'s `Depends` cell names the `task_order` file.

## Consequences

- A 14-candidate pool can reach an `M10` row only if it meets the 10-base minima: at least three sources and three families among the ten selected. A pool from two sources reaches at most an `L8` row.
- A pool of 15–19 can reach `P` = 15. The `M10` corpus is then the first ten bases of the 15-base search, which can differ from a 10-base search over the same pool. Either way, the choice depends only on candidate metadata, never on outcomes.
- The task order reads only template IDs and categories. An `M10` study measures two high-risk, two read/query, one local-web extraction, and one cross-source comparison template, whichever templates those are.
- `W7-T2`'s owner re-accepts the changed row in its W7 issue.
- `STATUS.md` keeps its dated October 11 text. The next rollup records DEV-0001.

## Verification

- `tests/test_corpus_rules_freeze.py` pins the new Section 5 text and checks that it defines the prefix, goal-order, task-order, and recheck rules.
- `tests/test_tasks_dependencies.py` and `tests/test_status_consistency.py` pass with the `TASKS.md` changes.
- The full no-credit suite passes with no provider call.
