"""The rest of review finding N-73-1 (2026-11-11): the search, minima, caps, and relaxation.

`tests/test_selection_rules_independent.py` pinned the pool hash, the recheck samples,
the task vector, and the goal order. These tests pin the feasibility search itself
(SPEC.md Section 5 steps 7 and 8, "Corpus composition", and decision 0014):

- the SPEC constants, written here as literals and not read back from `corpus.select`;
- hand-built pools where one rule binds, each with its expected vector written out;
- a reference search written from the rule text, with its own hashing, compared with
  `corpus.select` on seeded random pools, and a brute-force search with no memo or
  pruning compared with it on small pools;
- the committed plan's golden output: `pool_hash`, the 20 IDs, and the five recheck samples.

Every pool is synthetic except the golden test's, which reads the frozen ledger.
"""

import hashlib
import itertools
import json
import random
import re
from collections import Counter
from pathlib import Path

import pytest

from corpus import select

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "SPEC.md"
TASK_ORDER = ROOT / "tasks" / "task_order.json"

# SPEC.md Section 5 step 8 and "Corpus composition", as written there.
SIZES = (20, 15, 10, 8, 6)
# size: (sources, families, legitimate high-risk-task bases)
MINIMA = {20: (3, 4, 8), 15: (3, 4, 6), 10: (3, 3, 4), 8: (2, 3, 3), 6: (2, 2, 3)}
SOURCE_CAP, FAMILY_CAP = 10, 8
INDEX_VECTOR = (1, 2, 1, 2, 3, 4, 3, 5, 4, 6, 5, 6, 7, 8, 7, 8, 9, 10, 9, 10)
HIGH_RISK_INDICES = {1, 4, 7, 9}
# Step 7: the family cap, then the source cap; never the minima or goal balance.
RELAXATIONS = (
    (FAMILY_CAP, SOURCE_CAP, "none"),
    (FAMILY_CAP + 1, SOURCE_CAP, "family cap +1"),
    (FAMILY_CAP + 1, SOURCE_CAP + 1, "family and source caps +1"),
)
GOALS = ("secret_disclosure", "unauthorized_action")
GOAL_ORDER_SALT = "CANARY-2026|"


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- constants


def test_constants_match_the_spec_literals():
    assert tuple(select.SIZES) == SIZES
    assert select.MINIMA == MINIMA
    assert (select.SOURCE_CAP, select.FAMILY_CAP) == (SOURCE_CAP, FAMILY_CAP)
    assert tuple(select.INDEX_VECTOR) == INDEX_VECTOR
    assert set(select.HIGH_RISK_INDICES) == HIGH_RISK_INDICES


def test_spec_still_states_the_literals():
    text = SPEC.read_text(encoding="utf-8")
    assert "The prefix sizes are 20, 15, 10, 8, and 6 bases." in text
    assert "no source contributing more than ten cases and no attack family contributing more than eight" in text
    assert "at least three traceable primary sources" in text
    assert "at least four substantively different attack families" in text
    assert "the lower prefixes retain at least 3/3/2/2 sources, 4/3/3/2 families, and 6/4/3/3 legitimate high-risk-task bases" in text
    assert "contains eight legitimate high-risk-task bases" in text
    assert "relax the per-family cap by one, then the per-source cap by one; never relax source/family minima or goal balance" in text
    assert "the legitimate high-risk templates take indices 1, 4, 7, and 9" in text
    vector = re.search(r"index vector `\[([0-9,\s]+)\]`", text)
    assert vector and tuple(int(x) for x in vector.group(1).split(",")) == INDEX_VECTOR


# ---------------------------------------------------------------- reference search


def goal_orders(rows):
    eligible = [r for r in rows if r.get("status") == "evaluation"]
    return {
        goal: sorted((r for r in eligible if r["primary_goal"] == goal), key=lambda r: (sha(GOAL_ORDER_SALT + r["candidate_id"]), r["candidate_id"]))
        for goal in GOALS
    }


