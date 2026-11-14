# 0038: Let the Gate 3 step use three late inputs merged on November 14, with a fixed `ENGINEERING` fallback

- Status: Proposed. Drafted with AI assistance; approved by the project lead by merging this record on November 14.
- Date: 2026-11-14
- Decision scope: Protocol (schedule, before the freeze)
- Secondary scopes: Governance
- Related specification sections: Sections 9, 10, and 11
- Related records: [decision 0027](0027-acceptance-by-work.md), [decision 0029](0029-gate-chain-shift.md), [decision 0034](0034-c1-result-records.md), [decision 0037](0037-c1-authorization.md), [decision 0031](0031-merge-on-green.md), [decision 0036](0036-lead-output-wiring.md), and `TASKS.md`'s `W8-T3` row (the November 13 evening note).
- Supersedes, for the words named only:
  - [decision 0029](0029-gate-chain-shift.md) item 5's "on W8 work merged by Friday, November 13", and the same cutoff in `TASKS.md` ([dependency discipline](../../TASKS.md#dependency-discipline), the gate-steps paragraph, and the W8 gate-step row), for the three inputs in item 1 only;
  - [decision 0036](0036-lead-output-wiring.md) item 1's "before `W8-T3`'s report module", item 5's "as it would have read `W8-T3`'s report code", and the second bullet of its Consequences;
  - [decision 0026](0026-malformed-calls-and-price-bound.md)'s "through `W8-T3`'s report code".

  Nothing else in those records changes.

## Context

Gate 3 runs Saturday, November 14, on `main` at `07e28ed`, whose `paid_run.code_digest` (`226b161c…1937`) the project lead attested for the November 13 whole-tree review.

