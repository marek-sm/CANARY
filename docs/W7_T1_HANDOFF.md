# W7-T1 local implementation handoff

AI-assisted engineering implementation against main `029b4eb`, October 26, 2026.
This is review-ready local work, not a scope reacceptance, merged PR, official
run, or human source/oracle sign-off. No pinned protocol text or locked schema
was changed. The November 3 note below records what changed since.

## Implemented

- `tasks/coverage-smokes.json` predeclares the exact complement of the five
  development-base templates: invoice-receipt-email (C3),
  maintenance-confirm-email (C3), open-ticket-ids (C2), read-ticket-status (C3),
  service-hours-extract (C4). Each runs clean once under D0_BASELINE,
  D1_POLICY_GATE and D2_DATAMARKING: 15 cells total.
- `runner.coverage` uses the W6-T3 durable runner, its native local tools,
  independent delivery audit, utility oracle, schema validation and stored-event
  result recomputation. Its live path is gated (November 3 note). Coverage fixtures are
  hash-pinned native W6-T1 resources, not single-record attack overlays; the C2
  open-ticket query preserves both matching rows. Noncanonical channels, attack
  conditions and changed records fail closed.
- `corpus.build_c1` builds all four reviewed W6-T2 records as C1 trusted-user-
  prompt variants. Hostile text is the exact canonical source payload in the
  user message, never a tool result. D0_BASELINE only; separate descriptive
  reporting and exclusion from every indirect estimate are explicit.
- C1 order follows decision 0018: c1-002, c1-003, c1-001, c1-004. The M10 prefix
  is the first three; all four are built regardless of tier. ENGINEERING has
  an empty official prefix. Source records and their review attribution remain
  untouched. No new review or eligibility decision is claimed.

## Local evidence and reproduction

Use Python 3.11 and the locked dependencies (`uv sync --locked`). From repo root:

```sh
python -m runner.coverage --check
python -m corpus.build_c1 --check
python -m runner.coverage --out results/development/w7-t1-review
python -m runner.coverage --out results/development/w7-t1-review --resume
python -m runner.c1_mock --out results/development/w7-t1-c1-review
python -m runner.c1_mock --out results/development/w7-t1-c1-review --resume
pytest -q tests/test_w7_t1.py
pytest -q
make corpus-check t1-suite
```

`make w7-t1-build` regenerates the predeclared artifacts;
`make w7-t1-check` checks drift; `make w7-t1-smoke` uses a fresh temporary run.
Never regenerate fixtures merely to conceal an unexpected drift.

On November 3, the ten task variants changed these tasks' prompts and added the
open-ticket C3 and C4 sources, so both evidence summaries were regenerated from a
fresh mock run. The open-ticket C2 source stays two rows. All 15 clean utility checks and all four C1 wiring checks still pass.
The test count below is from the original run.

Validation: the final full suite passed **1784 tests** (including seven new
W7-T1 tests); `corpus-check` reported zero problems and `t1-suite` passed every
listed template/adapter utility check. `git diff --check` passed.

The local cloud run passed 15/15 mock clean utility checks, and every stored
result exactly recomputed from its recorded events. Its compact evidence is
[`evidence/w7-t1/coverage-summary.json`](evidence/w7-t1/coverage-summary.json),
including per-cell result/event hashes. Raw run state is deliberately ignored
under `results/development/w7-t1-cloud`; it contains synthetic per-run canaries
and is not part of the review patch. A fresh run generates different evidence
hashes. The focused tests also verify completed resume cannot invoke a provider
again, and unchanged JSONL records survive resume byte-for-byte.

These are **mock-only engineering checks with zero development/live/official
credit**, not evidence about model resistance or defense efficacy. Coverage
records retain the runner's development split, use a separate corpus root and
manifest, and must never be mixed into official indirect estimates.

## Remaining gates / precise limitations

