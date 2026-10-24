import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "TASKS.md"

SLICE_ROW = re.compile(r"^\| (W(\d+)-T(\d))(?: †)? \|")
SLICE_REF = re.compile(r"W(\d+)-T(\d)")
# Slice, Committed deliverable, Est, Depends, Pull-forward, Defer first, Owner.
SLICE_CELLS = 7
DEPENDS = 3


def cells(line):
    """A table row's cells, split on unescaped pipes only, so a `\\|` inside a
    cell can't shift the Depends column."""
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip())[1:-1]]


def slice_rows(text=None):
    rows = {}
    for line in (TASKS.read_text(encoding="utf-8") if text is None else text).splitlines():
        match = SLICE_ROW.match(line)
        if match:
            row = cells(line)
            assert len(row) == SLICE_CELLS, f"{match.group(1)}: {len(row)} cells"
            rows[match.group(1)] = (int(match.group(2)), row[DEPENDS])
    return rows


def late_dependencies(rows):
    return [
        f"{slice_id} depends on W{ref_week}-T{ref_track}"
        for slice_id, (week, depends) in sorted(rows.items())
        for ref_week, ref_track in SLICE_REF.findall(depends)
        if int(ref_week) >= week
    ]


def test_lattice_has_every_slice():
    expected = {f"W{week}-T{track}" for week in range(5, 14) for track in range(1, 6)}
    assert set(slice_rows()) == expected


def test_depends_names_only_work_merged_before_the_slice_starts():
    assert late_dependencies(slice_rows()) == []


def test_an_escaped_pipe_cannot_hide_a_same_week_dependency():
    row = r"| W8-T3 | The `tier\|budget` input | 5.0 | W8-T1 (Mon) | — | — | Samson |"
    assert late_dependencies(slice_rows(row)) == ["W8-T3 depends on W8-T1"]


def test_a_slice_row_with_a_shifted_column_is_refused():
    row = "| W8-T3 | The input | 5.0 | W7-T3 (Mon) | — | Samson |"
    with pytest.raises(AssertionError, match="6 cells"):
        slice_rows(row)
