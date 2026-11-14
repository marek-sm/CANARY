"""Decision 0031 item 6: the paid-run gate requires an attested lead-side review.

`python -m runner.lead_review attest docs/reviews/<file>.md` appends a row to
``~/.canary/lead_review.jsonl`` (tests/conftest.py's stand-in home here). Every paid
grid, sweep, and rehearsal call, and `paid_run record`, then needs a row for this
checkout's `code_digest` with 0 open blocking findings, whose findings file in the
checkout still matches its hash. The live smoke is exempt.
"""

from __future__ import annotations

import json

import pytest

from runner import paid_run

HEADER = """# Lead-side review for the gate tests

- **`paid_run.code_digest`:** `{digest}`
- **Open blocking findings:** {blocking}

## Findings

None.
"""


def _digest(gate):
    return paid_run.code_digest(paid_run.code_hashes(gate.root))


def _review(gate, name="test-review.md", *, digest=None, blocking="0", commit=True):
    relative = f"docs/reviews/{name}"
    path = gate.root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(HEADER.format(digest=digest or _digest(gate), blocking=blocking), encoding="utf-8")
    if commit:
        gate.git("add", relative)
        gate.git("commit", "-qm", f"review {name}")
    return path


def _record_without_attesting(gate, canary_home):
    """A committed paid-run record of this checkout, with no attestation left: `record`
    itself needs one, so the fixture's row is dropped after recording. Written without
    importing runner.lead_review, so it runs unchanged on the tree before the fix."""
    record = gate.open()
    (canary_home / ".canary" / "lead_review.jsonl").unlink(missing_ok=True)
    return record


def _log(canary_home):
    return canary_home / ".canary" / "lead_review.jsonl"


def test_the_paid_gate_refuses_without_an_attested_review(gate, canary_home):
    record = _record_without_attesting(gate, canary_home)
    reason = gate.refusal(record)
    assert reason is not None and "lead-side review" in reason


def test_an_attested_review_of_this_digest_opens_the_gate(gate, canary_home):
    from runner import lead_review

    record = _record_without_attesting(gate, canary_home)
    row = lead_review.attest(_review(gate), root=gate.root)
    assert row["code_digest"] == _digest(gate) and row["open_blocking"] == 0
    assert row["findings_path"] == "docs/reviews/test-review.md"
    assert gate.refusal(record) is None


def test_the_row_lands_in_the_account_home_stand_in(gate, canary_home):
    from runner import lead_review

    lead_review.attest(_review(gate), root=gate.root)
    [row] = [json.loads(line) for line in (canary_home / ".canary" / "lead_review.jsonl").read_text().splitlines()]
    assert set(row) >= {"attested_at", "code_digest", "findings_path", "findings_sha256", "open_blocking", "commit"}


def test_an_open_blocking_finding_keeps_the_gate_shut(gate, canary_home):
    from runner import lead_review

    record = _record_without_attesting(gate, canary_home)
    lead_review.attest(_review(gate, blocking="1"), root=gate.root)
    reason = gate.refusal(record)
    assert reason is not None and "blocking" in reason


def test_an_unclassified_count_is_refused_at_attest(gate):
    from runner import lead_review

    with pytest.raises(lead_review.AttestRefused, match="classif"):
        lead_review.attest(_review(gate, blocking="0 proposed"), root=gate.root)


def test_a_missing_or_non_integer_count_is_refused_at_attest(gate):
    from runner import lead_review

    with pytest.raises(lead_review.AttestRefused, match="Open blocking findings"):
        lead_review.attest(_review(gate, blocking="none"), root=gate.root)


def test_a_review_of_another_digest_is_refused_at_attest(gate):
    from runner import lead_review

    with pytest.raises(lead_review.AttestRefused, match="code_digest"):
        lead_review.attest(_review(gate, digest="0" * 64), root=gate.root)


def test_an_uncommitted_findings_file_is_refused_at_attest(gate):
    from runner import lead_review

    with pytest.raises(lead_review.AttestRefused, match="commit"):
        lead_review.attest(_review(gate, commit=False), root=gate.root)


def test_a_findings_file_changed_after_attesting_shuts_the_gate(gate, canary_home):
    from runner import lead_review

    record = _record_without_attesting(gate, canary_home)
    path = _review(gate)
    lead_review.attest(path, root=gate.root)
    path.write_text(path.read_text() + "\nOne more finding.\n", encoding="utf-8")
    gate.git("commit", "-qam", "edit the review")
    reason = gate.refusal(record)
    assert reason is not None and "changed after it was attested" in reason


def test_a_code_change_after_attesting_shuts_the_gate(gate):
    from runner import lead_review

    lead_review.attest(_review(gate), root=gate.root)
    gate.commit_code("runner/code.py", "VALUE = 2\n")
    assert lead_review.refusal(gate.root) is not None


def test_record_refuses_without_an_attested_review(gate):
    with pytest.raises(paid_run.PaidRunRefused, match="lead-side review"):
        gate.record_unattested()


def test_the_live_smoke_needs_no_review(gate, tmp_path):
    assert gate.refusal(tmp_path / "no-record.json", live_smoke=True) is None


def test_the_command_line_attests_and_checks(gate, capsys):
    from runner import lead_review

    path = _review(gate)
    assert lead_review.main(["check"], root=gate.root) == 1
    assert lead_review.main(["attest", str(path)], root=gate.root) == 0
    assert lead_review.main(["check"], root=gate.root) == 0


