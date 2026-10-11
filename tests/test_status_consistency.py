"""Decision 0003's repository check: reject a `STATUS.md` claim that conflicts
with `TASKS.md`, `SPEC.md`, `protocol/active.json`, or the public results bundle.

CI runs this on every pull request, so it checks only claims that stay true
between weekly rollups. Each check is one-directional, so ordinary progress (a
ticked gate box, a `SPEC.md` version bump, a new protocol or results file)
never fails an older, dated rollup. Renaming something a rollup cites (an
owner, a linked heading, a Section 12 tier) does fail it, so the pull request
making the rename updates `STATUS.md` too.

The checks rely on this `STATUS.md` shape, and a missing row fails rather than
passing silently:

- an "Active-contributor count" row that starts with the count;
- an "Active/provisional tier" row whose first backticked tier ID is the tier;
- at least one "Gate N result" row;
- owner-outcome rows labelled "T<n> — <name>";
- until `protocol/active.json` exists, "Current protocol or run ID" and
  "Official empirical trials" rows that open with "Not" or "None";
- until `results/public/` holds a bundle, a "Public result or defense-effect
  claim" row that opens with "Not" or "None";
- at least one link to `TASKS.md`.
"""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "STATUS.md"
TASKS = ROOT / "TASKS.md"
SPEC = ROOT / "SPEC.md"

SLICE_ROW = re.compile(r"^\| (W(\d+)-T(\d))(?: †)? \|")
SLICE_REF = re.compile(r"\bW\d+-T\d+\b")
OWNER_ROW = re.compile(r"^T(\d+) — (.+)$")
GATE_ROW = re.compile(r"^Gate (\d+) result$")
BACKTICKED = re.compile(r"`([^`]+)`")
TIER_SHAPE = re.compile(r"[FRML]\d+(?:-[A-Z]+)?|ENGINEERING|STOP")
SPEC_HEADER = re.compile(r"^\*\*Public project and experimental specification v(\d+\.\d+\.\d+)\*\*", re.M)
SPEC_CLAIM = re.compile(r"`SPEC\.md` (?:is now )?v(\d+\.\d+\.\d+)")
GATE1_CAP = re.compile(r"\*\*Gate 1 fails:\*\*.*?`([A-Z0-9-]+)` or smaller")
NOT_YET = re.compile(r"^[*_]*(?:not|none)\b", re.I)
NOT_PASSED = re.compile(r"\bnot passed\b", re.I)
PASS_WORD = re.compile(r"(?<!not )\b(?:passed|met)\b", re.I)
LINK = re.compile(r"\]\(([^)\s]+)\)")


def table_rows(markdown):
    """First-column label -> second-column value for every Markdown table row."""
    rows = {}
    for line in markdown.splitlines():
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) >= 2:
                rows.setdefault(cells[0], cells[1])
    return rows


def missing_rows(rows, *labels):
    return [f"STATUS.md has no '{label}' row" for label in labels if label not in rows]


def slice_owners(tasks):
    owners = {}
    for line in tasks.splitlines():
        match = SLICE_ROW.match(line)
        if match:
            owners[match.group(1)] = line.strip().strip("|").split("|")[-1].strip()
    return owners


def person(name):
    return name.strip().strip("`").lstrip("@").casefold()


def section(markdown, number):
    match = re.search(rf"^## {number}\. .*?(?=^## \d+\. |\Z)", markdown, re.M | re.S)
    return match.group(0) if match else ""


def tier_table(spec):
    """Section 12 tier IDs in table order -> official trial count."""
    tiers = {}
    for line in section(spec, 12).splitlines():
        match = re.match(r"^\| `([A-Z0-9-]+)` \|.*\| ([\d,]+) \|$", line)
        if match:
            tiers[match.group(1)] = int(match.group(2).replace(",", ""))
    return tiers


def ceiling_table(spec):
    """Section 12 (fewest, most) active contributors -> maximum geometry."""
    ceilings = []
    for line in section(spec, 12).splitlines():
        match = re.match(r"^\| (\d+)(?:–(\d+)| (or more))? \| [^|`]*`([A-Z0-9-]+)`[^|]*\|$", line)
        if match:
            low, high, more, geometry = match.groups()
            ceilings.append((int(low), float("inf") if more else int(high or low), geometry))
    return ceilings


def empirical_tiers(spec):
    """Section 12 tiers with official trials, largest first.

    `ENGINEERING` and `STOP` run no official trials, and Section 12 doesn't rank
    them against the empirical rows, so `rank` gives them None.
    """
    return [tier for tier, trials in tier_table(spec).items() if trials > 0]