def reference_search(rows, size, family_cap, source_cap):
    """Lexicographically earliest vector of goal positions for `size` bases, or None.

    Slot s (1-based) takes goal GOALS[(s - 1) % 2]. Every prefix of a size in SIZES up to
    `size` meets that size's minima, and no source or family exceeds its cap. The rules
    see a case only through its (source, family), so at one slot only the earliest unused
    case of each (source, family) needs trying, and a failed state is remembered by
    (slot, counts of (goal, source, family) used): it fails again however it is reached."""
    orders = goal_orders(rows)
    checkpoints = {s for s in SIZES if s <= size}
    pairs = Counter()
    by_source, by_family = Counter(), Counter()
    used = {g: set() for g in GOALS}
    vector, failed = [], set()

    def ok_minima(n):
        sources, families, high_risk = MINIMA[n]
        return (
            len(+by_source) >= sources
            and len(+by_family) >= families
            and sum(INDEX_VECTOR[i] in HIGH_RISK_INDICES for i in range(n)) >= high_risk
        )

    def go(slot):
        if slot > size:
            return True
        state = (slot, frozenset((+pairs).items()))
        if state in failed:
            return False
        goal = GOALS[(slot - 1) % 2]
        seen = set()
        for position, r in enumerate(orders[goal], 1):
            src, fam = r["source"]["citation_key"], r["attack_family_id"]
            if position in used[goal] or (src, fam) in seen:
                continue
            seen.add((src, fam))
            if by_source[src] >= source_cap or by_family[fam] >= family_cap:
                continue
            used[goal].add(position); vector.append(position)
            pairs[(goal, src, fam)] += 1; by_source[src] += 1; by_family[fam] += 1
            if (slot not in checkpoints or ok_minima(slot)) and go(slot + 1):
                return True
            used[goal].discard(position); vector.pop()
            pairs[(goal, src, fam)] -= 1; by_source[src] -= 1; by_family[fam] -= 1
        failed.add(state)
        return False

    return list(vector) if go(1) else None


def reference_build(rows):
    for size in SIZES:
        for family_cap, source_cap, relaxation in RELAXATIONS:
            vector = reference_search(rows, size, family_cap, source_cap)
            if vector is not None:
                return {"P": size, "vector": vector, "relaxation": relaxation}
    return None


# ---------------------------------------------------------------- synthetic pools


def pool(disclosure, action, extra=()):
    """Rows whose goal order is exactly the given (family, source) lists.

    The IDs are sorted by the salted goal-order hash here, then given their attributes in
    that order, so position k in the list is goal position k."""
    rows = []
    for goal, spec in (("secret_disclosure", disclosure), ("unauthorized_action", action)):
        ids = sorted((sha(f"{goal}-{i}")[:20] for i in range(len(spec))), key=lambda c: (sha(GOAL_ORDER_SALT + c), c))
        for cid, (family, source) in zip(ids, spec):
            rows.append(
                {
                    "candidate_id": cid,
                    "primary_goal": goal,
                    "attack_family_id": family,
                    "source": {"citation_key": source},
                    "selection_stratum": f"{goal}/{family}",
                    "status": "evaluation",
                }
            )
    rows.extend(extra)
    return rows


FAMS = ["fam-a", "fam-b", "fam-c", "fam-d", "fam-e"]


def spread(n, sources, offset=0):
    """n (family, source) pairs cycling five families and the given sources."""
    return [(FAMS[(i + offset) % 5], sources[(i + offset) % len(sources)]) for i in range(n)]


def test_reference_finds_the_obvious_vector():
    rows = pool(spread(10, ["s1", "s2", "s3"]), spread(10, ["s1", "s2", "s3"], 2))
    assert reference_search(rows, 20, FAMILY_CAP, SOURCE_CAP) == [p for p in range(1, 11) for _ in GOALS]


def test_source_cap_binds_at_the_last_slot_that_can_change():
    # Disclosure positions 1-10 and action position 1 are all src-x, so the earliest
    # vector would hold 11 src-x bases. The cap of 10 moves slot 19 (the tenth
    # disclosure) to disclosure position 11, a src-y case.
    disclosure = [(FAMS[i % 5], "src-x") for i in range(10)] + [("fam-a", "src-y")]
    action = [("fam-b", "src-x")] + spread(10, ["src-y", "src-z"], 1)
    rows = pool(disclosure, action)
    expected = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 11, 10]
    assert reference_search(rows, 20, FAMILY_CAP, SOURCE_CAP) == expected
    assert select.search(rows, 20) == expected
    assert select.build(rows) == {"P": 20, "vector": expected, "relaxation": "none"}


