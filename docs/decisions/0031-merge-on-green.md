# 0031: Merge on green, review results code on the lead side before every paid run and freeze, and keep a second human on records and CI

- Status: Accepted. Directed by the project lead at the November 8 team meeting and approved by merging this record; drafted with AI assistance.
- Date: 2026-11-08
- Decision scope: Governance
- Secondary scopes: Protocol
- Related specification sections: Sections 5, 11, 14, 15, and 17
- Supersedes, for the sentences named in item 10 only: decisions 0015, 0022, 0025, 0027, 0028, 0029, and 0030. Every other part of each record stays in force.

## Context

**What this record costs, first.**

- **Independent human review of results code ends.** No member reviews a pull request before it merges. Results and release code are reviewed on the lead side instead. That is an AI review, and the project lead reads and classifies every finding it makes. The paper states this as a mandatory limitation (`SPEC.md` Section 14).
- **Lead-built code loses its second human.** Decision 0030 item 7 kept a member reviewer on any slice the project lead builds. That goes. The stop rule, the paid-run gate, the demo-rehearsal command, and every lead fix are reviewed only by the person who directed them, with AI help.
- **Slices build on merged work that no one has reviewed yet.** That replaces decision 0022's "merged, reviewed work". The lead-side review still comes before any paid run, freeze, or gate step that uses the code.
- **An owner's answer clears a change request.** The reviewer no longer has to re-approve.
- **The paid summary loses its two named member reviewers, and the standing review pairs end.** Member reviews stay welcome but optional.
- **Monday's development grid runs on scoring code whose findings can't change it.** Under decision 0028, as decision 0029 re-dated it, changes to grid-scored facts closed on November 8. A scoring finding made on November 9 goes to `W8-T1` or `W8-T4`, and the Gate 2 record states it. Floor cells are never re-scored.

**What doesn't change.** Every artifact-level review stays. GitHub enforces only that a record or CI change gets an approval from a second contributor (item 3). The rest is enforced by rule and by each lead-side review:

- the `SPEC.md` Section 5 source review;
- the golden-vector reviewer (decision 0006);
- the adaptation review;
- `W12-T3`'s numerical audit, which is a task, not a pull-request review;
- the project lead's approval of every claim, number, and limitation.

No scientific scope, gate date, tier rule, trial count, or spend figure changes. No result exists, and none is promised.

**Why.** On November 8, the project lead told the team that pull requests merge as soon as CI passes. Member review has become the slow step:

