# 0022: Start on merge: slices and gate steps start when their inputs land, and dates become deadlines

- Status: Accepted. Approved by the project lead on 2026-10-25; drafted with AI assistance.
- Date: 2026-10-25
- Decision scope: Protocol
- Secondary scopes: Governance
- Related specification sections: the preamble, Sections 0, 9, 11, 12, and 14
- Supersedes: in `TASKS.md`, the "before its Monday" timing of the dependency rule and the pull-forward rule, the same-week planning lines under the dependency rule, the Saturday and Friday-cutoff timing of the gate-steps paragraph, the fixed weekday timing of the weekly cadence, "one lattice slice per week", and the Standing row's "the one peer pull request"; decision 0015's kept Thursday, Friday, and Saturday cadence (timing only); decision 0021's "no W7 slice starts before October 26" (item 2), the fixed-day wording of its items 3–5 (the dates stand as latest dates), its item 4 statement that no other row may plan around same-week work, and its item 8 pull-forward limit to work merged before that week's Monday; and decision 0014's "merged before its Monday" timing for `W8-T4`.

## Context

Decision 0021 gives each lattice week one club week. One week of work per week finishes by the December 6 release freeze, with no slack, and W12 and W13 share club week 15. Two calendar rules stop an early finish from winning any of that time back:

- **The dependency rule.** "A slice uses only work that is merged before its Monday." A W7 slice that merges on Wednesday still leaves its W8 consumer waiting until the next Monday.
- **The gate steps.** They run on Saturday, on work merged by Friday.

W7 and W8 can't run side by side. W8 freezes the tasks, the corpus, and the defenses from W7's grid results and the tier decision. So the only lever is to start each piece the day its inputs land.

What the dependency rule protects stays: a slice uses only merged, reviewed work that its `Depends` cell names, and never plans around unmerged work. `tests/test_tasks_dependencies.py` checks the `Depends` cells, and no `Depends` cell changes. Decision 0015 kept "the dependency rule and its test"; this record keeps both and changes only when a slice may start.

## Options considered

1. **Keep Monday starts and Saturday gate steps.** Rejected. An early finish wins nothing back, and club week 15 stays the only margin.
2. **Run W8 alongside W7.** Rejected. W8 freezes from W7's grid results and the tier decision, so starting it before them builds on work that will change.
3. **Start each slice and gate step when its inputs land, keep every scheduled date as a deadline, and let no slice cross a gate before that gate runs.** Chosen.

## Decision

1. **Start on merge, within a gate's boundary.** A slice starts the day every input its `Depends` cell names is on `main`, even before its scheduled Monday. A `(Mon)` marker in a `Depends` cell now reads "by the slice's start". Across a gate, a slice also waits for that gate:
   - **W8** starts only after the Gate 2 step. Its tier-dependent steps also wait for the project lead's tier, budget, model, and decoding input (item 3).
   - **W9** starts at the Gate 3 step, which is the freeze, or on its scheduled Monday, November 9, whichever comes first, so it never starts later than before. Merged W8 work may still change until W9 starts, for example through a decision 0014 step-6 rerun. After that, decision 0021's rule holds: W8 work merged by the November 6 review cutoff doesn't change, and late W8 work may merge through November 10. That keeps the reason behind the rule, which is that W9 has started on it (decision 0011 item 1). `W9-T3`'s sweep step still starts on the Gate 3 record.
   - **W11** keeps its inputs: `W9-T3`'s records and the supported-results decision. Its audits still finish before the absolute data cutoff, so repair stays possible.
   - **W12** starts after the absolute data cutoff, or earlier once Gate 4's integrity checks pass, `W11-T1`'s and `W11-T4`'s audits have merged, and no repair is pending. Either way, no W12 output binds to data that a repair could still change.
   - **W13** keeps decision 0021's named same-week start inside club week 15.
2. **Gate steps run when their inputs are reviewed and merged.** The project lead runs a gate step on the first day every slice it uses is merged with its named reviewer's approval, and every lead input it uses is on `main`. For the Gate 3 step that includes decision 0012's output wiring. The scheduled date becomes the latest date.
   - The project lead may hold the Gate 3 step, still no later than November 11, for decision 0009 item 7's optional floor rerun.
   - Decision 0012's notice to `W9-T3`'s owner comes at the November 6 review cutoff, or earlier, on the day W8's last slice merges.
