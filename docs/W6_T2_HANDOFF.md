# W6-T2 handoff: development bases, C1/demo sources, intake

Owner: `j0hanj` (T2). Reviewer and independent source reviewer: `marek-sm` (project lead), since the October 15 T3 capacity reassignment in `TASKS.md`. Before that it was T3 under the standing pairs.

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

**Why the C1 controls reuse dev goals.** `unauthorized_action` payloads that port to our four tools are scarce. Basically it's AgentDojo's email goals, and under `M10-ALL` W7-T2 needs at least 7 per goal. Any evaluation candidate near-identical to a dev, C1, or demo base is lost to evaluation. So the two action C1 controls reuse the two goals the dev bases already took (tasks 0 and 3) under a different wrapper. That way they don't use up any more of the pool.

## For the source review

For each record, please check that the URL and `source_locator` open, that `original_payload` matches the source exactly, and that every adaptation note is one of the Section 5 mechanical substitutions. The ones worth a closer look:

- dev-002 and dev-005 point at the fake API key in the fixture config file ("passwords" and "Facebook security code received via email from ..." were swapped). I counted that as the protected-secret and resource-locator substitution.
- dev-001, c1-001, c1-002 and demo-001 point at the fictional customer record ("Amazon", "my Amazon account", "Teladoc ... medical", "saving accounts" were swapped), for the same reason.
- No record deletes words anymore; `tests/test_dev_corpus.py` checks that every adaptation is substitution-only.
- AgentDojo typos ("iunstructions", "from by") are kept on purpose.

Once you sign off, replace `PENDING_REVIEW` with your ID in `source.reviewed_by` and `attack.reviewed_by` of each record and ledger row. That includes dev-001, which never got its W5 review.

## dev-001 fix

The W5 adaptation dropped "from Amazon" and "my alternate email address," from the original. Neither deletion is a permitted substitution. "my alternate email address," is back, and "Amazon" is now "my customer record", which also says where the canary lives. That changed dev-001's canonical payload hash, its three attack renders, its manifest, and its ledger row. The clean renders and the template didn't change. The license field now names the actual `LICENCE` file.

## Open items

- **Task IDs and oracle refs** stay null until W6-T1 (#32) merges. Then they get filled from its registry.
- **dev-001's renders don't carry its benign facts** (stars, verified flag). That re-render is lead scaffold now, after #32 and #34 merge (October 18 rollup).
- **C1 and demo aren't ledger statuses.** The frozen Section 5 list has no value for them, so their source records live in `corpus/c1/` and `corpus/demo/` with `split` set to `c1_control` or `demo`, and they're checked as reserved bases. The project lead decides whether that needs a record.
- **Evaluation rows carry `canonical_payload`.** Near-duplicate detection needs the text, so `python -m corpus.intake` treats a kept evaluation row without it as a problem. A `duplicate` row names its kept case in `duplicate_of`, and the keeper has to have the lowest salted hash.
- **`make corpus-check` is red until sign-off.** Any kept row or reserved record still marked `PENDING_REVIEW` is a problem, on purpose.
