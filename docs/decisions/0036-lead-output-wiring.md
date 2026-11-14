# 0036: Generate decision 0012's outputs from the lead's own report module

- Status: Proposed. Drafted with AI assistance; approved by the project lead by merging this record, which must happen by the end of Friday, November 13.
- Date: 2026-11-13
- Decision scope: Protocol
- Secondary scopes: Governance
- Related specification sections: Sections 9, 10, and 11
- Supersedes, for the location only:
  - [decision 0012](0012-request-to-effect-table-and-tool-name-ablation.md) item 7's "adds the two outputs to `W8-T3`'s merged report code";
  - [decision 0021](0021-two-week-shift.md) item 5's and [decision 0024](0024-engineering-tier-input.md) item 6's same words;
  - their date as [decision 0029](0029-gate-chain-shift.md) moved it, through Friday, November 13; and
  - the same words in `TASKS.md`'s decision 0012 entries, which this record amends in place.

  Every other part of decision 0012, its `SPEC.md` Section 10 subsection, and that subsection's pin stay in force. Item 2 below states the other changes to decision 0012's functions: the C1 skip that decision 0034 item 8 asked for, and a duplicate refusal this record adds.

## Context

Decision 0012 item 7 has the project lead wire the request-to-effect table and the tool-name-only ablation into `W8-T3`'s merged report code, as an additive change that alters no existing output, so the Gate 3 step freezes them. If the wiring isn't on `main` by the date, the lead withdraws the subsection, its pin, and both shells through Section 11 change control before the Gate 3 step. [Decision 0028](0028-restore-strength.md) item 4 adds its count-only outputs in `ReliabilityAndResourceDiagnostics` to the same wiring.

