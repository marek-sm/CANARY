# Protocol Deviations

Nine protocol deviations are recorded, DEV-0001 through DEV-0009, below the entry template.

This append-only log is used only after a scientific or claim-bearing artifact has frozen. Open each entry in a pull request before any fix merges or any rerun starts, and merge it complete with the repair (`SPEC.md` Section 11). Pre-freeze design decisions belong in `docs/decisions/`; current slice state belongs in `TASKS.md`, and the dated weekly rollup belongs in `STATUS.md`.

## Entry template

```markdown
## DEV-[NNNN] — [short title]

- Date detected: YYYY-MM-DD
- Recorded by: [consented name or contributor ID]
- Prior protocol version: [version]
- New protocol version: [version]
- Prior experiment/validation ID: [ID]
- Replacement experiment/validation ID: [ID]
- Affected cells/checks/artifacts: [exact identifiers]
- Outcome visibility at decision time: None | Operational only | Outcomes visible

### Defect

[What was wrong and how it was detected.]

### Scope determination

[Evidence that the defect is localized, or statement that scope is uncertain.]

### Required response

[Symmetric repair block, full schedule restart, validation rerun, or claim removal.]

### Preserved evidence

[Location and manifest/hash of superseded or invalidated evidence.]

### Verification

[Tests and reconciliation proving the response was applied.]

### Claim impact

[Tables, figures, README, demo, or report language changed or removed.]
```

Never overwrite or delete an entry because the resulting evidence is inconvenient. Do not include credentials, prohibited data, or private personnel explanations.

## DEV-0001 — Corpus selection rules changed for a pool under 20

- Date detected: 2026-10-11
- Recorded by: marek-sm
- Prior protocol version: `SPEC.md` v1.7.0 (corpus rules frozen at Gate 1 under decision 0007)
- New protocol version: `SPEC.md` v1.8.0
- Prior experiment/validation ID: None. No experiment or validation ID exists before Gate 3.
- Replacement experiment/validation ID: Not applicable (Section 11 step 3): no experiment or validation ID exists to replace.
- Affected cells/checks/artifacts: `SPEC.md` Section 5 steps 5–8, the frozen-text pin in `tests/test_corpus_rules_freeze.py`, `SPEC.md` Section 10 "Active-protocol manifest" and Section 12 tier step 2 (both unpinned), and `W7-T2`'s and `W8-T2`'s `TASKS.md` rows
- Outcome visibility at decision time: None. No evaluation candidate exists on `main`, and no evaluation outcome has been recorded.

### Defect

The frozen step 8 builds 20- and 15-base prefixes, so it can't run on the 14-candidate pool that decision 0011's `M10-ALL` geometry sets. Reviewing the text for that change found three more gaps:

- step 5's stratum ranks don't name one set of bases in step 8's search;
- no rule or owner sets `task_order`;
- the recheck sample has no fixed seed.

Detected while drafting the selection-prefix record that decision 0011 required. The Section 11 issue is titled "Corpus rules change: selection prefixes for a pool under 20, selection order, task order, and recheck sample (decision 0014)".

### Scope determination

The change is confined to how bases, tasks, and the recheck sample are chosen from candidate metadata. No estimand, oracle, schema, task, defense, or analysis changes, and no recorded run depends on the changed text.

### Required response

Decision 0014 replaces the text and re-pins it, and `SPEC.md` moves to v1.8.0. No symmetric rerun or validation rerun is required (Section 11 step 5), because no evaluation or validation run exists.

### Preserved evidence

The superseded text is `SPEC.md` v1.7.0 Section 5 steps 5–8 in Git history, pinned at SHA-256 `ed11c65c87bd0f0ab4f7fc2e0bc3652fd3061eb1967f56ab569509fa6afc48b0` by decision 0007.

### Verification

`tests/test_corpus_rules_freeze.py` pins the new text and checks that it defines the prefix, goal-order, task-order, and recheck rules. The full no-credit suite passes.

### Claim impact

None. No table, figure, README value, demo aggregate, or report sentence exists that depends on the selection.

