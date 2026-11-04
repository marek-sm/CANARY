# Cloud integration: `cloud/integration`

- Branch `cloud/integration`, from `origin/main` `519e9af`. Final code commit `72f92bd`; `61de086` and `4f84315` change only a test line and regenerated evidence. Pushed as each milestone landed.
- VM: Ubuntu 24.04, x86_64, kernel 6.18.44, running as root. Installed bubblewrap 0.9.0. `sysctl -w kernel.apparmor_restrict_unprivileged_userns=0` failed with "cannot stat". This kernel has no such key, and `bwrap --unshare-all` works without it. Every command ran as the non-root users `canary` and `canary2` (throwaway homes, so throwaway `~/.canary` ledgers), on uv's Python 3.11.15, with a login environment that holds no token, proxy, `CI`, or provider variable. `tools/sandbox.py` was not touched.
- Made no provider call and created or used no key. Every paid path ran the real SDK and the real `AnthropicMessagesAdapter` over an `httpx.MockTransport` that accepts only `https://fake.invalid` and a fake key. Did not read `corpus/evaluation/` or #73's branch. Opened no pull request, posted no comment, and merged into no other branch.
- An AI did this. It is not the human review SPEC.md requires (decision 0028 item 8).

## Results

| Step | Result |
|---|---|
| 1 Integrate | Five merges, each committed. One was a no-op. Every conflict is listed below |
| 2 `make sandbox-check` | PASS: 78 passed under real bwrap |
| 2 `trace`, `t1-smoke`, `t1-suite`, `w7-t1-smoke`, `corpus-check` | PASS: every target exited 0 |
| 2 `make grid-check` | PASS: 70 passed in 240.80s, then the 90-cell mock grid and its verify |
| 2 `make test` | PENDING: running on `72f92bd` when this was pushed |
| 3 Paid-path rehearsal | PASS: all 19 scripted steps, the record commit, and the killed first grid run behaved as expected. **No false refusal** (see below) |
| 4 Sweep after Gate 3 | Runs now, at a ledger of 116 and of 120, after three code fixes and one new entry point, all pushed here |
| 5 Known fixes | PASS: all 10 fault-injection probes were caught by a failing test |
| 5 Imports | 7 `cloud/mutation` test files and `tests/redteam/` added: 182 passed. 2 mutation files left out |

**Step 2, `make test` timing and hangs.** I ran pytest-timeout (900 s per test) as a bare module with no dist-info, from a scratch directory. Installed in the venv, it made the lock check refuse, correctly. No test reached the timeout, either on its own or under load: the suite ran beside up to three other jobs (the rehearsal, the sweep, and the reference fuzz) on 4 CPUs. The slowest test took 55 s (`test_ninety_cell_forced_kill_then_resume_via_provider_hook`), and the whole suite took 17–23 min. I found no real hang to fix. I can't test the Mac. On the Mac, each tool runs under `sandbox-exec` and verify-and-evidence builds many 90-cell grids, so a slow per-tool start there multiplies across the suite. That is a guess, not a finding.

**Step 2, `LINUX_ABSENCE` probes under real bwrap.** Every probe passed. I logged each outcome: reads of the key file, repository, and server log gave ENOENT, and so did both foreign sockets. Writes to evidence, repository, server log, and tmp gave EROFS. The loopback TCP connection gave ECONNREFUSED. Exec, and the macOS-style denials, gave `PermissionError`. ENETUNREACH never came up, because no probe reached it. No expectation was wrong, and the sandbox didn't fail.

## Step 3: the paid path, rehearsed (one fresh clone of `72f92bd`, user `canary`)

Each step exited 0: `spend_ledger init` and `set-cap 9.5`, mock grid (90), grid verify, `paid_run record`, record committed, `paid_run check`, live smoke through `drive.py runner.live_smoke` (2 requests, utility true), the paid grid with a kill and a resume, grid verify (90/90), grid summary, coverage live (15/15 passed), coverage verify, `raw_manifest` write and `--check`, `floor-count` (15 floor cells, scoring code compared), `gate2-budget` (passes, required balance $4.44, bound $0.0641216, development trials taken from the ledger), `spend_ledger show`, and `paid_run check` again.

