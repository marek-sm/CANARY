"""Deterministic case selection (SPEC.md Section 5 steps 5-8; decision 0014).

    python -m corpus.select           # print P, the nested prefixes, tasks, and recheck samples
    python -m corpus.select --json    # same, as JSON

Reads only candidate metadata (IDs, goals, families, sources) from
`corpus/candidates.jsonl` and template IDs from `tasks/task_order.json`. It never
reads a trial, a result, or anything a model produced, so selection can't depend
on outcomes. It writes nothing: week 8 runs it at the selected tier and freezes
the output.

The rules, in order:

- Each primary goal's eligible (`evaluation`) candidates are ordered by ascending
  `SHA256("CANARY-2026|" + candidate_id)`, ties broken by `candidate_id`. A
  candidate's goal position is its 1-based place in that order.
- Bases alternate goals starting with `secret_disclosure`, so base i's goal is
  fixed and the search only picks a goal position for each base.
- The search returns the lexicographically earliest vector of goal positions
  whose prefixes meet every rule below, for the largest prefix size `P` in
  20/15/10/8/6 that has one. Every smaller prefix is the first part of the same
  vector, so a retained base never changes position or task after a downgrade.
- Minima per built prefix size: sources / families / legitimate high-risk-task
  bases of 3/4/8 at 20, 3/4/6 at 15, 3/3/4 at 10, 2/3/3 at 8, 2/2/3 at 6. The
  high-risk count follows from the task vector, so it always holds.
- Caps: at most 10 bases per source and 8 per family. If nothing is feasible,
  relax the family cap by one, then the source cap by one, then move to the next
  smaller size (step 7). Minima and goal balance are never relaxed.
- Base i gets task_order index `INDEX_VECTOR[i - 1]`.
- Recheck sample for a prefix of size N: the ceil(0.20 × N) retained cases with
  the lowest `SHA256("CANARY-2026-recheck|" + pool_hash + "|" + candidate_id)`,
  where `pool_hash` is the SHA-256 of every ledger `candidate_id`, sorted and
  newline-joined.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from corpus.intake import selection_hash

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "corpus" / "candidates.jsonl"
TASK_ORDER = ROOT / "tasks" / "task_order.json"

GOALS = ("secret_disclosure", "unauthorized_action")
SIZES = (20, 15, 10, 8, 6)
INDEX_VECTOR = (1, 2, 1, 2, 3, 4, 3, 5, 4, 6, 5, 6, 7, 8, 7, 8, 9, 10, 9, 10)
HIGH_RISK_INDICES = frozenset({1, 4, 7, 9})
# size: (sources, families, legitimate high-risk-task bases)
MINIMA = {20: (3, 4, 8), 15: (3, 4, 6), 10: (3, 3, 4), 8: (2, 3, 3), 6: (2, 2, 3)}
SOURCE_CAP, FAMILY_CAP = 10, 8
RECHECK_SALT = "CANARY-2026-recheck|"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def eligible(rows: Iterable[Mapping]) -> list[Mapping]:
    return [row for row in rows if row.get("status") == "evaluation"]


def goal_order(rows: Iterable[Mapping], goal: str) -> list[Mapping]:
    """A goal's eligible candidates in selection order (step 5)."""
    pool = [row for row in eligible(rows) if row["primary_goal"] == goal]
    return sorted(pool, key=lambda row: (selection_hash(row["candidate_id"]), row["candidate_id"]))


def selection_ranks(rows: Iterable[Mapping]) -> dict[str, int]:
    """`selection_rank`: 1-based rank inside each goal/family stratum (step 5)."""
    strata: dict[str, list[str]] = {}
    for row in eligible(rows):
        strata.setdefault(row["selection_stratum"], []).append(row["candidate_id"])
    ranks = {}
    for ids in strata.values():
        for rank, cid in enumerate(sorted(ids, key=lambda c: (selection_hash(c), c)), 1):
            ranks[cid] = rank
    return ranks


def slot_goal(slot: int) -> str:
    """Goal of the 1-based base position: disclosure first, then alternating."""
    return GOALS[(slot - 1) % 2]


def _source(row: Mapping) -> str:
    return row["source"]["citation_key"]


def _meets_minima(chosen: Sequence[Mapping], size: int) -> bool:
    sources, families, high_risk = MINIMA[size]
    have_high_risk = sum(INDEX_VECTOR[i] in HIGH_RISK_INDICES for i in range(size))
    return (
        len({_source(row) for row in chosen}) >= sources
        and len({row["attack_family_id"] for row in chosen}) >= families
        and have_high_risk >= high_risk
    )


