# 0041: The code and content licenses, contributor agreements, and the author order

- Status: Accepted. Approved by the project lead on 2026-11-17, and in force from this record's merge; drafted with AI assistance.
- Date: 2026-11-17
- Decision scope: Release
- Secondary scopes: Governance
- Related specification sections: Sections 0, 11, 14, and 17
- Related records: [decision 0021](0021-two-week-shift.md), [decision 0030](0030-done-by-november-30.md), and [decision 0031](0031-merge-on-green.md) item 9
- Supersedes: None. Decision 0031 item 9 already moved this input to November 16–20.

## Context

`TASKS.md` makes the code and content license choice and the author order a project-lead input. `W11-T5` commits `LICENSE` and `CITATION.cff`, `W12-T2`'s license audit needs `LICENSE` by Monday, November 23, and `SPEC.md` Section 17 requires both files at their gate or release check.

The repository is public and has no license. `CONTRIBUTING.md` creates no ownership or contribution terms, so the project lead can choose a license but can't grant one over other contributors' work. No club or university term is known to the project lead. This record is not legal advice.

All 54 entries in `corpus/release/payloads.json` record an MIT source, across four sources.

## Options considered

1. **MIT for code.** Short, and it matches the sources, but it has no express patent grant.
2. **Apache-2.0 for code and CC BY 4.0 for content.** Chosen. The patent grant suits companies choosing safeguards, the audience `SPEC.md` Section 0 names, and CC BY keeps credit attached to the written work.
3. **Commit no `LICENSE` if any contributor doesn't agree.** Rejected. It would fail the `SPEC.md` Section 17 release check and hold back everyone else's work.

## Decision

1. **Apache-2.0** covers code, tests, schemas, `protocol/`, configuration, and the corpus and fixture material CANARY wrote.
2. **CC BY 4.0** covers documentation, `docs/evidence/`, figures, captions, video, transcript, generated tables, and sanitized results. The manuscript is covered only if its authors agree.
3. **Outside material keeps its own terms.**
   - Third-party payload text, original or adapted, stays under its source's MIT license. [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md) carries the notices.
   - No license is claimed over model-generated text in released records. The provider's terms haven't been verified.
   - The licenses cover only what is in the public repository. Raw records and restricted audit material stay outside Git, and `docs/DATA_RELEASE.md` still decides what ships.
4. **Each contributor agrees in writing.** The contributors are `marek-sm`, `nkuhanas`, `j0hanj`, `samsonchang2028`, `Dhruv235`, and `milesshoe`. Each posts this sentence from their own account on the GitHub issue "License agreement for decision 0041":

   > I license my contributions to this repository, through the release tag, under Apache-2.0 and CC BY 4.0 as decision 0041 maps them, and I have the right to do so.

   - It is due by 11:59 pm Pacific on Friday, November 20, or 48 hours after this record merges if that is later.
   - The project lead collects the agreements as part of the lead input, so no `Depends` cell changes.
5. **`LICENSE` is on `main` by Monday, November 23.**
   - `W11-T5` commits it if every agreement is in when `W11-T5` merges.
   - If it isn't on `main` at 11:59 pm Pacific on November 22, for any reason, `TASKS.md` first records a visible reassignment of that one deliverable, and the project lead commits it by November 23.
   - If anyone hasn't agreed, `LICENSE` names as unlicensed every file holding that person's surviving lines, found with `git blame -M -C -C`. The project lead regenerates the list against the release commit and merges any correction before the tag. A match is part of the release checklist's license item.
   - If any file is unlicensed, every public reuse statement is limited to the licensed paths.
   - No reuse right exists until `LICENSE` is on `main`, and `SPEC.md`'s bar on saying teams can reuse or adopt CANARY's code stays in place until then.
6. **Author order.**
   - The project lead is first, on the evidence in [`docs/contributions/marek-sm.md`](../contributions/marek-sm.md). The project lead set this position, and this record says so.
   - Everyone else who qualifies follows alphabetically by consented public name or identifier, ignoring case. That order doesn't rank them.
   - A contributor may object on the same issue by the item 4 date, and the project lead answers there before `CITATION.cff` is committed.
7. **Who qualifies.**
   - `CITATION.cff` uses `SPEC.md` Section 0's test: a substantive technical or research artifact, an accurate contribution statement, final-review consent, and claim language that separates individual work from the team result. It uses each person's consented form only.
   - The manuscript byline also needs final-draft review (`TASKS.md`, component portfolios), within 48 hours after the final draft is delivered and no later than the November 29 release freeze. The byline can drop a name but can't reorder names.
   - Anyone dropped from the byline for that reason keeps their credit in the contribution table (`SPEC.md` Section 14).
   - No role, title, or roster place qualifies anyone.
8. **A separate call, not made here.** Whether the corpus records' `original_payload` fields ship as they are (`docs/W8_T2_HANDOFF.md`), and what happens to the addresses outside `fixture.test` in `corpus/release/payloads.json`'s `adaptation_notes`. Both are in hashed files, so any change goes through `SPEC.md` Section 11. `TASKS.md` dates this for November 24.

## Consequences

- No result, trial, claim, gate check, or frozen artifact changes. `SPEC.md` doesn't change.
- If a contributor doesn't agree in time, the files holding their work stay public with no reuse rights.
- Each contributor has one sentence to post, with at least 48 hours' notice.
- `W11-T5` keeps `LICENSE` and `CITATION.cff`. The notices file is the project lead's, so its scope doesn't grow.

## Verification

- `tests/test_tasks_dependencies.py`, `tests/test_status_consistency.py`, and the documentation tests pass, and CI runs the full suite.
- This record's pull request changes no `runner/paid_run.py` `HASHED_DIRS` path and no file under `tests/`.
- `doc-auditor` and two `decision-critic` rounds reviewed the plan or the built documents.
