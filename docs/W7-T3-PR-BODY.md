# W7-T3 pull request (copy into GitHub)

**Title:** W7-T3: ninety-cell development grid orchestration and Gate 2 budget evaluation

**Base (until #47 merges):** `lead/w6-t3-part-a`  
**Reviewer:** @milesshoe (Miles, T5)

## Summary

- Committed `protocol/development_grid_spec.json` (90 cells) and `runner/grid_dev` (`validate`, `mock`, `verify`, `summary`, `live` with paid-run gate).
- Adds `analysis/gate2_budget.py` for the Section 9 budget inequality on live grid records.
- CI runs `make grid-check` after `make test` (validate, grid tests, 90-cell mock preflight on fixture corpus).
- **Limitation:** executor still uses the W6-T3 text-only path until lead tool-result delivery merges; mock/live runs prove schedule, resume, and record shape—not yet indirect Gate 2 instrument.

## Depends on

- #47 (W6-T3 runner) merged first when retargeting to `main`.
- Official `make grid-mock` on `corpus/development/` after W6-T2 **#34** merges.
- Live grid only after lead records paid-run condition (`CANARY_PAID_RUN_ACK=1` is not sufficient alone).

## Test plan

- [ ] `make test` and `make grid-check` green in CI
- [ ] `make grid-mock-fixtures` locally (optional)
- [ ] Confirm no `state/` in the PR diff
