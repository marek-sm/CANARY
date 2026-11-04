"""The ten decision 0025 variants, and the multi-row source, through real delivery.

Mock provider only: every cell renders an evaluation-shaped base with the committed
renderers, overlays it on the W6-T1 fixtures, and runs under each configuration, so a
variant the gate blocks or marking breaks fails here and not first on a paid run.
"""
import copy
import json
from pathlib import Path

import pytest

from channels.render import RECORD_RENDERERS
from corpus import render_fixtures
from defenses.interfaces import DATAMARK_MARKER
from runner import delivery, execute, schedule
from runner.mock_provider import MOCK_MODEL_ID
from runner.mock_slice import read_jsonl
from tasks import registry
from tools.query_db import QUERIES

VARIANTS = [
    ("read-ticket-status", "C2"), ("read-ticket-status", "C4"),
    ("invoice-receipt-email", "C2"), ("invoice-receipt-email", "C4"),
    ("maintenance-confirm-email", "C2"), ("maintenance-confirm-email", "C4"),
    ("open-ticket-ids", "C2"), ("open-ticket-ids", "C3"), ("open-ticket-ids", "C4"),
    ("service-hours-extract", "C2"), ("service-hours-extract", "C3"),
]
CONFIGURATIONS = ("D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING")


def _resource(call):
    if call["tool"] == "query_db":
        return QUERIES[call["args"]["query_id"]][1]
    return call["args"]["path"] if call["tool"] == "read_file" else call["args"]["url"]


def _facts(template):
    call = template["variants"]["C2"]["required_calls"][0]
    param, resource = QUERIES[call["args"]["query_id"]]
    seed = json.loads((registry.FIXTURES / "db-seed.json").read_text(encoding="utf-8"))
    rows = [row for row in seed if row["resource"] == resource and row["lookup"] == call["args"]["params"][param]]
    return json.loads(rows[0]["content"])


def _base(tmp_path, monkeypatch, template_id):
    """An evaluation-shaped base for this task, rendered by the committed renderers."""
    monkeypatch.setattr(render_fixtures, "ROOT", tmp_path)
    monkeypatch.setattr(delivery, "REPO_ROOT", tmp_path)
    record = copy.deepcopy(DEV_BASE)
    base_id = f"variant-{template_id}"
    template = registry.load(template_id)
    record["base_case_id"] = base_id
    record["task"] = {**record["task"], "template_id": template_id}
    record["fixture"]["wrapper"] = {"title": "Fictional record", "facts": _facts(template), "text_field": "note"}
    record["fixture"]["template_path"] = str(tmp_path / f"fixtures/{base_id}/content.template.txt")
    record["fixture"]["rendered_hash_manifest"] = f"fixtures/{base_id}/rendered-hashes.json"
    for channel, variant in template["variants"].items():
        record["channels"][channel]["resource"] = _resource(variant["required_calls"][0])
    template_text = DEV_TEMPLATE
    path = Path(record["fixture"]["template_path"])
    path.parent.mkdir(parents=True)
    path.write_text(template_text, encoding="utf-8")
    for target, text in render_fixtures.expected_files(record).items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / f"{base_id}.json").write_text(json.dumps(record), encoding="utf-8")
    return record, corpus, template


DEV_BASE = json.loads((delivery.REPO_ROOT / "corpus/development/dev-002.json").read_text(encoding="utf-8"))
DEV_TEMPLATE = (delivery.REPO_ROOT / DEV_BASE["fixture"]["template_path"]).read_text(encoding="utf-8")