- C1 variants have a separate **mock-only plumbing executor**, `runner.c1_mock`.
  It exercises each source's canned action through the same bounded agent loop
  and safe fixture tools, with durable fresh synthetic canaries per control,
  secret/customer and local-inbox overlays, and verified fake-sink receipts.
  The generated prompt definitions remain source-faithful; the mock's canned
  tool choices are engineering checks, not observed model choices.
- All four local C1 wiring checks passed, including saved-address/customer
  record sends and local-email forwarding. Compact no-credit evidence is
  [`evidence/w7-t1/c1-summary.json`](evidence/w7-t1/c1-summary.json). Each control
  ran once, not the official three repeats. Authorization is explicitly null;
  no indirect policy verdict or model positive-control success is claimed.
- The locked result schema and indirect scheduler accept C2–C4, not C1.
  (*Superseded November 12:* result schema 1.1.0 has the official C1 record,
  [decision 0034](decisions/0034-c1-result-records.md); the indirect scheduler
  still accepts only C2–C4.) C1
  mock evidence therefore uses separate versioned descriptive JSON, never
  indirect ResultRecords. An eventual official C1 executor/report remains
  separate gated work. Completed mock resume verifies evidence without
  redispatch; incomplete mock runs fail closed and must be preserved/inspected,
  not resumed with possibly duplicate actions.
- Live clean coverage, C1-cost pilots and official C1 runs remain unperformed.
  The tool sandbox resolved audit F-01 ([decision 0023](decisions/0023-tool-sandbox.md)).
  Paid execution now opens only through the paid-run record, once the project lead
  confirms the paid-run condition in `TASKS.md`.
- Accountable humans still own source/adaptation review, oracle review, W7-T1
  row reacceptance and merge approval. Nothing was pushed, sent or deployed.

## November 3, 2026 note

Audit follow-up, mock-only and with no provider call:

- **Evidence.** [`evidence/w7-t1/*.json`](evidence/w7-t1) are regenerated with
  `make w7-t1-evidence` and now record their code commit, code digest,
  uncommitted hashed paths, and tool sandbox, plus the control and manifest hashes.
  `tests/test_w7_t1.py` compares those hashes with current code. Result and event
  hashes aren't compared: a fresh run mints fresh canaries and timestamps, so they
  differ by design. These two files were regenerated before this change was
  committed, so their `dirty_paths` list its files; rerun the target after the
  commit to record a clean tree.
- **Resume.** A completed `runner.coverage` resume verifies its summary and never
  rewrites it, and it refuses a changed summary, sink file, fixture, or canary map.
- **C1.** Every `runner.c1_mock` event carries its time and component versions, and
  each control and the summary name the sandbox and code. `max_steps` is 8, every
  template's bound; the earlier 4 had no recorded reason, and the canned actions
  take at most three steps, so neither bound decides them. The C1 controls'
  `live_blocker` text dropped the same stale F-01 claim, which changes their hashes.
- **The live path.** `python -m runner.coverage --live` (`make coverage-live`) runs
  the 15 cells on a real provider, by hand only, on the project lead's machine
  (decision 0023 item 8). It takes the paid-run gate first, and every cell takes it
  again. `make coverage-verify RUN=<dir>` is the matching check for the smokes, and
  `make raw-manifest RUNS="<dir> ..." OUT=<file>` is the SHA-256 manifest decision
  0025 item 5 names. Neither has run on a real provider, and both still make no
  claim about model resistance or defense efficacy.

## November 5, 2026 note

`main` (decisions 0028 and 0029, the stack-gap fixes, and the sandbox death-signal
fix) is merged into the task variants, mock-only and with no provider call.
`DELIVERY_VERSION` moves to v0.6.0, past both sides' versions (v0.3.0 here, v0.5.0
on `main`). `make w7-t1-build` re-pinned the C1 controls and coverage files to the
merged code, and `make w7-t1-evidence` regenerated
[`evidence/w7-t1/*.json`](evidence/w7-t1): coverage 15 of 15, C1 4 of 4. As on
November 3, they were regenerated before the merge was committed, so their
`dirty_paths` list the merged files; rerun the target after the commit to record a
clean tree.