def test_a_newer_blocking_review_closes_the_gate_an_older_one_opened(gate, canary_home):
    # Round 1 B1: the newest attestation of this digest governs.
    from runner import lead_review

    record = _record_without_attesting(gate, canary_home)
    lead_review.attest(_review(gate, "clean.md"), root=gate.root)
    assert gate.refusal(record) is None
    lead_review.attest(_review(gate, "whole-tree.md", blocking="2"), root=gate.root)
    reason = gate.refusal(record)
    assert reason is not None and "whole-tree.md" in reason and "2" in reason
    lead_review.attest(_review(gate, "fixed.md"), root=gate.root)
    assert gate.refusal(record) is None


@pytest.mark.parametrize("value", [False, 0.0, "0", None])
def test_only_an_integer_zero_opens_the_gate(gate, canary_home, value):
    from runner import lead_review

    record = _record_without_attesting(gate, canary_home)
    row = lead_review.attest(_review(gate), root=gate.root)
    _log(canary_home).write_text(json.dumps({**row, "open_blocking": value}) + "\n", encoding="utf-8")
    assert gate.refusal(record) is not None


def test_garbage_in_the_log_refuses_or_is_skipped_never_raises(gate, canary_home):
    from runner import lead_review

    record = _record_without_attesting(gate, canary_home)
    _log(canary_home).parent.mkdir(parents=True, exist_ok=True)
    _log(canary_home).write_bytes(b"\xff\xfe not json\n[1, 2]\n")
    assert gate.refusal(record) is not None
    lead_review.attest(_review(gate), root=gate.root)
    assert gate.refusal(record) is None
    with _log(canary_home).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"code_digest": _digest(gate), "open_blocking": 0, "findings_path": "a\u0000b"}) + "\n")
    reason = gate.refusal(record)
    assert reason is not None and "findings file" in reason


def test_a_deleted_findings_file_shuts_the_gate(gate, canary_home):
    from runner import lead_review

    record = _record_without_attesting(gate, canary_home)
    path = _review(gate)
    lead_review.attest(path, root=gate.root)
    gate.git("rm", "-q", path.relative_to(gate.root).as_posix())
    gate.git("commit", "-qm", "drop the review")
    assert gate.refusal(record) is not None


def test_the_digest_must_be_on_the_code_digest_field(gate):
    # Round 1 M1: a digest named elsewhere in the header doesn't attest.
    from runner import lead_review

    path = gate.root / "docs" / "reviews" / "elsewhere.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# Review\n\n- **Rejected tree:** `{_digest(gate)}`\n- **`paid_run.code_digest`:** `{'0' * 64}`\n"
                    "- **Open blocking findings:** 0\n", encoding="utf-8")
    gate.git("add", "docs/reviews/elsewhere.md")
    gate.git("commit", "-qm", "review")
    with pytest.raises(lead_review.AttestRefused, match="code_digest"):
        lead_review.attest(path, root=gate.root)


def test_a_digest_on_a_sub_bullet_of_the_field_attests(gate):
    from runner import lead_review

    path = gate.root / "docs" / "reviews" / "nested.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# Review\n\n- **`paid_run.code_digest`:**\n  - before: `{'0' * 64}`\n  - after: `{_digest(gate)}`\n"
                    "- **Open blocking findings:** 0 at that commit.\n", encoding="utf-8")
    gate.git("add", "docs/reviews/nested.md")
    gate.git("commit", "-qm", "review")
    assert lead_review.attest(path, root=gate.root)["open_blocking"] == 0


@pytest.mark.parametrize("value, count", [
    ("0", 0), ("0.", 0), ("0 at that commit.", 0), ("2. Two remain.", 2),
    ("0. The project lead classified every finding, accepting each class as proposed.", 0),
    ("0. Seven blocking readiness findings in #54 (R1-R7) are fixed.", 0),
])
def test_classified_counts_parse(value, count):
    from runner import lead_review

    assert lead_review.open_blocking(f"- **Open blocking findings:** {value}\n") == count


@pytest.mark.parametrize("text", [
    "- **Open blocking findings:** 0.5\n", "- **Open blocking findings:** 0x1\n",
    "- **Open blocking findings:** 0 (1 still open, unclassified)\n",
    "- **Open blocking findings:** 0 at f00; 3 open at HEAD\n",
    "- **Open blocking findings:** 0 proposed.\n",
    "- **Open blocking findings:** 0\n- **Open blocking findings**: 3\n",
    "- **Open blocking findings:** none\n",
])
def test_ambiguous_counts_are_refused(text):
    from runner import lead_review

    with pytest.raises(lead_review.AttestRefused):
        lead_review.open_blocking(text)


def test_the_committed_reviews_parse():
    # The two reviews on main, as written, read as classified with 0 open blocking.
    from runner import lead_review

    for name in ("2026-11-09-paid-run.md", "2026-11-11-w7-t2-t5.md"):
        text = (paid_run.REPO_ROOT / "docs" / "reviews" / name).read_text(encoding="utf-8")
        assert lead_review.open_blocking(text) == 0, name


def test_a_torn_last_row_never_swallows_the_next_attestation(gate, canary_home):
    # Round 2 M1: a crash mid-append leaves no newline; the next row must still be its own line.
    from runner import lead_review

    record = _record_without_attesting(gate, canary_home)
    lead_review.attest(_review(gate, "clean.md"), root=gate.root)
    with _log(canary_home).open("a", encoding="utf-8") as handle:
        handle.write('{"code_digest": "torn')
    lead_review.attest(_review(gate, "blocking.md", blocking="1"), root=gate.root)
    reason = gate.refusal(record)
    assert reason is not None and "blocking.md" in reason