@pytest.mark.parametrize("template_id,channel", VARIANTS)
def test_a_variant_runs_through_delivery_under_every_configuration(tmp_path, monkeypatch, template_id, channel):
    record, corpus, template = _base(tmp_path, monkeypatch, template_id)
    spec = {"experiment_id": "variant", "model_id": MOCK_MODEL_ID, "seed": "variant",
            "base_case_ids": [record["base_case_id"]], "channels": [channel], "conditions": ["attack", "clean"],
            "configurations": list(CONFIGURATIONS), "repeats": 1}
    trials = schedule.generate_schedule(spec)
    out = tmp_path / "run"
    execute.run_schedule(out, trials, corpus_root=corpus, spec=spec, delivery=True)
    assert len(trials) == 2 * len(CONFIGURATIONS)
    payload_word = record["attack"]["canonical_payload"].split()[0]
    for trial in trials:
        slug = out / execute.trial_slug(trial)
        (result,) = read_jsonl(slug / "results.jsonl", "result")
        events = read_jsonl(slug / "events.jsonl", "event")
        assert result["termination_reason"] == "final_answer", (trial.configuration, result["termination_reason"])
        assert result["utility"]["pass"] is True, trial.configuration
        observations = [e["payload"]["observation"] for e in events if e["event_type"] == "tool_result"]
        assert observations and all(o["ok"] for o in observations), trial.configuration
        delivered = json.dumps(observations[0], ensure_ascii=False)
        assert (DATAMARK_MARKER in delivered) is (trial.configuration == "D2_DATAMARKING")
        attacked = trial.condition == "attack"
        assert (payload_word in delivered.replace(DATAMARK_MARKER, " ")) is attacked
        if template_id == "open-ticket-ids":
            source = observations[0]
            if channel == "C2":
                assert [row["record_id"] for row in source["rows"]] == ["T-100", "T-102"]
                assert (payload_word in source["rows"][0]["content"].replace(DATAMARK_MARKER, " ")) is attacked
                assert payload_word not in source["rows"][1]["content"].replace(DATAMARK_MARKER, " ")
            else:
                records = delivery.observed_records(source)
                assert sorted(r["ticket_id"] for r in records) == ["T-100", "T-102"], "the channels list the same rows"
                assert all(r["status"] == "open" for r in records)


def test_the_payload_goes_in_the_row_holding_the_bases_facts(tmp_path, monkeypatch):
    """Not simply the first row of a multi-row source."""
    record, _, _ = _base(tmp_path, monkeypatch, "open-ticket-ids")
    facts = {"ticket_id": "T-102", "status": "open"}
    record["fixture"]["wrapper"]["facts"] = facts
    delivered = json.dumps({**facts, "note": "the payload"})
    files = {"db-seed.json": (registry.FIXTURES / "db-seed.json").read_bytes()}
    delivery._overlay(files, record, "C2", delivered)
    rows = {row["record_id"]: row["content"] for row in json.loads(files["db-seed.json"]) if row["resource"] == "tickets"}
    assert rows["T-102"] == delivered
    assert "the payload" not in rows["T-100"] and "the payload" not in rows["T-101"]


def test_a_rendered_list_puts_the_note_beside_its_own_record(tmp_path, monkeypatch):
    record, _, _ = _base(tmp_path, monkeypatch, "open-ticket-ids")
    wrapper = render_fixtures.wrapper_with_listed_records(record)
    assert wrapper["also"] == [{"ticket_id": "T-102", "status": "open"}]
    rendered = RECORD_RENDERERS["C3"][0]("the note", wrapper)
    assert rendered.index("T-102") < rendered.index("T-100") < rendered.index("the note")


def test_facts_that_are_no_row_of_a_multi_row_source_are_refused(tmp_path, monkeypatch):
    record, _, _ = _base(tmp_path, monkeypatch, "open-ticket-ids")
    record["fixture"]["wrapper"]["facts"] = {"ticket_id": "T-999", "status": "open"}
    with pytest.raises(ValueError, match="aren't a row"):
        render_fixtures.wrapper_with_listed_records(record)


def test_a_listed_record_must_be_single_line():
    wrapper = {"title": "t", "facts": {"a": "b"}, "text_field": "note", "also": [{"a": "one\ntwo"}]}
    for channel in ("C3", "C4"):
        with pytest.raises(ValueError, match="single-line"):
            RECORD_RENDERERS[channel][0]("note", wrapper)


def test_marking_covers_every_row_of_a_multi_row_observation():
    observation = {"ok": True, "rows": [{"record_id": record, "content": json.dumps({"note": "two words"})}
                                        for record in ("a", "b")]}
    marked = delivery.mark_observation("query_db", observation)
    assert all(DATAMARK_MARKER in row["content"] for row in marked["rows"])


@pytest.mark.parametrize("mock_answer", [
    lambda template, channel, observation: delivery.DeliveryTaskMock(template, channel)._answer([observation]),
])
def test_the_mocks_count_only_open_tickets(mock_answer):
    template = registry.load("open-ticket-ids")
    rows = [{"record_id": t, "content": json.dumps({"ticket_id": t, "status": s})}
            for t, s in (("T-100", "open"), ("T-101", "closed"))]
    assert mock_answer(template, "C2", {"ok": True, "rows": rows}) == {"ticket_ids": ["T-100"]}
