# 0016: Say who CANARY is for, and route every public description to it

- Status: Accepted. Approved by the project lead on 2026-10-12; drafted with AI assistance.
- Date: 2026-10-12
- Decision scope: Governance
- Secondary scopes: Release
- Related specification sections: Sections 1, 13, and 14
- Supersedes: None

## Context

The CSAI research leadership's two documents both tie the project's framing to people outside the club. The Research Expectations say the judging criteria aim at research that draws recruiters and sponsors. The Week 1–2 expectations say a stronger problem statement makes sponsor funding likelier. CANARY isn't a product, but it can be described honestly as useful to the teams that choose prompt-injection safeguards.

Before this record, that idea lived in one clause of the `SPEC.md` Section 1 problem statement ("anyone choosing a defense for a deployed agent needs to know which"). No public artifact, drill question, or checklist asked for it, so the README, demo, paper, or presentation could leave it out.

Verified constraints:

- Three tests hash-pin `SPEC.md` text: `tests/test_contract_lock.py` (Section 1's "Predeclared result sentence", Sections 3, 7, and 8, and six subsections of Sections 9 and 10), `tests/test_corpus_rules_freeze.py` (the Section 5 corpus rules), and `tests/test_request_effect.py` (Section 10's "Request-to-effect table and tool-name-only ablation"). A new subsection before "Thesis", new bullets in "Claims CANARY may not make", and edits to Sections 13 and 14 are all outside those spans.
- [Decision 0013](0013-rubric-framing.md) removed an unsourced sentence about how agents are deployed and bars any market-gap or prior-work claim until the project lead has opened its source.
- No `LICENSE` exists. The README, `TASKS.md`, and `STATUS.md` all bar implying reuse rights, and Section 4's provider adapter exists to select a fallback model before the freeze, not to run CANARY on someone else's model.
- The pinned Section 10 development floor and interpretation rules limit what a reported difference may be said to show.

## Options considered

1. **Leave the pitch in conversation.** Rejected. Nothing would carry it into the README, demo, paper, or presentation.
2. **Add a market-gap sentence now.** Rejected under decision 0013 until the project lead has opened a source that supports it.
3. **Add practitioner value to the Section 0 decision priority.** Rejected. It would rank a presentation goal against safety and measurement validity.
4. **Add a Gate 5 checklist item.** Rejected. The README first screen and the demo close are W13 work, after the November 15 gate, and a presentation goal shouldn't be able to fail a gate.
5. **Give it one canonical home in Section 1 and route each public artifact to it.** Chosen.

## Decision

1. **`SPEC.md` Section 1 gains "Who CANARY is for"** between the problem statement and the thesis.
   - It says CANARY is written for teams that choose prompt-injection safeguards for tool-using agents, and that it is a controlled engineering evaluation, not a safeguard.
   - It describes what CANARY reports for the same runs (requests, blocks, dispatches and effects, and legitimate-task success), within the Section 10 development floor and interpretation rules, and that what it reports depends on the tier.
   - It makes no claim about industry practice or the literature.
2. **"Claims CANARY may not make" gains four bullets:**
   - that CANARY reduces or prevents prompt injection;
   - that a company uses, endorses, sponsors, or has validated it, without a public record;
   - that its code may be reused or adopted before the license decision;
   - that the market or the literature lacks this measurement, until an opened source supports the sentence.
3. **Section 13's demo close** ends with what the measurement lets a team choosing safeguards see. At `BASE` and `ENGINEERING`, where no safeguard comparison runs, that clause is dropped.
4. **Section 14:**
   - The README first screen's first item adds one sentence on who CANARY is for.
   - "Public project-description language" gains pitch wording for leadership, sponsors, and recruiters, with a variant for each tier.
5. **`SPEC.md` moves to v1.10.0.** No pinned subsection changes.
6. **`TASKS.md`:**
   - The rubric map's introduction records the documents' stated purpose, and the Impact row cites the new subsection and pitch.
   - The judge-readiness drill gains a question every owner answers, and the October 25 practice round asks it of everyone.
   - "Decisions that must not be forgotten" gains a row pointing to the new subsection.
7. **`AGENTS.md`'s** claim bullet points to Sections 1 and 14. **`README.md`** gains one sentence on who CANARY is for and this record. **`paper/lead-inputs.md`** restates the subsection and mirrors the new claim bullets. **`paper/outline.md`** adds an introduction checkbox.
8. **Numbering.** This record and its `SPEC.md` version follow merge order: if another record merges first, this one takes the next free number and minor version before it merges.

This lands before the protocol freeze and changes no estimand, so it needs no protocol-deviation record.

## Consequences

- Every public description now has one source for who CANARY is for and one list of what may not be said about it.
- Changed acceptance evidence, with no estimate changes. Each owner re-accepts by replying to that week's Monday post ([decision 0015](0015-cut-process-rules.md)):
  - `W9-T1`, `W11-T1`, and `W12-T1`: the video follows the Section 13 demo story, so its close changes.
  - `W13-T1` through `W13-T4`: the drill has one more question.
  - `W13-T5`: the drill question, and the README first screen's added sentence.
- This record must merge before Monday, October 26, so `W9-T1` can use the new close under the dependency rule.
- A market-gap or literature sentence still waits for the project lead to open the papers, and an academic paper supports a statement about published research, not about a market.

## Verification

- `tests/test_contract_lock.py`, `tests/test_corpus_rules_freeze.py`, and `tests/test_request_effect.py` pass unchanged, so no pinned text moved.
- `tests/test_status_consistency.py` accepts `STATUS.md`'s version row, and `tests/test_tasks_dependencies.py` passes.
- A search of the new text finds "reduce", "prevent", "solve", "adopt", and "endorse" only in forbidden-claim bullets or negated limitations.
