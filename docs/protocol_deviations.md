# Protocol Deviations

Two protocol deviations are recorded, DEV-0001 and DEV-0002, below the entry template.

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