- **No estimand report module.** `W8-T3` (#77) merged without one. `make report` names `analysis.report`, which doesn't exist, and nothing in the repository computes a `SPEC.md` Section 10 estimand: there is no bootstrap and no analysis seed. Of the 25 estimands in `paper/estimand_manifest.json`, `analysis/lead_outputs.py` generates three (decision 0036) and `analysis/c1_table.py` one. The other 21 have no code.
  - Section 11 freezes "the applicable analysis/report generator plus empty empirical table/figure definitions" at Gate 3.
  - So the Gate 3 step can't pass at an empirical tier on `07e28ed`.
- **The fallback hashes.** The same Section 11 list needs the dormant `ENGINEERING` fallback's plan, schema, report generator, and hashes for every non-`STOP` tier. Nothing computes those hashes (`analysis/active_protocol.py` only passes them through), and `protocol/engineering_validation_plan.json` still says `validation_id: "PENDING-validation-id"`. Both an empirical step and an `ENGINEERING` step have this gap.
- **G3-2, a defect in the attested tree.** The morning's review of decision 0036's last fixes found it: `analysis/lead_outputs.load_run` reads each trial's events from the directory beside its results file. `runner.sweep.verify_sweep` verifies the events in the trial's own `trial_slug` directory instead. A rearranged run could therefore feed the count-only tables events the verifier never checked, against decision 0036 item 5.
- **`W8-T5` has no pull request.** Its owner pushed `codex/w8-t5-output-freeze` (`d3b1910`, the output-pipeline freeze record) on November 13 and never opened a pull request. Every hash in that record still matches `main`.

None of the 1,092 planned official trials has run. No evaluation, official, or C1 outcome exists. The November 9 development outcomes are visible.

## Options considered

1. **`ENGINEERING` now.** Rejected. None of the 1,092 planned official trials would run, and there would be no empirical result, because of a missing file rather than anything measured. The model, prefix, defenses, and budget are ready.
2. **`STOP`.** Rejected for the same reason. It would also lose the validation report.
3. **Freeze without the generator and add it later through Section 11.** Rejected. `AGENTS.md` rejects a feature after the freeze. `analysis/` is in `paid_run.code_digest`. Analysis written once outcomes exist isn't pre-specified.
4. **Run Gate 3 after November 14.** Rejected. Section 11 freezes "no later than Saturday, November 14, 2026".
5. **Have `W8-T3`'s owner write it today.** Rejected. Asking for it now gives less than 24 hours' notice, and taking over part of a slice needs a visible decision before work proceeds (`AGENTS.md`, "Ownership and completion"), so it is a reassignment. The owner also has the `W9-T3` sanitizer pull request due November 15.
6. **A smaller prefix.** Rejected. It supplies no code.
7. **Cut `W8-T5`'s freeze record.** Rejected. The record is finished and pushed; only its merge is missing.
8. **A same-day window for three named inputs, with a fallback fixed now.** Chosen.

## Decision

1. **Window.** This is a schedule decision before the freeze (`AGENTS.md`, "Change classification", third row). For three inputs only, the Gate 3 step uses work merged through 9:00 pm on November 14:
   - (a) the G3-2 fix;
   - (b) `W8-T5`'s freeze record from `d3b1910`;
   - (c) the estimand report module.

   Section 11's date and pass evidence don't change. The November 13 whole-tree review stays as attested, and the file isn't edited; the corrections a documentation audit found in it on November 14 go into the new review file as errata. Until the Gate 3 step finishes, nothing else merges to `main` that changes a path in `runner/paid_run.py`'s `HASHED_DIRS`. The step runs from a fresh checkout of a commit whose `paid_run.code_digest` is the attested digest.

2. **Stage 1: the fallback base.** It comes first, in two pull requests.
   - **The G3-2 fix PR (lead scaffold).**
     - `analysis/lead_outputs.load_run` refuses a trial unless its results file sits in that trial's `trial_slug` directory, with a failing-first test in a new test file.
     - `python -m analysis.gate3_hashes` prints `analysis_hash` (item 4) and the four fallback hashes (item 5). With `--check protocol/active.json`, it fails on any mismatch and on any null fallback hash. The step therefore runs only committed commands and builds nothing new.
     - Cheap fixes from the same review of decision 0036's code:
       - the stored-record binding compares type-strictly;
       - a test reads the canaries from the released record;
       - the binding comment no longer says the sanitizer keeps every bound field unchanged;
       - the docstring states that only the command-line path binds.
   - **the `W8-T5` PR.** `d3b1910`, unchanged except that its `Makefile` conflict with #104 is resolved. It is a visible scope change of the merge step only, recorded in `TASKS.md`'s `W8-T5` row before the `W8-T5` PR opens, as on #66 (recorded November 11).
     - The project lead tells `W8-T5`'s owner before opening the `W8-T5` PR, in an informative notice that asks nothing.
     - If the owner says, before `D_G` is attested, that `d3b1910` isn't the finished `W8-T5` deliverable (decision 0027 item 1), the `W8-T5` PR doesn't merge, Stage 1 is the G3-2 fix PR alone, and the Gate 3 record states `W8-T5` as missed.
     - `W8-T5`'s owner keeps the slice, and the Gate 3 record states that it merged one day late.
   - **Review.** Both pull requests get decision 0031 items 4 and 5's lead-side review in `docs/reviews/2026-11-14-gate3-inputs.md`. The project lead then attests the resulting digest, `D_G`.
     - If that review finds a blocking problem in the `W8-T5` PR, the `W8-T5` PR is left out and Stage 1 is the G3-2 fix PR alone.
     - If it finds one in the G3-2 fix PR that can't close by 9:00 pm, item 6's last branch applies.

3. **Stage 2: the module.**
   - **Reassignment.** The estimand report module moves from `W8-T3` to the project lead as lead scaffold.
     - This record's pull request records the move in `TASKS.md`'s `W8-T3` row, and it merges before any module code or test is written.
     - The move is recorded one day after the slice's last merge date.
     - It is the visible reassignment that decision 0036 Option 2 lacked, and it follows the `W8-T3` row's November 13 evening note.
     - `W8-T3`'s 5.0-hour estimate stays as the planning record, and no member's hours change.
   - **What it is.** The report module PR adds `analysis/report.py`, the module `make report` already names. It adds no dependency: it uses the standard library only, with `random.Random(20261114)`.
     - Its estimands read only `primary_indirect` records from decision 0036 item 5's final set, through `lead_outputs`' readers. Its C1 section comes from `analysis/c1_table.py` over `c1_control` records.
     - It generates every manifest estimand that `lead_outputs` doesn't, exactly as Sections 9 and 10 define them:
       - adapter-first rates and macro-averages, with `x/n` or pair counts and complete and missing pairs;
       - the raw trial-level clean-utility rate;
       - 10,000 paired cluster-bootstrap draws: global over bases for security, within each task stratum for utility and secure completion;
       - excluded draws counted, an interval withheld below 9,500 valid draws, and a boundary-collapse warning;
       - `NA (0 eligible requests)`, with non-evaluable and unknown-disposition request counts by reason, and the suspension of the perfect-conformance claim;
       - mixed-repeat groups;
       - leave-one-attack-family-out sensitivity with `NA (stratum emptied)`;
       - the C2−C3, C2−C4, and C3−C4 contrasts;
       - the 5% component threshold and headline ineligibility;
       - missingness ranges, including the four-cell best/worst assignment;
       - each table's scheduled, observed, unresolved, complete-pair, attempted, and superseded counts;
       - the content-filter request count;
       - Section 10's development-floor form, which applies.
     - **Geometry.** It reads the geometry from the run's `protocol/active.json`; the empty output doesn't depend on it.
     - **Output.** It writes `paper/generated/report.md`. With no records, that file holds the shells marked `PRE-RESULTS — NO DATA`. Missingness ranges and threshold flags render there. No manifest shell, column, or pin changes.
     - **Frozen files it doesn't edit.** The report module PR doesn't edit `paper/generated/estimand_shells.md`, the manifest, `analysis/report_shells.py`, `tests/test_make_report.py`, or `tests/test_paper_scaffold.py`, which `W8-T5`'s record pins, or the `Makefile`; its own `make report` tests go in a new file. The `Makefile`'s message and comments naming `W8-T3` therefore stay out of date.
     - Decision 0012's first table stays first, because `make report` runs `lead_outputs` before this module.
     - A module missing any manifest estimand or any rule in this item isn't done under item 6.

4. **Seed and `analysis_hash`.**
   - **Seed.** The analysis seed is `20261114`. It is fixed here, before any module code exists, without running the bootstrap on any record.
   - **`analysis_hash`.** `analysis.gate3_hashes` computes it from a clean checkout's working-tree bytes. It is the SHA-256 of a UTF-8 text built as follows:
     - one line `<path> <lowercase sha256>` for every git-tracked file under `analysis/` except `analysis/sanitizer.py`, plus `paper/estimand_manifest.json`;
     - lines sorted by path bytes;
     - joined with LF, with no trailing newline.

     The sanitizer is excluded because it crosses Gate 3 to `W9-T3` (`TASKS.md`, `W8-T3` row). The step passes the value to `analysis.active_protocol.generate(...)`, and the check recomputes it. A later change to any covered file follows Section 11.

5. **Fallback inputs.** This record's pull request:
   - sets the dormant plan's `validation_id` to `CANARY-2026-ENG-V1`;
   - regenerates `paper/generated/engineering_report.md` with `make engineering-report`.

   The plan's `checks` list is the validation manifest. At the step, both tiers take these values, which the check recomputes and none of which may be null:
   - `source_ledger_hash`, copied from `corpus/freeze.json`;
   - `validation_plan_hash`, `validation_schema_hash`, and `report_generator_hash`: the SHA-256 of `protocol/engineering_validation_plan.json`, `schemas/engineering_validation.schema.json`, and `analysis/engineering_report.py`.

   At `ENGINEERING`, `generate(...)` receives one null reason for each null field.

6. **Fallback, fixed now and outcome-blind.**
   - **What "done" means.** By 9:00 pm on November 14, the report module PR has merged and meets item 3, and its review is attested with 0 open blocking findings.
   - **If the report module PR isn't done,** the Gate 3 step runs at `ENGINEERING` before midnight, with no further decision.
     - It runs from a fresh checkout of `D_G`'s commit plus this record's unhashed pull request. If the report module PR merged, the checkout is `main` after reverting it, and its digest must equal `D_G`.
     - If `D_G` isn't attested by 9:00 pm either, the step runs on the commit where this record merged. That record changes no `HASHED_DIRS` path, so the commit's digest is `226b161c…1937`. Then:
       - if the project lead classed G3-2 as blocking, it is an open blocking finding on the frozen code. The Gate 3 pass evidence requires 0 open blocking at every tier (`SPEC.md` Section 11, Gate 3 row), so the response is `STOP`;
       - otherwise `07e28ed`'s attested review governs, and the step runs at `ENGINEERING`.
     - **The `ENGINEERING` checks** are `make freeze-check`, `defense-freeze-check`, `recheck`, `python -m tasks.freeze --check`, `python -m analysis.active_protocol --check`, `make paper-shells-check`, `output-freeze-check` (when the `W8-T5` PR merged), `lead-outputs-check`, `engineering-report-check`, and, on `D_G`, `python -m analysis.gate3_hashes --check protocol/active.json`. The Gate 3 record keeps each one's output.
     - `analysis_hash` is null, with its reason. `make report` isn't a pass item at `ENGINEERING`; its exit-2 message is recorded.
     - "The step has run" means `protocol/active.json` and the Gate 3 record are committed on a pushed branch by 11:59 pm.
   - **If the report module PR is done but another pass item fails,** the ordinary Section 11 Gate 3 response applies.

7. **Review of the report module PR.**
   - Decision 0031 items 4 and 5's lead-side review: up to two `fix-reviewer` rounds and `docs/reviews/2026-11-14-report-module.md`, then the project lead's attestation, then a new mock grid and paid-run record.
   - The project lead can explain each estimand's code path before attesting.
   - The report module PR is due by 6:00 pm. A blocking finding in the lead's review that can't close by 9:00 pm triggers item 6.

8. **Blinding.**
   - No evaluation, official, or C1 outcome exists. Development outcomes are visible (the November 9 grid; the development floor applies at 0 of 15), and the module is written after them.
   - The module's docstring lists every choice `SPEC.md` leaves open before any test is written: the percentile rule, the boundary-collapse test, and the undefined-draw test.
   - A separate agent writes the golden tests from the `SPEC.md` formulas without seeing the module:
     - exact values on small synthetic sets;
     - the bootstrap logic checked by enumerating every resample of a three-base set through an injectable resampler;
     - a seed-fixed regression value;
     - degenerate cases.
   - Development records are test fixtures only and never enter a reported result.

9. **Authorities.** Nothing is frozen, so under `AGENTS.md` this record's pull request updates every affected authority together:
   - `TASKS.md`:
     - the dependency rule's Gate 3 record entry, the gate-steps paragraph, and the W8 gate-step row;
     - the `W8-T3` row (reassignment) and the `W8-T5` row (the merge-step scope change);
     - a November 14 lead-inputs row and the planned-exceptions sentence;
     - `W9-T3`'s `Depends` cell and its sanitizer note;
   - `STATUS.md`'s next-gate row;
   - `README.md`'s `make report` sentence and decisions row.

   `SPEC.md` doesn't change, and no protocol-deviation record is needed.

10. **Numbering.** This record takes 0038. Decision 0035 is open as #94 and keeps its number.

## Consequences

- **Lead time.** The project lead's added time on November 14 is about six hours:
  - Stage 1's review and attestation, 0.5 hours;
  - The report module PR's review and attestation, 2.5 hours;
  - classifications and this record, 0.5 hours;
  - the mock grid, paid-run record, `active.json`, and checks, 1 hour;
  - the Gate 3 record, 0.5 hours;
  - the gap sentence, due before the freeze, 1 hour.

  Decision 0031 item 9's trigger had already fired, so the license choice and author order stay at November 16–20.
- **Attestations and schedule.** There are two attestations today, `D_G` and then the final digest. The sweep starts after tonight's step and runs through November 17. Gate 4's dates don't move.
- **What the paper states.** The estimand code was written by the project lead with AI assistance on Gate 3 day, after development outcomes were visible, and its only review was the lead-side review.
- **If the window misses,** `ENGINEERING` applies under item 6, and no empirical result exists.
- This record claims nothing about what any estimand will show.

## Verification

- The golden tests in item 8 pass against `analysis/report.py`.
- `make report` over a synthetic `F20`-sized set of 1,092 records finishes in under five minutes without a key or network (Section 11).
- The empty run matches the committed shells.
- `python -m analysis.gate3_hashes --check protocol/active.json` passes at the step.
- The full suite and `tests/test_tasks_dependencies.py` pass, and `D_G` and the final digest are printed and attested.
