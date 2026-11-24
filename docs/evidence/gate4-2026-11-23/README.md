# Gate 4 step: November 23, 2026

This is the Gate 4 step's record (`TASKS.md`, "Gate 4"). The project lead ran it on Monday, November 23, 2026, from 6:38 pm to 6:54 pm Pacific time, outside any AI session, under [decision 0043](../../decisions/0043-gate4-and-demo-day-dates.md).

- **Gate 4 passed on November 23, after two misses.** It was not passed at its November 19 target, nor at 11:59 pm November 20, the time [decision 0042](../../decisions/0042-gate4-late-evidence.md) set. Decision 0043 moved it a second time, after the fact and past Gate 4's own November 22 cutoff, while official records existed and members had raw access. This record never presents either earlier time as met.
- **Every whole-sweep item passed.** All 17 headline comparisons are eligible, and C1 passed.
- **No pass item was relaxed.** No trial and no repair ran after the November 22 data cutoff, and none was needed.
- **This record holds no estimate, count, or rate.** It records only pass or fail lines, exit codes, file hashes, and times.

Result line for `STATUS.md`: Not passed on November 19 or at 11:59 pm November 20; the step ran on November 23 under decision 0043, with every whole-sweep pass item met, all 17 headline comparisons eligible, and C1 passed.

## How it ran

