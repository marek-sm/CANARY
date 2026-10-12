# Protocol Deviations

One protocol deviation is recorded: DEV-0001, below the entry template.

This append-only log is used only after a scientific or claim-bearing artifact has frozen. Pre-freeze design decisions belong in `docs/decisions/`; current slice state belongs in `TASKS.md`, and the dated weekly rollup belongs in `STATUS.md`.

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
