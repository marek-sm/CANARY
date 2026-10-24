# 0017: Make usefulness to teams choosing safeguards CANARY's purpose

- Status: Accepted. Approved by the project lead on 2026-10-13; drafted with AI assistance.
- Date: 2026-10-13
- Decision scope: Governance
- Secondary scopes: Release
- Related specification sections: Sections 0, 1, and 14
- Supersedes: [Decision 0016](0016-practitioner-relevance.md) item 2, fourth bullet, in part: "No published work measures this" is now forbidden outright, not only until an opened source supports it.

## Context

[Decision 0016](0016-practitioner-relevance.md) said who CANARY is for and routed every public description to it. It rejected adding practitioner value to the Section 0 decision priority (its option 3), because that would rank a presentation goal against safety and measurement validity.

On October 13 the project lead decided that usefulness to companies is CANARY's main goal: applied research whose measurement serves a team's decision, as opposed to research for its own sake. The experiment doesn't change. Less than two months remain, the measurement contract is locked, and the protocol freezes on October 28.

The judging rubric's impact criterion, paraphrased in the `TASKS.md` rubric map, asks for a named gap in what the market lacks. As of October 13 the project lead has opened none of the three Week 1–2 papers, so under [decision 0013](0013-rubric-framing.md) no gap or prior-work claim can be made yet.

Verified constraints:

- `tests/test_contract_lock.py`, `tests/test_corpus_rules_freeze.py`, and `tests/test_request_effect.py` pin no part of Section 0, "Who CANARY is for", "Claims CANARY may not make", or Section 14. `tests/test_paper_scaffold.py` checks only the outline's first eleven `##` headings.
- Section 11's "After freeze" lets prose change without a protocol version only when it changes no data or claim.
- No `LICENSE` exists, so nothing may imply that others can reuse CANARY's code.
- Decision 0004 item 19 governs reference 15, and new Section 18 entries are numbered after it.

  *Corrected October 18: this line credited the numbering to decision 0013, which has no such rule. The numbering didn't change.*

## Options considered

1. **Rank usefulness in the Section 0 priority list.** Rejected, as in decision 0016.
2. **Rank it above validity or honest claims.** Rejected. An invalid or overstated result can't inform a team's decision, and the ranking would push toward overclaiming.
3. **Change the experiment, such as more models, commercial guardrails, or realistic tools.** Rejected. The contract is locked and the freeze is October 28.
4. **Make CANARY a tool other teams run on their own agents.** Rejected. It needs a license, an adapter for outside models, and packaging, and a public product isn't the project's goal.
5. **Add a separate brief for companies.** Rejected. It's another deliverable; the paper's close and the checklist carry the same content.
6. **State that the market lacks this measurement.** Rejected. No source has been opened, and an academic paper can't support a statement about a market.
7. **State the purpose and a tie-breaker that ranks nothing, add a measurement checklist and a paper close, and allow a gap sentence only when opened sources support it.** Chosen.

## Decision

1. **`SPEC.md` Section 0:**
   - The opening paragraph says CANARY is applied research, written for teams that choose prompt-injection safeguards for tool-using agents.
   - After the decision priority, a tie-breaker: when options are otherwise equal under the list, choose the one more useful to those teams. Usefulness is the reason for the work, not an obligation on the list. It never permits cutting anything the list protects, and it doesn't reopen choices Sections 11 and 12 fix.
   - "Definition of project success" is unchanged.
2. **Section 1's "Who CANARY is for"** is rewritten around a table that maps RQ1–RQ3 to the questions a team asks, for the one model tested. It keeps every limit decision 0016 set.
3. **Section 1's market-gap claim bullet** forbids "The market lacks this measurement," "No one measures this," and "No published work measures this" outright. A gap sentence may state only what specific sources the project lead has opened show, scoped to those sources, cited in Section 18, and stated beside the overlap list. An academic paper supports a statement about published research; a statement about a market needs a market source.
4. **Section 14:**
   - Paper item 8 closes, at every tier, with what the evidence does and doesn't let a team choosing safeguards conclude, and the measurement checklist. The close adds no number that isn't generated.
   - A new "Measurement checklist for teams" lists seven practices CANARY's design follows. It describes a method, not CANARY's code, isn't complete or validated, and claims no novelty.
   - "A car that never starts has a perfect crash record." may precede the pitch opener at any tier.
5. **`SPEC.md` moves to v1.11.0.** No pinned subsection changes.
6. **The gap input.** By Sunday, October 25 (target Sunday, October 18), the project lead opens the three Week 1–2 papers. Then either:
   - a lead-scaffold change adds the scoped gap sentence, its Section 18 entries, and overlap-list additions for works the project lead has opened, with the project lead's related-work notes for the paper leads; or
   - the project lead records that the opened sources support no gap sentence, and the Section 1 bullet keeps forbidding one.

   Either way, reference 15 is resolved: found and recorded under decision 0004 item 19, or dropped by a small record that supersedes that item and edits each place that names it.
7. **`TASKS.md`:**
   - A lead-input row for the gap input, with no slice waiting on it. It is due before the paper leads draft during October 26 to November 1.
   - The November 15 claim-language row covers the paper's close.
   - The impact row adds the checklist, and its boundary points to the Section 1 bullet.
   - The Week 1–2 paragraph records the due date and the no-gap branch.
   - The drill question and the October 25 practice round are unchanged.
8. **`README.md`, `AGENTS.md`, `paper/lead-inputs.md`, and `paper/outline.md`** point to the purpose, the checklist, and the gap rule. The outline's generated-artifacts rule covers numbers and figures, so the close and checklist can sit in section 8.
9. **Numbering.** This record and its `SPEC.md` version follow merge order: if another record merges first, this one takes the next free number and minor version before it merges.

This record lands before the protocol freeze and changes no estimand, so it needs no protocol-deviation record. The gap input is due before the freeze for the same reason. A gap sentence proposed after the freeze needs its own record that settles its Section 11 status.

## Consequences

- CANARY's purpose is stated in Section 0, and every tie between otherwise equal options goes to the more useful one.
- A team gets a checklist it can apply to its own agent at every tier, including `ENGINEERING`.
- The rubric's gap criterion gets a sourced sentence only if the opened papers support one. Leadership hears that conditionally until then.
- The re-accepting slices are decision 0016's set, with no estimate changes: `W9-T1`, `W11-T1`, `W12-T1`, and `W13-T1` through `W13-T5`. `W11-T2`, `W12-T2`, `W11-T4`, and `W12-T4` keep their acceptance text, and their audits cover the new text as written.
- The paper leads place one more closing subsection, whose content the project lead supplies with the November 15 claim language.
- The project lead's added load is about two hours of reading, plus any overlap works the project lead chooses to open. AI assistance drafts the follow-up change and any reference-15 record.

## Verification

- `tests/test_contract_lock.py`, `tests/test_corpus_rules_freeze.py`, `tests/test_request_effect.py`, and `tests/test_paper_scaffold.py` pass unchanged.
- `tests/test_status_consistency.py` accepts `STATUS.md`'s version row, and `tests/test_tasks_dependencies.py` passes.
- A search of the new text finds "market", "gap", "overlap", "novel", "secure", and "adopt" only in forbidden-claim bullets, negated limits, or conditional rules.