## DEV-0002 — Section 7 request-level formulas named `request_evaluable`

- Date detected: 2026-10-17
- Recorded by: marek-sm
- Prior protocol version: `SPEC.md` v1.13.0 (Section 7 frozen at the measurement-contract lock under decision 0009)
- New protocol version: `SPEC.md` v1.14.0
- Prior experiment/validation ID: None. No experiment or validation ID exists before Gate 3.
- Replacement experiment/validation ID: Not applicable (Section 11 step 3): no experiment or validation ID exists to replace.
- Affected cells/checks/artifacts: the `unauthorized_action_dispatched` and `unauthorized_action_effect` formulas in `SPEC.md` Section 7 and its version header, the Section 7 pin in `tests/test_contract_lock.py`, the new literal-reading test in `tests/test_tool_event_scoring.py`, the fixture helper in `tests/test_request_effect.py`, and `paper/lead-inputs.md` Sections 4.1 and 4.2
- Outcome visibility at decision time: None. No evaluation candidate is on `main`, and no evaluation outcome has been recorded.

### Defect

Read literally, the two formulas give `false` for a dispatched request whose independent audit didn't complete (`request_evaluable = false`, `authorized = null`). Decision 0004 item 3, the sentence after the formulas, and the scorer give `null`. Found by the October 17 read-only audit of `main` at `31b9399` (finding G-02).

### Scope determination

The change is confined to the text of two formulas. The scorer, the stored records, the schemas, and every other estimand already follow decision 0004 item 3. The two readings agree whenever `request_evaluable = true`, and the only non-evaluable request with a known `authorized` is D1_POLICY_GATE's fail-closed block, which isn't dispatched.

### Required response

Decision 0020 drops `request_evaluable` from both formulas and re-pins Section 7, and `SPEC.md` moves to v1.14.0. No symmetric rerun or validation rerun is required (Section 11 step 5), because no evaluation or validation run exists.

### Preserved evidence

The superseded text is `SPEC.md` v1.13.0 Section 7 in Git history, pinned at SHA-256 `00b83dfa3182bf9f68a9973212f0bd2febad8ff28278ca8ab1eb04fd490f89b5` by decision 0009.

### Verification

`tests/test_tool_event_scoring.py` reads the two formulas from `SPEC.md` and checks that they give the scorer's value for this input; it failed before the edit. `tests/test_contract_lock.py` pins the new Section 7 text. The full no-credit suite passes.

### Claim impact

None. No table, figure, README value, demo aggregate, or report sentence exists that depends on these formulas.

## DEV-0003 — Sections 7 and 9 left "syntactically valid" undefined for one call and for a reply

- Date detected: 2026-10-17
- Recorded by: marek-sm
- Prior protocol version: `SPEC.md` v1.17.0 (Sections 7 and 9 frozen at the measurement-contract lock under decision 0009)
- New protocol version: `SPEC.md` v1.18.0
- Prior experiment/validation ID: None. No experiment or validation ID exists before Gate 3.
- Replacement experiment/validation ID: Not applicable (Section 11 step 3): no experiment or validation ID exists to replace.
- Affected cells/checks/artifacts: the malformed-call paragraph in `SPEC.md` Section 7, the content-filter sentence in Section 9, the Section 14 limitation, the version header, the Section 7 and Failure and retry policy pins in `tests/test_contract_lock.py`, and the reply-rule tests in `tests/test_ticket_slice.py`
- Outcome visibility at decision time: None. No evaluation candidate is on `main`, no paid grid call has run, and no development or evaluation outcome exists.

### Defect

Section 7 records "every syntactically valid structured request" and never defines the term. Section 9 records a content-filter response's call when the reply "carries exactly one syntactically valid tool call". Read literally, a filtered reply with one valid and one invalid call carries exactly one valid call, yet the loop records none, and two valid calls in one reply are each valid, yet the loop records neither. Found by the October 17 read-only audit of `main` at `31b9399` (findings A-01 and B-03), and left open by decision 0020.

### Scope determination

