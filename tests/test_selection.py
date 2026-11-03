"""W7-T2 selection script (SPEC.md Section 5 steps 5-8; decision 0014).

Everything here runs on synthetic candidate IDs and synthetic template IDs, so
the tests pin the rules without depending on which candidates are in the pool.
"""

import hashlib
import json
from pathlib import Path

from corpus import select
from corpus.intake import selection_hash

ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_ORDER = {"order": [{"index": i, "template_id": f"synthetic-task-{i:02d}"} for i in range(1, 11)]}
FAMILIES = ["fam-a", "fam-b", "fam-c", "fam-d"]
SOURCES = ["src-x", "src-y", "src-z"]


def cid(seed):
    return hashlib.sha256(seed.encode()).hexdigest()[:20]


def row(seed, goal, family="fam-a", source="src-x", status="evaluation"):
    return {
        "candidate_id": cid(seed),
        "primary_goal": goal,
        "attack_family_id": family,
        "source": {"citation_key": source},
        "selection_stratum": f"{goal}/{family}",
        "status": status,
    }


def diverse_pool(per_goal=7):
    rows = []
    for goal in select.GOALS:
        for i in range(per_goal):
            rows.append(row(f"{goal}-{i}", goal, FAMILIES[i % 4], SOURCES[i % 3]))
    return rows


def test_goal_order_is_by_salted_hash_then_id():
    rows = diverse_pool()
    for goal in select.GOALS:
        order = [r["candidate_id"] for r in select.goal_order(rows, goal)]
        assert order == sorted(order, key=lambda c: (selection_hash(c), c))
        assert all(r["primary_goal"] == goal for r in select.goal_order(rows, goal))


def test_only_evaluation_rows_are_eligible():
    rows = diverse_pool() + [row("dropped", "secret_disclosure", status="duplicate"), row("dev", "secret_disclosure", status="development")]
    ids = {r["candidate_id"] for r in select.goal_order(rows, "secret_disclosure")}
    assert cid("dropped") not in ids and cid("dev") not in ids


def test_selection_rank_is_per_stratum():
    rows = diverse_pool()
    ranks = select.selection_ranks(rows)
    for stratum in {r["selection_stratum"] for r in rows}:
        members = sorted((r["candidate_id"] for r in rows if r["selection_stratum"] == stratum), key=lambda c: (selection_hash(c), c))
        assert [ranks[c] for c in members] == list(range(1, len(members) + 1))


def test_bases_alternate_goals_starting_with_disclosure():
    assert [select.slot_goal(s) for s in range(1, 5)] == ["secret_disclosure", "unauthorized_action"] * 2


def test_unconstrained_search_takes_the_earliest_positions():
    # Every candidate has its own source and family, so no rule binds and the
    # earliest vector is simply 1, 1, 2, 2, 3, 3.
    rows = [row(f"{goal}-{i}", goal, f"fam-{goal[0]}{i}", f"src-{goal[0]}{i}") for goal in select.GOALS for i in range(4)]
    assert select.search(rows, 6) == [1, 1, 2, 2, 3, 3]


def test_minima_force_the_search_past_early_positions():
    # All action candidates and the first two disclosure candidates in goal
    # order share one source and family. The 6-base prefix needs 2 sources and
    # 2 families, so the search has to reach the third disclosure candidate.
    actions = [row(f"a-{i}", "unauthorized_action") for i in range(3)]
    plain = [row(f"s-{i}", "secret_disclosure") for i in range(3)]
    last = select.goal_order(plain, "secret_disclosure")[-1]["candidate_id"]
    disclosures = [
        dict(r, attack_family_id="fam-b", source={"citation_key": "src-y"}) if r["candidate_id"] == last else r
        for r in plain
    ]
    assert select.search(actions + disclosures, 6) == [1, 1, 2, 2, 3, 3]
    assert select.search(actions + plain, 6) is None


def test_fourteen_candidates_reach_ten_not_fifteen():
    plan = select.plan(diverse_pool(7), SYNTHETIC_ORDER)
    assert plan["P"] == 10
    assert set(plan["prefixes"]) == {"10", "8", "6"}


def test_smaller_prefixes_nest_inside_the_largest():
    plan = select.plan(diverse_pool(8), SYNTHETIC_ORDER)
    largest = [b["candidate_id"] for b in plan["prefixes"][str(plan["P"])]["bases"]]
    for size, prefix in plan["prefixes"].items():
        assert [b["candidate_id"] for b in prefix["bases"]] == largest[: int(size)]


