# Paid summary: the November 9 development grid and coverage smokes

This is the paid summary [decision 0025](../../decisions/0025-full-study.md) item 5 requires. It holds no raw provider bodies. The raw records stay outside Git, in the private raw-record storage open to the project lead, `W7-T1`'s and `W7-T3`'s reviewers, and `W8-T1`'s owner. All of these runs are development-only and are excluded from estimates (`SPEC.md` Section 9).

## What ran

- **Recorded commit:** the paid-run record ([#88](https://github.com/marek-sm/CANARY/pull/88), `protocol/paid_run_record.json`) was committed as `ce6c3219b301a30e1c572466e8111a00c9c97c38`, on top of `f1907efd53aaccc47102ba728615d43965c41e50`. That commit is the one [`docs/reviews/2026-11-09-paid-run.md`](../../reviews/2026-11-09-paid-run.md) reviewed.
- **Code:** every run's provenance records commit `ce6c321`, `paid_run.code_digest` `5529d5eaae2e16a6d02a5e82c26c8c2b311955229e8b9f22bb4e733b48f0e279`, and no dirty paths.
- **Where it ran:** a fresh clone on the project lead's Mac, on November 9, 2026, after `paid_run check` printed "paid runs may start here".
- **Model:** `claude-haiku-5-5`, through the Messages endpoint.

## Files

| File | What it is | Command |
|---|---|---|
| [`grid-live-summary.json`](grid-live-summary.json) | The 90-cell development grid (`W7-T3`) | `python -m runner.grid_dev summary results/development/grid-live` |
| [`coverage-live-verify.json`](coverage-live-verify.json) | The 15 clean task-coverage smokes (`W7-T1`) | `python -m runner.coverage --verify results/development/coverage-live` |
| [`raw-manifest.json`](raw-manifest.json) | SHA-256 hashes of every raw results and events file in the grid, the smokes, and decision 0026's live check | `python -m runner.raw_manifest results/development/grid-live results/development/coverage-live results/development/live` |

Each file is the unedited output of its command, run from the paid clone. `python -m runner.raw_manifest … --check raw-manifest.json` printed "ok: 3 run(s) match".

## What the files show

- **Grid:**
  - 90 of 90 trials found, with `complete: true`.
  - No infrastructure failure and no run-wide stop.
  - 0 gate/audit mismatches and 0 unauthorized dispatches.
  - Usage was recorded for every trial.
- **Smokes:** 15 of 15 found, all `completed`, run on `claude-haiku-5-5`, not the mock.
- **Development trials:** the ledger on the project lead's Mac records 107 of the Section 9 ceiling of 120. They are the October 10 check, decision 0026's live check, the 90 grid cells, and the 15 smokes.
- **Spend:** the ledger prices those trials at $0.039647 at `analysis/price_bound.py`'s rates. That matches the summary's token counts, and the project lead reconciles it with the Claude Console.

The Gate 2 step reads these runs separately. This summary reports no readiness decision, floor count, or budget result.
