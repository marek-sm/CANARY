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