def rank(token, empirical):
    """Position of an empirical tier or tier family in `empirical`, or None."""
    for position, tier in enumerate(empirical):
        if tier == token or tier.startswith(token + "-"):
            return position
    return None


def tier_tokens(text):
    return [token for token in BACKTICKED.findall(text) if TIER_SHAPE.fullmatch(token)]


def current_tier(rows):
    tokens = tier_tokens(rows.get("Active/provisional tier", ""))
    return tokens[0] if tokens else None


def slice_id_conflicts(status, tasks):
    lattice = slice_owners(tasks)
    return [f"{ref} is not a TASKS.md slice" for ref in sorted(set(SLICE_REF.findall(status))) if ref not in lattice]


def owner_conflicts(status, tasks):
    portfolio_rows = [match for match in map(OWNER_ROW.match, table_rows(status)) if match]
    if not portfolio_rows:
        return ["STATUS.md has no 'T<n> — <name>' owner rows"]
    owners = slice_owners(tasks)
    conflicts = []
    for match in portfolio_rows:
        track, name = match.groups()
        portfolio = {person(owner) for slice_id, owner in owners.items() if slice_id.endswith(f"-T{track}")}
        if person(name) not in portfolio:
            conflicts.append(f"T{track} — {name} owns no T{track} slice in TASKS.md")
    return conflicts


def tier_conflicts(status, spec):
    tiers, ceilings = tier_table(spec), ceiling_table(spec)
    if not tiers or not ceilings:
        return ["SPEC.md Section 12 tier or ceiling table not found"]
    rows = table_rows(status)
    known = set(tiers) | {geometry for _, _, geometry in ceilings}
    conflicts = missing_rows(rows, "Active-contributor count", "Active/provisional tier")
    conflicts += [f"`{token}` is not a SPEC.md Section 12 tier" for token in tier_tokens(status) if token not in known]
    tier = current_tier(rows)
    count = re.match(r"\d+", rows.get("Active-contributor count", ""))
    if "Active/provisional tier" in rows and tier is None:
        conflicts.append("the 'Active/provisional tier' row names no Section 12 tier")
    if "Active-contributor count" in rows and count is None:
        conflicts.append("the 'Active-contributor count' row doesn't start with a number")
    empirical = empirical_tiers(spec)
    if conflicts or rank(tier, empirical) is None:
        return conflicts
    contributors = int(count.group(0))
    ceiling = next(geometry for low, high, geometry in ceilings if low <= contributors <= high)
    if rank(ceiling, empirical) is None or rank(tier, empirical) < rank(ceiling, empirical):
        return [f"tier `{tier}` is above the Section 12 ceiling `{ceiling}` for {contributors} active contributors"]
    return []


def gate1_response_conflicts(status, spec):
    rows = table_rows(status)
    if not NOT_PASSED.search(rows.get("Gate 1 result", "")):
        return []
    cap = GATE1_CAP.search(spec)
    if not cap:
        return ["SPEC.md Section 11 has no Gate 1 failure cap"]
    tier, empirical = current_tier(rows), empirical_tiers(spec)
    if tier and rank(tier, empirical) is not None and rank(tier, empirical) < rank(cap.group(1), empirical):
        return [f"tier `{tier}` is above `{cap.group(1)}`, the Gate 1 failure cap, while Gate 1 is not passed"]
    return []


def version(text):
    return tuple(int(part) for part in text.split("."))


def spec_version_conflicts(status, spec):
    header = SPEC_HEADER.search(spec)
    if not header:
        return ["SPEC.md header has no version"]
    return [
        f"STATUS.md cites SPEC.md v{claim}, newer than v{header.group(1)}"
        for claim in SPEC_CLAIM.findall(status)
        if version(claim) > version(header.group(1))
    ]


def protocol_conflicts(status, protocol_exists):
    if protocol_exists:
        return []
    rows = table_rows(status)
    labels = ("Current protocol or run ID", "Official empirical trials")
    return missing_rows(rows, *labels) + [
        f"'{label}' claims a protocol before protocol/active.json exists"
        for label in labels
        if label in rows and not NOT_YET.match(rows[label])
    ]


def public_result_conflicts(status, has_bundle):
    if has_bundle:
        return []
    rows = table_rows(status)
    label = "Public result or defense-effect claim"
    if label not in rows:
        return missing_rows(rows, label)
    if NOT_YET.match(rows[label]):
        return []
    return [f"'{label}' claims a result before results/public/ holds a bundle"]


