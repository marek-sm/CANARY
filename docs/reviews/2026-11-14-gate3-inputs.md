# Lead-side review of the Gate 3 step's Stage 1 inputs

- **Decision:** [0031](../decisions/0031-merge-on-green.md) items 4 and 5, for the two Stage 1 inputs that [decision 0038](../decisions/0038-gate3-report-module.md) item 2 lets the Gate 3 step use: the G3-2 fix PR (#107) and Miles's `W8-T5` PR (branch `lead/w8-t5-merge`). This file also holds the errata to the attested whole-tree review [`2026-11-13-whole-tree.md`](2026-11-13-whole-tree.md), which can't be edited once attested.
- **Commit reviewed:** `main` after #106 (decision 0038, no hashed path), #107, Miles's `W8-T5` PR, and decision 0039's PR (docs only, no hashed path) have merged. This is decision 0038's fallback base, `D_G`. The project lead prints the digest on that `main` and attests only if it equals the one below.
- **`paid_run.code_digest`:** `fdbc1c38d6bf334eb40bb00d5799dc9eaa7faacb4d2672f700eb0ece6bceccf3` (`D_G`)
- **Open blocking findings:** 0. The project lead classified every finding on November 14, accepting each class as written below.
- **Safety findings:** none.
- **Method:**
  - Claude, an AI assistant, wrote the G3-2 fix PR and read Miles's `W8-T5` PR, and ran mock-only checks. No provider call or network call was made, no key was set, and `~/.canary` wasn't read.
  - G3-2 was found by `fix-reviewer`'s pass on PR 1's last four post-review fixes on the morning of November 14, on the attested `07e28ed` tree. Its fix went through a failing-first test on a real sweep run (the fake provider of `tests/test_sweep.py`) and one `fix-reviewer` round, which found 0 blocking findings and 6 minor ones and ran mutation checks: dropping the directory check, dropping the schedule check, `==` in place of `same_json`, reading canaries from the released record, a changed hash text, a case-folded sort, leaving the sanitizer in, and dropping the `ENGINEERING` reason check or the untracked-file check each made a test fail.
  - Miles's `W8-T5` PR was read in full against `main`: its diff is his commit `d3b1910`'s 6 files, with the `Makefile` conflict with #104 resolved in the merge commit.
  - Suites, mock-only: the full suite on the G3-2 fix PR's tree (4,086 passed, 74 skipped, 0 failed); `tests/test_output_pipeline_freeze.py`, `tests/test_make_report.py`, and `tests/test_paper_scaffold.py` on the merged `W8-T5` tree (10 passed); and, on #107's merge commit `16fa6db` with the `W8-T5` PR's diff applied, those three files with `tests/test_gate3_inputs.py` (48 passed, 1 skipped) and `make output-freeze-check`, `engineering-report-check`, `lead-outputs-check`, and `paper-shells-check` (exit 0), with the same `paid_run.code_digest` as below.
- **Classes (decision 0031 item 5):** a finding is blocking if it could change a score, a count, a gate or readiness result, or a safety property. Non-blocking findings go to their owners by the next freeze, or are stated as limitations. The project lead classified every finding on November 14 as written below: G3-2 blocking, fixed in #107; G3-M1 to G3-M6 and N-W8T5-1 non-blocking; and no safety finding.

## Scope

| Scope | What was read |
|---|---|
| #107 | In full: `analysis/lead_outputs.py`'s changes, the new `analysis/gate3_hashes.py`, `tests/test_gate3_inputs.py`, and the changed helpers in `tests/test_count_diagnostics.py`; against `runner/sweep.py` `verify_sweep`, `runner/execute.py` `stored_schedule`, `trial_slug`, and `check_stored_run`, `analysis/sanitizer.py` `scored_projection`, and `analysis/active_protocol.py` `generate` with `schemas/active_protocol.schema.json` |
| Miles's `W8-T5` PR | In full: `analysis/output_pipeline_freeze.py`, `paper/output_pipeline_freeze.json`, `tests/test_output_pipeline_freeze.py`, `docs/W8_T5_HANDOFF.md`, `paper/README.md`, and the `Makefile` merge resolution |
| Left out | Everything else on `main`, which the whole-tree review covered for `226b161c…1937` |

## Blocking findings, fixed

| ID | Finding | Fix and test |
|---|---|---|
| G3-2 | **The count-only tables could read raw events the verifier never checked.** `analysis/lead_outputs.load_run` read each trial's events from beside whichever `*/results.jsonl` it found, while `runner.sweep.verify_sweep` (through `runner.execute.check_stored_run`) recomputes the events in the trial's scheduled directory, `execute.trial_slug(trial)`. A result moved into another directory beside edited events still verified complete, and decision 0028 item 4's counts were computed from the edited copy. This was in the attested `07e28ed` tree | #107: `load_run(run, schedule)` takes the run's stored schedule and refuses a result whose trial isn't in it or whose directory isn't `trial_slug(trial)`. `tests/test_gate3_inputs.py`: two cases on a real sweep run, a raw run as the record source and an `--events` run, both of which failed before the fix with `DID NOT RAISE ValueError` after `verify_sweep` returned `complete: True` |

## Non-blocking findings

| ID | Owner or limitation | Finding |
|---|---|---|
| G3-M1 | Fixed in #107 | `_bound` compared the final record with the raw run's stored result using Python `==`, so `true` equalled `1` (`fix-reviewer`'s M3 on PR 1). It now uses `same_json`; before the fix, `{"n": true}` and `{"n": 1}` compared equal |
| G3-M2 | Fixed in #107 | No test showed that the canary counts read the raw run's canary set, not the released record's (M2 on PR 1). A test now does, and fails if the released record's set is read |
| G3-M3 | Fixed in #107 | The `BOUND_FIELDS` comment said the sanitizer keeps every bound field unchanged; `scored_projection` omits `normalized_args` and the sanitizer may redact a nested key (M4 on PR 1). The comment now says so, and that such a record is refused |
| G3-M4 | Limitation, stated in the module docstring | The binding of an `--events` run's stored result to its final record is enforced only in `main()`; `generate()` binds nothing (M5 on PR 1) |
| G3-M5 | Limitation: the step runs from a fresh checkout | `analysis.gate3_hashes`' clean-checkout check reads git's index, so a covered file marked `--assume-unchanged` or `--skip-worktree` and then edited, or a file removed from the index and excluded, isn't refused. It also doesn't confirm that `corpus/freeze.json` and the validation plan and schema are tracked (they are). A fresh checkout has none of these states |
| G3-M6 | Project lead, after Gate 3 | Test gaps: `tests/test_tasks_dependencies.py` doesn't check lead inputs (M6 on PR 1); `tests/test_gate3_inputs.py` tests a modified and an untracked file but not a staged-only or deleted one (both refused by hand), and its check of this checkout's own hash is a smoke test. M1 on PR 1, that test 1's pre-fix output there failed on an API shape rather than on the read, is superseded by this pull request's own failing-first evidence |
| N-W8T5-1 | Limitation until the Gate 3 record pins it, as WT-8 | `analysis.output_pipeline_freeze --check` compares the committed record with the disk only, so a regenerated record (`make output-freeze`) passes. The Gate 3 record states `output_pipeline_hash` and `test_evidence_hash`, which anchors them |

For the step, not a finding in either pull request: `analysis.active_protocol.generate(...)` at `ENGINEERING` replaces its default `official` null reason whenever any `null_reasons` are passed, so the step passes every null field's reason itself, as decision 0038 item 5 requires. `active_protocol.validate` doesn't check `tier_class` against the tier's row; the step takes both from the `TIERS` row.

## Errata to `2026-11-13-whole-tree.md`

The attested file stays as it is (`runner/lead_review.py` refuses a changed file). These corrections come from the November 14 `doc-auditor` pass on `main`, and none changes a finding, a class, or the digest:

1. **Line 3** says the review covers "the three fixes this review's own pull request makes". It made six: WT-1, WT-2, N-78-1, N-77-4, N-77-5, and N-77-6, as its Classes line and tables say.
2. **Line 4** names `0337037` as the commit "after this pull request merges". `0337037` was the base; the merged tip is `07e28ed` (#105's merge), whose `paid_run.code_digest` is the attested `226b161c…1937`.
3. **Lines 37–38:** the "Pre-fix failing output…" sentence sits between table rows, so the N-77-4, N-77-5, and N-77-6 rows render as loose text, not as rows of the blocking table. All three are blocking findings fixed in #105, as the Classes line states.
4. `STATUS.md` lines that still called #74 and #77 open were fixed in #106.

## What holds

- A raw run's result is read only from its scheduled directory, and only for a trial in its stored schedule; a nested results file is ignored by both the verifier and `load_run`, a second copy is refused, and a non-string `logical_trial_id` is refused.
- `analysis_hash` follows decision 0038 item 4 byte for byte: tracked files under `analysis/` except the sanitizer, plus the manifest, sorted by path bytes, LF-joined with no trailing newline. `--check` fails on a null or mismatched fallback field at every tier but `STOP`, on a wrong `analysis_hash` at an empirical tier, and on an `analysis_hash` at `ENGINEERING` that isn't null with its own reason.
- All 6 hashes in `paper/output_pipeline_freeze.json` match `main`; the merged `Makefile` runs `output-freeze-check` in both `test` and `report`, and `report` still runs the lead outputs.

## Not checked

- No sweep, C1, or paid run exists, so neither pull request ran on official evidence.
- Linux `bwrap` wasn't rerun; neither pull request touches the sandbox.
