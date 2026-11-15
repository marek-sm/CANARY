# Gate 3 step: November 15, 2026

This is the Gate 3 step's record (`TASKS.md`, "Gate steps"). The project lead ran it on Sunday, November 15, 2026, at 1:37:19 pm Pacific time, at tier `F20`, under [decision 0040](../../decisions/0040-gate3-late-step.md).

- **The step is late.** It missed decision 0039's window, the November 14 step deadline of 11:59 pm, and `SPEC.md`'s November 14 Gate 3 date.
- **Decision 0040 moved the dates after the miss.** It moved decision 0039's window and `SPEC.md`'s Gate 3 date one day, after both were missed, with `STOP` known as the response decision 0039 item 4 would have required. It is `SPEC.md` Section 11's second recorded exception.
- **A `STOP` step was drafted and discarded.** It was drafted on the night of November 14 and never committed or pushed.
- **Nothing has run.** 1,092 is the scheduled count: 1,080 sweep trials and 12 C1 control trials. No evaluation, official, or C1 outcome exists.

Result line for `STATUS.md`: Not passed on November 14; the step ran at `F20` on November 15 under decision 0040, with every pass item met.

## How it ran

- **Checkout:** `~/Projects/CANARY-wt-gate3`, branch `lead/gate3-step`, at HEAD `2b20105` (`2b20105fcbd5f558ebead47719b3f410f2a94dd3`, 1:36:23 pm on November 15).
  - `2b20105` is `340efb2` plus only this driver. `340efb2` is in turn `2cf34f9` (`2cf34f911fc3020cde4f826c018d99d97ca3f81c`, #111's merge) plus only `protocol/paid_run_record.json`. Neither added path is hashed, so the hashed content is `2cf34f9`'s.
  - `code_commit` in `active.json` is `2b20105`, the commit the step ran on (decision 0039 item 5; decision 0040 item 2).
  - Its `paid_run.code_digest` is `e36bd5ba3cf0ea8be80c3c3ca4a8cf43d36e154e26f4d7838d9c799df03a23a8`, the attested final digest, printed in [`checks.txt`](checks.txt).
- **Machine:** the project lead's Mac, the machine the sweep runs on. Automatic macOS updates stay off from this step through Tuesday, November 17, the end of the sweep (decision 0039 item 6; decision 0040 item 4).
- **Driver:** [`gate3_step.py`](gate3_step.py), SHA-256 `3b69ab7cc32971a861fec049b991afe9caa0e484d57aa8a055502f463f748506`.
  - It was committed before it ran (decision 0040 item 3).
  - It calls only committed code (`analysis.gate3_hashes.compute` and `check`, `analysis.active_protocol.generate`, the two schedule refusals, and `runner.schedule.generate_schedule`), with decision 0039 item 5's inputs.
  - It refuses unless `--code-commit` is HEAD, no tracked file differs from HEAD, and it runs in a virtual environment. It writes nothing until the manifest agrees with the recomputed hashes, both refusals are `None`, and the schedules hold `tier_arithmetic`'s 1,080 and 12 trials.
  - It ran from the worktree root with the project's virtual environment as `python docs/evidence/gate3-2026-11-15/gate3_step.py --code-commit "$(git rev-parse HEAD)" --out protocol`.
- **No provider call** was made.

| Output | What it is |
|---|---|
| `protocol/active.json` | The manifest at `F20` |
| `protocol/sweep_spec.json`, `protocol/c1_spec.json` | Built from `active.json` and the protocol sentinel |
| [`checks.txt`](checks.txt) | Each check's command, its output, and its exit code, unedited |
| [`computed-hashes.json`](computed-hashes.json) | `python -m analysis.gate3_hashes` on this checkout, SHA-256 `d1c2b48e6188ec1482367a2908af02d709d119f290c63471b37915e010757534` |
| [`gate3_step.py`](gate3_step.py) | The driver, committed byte for byte |

### Mock grids and paid-run records

- **The first mock grid and record are superseded.** The project lead made them at 9:30–9:32 pm on November 14, after the miss, in this checkout:
  - the mock grid `results/development/grid-mock`, experiment `grid-dev`, mock provider only: 90 of 90 trials, with `verify` complete;
  - events SHA-256 `048629589ea10ea3d743f7348d06509ec3e77d55a9210845830b4e9891d38091`, results SHA-256 `b0f574655a174626964a542bb64fbe966f9066da8659d0ad7b7a4fe6fe796bdf`;
  - `python -m runner.paid_run record results/development/grid-mock --delivery '#61' --sandbox '#64' --request-to-effect '#39'`, committed as `340efb2` at 9:32:10 pm.

  They stay in history.
- **A new pair followed the step,** before any paid sweep or C1 call (decision 0040 item 3; decision 0025 item 12; decision 0029 item 6). The project lead made it on November 15 on `8b313aa`, the commit that records the step in the living documents:
  - the mock grid `results/development/grid-mock-2026-11-15`, experiment `grid-dev`, mock provider only: 90 of 90 trials, with `verify` complete;
  - events SHA-256 `9522889758328bdb02324c28d2d910865d3dd5270979b00a81f8e01de2ee615d`, results SHA-256 `71de7af06d3e26bd15a33d74b05f085a61a5622291c91f6e8f282345c82a94d5`;
  - `python -m runner.paid_run record results/development/grid-mock-2026-11-15 --delivery '#61' --sandbox '#64' --request-to-effect '#39'`, with `recorded_commit` `8b313aa`, committed as `6c26b32` at 2:10:54 pm;
  - `python -m runner.paid_run check` then printed "paid runs may start here".

  The record names the mock grid inside this checkout, so the checkout stays untouched through the sweep.

### Inputs

Every value comes from decision 0039 item 5, a committed freeze, or a committed command. None changed for the late step.

- **Fixed by decision 0039 item 5:**
  - `protocol_id` `CANARY-2026-F20`, `protocol_version` `1.0.0`;
  - `experiment_id` `canary-2026-sweep`, `schedule_seed` `CANARY-2026-sweep-20261114`;
  - protocol sentinel `canary-2026-v1`, `schedule_concurrency` 1;
  - `data_cutoff` `2026-11-22`, `budget_cap_usd` 10.0;
  - the two `accountable_roles` strings;
  - `selection_reason_category` `headcount ceiling`, `active_contributor_count` 6;
  - `container_digest` null (decision 0029 item 6).

  `schedule_seed` keeps its `20261114` date. It was fixed before the step, and decision 0040 item 2 changes no fixed value.
- **From committed freezes:**
  - bases `eval-001` to `eval-020` and `corpus_hash` `5afb8e1e…9859`, from `corpus/freeze.json`;
  - `defense_hash` `519d6ced…e5a9`, from `defenses/freeze.json`;
  - the four common hashes, from `tasks/freeze.json` as #111 regenerated it;
  - the model `claude-haiku-5-5`, the `messages` endpoint, effort `medium`, and `development_floor`, from [`../gate2-2026-11-10/floor-count.json`](../gate2-2026-11-10/floor-count.json).
- **From `python -m analysis.gate3_hashes`** (decision 0038 items 4 and 5, decision 0039 item 2):
  - `analysis_hash` `ebdced2184ea200ef8d2b391123582253d463e7d946a2e147638bef5e5651827` (seed `20261114`);
  - the `ENGINEERING` fallback: `validation_id` `CANARY-2026-ENG-V1`, report generator `dfa713d3…ad5f`, source ledger `dc4fde13…9c41`, plan `d662928f…3058`, schema `f961b665…5755`;
  - `host_environment`.

  Each equals its value in `computed-hashes.json`.

## Results

### `protocol/active.json`

- **Tier:** `F20`. `official_trial_count` 1,092.
- **SHA-256:** `13c32fa066b950f7aa932bf39b55934652a13f172d7fda66e18a50e5c8e3c247`.
- **Spec files:** `protocol/sweep_spec.json` SHA-256 `cd82d167e5072355644cbb971028697e2c2757c67e97d353446ac1320cfda65b`; `protocol/c1_spec.json` SHA-256 `759c8eb03360e2a26b6ba34fb8f46b53fbd14a07dc1580eb0023ee1e0f04f385`.
- **Scheduled:** 1,080 sweep trials, which pass `runner.sweep`'s schedule refusal, and 12 C1 trials, which pass `runner.c1_trial`'s, for 1,092. These are counts of planned trials, not results.
- **Host environment,** read on this machine. It equals `computed-hashes.json`.

  | Field | Value |
  |---|---|
  | `os_build` | `macOS-27.2-arm64-arm-64bit Darwin Kernel Version 27.2.0: Wed Oct 14 23:48:06 PDT 2026; root:xnu-13432.41.4~25/RELEASE_ARM64_T8142` |
  | `python_build` | `3.11.9 (v3.11.9:de54cf5be3, Apr  2 2024, 07:12:50) [Clang 13.0.0 (clang-1300.0.29.30)]` |
  | `sqlite_version` | `3.45.1` |
  | `uv_lock_sha256` | `5abf80158bac28de420bcffa4f742642522481abe5e6f06efc43e00eb77fa6fd` |
  | `sandbox` | `macos-sandbox-exec:tool-sandbox-v0.3.0:10ee91ae313186fa` |

### Checks

Every check exited 0. Each one's output is in [`checks.txt`](checks.txt), in the order run: the two freeze checks, the driver, then the rest.

| Check | Exit |
|---|---|
| `make freeze-check` | 0 |
| `make defense-freeze-check` | 0 |
| The driver, with both schedule refusals `None` and 1,080 + 12 = 1,092 trials | 0 |
| `python -m analysis.active_protocol --check protocol/active.json` | 0 |
| `python -m analysis.gate3_hashes --check protocol/active.json` | 0 |
| `make recheck` | 0 (`PASS`, 0 corpus checks failed) |
| `python -m tasks.freeze --check` | 0 |
| `make paper-shells-check` | 0 |
| `make output-freeze-check` | 0 |
| `make lead-outputs-check` | 0 |
| `make engineering-report-check` | 0 |
| `make report` | 0, and no tracked file changed |
| `paid_run.code_digest` print | `e36bd5ba3cf0ea8be80c3c3ca4a8cf43d36e154e26f4d7838d9c799df03a23a8` |

`python -m runner.paid_run check` reads `~/.canary`, so only the project lead runs it. The project lead ran it after committing the new paid-run record (`6c26b32`), and it printed "paid runs may start here".

### Attested digests

The project lead attested each digest with `python -m runner.lead_review attest`. That command refuses unless the checkout's digest is one the review file names (decision 0039 item 3).

| Digest | Checkout | Review file | Attested (Pacific) |
|---|---|---|---|
| `D_G` `fdbc1c38d6bf334eb40bb00d5799dc9eaa7faacb4d2672f700eb0ece6bceccf3` | `14b9129` (#110's merge) with only #108 reverted | [`2026-11-14-gate3-inputs.md`](../../reviews/2026-11-14-gate3-inputs.md) | November 15, after 1:36:10 pm |
| `D_H` `8019e790a3bbbc984301597e6d32741e52077947c779b2e62acf84c0dea4bed7` | `main` at `2cf34f9` with only #108 reverted | [`2026-11-14-host-environment.md`](../../reviews/2026-11-14-host-environment.md) | November 14, 9:26:29 pm |
| Final `e36bd5ba3cf0ea8be80c3c3ca4a8cf43d36e154e26f4d7838d9c799df03a23a8` | `main` at `2cf34f9` | [`2026-11-14-report-module.md`](../../reviews/2026-11-14-report-module.md) | November 14, 9:26:30 pm |

- Each review file has 0 open blocking findings.
- **Where the times come from.** The `D_H` and final times are the `attested_at` values the project lead printed from the attestation file on the project lead's machine. That file lives outside the repository, so this record can't verify them.
- **The `D_G` time is a bound.** It comes from the time of the local revert commit on its checkout, `9e88615`, which was never pushed.
- **The machine evidence for the final digest's time is commit `340efb2`** (9:32:10 pm). `runner.paid_run record` refuses unless an attested lead-side review of the checkout's digest exists, so the final digest was attested before 9:32:10 pm. No commit bounds the `D_H` time.
- **Erratum: `D_G` wasn't attested on November 14.** Decision 0040's context table says it was, and #111's attested review `2026-11-14-host-environment.md` implies it ("attested from `2026-11-14-gate3-inputs.md`"). The project lead's attestation file showed no `D_G` row on November 15.
  - The project lead then attested `D_G` on its checkout, after `D_H`, the reverse of the order in decision 0039 items 3 and 4.
  - The review it attests was written, and its findings classified, on November 14.
  - The Gate 3 pass item, an attested review of the frozen code's digest with 0 open blocking findings, rests on the final digest's attestation. That attestation was made on November 14.
  - The host-environment review file isn't edited, because `runner.lead_review` rechecks its SHA-256.
- **Reverting #108 on top of #111 conflicted on one file.** #108 added `docs/reviews/2026-11-14-report-module.md`, and #111 edited it. Deleting the file resolved the conflict and completed the revert. `docs/` isn't in `HASHED_DIRS`, so the digest printed `D_H` both before and after. Reverting #108 on `14b9129` for `D_G` applied cleanly.

## What this record states

- **The missed times.** The #111 times come from GitHub:

  | Requirement | Actual |
  |---|---|
  | #111 opened by 7:00 pm (decision 0039 item 1) | 8:16:45 pm (`createdAt` `2026-11-15T04:16:45Z`) |
  | #111 merged through 9:00 pm (decision 0039 item 1) | 9:18:40 pm (`mergedAt` `2026-11-15T05:18:40Z`) |
  | `D_G` attested by 9:00 pm (decision 0038 item 6) | November 15, after 1:36:10 pm |
  | `D_H` attested by 9:00 pm (decision 0038 item 6) | 9:26:29 pm |
  | Step run by 11:59 pm on November 14 (decisions 0038 item 6 and 0039 item 4) | Missed; ran November 15 at 1:37:19 pm |
  | `SPEC.md` Gate 3 date, November 14 | Missed; ran November 15 |

- **Decision 0040.** It moved decision 0039's window and `SPEC.md`'s Gate 3 date one day, after both were missed. It was made with `STOP` known as the response decision 0039 item 4 would have required. It is `SPEC.md` Section 11's second recorded exception; the first is decision 0025's Gate 1 change.
- **The content didn't change.** It was byte-identical to the digests named before the window. `D_G`, `D_H`, and the final digest were each named in their review files before #111 opened, and each matched its checkout when attested.
- **Two rehearsals before the miss.** The step driver was rehearsed twice on November 14, at 6:17 pm and 6:29 pm, in a session scratchpad, and never committed.
  - Both rehearsals used decision 0039 item 5's inputs and seed, and both generated the `F20` schedule: 1,080 + 12 = 1,092.
  - A schedule follows deterministically from inputs already fixed, and it carries no outcome. The step regenerated it from committed code.
- **Made after the miss:**
  - the first mock grid and paid-run record (9:30–9:32 pm on November 14), now superseded;
  - `D_G`'s attestation (November 15);
  - the driver's commit and the step (November 15).
- **The miss was first reported to the project lead as met.** The report was corrected that evening.
- **The discarded `STOP` step.** It was drafted on the night of November 14 and discarded, never committed or pushed.
- **Methods cost.** Moving a pre-registered gate date after it was missed weakens what the pre-registration commits to. This record discloses that rather than presenting the date as met. No check, case, pass item, tier input, seed, or other pre-fixed value changed.
- **Late and out-of-order inputs:**
  - #105, the November 13 whole-tree review, merged at 9:46 am on November 14 as `07e28ed`.
  - `W8-T5`'s output-pipeline freeze record (#109) merged at 7:53 pm on November 14, one day late (decision 0038 item 2). Its owner keeps the slice.
  - The report module (#108) merged at 7:21 pm, before #109 and before `D_G` was attested, though decision 0038 planned it last. Decision 0039 item 3 sets where each digest is attested as a result.
- **The estimand report module** (`analysis/report.py`):
  - the project lead wrote it with AI assistance on November 14, after the November 9 development outcomes were visible and before any evaluation, official, or C1 outcome existed;
  - its only review was the lead-side review;
  - a separate agent wrote its golden tests without seeing the module (decision 0038 item 8).
- **The official C1 executor** was reassigned from `W8-T3` to the project lead on the evening of November 13 (`TASKS.md`, `W8-T3` row).
- **Gate 2 ran on prompt v0.1.1.** #74 (`W8-T1`) then changed the system prompt, so `corpus/c1_controls/manifest.json` changed after Gate 2 without a version bump (N-74-4):
  - its SHA-256 was `9e8ff2462ddaafde4344abf02768d271b280e3ab60bebb5de2786fe4ee716625` at Gate 2's commit `ce6c321`;
  - it is `79c4c22e07751ba2764d1a0f7d5ff5c2ed345908da9c15602804eb8ef5174cc7` here.
- **The output-pipeline freeze** (N-W8T5-1). `analysis.output_pipeline_freeze --check` compares the committed record only with the disk, so this record anchors two values:
  - `output_pipeline_hash` `5579550bca2424ef2f339f713b430a21fd13958830320cd390d0a7353987d9c1`;
  - `test_evidence_hash` `be03c83d02890dcc9bc1bf3b63831c935c601148b4ff2a20a365a5123f8b78a8`.
- **Contributor count:** no disclaimer of the November 9 reply arrived, so `active_contributor_count` stays 6 (decision 0032 item 3).
- **Host environment.** `active.json` names the five values decision 0029 item 6 lists.
  - At Gate 4, `python -m analysis.gate3_hashes --check-run RUN --active protocol/active.json` runs on every sweep and C1 run directory. Any invocation in a different host environment fails it (decision 0039 item 2).
  - The launcher code, `tools/sandbox.py`, is pinned by `code_commit` and by `tasks/freeze.json`'s `sandbox` group.
- **A tool read during review.** While checking #111, a `fix-reviewer` agent's call read `~/.canary/spend_cap.json` once, through `spend_ledger.cap_or_none()`. The value wasn't printed, and no key was read ([`2026-11-14-host-environment.md`](../../reviews/2026-11-14-host-environment.md)).
- **Not checked.**
  - No sweep, C1, or paid run exists, so `--check-run` hasn't run on official evidence.
  - Linux `bwrap` wasn't rerun, because the step machine is macOS.
- This record claims nothing about what any estimand will show.