def gate_checklist(tasks, gate):
    """(ticked, text) for each checkbox under TASKS.md's '### Gate <n>' heading, or None."""
    lines = tasks.splitlines()
    for index, line in enumerate(lines):
        if re.match(rf"^### Gate {gate}\b", line):
            items = []
            for item in lines[index + 1:]:
                if item.startswith("#"):
                    break
                box = re.match(r"^- \[([ x])\] (.*)$", item)
                if box:
                    items.append((box.group(1) == "x", box.group(2)))
            return items
    return None


def claims_pass(value):
    return not NOT_PASSED.search(value) and bool(PASS_WORD.search(value))


def gate_conflicts(status, tasks):
    gates = [(GATE_ROW.match(label), value) for label, value in table_rows(status).items()]
    gates = [(int(match.group(1)), value) for match, value in gates if match]
    if not gates:
        return ["STATUS.md has no 'Gate N result' row"]
    conflicts = []
    for gate, value in gates:
        if not claims_pass(value):
            continue
        items = gate_checklist(tasks, gate)
        if items is None:
            conflicts.append(f"Gate {gate} is reported passed but TASKS.md has no Gate {gate} checklist")
        else:
            conflicts += [f"Gate {gate} is reported passed but TASKS.md leaves open: {text}" for ticked, text in items if not ticked]
    return conflicts


def heading_slugs(markdown):
    """GitHub's heading anchors: lowercased, punctuation dropped, spaces to hyphens, repeats numbered."""
    slugs, seen, fenced = set(), {}, False
    for line in markdown.splitlines():
        if line.startswith("```"):
            fenced = not fenced
            continue
        heading = re.match(r"^#{1,6} (.*)$", line)
        if heading and not fenced:
            slug = re.sub(r"[^\w\- ]", "", heading.group(1).strip().lower()).replace(" ", "-")
            slugs.add(f"{slug}-{seen[slug]}" if slug in seen else slug)
            seen[slug] = seen.get(slug, 0) + 1
    return slugs


def link_conflicts(status, root):
    conflicts, paths = [], []
    for target in LINK.findall(status):
        if re.match(r"[a-z]+:", target):
            continue
        path, _, anchor = target.partition("#")
        paths.append(Path(path))
        if path and not (root / path).exists():
            conflicts.append(f"link target {target} does not exist")
        elif anchor and (not path or path.endswith(".md")):
            text = (root / path).read_text(encoding="utf-8") if path else status
            if anchor not in heading_slugs(text):
                conflicts.append(f"link anchor {target} matches no heading")
    if Path("TASKS.md") not in paths:
        conflicts.append("STATUS.md does not link TASKS.md")
    return conflicts


def conflicts(status, tasks, spec, root, protocol_exists, has_bundle):
    return (
        slice_id_conflicts(status, tasks)
        + owner_conflicts(status, tasks)
        + tier_conflicts(status, spec)
        + gate1_response_conflicts(status, spec)
        + spec_version_conflicts(status, spec)
        + protocol_conflicts(status, protocol_exists)
        + public_result_conflicts(status, has_bundle)
        + gate_conflicts(status, tasks)
        + link_conflicts(status, root)
    )


def repo_state():
    return {
        "tasks": TASKS.read_text(encoding="utf-8"),
        "spec": SPEC.read_text(encoding="utf-8"),
        "root": ROOT,
        "protocol_exists": (ROOT / "protocol" / "active.json").exists(),
        "has_bundle": any(
            path.is_file() and path.name != ".gitkeep" for path in (ROOT / "results" / "public").rglob("*")
        ),
    }


FIXTURE = """\
# CANARY Status — Club Week 6 — October 4, 2026

| Field | Current public state |
|---|---|
| Documentation baseline | `SPEC.md` is now v1.3.0 |
| Active-contributor count | 6 — five portfolio owners plus the project lead |
| Active/provisional tier | Provisional build geometry: `R15` |
| Gate 1 result | **Not passed** at `6263576`, with only the versioned-contract item unmet |
| Current protocol or run ID | Not created; required by Gate 3 |
| Official empirical trials | None represented as started |
| Public result or defense-effect claim | None |

| Portfolio | Week 6 outcome |
|---|---|
| T1 — Chace | `W6-T1` |

Slice owners live in [`TASKS.md`](TASKS.md); Gate 1 is [checked here](TASKS.md#gate-1--end-of-week-5), after [decision 0007](docs/decisions/0007-gate1-corpus-rules-freeze.md).
"""

