# 0015: Cut process rules that don't protect the research

- Status: Accepted. Approved by the project lead on 2026-10-12; drafted with AI assistance.
- Date: 2026-10-12
- Decision scope: Governance
- Secondary scopes: Protocol
- Related specification sections: Sections 11 and 17
- Supersedes: [decision 0011](0011-week8-replan.md) item 8, only where it names the Monday issue as the place to re-accept a changed slice; [decision 0014](0014-selection-prefixes-and-task-order.md)'s consequence that `W7-T2`'s owner re-accepts in its W7 issue, only for that venue

## Context

The project lead asked to cut rules that cost the team time without protecting the research. The trigger was `SPEC.md` Section 11's requirement of a separate GitHub issue for every material post-freeze change: [decision 0014](0014-selection-prefixes-and-task-order.md) merged on October 12 as #41 without that issue, although `docs/protocol_deviations.md` DEV-0001 already recorded the defect, the affected text, outcome visibility, and the response.

A review of `SPEC.md`, `TASKS.md`, `STATUS.md`, `AGENTS.md`, `CONTRIBUTING.md`, the pull-request template, and `docs/` sorted each process rule by whether it protects the research claims, safety, or spend, keeps a part-time team on schedule, or only re-records a fact already recorded elsewhere. The club's judging criteria score the problem statement, research rigor, conceptual understanding, presentation design, and prompting efficiency. None of them asks for the rules this record removes.

Verified constraints:

- Section 11's "After freeze" text is outside every hash-pinned span: `tests/test_contract_lock.py`, `tests/test_corpus_rules_freeze.py`, and `tests/test_request_effect.py`. It is not on the week-5 lock list or in the Gate 3 hash set. Decisions 0007 and 0009 apply Section 11 to the text they froze, but Section 11 itself is unfrozen, so changing it is a pre-freeze change and needs no deviation entry.
- The issue's one unique property was a public timestamp before the fix. A deviation entry opened in a pull request before the fix carries the same timestamp.
- No test reads the pull-request template.

## Options considered

1. **Keep every rule.** Rejected. The weekly slice issues alone cost the project lead about 50 minutes a week to copy rows that `TASKS.md` already holds.
2. **Cut broadly, including the contribution records, `SPEC.md` Sections 12, 13, 16, and 17, and the Section 5 selection mechanism.** Rejected for now. Contribution records feed work after October: the video, the release, the `ENGINEERING` finding, and the judge drill. Section 5 is pinned and was just changed. The other sections need their own decisions at the points they matter.
3. **Cut four rules and trim the pull-request template, keeping every rule that protects validity, safety, spend, or the gate schedule.** Chosen.

## Decision

1. **No separate issue for a post-freeze change.**
   - Section 11 "After freeze" item 1 becomes the dated deviation entry.
   - The entry is opened in a pull request before any fix merges or any rerun starts. It records the defect, the affected cells or validation checks, the scope determination, and outcome visibility.
   - It merges complete, with the repair, so a merged entry is never edited.
   - Old item 6 is deleted, so items 2–5 keep their numbers, and DEV-0001's references to "step 3" and "step 5" stay correct.
   - `SPEC.md` moves to v1.9.0.
2. **No weekly slice issues.**
   - On Monday the project lead posts the week's five slices in the team channel. Each gets its owner, reviewer, due date, any `BLOCKED` producers, and a link to its `TASKS.md` row.
   - GitHub already records when each input merged and each pull request opened, so nobody logs those dates.
   - A changed slice is re-accepted by replying to that week's post, and the Sunday rollup records the date. The `TASKS.md` owner column stays the authority for ownership.
3. **No Monday `STATUS.md` update.** The Sunday rollup is the weekly record. The Monday rule conflicted with it.
4. **No 24-hour next action for each blocker.** Blockers are still recorded with a named owner in the week's team-channel thread, and the Sunday rollup carries them into `STATUS.md`. Whether a slice is blocked still follows from its `Depends` cell and `main`.
5. **A shorter pull-request template.** It keeps every safety, measurement, release-claim, and documentation check, merged into four checkboxes, plus the slice, owner, reviewer, frozen-artifact, and evidence fields. It drops the specification-sections, tier-impact, and generated-artifacts fields and the owner-attestation checkbox. The slice's `TASKS.md` row, the lead's tier decisions, the diff, and decision 0002 already carry those. `CONTRIBUTING.md`'s rule on independent review is unchanged.

**Kept:**
- the freeze;
- the deviation log, now opened before the repair;
- preserved old data, symmetric reruns, and the version increment;
- one reviewer per slice;
- recorded blockers;
- weekly contribution records;
- the Sunday explanation of each merged pull request and the October 25 practice round;
- the Thursday, Friday, and Saturday cadence;
- the paid-run condition;
- the dependency rule and its test;
- the gate-pass consistency test.

## Consequences

- #41's Section 11 issue, which DEV-0001 cites by title, was not opened before #41 merged. The project lead opens it once, after the merge, with that title and a line saying so. That makes the existing record accurate without editing the append-only log or decision 0014. Later changes follow the new item 1.
- `AGENTS.md`'s change table and `CONTRIBUTING.md` list the Section 11 steps with the deviation entry first. `AGENTS.md`'s row also gains the new experiment or validation ID, which it had left out.
- `TASKS.md`'s Monday and Friday cadence lines change. The W7 recovery bullet on issue logs and the W8 re-acceptance line are marked superseded rather than deleted. No owner, estimate, `Depends` cell, or Committed text changes.
- `STATUS.md` keeps its dated October 11 text with two dated notes. The next rollup records this decision and v1.9.0.
- The team channel becomes the week's working notice of blockers and re-acceptances. `TASKS.md` stays the authority for slice state, and `STATUS.md` stays the dated record, as [decision 0003](0003-weekly-status-artifact.md) requires.

## Verification

- The full no-credit suite passes, including the unchanged pinned-text tests, `tests/test_tasks_dependencies.py`, and `tests/test_status_consistency.py`.
- `python -m analysis.report_shells --check` passes.
- A search of the tracked documents finds no remaining requirement for a post-freeze issue, a weekly slice issue, or a 24-hour blocker action outside superseded or dated history.
