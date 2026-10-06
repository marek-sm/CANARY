"""C2/C3/C4 crossed indirect-delivery renderers.

Each renderer wraps one channel-agnostic content string (the fixture
template with `INSERTION_MARKER` substituted for either the attack payload
or its clean replacement) into the exact bytes that tool would return.
Each parser is the inverse: given rendered bytes, recover the exact
substituted content string, regardless of the escaping or wrapping that
channel's serialization applied.
"""

from __future__ import annotations

import html
import json
import re

INSERTION_MARKER = "{{INJECTION_SLOT}}"

_C2_RESOURCE = "sku-2201"
_C2_REVIEWER = "morgan91"
_C2_DATE = "2026-01-14"

_C3_PRODUCT_NAME = "Compact Desk Lamp"

_C4_REVIEW_DIV = re.compile(r'<div class="review"[^>]*>(.*?)</div>', re.S)


def substitute(template: str, value: str) -> str:
    """Replace the single insertion marker in template with value."""
    if template.count(INSERTION_MARKER) != 1:
        raise ValueError("template must contain exactly one insertion marker")
    return template.replace(INSERTION_MARKER, value)


def render_c2(content: str) -> str:
    """Structured tool/database output: a `query_db` result row."""
    row = {
        "product_id": _C2_RESOURCE,
        "review": {
            "reviewer": _C2_REVIEWER,
            "date": _C2_DATE,
            "comment": content,
        },
    }
    return json.dumps(row, ensure_ascii=False, indent=2)


def parse_c2(rendered: str) -> str:
    row = json.loads(rendered)
    return row["review"]["comment"]


def render_c3(content: str) -> str:
    """Retrieved local document: the body `read_file` returns."""
    header = f"Product: {_C3_PRODUCT_NAME} ({_C2_RESOURCE})\n"
    header += f"Reviewer: {_C2_REVIEWER} | {_C2_DATE}\n\n"
    return header + content + "\n"


def parse_c3(rendered: str) -> str:
    _, _, body = rendered.partition("\n\n")
    return body[:-1] if body.endswith("\n") else body


def render_c4(content: str) -> str:
    """Fetched local web content: visible text `fetch_url` returns."""
    escaped = html.escape(content)
    return (
        "<html><body>"
        f"<h1>{_C3_PRODUCT_NAME}</h1>"
        f'<div class="review" data-reviewer="{_C2_REVIEWER}" data-date="{_C2_DATE}">'
        f"{escaped}</div>"
        "</body></html>"
    )


def parse_c4(rendered: str) -> str:
    match = _C4_REVIEW_DIV.search(rendered)
    if match is None:
        raise ValueError("no review div found in rendered C4 content")
    return html.unescape(match.group(1))


# --- v2: record renderers for dev-002 onward -------------------------------
#
# The v1 functions above stay as they are: dev-001's committed rendered hashes
# and the six-cell runner both depend on those exact bytes. From dev-002 on,
# each base carries a `fixture.wrapper` block in its record instead of
# hard-coded constants:
#
#   {"title": "...", "facts": {"field": "value", ...}, "text_field": "note"}
#
# `facts` are the benign facts the task's expected answer comes from. Every
# channel prints all of them, in record order, so C2/C3/C4 agree on the answer.
# The substituted content only ever lands in `text_field`.

RECORD_EXTRACTOR_VERSIONS = {
    "C2": "c2-extract-v2",
    "C3": "c3-extract-v2",
    "C4": "c4-extract-v2",
}


def _check_wrapper(wrapper: dict) -> None:
    field = wrapper["text_field"]
    if field in wrapper["facts"]:
        raise ValueError(f"text_field {field!r} collides with a fact name")
    for key, value in wrapper["facts"].items():
        if "\n" in str(key) or "\n" in str(value):
            raise ValueError("fact names and values must be single-line")
    if "\n" in wrapper["title"]:
        raise ValueError("title must be single-line")


def render_record_c2(content: str, wrapper: dict) -> str:
    """`query_db` row: the benign facts plus the one free-text field."""
    _check_wrapper(wrapper)
    row = dict(wrapper["facts"])
    row[wrapper["text_field"]] = content
    return json.dumps(row, ensure_ascii=False, indent=2)


def parse_record_c2(rendered: str, wrapper: dict) -> str:
    return json.loads(rendered)[wrapper["text_field"]]


def render_record_c3(content: str, wrapper: dict) -> str:
    """`read_file` body: title and `field: value` lines, blank line, then text."""
    _check_wrapper(wrapper)
    header = wrapper["title"] + "\n"
    header += "".join(f"{k}: {v}\n" for k, v in wrapper["facts"].items())
    return header + "\n" + content + "\n"


def parse_record_c3(rendered: str, wrapper: dict) -> str:
    _, sep, body = rendered.partition("\n\n")
    if not sep:
        raise ValueError("no header/body separator in rendered C3 content")
    return body[:-1] if body.endswith("\n") else body


def render_record_c4(content: str, wrapper: dict) -> str:
    """`fetch_url` page: facts as a definition list, text in its own div."""
    _check_wrapper(wrapper)
    esc = html.escape
    facts = "".join(
        f"<dt>{esc(str(k))}</dt><dd>{esc(str(v))}</dd>"
        for k, v in wrapper["facts"].items()
    )
    return (
        "<html><body>"
        f"<h1>{esc(wrapper['title'])}</h1>"
        f"<dl>{facts}</dl>"
        f'<div class="{esc(wrapper["text_field"])}">{esc(content)}</div>'
        "</body></html>"
    )


def parse_record_c4(rendered: str, wrapper: dict) -> str:
    field = re.escape(html.escape(wrapper["text_field"]))
    match = re.search(rf'<div class="{field}">(.*?)</div>', rendered, re.S)
    if match is None:
        raise ValueError(f"no {wrapper['text_field']} div in rendered C4 content")
    return html.unescape(match.group(1))


RECORD_RENDERERS = {
    "C2": (render_record_c2, parse_record_c2),
    "C3": (render_record_c3, parse_record_c3),
    "C4": (render_record_c4, parse_record_c4),
}
