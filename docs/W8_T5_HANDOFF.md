# W8-T5 accessible output-pipeline freeze

W8-T5 freezes the accessible, pre-results output structure inherited from
W5-T5. It does not freeze or reinterpret scientific analysis: W8-T3 owns that
code, and `SPEC.md` remains the authority for every estimand and claim.

## Frozen pipeline

[`paper/output_pipeline_freeze.json`](../paper/output_pipeline_freeze.json)
records hashes for:

- `analysis/report_shells.py`, the deterministic shell renderer;
- `paper/estimand_manifest.json`, the table, caption, alt-text, and column
  declarations; and
- `paper/generated/estimand_shells.md`, the generated table equivalents and
  intentionally empty figure shells.

The record also hashes the focused tests separately. The pipeline is explicitly
`PRE-RESULTS — NO DATA`; it contains no empirical value or defense claim.

## Acceptance evidence

Run offline, without a model key or provider access:

```sh
uv run make paper-shells-check
uv run make output-freeze-check
uv run make report REPORT_MODULE=analysis.report_shells
uv run pytest -q tests/test_paper_scaffold.py tests/test_make_report.py tests/test_output_pipeline_freeze.py
```

At Gate 3, ordinary `make report` first regenerates these accessible shells,
checks them against the freeze record, and then invokes W8-T3's frozen report
module.

## Limitation

This freeze verifies deterministic accessible structure and detects drift in
the W5-T5 shell pipeline. It does not validate future numerical results, their
scientific interpretation, or W8-T3's analysis implementation; those require
the frozen sanitized bundle, W8-T3's checks, and project-lead approval.
