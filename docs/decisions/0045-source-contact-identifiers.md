# 0045: Contact identifiers that a pinned source wrote into its own attack text ship as public source text, and `eval-006`'s two real URLs are disclosed

- Status: Accepted. Approved by the project lead on 2026-11-24, and in force from this record's merge; drafted with AI assistance.
- Date: 2026-11-24
- Decision scope: Release
- Secondary scopes: Governance
- Related specification sections: Sections 3, 5, 11, 15, and 17 (the public/private repository boundary)
- Related records: [decision 0041](0041-license-and-author-order.md) item 8, the W8-T2 review's Q-93-2 and N-93-6 ([`docs/reviews/2026-11-13-w8-t2.md`](../reviews/2026-11-13-w8-t2.md)), [`docs/DATA_RELEASE.md`](../DATA_RELEASE.md), [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md), and DEV-0010 in [`docs/protocol_deviations.md`](../protocol_deviations.md)
- Supersedes: None

## Context

Decision 0041 item 8 left one call to the project lead, which `TASKS.md` dates November 24. The call is whether the corpus records' `original_payload` fields ship as they are, and what happens to the addresses outside `fixture.test` in `corpus/release/payloads.json`'s `adaptation_notes`. The W8-T2 review asked the same question on November 13 (Q-93-2). It also noted, under N-93-6, that the release list withholds only email addresses, so URLs and phone-like and account-format strings stay in full. Neither had been ruled on.

This record gives no value of any of these strings. The facts below come from the repository's code and documents. No run record was read.

- **The strings.** Eight distinct email addresses on real domains, repeated across records, and a smaller set of URLs and phone-like and account-format strings. Each was written by one of the four pinned MIT sources into its own attack text. They appear in `original_payload` and `adaptation_notes` across 47 files under `corpus/`. The adapted payloads replace every email address with a `fixture.test` recipient (`tests/test_release_payloads.py`).
- **History.** The repository is public. The development, C1, and demo records carried these strings before #73, and #73, merged November 10, added the evaluation candidates.
- **Hashes.** Every one of the 47 files is under `runner/paid_run.py`'s `HASHED_DIRS`. Of them, 13 are in Gate 3's `corpus_hash` and 23 in its `source_ledger_hash` (`corpus/freeze.json`). Candidate IDs derive from `original_payload_sha256` (`SPEC.md` Section 5).
- **`eval-006`.** This frozen evaluation base keeps two real third-party URLs in its adapted payload and in its three rendered fixtures, one a chat-service invite and one a forum. No other fixture holds a domain outside the reserved and example ones. This conflicts with `AGENTS.md`'s "reserved/example domains" and `SPEC.md` Section 3's "Every secret, identity, record, domain, and message is synthetic".
  - The W8-T2 review raised this as N-93-6 on November 13, before the Gate 3 freeze. The project lead classified that review the same day, as proposed: no blocking finding and no safety finding.
  - `tools/sandbox.py` denies every tool every network endpoint, and `tests/test_tool_sandbox.py` is Section 11's proof of that. No CANARY tool could reach these URLs or any of the addresses.
- **Reports.** `SECURITY.md` gives a private route, through GitHub private vulnerability reporting when it is enabled. On November 24 it was disabled.
- **The binding checkpoint.** `docs/commitments.md` says the attack text comes only from published sources, credited under their licenses, and that every task, tool, mailbox, and secret is fictional and local. It makes no claim about the domains in source text. Nothing here contradicts it.

## Options considered

1. **Treat the strings as Prohibited** (`docs/DATA_RELEASE.md`'s "personal/contact data"). Rejected on the test in item 1: nothing links any of them to an identified person.
2. **Redact them at `HEAD` through Section 11.** Rejected. Git history and the four public sources keep every value, so redaction removes nothing. The edit would break Gate 3's two corpus hashes, the candidate IDs, and the recorded paid-run digest.
3. **Leave the corpus out of the tagged release.** Rejected. A fresh clone could no longer reproduce the corpus, the fixtures, or the replay.
4. **Rule them public source text, ship as built, and disclose `eval-006`.** Chosen.

## Decision

1. **The test.** A string is Prohibited personal or contact data only if something links it to an identified person. Contact identifiers that a pinned, redistributable source wrote into its own attack text meet no such link. That covers email addresses, URLs, and phone-like and account-format strings. They are in `docs/DATA_RELEASE.md`'s Public source class, as payload text the source's license lets the project redistribute. This rules on Q-93-2 and on N-93-6's release class. No `SPEC.md` text changes.
2. **The records and the release list ship as they are.** No hashed file changes. The release list's `[address withheld <sha8>]` view stays the public listing of the originals. N-93-6's two suggested fixes to the release list, a wider `policy` statement and reading `redistribution` from the recorded license decision, aren't made, because `corpus/release_payloads.py` and its output are hashed. Its docstring's claim that adapted payloads hold only `fixture.test` addresses is true of email addresses; `eval-006`'s URLs are disclosed under item 5.
3. **`eval-006` stays frozen and unrepaired.** It was classified non-safety before the freeze, and no tool can reach either URL. It was found before the November 22 cutoff, so [decision 0043](0043-gate4-and-demo-day-dates.md) item 5 doesn't apply, and it changes no scored field. The conflict with the synthetic-domain rule is disclosed. The release and the paper don't claim that every fixture domain is reserved or synthetic (claim removal; DEV-0010).
4. **A report reclassifies that value.** If anyone shows that a value identifies a real person, that value is Prohibited. `docs/DATA_RELEASE.md`'s incident response then applies as written: block the release, remove the value from Git history by an approved procedure, and never paste the value into a public issue or record. A report before the December 2 freeze blocks this release.
5. **Disclosure.** `THIRD_PARTY_NOTICES.md` says that the corpus records reproduce each source's original text verbatim, including the contact addresses and URLs the source wrote. It also says that the adapted payloads replace email addresses with `fixture.test` recipients, that `eval-006` keeps two real URLs, that no tool can reach any external address, and that reports go through `SECURITY.md`.

## Consequences

- **What is lost: nothing now.** No result, trial, estimand, claim, gate item, hashed file, or commitment changes. The paper loses only the option of claiming that every fixture domain is synthetic, which `eval-006` makes untrue.
- **The contingent cost.** An upheld report under item 4 would mean a history rewrite. That would break pinned commits, including the raw manifests' code commit, and change the affected candidate IDs and the corpus hashes. The repository has no written procedure for it yet. That cost exists whatever this record decides, because the values are already in public history.
- **For the report route to work,** the project lead turns on GitHub private vulnerability reporting before the Gate 5 step (`TASKS.md`, this row). Until then, `SECURITY.md`'s fallback applies: a public issue that asks for a private route and gives no value.
- **Lead time:** about 0.5 hours. Decision 0043 item 12's estimates for November 23–29 come to about 6.5 hours, so the week stays near 7, under [decision 0031](0031-merge-on-green.md)'s 10-hour trigger.

## Verification

- This record's pull request touches no `HASHED_DIRS` path and no `CODEOWNERS` path. It adds no address outside `fixture.test` and no corpus URL to any file.
- `tests/test_tasks_dependencies.py`, `tests/test_status_consistency.py`, `tests/test_commitments.py`, `tests/test_contract_lock.py`, `tests/test_release_payloads.py`, and the documentation tests pass, and CI runs the full suite.
