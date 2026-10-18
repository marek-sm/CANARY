# 0019: Reconcile the documentation contradictions the October 17 audit found

- Status: Accepted. Approved by the project lead on 2026-10-18; drafted with AI assistance.
- Date: 2026-10-18
- Decision scope: Governance
- Secondary scopes: Protocol
- Related specification sections: Sections 5, 7, 10, 11, 12, 16, and 17
- Supersedes: None

## Context

On October 17 the project lead ran a read-only audit of `main` at `31b9399`. An independent verifier checked each finding. The audit found seven contradictions or gaps in documents the project lead maintains. Six are settled here, each by text that already states the rule. `AGENTS.md` requires a record when artifacts conflict, so this record names each one and its source.

Verified constraints:

- Gate 3's full freeze hasn't happened, but the week-5 measurement-contract lock (decision 0009) and the Gate 1 corpus-rules freeze (decision 0007) have. No edit here touches text pinned by `tests/test_contract_lock.py`, `tests/test_corpus_rules_freeze.py`, or `tests/test_request_effect.py`. Section 10's "Active-protocol manifest", Section 16, and Section 17 are unpinned (decision 0009 item 1).
- No official experiment exists, and no result is affected.
- The verifier rated F-04 and F-05 plausible rather than confirmed. Their edits only make the text consistent; neither adds a requirement.

## Options considered

1. **Leave the documents as they are.** Rejected. Each lower or looser text misstates a rule stated elsewhere, and some of them steer near-term work: `W8-T3`'s manifest generator, the paper's conformance table, and the planned change to the decision 0012 pin (`TASKS.md`, decision 0012).
2. **Bring each one into line with the text that already states the rule.** Chosen.

## Decision

1. **`SPEC.md` Section 16, adaptation drift (audit F-03).** The response becomes "preserve the rejection and rerun the Section 5 step 8 search over the remaining eligible candidates, in the same goal order". That's pinned Section 5 step 6 as decision 0014 left it. The row had kept the earlier "take the next precomputed eligible candidate" rule.
2. **`SPEC.md` Section 10, active-protocol manifest (audit F-04).** The list now names fields that other `SPEC.md` text already requires in `protocol/active.json`:
   - the row's exact components, arithmetic, and accountable roles, from Section 12 step 5, which is equal-rank but more specific;
   - the model, endpoint, and reasoning effort the development-floor cells ran on, from the pinned Section 10 floor rule.
3. **`SPEC.md` Section 17, `TASKS.md` row (audit F-09 and G-13).** The row drops "16". `TASKS.md` owns slice structure, and its lattice has 45 slices.
4. **`paper/lead-inputs.md` §4.4 (audit E-06, its lead half).** It gains the content-filter exception from `SPEC.md` Sections 7 and 9 and decision 0008 item 2, with an approval note at the top of the file. The file says it must be corrected when it disagrees with `SPEC.md`. The matching columns in the conformance shells belong to W5-T5's owner and are on that owner's audit list.
5. **`AGENTS.md` and `CONTRIBUTING.md` (audit F-05).** Their pre-freeze rule ("update every affected authority and test together") now names its exception: text a decision hash-pinned (decisions 0007, 0009, and 0012) and a locked schema change on the `docs/DATA_CONTRACTS.md` evolution list (decision 0009). Those follow `SPEC.md` Section 11 change control as the pinning or locking decision requires, with any pin updated deliberately. The new text lists no steps of its own. It points to decision 0014 and DEV-0001 for how Section 11 applied before the full freeze, so no step is dropped or added.
6. **Decision 0018's order table (audit D-09 and F-11).** `c1-003`'s selection-hash prefix is corrected from `4d455758…` to `4d457558…`, with a dated note in the record (`docs/decisions/README.md`: typographical errors are corrected transparently). The order doesn't change.
7. **Deferred: `CLAUDE.md` line 23 (audit F-06).** Turning the line into a pointer to `AGENTS.md` would drop a rule: `AGENTS.md` has no counterpart to "never use evaluation candidates for development" (`SPEC.md` Section 5 and Section 11, "End of week 8"). The line stays until `AGENTS.md` carries that rule.
8. **Version.** `SPEC.md` moves to v1.13.0.

## Consequences

- No protocol-deviation entry is needed, because no pinned text changes.
- `W8-T3`'s `protocol/active.json` generator already needs the item 2 fields under Section 12 step 5 and the floor rule. The fuller list just states them in one place, so a merge after Monday, October 19 changes nothing `W8-T3` must do.
- The paper's conformance write-up counts content-filter calls separately instead of calling them indeterminate.
- Whichever of this record and the October 18 `STATUS.md` rollup merges second should cite `SPEC.md` v1.13.0.

## Verification

- `tests/test_contract_lock.py`, `tests/test_corpus_rules_freeze.py`, and `tests/test_request_effect.py` pass unchanged, which shows no pinned text moved.
- `tests/test_status_consistency.py` passes with the version bump.
- The full no-credit suite passes with no provider call.