- **The kill.** I made each request sleep, then sent SIGKILL once `t0045_dev-004_C3_clean_D2_DATAMARKING_r1` had one durable attempt and no result. Before resuming, I made a docs-only commit. `runner/.DS_Store` and `tools/.DS_Store` had been created at 20 results and stayed in place. The resume finished 90/90. The killed trial stays charged at the trial bound, $0.0641216, and its resume is `new_trial: false`, so the ledger reads 107 of 120: 1 seed, 1 smoke, 90 grid, and 15 coverage.
- **U+2028.** Every reply that calls a tool also carries the scripted text "Calling X. One moment.". All 105 events files hold it raw, and verify, the floor count, and the budget all read them.
- **False refusals: none.** My first rehearsal run stopped at `grid_dev live` and `coverage --live`: "set CANARY_PAID_RUN_ACK=1 …". That was my omission, not a false refusal: it is a deliberate switch, on `main` since before these branches, and it refuses before any key is read. But **no documented paid-step sequence mentioned it**, so the lead would have hit it at the paid grid. It is now documented in `docs/INTERFACES.md` and `README.md`.

## Step 4: can the official sweep run after Gate 3 with no change to hashed code?

**Yes, on this branch, and the changes it needed are made.** The run: user `canary2`, a fresh clone, the ledger seeded to 116 development trials (and separately to 120), mock grid, record, check, then `python -m runner.sweep live --spec … --protocol-version 1.19.0` over the fake transport. The corpus was `eval-001` and `eval-004`, relabelled copies of `dev-001` and `dev-004` with their fixtures at `fixtures/eval-NNN/`, committed before the record as a W8-T2 freeze would commit them. Results: 36/36 trials `completed`, all valid against the locked result schema, with `split` evaluation, `protocol_version` 1.19.0, trial ids holding the `p1-19-0` sentinel, and `channel`, `condition`, and superblock set. The development count stayed at 116, and at 120 the sweep still ran (18/18). `python -m runner.sweep verify` and `check_stored_run` pass.

What blocked it, all fixed here and needing to merge before the November 11 freeze:
1. `check_stored_run` refused every evaluation run, because its mode file reads `{"delivery": true, "split": "evaluation"}` (`runner/execute.py:1689`).
2. It recomputed results under `split="development"`, both in `_result_from_events` (`runner/execute.py:1643`) and in the identity check (`runner/execute.py:1636`).
3. There was no committed sweep entry point. I added `runner/sweep.py` and `tests/test_sweep.py`.

`runner/grid_dev.py`'s `corpus/development` and spec checks apply only to `grid_dev live`, so they don't block the sweep.

What remains, outside code: the evaluation corpus and its `fixtures/eval-NNN/` renders must be committed before the paid-run record, or the gate refuses. A base whose renders are missing ends as a silent `infrastructure_failure`: the first fake run gave 36 of them. Each closed at $0, because no call was made, but each still holds a ledger start. `runner.sweep live` refuses any base whose `split` isn't `evaluation`, but not missing renders. Run `sweep verify` or a mock pass before paying. The spec's source, `protocol/active.json`, belongs to W8-T3; `runner.sweep` takes an explicit spec file and protocol version until that generator exists.

## Every conflict and how I resolved it

