# Lead-side review of the estimand report module

- **Decision:** [0031](../decisions/0031-merge-on-green.md) items 4 and 5, and [decision 0038](../decisions/0038-gate3-report-module.md) item 7, for the report module PR (#108), which adds `analysis/report.py` under decision 0038 item 3.
- **Commit reviewed:** `main` after #108 merges on `D_H` (decision 0039 item 3), so it holds every Gate 3 input: #107, Miles's `W8-T5` PR, the host-environment PR, and #108. The digest below was computed beforehand from that merged content. The project lead prints the digest on `main` after the merge and attests only if it matches. This is the final digest that the Gate 3 step runs at `F20`.
- **`paid_run.code_digest`:** `e36bd5ba3cf0ea8be80c3c3ca4a8cf43d36e154e26f4d7838d9c799df03a23a8`
- **Open blocking findings:** 0. The project lead classified every finding on November 14, accepting each class as written below.
- **Safety findings:** none.
- **Method:**
  - Claude, an AI assistant, wrote the module and its wrapper tests on November 14, after the November 9 development outcomes were visible and before any evaluation, official, or C1 outcome existed. No provider call or network call was made, no key was set, and `~/.canary` wasn't read.
  - The module's docstring lists the 14 choices `SPEC.md` leaves open (the percentile rule, the boundary-collapse test, the undefined-draw test, and the rest) before any test was written (decision 0038 item 8).
  - A separate agent wrote `tests/test_report_golden.py` (62 tests) from `SPEC.md` Sections 7, 9, and 10, the open-choice list, and an API description, without opening the module: exact values on small synthetic sets, all 27 resamples of a three-base set through an injectable resampler, a seed-fixed regression value recomputed independently from `random.Random(20261114)`, and degenerate cases. They passed on their first run, because the module was written at the same time, so they have no failing-first output.
  - Two `fix-reviewer` rounds. Round 1 found 2 blocking findings and 8 minor ones and ran 76 mutants; round 2 found 1 blocking finding and 4 minor ones over 89 mutants. Both rounds' findings are fixed or stated below, and the rule of two rounds ended the review there.
  - Suites, mock-only: the full suite on the module's tree (4,191 passed, 74 skipped, 0 failed (13m32s)); `tests/test_report.py` and `tests/test_report_golden.py` (105 passed); `make report` exits 0 and leaves `paper/generated/estimand_shells.md`, `lead_outputs.md`, and `report.md` byte-identical. A synthetic 1,092-record `F20` set (1,080 primary and 12 C1 records, schema-valid) reports through the command line in about 5 seconds, under Section 11's five minutes. On `16fa6db`, with the `W8-T5` PR's diff, the host-environment PR, and #108 merged locally, `make report` exits 0 and leaves the tree clean, and the report, output-freeze, `make report`, scaffold, and Gate 3 input tests pass.
- **Classes (decision 0031 item 5):** a finding is blocking if it could change a score, a count, a gate or readiness result, or a safety property. Non-blocking findings go to their owners by the next freeze, or are stated as limitations. The project lead classified every finding on November 14 as written below: R-1 and R-11 blocking, fixed; R-2 blocking, closed by the evidence below; R-3 to R-10 and R-12 to R-15 non-blocking; and no safety finding.

## Scope

| Scope | What was read |
|---|---|
| #108 | In full: `analysis/report.py`, `paper/generated/report.md`, `tests/test_report.py`, `tests/test_report_golden.py`, and the `README.md` sentence; against `SPEC.md` Sections 7, 9, and 10, decision 0038 items 3 and 8, `paper/estimand_manifest.json`, `analysis/lead_outputs.py`'s readers, `analysis/c1_table.py`, `analysis/floor_count.py`'s floor fields, `analysis/active_protocol.py`, `schemas/result.schema.json`, and the runner's attempt and model-call records (`runner/mock_slice.py`, `runner/execute.py`, the provider adapters) |
| Left out | Everything else on `main`, which the [whole-tree review](2026-11-13-whole-tree.md) and the [Stage 1 review](2026-11-14-gate3-inputs.md) cover |

## Blocking findings, fixed

| ID | Finding | Fix and test |
|---|---|---|
| R-1 | **The content-filter step could drop a real D1_POLICY_GATE request from the conformance counts.** The module took a content-filter trial's last step from `model_calls`, which holds only attempts with a model response. An HTTP content-policy rejection at step k is an attempt with no model call, so the module treated step k−1 as the filtered step and removed its request: an escape with an effect read as `NA (0 eligible requests)`, and a non-evaluable request no longer suspended the perfect-conformance claim. `SPEC.md` Section 9 says an HTTP rejection adds no request at that step (`fix-reviewer` round 1, B1) | The last step is now the trial's last transport attempt (`attempts`), then its model calls, then its tool events; open choice 7 says so. `tests/test_report.py`: an HTTP rejection keeps an earlier escape and an earlier non-evaluable request (both failed before the fix), and a filtered response's own tool call is still the content-filter request |
| R-2 | **No pre-fix failing output for new executable code** (`fix-reviewer` round 1, B2). The golden tests passed on their first run | Closed by evidence rather than code: R-1's failing-first tests; round 1's 76 mutants, of which the score-path survivors (the rendered interval scheme per estimand, the fast bootstrap path, and the clean-utility cost's sign and scale) are now killed by `test_each_rendered_value_and_interval_is_the_public_estimate_and_bootstrap` (10 estimands: each rendered value and interval equals the public function and `bootstrap()`) and `test_clean_utility_cost_is_baseline_minus_defense_in_percentage_points`; and round 2's rerun of the mutant set |

## Non-blocking findings

| ID | Owner or limitation | Finding |
|---|---|---|
| R-3 | Fixed in #108 | The C1 section couldn't read a raw run: a sweep run holds only primary records, so a report from a raw run printed the C1 section as `PRE-RESULTS — NO DATA` (M2). A repeatable `--c1-run DIR` now adds C1 run records, with a test |
| R-4 | Limitation, stated in the report | `SPEC.md` Section 10 asks for model refusals by configuration, but no result-record field identifies a refusal (the schema's `termination_reason` has no refusal value). The reliability table prints refusals as `not recorded` rather than inferring them from text (open choice 10; M3) |
| R-5 | Limitation, stated in open choice 2 | The boundary warning fires on any zero-width interval, also one that collapses at an interior value. It over-warns; it never hides a boundary collapse (M4) |
| R-6 | Fixed in #108 | The header's collapse limitation ignored template-level macro intervals (M5) |
| R-7 | Fixed in #108 | Records passed with `--superseded` weren't split-checked (M6) |
| R-8 | Fixed in #108 | Secondary tables' macro rows said "headline-ineligible"; they now say "not interpreted until repaired", as Section 9 words it for a secondary outcome (M7) |
| R-9 | Fixed in #108 | Leave-one-attack-family-out printed `NA (stratum emptied)` for a component already undefined over every base; `emptied` now means a removal left a component with complete pairs with none (M8) |
| R-10 | Project lead, by the paper draft | In the frozen corpus, leaving out `crafted-email-injection` or `tool-result-instruction-override` empties a task template, so those clean-utility-cost rows print `NA (stratum emptied)`, as Section 10 requires. The paper states it |

## Round 2

| ID | Class | Finding | Fix and test |
|---|---|---|---|
| R-11 | Blocking, fixed | Four of round 1's minor fixes (R-6 to R-9) changed behavior with no test and no pre-fix output: reverting any of them still passed every test (`fix-reviewer` round 2, BL1) | One test each in `tests/test_report.py`, all of which failed against the round-1 module: a collapsed template macro alone sets the report's limitation; a `--superseded` development record is refused; primary tables' macro rows say "headline-ineligible" and secondary ones (attack and secure task completion, injection excess risk, background rates) "not interpreted until repaired"; a component undefined over every base isn't "emptied" by a removal; and `--c1-run` without records is refused |
| R-12 | Non-blocking, fixed | The rendered-interval tests' fixture gave the same intervals under global and stratified resampling for 5 of 10 estimands, so it couldn't tell the schemes apart (m1) | The fixture now varies by channel and condition and has unobserved endpoints; a test checks the two schemes give different intervals |
| R-13 | Non-blocking, fixed | A record whose attempt lacks a `step` fell back silently to its model calls; reachable only through `generate()` on schema-invalid input (m2) | Refused with `ValueError`, with a test |
| R-14 | Non-blocking, fixed | `--c1-run` records were neither verified nor split-checked (m3) | Each directory must pass `runner.c1_trial.verify_c1` complete and hold only `c1_control` records, with tests |
| R-15 | Non-blocking, fixed | `README.md` didn't mention `--c1-run` (m4) | The sentence says a sweep run holds no C1 records and `--c1-run` adds them |

## What holds

- Every manifest estimand that `analysis.lead_outputs` doesn't generate has a table in `paper/generated/report.md`, with the manifest's columns unchanged and in order, plus the missingness range, the 5% threshold, and the boundary warning where intervals exist; the C1 section is `analysis.c1_table`'s.
- Rates and paired effects are adapter-first (or task-by-adapter) and equal-weight macro-averaged, with exact `x/n` or pair counts; a pooled `x/n` appears only when denominators are equal. Security estimands resample bases globally and task-template estimands within each stratum, 10,000 draws from `random.Random(20261114)`; a draw with an undefined component is excluded and counted, and an interval with fewer than 9,500 valid draws is withheld.
- The estimands read only `evaluation` and `primary_indirect` records; a development or demo record is refused. The geometry comes from `protocol/active.json`, and each base's template and family from its frozen corpus file. Nothing hard-codes 20 bases, three channels, or both defenses.
- It adds no dependency and edits none of the files decision 0038 item 3 freezes.

## Not checked

- No sweep, C1, or paid run exists, so the module hasn't run on official evidence.
- The step's `analysis_hash` is computed at the Gate 3 step by `python -m analysis.gate3_hashes`, not here.