- **Checkout:** `~/Projects/CANARY` on `main` at `ce0fd07` (`ce0fd0761a392f21dcc63b976595c913ae317110`, #121's merge), with no tracked change before or after the step.
  - Its `paid_run.code_digest` is `8db968f8dd84942006d1f33a2588ca7b09ab3dea3ef948fb30d9d16c4cf0419a`, the same as at #122's merge `147e2c6`. Nothing merged after #122 touches the digest's hashed paths.
  - `python -m runner.lead_review check` printed that an attested lead-side review covers this checkout. That review is [`2026-11-22-gate4-scaffold.md`](../../reviews/2026-11-22-gate4-scaffold.md), with 0 open blocking findings, attested on November 22 before any bundle existed.
- **The audit:** `scripts/gate4_audit.py` at commit `ad844b1e7dd7a915c8482f14b73c9f83901a3adb`.
  - SHA-256 `71bf110d284084ba300d5f2c10c13ac80a17943864dd7b3720d0f500379e3ea5`, recomputed before it ran and equal to the review file's value (decision 0042 item 9).
  - `runner.lead_review` binds only `code_digest`, which doesn't cover `scripts/`, so this hash is what binds the audit.
- **The sanitizer:** `analysis/sanitizer.py` v0.2.0, SHA-256 `14880c38fcfb42cacaa56584e7b4efd3fc24ef40615da04a6998c0e2f0e36f65`, recomputed before it ran.
- **The raw runs:** the Gate 3 checkout's folders, `~/Projects/CANARY-wt-gate3/results/raw/sweep/canary-2026-sweep` and `…/c1/canary-2026-sweep`. Both matched the published [raw manifests](../raw-manifests-2026-11-18/README.md) before anything else ran.
- **Machine:** the project lead's Mac, the machine that ran the sweep.
- **No provider call** was made.
- **The AI session** that prepared the commands saw only the pass or fail lines, exit codes, file hashes, and file times. It never opened a run folder, a bundle, or a generated output.

## Checks

Each command's output is in [`checks.txt`](checks.txt), in the order run, which follows decision 0042 item 6 and decision 0036 item 5.

| Step | Check | Result |
|---|---|---|
| 1 | The raw manifests' SHA-256 values against the [manifest record](../raw-manifests-2026-11-18/README.md) | Both equal |
| 1 | `python -m runner.raw_manifest RUN --check MANIFEST`, sweep and C1 | `ok: 1 run(s) match`, both |
| 2 | `python -m analysis.gate3_hashes --check-run RUN --active protocol/active.json`, sweep and C1 | Exit 0, both |
| 3 | `python -m runner.lead_review check` | Attested |
| 4 | The audit's and sanitizer's SHA-256 | Both equal |
| 5 | `python -m analysis.sanitizer --in RUN --out BUNDLE --commit ce0fd07… --protocol-id CANARY-2026-F20`, sweep and C1 | Both bundles written, 6:47 pm |
| 6 | `python scripts/gate4_audit.py --raw … --sanitized … --c1-raw … --c1-sanitized …` | Exit 0, finished 6:48 pm |
| 7 | `python -m analysis.lead_outputs SWEEP --out …` | Exit 0, 6:53 pm |
| 7 | `python -m analysis.report SWEEP --active protocol/active.json --c1-run C1 --out …` | Exit 0, 6:54 pm |

The times are the output files' modification times on the project lead's machine.

### The audit's lines

| Group | Lines | Result |
|---|---|---|
| Whole-sweep items | `verify_sweep`, `sanitized_match`, `missingness`, `model_comparability`, `attempt_histories`, `identifiers`, `resets` | All pass |
| Headline eligibility | 17 `eligible_*` lines: model-violation, system-compromise, clean-utility, and high-risk clean-utility rates for each of the three configurations; the two D2_DATAMARKING differences; the D1_POLICY_GATE residual system-risk difference; and the two clean-utility costs | All pass |
| Sweep overall | `overall_sweep` | `PASS` |
| C1 | `c1_verify`, `c1_sanitized_match`, `c1_model_comparability`, `c1_attempt_histories`, `c1_identifiers`, `c1_resets` | All pass |
| C1 overall | `overall_c1` | `PASS` |

Under decision 0043 item 2, the response would have been `STOP` if any whole-sweep item had failed or every `eligible_*` line had failed. Neither happened.

### Pass items (`SPEC.md` Section 11)

| Pass item | Evidence |
|---|---|
| Scheduled cells complete | `verify_sweep` and `c1_verify`: completeness, schema, schedule membership against the committed specs, duplicates, stored environment, every result recomputed from its events, and replay |
| Missingness | `missingness` (the accounting is complete) and the 17 `eligible_*` lines (each under Section 9's 5% threshold) |
| Comparability | `model_comparability`, `c1_model_comparability` |
| IDs | `identifiers`, `c1_identifiers` |
| Hashes | The raw-manifest checks, and the audit's and sanitizer's SHA-256 |
| Resets | `resets`, `c1_resets` |
| Attempt histories | `attempt_histories`, `c1_attempt_histories` |
| Raw-to-endpoint recomputation | Inside `verify_sweep` and `c1_verify` |
| Sanitized manifests | `sanitized_match`, `c1_sanitized_match`: each bundle is exactly this sanitizer's output for the raw records, its manifest binds every file, and it holds nothing else |
| Generated outputs | Step 7, both exit 0 |
| Host environment (decision 0028 item 9) | `--check-run`, both runs |

## Outputs

None of these files is in Git. They stay on the project lead's machine, outside every checkout. The sanitizer is deterministic, so the release rebuilds each bundle byte for byte into `results/public/`.

| File | SHA-256 |
|---|---|
| Sweep bundle `manifest.json` | `132fe282931a7ce5ea0d996eea04057264da19c16c83bfa6e695256b50bad24b` |
| C1 bundle `manifest.json` | `9767cd632ca1bf911497d78e353abd32780ba908c3cb656ef09750600c743394` |
| `gate4-audit.txt` (the audit's output, copied in `checks.txt`) | `b23361e4bf006a0f583d9e67afd23054a5fe0c8e60249608b69a6cabcc1eb42c` |
| `lead_outputs.md` | `6b7525c3eec282cdcdd030da535d92fc05dfa8de736e0defd00d2938b76c2fcf` |
| `report.md` | `e628795c8f30a44706295dead36fd8d4c4e9f55bdd71f60c6a18e084bb25e572` |

- Each bundle manifest names `produced_by_commit` `ce0fd0761a392f21dcc63b976595c913ae317110`, `protocol_id` `CANARY-2026-F20`, and `sanitizer_version` `sanitizer-v0.2.0`.
- `lead_outputs.md` and `report.md` came from the raw sweep run, which each refuses unless `runner.sweep.verify_sweep` finds it complete. `report.md`'s C1 section came from the raw C1 run, which it refuses unless `runner.c1_trial verify` finds it complete.
- `lead_outputs.md`'s count-only tables are an internal check only. They appear in no public table, number, or claim (decision 0043 item 4).
- No `--events` run and no `--superseded` file was passed, because no repair ran.

## Provisional supported-results decision

The project lead made this decision on November 23, after the step (decision 0043 item 2; `TASKS.md`, lead inputs). It is provisional until `W11-T1` and `W11-T4` merge, by 6:00 pm Wednesday, November 25. The final decision comes by 11:59 pm that day, and `W11-T3`'s last push binds to it.

- **Eligibility.** All 17 headline comparisons are eligible, so none leaves the headline for missing data.
- **The sentence form.** The headline takes `SPEC.md` Section 1's development-floor form, because the predeclared floor applied at Gate 2 (0 of 15 development D0_BASELINE attack cells on the official model configuration; `protocol/active.json`).
- **Supported for the headline:**
  - D1_POLICY_GATE's blocked and escaped counts among evaluable policy-violating requests;
  - residual system compromise under D0_BASELINE and under D1_POLICY_GATE;
  - the change in clean completion under each defense, including the authorized high-risk subset.
- **Reported, not interpreted:** the attacked model-violation counts under D0_BASELINE and D2_DATAMARKING, per channel, and the two D2_DATAMARKING differences with their intervals. No verb of change describes them (`SPEC.md` Sections 1 and 10).
- **C1** appears only in its separate descriptive table and never enters a reported estimate.
- **Claims** stay inside `SPEC.md` Section 1's barred claims, and no count-only table is public.

## What this record states

- **Both misses, and decision 0043** (decision 0043 item 9; decision 0042 items 1 and 8).
  - Gate 4's November 19 target was missed, because `W9-T3`'s sweep, audit, and generated-results pull request, due November 18, never opened.
  - Decision 0042 (DEV-0008) moved the step once, to 11:59 pm November 20. It was missed too, and that once-only exception lapsed.
  - Decision 0043 (DEV-0009), `SPEC.md` Section 11's fourth recorded exception, let the step complete by 11:59 pm November 23. It is the second after-the-fact move. It lands past Gate 4's own November 22 cutoff, with official records in existence and the owners of `W9-T3`, `W11-T1`, and `W11-T4` holding raw access since November 17. This record doesn't claim they haven't read outcomes.
  - Until the audit passed, the project lead saw only what decision 0025 item 12 allows: completeness, schema validity, cost, latency, provider errors, and safety logs. That blinding was by rule: the project lead ran the sweep and could reach the raw records.
  - Moving a pre-registered gate after it was missed weakens what the pre-registration commits to. This record discloses it rather than presenting a time as met.
- **Which items the project lead built, ran, and checked, with no member review** (decision 0042 item 9; decision 0043 items 3 and 9).
  - `W9-T3` had no pull request by decision 0043 item 1's time, 3:24 pm November 22, nor by its outer limit, 1:00 pm November 23: GitHub showed no `W9-T3` pull request at 6:33 pm November 23. `W9-T3` stays Samson's slice.
  - The project lead built, with AI assistance, the sanitizer v0.2.0 and the count-only audit `scripts/gate4_audit.py` ([#122](https://github.com/marek-sm/CANARY/pull/122)).
  - The project lead ran the sanitized sweep and C1 bundles, the audit, and the generated outputs.
  - Their only review is the lead-side review, an AI review whose findings the project lead classified. No member reviewed them. A lead-built sanitizer was checked by a lead-built match (`SPEC.md` Section 9). This adds to decision 0028 item 10's limitation on the project lead's raw access.
- **Limitations from the lead-side review:**
  - **G4-13:** the sanitizer replaces free text with its SHA-256 content address, and the address of a short, guessable text can be reversed by guessing. Every record holds only fictional fixtures (`AGENTS.md`, safety rules), so no real secret or person is exposed.
  - **G4-18:** eligibility uses the report's null rule, so a trial that ended in failure but disclosed a canary counts as observed, not missing. The audit reproduces the report's rule exactly and doesn't change it.
- **The count-only tables leave the public release** (decision 0043 item 4). They size a bias that can favor D2_DATAMARKING (decision 0028 lines 25 and 48). They were computed internally in `lead_outputs.md` and are withheld from the public tables, because they can't regenerate from the sanitized bundle.
- **The frozen `ENGINEERING` fallback had no executor at Gate 3** (`SPEC.md` Section 11; decision 0043 option 3). A failure here would have meant `STOP`.
- **The replay fixes came before decision 0043** (decision 0043 item 7). They were built on November 21, before that record merged. Miles approved [#121](https://github.com/marek-sm/CANARY/pull/121) at 5:39 pm November 22, and it merged at 11:25 pm.
- **The host changed after the sweep** (decision 0042 item 7). macOS updated itself to 27.2.1 on November 18. `analysis.gate3_hashes --check` on this Mac now differs from `protocol/active.json` on `os_build` only. `--check-run` compares the runs' stored provenance, not this Mac, and passed on both runs. No repair ran, so no repair host was needed. `paid_run record` on this host still needs checking before the December 2 live-first gate.
- **DEV-0007.** Decision 0028 item 8's in-sweep integrity check at about 50% and its batch hashes didn't run. The raw manifests anchor the files only from their publication on November 18. Step 1 shows that the files haven't changed since then, not before.
- **`W11-T1` and `W11-T4`** hadn't merged at the step. The decision above is provisional until they merge, by 6:00 pm Wednesday, November 25. The final supported-results decision, by 11:59 pm November 25, records whether they had merged before it.
- **Not checked by the AI session:** the attestation row lives in `~/.canary` on the project lead's machine, so only `lead_review check`'s output above shows it.
- This record claims nothing about what any estimand shows.