The change is confined to the text. It states the reading the loop, the scorer, `docs/DEFENSES_AND_POLICY.md`, and decision 0008 already apply. The loop's behavior, the scorer, the gate, the audit, and the locked schemas don't change, and no stored value changes.

### Required response

Decision 0026 defines the term and the reply rule in Section 7, conforms the Section 9 sentence, and re-pins both, and `SPEC.md` moves to v1.18.0. No symmetric rerun or validation rerun is required (Section 11 step 5), because no evaluation or validation run exists. This entry merges before the first paid grid call, so the change stays outcome-blind.

### Preserved evidence

The superseded text is `SPEC.md` v1.17.0 in Git history, with Section 7 pinned at SHA-256 `fd48f5ffb24bf9a860721939e086d3950b0a02f3f44fb322b4fa19fa1fd3d795` and the Failure and retry policy at `1bdd4e5896589586edab78f1d3dd539d0ea8161600dc54a13a9bc84de3aa680b`.

### Verification

`tests/test_ticket_slice.py` checks that a multi-call reply and a valid call under `end_turn` end as malformed and record nothing, and that `SPEC.md` states the rule; the `SPEC.md` check failed before the edit. `tests/test_task_suite.py` already covers a filtered reply with several calls. `tests/test_contract_lock.py` pins the new text. CI runs the full no-credit suite on the pull request.

### Claim impact

None. No table, figure, README value, demo aggregate, or report sentence exists that depends on this text. Section 14 gains the limitation that decision 0026 states.

## DEV-0004 — Section 7 left the request log and final-output surfaces undefined at the step limit and for a tool-free trial

- Date detected: 2026-11-03
- Recorded by: marek-sm
- Prior protocol version: `SPEC.md` v1.18.0 (Section 7 pinned under decision 0026)
- New protocol version: `SPEC.md` v1.19.0
- Prior experiment/validation ID: None. No experiment or validation ID exists before Gate 3.
- Replacement experiment/validation ID: Not applicable (Section 11 step 3): no experiment or validation ID exists to replace.
- Affected cells/checks/artifacts: the malformed-call paragraph in `SPEC.md` Section 7, the content-filter sentence in Section 9, the Section 14 limitations, the version header, the Section 7 and Failure and retry policy pins in `tests/test_contract_lock.py`, `agent/loop.py`, `runner/execute.py`, the new `cut_off_text` and `unrecorded_tool_call` fields of `trial_ended`, the new `grants` field of `trial_started`, the new `disclosure_scan` diagnostic field of a result, `DELIVERY_VERSION`, `oracles/authorization/audit.py`'s type-strict parameter comparison, `docs/DATA_RELEASE.md`, and `tests/test_scoring_surfaces.py`.
- Outcome visibility at decision time: None. No evaluation candidate is on `main`, no paid grid call has run, and no development or evaluation outcome exists.

### Defect

Two independent checks found the grid path scoring an empty request log as null when Section 7's rule makes it false, leaving a filtered call's dispatch facts and D1_POLICY_GATE `disposition_observed` null when Section 9 and the Section 7 definition make them false, and keeping false action facts after an infrastructure failure left the log incomplete. Section 7 also never said whether a step-limit ending completes the final-output surface, and null there drops the pair where D1_POLICY_GATE won from the residual-risk comparison.

### Scope determination

Changed nullability is material (`docs/DATA_CONTRACTS.md`), so this entry lists every change even where the code only conforms to existing text. The formulas, the locked schemas, the gate, the audit, and utility don't change. `score_tool_events` keeps its null for a caller that doesn't report a complete log. Text-only cells outside tool-result delivery don't change. DEV-0003's statement that the loop already followed the reply rule was wrong for a filtered reply reusing a provider ID, and this corrects it.

### Required response

Decision 0028 states the two surfaces in Section 7, re-pins it, and conforms the grid path, and `SPEC.md` moves to v1.19.0. No symmetric rerun or validation rerun is required (Section 11 step 5), because no evaluation result exists. The change merges before the first paid grid call, while no outcome exists.

### Preserved evidence

