# Venue checklists: where CANARY answers each item

> **Pre-results routing aid.** This file maps the NeurIPS paper checklist and the IEEE conference-paper structure to the `SPEC.md` sections and artifacts that will answer them. It is a paraphrase and makes no venue claim: the designated paper leads haven't confirmed the venue or template. `SPEC.md` stays canonical. Where this file and `SPEC.md` differ, `SPEC.md` wins and this file is corrected.

The club's Week 1–2 expectations recommend keeping both venues' guides in the repository so contributors and coding agents can check the paper against them. The sources, opened October 11, 2026:

- NeurIPS Paper Checklist (2026 edition): https://neurips.cc/public/guides/PaperChecklist
- IEEE Author Center, "Structure your paper" (conferences): https://conferences.ieeeauthorcenter.ieee.org/write-your-paper/structure-your-paper/

Recheck both pages when the paper leads name the venue (`TASKS.md`, "Decisions that must not be forgotten", intended publication venue language). Their wording, item count, and rules can change between editions.

## NeurIPS paper checklist

The 2026 guide puts the checklist after the references and any supplemental material. It doesn't count toward the page limit, and a paper without it can be desk-rejected. Each item is answered Yes, No, or NA, usually with a one- or two-sentence justification that reviewers see.

| # | Item, paraphrased | Where CANARY answers it | Open, and whose |
|---:|---|---|---|
| 1 | Claims: the abstract and introduction claim only what the results support, at the scope they support | `SPEC.md` Section 1 (problem statement, predeclared result sentence, contribution statement, and the claims CANARY may not make); Section 14 release language; `paper/lead-inputs.md` | Claim language is the project lead's (Gate 5, November 15) |
| 2 | Limitations: assumptions, how robust the results are to them, and the scope | `SPEC.md` Section 14, "Mandatory limitations"; Sections 2 (scope), 15, and 16 (technical risks); paper outline section 9 | Each owner's W8 limitation; the project lead approves |
| 3 | Theory, assumptions, and proofs | No theoretical results, so NA | — |
| 4 | Reproducibility: enough detail to reproduce the main results | `SPEC.md` Section 11 reproducibility criteria; `protocol/active.json` (Gate 3); fresh-clone `make report` and `make replay` (Gate 5); paper outline section 10 | `W11-T3` reproducibility material |
| 5 | Open access to data and code, with instructions | `SPEC.md` Section 14 public artifacts; `docs/DATA_RELEASE.md` (sanitized bundle, restricted payloads) | The code and content license is chosen November 1 (project lead) |
| 6 | Experimental settings: data splits, hyperparameters, and how they were chosen | `SPEC.md` Section 5 (splits and selection), Section 9 (model pinning, decoding settings, schedule); `protocol/active.json` | The frozen decoding settings: the project lead's tier, budget, and model input (October 18, or October 25 under the slip rule) |
| 7 | Statistical significance: error bars or intervals, what varies, how they're computed | `SPEC.md` Section 10 (cluster resampling by `base_case_id`, 10,000 paired draws, missingness ranges, exact `x/n`) | — |
| 8 | Compute resources: hardware and time per run and in total | Hosted-model calls: per-trial `usage` in the result records; the Section 9 Gate 2 budget equation; spend in `STATUS.md` | Totals come from the frozen bundle at the release candidate |
| 9 | Code of ethics: the work follows it, or explains any deviation | `SPEC.md` Section 15 (research integrity and ethics); Section 3 safety boundary | The paper leads confirm against the venue's code |
| 10 | Broader impacts, positive and negative | `SPEC.md` Sections 3 and 15; the release boundary in `docs/DATA_RELEASE.md` | Paper section 9 prose (paper leads, from owner inputs) |
| 11 | Safeguards for releasing high-risk assets | Fictional local fixtures only, no real email, web, or credentials (`AGENTS.md`, `SPEC.md` Section 3); demo safety (Section 13); sanitizer and restricted payloads (`docs/DATA_RELEASE.md`) | — |
| 12 | Licenses of existing assets: credit, license name, and terms | `SPEC.md` Section 5 requires a license or permission record for every case; Section 18 references | `W8-T2` and `W11-T2` citation audits |
| 13 | New assets: documentation, license, and limitations | Corpus ledger and harness documentation; `docs/DATA_RELEASE.md` | License (November 1, project lead) |
| 14 | Crowdsourcing and human subjects | No human subjects, so NA | — |
| 15 | IRB or equivalent approval | No human subjects, so NA | — |
| 16 | Declaration of LLM use, when an LLM is a core part of the method | The evaluated hosted model is the system under test (`SPEC.md` Sections 4 and 9), so the paper declares it. AI-assisted coding and editing follow `SPEC.md` Section 15 and `AGENTS.md` ("AI assistance") | Whether the venue also wants AI-assisted development declared: paper leads |

## IEEE conference-paper structure

| IEEE element, paraphrased | CANARY input | Paper outline section |
|---|---|---|
| Title: specific, concise, and searchable | Uses `CANARY` in all caps with no novelty claim (`TASKS.md`, "Decisions that must not be forgotten") | — |
| Abstract: one stand-alone paragraph of at most 250 words, plus 3–5 keywords | The approved result sentence (`SPEC.md` Section 1) | 1 |
| First footnote: funding source, and any ethics approval or exemption | Funding as a non-personal source category (`STATUS.md` spend row); no human subjects | — (paper leads) |
| Introduction: the research landscape, narrowed to the research question | `SPEC.md` Section 1 problem statement and overall question; related work from `W8-T2` | 2, 3 |
| Methods: detailed enough to reproduce | `SPEC.md` Sections 3–10 | 4–7 |
| Results and discussion: findings, honestly bounded | Generated outputs only (`paper/generated/`), with the Section 10 interpretation rules | 8, 9 |
| Conclusion: findings, implications, and future work | Approved claim language (Gate 5) | None: the outline has no conclusion section, so the paper leads add one or fold it into 9 |
| Acknowledgments | Consented names only (`docs/contributions/`) | 10 |
| References: only directly relevant sources | `SPEC.md` Section 18, after the citation audits | — |
