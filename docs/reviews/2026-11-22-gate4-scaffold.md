# Lead-side review of the Gate 4 lead scaffold

- **Decision:** [0031](../decisions/0031-merge-on-green.md) items 4 and 5, [decision 0042](../decisions/0042-gate4-late-evidence.md) items 6 and 9, and [decision 0043](../decisions/0043-gate4-and-demo-day-dates.md) items 1 and 3, for #122: the sanitizer v0.2.0 (`analysis/sanitizer.py`) and the count-only audit (`scripts/gate4_audit.py`). Item 1's time is 24 hours after decision 0043 merged, which was 3:24 pm Sunday, November 22, because that is earlier than its 1:00 pm Monday limit. Samson's `W9-T3` had no pull request by then, so the scaffold covers every item that decision 0043 item 3 lists.
- **Commit reviewed:** `147e2c6`, #122's merge into `main` on top of `32f6147` at 9:37 pm November 22. The digest below was computed beforehand from `32f6147` with #122's branch merged, and again on `147e2c6`, with the same result. The project lead prints the digest on `main` and attests only if it matches. #121 and the documentation pull requests of November 22 touch no hashed path.
- **`paid_run.code_digest`:** `8db968f8dd84942006d1f33a2588ca7b09ab3dea3ef948fb30d9d16c4cf0419a`
- **The audit file:** `scripts/gate4_audit.py` at commit `ad844b1e7dd7a915c8482f14b73c9f83901a3adb`, SHA-256 `71bf110d284084ba300d5f2c10c13ac80a17943864dd7b3720d0f500379e3ea5`. `scripts/` is outside the code digest, so this line binds it (decision 0042 item 9). Before running the audit, the project lead recomputes `shasum -a 256 scripts/gate4_audit.py` and refuses on a mismatch.
- **The sanitizer file:** `analysis/sanitizer.py`, SHA-256 `14880c38fcfb42cacaa56584e7b4efd3fc24ef40615da04a6998c0e2f0e36f65`, inside the code digest above.
- **Open blocking findings:** 0. The project lead classified every finding on November 22, accepting each class as written below.
- **Safety findings:** none.
- **Method:**
  - Claude, an AI assistant, wrote both files and their tests on November 19–21, on synthetic and mock records only. No provider call or network call was made, no key was set, and `~/.canary` wasn't read. The work used no official sweep or C1 record.
  - Five `fix-reviewer` rounds: two on the sanitizer alone (November 19–20) and three on the whole scaffold (November 21). The third scaffold round is the scaffold's own pass over decision 0043's changes (decision 0043 item 3), and it found no blocking finding. No round reported mutant counts.
  - Failing-first output for each round's fixes: 110 audit tests failed against the base, where the script didn't exist; 45 of 113 failed against the round-1 audit, and 82 of 137 against the round-2 audit; 17 of 21 sanitizer tests failed against the base sanitizer.
  - Suites, mock-only: `tests/test_gate4_audit.py` (137 passed); `tests/test_sanitizer_events.py` with `tests/test_sanitizer.py` (27 passed); the full suite on #122's branch merged into `32f6147` (4,424 passed, 75 skipped, 0 failed (33m52s)).
  - No member reviewed the scaffold (decision 0043 item 9's disclosure).
- **Classes (decision 0031 item 5):** a finding is blocking if it could change a score, a count, a gate or readiness result, or a safety property. Non-blocking findings are fixed or stated as limitations. The project lead classified the findings below on November 22: G4-1 to G4-9 blocking, fixed or closed as written; G4-10 to G4-20 non-blocking; and no safety finding.

## Scope

| Scope | What was read |
|---|---|
| #122 | In full: `analysis/sanitizer.py`, `scripts/gate4_audit.py`, `tests/test_sanitizer_events.py`, and `tests/test_gate4_audit.py`, against `SPEC.md` Sections 9 and 11, decisions 0025 item 12, 0036 item 5, 0042 item 9, and 0043 items 2 to 4, `analysis/report.py`'s eligibility rule, `runner/sweep.py`'s `verify_sweep`, and the result and event schemas |
| Left out | Everything else on `main`, which the [whole-tree review](2026-11-13-whole-tree.md) and the November 14 reviews cover |

## Blocking findings, fixed or closed

| ID | Finding | Fix and test |
|---|---|---|
| G4-1 | **A canary used as an argument key leaked.** The sanitizer sanitized values but not dictionary keys (sanitizer round 1, B1) | Keys are sanitized; a test with a canary key |
| G4-2 | `disclosure_scan` was hashed twice (sanitizer round 1, B2) | Hashed once, with a test |
| G4-3 | Content-addressing `normalized_args` breaks `analysis/lead_outputs.py --events`'s link to arguments (sanitizer round 1, B3) | Closed by record: decision 0043 item 4 keeps it content-addressed |
| G4-4 | **`resets` would fail every correct three-repeat run.** It grouped trials across repeats, but each repeat writes fresh canaries (scaffold round 1, B1) | Compared within each superblock, with only the database and rendering compared across repeats; a three-repeat pass test and tamper tests |
| G4-5 | **`missingness` checked only two-arm pairs.** It skipped the four-cell datamarking difference and the adapter contrasts, so a case the report marks ineligible passed (scaffold round 1, B2) | Uses the report's per-component rule; tests at the 5% boundary on both sides, an adapter case, and a 40-seed agreement test against `analysis/report.py`'s notes |
| G4-6 | The audit imported more names from `analysis/report.py` than decision 0042 item 9 lists; none computes a rate (scaffold round 1, B3) | Closed by record: decision 0043 item 3 lists the exact names, and a test pins them by set equality and forbids `generate`, `rate`, and `_estimate` |
| G4-7 | `sanitized_match` passed with extra files in the bundle (scaffold round 1, B4) | The bundle must hold exactly the manifest's files; a stray-file test |
| G4-8 | The sanitizer's failing-first log predated its current tests (scaffold round 1, B5); and the 12 C1 trials had no audit | The log was regenerated against the current tests; five `c1_*` checks and `c1_resets` were added, and missing C1 arguments print `c1: fail` |
| G4-9 | **`model_comparability` failed on a null `model_resolved`.** That is normal when a trial's retries run out or a first step is refused by a content filter, so one such trial would fail the whole sweep (scaffold round 2) | Nulls are set aside, and at least one non-null value and exactly one distinct value are required; `defense_hash` may be null only on an infrastructure failure. Tests: retries-exhausted and fixture-build-failed trials pass, and a second model fails |

Two more false failures found while fixing round 1 were also fixed with tests: the `identifiers` check took its sentinel from the protocol version, and `corpus_hash` was compared across bases instead of once per base.

## Non-blocking findings

| ID | Owner or limitation | Finding |
|---|---|---|
| G4-10 | Fixed in #122 | `_safe` caught only `Exception`, so a `SystemExit` message could print; it now catches `BaseException`, with a test |
| G4-11 | Fixed in #122 | Vacuous passes: nothing planned, no records, or a field null everywhere; each now fails, with tests |
| G4-12 | Fixed in #122 | An empty `final_output` became `[REDACTED]`; empty strings stay empty |
| G4-13 | Limitation, stated in the Gate 4 record | A content address of a short, guessable text can be reversed by guessing. Every record holds only fictional fixtures (`AGENTS.md`, safety rules) |
| G4-14 | Fixed in #122 | `missingness` checked more endpoints than the report uses; it now matches the report, and the agreement test reads `report.generate`'s notes |
| G4-15 | Fixed in #122 | `resets` failed on a trial whose fixture build failed; null is allowed only on an infrastructure failure |
| G4-16 | No change | An argument error prints usage and exits 2, which carries only the caller's own arguments |
| G4-17 | Stated in the run steps | Exit 0 doesn't rule out `STOP`: if every `eligible_*` line fails, decision 0043 item 2's `STOP` applies |
| G4-18 | Limitation, stated in the Gate 4 record | Eligibility uses the report's null rule, so a trial that ended in failure but disclosed a canary counts as observed, not missing. The audit reproduces the report's rule exactly and doesn't change it |
| G4-19 | Stated in the run steps | The audit doesn't check raw runs against the raw manifests; `python -m runner.raw_manifest RUN --check MANIFEST` runs first (decision 0042 item 6) |
| G4-20 | No change | The test file's "no digit anywhere" rule was relaxed, because `c1_*` names contain a digit; the line patterns still pin every output line. `model_resolved` nulls are set aside whatever the trial's status, as `runner/execute.py` does |

## What holds

- The audit prints only `<check>: pass|fail` lines, `overall_sweep`, and `overall_c1`, through one emitter. Any exception becomes a bare `fail`. Tests assert that no digit outside the fixed names, no identifier, and no traceback reaches the output (decision 0025 item 12).
- Which `eligible_<comparison>` lines print comes only from the geometry in `protocol/active.json` and the corpus, never from records. The exit code follows `overall_sweep`.
- The sanitizer content-addresses removed text, keeps event payloads deny-by-default, schema-checks both released JSONL files, and puts event identifiers and the raw-evidence digest in the projection check.

## Not checked

- No member reviewed the scaffold, and Samson's `W9-T3` had no pull request to compare.
- The scaffold hasn't run on official evidence. The project lead runs it outside any AI session by 11:59 pm Monday, November 23.