TASKS_FIXTURE = """\
| W5-T1 | One safe tool | 3.5 ⚠ | Committed scaffold (Mon) | → W6-T1 | — | Chace |
| W6-T1 | Remaining tools | 11.0 ⚠ | W5-T1 (Mon) | → W7-T1 | — | Chace |

### Gate 1 — end of week 5

- [x] One excluded base renders into attack and exact clean twins.
- [ ] Lead's lock commit: the measurement contract is versioned.

### Gate 5 and release — weeks 11 through 13

- [ ] `make report` and `make replay` work from a fresh clone.
"""


def edited(old, new, text=FIXTURE):
    assert old in text
    return text.replace(old, new)


def with_row(markdown, label, value):
    return re.sub(rf"^\| {re.escape(label)} \|[^|\n]*\|$", f"| {label} | {value} |", markdown, count=1, flags=re.M)


def rename_portfolio_owner(status, track, name):
    return re.sub(rf"^\| T{track} — [^|]+\|", f"| T{track} — {name} |", status, flags=re.M)


def rename_slice_owners(tasks, track, name):
    pattern = re.compile(rf"^(\| W\d+-T{track}(?: †)? \|.*\| )[^|]+( \|)$", re.M)
    return pattern.sub(lambda match: match.group(1) + name + match.group(2), tasks)


def test_status_md_agrees_with_its_authorities():
    assert conflicts(STATUS.read_text(encoding="utf-8"), **repo_state()) == []


def test_a_week_6_rollup_with_renamed_owners_passes():
    state = repo_state()
    state["spec"] = SPEC_HEADER.sub("**Public project and experimental specification v1.4.0**", state["spec"], count=1)
    status = STATUS.read_text(encoding="utf-8")
    status = re.sub(r"^# .*$", "# CANARY Status — Club Week 6 — October 4, 2026", status, count=1, flags=re.M)
    status = with_row(status, "Gate 1 result", "Not passed at `6263576`, with only the versioned-contract item unmet")
    status = SPEC_CLAIM.sub("`SPEC.md` is now v1.4.0", status)
    for track, status_name, tasks_name in (
        (2, "`j0hanj`", "`@j0hanj`"),
        (3, "@samsonchang2028", "samsonchang2028"),
        (5, "milesshoe", "MilesShoe"),
    ):
        status = rename_portfolio_owner(status, track, status_name)
        state["tasks"] = rename_slice_owners(state["tasks"], track, tasks_name)

    assert conflicts(status, **state) == []


def test_the_fixture_has_no_conflicts():
    assert conflicts(FIXTURE, TASKS_FIXTURE, SPEC.read_text(encoding="utf-8"), ROOT, False, False) == []


def test_rejects_a_slice_id_outside_the_lattice():
    status = edited("`W6-T1`", "`W6-T1` and `W14-T1`")
    assert slice_id_conflicts(status, TASKS.read_text(encoding="utf-8")) == ["W14-T1 is not a TASKS.md slice"]


def test_rejects_an_owner_with_no_slice_in_the_portfolio():
    status = edited("| T1 — Chace |", "| T1 — Dhruv |")
    assert owner_conflicts(status, TASKS_FIXTURE) == ["T1 — Dhruv owns no T1 slice in TASKS.md"]


def test_rejects_a_tier_id_that_section_12_does_not_define():
    status = edited("`R15`", "`R99`")
    assert "`R99` is not a SPEC.md Section 12 tier" in tier_conflicts(status, SPEC.read_text(encoding="utf-8"))


def test_rejects_a_tier_above_the_headcount_ceiling():
    spec = SPEC.read_text(encoding="utf-8")
    above_r15 = edited("`R15`", "`F20`", edited("| 6 — five", "| 5 — four"))
    above_stop = edited("`R15`", "`L8-ONE`", edited("| 6 — five", "| 1 — no"))

    assert tier_conflicts(above_r15, spec) == [
        "tier `F20` is above the Section 12 ceiling `R15` for 5 active contributors"
    ]
    assert tier_conflicts(above_stop, spec) == [
        "tier `L8-ONE` is above the Section 12 ceiling `STOP` for 1 active contributors"
    ]
    assert tier_conflicts(edited("`R15`", "`M10`"), spec) == []
    assert tier_conflicts(edited("`R15`", "`ENGINEERING`", edited("| 6 — five", "| 1 — no")), spec) == []


def test_rejects_a_tier_above_the_gate_1_failure_cap():
    status = edited("`R15`", "`F20`")
    assert gate1_response_conflicts(status, SPEC.read_text(encoding="utf-8")) == [
        "tier `F20` is above `R15`, the Gate 1 failure cap, while Gate 1 is not passed"
    ]