- `W7-T4` ([#54](https://github.com/marek-sm/CANARY/pull/54)) has carried a change request since October 25. It reports four reproduced readiness gaps.
- `W7-T5` ([#66](https://github.com/marek-sm/CANARY/pull/66)), `W8-T1` ([#74](https://github.com/marek-sm/CANARY/pull/74)), and `W8-T3` ([#77](https://github.com/marek-sm/CANARY/pull/77)) are green and unreviewed.
- Decision 0028 item 8's measurement-code reviews were due November 8.

The paid run on Monday, November 9 needs #54. Decision 0025 item 4 freezes the readiness checks at the first paid call, so #54 must be right before the paid-run record is written, whoever checks it.

**Where `SPEC.md` ties review.** Four places:

- Section 15's AI-assistant rule ("AI-generated code receives ordinary review and tests");
- Section 17's `CONTRIBUTING.md` row ("relax scientific review");
- Section 14's mandatory limitations;
- Gate 3's pass evidence in Section 11.

No pull-request approval is required anywhere in `SPEC.md`, and none of these passages is hash-pinned. This record edits them, with no pinned text changed.

## Options considered

1. **Keep member review before merge.** Rejected. It is the step that stalled #54, #66, #74, and #77, and it would hold Monday's paid run on one member's review.
2. **Merge on green with no review.** Rejected. It drops `SPEC.md` Section 15's ordinary review and leaves the paid runs and the freeze on code no one has read.
3. **The project lead reviews before every merge.** Rejected. It moves the bottleneck to a lead who works under 10 hours a week.
4. **Merge on green. Review results code on the lead side after the merge, and always before the next paid run, freeze, or gate step that uses it. Enforce that review in the paid-run gate and at Gate 3. Keep a second human on record and CI paths through GitHub.** **Chosen.**

## Decision

1. **Merge on green.**
   - An owner merges their own pull request once its required check, `test`, passes. No approval is required. The project lead's pull requests follow the same rule, with no bypass.
   - Required checks stay non-strict. If `main` goes red after a merge, the owner of that merge fixes it within 24 hours.
   - No paid run, freeze, or gate step runs on a red `main`.

2. **Change requests.**
   - A member's change request blocks the merge until the owner answers it in the thread, either with a fix or with a reply saying why not.
   - If GitHub still shows the pull request as blocked after the answer, the project lead dismisses the review and links the answer.
   - Owners keep decision 0021's 48-hour turnaround on comments, conflicts, and questions, through November 29 (decision 0030).

3. **A second human on records and CI, enforced by GitHub.**
   - `.github/CODEOWNERS` names all six contributors as owners of the record files: the JSON and JSONL files under `/corpus/` and `/oracles/authorization/`, everything under `/defenses/vectors/`, and `/.github/`. The code beside those records, such as `corpus/intake.py` and `oracles/authorization/audit.py`, isn't covered, so it merges on green like other code. The `main` ruleset requires a code owner's review and dismisses stale approvals on push.
   - So a pull request that adds, edits, or deletes a corpus record, a ledger row, a golden vector, a vector set, or a CI file needs an approval from someone other than its author. GitHub accepts any of the six, so it can't check that the approver is the named reviewer. The rule is that for a source record the approver is the `SPEC.md` Section 5 source reviewer, and for a golden vector the decision 0006 reviewer.
   - GitHub reads `CODEOWNERS` from the base branch, so a pull request can't lift its own requirement.
   - An approval on those paths is always the real review. It is never a click to let a merge through.
   - Each lead-side review also checks two things. Every `reviewed_by` value merged since the last review must name the person whose approval or posted sign-off covers it, and each source-record approval must come from that record's Section 5 reviewer. A mismatch is a blocking finding. A value that isn't a GitHub login, such as `"Chace"` in `defenses/vectors/datamarking-w5-t4.json`, is reported.

4. **What the lead-side review covers, and when.**
   - **Results and release code:**
     - the code, schemas, policies, and grid specifications under `runner/paid_run.py`'s `HASHED_DIRS`;
     - the scripts under `demo/` and `paper/`;
     - the sanitizer, report, figure, and release-bundle code.
   - **What it leaves out:** corpus and fixture records, which the source review covers, and `uv.lock`, which is pinned.
   - **When:** after the merge, and always before the next paid-run record, freeze, or gate step that uses that code.
   - **All other code** is reviewed the same way before the release freeze.

5. **How a review runs.**
   - Claude reviews the diff since the last review and writes `docs/reviews/YYYY-MM-DD-<scope>.md`. Its header names the commit, the `paid_run.code_digest` of that checkout, and the number of open blocking findings.
   - **The project lead reads and classifies every finding** (Section 15: humans decide whether a defect invalidates results). A finding is blocking if it could change a score, a count, a gate or readiness result, or a safety property.
   - **Blocking findings are fixed in follow-up pull requests** before that paid run or freeze, and each fix's diff gets the same review.
   - **Who fixes:** the owner, if 24 hours or more remain. Otherwise the project lead fixes it, as a visible scope change recorded in `TASKS.md`.
   - **Non-blocking findings** go to the owner, to fix by the next freeze, or are stated as limitations.
   - **Grid-scored code after November 8 is the exception.** Its findings follow decision 0028: they go to `W8-T1` or `W8-T4`, and the gate record states any that bear on a gate.
   - **A safety finding stops the paid run** until it is fixed.

6. **Enforcement in the paid-run gate.** By Friday, November 13, the project lead adds `python -m runner.lead_review attest docs/reviews/<file>.md` as lead scaffold, merged with W8 so Gate 3 freezes it.
   - The command appends a row to `~/.canary/lead_review.jsonl` on the project lead's machine. It uses the same account home as `runner/spend_ledger.py`, and the same stand-in under pytest.
   - Each row holds the checkout's `code_digest`, the findings file's SHA-256, and its open blocking count.
   - `paid_run`'s refusal, at both `record` and every paid call, requires a row that matches the checkout's digest, has 0 open blocking findings, and whose findings file in the checkout still matches its hash. Otherwise every grid, sweep, and rehearsal call is refused.
   - Collaborators can't write that file, since paid calls run only on the project lead's machine (decision 0023 item 8).
   - The live smoke is exempt, as it is from the paid-run record, because it scores nothing.
   - The build is tested on the mock provider, with a failing reproduction test first and an independent fix review.
   - **Monday, November 9 comes before this check exists.** Its review is written and merged before the record, and the Gate 2 record says the check wasn't yet in force.

7. **Gate 3.**
   - **Review timing:** from November 9, each merge of results code is reviewed within 24 hours. The whole-tree pass over item 4's scope starts on `main` on Wednesday, November 11, so on November 13 only that day's merges remain.
   - **New pass evidence:** an attested lead-side review of the frozen commit with 0 open blocking findings (`SPEC.md` Section 11).
   - **An open blocking finding at the Gate 3 step:** the step holds, within Saturday, November 14, for the fix and its review. If that can't close on November 14, the Gate 3 response applies, and a smaller prefix doesn't repair code. So the choice is `ENGINEERING` or `STOP`.

8. **Monday, November 9, before the paid-run record.**
   1. Each of the four gaps in the October 25 change request on #54 becomes a test in #54. Each test fails before any fix and passes after. A gap still present is fixed in the same push, which the project lead makes as a visible scope change, like the November 8 fallback push. `W7-T4`'s owner keeps the slice.
   2. The lead-side review covers:
      - #54;
      - every results-code change that merged with no member review: #70, #76, #78, #80, #82, and #83;
      - decision 0028 item 8's files: `runner/delivery.py`, the scoring in `runner/mock_slice.py` and `runner/execute.py`, `analysis/floor_count.py`, `analysis/request_effect.py`, and `analysis/gate2_budget.py`.

      Any member review of those files that has already posted counts. Readiness findings in #54 are fixed before the record. Scoring findings follow item 5's exception. A safety finding stops the run.
   3. The answer to the change request is posted, and #54 merges.
   4. The review's findings file merges.
   5. The paid run's fresh clone checks out the exact commit that step 2's review names. The paid-run record is committed on a branch on top of that commit. So a merge of #66, #73, #74, #77, or any other pull request on Monday can't put unreviewed code into the run.

9. **The project lead's capacity, a visible schedule decision.**
   - Claude builds the four tests, `CODEOWNERS`, and `runner/lead_review.py`.
   - The project lead's added time for November 9–15 is about 3.5 hours:
     - 45 minutes for Monday's findings;
     - 45 minutes for the rolling W8 reviews;
     - 45 minutes for the Gate 3 pass;
     - 30 minutes to review the `lead_review` build;
     - 30 minutes for record and CI approvals;
     - 15 minutes for the ruleset.
   - No record holds the project lead's baseline for the week, so the trigger is the project lead's own count. If the week passes 10 hours, the license choice and the author order move to November 16–20, recorded in `TASKS.md`. Only `W11-T5` uses them, and `W9-T5`'s `LICENSE` pull-forward waits with them. Nothing on the gate path moves. The gap sentence doesn't move: decision 0017 makes it due before the freeze.

10. **Sentences superseded.** Each phrase below is replaced as stated. The rest of each record stays in force.
    - **Decision 0015:**
      - Item 2's Monday post no longer names a reviewer.
      - Item 5's reviewer field becomes optional, except on item 3's paths.
      - "one reviewer per slice" in its kept list ends.
    - **Decision 0022:**
      - The Context's "merged, reviewed work" becomes "merged work".
      - In item 2, "merged with its named reviewer's approval" becomes "merged with CI green and, for results code, the lead-side review decision 0031 requires".
      - Item 6's named reviewer in start notices and its 48-hour reviewer clause end.
      - Item 8's "One reviewer per slice" ends, and so does the reviewer in the Monday post.
    - **Decision 0025:**
      - Item 2's "under each slice's one reviewer" ends.
      - In item 4, "merged with reviewer approval" becomes "merged".
      - Item 5's and item 9's 24-hour reviews end, and "a last push its reviewer approves" becomes "a last push".
      - Item 14's "one reviewer per slice" ends.
    - **Decision 0027:** item 6's "One reviewer per slice" ends.
    - **Decision 0028:**
      - Item 8's member reviews of measurement code, and T1's recheck of `0434116`, become item 8 above. Their routing is unchanged.
      - Item 8's "`W11-T3`'s last approved push" becomes "last push".
    - **Decision 0029:**
      - Item 2's "then T1's review", T1's review of the `W7-T4` push, T2's review of `W7-T5`, and the paid summary "reviewed by `W7-T3`'s and `W7-T1`'s reviewers" end. Each item now merges on green after item 8's review.
      - Item 4's "each reviewed within 24 hours" ends.
      - In item 5, "reviewed by" becomes "merged by", and "`W11-T3`'s last approved push" becomes "last push".
    - **Decision 0030:**
      - In item 4, "reviewed and merged by" becomes "merged by".
      - Item 7's "A slice the project lead builds keeps its standing-pair member reviewer" ends. Item 7's own sentence, "Any lead-only review is recorded as a limitation", is now met by the Section 14 bullet.
    - **Decision 0021 needs no amendment.** Its review dates were already replaced by decisions 0029 and 0030, and its 48-hour rule binds authors, not reviewers. Item 8's sentence that the project lead remains the source reviewer is an artifact review, so it stays.

11. **The `main` ruleset.** After this record merges, the project lead changes the `protect-main` ruleset:
    - required approvals go to 0;
    - code-owner review is required;
    - last-push approval and the extra approval for unattributed changes are both off;
    - `test` stays the only required check, non-strict;
    - the administrator bypass is removed.

    Then #66 should show as mergeable, and #73 should stay blocked until it has a code owner's approval. If code-owner review doesn't take effect with 0 required approvals, required approvals go back to 1 the same day and `STATUS.md` records it. The project lead then adds a `pull_request_target` check that reads a pull request's files only as data and enforces item 3. Every later ruleset change is recorded in `STATUS.md`.

12. **Numbering and version.** This record takes 0031. `SPEC.md` moves to v1.22.0. Only unpinned text changes: Section 11's Gate 3 pass evidence and response, Section 14's mandatory limitations, and Section 15's AI-assistant rule.

## Consequences

- **Faster merges.** #66, #74, and #77 can merge as soon as their owners choose. #54 merges Monday, after its four gap tests and the review.
- **The project lead carries the review.** That is about 3.5 more hours in November 9–15, under item 9's rule. Claude does the reading, and the project lead classifies the findings.
- **Members still approve record and CI changes.** A `W8-T2` freeze push that changes corpus records needs a code owner's approval, and by rule that is the source reviewer, as before. A `W8-T4` vector edit needs another contributor's approval.
- **The paper's limitations grow by one bullet.** Results code had no independent human review, and lead-built code had no second human reviewer.
- **The guarantee moves from a person to a check.** Once item 6 lands, no paid run or sweep starts on code without an attested review.

## Verification

- `tests/test_contract_lock.py`, `tests/test_corpus_rules_freeze.py`, and `tests/test_request_effect.py` pass unchanged, which shows no pinned `SPEC.md` text changed.
- `tests/test_status_consistency.py` and `tests/test_tasks_dependencies.py` pass, because no slice table changes shape and no `Depends` cell changes.
- After the ruleset change: #66 shows as mergeable, and #73 stays blocked until a code owner approves it.
- By November 13: `runner/lead_review.py` and the `paid_run` refusal merge with a test that fails before the change and passes after.
- At Gate 3: the record names the attested review of the frozen commit and its open blocking count, 0.
