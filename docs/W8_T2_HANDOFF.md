# W8-T2 handoff: corpus freeze preparation

Owner: `j0hanj` (T2). Reviewer: `marek-sm`. Tier input: `F20` (decision 0032, #91), so the frozen corpus is the 20-base prefix.

| Part | Where |
|---|---|
| First step: `P` = 20 and the built prefixes, posted from `make select` over the reviewed pool | #73 and this pull request |
| 20 evaluation base cases, `eval-001` to `eval-020`, in prefix order, each with C2/C3/C4 fixtures and exact clean twins | `corpus/evaluation/eval-*.json`, `fixtures/eval-*/`, built by `corpus/build_evaluation.py` |
| Section 15 corpus-freeze citation audit | `docs/audits/2026-11-11-w8-t2-citation-audit.md` (script evidence done; human ticks pending) |
| Freeze manifest: `corpus_hash` and `source_ledger_hash` for `protocol/active.json` | `corpus/freeze.json`, `corpus/freeze.py` |
| Release-safe payloads, outside Gate 3's hash set | `corpus/release/payloads.json`, `corpus/release_payloads.py` |
| Draft corpus notes for the paper leads | Below |

## Commands

```sh
uv run make select                               # P, the built prefixes, tasks, recheck samples
uv run make freeze-check                         # eval records, fixtures, and freeze.json all current
uv run make eval-build N=20                      # rebuild the evaluation cases (only under Section 11 after freeze)
uv run python -m corpus.release_payloads --check # release list is current
uv run pytest -q tests/test_evaluation_corpus.py tests/test_release_payloads.py
```

## Release-safe payloads

`corpus/release/payloads.json` lists every considered case once: the five development bases, the four C1 records, the demo case, and all 44 W7-T2 candidates, kept or rejected. Each entry keeps its source pointer, version, license, redistribution decision, and original-payload SHA-256.

All four sources are MIT, so payload text may be redistributed. Adapted payloads only hold `@fixture.test` addresses and are listed in full. Originals keep their wording, but every email address outside `fixture.test` becomes `[address withheld <sha8>]`: the benchmarks invented addresses like `amy.watson@gmail.com` on real domains, and `docs/DATA_RELEASE.md` treats contact identifiers as removable. 33 of 54 originals have an address withheld. The hash and locator still let anyone check the withheld text against the pinned source.

**For the project lead:** the unredacted originals are already in the corpus records on `main` (`original_payload`), as SPEC.md Section 8's record shape asks. Whether the public release ships those fields as-is or only this list is your call; this list doesn't change them.

## Draft notes for the paper leads

### Corpus method

- **Sources.** Four public benchmarks, each pinned: InjecAgent (`uiuc-kang-lab/InjecAgent@f19c9f2`), AgentDojo (tag `v0.1.35`), Agent Security Bench (`agiresearch/ASB@544540f`), and LLMail-Inject (Hugging Face `microsoft/llmail-inject-challenge` revision `1063bdf`). All MIT.
- **Intake.** 44 evaluation candidates were considered. 27 were eligible (13 `secret_disclosure`, 14 `unauthorized_action`), 1 was a near-duplicate of a C1 control, and 16 were rejected at source screening with a recorded reason, mostly because their goal needs a tool CANARY doesn't have. No considered candidate was dropped without a ledger row.
- **No outcome-based choice.** Each candidate's ID is derived from four source fields before adaptation. Near-duplicates follow a frozen rule (decision 0007). Selection (decision 0014) alternates goals, orders each goal by a salted hash of the ID, and takes the earliest vector that meets the source and family minima and caps. Nothing in intake or selection reads a model output, and no candidate ran on a model before the freeze.
- **LLMail-Inject subset.** Which of its submissions to consider was fixed before any was read: scenario 1-3 texts naming `contact@contact.com` and "confirmation", taken in salted-hash order. The dataset's success labels were never read.
- **Review.** The project lead, who opened and adapted none of them, re-opened every source and case and passed all 44 records and four licenses on November 8 (#73).
- **Size.** On that pool the script builds a 20-base prefix with no cap relaxation, and the 15-, 10-, 8-, and 6-base prefixes nest inside it.

### Adaptation

Only mechanical substitutions (SPEC.md Section 5): synthetic recipients and domains at `fixture.test`, product and tool names, resource locators, and the protected secret (the fictional customer record or the fake API key in a fixture config file). Nothing is deleted or added; `tests/test_eval_intake.py` checks that word by word. Attack wrappers stay verbatim, typos included, so a payload's family survives adaptation. Every adapted payload round-trips through the C2, C3, and C4 serializers.

### Citations

| Key | Source | Pinned at | License |
|---|---|---|---|
| `injecagent-2024` | InjecAgent, arXiv:2403.02691 | `f19c9f2c79a41046eb13c03c51a24c567a8ffa07` | MIT |
| `agentdojo-2024` | AgentDojo, github.com/ethz-spylab/agentdojo | `v0.1.35` (`a75aba76`) | MIT |
| `asb-2024` | Agent Security Bench (ASB), github.com/agiresearch/ASB | `544540ff0788998072f7df463056fd17e62cc9f4` | MIT |
| `llmail-inject-2025` | LLMail-Inject, huggingface.co/datasets/microsoft/llmail-inject-challenge | `1063bdf01ec8762b812d5e06ee768a06faa5a6f7` | MIT |

The paper citations for AgentDojo, ASB, and LLMail-Inject (venue and arXiv IDs) get confirmed in the Section 15 citation audit, not filled in from memory.

### Related work (draft, descriptive only)

- **InjecAgent** puts attacker instructions inside tool responses of simulated tool-integrated agents and splits them into direct-harm and data-stealing cases.
- **AgentDojo** pairs user tasks with injection tasks across suites (workspace, Slack, travel, banking) and wraps each injection goal in one of several attack templates.
- **ASB** gives each agent attacker tools and injects attacker instructions through several injection methods (naive, fake completion, context ignoring, and others).
- **LLMail-Inject** is a dataset of submissions to an adaptive challenge against a simulated email assistant, where the attacker's email has to make the assistant send a specific email.

CANARY reuses their payloads, not their harnesses or numbers. Nothing here claims a gap in this work or compares results with it.

### One limitation

The corpus only covers attack goals that port to CANARY's four safe local tools. 16 of 44 considered candidates were rejected, most because their goal needs a tool CANARY doesn't have (payments, smart locks, shells, calendars), so results say nothing about those capabilities.

## The frozen corpus

`corpus/build_evaluation.py` takes the 20-base prefix from `corpus/select.py`, so nobody picks or orders a case. Base i becomes `eval-<i:03d>` with task_order index `INDEX_VECTOR[i - 1]`, so each of the ten templates gets two bases and the goals split 10/10. Each record copies its source and attack blocks verbatim from the candidate's reviewed source record, and its task block is derived from the W6-T1 registry the way the development bases' are.

- The five templates a development base already represents reuse that base's wrapper and clean text, so the splits render alike.
- The other five take their facts from the W6-T1 record at their resource. `open-ticket-ids` lists T-102 beside T-100 on C3 and C4 through `corpus.render_fixtures`' multi-row handling.
- Every record validates against `base_case.schema.json`, and the sweep's own render preflight (`runner.sweep._renders_refusal`) passes for all 20 bases × 3 channels × 2 conditions.

`corpus/freeze.json` holds the SHA-256 of 187 corpus files and 45 ledger files: `corpus_hash` `5afb8e1ee8f120f7ea8abfcdf4870b1339cdc5f992fe19f8e50a56939b6c9859` and `source_ledger_hash` `dc4fde13c548b4bf1e9b455efc5cba951dc713a8e86423c0742174a9ff439c41`. `make freeze-check` fails if any of them changes, and a change after the freeze follows SPEC.md Section 11.

## Still open

- **Citation audit, human part.** The script found every one of the 20 originals byte-for-byte at its pin and every hash recomputes, but Section 15 needs the opener and the reviewer to open each source themselves and tick the worksheet.
- **Q-73-1** (how a relaxation applies to nested prefixes) doesn't bind: this freeze uses no relaxation.
