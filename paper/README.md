# CANARY Paper and Accessible Report Inputs

This directory contains structure and generated-output scaffolding for the
designated paper leads. It does not contain manuscript claims or hand-entered
results.

- [`outline.md`](outline.md) follows the ten-section structure in `SPEC.md`
  Section 14 and identifies the technical-input owner for each section.
- [`estimand_manifest.json`](estimand_manifest.json) reserves accessible output
  structures for the predeclared estimands and diagnostic outputs in `SPEC.md`
  Section 10.
- [`generated/estimand_shells.md`](generated/estimand_shells.md) is generated
  from that manifest and intentionally contains no data.

Regenerate the shells with:

```bash
python -m analysis.report_shells
```

Check that the committed artifact is current with:

```bash
python -m analysis.report_shells --check
```

The project lead owns the thesis, protocol/metric wording, numerical claims,
and limitations approval. The designated paper leads own prose assembly,
editing, venue formatting, and submission. T5 supplies accessible structure,
figures, captions, alt text, and release packaging; this scaffold does not
transfer scientific or manuscript ownership.