1. **`lead/one-call-price-bound`**: already on `main` as #70 (`519e9af`). `git merge` said "Already up to date", so there is no commit.
2. **`lead/restore-strength`** (`fa04b14`): no conflicts.
3. **`lead/paid-gate-hardening`** (`fbaabde`, plus `447f891`):
   - `README.md`, grid paragraph: kept paid-gate's spend-ledger sentences. Replaced its `gate2-budget … C1_COST= RESERVE=` sentence with main's price-bound form, without `DEV_TRIALS`, adding that the budget counts development trials from the ledger.
   - `docs/INTERFACES.md`, paid gate: took paid-gate's bullet list and paragraphs, and added the bullet "the provider declares decision 0026 item 3's one-call setting, on the live smoke too". Added that the budget counts development trials from the ledger and that the ledger's rates are `analysis/price_bound.py`'s.
   - `analysis/gate2_budget.py`: main's `price_bound` imports, plus `paid_run` and `spend_ledger`. In `main()`, paid-gate's `check_code_matches_run` runs first, then main's `load_run` and `check_complete_grid`, then `evaluate_budget` with tier, defense, C1 pilot, `development_trials_used=development_trials_used()` (the ledger, `:260`), and `price_bound_usd=_price_bound_used()` (`:249`). `_price_bound_used` reads the bound at call time, so a raised bound is re-evaluated, and raises if the module is missing, with no typed fallback. The report adds `price_bound_source`, `development_trials_source`, and `code_check`. `--development-trials-used` is gone, and so is `DEV_TRIALS` in `Makefile:76`.
   - `runner/spend_ledger.py:52-70`: every rate, the largest request, and `TRIAL_BOUND_USD` now come from `analysis/price_bound.py`, and the TODO is removed. The bound is $0.0641216, up from $0.0585216.
   - `runner/paid_run.py` docstring: kept both bullets. `ONE_CALL_SETTINGS` sits after `UNLOCKED_TOOLS`. `require_paid_run` merged automatically: the refusal check, then the one-call check.
   - `tests/test_tool_sandbox.py`: paid-gate's `gate.record()` form, plus main's one-call test.
   - Tests updated: the bound-equality test in `test_spend_ledger.py`; `BUDGET_ARGUMENTS` in `test_paid_run_gate.py`; a missing bound module now refuses; `test_grid_usage.py` refuses both typed flags; `test_gate2_budget.py` uses a stand-in ledger and adds a test that counts from the ledger. The fake paid providers declare `ONE_CALL_SETTINGS[0]`.
4. **`lead/verify-and-evidence`** (`43b2b24`, plus `e035ea6` and `cf1e219`):
   - `README.md`: verify's floor-count paragraph plus HEAD's scoring-digest sentence; verify's grid paragraph up to its budget sentence, then HEAD's ledger and budget sentences; verify's coverage, raw-manifest paragraph.
   - `analysis/floor_count.py`: `from runner import execute, paid_run`. `analysis/gate2_budget.py`: HEAD's imports plus `ValidationError`.
   - `runner/delivery.py:78`: `DELIVERY_VERSION` was v0.4.0 (restore) and v0.3.0 (verify, task-variants). Set to **v0.5.0**. The other version constants don't collide.
   - `runner/execute.py`: `execute_trial` finishes the ledger, then commits `_result_from_events(…, split=, protocol_version=, analysis_role=)` (`:986`). `_result_from_events` (`:989`) takes them keyword-only and passes them to `assemble_result`.
   - `runner/grid_dev.py`: `live_run_refusal(root, spec, out_dir) or execute.raw_evidence_refusal(out_dir)`.
   - `runner/live_smoke.py`: kept HEAD's model check and `paid_run_refusal(live_smoke=True)`, and verify's raw-evidence check, which now runs first (`:82`). All of them run before the key is read.
   - `tests/test_floor_count.py`: both imports, and verify's real-run test body. That body's `run_schedule` writes its own provenance, so HEAD's hand-written line was dropped.
   - Interactions with the paid gate, all fixed in `e035ea6`:
     - verify's recompute refused the gate fixture's grid, because it was copied without `env/`. `tests/conftest.py:115` now ignores only `*.sock`.
     - `load_run` rightly refused hand-made `live_grid` records. They are now a real, recomputable, real-model-named 90-cell run (`tests/conftest.py:81`).
     - `_check_mock_run` runs the record's named checks before `verify_grid_run` (`runner/paid_run.py:574`), so each refusal still says which check failed.
     - Two gate tests first assert the recompute refuses their hand edit, then stub it to test their own check (`tests/test_paid_run_gate.py:136,527`).
     - `spend_ledger.read` split at U+2028 (`runner/spend_ledger.py:125`).
     - c1 evidence keeps verify's three code keys (`runner/c1_mock.py:115`).
     - verify's fakes declare the one-call setting, and its coverage-live fakes get a stand-in ledger.
