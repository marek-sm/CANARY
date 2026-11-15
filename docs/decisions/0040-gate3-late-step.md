# 0040: Run the full `F20` Gate 3 step on November 15, one day after every November 14 deadline was missed, as `SPEC.md` Section 11's second recorded exception

- Status: Proposed. Drafted with AI assistance; approved by the project lead by merging this record on November 15.
- Date: 2026-11-15
- Decision scope: Protocol (schedule, before the freeze)
- Secondary scopes: Governance
- Related specification sections: the preamble and Sections 0, 11, and 12
- Related records: [decision 0025](0025-full-study.md), [decision 0029](0029-gate-chain-shift.md) items 5 and 6, [decision 0031](0031-merge-on-green.md), [decision 0038](0038-gate3-report-module.md), and [decision 0039](0039-gate3-host-environment.md).
- Supersedes, for the words named only, and only their times, not the rules around them:
  - [decision 0029](0029-gate-chain-shift.md) item 5's "Gate 3 runs Saturday, November 14" and "The sweep runs Saturday, November 14";
  - [decision 0038](0038-gate3-report-module.md) item 1's "Section 11's date … don't change", for the date only;
  - decision 0038 item 6's "By 9:00 pm on November 14", for the review's attestation, and "by 11:59 pm";
  - [decision 0039](0039-gate3-host-environment.md) item 1's "opened by 7:00 pm and merged through 9:00 pm", for the host-environment PR (#111);
  - decision 0039 item 4's "merged by 9:00 pm" and "by 11:59 pm", and with them its `STOP` outcome. Its "nothing is relaxed" and no-fallback sentences stay, read against the November 15 times in item 1 below;
  - `TASKS.md`'s "A Gate 3 miss on November 14 takes the Section 11 Gate 3 response", for the date only;
  - `TASKS.md`'s November 14 lead-inputs row, "If it misses, the `SPEC.md` Section 11 Gate 3 response applies with no fallback, which is `STOP` (decision 0039 item 4)".

  Nothing else in those records changes.

## Context

Every November 14 deadline on the Gate 3 path was missed. Each time below is Pacific time.

| Deadline | Source | What happened | Evidence |
|---|---|---|---|
| The report module PR, by 6:00 pm | Decision 0038 item 7 | #108 merged at 7:21 pm, first rather than last | GitHub merge time, `31d8a7d` |
| The `W8-T5` PR, by 9:00 pm | Decision 0038 item 1 | #109 merged at 7:53 pm, one day after the slice's November 13 last merge | GitHub merge time |
| `D_G` attested, by 9:00 pm | Decision 0038 item 6 | Attested before 8:00 pm, on `main` with #108 reverted | The project lead's statement |
| The host-environment PR, opened by 7:00 pm | Decision 0039 item 1 | #111 opened at 8:16:45 pm | GitHub `createdAt` `2026-11-15T04:16:45Z` |
| The host-environment PR, merged by 9:00 pm | Decision 0039 items 1 and 4 | #111 merged at 9:18:40 pm, as `2cf34f9` | GitHub `mergedAt` `2026-11-15T05:18:40Z` |
| `D_H` attested, by 9:00 pm | Decision 0038 item 6 and decision 0039 items 3 and 4 | Attested after 9:18 pm, on `2cf34f9` with #108 reverted | The project lead's statement |
| The final digest `e36bd5ba…23a8` attested | Decision 0039 item 3 | Attested on `2cf34f9` before 9:32:10 pm | The project lead's statement; the bound is commit `340efb2` (9:32:10 pm), a paid-run record that `runner.paid_run record` writes only for an attested checkout |
| The step committed on a pushed branch, by 11:59 pm | Decision 0038 item 6 and decision 0039 item 4 | Not done | — |
| Gate 3, November 14 | `SPEC.md` Section 11 | Missed | — |

Before writing this record, the project lead was first told that the window was met, which was wrong. The report was corrected that evening.

As written, decision 0039 item 4 makes the Gate 3 response `STOP`: 0 of the 1,092 planned official trials, and no comparative claim (`SPEC.md` Section 12). Decision 0038 Option 4 had rejected "Run Gate 3 after November 14". This record does it anyway, after the miss, with `STOP` known.