3. **The tier, budget, model, and decoding input waits for all of W7.** It comes after the Gate 2 step and after every W7 slice has merged. That covers:
   - the coverage smokes, which every empirical tier needs (`SPEC.md` Section 12 step 3);
   - the built C1 controls, which set the C1 count;
   - `W7-T2`'s reviewed pool, which can cap the tier (Section 12);
   - the development task-completion evidence the model choice uses (Section 9).

   It may come before November 1. If a W7 slice hasn't merged by November 1, the input comes November 1 from the merged evidence, as under decision 0021.
4. **Dates become deadlines, except where order matters.**
   - **Latest dates:** the Gate 2 step by October 31, the tier input by November 1, the Gate 3 step by November 11, and the Gate 5 step by December 3.
   - **The absolute data cutoff** stays Sunday, November 22. Data may lock earlier once Gate 4 passes and no repair is pending, never later.
   - **Gate 4** stays a target, November 15, with its contingency window up to the cutoff.
   - **The release freeze** comes no later than December 6, and still after the judge-readiness drill and the paper leads' final draft.
   - Decision 0021's slip rule and tripwires keep their dates as latest dates. No date moves later.
   - The 72-hour slice clock still counts from the scheduled Monday. A slice that starts early has more time, not an earlier deadline.
5. **Week 14 and the folded rows.** No slice is expected to start or run in club week 14, November 23–29. Work whose inputs land then starts Monday, November 30. The folded W10 rows carry no work and never start.
6. **Owners and reviewers.**
   - When a slice's inputs land, its owner starts it. The project lead posts a start notice in the week's team-channel thread, naming the inputs that landed and the slice's named reviewer. A slice that starts before a lead input is due records the missing input as one blocked step, under the existing missing-input rule.
   - An owner holds one open slice at a time. The next one starts after the current one merges, and a second slice is still allowed only for an explicit pairing reason. Optional pull-forward, including decision 0021 item 8's named pull-forwards, isn't an open slice.
   - Reviewers review their pair's pull requests as they open, within decision 0021's 48 hours.
   - This changes no slice's scope, inputs, deadline, or acceptance evidence, which are what an owner accepts. It is a team rule, like decision 0021's 48-hour turnaround, and takes effect when it merges.
7. **Pull-forward.** Its limit changes from "merged before that week's Monday" to "merged before you start it". Optional pull-forward still comes after committed work, and it never moves work that needs a later gate's decision or freeze ahead of that gate. The W9 boundary in item 1 applies to W9 slices, not to decision 0021 item 8's named pull-forwards, which use only development records and `W5-T5`'s shells.
8. **Unchanged.**
   - One reviewer per slice.
   - The paid-run condition.
   - The `SPEC.md` Section 9 development ceiling.
   - The freeze before any official outcome is inspected.
   - No evaluation candidate on a live model before the freeze.
   - Decision 0021's named same-week exceptions.
   - The Monday post (decision 0015), which still names each slice's owner, reviewer, latest date, and `BLOCKED` producers.
9. **`SPEC.md` moves to v1.16.0, with unpinned text changes only.** The preamble's date paragraph, Section 0's freeze and release rows, Section 11's freeze heading paragraph, and Section 14's release tag now read "no later than". The Section 11 gate table keeps its targets, and the absolute data cutoff stays as written.
10. **Numbering.** This record and its `SPEC.md` version follow merge order: if another record merges first, this one takes the next free number and minor version before it merges.

## Consequences

- **Time comes back only when work lands early.** The rule changes nothing until a slice or gate step finishes before its date. The corpus, `W6-T2`, still gates W7's paid work.
- **The project lead's load moves earlier.** Gate steps and start notices can fall on any day. Club week 10, which already holds the rolling source review, may also hold an early Gate 2 step and tier decision.
- **The fixed outside dates cap the gain late in the schedule.** The paper leads' November 16 draft, the November 30 hardware confirmation, and the December 3 final draft don't move earlier.
- **Week 14 stays dark,** so an early finish in club week 13 shows up as slack in club week 15, not as work over the break.

## Verification

- `tests/test_tasks_dependencies.py` passes unchanged, because no `Depends` cell changes.
- `tests/test_contract_lock.py`, `tests/test_corpus_rules_freeze.py`, and `tests/test_request_effect.py` pass unchanged, which shows no pinned `SPEC.md` text changed.
- `tests/test_status_consistency.py` passes against the October 25 rollup.
- `TASKS.md`'s dependency rule, pull-forward rule, gate steps, lead-inputs introduction, weekly cadence, and Standing row match this record.
