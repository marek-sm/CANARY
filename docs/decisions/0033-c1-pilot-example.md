# 0033: Supersede decision 0018's C1-cost pilot example

- Status: Accepted. Approved by the project lead on 2026-11-11 by merging this record; drafted with AI assistance.
- Date: 2026-11-11
- Decision scope: Protocol
- Secondary scopes: None
- Related specification sections: Sections 5, 9, and 12
- Supersedes, for the example named in item 1 only: decision 0018 item 3. Every other part of decision 0018 stays in force.

## Context

[Decision 0018](0018-c1-control-order.md) item 3 closes C1 eligibility "at the first live call on any C1 record, such as a C1-cost pilot under Section 9." [Decision 0025](0025-full-study.md) item 8 then required a record superseding that example before any C1-cost pilot, and by November 10, because any C1-cost pilot uses development-base material only (`SPEC.md` Section 5: all live-model development before freeze uses only the five excluded development bases). A pilot on development material isn't a live call on a C1 record, so the example named a case that can't happen.

This record is one day late: it was due November 10. Nothing turned on the slip. No C1-cost pilot ran: the 107 development trials are the October 10 check, decision 0026's live check, the 90-cell grid over the five development bases, and the 15 coverage smokes, none on a C1 record ([`docs/evidence/paid-run-2026-11-09/`](../evidence/paid-run-2026-11-09/README.md)).

## Options considered

1. **Leave the example.** Rejected. It contradicts Section 5 and decision 0025 item 8.
2. **Replace the example and state when eligibility closes in practice.** Chosen.

## Decision

1. **The example is withdrawn.** A C1-cost pilot uses development-base material only. It isn't a live call on a C1 record and doesn't close C1 eligibility.
2. **The rule stays.** C1 eligibility closes at the first live call on any C1 record. Until then, a record leaves only with a Section 5 status found by building or mock-checking it, never because of a live result. After it, the set is fixed and no record leaves (`SPEC.md` Section 12).
3. **The freeze fixes the set first, in practice.** All live-model development before the freeze uses only the five development bases (`SPEC.md` Section 5), so no C1 record reaches a live model before the Gate 3 freeze on Saturday, November 14. The freeze fixes the C1 set, and removing a record after it is a material change under `SPEC.md` Section 11. The first live call on a C1 record comes later, in the sweep, and item 2's rule then also holds.
4. **A pilot's cost enters the budget only through Section 9's maximum.** The Section 9 equation prices each C1 trial at the larger of a development-only direct-injection pilot, the global observed maximum, and the frozen price bound. A pilot changes the C1 price only if it costs more than the frozen bound, which decision 0025 item 11 then re-evaluates. A pilot also spends one of the 13 reserved development trials, so it reduces the balance and the reserve.
5. **Numbering.** This record takes 0033.

## Consequences

- Decision 0018's order and its four C1 records are unchanged.
- `SPEC.md` carries no pilot example and doesn't change.

## Verification

- No test reads the example. `tests/test_contract_lock.py` passes unchanged.