On November 13, the last day, `W8-T3`'s report code isn't on `main`. `make report` names a placeholder module, `analysis.report`, that doesn't exist, and `W8-T3`'s open pull request (#77, last pushed November 8) adds an `ENGINEERING` report generator but no estimand report module. So there is nothing to wire into, and the literal reading leaves only the withdrawal.

Withdrawing would drop two predeclared, pinned outputs and the count-only diagnostics because a member slice's file is missing, not because of anything they measure. Item 7's location isn't hash-pinned: the pin covers the Section 10 subsection, which doesn't say where the outputs are generated. No evaluation outcome exists, so the location is outcome-blind.

## Options considered

1. **Withdraw the subsection, its pin, and both shells.** Rejected. It loses the thesis table (decision 0012 Consequences) and decision 0028 item 4's counts, for a reason that has nothing to do with them.
2. **Write `W8-T3`'s report module for it, or push the call into #77.** Rejected. Both take `W8-T3` scope, or change a member's pull request, without a visible reassignment (`AGENTS.md`, "Ownership and completion"). #77 also has no estimand module to call from.
3. **Generate the outputs from a lead scaffold module that `make report` runs.** Chosen.

## Decision

1. **Location.** `analysis/lead_outputs.py`, lead scaffold, generates decision 0012's two outputs (from `analysis/request_effect.py`) and decision 0028 item 4's count-only outputs (from `analysis/diagnostics.py`). `make report` runs it after the estimand shells and before `W8-T3`'s report module. The request-to-effect table is the first table it generates, which is how the pinned "first table in the generated outputs" holds. `W8-T3`'s report code doesn't call it. `W8-T3`'s and `W8-T5`'s scope and hours don't change: `W8-T5`'s pipeline still renders every manifest shell, and these tables sit in their own generated file.
2. **What changes in decision 0012's functions.** They skip official C1 control records in the C1 form (`split` and `analysis_role` `c1_control`, channel C1) rather than refuse them, as [decision 0034](0034-c1-result-records.md) item 8 asks, and refuse any other record on that split. This record adds one more refusal, which no earlier decision asked for: a `logical_trial_id` that appears twice, found by the November 13 whole-tree review. Decision 0012 item 5's refusal of every other non-evaluation record stands. No formula, column, or count changes.
3. **Additive.** It changes no existing output, and the Section 10 subsection, its pin, and the shells in `paper/estimand_manifest.json` don't change. Its empty shells are committed as `paper/generated/lead_outputs.md`. The count-only tables add two null counts that decision 0028 item 4 doesn't name ("Replies whose blocks can't be read", and the unknown column for required calls), so that an unknown is never shown as false (`AGENTS.md`, "Measurement rules"). They change no count that decision 0028 item 4 names. They were written after the November 9 development records were visible, and they read no evaluation record.
4. **Frozen at Gate 3.** It sits under `analysis/`, so the Gate 3 code commit and `paid_run.code_digest` freeze it with the rest of the analysis code. The lead-side review of its code (decision 0031 item 7) closes before the Gate 3 step.
5. **What it reads, and who runs it.** It reads any final set of result records: a raw sweep run, which it refuses unless `runner.sweep.verify_sweep` finds it complete with every stored result recomputed from its raw events, or a released JSONL file of result records, each validated against the result schema. Choosing the final, non-superseded set is the caller's: a raw sweep run holds one result per scheduled trial, and with a repair the caller passes the final set's records as JSONL, leaving out the superseded blocks `docs/DATA_RELEASE.md` keeps, with each raw run through `--events`. Decision 0012's two tables read only the records. The count-only tables read only verified raw evidence: each primary record's stored result and raw events from a complete raw run (the records' own run, or runs passed with `--events`, such as a sweep run and its repair runs), and only when every primary record in the final set has them; otherwise they are rendered as needing the raw events. A raw run's stored result must agree with the final record it stands for on the cell, the ending, every scored fact, and each tool event's dispositions and arguments.
   - The project lead runs it over the raw sweep run after Gate 4's integrity checks pass, for the supported-results decision. The rest of Gate 4's checks hold by rule, as the sweep's blinding does (`SPEC.md` Section 14). Over a JSONL file, nothing in the code checks completeness, so blinding there holds by rule alone.
   - `W9-T3`'s generated-results run reads the released, sanitized JSONL with this module for decision 0012's two tables, as it would have read `W8-T3`'s report code, so `W9-T3`'s scope and hours don't change.
6. **Release path.** Decision 0012's two tables regenerate from the released JSONL with this module: they read identifiers, steps, reason codes, and true/false/null fields, which the sanitizer's scored projection keeps unchanged. The count-only tables need raw events, which the released bundle may not carry unchanged; until their release path is settled, the project lead generates them from the access-controlled raw runs through `--events`, which is not yet the release path `SPEC.md` Section 11 requires. The project lead settles it by Friday, November 20, in a `TASKS.md` lead-inputs row used by `W12-T3` (pull request November 24): either a path under which they regenerate from the released bundle, or, if none exists, their removal from the final tables through Section 11 change control. A change to this frozen module also goes through Section 11.
7. **Notice.** As decision 0012 item 7 and decision 0029 require, the project lead tells `W9-T3`'s owner about the wiring the day W8's last slice merges. The notice is informative and asks nothing.
8. **Numbering.** This record takes 0036. Decision 0035 is open as #94 and keeps its number.

Nothing is frozen yet and no evaluation outcome exists, so under `AGENTS.md` this updates every affected authority together. `SPEC.md` doesn't say where the outputs are generated, so it doesn't change, and no protocol-deviation record is needed.

## Consequences

- The Section 10 subsection, its pin, and both shells stay, and Gate 3 freezes the code that generates them.
- This record doesn't change what happens if `W8-T3` misses November 13. The Section 11 Gate 3 response for a missing estimand report module still applies, as `TASKS.md` already says.
- `analysis/` is in the paid-run record's hash, so after this merges a paid call needs a new mock grid and paid-run record, as decision 0034 already requires.
- **One open item, dated: the count-only release path.** Decision 0028 item 4 defines the count-only outputs over raw events, and the sanitizer may replace restricted payload text. So whether they regenerate from the released bundle depends on `W9-T3`'s sanitizer. That question comes from decision 0028 item 4's definition, not from this record. Item 6 dates it November 20, and either outcome there keeps `SPEC.md` Section 11's rule that every final empirical table regenerates from released JSONL. No outcome depends on it.
- The project lead's added time on November 13 is about two hours for the wiring plus about 45 minutes for the records reader, about 2.75 hours in all, beside `W8-T4`'s fallback and the two other November 13 lead inputs. It is lead time only and moves no member's hours.

## Verification

- `tests/test_count_diagnostics.py` covers:
  - the location;
  - the empty shells against the committed file;
  - the refusal before a raw run verifies complete;
  - the released-JSONL path, its schema refusal, and the count-only tables marked as needing the raw events;
  - raw events from several verified runs, a trial in two runs refused, a disagreeing stored result refused, and events outside the final set ignored;
  - `make report` running the module (`make -n report`).
- `tests/test_request_effect.py` passes with its pin unchanged and covers item 2's C1 skip and duplicate refusal.
