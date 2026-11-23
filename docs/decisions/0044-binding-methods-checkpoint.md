# 0044: The November 21 methods checkpoint sent to the research mentor binds every later change

- Status: Accepted. Approved by the project lead on 2026-11-21, and in force from this record's merge; drafted with AI assistance.
- Date: 2026-11-21
- Decision scope: Governance
- Secondary scopes: Release
- Related specification sections: Sections 11, 14, 16, and 17
- Related records: [decision 0001](0001-document-authority.md), [decision 0031](0031-merge-on-green.md), [decision 0043](0043-gate4-and-demo-day-dates.md), and [`docs/commitments.md`](../commitments.md)
- Supersedes: None

## Context

On November 21, 2026, the project lead sent the project's research mentor a methods checkpoint. It covers the research question, methods, measurement, analysis plan, design safeguards, ethics, development evidence, status, limitations, and three discussion items. The paper is written to it. The project lead ruled that nothing in it may be contradicted or changed without the lead's approval.

That rule lived only in the lead's private notes, so contributors and coding tools couldn't see it. `AGENTS.md` is the file every coding tool reads first, and `CONTRIBUTING.md` is the file every contributor reads first. Neither pointed to the checkpoint.

The checkpoint was written from `SPEC.md` and the decision records. It cites no private file, quotes no leadership document, and holds no sweep or C1 outcome. Its byline names the mentor, a private individual who hasn't consented to public attribution (`AGENTS.md`, public-repository hygiene). A few of its status facts aren't yet in a tracked file: the season spend, the contributor agreements, the pending console check, the November 19 manifest re-check, and the fallback audit's AI assistance. The November 22 `STATUS.md` rollup publishes them. This record merges only after that rollup is on `main`, so `STATUS.md` stays their home.

## Options considered

1. **Keep the rule in the lead's private notes and in AI-tool memory.** Members and their tools never see it, so a change could contradict the checkpoint unnoticed.
2. **Publish the checkpoint with its byline.** It names a private individual without consent. It also adds nothing a reader could verify.
3. **Publish the checkpoint with only its byline left out, in a tracked file that every contributor and tool reaches, pinned by hash.** Chosen.

## Decision

1. **The file.** [`docs/commitments.md`](../commitments.md) holds the checkpoint as sent, with the byline left out and the tables restored from the sent document's cell order. Before merge, a local check flattened the restored tables back to one cell per line and confirmed that the text matches the lead's as-sent copy word for word. The file also holds the check below, the list of dated-status sentences, and a log of corrections sent to the mentor.
2. **It owns nothing scientific.** `SPEC.md`, the schemas, `protocol/active.json`, and the decision records keep every meaning. The file adds a check before a change. It never removes or delays a Section 11 step, and a deviation entry still opens before any fix merges. It isn't a seventh authority in `AGENTS.md`'s authority model. This record adds one row to `SPEC.md` Section 17's authority table and supersedes nothing in decision 0001.
3. **The check.** Before changing code, `SPEC.md`, a decision, `TASKS.md`, the paper, the README, the demo, or the release, check the change against the file. If it would contradict a commitment, stop and tell the project lead, and the change waits for the lead's decision. If the lead approves it, the mentor gets a disclosed correction, and the lead logs it.
4. **An existing disagreement** between the checkpoint and `SPEC.md` or a decision is reported to the project lead. Work on the affected point waits for the lead's ruling. Only Section 11 steps go ahead in the meantime. Scientific meaning still comes from `SPEC.md`, and neither text is edited silently.
5. **Dated status.** The sentences and table rows the file lists state facts as of November 21. They are quoted as sent and never rewritten. When an event overtakes one materially, the project lead decides whether the mentor gets a correction. `STATUS.md` holds current values. Every other sentence is a commitment.
6. **The paper.** `paper/lead-inputs.md` still governs paper inputs. The paper may add what `SPEC.md` or a decision requires: the full condition identifiers, the separate descriptive C1 table, limitations the checkpoint leaves out, and decision 0043 item 2's `STOP` when no headline comparison stays eligible. The paper may not contradict a commitment.
7. **Feedback isn't review.** The mentor's feedback on the discussion items can shape the paper's emphasis within the checkpoint. It is not peer or external review (`SPEC.md` Sections 14 and 16).
8. **Members.** No slice gains an acceptance criterion. The project lead checks claim-bearing work against the file at decision 0043's claim-language, numbers, README, and demo-wording steps. `AGENTS.md`, `CONTRIBUTING.md`, and `TASKS.md` point to the file, and an owner who thinks a change might contradict it says so in the pull request.
9. **Publication and privacy.** The project lead consents to publishing the checkpoint text. It is a lead-written methods summary drawn from public records, with nothing written by the mentor and no personal data, so it isn't the private correspondence that `AGENTS.md` bars. The byline is left out, and the file says "research mentor". The corrections log holds only the lead's corrections, never the mentor's replies. No hash of the as-sent text is published, because a hash could confirm a guessed name.
10. **Bare condition labels.** The quoted checkpoint uses the bare labels D0, D1, and D2. They stay as sent inside the pinned section only. Everywhere else, the `AGENTS.md` rule on full identifiers applies.
11. **The pin.** The text strictly between `<!-- checkpoint:begin -->` and `<!-- checkpoint:end -->`, as UTF-8 with LF line endings and with its leading and trailing newlines stripped, has this SHA-256:

    Checkpoint section SHA-256: `08d2a86407458fad03740d44f81b408841cfd8ceab2850a2bf52232036156a27`

    `tests/test_commitments.py` reads that value from this record and fails if the section changes. This record is append-only once accepted, so the pin protects the text from this record's merge onward.

## Consequences

- Every contributor and coding tool sees the checkpoint before changing anything.
- A change that would contradict it stops at the project lead, and every approved correction reaches the mentor and the log.
- `SPEC.md` keeps sole scientific authority, and Section 11 runs as written.
- The project lead spends about 0.5 hours reviewing this record, plus about 0.25 hours at each of the four claim-bearing checks.
- A pointer in `.github/pull_request_template.md` would need a second contributor's approval under decision 0031's code-owner rule, so it isn't part of this record.
