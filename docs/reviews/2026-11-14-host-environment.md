# Lead-side review of the host-environment PR

- **Decision:** [0031](../decisions/0031-merge-on-green.md) items 4 and 5, and [decision 0039](../decisions/0039-gate3-host-environment.md) item 2. The PR is the fourth late Gate 3 input. It names decision 0029 item 6's host environment in `protocol/active.json`, adds its check and the Gate 4 comparison, and regenerates `tasks/freeze.json` for the schema hash.
- **Commit reviewed:** `main` after the host-environment PR merges, with only #108 (the report module, which merged first at 7:21 pm) reverted: `D_G` (decision 0038 item 2, attested from [`2026-11-14-gate3-inputs.md`](2026-11-14-gate3-inputs.md)) plus this PR ([decision 0039](../decisions/0039-gate3-host-environment.md) item 3). The digest below was computed beforehand from that content. The project lead prints the digest on that checkout and attests only if it matches.
- **`paid_run.code_digest`:** `8019e790a3bbbc984301597e6d32741e52077947c779b2e62acf84c0dea4bed7` (`D_H`)
- **Open blocking findings:** 0. The project lead classified every finding on November 14, accepting each class as written below.
- **Safety findings:** none.
- **Method:**
  - Claude, an AI assistant, wrote the PR on November 14. It ran mock-only checks and made no provider or network call.
  - **Disclosure.** While checking that real provenance lines pass `--check-run`, the `fix-reviewer` agent called `runner.execute._record_provenance` outside pytest. That function calls `spend_ledger.cap_or_none()`, which read `~/.canary/spend_cap.json` once. The agent didn't print the value and deleted the scratch run that held it. No key was read, and no paid call was made.
  - **Tests, failing first.** The new tests in `tests/test_gate3_inputs.py` and `tests/test_active_protocol.py` were written before the code. With the host reader injected and `raising=False`, they run against `main` (`16fa6db`): 99 failed, 31 passed, 1 skipped. Of the failures, 93 were `KeyError: 'host_environment'` and the rest `TypeError: generate() got an unexpected keyword argument 'host_environment'`. The feature didn't exist, so no old check could be shown accepting a bad host value.
  - **One `fix-reviewer` round:** 0 blocking findings and 6 minor ones, from 22 mutants. All six are handled below. Its two surviving mutants (checking only the last provenance line, and comparing by strip, casefold, or prefix) now fail new tests: a mismatch in the middle line, and near-miss values such as a trailing space, a case change, a one-character suffix, or a number.
  - **Suites, mock-only:**
    - the full suite on the PR's tree before the minor fixes: 4,136 passed, 74 skipped, 0 failed; and on the final tree: 4,158 passed, 75 skipped, 0 failed;
    - after them, `tests/test_gate3_inputs.py`, `tests/test_active_protocol.py`, `tests/test_whole_tree_n77.py`, `tests/test_c1_w8t3.py`, and `tests/test_task_freeze.py`: 220 passed, 2 skipped;
    - `python -m tasks.freeze --check` exits 0.
  - **Dry run of the step.** It used `16fa6db` with the `W8-T5` PR's diff, this PR, and the report module PR merged locally, in a scratch output:
    - `generate("F20", …)` with decision 0039 item 5's values gives 1,092 official trials;
    - `analysis.active_protocol --check` and `analysis.gate3_hashes --check` pass, host environment included;
    - the sweep spec passes `runner.sweep`'s schedule refusal and schedules 1,080 trials;
    - the C1 spec passes `runner.c1_trial`'s and schedules 12;
    - `ENGINEERING` passes both checks;
    - `make report` exits 0 and leaves the tree clean.
- **Classes (decision 0031 item 5):** a finding is blocking if it could change a score, a count, a gate or readiness result, or a safety property. Non-blocking findings go to their owners by the next freeze, or are stated as limitations. The project lead classified every finding on November 14 as written below: HE-M1 to HE-M6 non-blocking, and no safety finding.

## Scope

| Scope | What was read |
|---|---|
| This PR | In full: `schemas/active_protocol.schema.json` (0.2.0, `host_environment`), `analysis/active_protocol.py` `generate`, `analysis/gate3_hashes.py` (`compute`, `check`, `_host_problems`, `check_run`, `main`), `tasks/freeze.json`, `docs/DATA_CONTRACTS.md`, and the two test files. Read against `runner/paid_run.py` `_machine_facts` and `code_provenance`, `runner/execute.py` `_record_provenance`, `tools/sandbox.py` `describe`, and `tasks/freeze.py` |
| Left out | Everything else, which the November 13 whole-tree review and the Stage 1 review cover for `D_G` |

## Non-blocking findings

| ID | Owner or limitation | Finding |
|---|---|---|
| HE-M1 | Fixed in this PR | `compute()`'s clean-checkout check didn't cover `uv.lock` or `tools/sandbox.py`. `uv_lock_sha256` or `sandbox` could therefore be frozen from uncommitted bytes, and the mismatch would show only at Gate 4. Both are now covered, with a test for each |
| HE-M2 | Fixed in this PR | `--check` and `--check-run` could be given together, and `--check` was then skipped silently. They are now mutually exclusive, with a test |
| HE-M3 | Fixed in this PR | The host comparison used `!=`, so a non-string `1` and `1.0` compared equal. Both sides must now be strings, with a test (`"number"`) |
| HE-M4 | Limitation, stated in the module docstring | `--check-run` fails on a torn last line, while `runner.paid_run.check_code_matches_run` skips one. This fails closed: nothing unread passes |
| HE-M5 | Order, decision 0039 item 3 | `docs/DATA_CONTRACTS.md` links to decision 0039, so this PR opens after decision 0039's PR merges |
| HE-M6 | This file | Decision 0039 item 2 requires this review file in the PR |

## What holds

- **Exact strings.** `active.json` names exactly the five values `runner.paid_run._machine_facts` reads, and every sweep and C1 invocation writes the same five keys to `code_provenance.jsonl`. A real start and stop line, written by `_record_provenance`, pass `--check-run`. Each field is a non-null string compared exactly.
- **`generate()`** refuses an unknown host key instead of dropping it, and a pre-step draft carries five nulls.
- **`--check`** fails at every tier but `STOP` on any of these:
  - a missing `host_environment`;
  - a null field on either side;
  - a non-string;
  - any difference from the machine running it.
- **`--check-run`** fails on any of these:
  - a missing, empty, unreadable, non-JSON, or non-object provenance line;
  - a missing key;
  - a null;
  - any difference, on any line.
- **`tasks/freeze.json`:** only the `schema` group's hash, the common `schema` hash, and the active-protocol schema's own hash change, and `python -m tasks.freeze --check` passes. Nothing else pins the old values.

## Not checked

- No sweep, C1, or paid run exists, so `--check-run` hasn't run on official evidence.
- Linux `bwrap` wasn't rerun. On Linux, `sandbox` reads `bwrap`'s fingerprint, and the step machine is macOS.
