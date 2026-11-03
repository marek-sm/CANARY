# 0027: Owners accept decision 0025's rows by a reply or by working on them

- Status: Accepted. Approved by the project lead on 2026-11-03; drafted with AI assistance.
- Date: 2026-11-03
- Decision scope: Governance
- Secondary scopes: Protocol
- Related specification sections: Sections 12 and 17
- Supersedes:
  - Decision 0025 item 9's last bullet, item 10's "Count" bullet, and item 12's "re-accepts by reply".
  - Decision 0024 item 5's "Re-acceptance" bullet, as decision 0025 item 2 carries it forward.
  - Decision 0015 item 2's re-acceptance by replying to that week's post, for the rows in item 1.
  - Decision 0015's Monday team-channel post, and decision 0022 item 8's restatement of it, for November 2 only.

## Context

Decision 0025 item 9 has owners re-accept its rows by replying to the Monday, November 2 post by the end of Tuesday, November 3, and leaves a row `BLOCKED` otherwise. Item 10 counts only owners who re-accept toward the tier's headcount ceiling.

On November 2 the project lead told each owner what's on them in a direct message instead of a public post, and asked for no reply. As written, every row would go `BLOCKED` on November 3 and the count could fall, with nobody having been asked. No text sets the form of acceptance; `SPEC.md` Section 17 sets what it requires.

## Options considered

1. **Ask each owner to reply after all.** Rejected by the project lead.
2. **Treat the October 26 re-acceptances as covering decision 0025.** Rejected. Decision 0025 changed rows, including `W7-T2`'s target, so the earlier acceptance doesn't cover them.
3. **Count a reply or new work on the slice as acceptance, read at the tier input.** Chosen.

## Decision

1. **What counts.** Decision 0025's rows are `W7-T1` through `W7-T5`, `W8-T1` through `W8-T5`, and `W9-T3`. An owner accepts a row by replying to the project lead, or by a commit or pull request on that slice's work that the owner authored after their November 2 direct message. Either one commits the owner to the whole row under `SPEC.md` Section 17: they've reviewed its scope, dependencies, deadline, and acceptance evidence, and they own every criterion. A review of someone else's slice doesn't count. No reply is required.
2. **When it's read.** The project lead reads it on Sunday, November 8, for the tier input (decision 0025 item 10). Until its item 3 date, no row is `BLOCKED` for lack of acceptance. A slice stays `BLOCKED` on its producers as before.
3. **The count.** The tier input counts the project lead and each owner who has accepted at least one row under item 1, which is a "defined current responsibility" under `SPEC.md` Section 12. A count of 5 sets the ceiling at `R15`. A row not accepted by November 8, or by its latest open date if that's later, is `BLOCKED` until its owner accepts or a visible reassignment, tier, cut, or schedule decision is recorded (decision 0021 item 11). A later acceptance clears the row and doesn't raise a tier input already recorded.
4. **`W9-T3`.** Its owner accepts the same way. If the tier input is `ENGINEERING`, owners accept the rows decision 0024 item 5 changes the same way, after that input.
5. **The November 2 post.** The direct messages replace that week's team-channel post, one time. Each named the owner's work, reviews, and latest dates, and linked the rows. A follow-up line tells each owner that a commit or pull request on a row accepts all of it, with no reply needed. The team channel still carries that week's blockers and start notices. Decision 0015's Monday post otherwise stands.
6. **Unchanged.** `SPEC.md` Sections 12 and 17, which set what acceptance requires and not its form. Every date in decision 0025. One reviewer per slice.

## Consequences

- **A row with no acceptance isn't visible until November 8,** unless a date in decision 0025 fires first. Those dates still trigger a visible decision on their own.
- **An owner whose slice is still `BLOCKED` on November 8 may have no slice work to show.** That owner counts by replying, and the project lead asks in time.
- **The count is read from Git and direct messages,** and the tier input records only the number and a non-personal reason (`SPEC.md` Section 12 step 1). The November 8 rollup records the date each acceptance was read, with no names (decision 0015 item 2).

## Verification

- `tests/test_status_consistency.py` and `tests/test_tasks_dependencies.py` pass, and no `Depends` cell changes.
- `tests/test_contract_lock.py`, `tests/test_corpus_rules_freeze.py`, and `tests/test_request_effect.py` pass, because no pinned `SPEC.md` text changes.
- At the tier input, the count is recorded as a number with a non-personal reason category.
