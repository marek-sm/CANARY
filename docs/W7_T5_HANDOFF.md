# W7-T5 replay and demo staging handoff

## Scope and evidence boundary

W7-T5 supplies the presentation path; it does not change T3's replay-data
semantics or create an official experiment. `make replay` reads and
schema-validates an already completed W6-T3 development record staged from
`demo/replay_spec.json` with mock tool-result delivery. It makes no provider
call, writes no run data, and labels the output `MOCK / EXCLUDED` and
`ILLUSTRATIVE — NOT STATISTICAL EVIDENCE`.

The separately reviewed `demo-001` source is now staged as fixed C2/C3/C4
attack/clean fixtures. It uses the existing `review-field-lookup` trusted task:
the agent may retrieve the review facts, while email is outside that task's
authorization policy. The staged case remains `split: demo`; it is not selected
into the corpus and is excluded from every estimate.

## Reproduction

```bash
uv run make replay
uv run make replay
uv run make corpus-check
uv run make demo-example-check
uv run pytest -q tests/test_demo_known_traces.py tests/test_corpus_records.py
```

The two replay commands are deliberately separate operator starts. Each should
begin immediately, print `RECORDED TRACE`, and finish without credentials or
network access. Miles must personally start both from a fresh terminal without
consulting notes before this human-operation acceptance item is checked off.

Automated path verification on October 29 ran the command twice successfully;
both rendered outputs had SHA-256
`3d8aedbbc783885a1cbdc407f37cf005b03720e200e132ef266f3b5397c3cb36`.
This verifies deterministic replay but does not replace Miles's two required
operator starts.

## Paper-lead technical notes

- The replay is generated from stored event/result JSONL; no outcome wording is
  hand-authored.
- The fixed demo case comes from `corpus/demo/demo-001.json`, retains the
  independently reviewed canonical payload and hash, and is rendered by the
  same channel adapters used for development cases.
- `D0_BASELINE`, `D1_POLICY_GATE`, and `D2_DATAMARKING` outcomes must be
  described only from their actual traces. This staging work establishes no
  defense result.
- Caption, alt-text, transcript, and generated-example scaffolds remain current.
  They require explicit unknown states and a text/table equivalent, and never
  rely on color alone.
- Limitation: a rehearsed excluded case demonstrates the interface and failure
  story only. It cannot estimate attack success, defense efficacy, clean
  utility, or general prompt-injection security.

## Gate 2 operator record

- Operator: Miles
- Run 1: completed October 29; Miles confirmed the separate no-notes replay start succeeded
- Run 2: completed October 29; Miles confirmed the second separate no-notes replay start succeeded
- Provider access: not required; replay path is read-only
- Reviewer: Johan (`j0hanj`), the standing T5 reviewer