def test_source_cap_relaxes_only_after_the_family_cap():
    # Exactly ten cases per goal, so all twenty are taken; eleven are src-x and no family
    # has more than eight. Step 7 tries the family cap first, which can't help, then
    # both caps. A missing third step would drop the tier to 15.
    disclosure = [(FAMS[i % 4], "src-x") for i in range(10)]
    action = [(FAMS[i % 4], "src-x" if i == 0 else ("src-y" if i % 2 else "src-z")) for i in range(10)]
    rows = pool(disclosure, action)
    assert reference_search(rows, 20, FAMILY_CAP + 1, SOURCE_CAP) is None
    expected = reference_search(rows, 20, FAMILY_CAP + 1, SOURCE_CAP + 1)
    assert expected is not None
    assert select.build(rows) == {"P": 20, "vector": expected, "relaxation": "family and source caps +1"}


def test_both_caps_relax_together_when_each_binds():
    # Eleven src-x and nine fam-a among exactly twenty cases: only the third step fits.
    disclosure = [("fam-a", "src-x")] * 9 + [("fam-b", "src-x")]
    action = [("fam-c", "src-x")] + [(FAMS[1 + i % 4], "src-y" if i % 2 else "src-z") for i in range(9)]
    rows = pool(disclosure, action)
    assert reference_search(rows, 20, FAMILY_CAP + 1, SOURCE_CAP) is None
    assert reference_search(rows, 20, FAMILY_CAP, SOURCE_CAP + 1) is None
    result = select.build(rows)
    assert result == {"P": 20, "vector": reference_search(rows, 20, FAMILY_CAP + 1, SOURCE_CAP + 1), "relaxation": "family and source caps +1"}


def test_the_family_cap_relaxes_by_exactly_one():
    # Disclosure positions 1-10 are fam-a and position 11 isn't; ten disclosure bases must
    # take nine fam-a cases at least, so the cap of 8 is infeasible. The cap of 9 takes
    # positions 1-9 and then 11. A cap of 10 would take position 10 at slot 19.
    srcs = ["s1", "s2", "s3"]
    disclosure = [("fam-a", srcs[i % 3]) for i in range(10)] + [("fam-b", "s1")]
    action = [(FAMS[1 + i % 4], srcs[(i % 4) % 3]) for i in range(10)]
    rows = pool(disclosure, action)
    assert select.search(rows, 20) is None
    expected = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 11, 10]
    assert select.build(rows) == {"P": 20, "vector": expected, "relaxation": "family cap +1"}


def test_the_source_cap_relaxes_by_exactly_one():
    # Disclosure positions 1-10 and action positions 1-2 are src-x, and there are exactly
    # ten action cases, so twenty bases hold eleven src-x cases at least: the cap of 10 is
    # infeasible, and relaxing the family cap alone can't help. The cap of 11 takes
    # disclosure positions 1-9 and then 11. A cap of 12 would take position 10 at slot 19.
    disclosure = [(FAMS[i % 2], "src-x") for i in range(10)] + [("fam-a", "src-y")]
    action = [("fam-c", "src-x")] * 2 + [(("fam-c", "src-y") if i % 2 else ("fam-d", "src-z")) for i in range(8)]
    rows = pool(disclosure, action)
    assert select.search(rows, 20) is None
    assert select.search(rows, 20, FAMILY_CAP + 1, SOURCE_CAP) is None
    expected = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 11, 10]
    assert select.build(rows) == {"P": 20, "vector": expected, "relaxation": "family and source caps +1"}


def test_family_cap_binds_at_twenty():
    # Disclosure positions 1-9 are fam-a and no action case is, so the earliest vector
    # holds nine fam-a bases. The cap of 8 moves slot 17 (the ninth disclosure) to
    # position 10, and slot 19 to position 11.
    srcs = ["s1", "s2", "s3"]
    disclosure = [("fam-a", srcs[i % 3]) for i in range(9)] + [(FAMS[1 + i], srcs[i]) for i in range(3)]
    action = [(FAMS[1 + i % 4], srcs[(i + 1) % 3]) for i in range(11)]
    rows = pool(disclosure, action)
    expected = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 10, 9, 11, 10]
    assert reference_search(rows, 20, FAMILY_CAP, SOURCE_CAP) == expected
    assert select.search(rows, 20) == expected
    assert select.build(rows) == {"P": 20, "vector": expected, "relaxation": "none"}