def test_rejects_a_spec_version_ahead_of_spec_md():
    spec = SPEC_HEADER.sub("**Public project and experimental specification v1.10.0**", SPEC.read_text(encoding="utf-8"))
    ahead = edited("v1.3.0", "v1.11.0")

    assert spec_version_conflicts(ahead, spec) == ["STATUS.md cites SPEC.md v1.11.0, newer than v1.10.0"]
    assert spec_version_conflicts(edited("v1.3.0", "v1.9.0"), spec) == []


def test_rejects_a_protocol_or_official_trial_before_active_json():
    status = edited("| Not created; required by Gate 3 |", "| `final-2026-10` |")
    status = edited("| None represented as started |", "| 12 of 822 |", status)
    expected = [
        "'Current protocol or run ID' claims a protocol before protocol/active.json exists",
        "'Official empirical trials' claims a protocol before protocol/active.json exists",
    ]

    assert protocol_conflicts(status, protocol_exists=False) == expected
    assert protocol_conflicts(status, protocol_exists=True) == []
    assert protocol_conflicts(edited("Not created", "Not yet created"), protocol_exists=False) == []


def test_rejects_a_public_result_before_a_bundle():
    status = edited("| Public result or defense-effect claim | None |", "| Public result or defense-effect claim | 0.42 |")
    expected = ["'Public result or defense-effect claim' claims a result before results/public/ holds a bundle"]

    assert public_result_conflicts(status, has_bundle=False) == expected
    assert public_result_conflicts(status, has_bundle=True) == []


def test_rejects_a_pass_claim_while_a_gate_item_is_open():
    gate_1 = with_row(FIXTURE, "Gate 1 result", "Passed at `abc1234`")
    gate_5 = edited("| Gate 1 result |", "| Gate 5 result |", with_row(FIXTURE, "Gate 1 result", "Met"))
    gate_3 = edited("| Gate 1 result |", "| Gate 3 result |", with_row(FIXTURE, "Gate 1 result", "Passed"))

    assert gate_conflicts(gate_1, TASKS_FIXTURE) == [
        "Gate 1 is reported passed but TASKS.md leaves open: Lead's lock commit: the measurement contract is versioned."
    ]
    assert gate_conflicts(gate_5, TASKS_FIXTURE) == [
        "Gate 5 is reported passed but TASKS.md leaves open: `make report` and `make replay` work from a fresh clone."
    ]
    assert gate_conflicts(gate_3, TASKS_FIXTURE) == ["Gate 3 is reported passed but TASKS.md has no Gate 3 checklist"]


def test_reads_unmet_and_not_met_as_open_and_met_as_a_pass_claim():
    all_ticked = TASKS_FIXTURE.replace("- [ ]", "- [x]")

    assert gate_conflicts(with_row(FIXTURE, "Gate 1 result", "Not met; two items unmet"), TASKS_FIXTURE) == []
    assert gate_conflicts(with_row(FIXTURE, "Gate 1 result", "Met at the lock commit `abc1234`"), all_ticked) == []


def test_rejects_a_broken_link_and_an_anchor_with_no_heading():
    broken = edited("0007-gate1-corpus-rules-freeze.md", "0009-missing.md")
    bad_anchor = edited("#gate-1--end-of-week-5", "#gate-1-end-of-week-5")
    no_tasks_link = edited("[`TASKS.md`](TASKS.md)", "`TASKS.md`", edited("(TASKS.md#gate-1--end-of-week-5)", "(SPEC.md)"))

    assert link_conflicts(broken, ROOT) == ["link target docs/decisions/0009-missing.md does not exist"]
    assert link_conflicts(bad_anchor, ROOT) == ["link anchor TASKS.md#gate-1-end-of-week-5 matches no heading"]
    assert link_conflicts(no_tasks_link, ROOT) == ["STATUS.md does not link TASKS.md"]


def test_rejects_a_status_md_missing_a_row_the_checks_rely_on():
    status = edited("| Current protocol or run ID | Not created; required by Gate 3 |\n", "")
    assert protocol_conflicts(status, protocol_exists=False) == ["STATUS.md has no 'Current protocol or run ID' row"]
    assert tier_conflicts(edited("| Active/provisional tier |", "| Tier |"), SPEC.read_text(encoding="utf-8")) == [
        "STATUS.md has no 'Active/provisional tier' row"
    ]
    assert owner_conflicts(edited("| T1 — Chace |", "| Chace |"), TASKS_FIXTURE) == [
        "STATUS.md has no 'T<n> — <name>' owner rows"
    ]
    assert gate_conflicts(edited("| Gate 1 result |", "| Gate one |"), TASKS_FIXTURE) == [
        "STATUS.md has no 'Gate N result' row"
    ]