def search(rows: Iterable[Mapping], size: int, family_cap: int = FAMILY_CAP, source_cap: int = SOURCE_CAP) -> list[int] | None:
    """Earliest feasible vector of `size` goal positions, or None."""
    orders = {goal: goal_order(rows, goal) for goal in GOALS}
    needed = {goal: sum(slot_goal(s) == goal for s in range(1, size + 1)) for goal in GOALS}
    if any(len(orders[goal]) < needed[goal] for goal in GOALS):
        return None
    checkpoints = {s for s in SIZES if s <= size}

    vector: list[int] = []
    chosen: list[Mapping] = []
    used = {goal: set() for goal in GOALS}
    sources: Counter = Counter()
    families: Counter = Counter()
    # Every rule depends only on a candidate's (source, family), so two
    # candidates of one goal with the same pair are interchangeable: if one
    # can't complete the vector at a slot, neither can the other, and a state
    # (slot, how many of each pair are used) that failed once fails again.
    # Skipping those keeps the search fast without changing which vector is
    # earliest.
    used_pairs: Counter = Counter()
    failed: set = set()

    def place(slot: int) -> bool:
        if slot > size:
            return True
        state = (slot, frozenset(used_pairs.items()))
        if state in failed:
            return False
        goal = slot_goal(slot)
        tried = set()
        for position, row in enumerate(orders[goal], 1):
            if position in used[goal]:
                continue
            source, family = _source(row), row["attack_family_id"]
            if (source, family) in tried:
                continue
            if sources[source] >= source_cap or families[family] >= family_cap:
                continue
            tried.add((source, family))
            pair = (goal, source, family)
            vector.append(position); chosen.append(row); used[goal].add(position)
            sources[source] += 1; families[family] += 1; used_pairs[pair] += 1
            if (slot not in checkpoints or _meets_minima(chosen, slot)) and place(slot + 1):
                return True
            vector.pop(); chosen.pop(); used[goal].discard(position)
            sources[source] -= 1; families[family] -= 1; used_pairs[pair] -= 1
            if not used_pairs[pair]:
                del used_pairs[pair]
        failed.add(state)
        return False

    return list(vector) if place(1) else None


def build(rows: Sequence[Mapping]) -> dict | None:
    """Largest feasible prefix size P with its vector, or None (step 8)."""
    for size in SIZES:
        for family_cap, source_cap, relaxation in (
            (FAMILY_CAP, SOURCE_CAP, "none"),
            (FAMILY_CAP + 1, SOURCE_CAP, "family cap +1"),
            (FAMILY_CAP + 1, SOURCE_CAP + 1, "family and source caps +1"),
        ):
            vector = search(rows, size, family_cap, source_cap)
            if vector is not None:
                return {"P": size, "vector": vector, "relaxation": relaxation}
    return None


def bases(rows: Sequence[Mapping], vector: Sequence[int], task_order: Mapping) -> list[dict]:
    """The ordered bases a vector names, with their tasks."""
    orders = {goal: goal_order(rows, goal) for goal in GOALS}
    templates = {entry["index"]: entry["template_id"] for entry in task_order["order"]}
    out = []
    for slot, position in enumerate(vector, 1):
        row = orders[slot_goal(slot)][position - 1]
        index = INDEX_VECTOR[slot - 1]
        out.append({
            "slot": slot,
            "candidate_id": row["candidate_id"],
            "primary_goal": row["primary_goal"],
            "goal_position": position,
            "attack_family_id": row["attack_family_id"],
            "source": _source(row),
            "task_index": index,
            "template_id": templates[index],
        })
    return out


def pool_hash(rows: Iterable[Mapping]) -> str:
    return sha256_text("\n".join(sorted(row["candidate_id"] for row in rows)))


def recheck_sample(retained_ids: Iterable[str], pool: str, size: int) -> list[str]:
    """The ceil(0.20 × size) retained cases with the lowest recheck hash."""
    count = math.ceil(0.20 * size)
    ranked = sorted(retained_ids, key=lambda cid: (sha256_text(RECHECK_SALT + pool + "|" + cid), cid))
    return ranked[:count]


def plan(rows: Sequence[Mapping], task_order: Mapping) -> dict:
    result = build(rows)
    out = {
        "pool_hash": pool_hash(rows),
        "eligible": {goal: len(goal_order(rows, goal)) for goal in GOALS},
        "P": None,
        "relaxation": None,
        "prefixes": {},
    }
    if result is None:
        return out
    ordered = bases(rows, result["vector"], task_order)
    out["P"], out["relaxation"] = result["P"], result["relaxation"]
    for size in (s for s in SIZES if s <= result["P"]):
        prefix = ordered[:size]
        out["prefixes"][str(size)] = {
            "bases": prefix,
            "recheck_sample": recheck_sample([b["candidate_id"] for b in prefix], out["pool_hash"], size),
        }
    return out


def load_rows(path: Path = LEDGER) -> list[dict]:
    # Only at newlines: str.splitlines also splits at U+2028, U+2029, and U+0085,
    # which a source's text can hold (LLMail-Inject submissions are free text).
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic case selection (SPEC.md Section 5 steps 5-8).")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = plan(load_rows(), json.loads(TASK_ORDER.read_text(encoding="utf-8")))
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print(f"pool_hash {result['pool_hash']}")
    print(f"eligible: {result['eligible']}")
    if result["P"] is None:
        print("no feasible prefix (SPEC.md Section 11 Gate 3 response applies)")
        return 0
    print(f"P = {result['P']} (relaxation: {result['relaxation']})")
    for size, prefix in result["prefixes"].items():
        print(f"\n{size}-base prefix, recheck sample {prefix['recheck_sample']}")
        for b in prefix["bases"]:
            print(f"  {b['slot']:>2} {b['candidate_id']} {b['primary_goal']:<19} {b['source']:<15} {b['attack_family_id']:<36} task {b['task_index']:>2} {b['template_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
