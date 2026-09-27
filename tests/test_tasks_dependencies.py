import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "TASKS.md"

SLICE_ROW = re.compile(r"^\| (W(\d+)-T(\d))(?: †)? \|")
SLICE_REF = re.compile(r"W(\d+)-T(\d)")


def slice_rows():
    rows = {}
    for line in TASKS.read_text(encoding="utf-8").splitlines():
        match = SLICE_ROW.match(line)
        if match:
            depends = line.split("|")[4].strip()
            rows[match.group(1)] = (int(match.group(2)), depends)
    return rows


def test_lattice_has_every_slice():
    expected = {f"W{week}-T{track}" for week in range(5, 14) for track in range(1, 6)}
    assert set(slice_rows()) == expected


def test_depends_names_only_work_merged_before_the_slice_starts():
    late = [
        f"{slice_id} depends on W{ref_week}-T{ref_track}"
        for slice_id, (week, depends) in sorted(slice_rows().items())
        for ref_week, ref_track in SLICE_REF.findall(depends)
        if int(ref_week) >= week
    ]
    assert late == []
