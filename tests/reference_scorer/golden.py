"""Run the reference authorization oracle on the repo's golden vector sets.

    uv run python -m tests.reference_scorer.golden oracles/authorization/golden/*.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .adapter import observed_action_hash
from .core import Grant, PriorCall, authorize, decisions_disagree, normalize_args


def run_vector(policies: dict, v: dict) -> dict:
    policy = policies[v["policy_id"]]
    req = v["request"]
    prior = [PriorCall(p["tool"], p["normalized_args"], p["dispatched"]) for p in v["prior_calls"]]
    grants = [Grant(g["grant_id"], g["policy_id"], g["policy_version"], g["action_hash"], g["consumed"])
              for g in v["grants"]]
    nargs = req["normalized_args"]
    res = authorize(policy, req["tool"], nargs, prior, grants, observed_action_hash)
    return {"evaluable": res.evaluable, "authorized": res.authorized, "reason_codes": res.reason_codes,
            "consumes_grant_ids": res.consumes_grant_ids, "renormalized_differs": normalize_args(req["tool"], nargs) != nargs}


def main(paths: list[str]) -> int:
    total = 0
    bad = []
    fx_total = 0
    fx_bad = []
    for p in paths:
        d = json.loads(Path(p).read_text())
        for v in d["vectors"]:
            total += 1
            got = run_vector(d["policies"], v)
            exp = v["expected"]
            diffs = {k: (got[k], exp[k]) for k in ("evaluable", "authorized", "consumes_grant_ids")
                     if got[k] != exp[k]}
            if sorted(got["reason_codes"]) != sorted(exp["reason_codes"]):
                diffs["reason_codes"] = (got["reason_codes"], sorted(exp["reason_codes"]))
            if got["renormalized_differs"]:
                diffs["normalization"] = "reference normalizer changes the vector's normalized_args"
            if diffs:
                bad.append((Path(p).name, v["vector_id"], v["description"], diffs))
        for f in d["differential_fixtures"]:
            fx_total += 1
            dis = decisions_disagree(f["gate"], f["audit"])
            got = None if dis is None else (not dis)
            if got != f["expected_match"]:
                fx_bad.append((Path(p).name, f["fixture_id"], got, f["expected_match"]))
    print(json.dumps({"vectors": total, "vector_disagreements": len(bad),
                      "differential_fixtures": fx_total, "fixture_disagreements": len(fx_bad)}))
    for b in bad:
        print("VECTOR", json.dumps(b))
    for b in fx_bad:
        print("FIXTURE", json.dumps(b))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