def test_every_built_prefix_meets_its_minima():
    plan = select.plan(diverse_pool(8), SYNTHETIC_ORDER)
    for size, prefix in plan["prefixes"].items():
        need_sources, need_families, need_high_risk = select.MINIMA[int(size)]
        bases = prefix["bases"]
        assert len({b["source"] for b in bases}) >= need_sources
        assert len({b["attack_family_id"] for b in bases}) >= need_families
        assert sum(b["task_index"] in select.HIGH_RISK_INDICES for b in bases) >= need_high_risk
        goals = [b["primary_goal"] for b in bases]
        assert abs(goals.count("secret_disclosure") - goals.count("unauthorized_action")) <= 1


def test_tasks_follow_the_index_vector_and_task_order():
    plan = select.plan(diverse_pool(8), SYNTHETIC_ORDER)
    for b in plan["prefixes"]["10"]["bases"]:
        assert b["task_index"] == select.INDEX_VECTOR[b["slot"] - 1]
        assert b["template_id"] == f"synthetic-task-{b['task_index']:02d}"


def test_a_pool_without_three_sources_has_no_ten_base_prefix():
    rows = [dict(r, source={"citation_key": SOURCES[i % 2]}) for i, r in enumerate(diverse_pool(7))]
    plan = select.plan(rows, SYNTHETIC_ORDER)
    assert plan["P"] in (8, 6)


def test_too_small_a_pool_has_no_prefix():
    plan = select.plan(diverse_pool(2), SYNTHETIC_ORDER)
    assert plan["P"] is None and plan["prefixes"] == {}


def test_family_cap_relaxes_before_moving_to_a_smaller_size():
    # 16 candidates, 10 in fam-a. A 15-base prefix has to take at least 9 of
    # them, which the cap of 8 blocks, so step 7 relaxes the family cap by one
    # instead of dropping to 10.
    rows = []
    for goal in select.GOALS:
        for i in range(8):
            family = "fam-a" if i < 5 else FAMILIES[1 + i % 3]
            rows.append(row(f"{goal}-{i}", goal, family, SOURCES[i % 3]))
    assert select.search(rows, 15) is None
    result = select.build(rows)
    assert result is not None
    assert (result["P"], result["relaxation"]) == (15, "family cap +1")


def test_recheck_sample_size_and_determinism():
    plan = select.plan(diverse_pool(8), SYNTHETIC_ORDER)
    for size, prefix in plan["prefixes"].items():
        expected = {20: 4, 15: 3, 10: 2, 8: 2, 6: 2}[int(size)]
        assert len(prefix["recheck_sample"]) == expected
        assert set(prefix["recheck_sample"]) <= {b["candidate_id"] for b in prefix["bases"]}
    assert select.plan(diverse_pool(8), SYNTHETIC_ORDER) == plan


def test_recheck_sample_depends_on_the_whole_pool():
    rows = diverse_pool(8)
    retained = [r["candidate_id"] for r in rows[:10]]
    a = select.recheck_sample(retained, select.pool_hash(rows), 10)
    b = select.recheck_sample(retained, select.pool_hash(rows + [row("late", "secret_disclosure")]), 10)
    assert select.pool_hash(rows) != select.pool_hash(rows + [row("late", "secret_disclosure")])
    assert len(a) == len(b) == 2


def test_selection_reads_no_outcome_fields():
    # Adding outcome-looking fields to every row can't change the plan.
    rows = diverse_pool(8)
    noisy = [dict(r, attack_success=True, utility=False, result={"score": 1}) for r in rows]
    assert select.plan(noisy, SYNTHETIC_ORDER) == select.plan(rows, SYNTHETIC_ORDER)


def test_committed_ledger_ranks_match_the_rule():
    rows = select.load_rows()
    ranks = select.selection_ranks(rows)
    for r in rows:
        if r["status"] == "evaluation":
            assert r["selection_rank"] == ranks[r["candidate_id"]]


def test_committed_pool_meets_the_w7_t2_floor():
    # TASKS.md W7-T2: 14 candidates, at least 7 per goal, 3 sources, 3 families.
    rows = [r for r in select.load_rows() if r["status"] == "evaluation"]
    goals = [r["primary_goal"] for r in rows]
    assert len(rows) >= 14
    assert goals.count("secret_disclosure") >= 7 and goals.count("unauthorized_action") >= 7
    assert len({r["source"]["citation_key"] for r in rows}) >= 3
    assert len({r["attack_family_id"] for r in rows}) >= 3
    task_order = json.loads((ROOT / "tasks" / "task_order.json").read_text())
    assert select.plan(select.load_rows(), task_order)["P"] >= 10
