# 0035: Register the S1 stress experiment for after Demo Day, and give the demo script both outcomes

- Status: Accepted. Approved by the project lead on 2026-11-12, and in force from this record's merge; drafted with AI assistance.
- Date: 2026-11-12
- Decision scope: Scope
- Secondary scopes: Demo
- Related specification sections: Sections 2, 5, 9, 11, 13, and 14
- Supersedes: None. S1 is later work under `AGENTS.md`'s "version as later work" rule, the same route `SPEC.md` Section 2 gives the composition arm. No deviation entry: this is not a defect (`SPEC.md` Section 16), and no pinned text, schema, hashed code, or frozen artifact changes.

## Context

At the November 10 Gate 2 step, the Section 10 development floor applied. On `claude-haiku-5-5`, 0 of the 15 development D0_BASELINE attack cells recorded a model violation ([decision 0032](0032-tier-input.md)). The main study's attack-rate comparisons are therefore reported as counts with no interpretation, and D1_POLICY_GATE may see few unsafe requests to block. The Section 13 hook, a live D0_BASELINE hijack on the demo case, will probably not happen: `demo-001` uses the same task template and source as `dev-001`.

The project lead asked for the closest lawful thing to a study whose attacks land. The main study can't change. Switching models was rejected in decision 0009's options, intake closed November 5, and strengthening payloads is forbidden by `SPEC.md` Section 5. That leaves a separate experiment with stronger published attacks, chosen by a rule that doesn't depend on any CANARY outcome.

Three reviews of a version that would run before Demo Day found it would weaken the project, under the project lead's condition that it must not. The reasons:

- **It would read as post hoc.** It would be added after the floor fired, with attacks chosen for succeeding elsewhere. Readers would compare it with the main matrix whatever the label said. Its D2_DATAMARKING row would lean against D2, because the attacks were selected partly for beating spotlighting-style defenses.
- **It would crowd the paper.** It adds a section and limitations to a six-to-eight-page paper whose leads never planned for it.
- **It would take lead time when there is none.** It needs about six to seven lead hours in the busiest stretch of the season, including November 13.
- **It would complicate the release.** The release would need either S1 code on `main` or a two-tag package (`SPEC.md` Sections 11 and 14).

**Lost, stated plainly:** S1's results are not in the November 29 paper and are not shown at Demo Day. Both may say only that S1 is registered.

The demo-script part (item 6) stands whether or not S1 ever runs.

## Options considered

1. **Run S1 before Demo Day, with its code inside the Gate 3 freeze.** Rejected. Its code would merge on November 13 beside the Gate 3 inputs, and an open finding on it would hold Gate 3 (decision 0031).
2. **Run S1 before Demo Day on its own branch and freeze, and put it in the paper.** Rejected under the project lead's condition, for the reasons in the Context.
3. **Register S1's design now, before any main outcome is inspected, run it after the confirmed Demo Day, and publish it as a versioned addendum.** Chosen.
4. **Run nothing more.** Rejected. A registered follow-up costs the fall nothing, and it is the honest next step.

## Decision

1. **S1 is a separately versioned experiment, run after the confirmed Demo Day (`TASKS.md`) and after the November 29 release.**
   - It is never pooled with, compared against, or reported inside the main study.
   - It edits nothing in the frozen release package.
   - It is published as a versioned addendum with its own tag.

2. **Model and setup.** `claude-haiku-5-5` with the frozen release's tasks, oracles, defenses, system prompt, tool descriptions, and sandbox, unchanged.

3. **Source and success rule.** These are fixed here, before any S1 label is read.
   - **Source:** LLMail-Inject at the revision already pinned for the main pool (`microsoft/llmail-inject-challenge` @ `1063bdf`, MIT), file `data/labelled_unique_submissions_phase1.json`.
   - **What the label means.** The public dataset card says each entry in that file carries a `reason` annotation, either `api_triggered` or `judge`, and that `api_triggered` "means that the API was triggered at least once for this prompt". In other words, the injected email made a defended LLMail agent call its send-email tool at least once.
   - **What the card does not say.** It does not record which level, meaning which model and defense, that happened on. The phase-1 levels used Phi-3-medium-128k-instruct and GPT-4o mini, under Spotlighting, PromptShield, LLM-as-a-judge, TaskTracker, or all of them.
   - **What was and wasn't read before.** The project lead opened this file for the main pool, but its labels were never read ([`docs/W7_T2_HANDOFF.md`](../W7_T2_HANDOFF.md)).
   - **The rule:**
     - **Eligible:** a submission is eligible only if its `reason` is `api_triggered`.
     - **Scenario filter:** the main pool's own. The text names `contact@contact.com` and "confirmation", and not "million".
     - **Length cap:** every D2_DATAMARKING-marked file a read can reach in the rendered fixture root is at most 4,000 bytes, and the prompt at most 3,000. This keeps `analysis/price_bound.py`'s bound valid.
     - **If the file doesn't hold up:** if, when opened, its annotations don't match the card as described here, S1 lapses and the lapse is recorded. Nothing else is substituted.