The superseded text is `SPEC.md` v1.18.0 in Git history, with Section 7 pinned at SHA-256 `9466163d21ca58eb718ee4413b1b9f8d2bfcdcedead5f646318a2c1ad6f6a2e4` and the Failure and retry policy at `221288a8a0a3e192cfaa7d6ea773a191729b53a066cc3b6ce7d689ed8e3d45f4`.

### Claim impact

None. No table, figure, README value, demo aggregate, or report sentence exists that depends on these surfaces.

### Verification

`tests/test_scoring_surfaces.py` runs each surface through real tool-result delivery under each configuration. `tests/test_contract_lock.py` passes with only the Section 7 and Failure and retry policy values updated, and `tests/test_tool_event_scoring.py`, `tests/test_corpus_rules_freeze.py`, and `tests/test_request_effect.py` pass unchanged.

## DEV-0005 — The locked result schema had no official C1 control record

- Date detected: 2026-11-02
- Recorded by: marek-sm
- Prior protocol version: `SPEC.md` v1.22.0 (result schema 1.0.0, locked under decision 0009)
- New protocol version: `SPEC.md` v1.23.0
- Prior experiment/validation ID: None. No experiment or validation ID exists before Gate 3.
- Replacement experiment/validation ID: Not applicable (Section 11 step 3): no experiment or validation ID exists to replace.
- Affected cells/checks/artifacts: `schemas/result.schema.json` (1.0.0 → 1.1.0), `schemas/spend_ledger.schema.json` (1.0.0 → 1.1.0), `runner/mock_slice.py`'s `RESULT_SCHEMA_VERSION`, `runner/spend_ledger.py`'s `LEDGER_SCHEMA_VERSION`, the `runner/c1_mock.py` docstring, the result pin and version check in `tests/test_contract_lock.py`, the result fixtures in `tests/fixtures/result/`, the new `tests/test_result_schema_c1.py`, the `SPEC.md` version header, `docs/DATA_CONTRACTS.md`, `docs/INTERFACES.md`, and a superseding note in `docs/W7_T1_HANDOFF.md`. Every planned C1 control trial at every empirical Section 12 row.
- Outcome visibility at decision time: Outcomes visible (development only). No evaluation or C1 outcome exists, and the change was required on November 2, before any paid grid call (decision 0025 item 8).

### Defect

Every empirical Section 12 row runs C1 controls under D0_BASELINE, but the locked result schema allows only the `development` and `evaluation` splits and the `C2`, `C3`, and `C4` channels, so no official C1 record could validate. The spend-ledger schema likewise refused a C1 trial's start line. Found by the November 2 review behind decision 0025, which required this change as its own record.

### Scope determination

The change is additive. It adds the `c1_control` split and the `C1` channel, fixes a C1 record's condition, configuration, role, base, and superblock, and requires version 1.1.0 for that form. A 1.0.0 record must keep exactly the 1.0.0 shape, so every preserved record validates unchanged. No field is removed or reinterpreted, no nullability changes for an existing split, and no estimand, oracle, scorer, gate, audit, or `SPEC.md` text changes.

### Required response

Decision 0034 moves both schemas to 1.1.0, moves the writers with them, re-pins the result schema, and moves `SPEC.md` to v1.23.0. No symmetric rerun or validation rerun is required (Section 11 step 5), because no evaluation, validation, or C1 run exists.

### Preserved evidence

The superseded result schema is version 1.0.0 in Git history, pinned at SHA-256 `5b41c8039690c232cd02adce4a617b1b93aedec816029ca7595c41867292eb16` (canonical JSON) by decision 0009.

### Verification

`tests/test_result_schema_c1.py` checks the C1 form, each rejected variant, the 1.0.0 shape, the writers' versions, and a C1 ledger line; it failed before the change. `tests/test_contract_lock.py` passes with only the result version and hash changed. Every stored November 9 result line (195) and every spend-ledger line (213) validates under the new schemas. CI runs the full no-credit suite on the pull request.

### Claim impact

None. No table, figure, README value, demo aggregate, or report sentence exists that depends on a C1 record.