Everything the step freezes is unchanged:
- The four late inputs are merged.
- The attested digests are those named in the review files before the window closed. Each was computed from the merged content in advance.
- No evaluation, official, or C1 outcome exists.

## Options considered

1. **`STOP`, as decision 0039 item 4 says.** Rejected. It loses all 1,092 official trials and every comparative claim.
2. **`ENGINEERING`.** Not available. Decision 0039 item 4 leaves the host-environment pass item unmet at every tier when #111 misses, and this step would still be late.
3. **Move the dates one day, change nothing else, and disclose it.** Chosen.

## Decision

1. **Dates, for the fall 2026 run only, moved once.**
   - Gate 3 moves from Saturday, November 14 to Sunday, November 15.
   - #111 counts as the fourth late input as merged, at 9:18:40 pm on November 14.
   - The three attestations count as made.
   - "The step has run" means these are committed on a pushed branch by 11:59 pm on November 15:
     - the step's driver;
     - `protocol/active.json`;
     - `protocol/sweep_spec.json` and `protocol/c1_spec.json`;
     - the Gate 3 record.
   - The date moves this once. If the step misses that time too, nothing in this record moves it again, and `SPEC.md` Section 11's missed-gate rule applies as written. That is the existing rule, not a new fallback.
2. **Nothing else changes.**
   - Decision 0039 item 5's inputs are used as written. That includes `schedule_seed` `CANARY-2026-sweep-20261114` and decision 0038 item 4's analysis seed `20261114`. The dates inside them are labels, not deadlines.
   - `code_commit` is the commit the step runs on, as decision 0039 item 5 says: the commit on `lead/gate3-step` that adds the driver. That commit is `2cf34f9` plus only paths outside `runner/paid_run.py`'s `HASHED_DIRS`:
     - `protocol/paid_run_record.json` (`340efb2`);
     - the driver.

     Its hashed content is therefore `2cf34f9`'s, and the digest print is `e36bd5ba…23a8`.
   - These are unchanged:
     - the `F20` tier and its 1,092 official trials (1,080 sweep and 12 C1);
     - every Section 11 Gate 3 pass item;
     - every check in decision 0038 item 6 and in decision 0039's Verification;
     - `make report` as an `F20` pass item.
   - `python -m analysis.gate3_hashes --check` stays strict on the host environment, so it fails closed if the machine changed overnight.
   - If any pass item fails at the step, the ordinary Section 11 Gate 3 response applies.
   - No other deadline that names the Gate 3 freeze moves with it, so no other item gains a day. These keep their November 14 dates:
     - the gap sentence's cutoff (`TASKS.md`, `STATUS.md`);
     - the raw-record folder's sweep-time owners;
     - the November 14 lead-inputs rows' merge times.
   - Nothing else merges to a `HASHED_DIRS` path before the step.
3. **Order.**
   1. This record's pull request merges first. It changes no `HASHED_DIRS` path.
   2. No paid or provider call happens until it has merged, and the step doesn't run until it has merged.
   3. The driver is committed before it runs, because a gate step runs committed code (`TASKS.md`, gate steps). The Gate 3 record gives its SHA-256.
   4. After the step, the project lead writes a new paid-run record from a new mock grid on the step branch's final commit, before any paid sweep or C1 call. Decisions 0025 and 0029 require a record written after Gate 3, and `TASKS.md`'s W9 note one on the frozen commit. The November 14 record, `340efb2`, stays in history.
   5. The attested review files (`docs/reviews/2026-11-14-*.md`) aren't edited, because `runner.lead_review` rechecks each one's SHA-256.
   6. The sweep and the C1 run execute in the step's checkout, which holds that mock grid.
   7. The step's pull request merges only after this one.
4. **Downstream dates.**
   - **The sweep and the official C1 run.** They start once the step's pull request has merged, on November 15 or 16. They still end by the end of Tuesday, November 17 (decision 0029 item 5; was November 14–17). That gives at most three days instead of four.
   - **Whether that is enough is an inference from development trials, not a committed measurement.** The November 9 live development grid ran 90 trials in about 4.5 minutes, which suggests about an hour for 1,092. If the sweep doesn't complete, the existing Gate 4 rules govern.
   - **These dates don't change:**
     - `W9-T3`'s sweep, audit, and generated-results pull request, November 18;
     - the Gate 4 target, November 19;
     - the final supported-results decision, November 20;
     - `data_cutoff` `2026-11-22`;
     - Gate 5, November 26;
     - the release freeze, at noon on November 29;
     - decision 0039 item 6's macOS update freeze, from the step through November 17.
