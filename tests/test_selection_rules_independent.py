"""Independent checks of the committed selection (review finding N-73-1, 2026-11-11).

`tests/test_selection.py` checks the script's rules on synthetic pools, but it reads
several constants back from `corpus.select` itself, so a wrong constant there passes.
These tests recompute parts of the committed plan from the rule text (SPEC.md Section 5
step 8 and decision 0014), with their own hashing and their own reading of the ledger
file: the pool hash, the recheck samples, the task index vector, the goal alternation
and salted goal order, and the nesting. They pin rules, not outputs, so a legitimate
change to the reviewed pool keeps them green. They don't check the feasibility search
itself (earliest vector, minima, caps, relaxation); `tests/test_selection.py` does that
on synthetic pools.
"""

import hashlib
import json
import math
import re
from pathlib import Path

import pytest

from corpus import select

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "corpus" / "candidates.jsonl"
SPEC = ROOT / "SPEC.md"
TASK_ORDER = ROOT / "tasks" / "task_order.json"

# Decision 0014 items 2 and 5, and SPEC.md Section 5 step 8, as written there.
GOAL_ORDER_SALT = "CANARY-2026|"
RECHECK_SALT = "CANARY-2026-recheck|"
FIRST_GOAL, SECOND_GOAL = "secret_disclosure", "unauthorized_action"


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ledger_rows():
    return [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").split("\n") if line.strip()]


def spec_index_vector():
    match = re.search(r"index vector `\[([0-9,\s]+)\]`", SPEC.read_text(encoding="utf-8"))
    assert match, "SPEC.md Section 5 step 8 no longer states the index vector"
    return [int(x) for x in match.group(1).split(",")]


@pytest.fixture(scope="module")
def committed_plan():
    plan = select.plan(select.load_rows(), json.loads(TASK_ORDER.read_text(encoding="utf-8")))
    if plan["P"] is None:
        pytest.skip("the reviewed pool supports no prefix; SPEC.md Section 11's Gate 3 response applies")
    return plan


def test_pool_hash_covers_every_ledger_record(committed_plan):
    ids = sorted(row["candidate_id"] for row in ledger_rows())
    assert committed_plan["pool_hash"] == sha("\n".join(ids))


def test_recheck_samples_follow_decision_0014(committed_plan):
    pool = sha("\n".join(sorted(row["candidate_id"] for row in ledger_rows())))
    for size, prefix in committed_plan["prefixes"].items():
        retained = [b["candidate_id"] for b in prefix["bases"]]
        ranked = sorted(retained, key=lambda cid: (sha(RECHECK_SALT + pool + "|" + cid), cid))
        assert prefix["recheck_sample"] == ranked[: math.ceil(0.20 * int(size))]


def test_tasks_follow_the_spec_index_vector(committed_plan):
    vector = spec_index_vector()
    templates = {e["index"]: e["template_id"] for e in json.loads(TASK_ORDER.read_text(encoding="utf-8"))["order"]}
    for prefix in committed_plan["prefixes"].values():
        for b in prefix["bases"]:
            assert b["task_index"] == vector[b["slot"] - 1]
            assert b["template_id"] == templates[b["task_index"]]


def test_slots_alternate_goals_and_take_the_salted_goal_order(committed_plan):
    eligible = [row for row in ledger_rows() if row.get("status") == "evaluation"]
    orders = {
        goal: sorted((r for r in eligible if r["primary_goal"] == goal), key=lambda r: (sha(GOAL_ORDER_SALT + r["candidate_id"]), r["candidate_id"]))
        for goal in (FIRST_GOAL, SECOND_GOAL)
    }
    for prefix in committed_plan["prefixes"].values():
        for b in prefix["bases"]:
            goal = FIRST_GOAL if b["slot"] % 2 == 1 else SECOND_GOAL
            assert b["primary_goal"] == goal
            assert orders[goal][b["goal_position"] - 1]["candidate_id"] == b["candidate_id"]


def test_smaller_prefixes_are_the_first_slots_of_the_largest(committed_plan):
    prefixes = committed_plan["prefixes"]
    largest = prefixes[str(committed_plan["P"])]["bases"]
    for size, prefix in prefixes.items():
        assert prefix["bases"] == largest[: int(size)]