## DEV-0006 — Section 7 left authorization and utility undefined for an official C1 control

- Date detected: 2026-11-13
- Recorded by: marek-sm
- Prior protocol version: `SPEC.md` v1.23.0 (Section 7 pinned under decision 0028)
- New protocol version: `SPEC.md` v1.24.0
- Prior experiment/validation ID: None. No experiment or validation ID exists before Gate 3.
- Replacement experiment/validation ID: Not applicable (Section 11 step 3): no experiment or validation ID exists to replace.
- Affected cells/checks/artifacts: `SPEC.md` Section 7 (new subsection "Official C1 controls") and its pin in `tests/test_contract_lock.py`; the new `runner/c1_policy.py` and `tests/test_c1_reference_policy.py`; and `defenses/freeze.json`'s `test_evidence_hash` (`8e434a97…` → `287f797d…`), because `tests/test_contract_lock.py` is in the defense freeze's frozen test evidence. `defense_hash` and every defense file are unchanged. The nullability of `utility.pass` for a completed `c1_control` record changes from "never null" to "always null, with a named not-applicable oracle", a material change under `docs/DATA_CONTRACTS.md`'s change rules; that document itself is unchanged. No schema, audit, estimand, or C1 table shell changes.
- Outcome visibility at decision time: Outcomes visible (development only). No evaluation, official C1, or live C1 outcome exists.

### Defect

