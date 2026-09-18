# Protocol Deviations

No protocol deviations are recorded.

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
