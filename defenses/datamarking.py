"""D2_DATAMARKING: the one locked, source-faithful datamarking implementation (W6-T4).

Source: Hines et al., arXiv:2403.14720v1, Section 3.3 (replace whitespace with a
marker and warn the model in the system prompt) and Section 5.4 (U+E000, removed
from the input before marking). Constants and the system instruction are frozen
in ``defenses.interfaces``; docs/DEFENSES_AND_POLICY.md Section 3 explains them.

For each untrusted span, applied exactly once:

  1. remove every pre-existing U+E000 and count it;
  2. normalize to NFC;
  3. replace each ``str.isspace()`` code point with one U+E000;
  4. (caller-visible) re-apply the channel's escaping with ``serialize_span``;
  5. record pre- and post-transform SHA-256.

``MarkedSpan.marked_text`` is the marked DECODED text (steps 1-3), so the round
trip "remove markers, get the NFC input with whitespace deleted" holds for every
format. ``pre_sha256`` hashes the span text exactly as received and
``post_sha256`` hashes ``marked_text``. ``serialize_span`` produces the escaped
form that goes back into the rendered fixture.

D2_DATAMARKING is behavioral guidance, not enforcement. The transform is NOT
idempotent (re-marking joins words); the pipeline must mark each span once, and
``mark`` rejects a repeated ``span_id`` to make a double pass loud.
"""

from __future__ import annotations

import hashlib
import html
import json
import unicodedata
from html.parser import HTMLParser
from typing import Any, Callable, Mapping, Sequence

from defenses.interfaces import (
    DATAMARK_MARKER,
    DATAMARKING_NORMALIZATION,
    DATAMARKING_SPEC_VERSION,
    DATAMARKING_SYSTEM_INSTRUCTION,
    DatamarkingResult,
    MarkedSpan,
    UntrustedSpan,
)

TRANSFORM_VERSION = "d2-datamarking-transform-v0.1.0"
_CHANNELS = ("C2", "C3", "C4")

_SERIALIZERS: Mapping[str, Callable[[str], str]] = {
    "text": lambda s: s,
    "json_string": lambda s: json.dumps(s, ensure_ascii=False),
    "html_text": lambda s: html.escape(s, quote=False),
    "html_attribute": lambda s: html.escape(s, quote=True),
}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def mark_text(text: str) -> tuple[str, int, int]:
    """Steps 1-3 for one decoded string: returns (marked, markers_inserted, markers_removed)."""
    removed = text.count(DATAMARK_MARKER)
    stripped = text.replace(DATAMARK_MARKER, "")
    normalized = unicodedata.normalize(DATAMARKING_NORMALIZATION, stripped)
    inserted = sum(1 for ch in normalized if ch.isspace())
    marked = "".join(DATAMARK_MARKER if ch.isspace() else ch for ch in normalized)
    return marked, inserted, removed


def serialize_span(span_format: str, marked_text: str) -> str:
    """Step 4: re-apply the channel's escaping to the marked decoded text."""
    try:
        return _SERIALIZERS[span_format](marked_text)
    except KeyError:
        raise ValueError(f"unknown span_format: {span_format!r}") from None


class DatamarkingTransform:
    """Marks every untrusted span and nothing else."""

    transform_version = TRANSFORM_VERSION
    spec_version = DATAMARKING_SPEC_VERSION

    def mark(self, spans: Sequence[UntrustedSpan]) -> DatamarkingResult:
        seen: set[str] = set()
        marked_spans: list[MarkedSpan] = []
        per_channel = {channel: 0 for channel in _CHANNELS}
        inserted_total = 0
        removed_total = 0
        for span in spans:
            if span.span_id in seen:
                raise ValueError(f"span {span.span_id!r} appears twice; mark each span exactly once")
            seen.add(span.span_id)
            if span.channel not in per_channel:
                raise ValueError(f"unknown channel: {span.channel!r}")
            if span.span_format not in _SERIALIZERS:
                raise ValueError(f"unknown span_format: {span.span_format!r}")
            marked, inserted, removed = mark_text(span.text)
            marked_spans.append(
                MarkedSpan(
                    span_id=span.span_id,
                    marked_text=marked,
                    pre_sha256=_sha256(span.text),
                    post_sha256=_sha256(marked),
                    markers_inserted=inserted,
                    preexisting_markers_removed=removed,
                )
            )
            per_channel[span.channel] += 1
            inserted_total += inserted
            removed_total += removed
        coverage = {
            "spans_total": len(marked_spans),
            **{f"spans_{channel}": count for channel, count in per_channel.items()},
            "markers_inserted": inserted_total,
            "preexisting_markers_removed": removed_total,
        }
        return DatamarkingResult(
            spans=tuple(marked_spans),
            system_instruction=DATAMARKING_SYSTEM_INSTRUCTION,
            transform_version=self.transform_version,
            coverage=coverage,
        )


# --------------------------------------------------------------------------
# Coverage helpers. Channel parsers (W6-T2) declare spans; these two helpers
# show the declared coverage rule precisely and let the tests check it in both
# directions: every untrusted string is marked, and nothing trusted is touched.
# --------------------------------------------------------------------------


def mark_json_strings(value: Any) -> tuple[Any, int]:
    """C2 coverage: mark every string VALUE in a decoded JSON document.

    Keys, numbers, booleans, and nulls are unchanged. Returns the marked value
    and the number of strings marked.
    """
    if isinstance(value, str):
        return mark_text(value)[0], 1
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        count = 0
        for key, item in value.items():
            out[key], n = mark_json_strings(item)
            count += n
        return out, count
    if isinstance(value, (list, tuple)):
        items = [mark_json_strings(item) for item in value]
        return [item for item, _ in items], sum(n for _, n in items)
    return value, 0


class _HtmlMarker(HTMLParser):
    """C4 coverage: mark every text node and attribute value; leave tags and structure alone."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.marked_spans = 0

    def _attrs(self, attrs: list[tuple[str, str | None]]) -> str:
        parts = []
        for name, value in attrs:
            if value is None:
                parts.append(f" {name}")
            else:
                self.marked_spans += 1
                marked = mark_text(value)[0]
                parts.append(f' {name}="{serialize_span("html_attribute", marked)}"')
        return "".join(parts)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.out.append(f"<{tag}{self._attrs(attrs)}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.out.append(f"<{tag}{self._attrs(attrs)}/>")

    def handle_endtag(self, tag: str) -> None:
        self.out.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.marked_spans += 1
        self.out.append(serialize_span("html_text", mark_text(data)[0]))

    def handle_comment(self, data: str) -> None:
        self.out.append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        self.out.append(f"<!{decl}>")


def mark_html_document(document: str) -> tuple[str, int]:
    """Mark a C4 HTML document. Returns the marked document and the number of spans marked."""
    parser = _HtmlMarker()
    parser.feed(document)
    parser.close()
    return "".join(parser.out), parser.marked_spans
