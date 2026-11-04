# CANARY stack gaps: the audit's seven fixes

Run 2026-11-04 on branch `cloud/stack-gaps`, from `origin/main` `5f3a52d` (decision 0028), as non-root user `dev` with bubblewrap and a throwaway home (`/home/dev`), after `uv sync --locked`. Each claim is **ran** (executed here) or **read** (code only). No provider call was made, and no key was created or used.

## 1. Answer

All seven are done, each with a failing test written first. Every new test passes. All four final targets pass on `af8193a`: `make test` gives 2656 passed and 1 skipped, with no failures. The expected #71 review-test failure didn't appear. Two limits remain. (a) The `actions/checkout` SHA is one I couldn't verify from here (item 7). (b) Once #66 merges, the Makefile will have two `replay` recipes (item 2).

Ranked by what's left, most urgent first:

1. **Item 7:** confirm `11bd71901bbe5b1630ceea73d27597364c9af683` is `actions/checkout` `v4.2.2` before merging. If it's wrong, CI fails at checkout, so it can't pass silently.
2. **Item 2 vs #66:** `git merge-tree` shows the trace fix merges cleanly. The Makefile then holds two `replay` recipes, and `make` warns and runs this branch's (**ran**, `make -n` on the merged Makefile). #66's owner keeps one.
3. **Item 4, `paid_run_record.schema.json`:** I widened its `code_sha256` path pattern to admit the fallback spec, and left the version at `1.1.0`. The schema isn't locked and no record exists yet. Bumping the version is your call.
4. **Item 3:** `REPORT_MODULE ?= analysis.report` is a placeholder name. `W8-T3` sets it to the module it commits.

## 2. Each item

**1. Fallback model.** A committed `protocol/development_grid_spec_fallback.json` holds the grid spec with `model_id: gpt-6-luna`. A test asserts it differs from the primary spec only in the model, so the one mock preflight the paid-run record checks covers both.
- `runner/grid_dev.py:46` defines `FALLBACK_SPEC`, and `:64` adds `committed_spec`. `:159` refuses any spec but the provider's own, and `:596` makes `live --provider openai` load the fallback spec by default.
- `runner/paid_run.py:83` adds the fallback spec to `HASHED_DIRS`, so the record hashes whichever spec runs.
- The earlier refusals still hold. The primary spec on openai refuses, and so does any `--model` that isn't the spec's.
- Tests (**ran**): 10 new in `tests/test_grid_dev_live.py`. `test_every_fallback_trial_requests_the_fallback_model` builds all 90 trials and asserts each one requests `gpt-6-luna`. A one-trial run through a recording adapter is sent `gpt-6-luna`. The file passes 24.

