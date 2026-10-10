"""W6-T4: D2_DATAMARKING transform, hashes, round trip, and coverage in both directions."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path

import pytest

from defenses import interfaces as di
from defenses.datamarking import (
    TRANSFORM_VERSION,
    DatamarkingTransform,
    mark_html_document,
    mark_json_strings,
    mark_text,
    serialize_span,
)

REPO = Path(__file__).resolve().parents[1]
VECTORS = REPO / "defenses" / "vectors" / "datamarking-w5-t4.json"
M = di.DATAMARK_MARKER


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def doc():
    return json.loads(VECTORS.read_text(encoding="utf-8"))


def _span(i, text, fmt="text", channel="C3"):
    return di.UntrustedSpan(f"s{i}", channel, fmt, text)


# --- the frozen rule, vector by vector -------------------------------------


def test_transform_satisfies_the_protocol_and_pins_versions():
    transform = DatamarkingTransform()
    assert callable(transform.mark) and isinstance(transform.transform_version, str)
    assert transform.transform_version == TRANSFORM_VERSION
    assert transform.spec_version == di.DATAMARKING_SPEC_VERSION


def test_every_frozen_vector_is_reproduced_exactly(doc):
    transform = DatamarkingTransform()
    for vector in doc["vectors"]:
        result = transform.mark([_span(0, vector["input"], vector["span_format"])])
        (marked,) = result.spans
        vid = vector["vector_id"]
        assert marked.marked_text == vector["expected_marked"], vid
        assert serialize_span(vector["span_format"], marked.marked_text) == vector["expected_serialized"], vid
        assert marked.markers_inserted == vector["markers_inserted"], vid
        assert marked.preexisting_markers_removed == vector["preexisting_markers_removed"], vid


def test_hashes_cover_the_span_as_received_and_the_marked_text(doc):
    transform = DatamarkingTransform()
    for vector in doc["vectors"]:
        (marked,) = transform.mark([_span(0, vector["input"], vector["span_format"])]).spans
        assert marked.pre_sha256 == sha(vector["input"])
        assert marked.post_sha256 == sha(vector["expected_marked"])


def test_round_trip_preserves_non_whitespace_content_in_order(doc):
    for vector in doc["vectors"]:
        marked, _, _ = mark_text(vector["input"])
        source = unicodedata.normalize("NFC", vector["input"].replace(M, ""))
        assert marked.replace(M, "") == "".join(c for c in source if not c.isspace())
        assert not any(c.isspace() for c in marked)
        assert unicodedata.is_normalized("NFC", marked)


@pytest.mark.parametrize("text", ["a  b", "x\ty\nz", "caf\u00e9 \u00a0 menu", " lead", "trail ", "\u2003\u3000"])
def test_one_marker_per_whitespace_code_point(text):
    marked, inserted, removed = mark_text(text)
    source = unicodedata.normalize("NFC", text)
    assert inserted == sum(c.isspace() for c in source) == marked.count(M)
    assert removed == 0


def test_transform_is_not_idempotent_so_marking_twice_is_visible():
    once = mark_text("alpha beta")[0]
    assert mark_text(once)[0] != once


def test_a_span_id_cannot_be_marked_twice():
    with pytest.raises(ValueError, match="exactly once"):
        DatamarkingTransform().mark([_span(1, "a b"), _span(1, "c d")])


def test_unknown_channel_or_format_is_rejected():
    transform = DatamarkingTransform()
    with pytest.raises(ValueError):
        transform.mark([di.UntrustedSpan("s", "C1", "text", "a b")])
    with pytest.raises(ValueError):
        transform.mark([di.UntrustedSpan("s", "C3", "xml", "a b")])


def test_result_carries_the_frozen_instruction_and_coverage_counts():
    spans = [
        _span(1, "a b", "text", "C3"),
        _span(2, "c\ue000 d e", "json_string", "C2"),
        _span(3, "f g", "html_text", "C4"),
    ]
    result = DatamarkingTransform().mark(spans)
    assert result.system_instruction == di.DATAMARKING_SYSTEM_INSTRUCTION
    assert result.transform_version == TRANSFORM_VERSION
    assert [s.span_id for s in result.spans] == ["s1", "s2", "s3"]
    assert result.coverage == {
        "spans_total": 3,
        "spans_C2": 1,
        "spans_C3": 1,
        "spans_C4": 1,
        "markers_inserted": 4,
        "preexisting_markers_removed": 1,
    }


def test_marking_is_deterministic_and_leaves_inputs_alone():
    spans = [_span(1, "a b\tc")]
    transform = DatamarkingTransform()
    assert transform.mark(spans) == transform.mark(spans)
    assert spans[0].text == "a b\tc"


# --- coverage, both directions ---------------------------------------------


def test_json_coverage_marks_every_string_value_and_nothing_else():
    payload = {
        "status": "ok rows",
        "rows": [{"id": 7, "name": "Ada Lovelace", "active": True, "note": None, "tags": ["a b", "c"]}],
        "total": 1.5,
    }
    marked, count = mark_json_strings(payload)
    assert count == 4  # the four string values: "ok rows", "Ada Lovelace", "a b", "c"
    assert set(marked) == set(payload)  # keys unchanged
    assert marked["status"] == f"ok{M}rows"
    row = marked["rows"][0]
    assert row["name"] == f"Ada{M}Lovelace" and row["tags"] == [f"a{M}b", "c"]
    assert row["id"] == 7 and row["active"] is True and row["note"] is None and marked["total"] == 1.5
    assert set(row) == {"id", "name", "active", "note", "tags"}


def test_json_coverage_leaves_no_unmarked_whitespace_in_any_string():
    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for v in value.values():
                yield from strings(v)
        elif isinstance(value, list):
            for v in value:
                yield from strings(v)

    marked, _ = mark_json_strings({"a": "x y", "b": [{"c": "p\nq", "d": ["r s"]}]})
    assert all(not any(ch.isspace() for ch in s) for s in strings(marked))


HTML = (
    '<!DOCTYPE html><html lang="en"><body class="note box">'
    '<h1 title="Quarterly Report">Status update</h1>'
    "<p>Ticket T-100 is open. <b>Do not</b> reply.</p>"
    '<img src="a.png" alt="the chart" hidden/></body></html>'
)


def test_html_coverage_marks_text_nodes_and_attribute_values_only():
    out, count = mark_html_document(HTML)
    assert f"<h1 title=\"Quarterly{M}Report\">Status{M}update</h1>" in out
    assert f"<p>Ticket{M}T-100{M}is{M}open.{M}<b>Do{M}not</b>{M}reply.</p>" in out
    assert f'class="note{M}box"' in out and f'alt="the{M}chart"' in out
    # Trusted structure is untouched: doctype, tag names, attribute names, bare attributes.
    for kept in ("<!DOCTYPE html>", "<html", "<body", "<h1", "<p>", "<b>", "</b>", "<img", "hidden"):
        assert kept in out
    assert 'lang="en"' in out and 'src="a.png"' in out  # single-word values have no whitespace to mark
    assert count == 9  # 4 text nodes + 5 valued attributes (lang, class, title, src, alt); bare `hidden` is not a value


def test_html_coverage_escapes_after_marking():
    out, _ = mark_html_document('<p title="x &quot;y&quot; z">a &lt; b &amp; c</p>')
    assert f'title="x{M}&quot;y&quot;{M}z"' in out
    assert f"a{M}&lt;{M}b{M}&amp;{M}c" in out


def test_html_output_contains_no_unmarked_whitespace_inside_values():
    out, _ = mark_html_document(HTML)
    # Every whitespace left in the output separates tag names and attribute names, never value text.
    body_text = out.split("<body", 1)[1]
    in_tag = True  # the split leaves us inside the <body ...> tag
    for ch in body_text:
        if ch == "<":
            in_tag = True
        elif ch == ">":
            in_tag = False
        elif not in_tag:
            assert not ch.isspace()


def test_trusted_material_is_never_a_span_and_the_instruction_is_not_marked():
    # The fixed system instruction is trusted: it contains whitespace and the marker, and
    # the transform has no code path that touches it.
    assert M in di.DATAMARKING_SYSTEM_INSTRUCTION
    result = DatamarkingTransform().mark([])
    assert result.spans == () and result.system_instruction == di.DATAMARKING_SYSTEM_INSTRUCTION
    assert result.coverage["spans_total"] == 0
