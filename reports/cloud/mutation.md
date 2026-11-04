# Mutation testing of the number-producing and safety-enforcing code

Base commit: `origin/main` at `3b165bfc7036a97804583cd22b5d2ea758ce1b3b` (November 4, 2026). Branch: `cloud/mutation`.

This is evidence for the project lead to decide on. An AI agent ran it and wrote it. It isn't the human review `SPEC.md` requires, and it doesn't stand in for one. No production code changed: the branch adds tests under `tests/`, this report, and the helper scripts and raw data under `reports/cloud/`.

## Summary

- **One real bug, with a failing test.** The audit evaluator compares `query_db` parameter values with Python `in`, so `true` and `1.0` match an allowlisted `1`, and `0` and `0.0` match `false`. The D1_POLICY_GATE evaluator compares type-strictly, as `docs/DEFENSES_AND_POLICY.md` requires. It's latent: every allowlisted parameter value in today's task policies and golden vectors is a string. `tests/test_gate_audit_typed_params.py` fails 4 cases by design.
- **mutmut** generated 5,949 mutants over the 14 target files. With the existing suite, minus seven slow 90-cell grid tests, 4,653 were killed and 1,296 were not (21.8%). I re-ran a random sample of 48 non-killed mutants against those seven slow tests, and none was killed. I also re-ran 27 of the reported findings against them, and none was killed. The slow tests don't change the picture.
- **Survival by module** ranged from 2.6% (`oracles/authorization/audit.py`) to 52.0% (`runner/paid_run.py`). Most survivors are error-message text, CLI help, JSON formatting, or equivalent mutants. The ones that matter are ranked below.
- **Most serious surviving mutants**, each now killed by a new test:
  - The paid-run gate stops refusing an ambient `ANTHROPIC_*` variable.
  - The paid-run record stops hashing `defenses/`, `corpus/`, or eight other directories (a module constant, found by the hand-written constant mutator).
  - Under D0_BASELINE and D2_DATAMARKING, dispatching no longer consumes the matching grant.
  - D0_BASELINE and D2_DATAMARKING dispatches are recorded as `blocked: true`.
  - The grant action hash ignores the contents of list arguments.
  - The tool sandbox silently skips unreadable directories when it checks for foreign sockets, or mounts all of the interpreter's `lib/`.
  - A Gate 2 budget equation in which every term can change unnoticed.
  - Both evaluators can count unknown prior calls twice, turning an evaluable request into a non-evaluable one.
- **Tests added.** 10 new test files with 165 test cases. Each test names the mutants it kills. They pass on unmodified code, except the one deliberately failing file.