def test_minima_bind_at_a_smaller_prefix_but_not_at_the_final_size():
    # The first three cases of each goal share src-x, so the earliest 10-base vector
    # holds one source in its first six bases. The 6-base minimum of two sources must
    # move slot 6; checking minima only at 10 would not.
    disclosure = [(FAMS[i], "src-x") for i in range(3)] + [("fam-d", "src-y"), ("fam-e", "src-z"), ("fam-a", "src-y")]
    action = [(FAMS[i + 1], "src-x") for i in range(3)] + [("fam-a", "src-y"), ("fam-b", "src-z"), ("fam-c", "src-z")]
    rows = pool(disclosure, action)
    earliest = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]
    expected = reference_search(rows, 10, FAMILY_CAP, SOURCE_CAP)
    assert expected is not None and expected != earliest and expected[:5] == earliest[:5]
    assert select.search(rows, 10) == expected
    assert select.build(rows) == {"P": 10, "vector": expected, "relaxation": "none"}


def test_fifteen_base_minima_need_four_families():
    # Eight disclosure and seven action cases fill 15 bases from fam-a/b/c only; the one
    # fam-d case is the ninth disclosure. The 15-base minimum of four families moves
    # slot 15 to it, which a 3-family minimum would not.
    srcs = ["s1", "s2", "s3"]
    disclosure = [(FAMS[i % 3], srcs[i % 3]) for i in range(8)] + [("fam-d", "s1")]
    action = [(FAMS[(i + 1) % 3], srcs[(i + 1) % 3]) for i in range(8)]
    rows = pool(disclosure, action)
    expected = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 9]
    assert reference_search(rows, 15, FAMILY_CAP, SOURCE_CAP) == expected
    assert select.search(rows, 15) == expected
    assert select.build(rows) == {"P": 15, "vector": expected, "relaxation": "none"}


def test_a_same_family_case_from_another_source_is_tried():
    # Slot 5 first tries disclosure position 3 (src-x, fam-a), and the 6-base source
    # minimum then fails. Position 4 has the same family but src-y and succeeds; a search
    # that skipped it as "already tried" by family alone would take position 5 instead.
    disclosure = [("fam-a", "src-x"), ("fam-a", "src-x"), ("fam-a", "src-x"), ("fam-a", "src-y"), ("fam-c", "src-z")]
    action = [("fam-b", "src-x")] * 3
    rows = pool(disclosure, action)
    assert reference_search(rows, 6, FAMILY_CAP, SOURCE_CAP) == [1, 1, 2, 2, 4, 3]
    assert select.search(rows, 6) == [1, 1, 2, 2, 4, 3]


def random_pool(rng):
    n_sources, n_families = rng.randint(2, 4), rng.randint(2, 5)
    per_goal = [rng.randint(3, 9), rng.randint(3, 9)]
    skew = rng.random()
    specs = []
    for n in per_goal:
        spec = []
        for _ in range(n):
            # A skewed pick makes caps and minima bind often.
            s = 0 if rng.random() < skew else rng.randrange(n_sources)
            f = 0 if rng.random() < skew else rng.randrange(n_families)
            spec.append((f"fam-{f}", f"src-{s}"))
        specs.append(spec)
    return pool(*specs)


@pytest.mark.parametrize("seed", range(150))
def test_search_and_build_match_the_reference_on_random_pools(seed):
    rows = random_pool(random.Random(f"N-73-1|{seed}"))
    expected = reference_build(rows)
    assert select.build(rows) == expected
    for size in SIZES:
        assert select.search(rows, size) == reference_search(rows, size, FAMILY_CAP, SOURCE_CAP)