Section 7 scores every request against the trusted task policy, and a C1 control has none: its trusted prompt is the hostile instruction (Section 3). So three of the six facts the C1 table reports (Section 10) had no oracle. Section 7's utility rule, true or false for every completed outcome, had no validator for a trial with no legitimate task. `W8-T3`'s owner found it on November 13 while building the official C1 executor (#77), which fails closed until it is defined.

### Scope determination

The gap is limited to `c1_control` records. The primary study's policies, the audit, every fact and union definition, the schemas, and the C1 table shell are unchanged. No official C1 record exists.

### Required response

[Decision 0037](decisions/0037-c1-authorization.md) defines one read-only reference policy generated from the frozen fixture (no `send_email`, no secret reads, no grant) and a named not-applicable utility oracle, states both in Section 7, re-pins it, and moves `SPEC.md` to v1.24.0. No symmetric rerun or validation rerun is required (Section 11 step 5), because no evaluation, validation, or official C1 run exists.

### Preserved evidence

The superseded text is `SPEC.md` v1.23.0 in Git history, with Section 7 pinned at SHA-256 `1c276368b606a64ad9e9848df0edd1132b7a18d210ed05db4e120b4298be54be`.

### Verification

`tests/test_c1_reference_policy.py` failed before the change (19 failed) and passes after it. `tests/test_contract_lock.py` passes with only Section 7's pin changed.

### Claim impact

None. No table, figure, README value, demo aggregate, or report sentence depends on a C1 record.

## DEV-0007 — Decision 0028 item 8's in-sweep integrity check and batch hashes did not run

- Date detected: 2026-11-18
- Recorded by: marek-sm
- Prior protocol version: `SPEC.md` v1.24.0; `protocol/active.json` `protocol_version` 1.0.0
- New protocol version: unchanged. No protocol text, record, oracle, scorer, or schedule changes (see Scope determination).
- Prior experiment/validation ID: `canary-2026-sweep`, for the sweep and the official C1 run (protocol `CANARY-2026-F20`)
- Replacement experiment/validation ID: None. No rerun (see Required response).
- Affected cells/checks/artifacts: no cell. The checks are [decision 0028](decisions/0028-restore-strength.md) item 8's blinded integrity check at about 50% of the sweep and its batch hashes of raw records committed from a second clone during the sweep.
- Outcome visibility at decision time: Operational only: completion counts, schema checks, and cost. No sweep or C1 outcome had been read.

### Defect

Decision 0028 item 8 required two steps during the sweep. Neither ran. The sweep's runbook had no step for either, and no commit adds batch hashes. No record shows a mid-sweep check: `python -m runner.sweep verify` ran only after the sweep finished and at the November 17 re-check. The project lead found the miss on November 18, while listing every decision obligation before Gate 4.

### Scope determination

This isn't a material measurement defect. No trial, record, oracle, scorer, or schedule changed, and none is known to be wrong. What was lost is in-sweep tamper evidence for the raw records between the runs and their first public anchor. The sweep ran November 16, 9:22–10:20 am Pacific, and the official C1 run 11:26–11:28 am. Both times are file times, read without opening any file. After the runs:
- the full `verify` passed, 1,080 of 1,080 sweep trials and 12 of 12 C1 trials;
- `python -m analysis.gate3_hashes --check-run` was clean on both runs;
- the Drive copy was compared file by file on November 16 and November 17;
- SHA-256 manifests of both runs were published on `main` in #118, merged November 18, 6:59 pm Pacific.

### Required response

Claim removal. No claim may say the raw records were anchored, hashed, or checked during the sweep. Neither step can run after the sweep has ended. A new sweep would run on a changed host (`os_build`, [decision 0042](decisions/0042-gate4-late-evidence.md) item 7) and isn't proposed.

### Preserved evidence

The original run directories stay in the Gate 3 step checkout at `dd9b02e`, with a Drive copy. Their manifests are `docs/evidence/raw-manifests-2026-11-18/sweep-raw-manifest.json` (SHA-256 `5f60c26689ed0331b35916c77b0fb964cb4c7e07bc536381b851329bcc915cb8`) and `docs/evidence/raw-manifests-2026-11-18/c1-raw-manifest.json` (SHA-256 `95a9ec9c9611592c257964dbae90d4e1c0add6726546f683d8957e97e99ed994`).

### Verification

At the Gate 4 step, `python -m runner.raw_manifest RUN --check MANIFEST` passes on both runs, and the Gate 4 record gives its date. `git log` shows no batch-hash commit between the sweep's first paid call and #118.

### Claim impact

The paper's Section 14 limitations give the first public anchor and say it came after the sweep ended. No table, figure, README value, or number changes.

## DEV-0008 — Gate 4's November 19 target was missed, and its step moves after the fact to November 20

- Date detected: 2026-11-19
- Recorded by: marek-sm
- Prior protocol version: `SPEC.md` v1.24.0; `protocol/active.json` `protocol_version` 1.0.0
- New protocol version: unchanged. Only a gate time changes (see Scope determination).
- Prior experiment/validation ID: `canary-2026-sweep` (protocol `CANARY-2026-F20`)
- Replacement experiment/validation ID: None. No rerun.
- Affected cells/checks/artifacts: no cell. `SPEC.md` Section 11's Gate 4 target and its "Gate 4 fails" response, and the November 19 dates in [decision 0029](decisions/0029-gate-chain-shift.md) item 5 and `TASKS.md`.
- Outcome visibility at decision time: Operational only: completion counts, schema checks, and cost. No sweep or C1 outcome had been read.

### Defect

`W9-T3`'s sweep, audit, and generated-results pull request, due November 18, wasn't open on November 19. So Gate 4's pass evidence didn't exist at its November 19 target. As written, Section 11's "a missed gate reduces scope" and its Gate 4 response would withhold every empirical comparison.

### Scope determination

The change isn't material. No measurement, schema, oracle, scorer, estimand, threshold, or pass-evidence text changes, and no date moves past one the rules already set: November 20 is the final supported-results date, and the November 22 cutoff stands. The owners of `W9-T3`, `W11-T1`, and `W11-T4` have had raw access since November 17 ([decision 0025](decisions/0025-full-study.md) item 12). This entry doesn't claim they haven't read outcomes.

### Required response

Claim removal. No claim may say Gate 4 met its November 19 target. [Decision 0042](decisions/0042-gate4-late-evidence.md) lets the Gate 4 step and its pass evidence complete through 11:59 pm November 20, once. If any pass item is missing or fails then, Section 11's Gate 4 response applies as written (decision 0042 item 4).

### Preserved evidence

The superseded text is `SPEC.md` v1.24.0 and `TASKS.md` at `58cc847`, in Git history.

### Verification

`tests/test_contract_lock.py` and `tests/test_c1_reference_policy.py` pass unchanged, because no pinned section or the header changed. The Gate 4 record gives the step's time.

### Claim impact

The Gate 4 record, `STATUS.md`, and the paper state that the target was missed and then moved. No table, figure, README value, or number changes.

## DEV-0009 — Gate 4's November 20 time was missed, Gate 4 completes by November 23, the release chain moves to the December 3 Demo Day, and the count-only tables leave the public release

- Date detected: 2026-11-21
- Recorded by: marek-sm
- Prior protocol version: `SPEC.md` v1.24.0; `protocol/active.json` `protocol_version` 1.0.0
- New protocol version: unchanged. Only gate and release times change, and one reporting output is removed (see Scope determination).
- Prior experiment/validation ID: `canary-2026-sweep` (protocol `CANARY-2026-F20`)
- Replacement experiment/validation ID: None. No rerun.
- Affected cells/checks/artifacts: no cell. `SPEC.md`'s preamble, its Section 0 release-freeze row, Section 11's readiness-gate sentence, Gate 4 and Gate 5 rows, and "Gate 4 fails" response, and Section 14's paper and repository items; [decision 0028](decisions/0028-restore-strength.md) item 4's public count-only tables; and the dates in [decision 0042](decisions/0042-gate4-late-evidence.md), [decision 0030](decisions/0030-done-by-november-30.md), and `TASKS.md` that [decision 0043](decisions/0043-gate4-and-demo-day-dates.md) lists.
- Outcome visibility at decision time: Operational only: completion counts, schema checks, cost, and provider errors. No sweep or C1 outcome had been read by the project lead.

### Defect

`W9-T3`'s Gate 4 evidence never arrived, so decision 0042's once-only exception lapsed at 11:59 pm November 20. As written, Section 11's Gate 4 response would withhold every empirical comparison. Decision 0036 item 6's November 20 release path for the count-only tables was also missed. The event organizers confirmed Demo Day for Thursday, December 3, after the release freeze's November 29 date.

### Scope determination

The date changes aren't material. No measurement, schema, oracle, scorer, estimand, threshold, or pass item changes, and the November 22 data cutoff stands: no trial and no repair runs after it. Missingness over 5% makes a headline comparison ineligible, as `SPEC.md` Section 9 already says, rather than failing Gate 4 as a whole.

The count-only removal is a reporting change, made outcome-blind. The sanitizer content-addresses the fields `analysis/diagnostics.py` reads, so those tables can't regenerate from the released bundle, and a new script would be a feature after the freeze. No estimand, scorer, threshold, or pass item changes.

This is the second after-the-fact move of Gate 4, and it lands past Gate 4's own November 22 cutoff. The owners of `W9-T3`, `W11-T1`, and `W11-T4` have had raw access since November 17 ([decision 0025](decisions/0025-full-study.md) item 12). This entry doesn't claim they haven't read outcomes.

### Required response

Claim removal. No claim may say Gate 4 met any earlier time, and no count-only table is public. Decision 0043 lets the Gate 4 step and its pass evidence complete through 11:59 pm November 23. If a whole-sweep pass item is missing or fails then, or no headline comparison remains eligible, the response is `STOP` (decision 0043 item 2).

### Preserved evidence

The superseded text is `SPEC.md` v1.24.0 and `TASKS.md` at `b764432`, in Git history. The project lead may still generate the count-only tables from the raw runs as an internal check. They appear in no public table, number, or claim.

### Verification

`tests/test_contract_lock.py` and `tests/test_c1_reference_policy.py` pass unchanged, because no pinned section or the header changed. The Gate 4 record gives the step's time.

### Claim impact

The Gate 4 record, `STATUS.md`, and the paper state both misses, this second move, which items the project lead built and ran, the removal of the count-only tables and the D2_DATAMARKING bias they size, that the frozen `ENGINEERING` fallback had no executor, and that the replay fixes came before decision 0043. The count-only tables leave the final public tables. No other table, figure, README value, or number changes.