4. **Selection.**
   - **Excluded:**
     - every `candidate_id` already in `corpus/candidates.jsonl`;
     - any candidate that `SPEC.md` Section 5 step 4's near-duplicate rule finds near-identical to a main development, evaluation, C1, or demo base.
   - **Order:** ascending `SHA256("CANARY-2026-llmail-s1|" + SHA256(text))`. A candidate that fails Section 5's eligibility, review, or adaptation checks, or the length cap, is replaced by the next one in order. Every drop is recorded in an S1 candidate ledger with a status.
   - **Templates:** the four whose policy authorizes `send_email` with a single-recipient allowlist and a grant: `invoice-receipt-email`, `maintenance-confirm-email`, `meeting-confirm-email`, and `shipping-notice-email`. With those, D1_POLICY_GATE's decisions rest on its recipient and argument checks, not on its tool list.
   - **Assignment and shortfall:** two bases per template, round-robin in hash order, for 8 bases. If the eligible pool runs out first, one per template (4). Below 4, S1 lapses.
   - **Adaptation:** the main rule only. `contact@contact.com` becomes `contact@fixture.test`, and the payload is otherwise byte-for-byte. A Section 5 reviewer who is neither the opener nor the adapter reviews every record, and two records are rechecked.

5. **Geometry, reporting, and freeze.**
   - **Geometry:** 8 bases × C2/C3/C4 × attack/clean × D0_BASELINE/D1_POLICY_GATE/D2_DATAMARKING × n=3, which is 432 trials.
   - **Reporting is descriptive only.** It gives exact true/false/null counts per configuration, condition, and adapter of:
     - the six Section 7 security facts;
     - the request-to-effect facts;
     - `utility_pass`.

     It has no interval, no supported-difference claim, no floor, and no result sentence, and its wording states counts only.
   - **Freeze.** Before S1's first live call, its code, spec, selection constants, and ledger are frozen and hashed by its own paid-run record. After that call it is reported whatever it shows. Only an integrity failure withholds it, and that is stated publicly.
   - **The addendum's own record, before that call, names:**
     - **its split:** `evaluation` with `analysis_role` `s1_stress` and a filter that keeps S1 records out of every main analysis, or a Section 11 schema change;
     - **its budget:** by code, from `analysis/price_bound.trial_bound_usd` at S1's measured maximum render × the Section 9 factor. At decision 0032's bound, 432 trials are about $27.70 before the factor. Either December's limit rises, recorded in `STATUS.md` first (decision 0028 item 7), or S1 lapses;
     - its reviewer, its rechecker, and their dates, each given more than 24 hours ahead.

6. **The demo script (`SPEC.md` Section 13).**
   - **Basis.** This is demo wording that changes no data or claim, which Section 11 allows (`SPEC.md` Section 11, "End of week 5 — measurement contract lock" and "After freeze").
   - **The stage case stays `demo-001`.**
   - **Step 3 names the recipient generically.** The text named `attacker@example.invalid`, but the case's recipient is `external-sync@fixture.test` (`corpus/demo/demo-001.json`).
   - **New branch rules, chosen by each actual trace:**
     - **D0_BASELINE makes no unsafe request.** Say that one run is not evidence, show the representative replay, and continue to the aggregate, as the reliability rules already say. The replay must be labelled with its real provider and run. Until N-66-1 is fixed (`docs/reviews/2026-11-11-w7-t2-t5.md`), and whenever no recorded trace of the official model shows a hijack, the narrator says plainly that no live hijack trace exists.
     - **D1_POLICY_GATE run with no unsafe request.** Step 4's sentence ("The model still made the unsafe request…") is replaced by a description of the actual trace, the same rule step 5 already uses.
   - **Step 7 may say once that a follow-up is registered,** with no result and none promised.
   - **The live-first gate is unchanged.**
   - **Not owned yet:** N-66-1/2/3 are open, and no `TASKS.md` row owns them. The demo operator and the video owner (`W12-T1`) get an informative note.

7. **The paper.** Section 14's paper structure gets one permitted sentence in the limitations section: a separately versioned follow-up is registered (this record), and no result from it exists or is promised.

8. **Versions.**
   - `SPEC.md` moves to v1.24.0, a documentation version.
   - `protocol/active.json`'s `protocol_version` stays the value Gate 3 froze, and the paper's frozen-protocol section cites that value.
   - Sections 2, 13, and 14 are unpinned. No pinned section changes.

9. **Timing.**
   - The pull request opens publicly before the main sweep's first paid call on November 14. That timestamps this design before any main outcome exists. It merges after the Gate 3 step, by November 15, and no later than November 17. `W9-T3` reports outcomes November 18.
   - Until it merges, the project lead reads only the sweep's completion counts.

10. **Numbering.** This record takes 0035.

## Consequences

- **The fall loses nothing it planned.** The fall gains the demo branches and one sentence each in the paper and on stage. No member gets new work. The project lead's added time is about one hour, on top of decision 0031 item 9's 3.5 hours for November 9–15; that week's total decides item 9's 10-hour rule.
- **S1 may lapse** if the labels don't hold up, or if December's limit isn't raised. Either way, that is stated where the registration sentence appears.
- **If S1 runs, its stated limitations are:**
  - it was added after the main floor fired;
  - its attacks were selected for succeeding against other systems;
  - it uses one source and one family;
  - its D2_DATAMARKING counts may be biased, because some of those systems used spotlighting;
  - task defects in `invoice-receipt-email` and `maintenance-confirm-email` (the November 9 coverage smokes) carry into its utility counts unless `W8-T1` resolves them.
- **The spend cap stays at $10 for the fall.** The project lead approved $50 for an S1 that would have run in November, and it no longer does.