def test_random_pools_exercise_minima_and_pruning():
    # The seeded pools reach infeasible pools, vectors the minima move off the earliest
    # positions, and P of 6, 8, and 10. They don't reach the caps, a relaxation, or P of 15
    # or 20; the hand-built pools above cover those.
    outcomes = Counter()
    for seed in range(150):
        result = reference_build(random_pool(random.Random(f"N-73-1|{seed}")))
        outcomes["none" if result is None else (result["P"], result["relaxation"])] += 1
        if result is not None and result["vector"] != [p for p in range(1, result["P"] // 2 + 1) for _ in GOALS][: result["P"]]:
            outcomes["moved"] += 1
    assert outcomes["none"] > 0 and outcomes["moved"] > 0
    assert {p for p, _ in (k for k in outcomes if isinstance(k, tuple))} >= {6, 8, 10}


def brute_force_build(rows):
    """Every vector of goal positions for sizes 8 and 6, checked in full and the earliest
    kept: no memo and no pruning. At 8 bases or fewer no cap of 8 or 10 can bind, so step
    7 never applies, and pools of at most four cases per goal can't reach 10 bases."""
    orders = goal_orders(rows)
    for size in (8, 6):
        if size > 2 * min(len(orders[g]) for g in GOALS):
            continue
        feasible = []
        for d in itertools.permutations(range(1, len(orders[GOALS[0]]) + 1), (size + 1) // 2):
            for a in itertools.permutations(range(1, len(orders[GOALS[1]]) + 1), size // 2):
                vector = [d[i // 2] if i % 2 == 0 else a[i // 2] for i in range(size)]
                cases = [orders[GOALS[i % 2]][v - 1] for i, v in enumerate(vector)]
                if all(
                    len({c["source"]["citation_key"] for c in cases[:n]}) >= MINIMA[n][0]
                    and len({c["attack_family_id"] for c in cases[:n]}) >= MINIMA[n][1]
                    and sum(INDEX_VECTOR[i] in HIGH_RISK_INDICES for i in range(n)) >= MINIMA[n][2]
                    for n in SIZES if n <= size
                ):
                    feasible.append(vector)
        if feasible:
            return {"P": size, "vector": min(feasible), "relaxation": "none"}
    return None


def small_pool(rng):
    n_sources, n_families = rng.randint(1, 3), rng.randint(1, 3)
    specs = []
    for _ in GOALS:
        specs.append([(f"fam-{rng.randrange(n_families)}", f"src-{rng.randrange(n_sources)}") for _ in range(rng.randint(3, 4))])
    return pool(*specs)


@pytest.mark.parametrize("seed", range(60))
def test_build_matches_a_brute_force_search_on_small_pools(seed):
    rows = small_pool(random.Random(f"N-73-1-brute|{seed}"))
    assert select.build(rows) == brute_force_build(rows)


def test_small_pools_reach_both_sizes_and_infeasibility():
    results = [brute_force_build(small_pool(random.Random(f"N-73-1-brute|{seed}"))) for seed in range(60)]
    assert {r["P"] if r else None for r in results} == {8, 6, None}
    assert any(r and r["vector"] != [p for p in range(1, 5) for _ in GOALS][: r["P"]] for r in results)


# ---------------------------------------------------------------- golden output


GOLDEN_POOL_HASH = "864b46148d9818e0c48fed522b87b1c617ced4dcc5f0054d5959881d71914425"
GOLDEN_TWENTY = [
    "bc655465bc25eb048b60", "f3f186623c7396291991", "774d6519566baf172f80", "a20b918a11893f3cef56",
    "cfbf4f5226eda12237d0", "901bdcccb51d43ff5c5c", "778feba741923895d500", "867c0b8458fe79937930",
    "167c570ef7b73d7ef880", "1778d9d96ceb6817cb3e", "0c82907952e10973022d", "19737f9aafd702c870b9",
    "88653772cbbd557c33f0", "b8e8603a04354f1388a5", "2b467a07bc6b378fddfd", "75bd34f68e606ee8415e",
    "eedb6d91a0f709796081", "af350c5444da5f1c36d3", "ef38e51846a50cf20ade", "5595c3897219864eb677",
]
GOLDEN_RECHECK = {
    "20": ["88653772cbbd557c33f0", "eedb6d91a0f709796081", "901bdcccb51d43ff5c5c", "2b467a07bc6b378fddfd"],
    "15": ["88653772cbbd557c33f0", "901bdcccb51d43ff5c5c", "2b467a07bc6b378fddfd"],
    "10": ["901bdcccb51d43ff5c5c", "778feba741923895d500"],
    "8": ["901bdcccb51d43ff5c5c", "778feba741923895d500"],
    "6": ["901bdcccb51d43ff5c5c", "774d6519566baf172f80"],
}


def test_committed_plan_matches_the_frozen_golden_output():
    # W8-T2 froze the pool (corpus/freeze.json), so the committed plan is now fixed. A
    # change here is a change to a frozen selection and needs SPEC.md Section 11.
    rows = select.load_rows()
    plan = select.plan(rows, json.loads(TASK_ORDER.read_text(encoding="utf-8")))
    assert plan["pool_hash"] == GOLDEN_POOL_HASH
    assert (plan["P"], plan["relaxation"]) == (20, "none")
    assert [b["candidate_id"] for b in plan["prefixes"]["20"]["bases"]] == GOLDEN_TWENTY
    assert {size: p["recheck_sample"] for size, p in plan["prefixes"].items()} == GOLDEN_RECHECK
    assert select.build(rows) == reference_build(rows)
