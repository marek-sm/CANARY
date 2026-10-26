# W7-T1 local implementation handoff

AI-assisted engineering implementation against main `029b4eb`, October 26, 2026.
This is review-ready local work, not a scope reacceptance, merged PR, official
run, or human source/oracle sign-off. No pinned protocol text or locked schema
was changed. The PR61 audit F-01 paid-path restriction is unchanged.

## Implemented

- `tasks/coverage-smokes.json` predeclares the exact complement of the five
  development-base templates: invoice-receipt-email (C3),
  maintenance-confirm-email (C3), open-ticket-ids (C2), read-ticket-status (C3),
  service-hours-extract (C4). Each runs clean once under D0_BASELINE,
  D1_POLICY_GATE and D2_DATAMARKING: 15 cells total.
- `runner.coverage` uses the W6-T3 durable runner, its native local tools,
  independent delivery audit, utility oracle, schema validation and stored-event
  result recomputation. It has no live-provider selector. Coverage fixtures are
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
- The locked result schema and indirect scheduler accept C2–C4, not C1. C1
  mock evidence therefore uses separate versioned descriptive JSON, never
  indirect ResultRecords. An eventual official C1 executor/report remains
  separate gated work. Completed mock resume verifies evidence without
  redispatch; incomplete mock runs fail closed and must be preserved/inspected,
  not resumed with possibly duplicate actions.
- Live clean coverage, C1-cost pilots and official C1 runs remain unperformed.
  Paid execution remains blocked by PR61 audit F-01; resolving isolation and
  obtaining the appropriate authorization/gates is separate work.
- Accountable humans still own source/adaptation review, oracle review, W7-T1
  row reacceptance and merge approval. Nothing was pushed, sent or deployed.
