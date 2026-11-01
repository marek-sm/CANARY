"""The committed task order (decision 0014; SPEC.md Section 5 step 8)."""

import hashlib
import json

import pytest

from tasks import registry, task_order

# Committed once from W6-T1's merged templates. Decision 0014: a template keeps
# its ID and index through any later fix, so this mapping never changes.
COMMITTED = {
    1: "meeting-confirm-email",
    2: "read-ticket-status",
    3: "order-status-extract",
    4: "invoice-receipt-email",
    5: "supplier-quote-compare",
    6: "open-ticket-ids",
    7: "maintenance-confirm-email",
    8: "service-hours-extract",
    9: "shipping-notice-email",
    10: "review-field-lookup",
}


# The slot table and salt as SPEC.md Section 5 step 8 states them, pinned here so
# the generator can't be checked only against itself.
SPEC_SLOTS = {
    "legitimate_high_risk": (1, 4, 7, 9),
    "read_query": (2, 6, 10),
    "local_web_extraction": (3, 8),
    "cross_source_comparison": (5,),
}
SPEC_SALT = "CANARY-2026-task|"


def committed():
    return json.loads(task_order.ORDER_FILE.read_text(encoding="utf-8"))


def test_the_committed_file_is_the_rule_applied_to_the_merged_templates():
    assert task_order.main(["--check"]) == 0
    assert committed() == task_order.compute(registry.templates())


def test_no_template_ever_changes_its_index():
    assert {entry["index"]: entry["template_id"] for entry in committed()["order"]} == COMMITTED


def test_indices_follow_the_category_slots():
    templates = registry.templates()
    order = committed()["order"]
    assert [entry["index"] for entry in order] == list(range(1, 11))
    for entry in order:
        assert templates[entry["template_id"]]["category"] == entry["category"]
        assert entry["index"] in SPEC_SLOTS[entry["category"]]
    assert task_order.INDICES == SPEC_SLOTS and task_order.SALT == SPEC_SALT


def test_within_a_category_the_lowest_hash_takes_the_lowest_index():
    for category in task_order.INDICES:
        entries = [e for e in committed()["order"] if e["category"] == category]
        hashes = [hashlib.sha256((SPEC_SALT + e["template_id"]).encode()).hexdigest() for e in entries]
        assert hashes == sorted(hashes)


def test_the_order_reads_only_ids_and_categories():
    templates = {tid: {"template_id": tid, "category": t["category"]} for tid, t in registry.templates().items()}
    assert task_order.compute(templates) == committed()


def test_a_template_set_that_doesnt_fill_the_slots_is_refused():
    templates = dict(registry.templates())
    templates.pop("review-field-lookup")
    with pytest.raises(ValueError, match="read_query"):
        task_order.compute(templates)


def test_an_unknown_category_is_refused():
    templates = dict(registry.templates())
    templates["extra"] = {"template_id": "extra", "category": "summarization"}
    with pytest.raises(ValueError, match="category"):
        task_order.compute(templates)


def test_check_and_write_refuse_a_file_that_differs(tmp_path, monkeypatch):
    stale = tmp_path / "task_order.json"
    stale.write_text(task_order.ORDER_FILE.read_text(encoding="utf-8").replace('"index": 1,', '"index": 11,'), encoding="utf-8")
    monkeypatch.setattr(task_order, "ORDER_FILE", stale)
    assert task_order.main(["--check"]) == 1
    before = stale.read_text(encoding="utf-8")
    assert task_order.main([]) == 1  # the writer never rewrites a committed order
    assert stale.read_text(encoding="utf-8") == before
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(task_order, "ORDER_FILE", missing)
    assert task_order.main(["--check"]) == 1