**2. Replay.** `demo/trace.py:104` `_observation_text` handles every successful tool shape: `text` (`read_file`, `fetch_url`), `rows` (`query_db`), and a bare `ok` (`send_email`). Its body, and the list it feeds (`:200`), are byte-identical to #66's (read on `origin/codex/w7-t5-replay-demo`). I placed the function above `_event_line`, so the files merge without a conflict.
- After the merge there will be two identical definitions, and the later one (#66's) wins.
- `:253` and `:262`: `main` accepts an events file, a trial directory, or a run directory.
- `Makefile:88` adds `make replay RUN=...`. It defaults to `make grid-mock`'s output and refuses in words when there are no records.
- Before the fix (**ran**): 54 of 90 fresh mock-grid traces failed, the same count the audit found.
- Tests (**ran**): 5 in `tests/test_replay_grid.py`.
  - All 90 traces of the session mock grid render.
  - A run directory prints 90 traces.
  - `make replay` runs under `unshare -rn` (no network) with a bare environment (no key variables) and prints 90 traces.
  - With `tests/test_demo_known_traces.py`, 746 passed.
- `git merge-tree HEAD origin/codex/w7-t5-replay-demo` (**ran**) reports one conflict, `README.md`. `origin/main` vs #66 already has that same conflict.

**3. `make report`.** `Makefile:18-23`. It runs `paper-shells` (`analysis.report_shells`), then `python -m $(REPORT_MODULE)`.
- If that module doesn't exist, it exits 2 with a message saying `W8-T3` commits the analysis and report code and only the estimand shells were generated.
- (**ran**) `make report` printed that message and exited 2. `paper/generated/estimand_shells.md` was unchanged.
- Tests: 2 in `tests/test_make_report.py`, both passed. No `W8-T3` code was built.

**4. JSON Schemas.**
- `runner/execute.py:350`: `_load_base` validates against `base_case.schema.json`. A base without `source` is refused before any trial directory is written.
- New unlocked schemas, all at `0.1.0` and not in `CONTRACT_SCHEMAS`:
  - `schemas/schedule_spec.schema.json`, enforced at `runner/grid_dev.py:70` and `runner/sweep.py:82`. `grid_dev validate` now prints a refusal instead of a traceback.
  - `schemas/active_protocol.schema.json`: one field per bullet of `SPEC.md`'s "Active-protocol manifest" list. Null official fields carry a reason. `ENGINEERING` forces empty lists and zero counts.
  - `schemas/manifest.schema.json`: from `docs/DATA_CONTRACTS.md`'s row and `SPEC.md` Section 8's bundle-manifest rule.
- `docs/DATA_CONTRACTS.md:18-20` indexes them.
- Ownership:
  - `W8-T3`'s row owns the `active.json` generator and the `ENGINEERING` validation schema, not the `active_protocol` schema. I didn't add `engineering_validation.schema.json`.
  - `W9-T3` and `W11-T3` own the sanitizer and the frozen manifests, so the manifest schema stays unlocked for them.
  - `runner.raw_manifest` keeps its own decision 0025 format.
- `runner.coverage`'s generated `coverage-*` records (W7-T1) were never `base_case`-valid, because they have no candidate or source. Only a `coverage-` ID in `native-task-coverage-v1` mode skips validation. A test shows a `dev-` base marked that way is still refused.
- Tests (**ran**): 23 in `tests/test_schema_runtime.py`, all passed.
- Two test changes. A stub in `tests/test_grid_live_decoding.py` now accepts the new `provider_name` keyword. The other is a fixture: `tests/test_sweep.py` relabelled `dev-001` as an evaluation base, which the schema refuses (`^eval-`). It now uses `eval-901`, with its renders copied under a temporary fixture root, the way `tests/test_delivery.py:211` repoints `delivery.REPO_ROOT`. No check was weakened.

**5. `compose.yaml`.** It now has `read_only: true` and the two `tmpfs` mounts, beside `network_mode: none`. With `docker compose run --rm mock`, that's the CI docker job's flags exactly. `README.md:31` adds "Docker instructions": the one command, its CI equivalent, and its limits (no bubblewrap or `make` in the image, tools fail inside it, the sweep runs outside it with a null `container_digest`). That covers `SPEC.md` Section 16's promise.
- Tests (**ran**): 3 in `tests/test_compose.py`. Two passed. The container test skips unless `CANARY_DOCKER_IMAGE` is set.
- The committed Dockerfile can't build here (403 on the `ghcr.io` uv blob, the same as the audit). I built a scratch variant that takes uv 0.12.18 from PyPI, with the CA as a build secret. With `CANARY_DOCKER_IMAGE` set to it, compose printed output byte-identical to the CI `docker run` flags (1 passed, as root, because docker needs root here).

**6. Sweep preflight.** `runner/sweep.py:57` `_renders_refusal` loads each base and calls `delivery.pinned_render` for every channel × condition. It refuses with the base, the cell, and the reason before any key is read (`:89`).
- Tests (**ran**): 5 new in `tests/test_sweep.py`, covering a missing file, a changed file, a missing pin, and a missing pin table. Each refuses with 0 adapter calls and no run directory, and a complete corpus passes. The file passes 12.

**7. CI pin.** `.github/workflows/ci.yml:12,33,43` now pin `actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2`.
- Test: `tests/test_ci_pins.py` requires every `uses:` to name a 40-hex SHA with a version comment. It failed on `@v4` and passes now.
- The SHA is unverified (**read**, from memory). Checking it means reading `actions/checkout`, which is outside this session's repository scope.
- It also moves from the floating `v4` tag to `v4.2.2`.

## 3. Final runs (as `dev`)

| Command | Result |
|---|---|
| `make sandbox-check` | 78 passed (49 s). Rerun on `af8193a`: 78 passed |
| `make t1-suite` | exit 0, 20 of 20 `utility=True`. Rerun on `af8193a`: same |
| `make grid-check` | exit 0: grid-validate, 80 passed, mock grid verified `complete: true` (273 s) |
| `make test` on `af8193a` | exit 0: grid-check 80 passed, then `pytest -q` 2656 passed, 1 skipped (the docker test), 0 failed (1545 s) |

The first `make test` (on `ee3f655`) failed: 8 failed and 28 errors. The causes were the coverage records, the paid-run record pattern, and the stub, all fixed above. A targeted rerun once failed `test_verify_evidence.py::test_a_torn_coverage_summary_is_refused_on_resume`. It passed alone and in the final full run, so I can't explain that one failure.

## 4. What I didn't do

- No provider call, key, or `.env`. I didn't read #73's branch or `corpus/evaluation/`, and I made no change to `tools/sandbox.py`, pinned `SPEC.md` text, or the locked schemas.
- I didn't implement `W8-T1` to `W8-T5`, `W9-T3`, `W11`, or `W12`. I didn't add the `engineering_validation` schema, the `active.json` generator, analysis code, or `demo/replay.py`.
- I didn't fix the audit's other findings: `defense_hash` (no longer null: 60 of 60 D1/D2 records in my mock grid carry it, **ran**), `container_digest`, the fixture-server request log, the installed-environment check, or `SPEC.md` §14's Docker limitation.
- The trace header still says `PROVIDER: MOCK` and `CASE: MOCK / EXCLUDED` for every record, including non-mock ones (**read**, `demo/trace.py`). That belongs to `W7-T5` or `W11-T5`.
- I didn't run the macOS sandbox, build the committed Dockerfile, or check CI on GitHub. I opened no pull request and posted no comment.
- `TASKS.md`, `STATUS.md`, and `docs/protocol_deviations.md` are unchanged: no slice state, gate, or freeze changed. `README.md` and `docs/DATA_CONTRACTS.md` are updated.