Sections: [What I ran](#what-i-ran) · [Raw counts](#raw-counts) · [Findings, ranked](#findings-ranked) · [Tests added](#tests-added) · [Other observations](#other-observations-not-from-surviving-mutants) · [What I didn't check](#what-i-didnt-check) · [Living documents](#living-documents)

## What I ran

### Environment

- Ubuntu 24.04.5 LTS, x86_64, Linux 6.18, running as root in a cloud VM. 4 CPUs.
- `apt-get install -y bubblewrap` installed bubblewrap 0.9.0.
- `sysctl -w kernel.apparmor_restrict_unprivileged_userns=0` failed. The key doesn't exist on this kernel, which has no AppArmor. Unprivileged user namespaces worked without it: `bwrap --ro-bind / / --unshare-all true` succeeded as the non-root user.
- I created a non-root user, `canary` (`useradd -m -s /bin/bash canary`). I copied the repository without `.git` to `/home/canary/work/CANARY`, owned by `canary`. `tools/sandbox.py`'s root refusal was left as it is.
- Every test, mutation, and verification command ran through this wrapper, so no credential, proxy, or provider variable reached a test:

  ```sh
  runuser -u canary -- env -i HOME=/home/canary PATH=/home/canary/.local/bin:/usr/local/bin:/usr/bin:/bin \
      LANG=C.UTF-8 UV_NO_SYNC=1 UV_OFFLINE=1 <command>
  ```

  Only `uv sync` was given the HTTPS proxy and a copy of the CA file, to download the locked dependencies.
- Python 3.11.18 (uv), pytest 9.1.1, and mutmut 3.8.1, installed into the scratch copy's `.venv` only. cosmic-ray 8.7.0 was installed but not used, because mutmut ran.
- No provider call was made and no key was created or used. `runner/paid_run.py` was not changed. I didn't read, fetch, or use `corpus/evaluation/` or PR #73's branch.

### Baseline

`uv run pytest -q -x -p no:cacheprovider`, as `canary`, on the scratch copy: **1860 passed in 232.06s**.

### Tier 1: mutmut over the existing suite

The `[tool.mutmut]` block was added only to the scratch copy's `pyproject.toml`, never to the repository:

```toml
[tool.mutmut]
pytest_add_cli_args_test_selection = ["--deselect", "<each of the 7 slow tests below>", ...]
source_paths = ["oracles/authorization/", "defenses/", "runner/mock_slice.py", "runner/delivery.py",
                "agent/loop.py", "analysis/floor_count.py", "analysis/request_effect.py",
                "analysis/gate2_budget.py", "runner/paid_run.py", "tools/sandbox.py"]
also_copy = [every other top-level directory and file the tests read]
```

Command: `.venv/bin/mutmut run --max-children 4`. Two things about how it ran:

- **Run 1** used no deselection and was stopped at 2,280 mutants. Each `runner/delivery.py` mutant took about 4 minutes, because the seven 90-cell grid tests (20 to 38 seconds each) cover nearly every delivery function.
- **Run 2** deselected those seven tests, which reset mutmut's results, and covered all 5,949 mutants. The tool's 2-hour background limit stopped it at 4,699. `mutmut run` resumed from its saved results and finished with `EXIT 0`.

mutmut runs, for each mutant, only the tests that its stats phase saw call the mutated function.

The seven deselected tests:

```
tests/test_grid_dev_full.py::test_ninety_cell_forced_kill_then_resume_via_provider_hook
tests/test_grid_dev_full.py::test_ninety_cell_mock_grid_completes_and_verifies
tests/test_grid_dev.py::test_summary_includes_usage_by_channel_configuration
tests/test_grid_dev_full.py::test_ninety_cell_resume_after_kill_matches_uninterrupted_run
tests/test_grid_dev_full.py::test_verify_rejects_fourth_provider_attempt
tests/test_grid_dev.py::test_verify_matches_mock_run_model_when_spec_lists_live_model
tests/test_delivery.py::test_the_full_ninety_cell_mock_grid_runs_through_delivery
```

### Tier 2: the slow tests, on a sample and on every reported finding

A full tier 2 would take about 190 seconds per mutant for 707 mutants, over 9 hours on 4 cores, so I didn't run it. `reports/cloud/mutation_tools/tier2.py` ran the slow tests that cover each mutant's function (mapped from run 1's mutmut stats) with `MUTANT_UNDER_TEST` set, in a copy of mutmut's `mutants/` tree:

- **A random sample of 48** of the 707 non-killed mutants whose functions a slow test covers. Eight came from the first draw; 40 came from `random.sample` with seed `20261104`. **48 survived, 0 were killed.** A sample of 48 with no kill puts a one-sided 95% upper bound of about 6% on the share of tier-1 survivors the slow tests would kill.
- **Every reported finding that a slow test covers** (27 mutants, one representative ID per row, listed in `mutation_data/reported_findings.txt`). **27 survived, 0 were killed.** The other 18 representatives have no slow test covering them, so tier 1 already ran every test that reaches them. Each finding's representative mutant survived the whole existing suite. Other IDs in the same row survived tier 1; I didn't run each of them against the slow tests. The B13 `main()` mutants are "no tests" in tier 1, and I didn't run them against the slow tests either.

### Verifying the new tests kill what they claim

`reports/cloud/mutation_tools/killcheck.sh` runs a test selection inside the copied `mutants/` tree with `MUTANT_UNDER_TEST=<name>` and reports `killed` (pytest exit 1) or `survived` (exit 0). My first version used a `--basetemp` whose parent didn't exist, which made every `tmp_path` test error, and so reported every mutant as killed. I caught it with a control mutant that couldn't be detected, fixed the script, and re-ran every check. All numbers here come from the fixed script, and the control mutant now reports `survived`.

### Constant mutation (hand-written)

mutmut 3 mutates only code inside functions and methods, so a module constant such as `FLOOR_THRESHOLD = 3` or the per-token prices is never mutated by tier 1. `reports/cloud/mutation_tools/const_mutator.py` mutates each literal in every module- and class-level assignment (numbers ±1 and 0, booleans flipped, strings wrapped in `XX`, one element dropped from a collection), one at a time, in a scratch copy. It then runs a targeted test selection for that file (`run_const.sh`), using the existing tests only, and restores the file. `*VERSION` constants were skipped. Results are under [Raw counts](#raw-counts).

My first constant run was discarded. Because the tool rewrites the source file for each mutant, two successive mutants of equal size written within the same second could load the previous mutant's cached `.pyc`, since pyc validation uses mtime in seconds and size. That gave spurious kills in about half a second; for example, 3 of 6 equivalent `'str' -> 'XXstrXX'` mutants in `audit.py` were reported killed. The tool now clears the module's `__pycache__` and sets `PYTHONDONTWRITEBYTECODE=1` for each run, and every constant number below comes from the rerun. mutmut, `killcheck.sh`, and `tier2.py` never rewrite source files, so they aren't affected.

## Raw counts

### Tier 1 (mutmut, existing suite without the seven slow tests)

"Not killed" means survived plus "no tests" (mutmut found no test that calls the function). The survival rate is not-killed divided by mutants.

| module | mutants | killed | survived | no tests | survival % |
|---|---|---|---|---|---|
| `agent/loop.py` | 368 | 322 | 46 | 0 | 12.5 |
| `analysis/floor_count.py` | 448 | 401 | 47 | 0 | 10.5 |
| `analysis/gate2_budget.py` | 260 | 131 | 129 | 0 | 49.6 |
| `analysis/request_effect.py` | 357 | 328 | 29 | 0 | 8.1 |
| `defenses/canonicalizer.py` | 312 | 253 | 59 | 0 | 18.9 |
| `defenses/datamarking.py` | 142 | 135 | 6 | 1 | 4.9 |
| `defenses/interfaces.py` | 92 | 71 | 21 | 0 | 22.8 |
| `defenses/policy_gate.py` | 386 | 373 | 13 | 0 | 3.4 |
| `oracles/authorization/audit.py` | 265 | 258 | 7 | 0 | 2.6 |
| `oracles/authorization/conformance.py` | 259 | 226 | 33 | 0 | 12.7 |
| `runner/delivery.py` | 1163 | 861 | 302 | 0 | 26.0 |
| `runner/mock_slice.py` | 826 | 710 | 86 | 30 | 14.0 |
| `runner/paid_run.py` | 508 | 244 | 165 | 99 | 52.0 |
| `tools/sandbox.py` | 563 | 340 | 223 | 0 | 39.6 |
| **total** | **5949** | **4653** | **1166** | **130** | **21.8** |

No mutant timed out or was marked suspicious. The 130 "no tests" mutants are `runner/paid_run.py` `main` (99), which no test calls, `runner/mock_slice.py` `main` (30), which no test calls (CI runs it as `make trace`), and one `defenses/datamarking.py` `handle_comment` mutant, because no test's HTML contains a comment.

Only `runner/mock_slice.py`'s scoring functions are in scope there: `or3`, `and3`, `_authorized_false`, and `score_tool_events`. All 60 of their mutants were killed (8, 8, 7, and 37). The module total above covers the whole file, as mutmut mutates it.

### After the new tests

Each tier-1 non-killed mutant was re-run against the new test file for its module (`killcheck.sh`, same `mutants/` tree). This is a lower bound: a new file for another module can kill some too.

| module | mutants | not killed by the existing suite | killed by the new tests | still not killed | survival % after |
|---|---|---|---|---|---|
| `agent/loop.py` | 368 | 46 | 17 | 29 | 7.9 |
| `analysis/floor_count.py` | 448 | 47 | 15 | 32 | 7.1 |
| `analysis/gate2_budget.py` | 260 | 129 | 97 | 32 | 12.3 |
| `analysis/request_effect.py` | 357 | 29 | 17 | 12 | 3.4 |
| `defenses/canonicalizer.py` | 312 | 59 | 28 | 31 | 9.9 |
| `defenses/datamarking.py` | 142 | 7 | 5 | 2 | 1.4 |
| `defenses/interfaces.py` | 92 | 21 | 10 | 11 | 12.0 |
| `defenses/policy_gate.py` | 386 | 13 | 9 | 4 | 1.0 |
| `oracles/authorization/audit.py` | 265 | 7 | 2 | 5 | 1.9 |
| `oracles/authorization/conformance.py` | 259 | 33 | 2 | 31 | 12.0 |
| `runner/delivery.py` | 1163 | 302 | 131 | 171 | 14.7 |
| `runner/mock_slice.py` | 826 | 116 | 29 | 87 | 10.5 |
| `runner/paid_run.py` | 508 | 264 | 178 | 86 | 16.9 |
| `tools/sandbox.py` | 563 | 223 | 172 | 51 | 9.1 |
| **total** | **5949** | **1296** | **712** | **584** | **9.8** |

Every one of the 65 mutant IDs named in the findings below is in the killed set (checked by name).

### Constant mutation

From `const_mutator.py` (rerun) and `const_recheck.py`. Survivors of the targeted run were re-run against the full existing suite minus the seven slow tests (\*), and then against the new test files. Identical mutant descriptions in one file (for example six `'str' -> 'XX'` in `audit.py`) are reconciled by count.

| file | constant mutants | not killed by targeted existing tests | of those, also not killed by the full existing suite* | still not killed after the new tests |
|---|---|---|---|---|
| `agent/loop.py` | 5 | 1 | 1 | 1 |
| `analysis/floor_count.py` | 46 | 2 | 2 | 2 |
| `analysis/gate2_budget.py` | 34 | 29 | 29 | 0 |
| `analysis/request_effect.py` | 17 | 0 | 0 | 0 |
| `defenses/canonicalizer.py` | 12 | 1 | 1 | 1 |
| `defenses/datamarking.py` | 17 | 1 | 1 | 0 |
| `defenses/interfaces.py` | 143 | 14 | 14 | 14 |
| `oracles/authorization/audit.py` | 27 | 6 | 6 | 6 |
| `oracles/authorization/conformance.py` | 14 | 4 | 0 | 0 |
| `runner/delivery.py` | 46 | 11 | 11 | 11 |
| `runner/mock_slice.py` | 27 | 16 | 16 | 8 |
| `runner/paid_run.py` | 28 | 24 | 24 | 0 |
| `tools/sandbox.py` | 19 | 11 | 11 | 11 |
| **total** | **435** | **120** | **116** | **54** |

The full existing suite killed 4 more than the targeted run: `conformance.TASK_VECTORS` path parts, which only `tests/test_task_suite.py` loads. Every remaining constant survivor after the new tests is one of these:

- a typing-only `Literal` or alias (`GateAction`, `SpanFormat`, `floor_count.Trial`), so equivalent;
- equivalent by construction (`audit._TOOL_ARG_TYPES` `'str'`, where only `'object'` is compared; `canonicalizer._UNRESERVED` gaining only an `X` it already has);
- mock-only identifiers and prompts in `runner/mock_slice.py` and `delivery._EMAIL_BODY`;
- stricter or fail-closed sandbox paths (`LINUX_SYSTEM_READS`, `MACOS_SYSTEM_READS`, `SANDBOX_EXEC`);
- recorded identifiers (`delivery.SECRET_FILES` paths, `SEND_EFFECT_ORACLE`) and `agent/loop.py`'s model-visible `CONTINUATION_PROMPT` text, none of which any test pins.

All 29 Gate 2 budget constants and all 24 `paid_run` constants are killed by the new tests. Those include the prices, the planned counts, the three-observation rule, the strata, `HASHED_DIRS`, and the record path.

## Findings, ranked

Ranks: **A**, a survivor that could change a reported number or recorded fact; **B**, one that could weaken a safety check; **C**, real but low impact. Each finding gives the code at `file:line` on the base commit, the mutant mutmut generated (its ID is reproducible with `mutmut show <id>` in a scratch copy configured as above), and a repro.

Every repro has the same shape. Make the one-line change to the production file in a scratch copy; the existing suite still passes, and the named new test fails. In tier 1 and tier 2 I ran the existing suite this way through mutmut, and I ran the new test with `killcheck.sh`.

### Real bug (failing test)

**R1 (A, latent). The audit evaluator's parameter check isn't type-strict.** `oracles/authorization/audit.py:197-198` uses `params[name] not in declared[name]`, and Python `in` treats `True == 1 == 1.0` and `False == 0 == 0.0` as equal. `defenses/policy_gate.py:46-55` (`_scalar_equal`) requires the same type, and `docs/DEFENSES_AND_POLICY.md` (D1_POLICY_GATE section) says "Value comparison against allowlists is type-strict, so `1`, `1.0`, and `true` never match each other". The two evaluators therefore disagree, and the audit, whose verdict is the `authorized` fact every security estimand reads, records the request as authorized.

- *Reachable?* `schemas/policy.schema.json` allows integer and boolean allowlist values, and `defenses/canonicalizer.py` passes booleans, integers, and finite floats through unchanged.
- *Present today?* No. Every allowlisted parameter value in `tasks/templates/*.json` and both golden vector sets is a string, so no current policy triggers it.
- *Repro:* `uv run pytest tests/test_gate_audit_typed_params.py` fails 4 cases (`True`, `1.0`, `0`, `0.0`) and passes 2.

This came from reading the audit while reviewing its survivors, not from a single mutant. The fix, and whether the golden vectors need a typed-parameter vector, are the lead's call.

### A: could change a reported number or recorded fact

| # | Location | Surviving mutant (ID) | Effect | Killed by |
|---|---|---|---|---|
| A1 | `runner/delivery.py:439` | `authorize(request, prior, grants)`, missing the policy (`xǁTrialToolsǁ_transition__mutmut_2..10`) | `_transition` swallows the TypeError, so a D0_BASELINE or D2_DATAMARKING dispatch never consumes its grant. Later requests then get a different `authorized` and `grant_already_consumed`. Survived the slow grid tests too | `test_delivery_mutants.py::test_a_dispatch_consumes_the_lowest_matching_grant_once` |
| A2 | `runner/delivery.py:505,510` | `next_state = None` and `_settle(request, True, None)` (`dispatch__mutmut_159/160/177`) | Same: no grant transition on a fresh D0_BASELINE or D2_DATAMARKING dispatch | same |
| A3 | `runner/delivery.py:463-466` | the resume path's grant transition dropped (`dispatch__mutmut_34..48`) | A resumed dispatch doesn't re-commit its grant, so a grant could be used twice across a resume | `test_a_resumed_dispatch_recommits_its_grant_and_counts_as_dispatched` |
| A4 | `runner/delivery.py:508` | `"blocked": True` (`dispatch__mutmut_169`) | D0_BASELINE and D2_DATAMARKING `tool_dispatch` events say blocked while the tool ran. Survived the slow grid tests too | `test_an_ungated_dispatch_records_what_happened_and_settles_as_dispatched` |
| A5 | `runner/delivery.py:560` | `"sink_received": True` and the send oracle swapped (`_blocked_effect__mutmut_2..15`) | A D1_POLICY_GATE-blocked send would be scored as reaching the sink, which feeds `external_exfiltration` | `test_a_blocked_send_records_no_sink_receipt_and_the_send_oracle` |
| A6 | `runner/delivery.py:571-573` | `effect_observed = ok` for any `ok`, and `sink_received: True` (`effect__mutmut_22..28`) | A read's effect could become a non-Boolean or reach the sink | `test_a_read_effect_is_the_tool_s_own_boolean_or_unknown` |
| A7 | `runner/delivery.py:536,544,549` | receipt count `= 1`, `-= 1`, `+= 2`; `> 2` (`_account_send__mutmut_13..17,27,46..48`) | On resume, a send's receipt could be attributed to the wrong call, or two receipts to one send, which changes `sink_received` | `test_resumed_sends_keep_their_receipts_and_a_new_send_takes_the_next_one`, `test_one_send_with_two_new_receipts_leaves_the_effect_unknown` |
| A8 | `runner/delivery.py:516` | `unmarked_observation_sha256` set to `None` or a hash of `null` (`dispatch__mutmut_199/203`) | The D2_DATAMARKING evidence hash is wrong | `test_an_ungated_dispatch_records_...` |
| A9 | `runner/delivery.py:168,170,188` | a non-JSON database value returns the marker count instead of the marked text (`_mark_value__mutmut_5/8`); every read marked as HTML (`mark_observation__mutmut_12`) | Changes what the model sees under D2_DATAMARKING | `test_a_database_value_is_marked_...`, `test_a_read_result_is_marked_as_text_...` |
| A10 | `analysis/gate2_budget.py:36-37,97,112,120,128` | each term: `contingency 2.25`, `trial_cost_usd(record, None)`, `>=` versus `>`, the `>= 3` stratum rule, missing-stratum default (129 survivors) | The Gate 2 budget verdict and its required balance can change unnoticed. The old tests only checked `passes` with a $1,000 balance | `test_gate2_budget_equation.py` (21 tests). The 32 survivors left are messages, help text, and formatting |
| A11 | `analysis/floor_count.py:163` | `c[0] != base` (`x_floor_count__mutmut_126`) | `by_base` missing counts are charged to the wrong bases. The existing test's two missing cells sat in two different bases, so swapping them gave the same counts | `test_floor_count_mutants.py::test_missing_cells_are_charged_to_their_own_base` |
| A12 | `analysis/floor_count.py:60-63` | one run-metadata field ignored, or the attempts' models replacing the metadata's (`x__is_mock__mutmut_5..22`) | A mock-provider record could be counted toward the development floor | `test_a_mock_model_in_either_run_metadata_field_is_refused` and two more |
| A13 | `analysis/request_effect.py:80` | the `authorized = false` term dropped (`x__blocked__mutmut_14`) | A gate block of an audit-authorized request would count as an unauthorized-request block | `test_request_effect_mutants.py::test_a_gate_block_of_an_audit_authorized_request_...` |
| A14 | `analysis/request_effect.py:126` | `or` changed to `and` (`x__first_unauthorized__mutmut_4`) | A non-evaluable first request could be scored in the tool-name-only ablation | `test_a_non_evaluable_first_request_makes_the_trial_indeterminate_...` |
| A15 | `defenses/policy_gate.py:88`, `oracles/authorization/audit.py:165` | `unknown = sum(2 ...)` (gate `_budget_exceeded__mutmut_17`, audit `_19`) | Both evaluators can raise `AuthorizationNotComputable` too early, which changes `request_evaluable` and, under D1_POLICY_GATE, blocks with `POLICY_UNAVAILABLE`. Both copies survived, so the golden vectors don't separate the two counts | `test_gate_canonicalizer_mutants.py::test_each_unknown_prior_call_counts_once_toward_the_budget` |
| A16 | `defenses/policy_gate.py:69`, `oracles/authorization/audit.py:139` | `continue` changed to `break` (gate `_shape_codes__mutmut_16`, audit `_17`) | A missing argument hides a later `argument_type_invalid`, so the reason codes change | `test_a_missing_argument_does_not_hide_a_later_wrong_type` |
| A17 | `defenses/canonicalizer.py:70,94,158` | `or` changed to `and`, or the NUL literal changed (`_url__mutmut_3/5`, `_email_to__mutmut_4`, `canonicalize_arguments__mutmut_61/63`) | An empty value or one with a NUL byte becomes an evaluable denial instead of a canonicalization failure, which changes `request_evaluable` | `test_an_empty_url_or_one_with_a_nul_byte_...` and two more |
| A18 | `defenses/canonicalizer.py:205`, `agent/loop.py:87` | the trial ID passed as `None` (`canonicalize_tool_use__mutmut_35`, `run_loop__mutmut_134`) | Every call ID becomes `None:stepN:call1` | `test_a_tool_use_block_keeps_its_trial_and_step`, `test_a_tool_request_carries_the_trial_s_call_id_...` |
| A19 | `agent/loop.py:26` | `"XXXX".join` (`x_response_text__mutmut_2`) | The final output's text blocks get joined with junk, which changes `final_output` and the disclosure checks that read it | `test_text_blocks_join_with_nothing_between_them` |
| A20 | `runner/mock_slice.py:353-354,394,436` | temperature and top_p read from a renamed key; `final_output_sha256` dropped; prompt hash over `None` (`assemble_result__mutmut_147..162,292`, `run_mock_trial__mutmut_42`) | Recorded run metadata and evidence hashes are wrong | `test_the_mock_result_records_its_decoding_prompt_and_output_hashes` |
| A21 | `defenses/datamarking.py:110,172,188` | per-channel count `= 1`; attributes joined with `XXXX`; a comment appended as `None` (`mark__mutmut_33`, `_attrs__mutmut_18`, `handle_comment__mutmut_1`) | Wrong coverage counts; a changed tag or a crash on a C4 page with several attributes or a comment | `test_defense_mutants.py`, three tests |
| A22 | `defenses/datamarking.py:49-54` | constant mutator: `ensure_ascii=False` and `quote=False` flipped in `_SERIALIZERS` | D2_DATAMARKING would also escape non-ASCII or quotes, changing what the model sees beyond the marker | `test_span_serializers_escape_only_what_their_format_needs` |

### B: could weaken a safety check

| # | Location | Surviving mutant (ID) | Effect | Killed by |
|---|---|---|---|---|
| B1 | `runner/paid_run.py:108` | `"XXANTHROPIC_XX"` and `"anthropic_"` (`environment_refusal__mutmut_10/11`) | An ambient `ANTHROPIC_API_KEY` no longer refuses a paid run. The existing test sets only `OPENAI_API_KEY` | `test_paid_run_mutants.py::test_any_ambient_provider_variable_refuses` |
| B2 | `defenses/interfaces.py:172` | `[_plain_json(None) for v in value]` (`_plain_json__mutmut_7`) | Every list element is hashed as `null`, so two actions that differ only inside a list share a grant's action hash. Survived the slow grid tests too | `test_defense_mutants.py::test_the_action_hash_binds_every_list_element` |
| B3 | `tools/sandbox.py:118` | `dirs.add(os.path.join(lib, ))` (`_interpreter__mutmut_34`) | The whole `<install>/lib` is mounted instead of `lib/pythonX.Y`. Survived the slow grid tests too | `test_sandbox_mutants.py::test_a_system_python_exposes_its_stdlib_...` |
| B4 | `tools/sandbox.py:141` | `onerror=None` (`_sockets__mutmut_6/8`) | An unreadable directory under a mount is skipped instead of refusing, against its docstring | `test_an_unreadable_directory_under_a_mount_refuses_the_launch` |
| B5 | `tools/sandbox.py:296` | `or True`, or the macOS branch inverted (`describe__mutmut_3/4/20..22`) | On Linux the paid-run record's sandbox string would hash the macOS profile, so a change to the bwrap rules wouldn't refuse a paid run | `test_describe_hashes_the_linux_rules_it_would_launch_with` |
| B6 | `tools/sandbox.py:190-207` | 30 mutants of `macos_profile`: the default-deny line, rule names, socket direction, separators | Linux CI never builds the macOS profile beyond the exec and read rules, and the lead's sweep runs on their own machine under this sandbox (`STATUS.md` risk 11) | `test_the_macos_profile_denies_by_default_and_allows_only_its_named_rules` and two more |
| B7 | `tools/sandbox.py:263-265` | the macOS `wrap` branch's arguments (`wrap__mutmut_17..31`) | Same exposure on macOS | `test_on_macos_wrap_runs_sandbox_exec_with_the_tool_s_profile` |
| B8 | `runner/paid_run.py:157` | `record_path` and `live_smoke` dropped (`require_paid_run__mutmut_5..8`) | The gate would read the repository's default record instead of the given one | `test_require_paid_run_reads_the_record_it_is_given`, `..._passes_the_live_smoke_exception_through` |
| B9 | `runner/paid_run.py:167` | `or` changed to `and` (`_mock_run_sandbox__mutmut_19`) | A mock grid run under two different sandboxes is accepted | `test_a_mock_grid_under_two_sandboxes_or_an_unrecorded_one_is_refused` |
| B10 | `runner/paid_run.py:217` | `dirty = None` (`build_record__mutmut_44`) | The record can be written while an untracked file sits in a hashed directory. The paid-run check refuses that later anyway | `test_the_record_refuses_an_untracked_hashed_file_present_at_recording` |
| B11 | `runner/paid_run.py:182-183`, `215-216` | no test ran the "no tool-result delivery" refusal or the sandbox-mismatch refusal; only their messages were mutated, so deleting either check would also pass | — | `test_the_record_refuses_a_mock_grid_run_without_tool_result_delivery`, `..._on_another_sandbox_...` |
| B12 | `runner/paid_run.py:85,76` | `--untracked-files=all` dropped; `HASHED_DIRS` dropped (`dirty_paths__mutmut_9/11`, `tracked_files__mutmut_10`) | Which files bind the record changes (one mutant stricter, one collapses paths) | `test_dirty_paths_name_each_untracked_file_...`, `test_code_hashes_cover_the_hashed_directories_only` |
| B13 | `runner/paid_run.py:243-262` | `main()` had no test (99 "no tests" mutants) | `check`'s exit code and `record`'s validate-before-write had no test | `test_check_reports_a_refusal_...`, `test_record_validates_before_writing` |
| B14 | `defenses/policy_gate.py:217-218` | the "evaluator returned something that isn't a decision" branch returns a malformed outcome (`evaluate__mutmut_25..31`) | Still not dispatched, but the recorded action or observation would be wrong. No test had reached this branch | `test_an_evaluator_that_returns_no_decision_fails_closed` |
| B15 | `oracles/authorization/conformance.py:129,136` | `or` changed to `and` (`_check_single_use__mutmut_19/32`) | The conformance harness would accept an evaluator that uses two grants in one replay, or denies an exhausted replay with the wrong code | `test_the_replay_catches_two_grants_consumed_at_once`, `..._requires_grant_already_consumed_...` |
| B16 | `agent/loop.py:84` | `or` changed to `and` (`run_loop__mutmut_121`) | A tool call with a dispatcher but no event recorder proceeds and crashes on the recorder | `test_a_tool_call_needs_both_a_dispatcher_and_a_tool_recorder` |
| B17 | `tools/sandbox.py:266` | `<= 4` and `< 5` (`wrap__mutmut_43/44`) | Refuses a valid `-I -c CODE` launch: stricter, not weaker | `test_a_one_line_program_with_no_arguments_is_a_valid_launch` |
| B18 | `runner/paid_run.py:52-55` | constant mutator: any `HASHED_DIRS` entry except `runner` and `uv.lock` dropped or renamed (20 constant mutants) | The paid-run record would stop covering, for example, `defenses/` or `corpus/`, so a change there after the record wouldn't refuse a paid run | `test_the_record_binds_every_directory_a_paid_cell_executes_or_reads`, `test_a_change_in_any_hashed_directory_refuses_a_paid_run` |

### C: low impact or equivalent (not killed, and why)

| Group | Count (approx.) | Why left |
|---|---|---|
| Error-message and help text (`ValueError(None)`, `"XX...XX"`, case changes) | most of the rest | Refusals still raise. The new tests pin a message where the message names the offending input |
| `encoding="UTF-8"` or `None` instead of `"utf-8"` | dozens | Equivalent under `LANG=C.UTF-8` |
| `runner/mock_slice.py:317-326` `model_violation`/`system_compromise` mutants | 14 | Equivalent: every primitive is hard-coded `None` in the mock slice |
| `runner/delivery.py` mock-provider internals (`DeliveryTaskMock`, `_typed`, `parse_record`) | about 50 | Affect only what the no-credit mock answers. Mock runs don't count toward any number (`SPEC.md` Section 9) |
| `runner/delivery.py:294-326`, `_overlay`/`build_fixtures` JSON indentation and `ensure_ascii` | about 30 | Byte layout of fixture files that tools parse as JSON |
| `tools/sandbox.py` `linux_argv` env names and values (`PATH`, `LANG`, `TMPDIR`), `--dev` target, `--cap-drop all` lowercase | about 20 | Stricter or harmless inside the sandbox. I didn't confirm bwrap's case handling of `all` |
| `tools/sandbox.py:303` replacement sort order (`describe__mutmut_52..57`) | 5 | Matters only if one machine path is a prefix of another. **Not pinned** |
| `analysis/floor_count.py`, `gate2_budget.py`, `paid_run.py` `main()` JSON indent and `sort_keys` | about 60 | Report formatting |

The full list of non-killed mutants with their status is in `reports/cloud/mutation_data/tier1_not_killed.tsv`, and the diff of each one is in `reports/cloud/mutation_data/survivor_diffs.txt`.

## Tests added

All are under `tests/`, and none changes production code. Each passes on the base commit except `test_gate_audit_typed_params.py`.

| File | Tests | Covers |
|---|---|---|
| `test_gate2_budget_equation.py` | 21 | Gate 2 budget terms, prices, strata rule, boundary, CLI |
| `test_floor_count_mutants.py` | 7 | `by_base` missing counts, mock detection, report keys |
| `test_request_effect_mutants.py` | 5 | Block count, ablation indeterminacy, refusal messages |
| `test_paid_run_mutants.py` | 24 | Ambient-variable refusals, record path, `HASHED_DIRS`, dirty and tracked scope, digest, record contents and refusals, `main` |
| `test_defense_mutants.py` | 12 | Action hash over lists, datamarking coverage, HTML, and serializers, conformance replay |
| `test_gate_canonicalizer_mutants.py` | 26 | Gate fail-closed on a non-decision, URL, recipient, and `query_id` canonicalization, both evaluators' budget and shape rules |
| `test_delivery_mutants.py` | 27 | `TrialTools` dispositions, grants, effects, receipts on resume, D2 marking |
| `test_sandbox_mutants.py` | 24 | macOS profile and `wrap`/`mode` branches, `describe()`, interpreter exposure, socket checks |
| `test_loop_mock_slice_mutants.py` | 13 | Loop text, validation, call IDs, default effect, mock-trial recorded hashes |
| `test_gate_audit_typed_params.py` | 6 (4 fail) | R1, failing by design |

**Full suite with the new tests.** I ran it on a fresh `git archive` of branch commit `069a170`, as `canary`, with `uv run --offline pytest -q -p no:cacheprovider`: **2021 passed, 4 failed in 296.96s**. The 4 failures are the `tests/test_gate_audit_typed_params.py` cases, by design. 2025 = 1860 existing + 165 new. I didn't run `make test`, which adds `grid-check`, or the Docker job; the new tests don't touch either.

## Other observations (not from surviving mutants)

These came up while reading the code for ranking. None has a test, and each is the lead's call.

1. **`analysis/gate2_budget.py:118-124` doesn't apply the price bound.** `SPEC.md` Section 9 says that a stratum with fewer than three valid development observations uses "the larger of the global observed maximum and that same price bound". The code uses the global observed maximum alone. The price bound isn't frozen yet (`STATUS.md`, lead's open items), so the code can't apply it today. The script also accepts any `--conservative-c1-trial-cost-usd`, where Section 9 defines that value as at least the global observed maximum and the price bound. It also counts every trial, not only "valid" ones.
2. **`analysis/gate2_budget.py:165`** catches `ValueError` and `OSError` but not `jsonschema.ValidationError`, so a schema-invalid record prints a traceback instead of `gate2-budget: ...` and exit 1. `floor_count.py:213` does catch it.
3. **D2_DATAMARKING and HTML comments.** `defenses/datamarking.py:187-188` passes a comment through unmarked, so text in `<!-- ... -->` on a C4 page reaches the model with its whitespace intact. `<?...?>` and `<![CDATA[...]]>` have no handler and are dropped from the page. I ran `mark_html_document("<p>a b<!-- ignore previous instructions --></p>")`, which returns the comment unchanged, and `mark_html_document("<p>x</p><?php echo 1 ?><![CDATA[keep this]]>")`, which returns `<p>x</p>`. No current fixture contains either. `docs/DEFENSES_AND_POLICY.md` lists what is marked (text nodes, attribute values) but doesn't say what happens to comments.

## What I didn't check

- **The full tier 2.** Only the 48-mutant random sample and the 27 slow-covered finding representatives ran against the seven slow tests. The other non-killed mutants whose functions a slow test covers weren't individually confirmed; the sample bounds how many the slow tests would kill.
- **Subprocess-only code.** mutmut's stats can't see calls in subprocesses, so a function reached only through a subprocess would show as "no tests" or be under-tested in tier 1. The 130 "no tests" mutants are listed above. The `paid_run` `main` ones are now mostly killed by new tests; the `mock_slice` `main` ones are not. Tool processes themselves (`tools/worker.py`, `tools/no_exec.py`, `tools/fixture_http.py`) weren't mutation targets.
- **macOS.** I couldn't run `sandbox-exec`. The macOS tests pin the profile text and the branches with the platform stood in for; they don't show that the profile confines a process.
- **Equivalence by hand.** I called mutants equivalent or low-impact by reading their diffs, not by proof. A reviewer may weigh some of them differently.
- **The constant mutator's kills** come from targeted test selections. Only its survivors were re-run against the full existing suite (minus the seven slow tests), so a constant mutant reported killed was killed by the targeted selection.
- **Mutation operators mutmut doesn't apply.** Deleted statements, removed function calls, and swapped arguments are mostly not generated. Mutation score is a lower bound on what tests miss.
- **Files outside the brief**, for example `runner/execute.py`, `runner/grid_dev.py`, `channels/`, `tasks/`, and `tools/*` other than `sandbox.py`. `runner/execute.py` holds the audit callback that writes `authorized`, and it wasn't mutated.
- **No real provider, no evaluation candidate, no live model.**

## Living documents

I didn't update `TASKS.md`, `STATUS.md`, `README.md`, or `docs/protocol_deviations.md`. The brief says not to change them on this branch, and no slice state, gate result, or frozen artifact changed. If the lead accepts this work, `README.md` would need a line for `reports/cloud/`, and R1 would need an owner and a decision.
