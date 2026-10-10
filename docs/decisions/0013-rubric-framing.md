# 0013: State the problem and an overall research question, without a prior-work claim

- Status: Accepted. Approved by the project lead on 2026-10-10; drafted with AI assistance.
- Date: 2026-10-10
- Decision scope: Governance
- Secondary scopes: Protocol
- Related specification sections: Sections 1, 2, 15, 17, and 18
- Supersedes: None

## Context

The CSAI judging rubric weighs the problem statement heavily, and the separate Week 1–2 expectations ask the project lead for 2–3 papers motivating the gap and a research question in writing, to answer by December, that involves that gap. `SPEC.md` Section 1 had a thesis and RQ1–RQ3 but no problem statement and no single question that ties them together. The `TASKS.md` rubric map also misparaphrased three criteria: it framed conceptual understanding as generic Q&A, aesthetics without the presentation itself, and enterprise readiness without the explicit grading of prompt quality, and it reused phrases from the rubric where it should paraphrase.

Verified constraints:

- As of October 10, the project lead has opened none of the papers proposed as market-gap evidence, nor the Inspect-based Canary repository named in Section 1. Section 15 bars any unopened citation from the paper, and the project lead's rule is that no number or prior-work claim from an unopened source enters `SPEC.md`, `paper/`, or any message.
- Section 1's contribution statement already places CANARY in an established research area with substantially overlapping work. A sentence saying the field lacks this measurement would be a claim about prior work.
- Decision 0004 item 19 requires a person to open the Inspect-based Canary repository and record its URL and version before Section 18 gets an entry for it.
- Section 1's "Predeclared result sentence" is hash-pinned by decision 0009. The thesis and research questions are not.

## Options considered

1. **Pivot to a new defense or attack so the project "solves" an unsolved problem.** Rejected. Section 1 forbids novelty and "solves prompt injection" claims, Section 2 fixes the scope, and the schedule can't absorb it.
2. **Present existing work as new.** Rejected.
3. **State the gap with published numbers from the proposed papers.** Deferred until the project lead opens them. A sourced sentence and its Section 18 entry can follow in a later change.
4. **Add Section 18 entry 15 now, marked unverified.** Rejected. Decision 0004 item 19 puts the entry after the source is opened, and Section 17 keeps facts that depend on later work in `TASKS.md`.
5. **State the problem from the metric's own logic, with no prior-work claim, and add an overall question built from existing estimands.** Chosen.
6. **Also adopt a week-15 deck rule, a per-slice prompt-log rule, or an optional second-model rerun.** Not adopted now. The deck rule and the prompt-log rule wait for leadership to say what format and prompt evidence judges will see. The rerun would conflict with Section 2's one-model scope, needs model spend, and, after the October 28 freeze, would be a new feature that `AGENTS.md` rejects.

## Decision

1. **`SPEC.md` Section 1 gains a "Problem statement" before the thesis.**
   - One end-to-end attack-success rate can be lowered in three ways: the model ignores the injection, a control outside the model blocks the proposed action, or the agent fails its legitimate task. So that rate alone can't show whether a defense made the model safer or the agent less able.
   - CANARY is not a new attack or defense. It records request, policy decision, dispatch, and effect separately for the same runs, beside exact no-injection twins and authorized risky tasks.
   - The statement makes no claim about prior work and doesn't say a gap exists in the literature.
2. **Section 1's "Research questions" gains an overall question.** Its clauses map to existing estimands:
   - model violation beyond the matched clean background (`InjectionExcessRisk` and the clean-adjusted D2_DATAMARKING difference);
   - the system-compromise rate;
   - D2_DATAMARKING's change in model violations;
   - D1_POLICY_GATE's residual compromise;
   - each defense's clean-utility cost.

   RQ1–RQ3 stay unchanged as its parts. It adds no estimand.
3. **`SPEC.md` moves to v1.7.0.** No pinned subsection changes.
4. **`TASKS.md`:**
   - The rubric map's conceptual, aesthetics, and enterprise-readiness criteria are re-paraphrased.
   - The impact row cites the problem statement and overall question. It drops its unsourced sentence about how agents are deployed, and its boundary adds that no prior-work number or literature-gap claim appears until the source is opened.
   - The aesthetics boundary says no slice builds a presentation deck.
   - A paragraph records which Week 1–2 expectation is addressed and which is open.
   - The kickoff reading marks reference 15 unverified.
5. **`paper/lead-inputs.md`** restates the problem statement and overall question for the paper leads.
6. **Numbering.** This record and its `SPEC.md` version follow merge order: if another record merges first, this one takes the next free number and minor version before it merges.

This lands before any evaluation outcome exists and changes no estimand, so it needs no protocol-deviation record.

## Consequences

- The impact criterion now has a stated problem and one research question, and the Week 1–2 research question exists in writing. Tying it to a market gap, and the 2–3 papers, stay open until the project lead opens and checks them.
- Whether a measurement study counts as solving an unsolved problem under the rubric is unconfirmed. That question goes to the club's research directors.
- Section 18 still ends at entry 14, and the paper's overlap statement stays incomplete until reference 15 is opened.

## Verification

- `tests/test_contract_lock.py` and `tests/test_corpus_rules_freeze.py` pass unchanged, so no pinned text moved.
- `tests/test_status_consistency.py` accepts the `STATUS.md` version row.
- The project lead confirms before merge that the problem statement and overall question contain no claim he can't support.
