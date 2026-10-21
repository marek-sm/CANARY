# CANARY Demo and Replay Assets

The terminal replay in `trace.py` reads schema-valid `events.jsonl` and its
sibling `results.jsonl`. It never uses hand-authored result text.

Generate the first accessible development-output example from the real W5-T3
six-cell runner:

```bash
uv run make demo-example
```

Verify that the committed example is current:

```bash
uv run make demo-example-check
```

The generated file is `generated/accessible_example.md`. It is deliberately
labeled as mock development evidence and excluded from every estimate. The
caption and transcript scaffolds reserve accessible structure ahead of results;
they do not authorize a claim or presentation duration.

W6-T5 acceptance evidence also includes `tests/test_demo_known_traces.py`,
which covers every display-only label, every true/false/null intersection of
the six underlying security facts, and the W5-T4 event-state language.
