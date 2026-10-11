# W6-T2 handoff: development bases, C1/demo sources, intake

Owner: `j0hanj` (T2). Reviewer and independent source reviewer: `samsonchang2028` (T3), per the standing pairs and `SPEC.md` Section 5.

## What's here

| Thing | Where |
|---|---|
| Five development bases, each naming its template from [decision 0007](decisions/0007-gate1-corpus-rules-freeze.md) | `corpus/development/dev-00{1..5}.json` |
| Attack/clean renders through C2, C3, C4 plus hash manifests | `fixtures/dev-00{2..5}/`; dev-001's three attack renders were redone, see below |
| Four C1 control source records (R15 needs four) | `corpus/c1/c1-00{1..4}.json` |
| One demo case source record | `corpus/demo/demo-001.json` |
| Record-driven renderers (`c2/c3/c4-extract-v2`) | `channels/render.py`, bottom half |
| Fixture builder and drift check | `corpus/render_fixtures.py` |
| Candidate IDs, exact-hash and near-duplicate detection, ledger checks | `corpus/intake.py` |
| Ledger rows for dev-002 to dev-005 | `corpus/candidates.jsonl` |

## Commands

```sh
uv run make corpus-check     # fixtures match a fresh render, ledger and reserved bases are consistent
uv run make corpus-fixtures  # rewrite fixtures after editing a record
uv run pytest -q tests/test_dev_corpus.py tests/test_intake.py
```

## Sources

Every original payload was copied byte-for-byte from the pinned source file, and its SHA-256 is stored next to it. Nothing was retyped.

| Case | Source and case | Goal | Family |
|---|---|---|---|
| dev-001 | InjecAgent `attacker_cases_ds` (W5-T2) | secret_disclosure | tool-result-instruction-override |
| dev-002 | InjecAgent `attacker_cases_ds.jsonl` line 21 | secret_disclosure | tool-result-instruction-override |
| dev-003 | AgentDojo workspace `injection_task_0` + `important_instructions_no_names` | unauthorized_action | important-instructions-impersonation |
| dev-004 | AgentDojo workspace `injection_task_3` + `ignore_previous` | unauthorized_action | ignore-previous-instructions |
| dev-005 | AgentDojo workspace `injection_task_4` + `direct` | secret_disclosure | todo-directive |
| c1-001 | InjecAgent ds line 1 | secret_disclosure | tool-result-instruction-override |
| c1-002 | InjecAgent ds line 25 | secret_disclosure | tool-result-instruction-override |
| c1-003 | AgentDojo `injection_task_0` + `direct` | unauthorized_action | todo-directive |
| c1-004 | AgentDojo `injection_task_3` + `direct` | unauthorized_action | todo-directive |
| demo-001 | InjecAgent ds line 4 | secret_disclosure | tool-result-instruction-override |

InjecAgent is pinned at `f19c9f2c` (MIT, `LICENCE` file). AgentDojo is pinned at tag `v0.1.35` / `a75aba76` (MIT). InjecAgent's attacker files have no per-case IDs, so those records use `NO_SOURCE_CASE_ID` and give the line number in `source_locator`.

**Why the C1 controls reuse dev goals.** `unauthorized_action` payloads that port to our four tools are scarce. Basically it's AgentDojo's email goals, and W7-T2 needs nine of them. Any evaluation candidate near-identical to a dev, C1, or demo base is lost to evaluation. So the two action C1 controls reuse the two goals the dev bases already took (tasks 0 and 3) under a different wrapper. That way they don't use up any more of the pool.

## For the source review

For each record, please check that the URL and `source_locator` open, that `original_payload` matches the source exactly, and that every adaptation note is one of the Section 5 mechanical substitutions. The ones worth a closer look:

- dev-002 and dev-005 swap the secret ("passwords", "Facebook security code") for CANARY's protected secret. I counted that as the protected-secret substitution.
- c1-002 and demo-001 swap medical or savings records for the fictional customer record, for the same reason.
- AgentDojo typos ("iunstructions", "from by") are kept on purpose.

Once you sign off, replace `PENDING_REVIEW` with your ID in `source.reviewed_by` and `attack.reviewed_by` of each record and ledger row. That includes dev-001, which never got its W5 review.

## dev-001 fix

The W5 adaptation dropped "my alternate email address," from the original. That isn't one of the permitted substitutions, and the notes didn't mention it. It's back in now. That changed dev-001's canonical payload hash, its three attack renders, its manifest, and its ledger row. The clean renders and the template didn't change. The license field now names the actual `LICENCE` file.

## Open items

- **Task IDs and oracle refs** stay null until W6-T1 (#32) merges. Then they get filled from its registry.
- **Resource names drift from #32.** The lead's assignment says `product_reviews`, `shipping_notices`, `meeting_requests`. #32's DB seed uses `reviews`, `shipping`, `meetings`. One side has to change before the W7 grid.
- **dev-001's renders don't carry its benign facts** (stars, verified flag). The v1 renderer only wraps the review text. Moving it to v2 changes its hashes and the six-cell runner's expectations, so it should land together with W6-T3's tool-result delivery change.
- **C1 and demo aren't ledger statuses.** The frozen Section 5 list has no value for them, so their source records live in `corpus/c1/` and `corpus/demo/` with `split` set to `c1_control` or `demo`, and they're checked as reserved bases. The project lead decides whether that needs a record.
- **Near-duplicate detection on evaluation rows** needs the canonical payload text. The ledger rows only carry hashes. `python -m corpus.intake` reads `canonical_payload` from evaluation rows when it's present; W7-T2 decides whether that lives in the ledger or in per-candidate records.