5. **Methods cost, stated once.** Moving a pre-registered gate date after it was missed weakens what the pre-registration commits to: the deadline didn't constrain the work it was set for.
   - The Gate 3 record, `STATUS.md`, and the paper state that the date was missed and then moved. They never present it as met.
   - What limits the harm:
     - no official, evaluation, or C1 outcome exists;
     - the frozen content is byte-identical to the digests named before the window closed;
     - only dates change.
6. **Disclosure.**
   - This record was written after the miss, with `STOP` known as decision 0039 item 4's response.
   - A `STOP` step was drafted the night of November 14 and then discarded. It was never committed or pushed.
   - The step driver was rehearsed twice on November 14, at 6:17 pm and 6:29 pm, before the miss. The rehearsals ran in a session scratchpad and were never committed.
     - Both used decision 0039 item 5's inputs and seed, and both generated the `F20` schedule: 1,080 + 12 = 1,092.
     - A schedule follows deterministically from inputs already fixed, and carries no outcome.
     - The step regenerates it from committed code.
   - The first mock grid (90 of 90 trials) and paid-run record (`340efb2`) were made at 9:30–9:32 pm, after the miss. Item 3's new record supersedes them for the sweep.
7. **`SPEC.md` Section 11.**
   - "the one recorded exception below" becomes "the two recorded exceptions below".
   - The Gate 3 row's target, and the Gate 3 dates in the preamble, Section 0's full-scope operating card, and the week-8 freeze text, say that the date moved after the fact to November 15 for the fall 2026 run.
   - The "Gate 3 fails" response adds this sentence: "For the fall 2026 run only, decision 0040 moves the Gate 3 date to November 15, after it was missed, and changes no pass evidence; it applies only because its record merged before any official trial ran or any evaluation outcome existed ([record](docs/decisions/0040-gate3-late-step.md))."
   - This text isn't pinned (decision 0009 item 1), so this is a schedule change before the freeze (`AGENTS.md`, "Change classification", third row), as in decision 0029.
   - `SPEC.md` stays at v1.24.0.
     - `tests/test_c1_reference_policy.py` (decision 0037) asserts the v1.24.0 header.
     - That test's SHA-256 is pinned in `tasks/freeze.json`, a `HASHED_DIRS` path. A version bump would therefore change the attested digest `e36bd5ba…23a8`, and the step couldn't run on it.
     - No rule needs a bump before the freeze: the version increment is a rule for a material change after it (`AGENTS.md`, "Change classification", fifth row; `SPEC.md` Section 11).
     - This record's merge commit identifies the edited text.
   - No protocol-deviation record is needed, because nothing is frozen.
8. **Authorities.** Nothing is frozen, so this record's pull request updates every affected authority together:
   - `SPEC.md`, as item 7 says;
   - `STATUS.md`: the next-gate row, the documentation baseline's version, the owner-outcomes sentence, and the week's dates;
   - `TASKS.md`:
     - the Gate 3 record entry and the gate-steps paragraph;
     - the W8 gate-step row and the November 14 lead-inputs rows;
     - the W8 heading, the W9 section, and the `W9-T3` row;
     - the gate-dates note;
     - the club-week-12 row and the Saturday cadence;
   - `README.md`'s decisions row.
9. **Numbering.** This record takes 0040.

## Consequences

- **The project lead's added time** is about 2.5 hours on November 15: this record's review and merge, the step's checks, `python -m runner.paid_run check`, the new mock grid and paid-run record, and the step's pull request.
- **The sweep loses up to a day** of its window. Item 4 gives the evidence that it still fits.
- **The study's account of Gate 3 changes.** The paper reports a Gate 3 that ran one day late under a rule written after the miss. This record claims nothing about what any estimand will show.

## Verification

- At the step, every check in item 2 exits 0. Both schedule refusals are `None`, and the schedules count 1,080 + 12 = 1,092.
- `python -m analysis.gate3_hashes --check protocol/active.json` and `python -m runner.paid_run check` pass on the step branch's final commit.
- `tests/test_status_consistency.py`, `tests/test_tasks_dependencies.py`, and the full suite pass on this record's pull request.
