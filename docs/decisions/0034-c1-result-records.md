# 0034: Official C1 control records in the result schema

- Status: Accepted. Approved by the project lead on 2026-11-12 by merging this record; drafted with AI assistance.
- Date: 2026-11-12
- Decision scope: Protocol
- Secondary scopes: None
- Related specification sections: Sections 3, 8, 9, 10, 11, and 12
- Supersedes: None. Deviation entry: DEV-0005 in [`docs/protocol_deviations.md`](../protocol_deviations.md).

## Context

Every empirical row in `SPEC.md` Section 12, from `F20` down to `R6`, runs C1 direct-injection controls under D0_BASELINE, at three repeats each. The result schema locked at 1.0.0 ([decision 0009](0009-measurement-contract-lock.md)) allows only `split` `development` or `evaluation`, and only `channel` `C2`, `C3`, `C4`, or null. So no official C1 record can validate, and no row has a lawful C1 record form. The spend-ledger schema refuses a C1 trial's start line for the same reason, so a C1 trial would stop before its first call. `runner/c1_mock.py` worked around this by writing its own engineering evidence.

[Decision 0025](0025-full-study.md) found the gap on November 2 and required this change as its own record (item 8), through Section 11 change control, with a deviation entry and re-pin, by November 8. It slipped to noon on Thursday, November 12, which leaves `W8-T3` more than 24 hours before its November 13 last merge (`TASKS.md`). A changed enum is a type change on `docs/DATA_CONTRACTS.md`'s evolution list, so decision 0009 item 9 sends it through Section 11. Decision 0014 with DEV-0001 and decision 0020 with DEV-0002 show how that applies before the full freeze.

No C1 record has run live, and none of the 107 development trials was on C1 ([decision 0033](0033-c1-pilot-example.md)).

## Options considered

1. **A separate C1 result schema.** Rejected. `SPEC.md` Section 8 has one result contract for official empirical trials, and the Section 10 C1 table reads the same six facts, unions, utility, and status a result record already carries.
2. **Add the C1 form to the result schema as version 1.1.0, additive only.** Chosen.

## Decision

1. **Result schema 1.1.0.** The `split` enum gains `c1_control`, the value `schemas/base_case.schema.json` already uses, and the `channel` enum gains `C1`, as `docs/evidence/w7-t1/c1-summary.json` already says.
2. **The C1 form.** A record with `split` `c1_control` must have:
   - a non-empty `protocol_version`;
   - `channel` `C1`, `condition` `attack`, and `configuration` `D0_BASELINE` (`SPEC.md` Sections 3, 9, and 12);
   - a non-empty `comparison_superblock_id`, one per C1 repeat, which carries its own canary pair (`SPEC.md` Section 9);
   - `analysis_role` `c1_control`, so a C1 record can never carry `primary_indirect`;
   - a `base_case_id` matching `c1-NNN`, so a development-material C1-cost pilot (decision 0033) can't pass as an official C1 record;
   - `schema_version` `1.1.0`.
3. **Other splits.** The evaluation branch is unchanged, so `C1` is never an evaluation channel. A development record may carry `C1`, for decision 0033's development-only pilot.
4. **Version.**
   - `$id` becomes `urn:CANARY:schema:result:1.1.0`. `schema_version` accepts `1.0.0` or `1.1.0`.
   - A `1.0.0` record must keep exactly the 1.0.0 shape: `split` is `development` or `evaluation`, and `channel` is `C2`, `C3`, `C4`, or null. So 1.0.0 still means what it meant, and preserved records validate.
   - Those preserved records include:
     - the 195 November 9 development and mock-grid result lines;
     - the committed replay record that `make replay` reads;
     - the records schema-only readers such as `runner/raw_manifest.py` see.
   - The recompute checks (`check_stored_run`, used by `verify_grid_run`, `floor_count.load_run`, and `sweep.verify`) compare `schema_version` field by field. They already run from the run's own commit (`analysis/floor_count.py`, `runner/execute.py`), and they keep doing so. A run started before this change is restarted under a new experiment ID, never resumed after it: a resume would mix 1.0.0 and 1.1.0 records, and `check_stored_run` would then refuse it from either commit. No run is in flight; the November 9 grid is complete.
5. **Writers move with the schema,** as at the lock (decision 0009 item 2). `runner/mock_slice.assemble_result` writes `1.1.0` through `RESULT_SCHEMA_VERSION`. The event, policy, and authorization-vector schemas stay 1.0.0, and no implementation version moves.
6. **The spend ledger.**
   - `schemas/spend_ledger.schema.json` moves to 1.1.0 the same way: a start line may carry `split` `c1_control` only at 1.1.0, and every 1.0.0 line stays valid.
   - `runner/spend_ledger` writes `1.1.0` through `LEDGER_SCHEMA_VERSION`.
   - `counts_against_ceiling` already counts only development trials, so C1 trials count in dollars, not against Section 9's 120 development trials.
7. **The protocol version.** `SPEC.md` moves to v1.23.0 for this change, and no `SPEC.md` text changes. Section 8 already makes the schemas authoritative and scopes the result schema to official empirical trials, which C1 controls are. No pinned section names the result split or channel sets.
8. **Left to `W8-T3`'s C1 part, which this record unblocks:**
   - the C1 schedule rows (`runner/schedule.py`'s `CHANNELS` and the schedule spec);
   - `execute.run_schedule`'s split guard and its message;
   - the official C1 executor, which doesn't exist yet (`docs/W7_T1_HANDOFF.md`, and the `live_blocker` field in `corpus/c1_controls/`). One run directory holds one split and one analysis role, so C1 runs as its own run directory in the sweep's window;
   - the C1 table generator, and the C1 list in `active.json`.

   For decision 0012's wiring (project lead, due November 13): `analysis/request_effect.py` must skip `c1_control` records rather than raise on them, and the evaluation-split C1 stand-in in `tests/test_request_effect.py` is a shape that can no longer exist.
9. **Numbering.** This record takes 0034.

## Consequences

- `protocol/paid_run_record.json` hashes both schemas, `runner/mock_slice.py`, `runner/spend_ledger.py`, and `runner/c1_mock.py`. Any paid call after this merges, a C1-cost pilot included, needs a new mock grid and a new paid-run record first.
- No experiment or validation ID exists, and no C1 or evaluation outcome exists, so nothing reruns (Section 11 steps 3 and 5).
- This record claims nothing about what the C1 controls will show.

## Verification

- `tests/test_result_schema_c1.py` checks the C1 form, each rejected variant, the 1.0.0 shape, the writer's version, and a C1 ledger line. It failed before the change.
- `tests/test_contract_lock.py` passes with only the result schema's version and hash changed. The event, policy, and authorization-vector pins and every `SPEC.md` pin are unchanged.
- Every stored November 9 result line (195) and every line of the project lead's spend ledger (213) validates under the 1.1.0 schemas.