5. **`lead/task-variants`** (`f164c48`, `0c483c1`, `4f84315`):
   - `TASKS.md`: kept the workspace row from HEAD (decision 0028 item 7's wording) and the variants row from task-variants.
   - `DELIVERY_VERSION` stays v0.5.0.
   - `corpus/c1_controls/manifest.json` regenerated by `make w7-t1-build`, and `docs/evidence/w7-t1/*.json` by `make w7-t1-evidence` on a clean tree. The evidence was regenerated again at the final code.
   - Interaction: verify's `defense_hash` read defense sources through `delivery.REPO_ROOT`, which the variants test repoints at a fixture tree. 11 cells ended `infrastructure_failure`. The hash now reads from the code root, `registry.ROOT` (`runner/delivery.py:145`); production values are unchanged.

## Code changes beyond merging

- `runner/execute.py:1636,1643,1689-1704`: a sweep's results verify under their own split and labels. Regression test: `tests/test_spend_ledger.py:410`.
- `runner/sweep.py`, a new entry point with `live` and `verify`, and `tests/test_sweep.py` (5 tests, 7 cases).
- `runner/delivery.py:145`; `runner/paid_run.py:574`; `runner/spend_ledger.py:52-70,125`; `analysis/gate2_budget.py:249-296`; `runner/c1_mock.py:115`; `runner/live_smoke.py:82` (all above).
- Docs: `README.md` and `docs/INTERFACES.md` (the sweep, `CANARY_PAID_RUN_ACK`, the ledger count).

## Step 5: the known fixes

I broke each fix in a scratch clone, and each break was caught by a failing test:
- the request-log surface and the step-limit disclosure (`test_scoring_surfaces.py`);
- the audit's type-strict parameters;
- floor_count dropped from the scoring digest (threshold edit refused);
- comparing `code_digest` instead of the scoring digest (the runner fix across a resume, the November 7 close);
- canaries bound to fixtures;
- the raw-response replay, and `final_output` alone;
- the `started_fields` claims, comparing only the first;
- the server log compared by count, not content.

**Reference scorer** (run from a scratch clone, not added). The repros were 38, the fuzz was 600 examples at seed 7, and the golden vectors were 238 with 1 known grant-choice difference. The fuzz found 0 repo invariant violations.

These are explained by decision 0028:
- malformed endings keep a null disclosure and null action facts;
- `max_steps` has no `final_output` event;
- a canary in cut-off text counts;
- a filtered reply's unrecorded block leaves `requested` null;
- `to` is lowercased (Finding 7);
- Finding 6's utility reading.

**Not covered by 0028:**
- D0_BASELINE and D2_DATAMARKING calls record `disposition_observed` null where the reference has true: 192 of 600 fuzz examples, and 17 of 38 repros.
- `display_label` is always null.

Neither changes an endpoint.

## Still wrong or open, ranked

1. A sweep with missing evaluation renders becomes silent infrastructure failures, with no preflight refusal (step 4).
2. Measurement code changed here (`runner/execute.py`, `runner/delivery.py`, `runner/paid_run.py`, `runner/sweep.py`) has had no human review. It has to merge before the mock grid and the record.
3. The expected failure, `test_the_task_variant_vectors_have_their_independent_review`, still fails, as briefed. It needs the human review.
4. `disposition_observed` and `display_label` differ from the reference scorer, and SPEC leaves both undecided.
5. Two `cloud/mutation` files were left out, because they import pre-integration names: `test_gate2_budget_equation.py` (`PLANNED_C1_TRIALS_F20`) and `test_paid_run_mutants.py` (`tests.test_tool_sandbox._record`). Their docstrings, and those of the imported files, cite `reports/cloud/*.md` files that aren't on this branch.
6. `CANARY_PAID_RUN_ACK` is a manual environment switch that isn't in `TASKS.md`'s paid-step sequence.

Living documents: I updated `README.md` and `docs/INTERFACES.md`, and resolved the `TASKS.md` merge conflict. No slice state changed, because no acceptance evidence exists. `STATUS.md` and `docs/protocol_deviations.md` don't apply: there was no gate result and no freeze. There is no `LEAD_TODO.md`.
