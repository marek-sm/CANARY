"""End-to-end differential harness: scripted mock replies through the repo's real
delivery runner (agent loop, gate, sandboxed tools, fake sink, repo scorer), then
the reference scorer on the same durable trace.

Mock provider only. No network call, no credential. Tools run in the repo's
sandbox, so this must run as a non-root user (tools/sandbox.py refuses root).

    uv run --with hypothesis python -m tests.reference_scorer.e2e repro OUT_DIR
    uv run --with hypothesis python -m tests.reference_scorer.e2e fuzz OUT_DIR --examples 200
"""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Callable, Optional

from runner import execute, grid_dev
from runner.mock_provider import MOCK_MODEL_ID, MockProvider

from .compare import compare_dir

REPO = Path(__file__).resolve().parents[2]
GRID_SPEC = {
    "base_case_ids": ["dev-001", "dev-002", "dev-003", "dev-004", "dev-005"],
    "channels": ["C2", "C3", "C4"],
    "conditions": ["attack", "clean"],
    "configurations": ["D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING"],
    "experiment_id": "refscore-e2e",
    "model_id": MOCK_MODEL_ID,
    "repeats": 1,
    "seed": "refscore-e2e-seed",
}
# Each switch emulates one finding already reported (see the report's finding list).
ALL_COMPAT = frozenset({"F_zero_requests", "F_no_final", "F_cf_fields", "F_cf_reuse", "F_infra_actions",
                        "F_disp_nonD1", "F_label"})
# The runner prefixes "CANARY-" to each factory token (runner/execute.py), so the
# factory yields bare uuid4-style hex tokens and scripts use the full values.
CANARY_TOKENS = (uuid.UUID(int=0xA11CE).hex, uuid.UUID(int=0xB0B).hex)
CANARIES = tuple("CANARY-" + t for t in CANARY_TOKENS)


def schedule() -> list:
    return grid_dev.validate_grid_spec(GRID_SPEC)


def pick(base: str, channel: str, condition: str, configuration: str):
    for t in schedule():
        if (t.base_case_id, t.channel, t.condition, t.configuration) == (base, channel, condition, configuration):
            return t
    raise KeyError((base, channel, condition, configuration))


def response(raw: Optional[dict], outcome: str = "model_response", n: int = 0) -> dict:
    return {
        "outcome": outcome,
        "provider_request_id": f"script-req-{n}",
        "model_requested": MOCK_MODEL_ID,
        "model_resolved": MOCK_MODEL_ID,
        "provider_fingerprint": None,
        "raw_response": raw,
        "usage": {"input_tokens": None, "output_tokens": None},
    }


class ScriptedProvider(MockProvider):
    """Replays a fixed list of provider responses; after the script, answers text.
    A MockProvider subclass, so runner.paid_run treats it as mock (no paid path)."""

    def __init__(self, script: list[dict]):
        super().__init__([])
        self.script = [copy.deepcopy(s) for s in script]
        self.calls = 0

    def complete(self, messages, tool_schemas, decoding, model_request):
        self.calls += 1
        if self.script:
            r = self.script.pop(0)
            r = dict(r)
            r.setdefault("provider_request_id", f"script-req-{self.calls}")
            return r
        return response({"stop_reason": "end_turn", "content": [{"type": "text", "text": "{}"}]}, n=self.calls)


def run_cell(out_dir: Path, trial, script: list[dict]) -> Path:
    canary_iter = itertools.cycle(CANARY_TOKENS)
    execute.run_schedule(
        out_dir,
        [trial],
        provider_factory=lambda t, c: ScriptedProvider(script),
        canary_factory=lambda: next(canary_iter),
        delivery=True,
    )
    dirs = [p for p in out_dir.iterdir() if p.is_dir()]
    assert len(dirs) == 1, dirs
    used = json.loads((dirs[0] / "results.jsonl").read_text().splitlines()[-1])["canaries"]
    assert list(used) == list(CANARIES), used  # scripts must embed the trial's real canaries
    return dirs[0]


# ---------------------------------------------------------------------------
# Script building helpers
# ---------------------------------------------------------------------------


def tool(name: str, args: Any, cid: str, stop: str = "tool_use", text: Optional[str] = None) -> dict:
    content = []
    if text is not None:
        content.append({"type": "text", "text": text})
    content.append({"type": "tool_use", "id": cid, "name": name, "input": args})
    return response({"stop_reason": stop, "content": content})


def text(t: str, stop: str = "end_turn") -> dict:
    return response({"stop_reason": stop, "content": [{"type": "text", "text": t}]})


def no_content() -> dict:
    return response(None, outcome="no_model_content")


def http_content_filter() -> dict:
    return response(None, outcome="provider_content_filter")


def template_for(base: str) -> dict:
    corpus = json.loads((REPO / "corpus" / "development" / f"{base}.json").read_text())
    return json.loads((REPO / "tasks" / "templates" / f"{corpus['task']['template_id']}.json").read_text())


def summarize(row: dict) -> dict:
    return {"dir": Path(row["dir"]).name, "diffs": row["diffs"], "ref_security": row["ref_security"],
            "ref_utility": row.get("ref_utility")}


def run_and_compare(out_root: Path, name: str, trial, script: list[dict]) -> dict:
    d = run_cell(out_root / name, trial, script)
    row = compare_dir(d, derive_grants=True)
    row["diffs_repo_normalization"] = compare_dir(d, derive_grants=True, repo_normalization=True)["diffs"]
    row["diffs_residual"] = compare_dir(d, derive_grants=True, repo_normalization=True, compat=ALL_COMPAT)["diffs"]
    res = json.loads((d / "results.jsonl").read_text().splitlines()[-1])
    row["repo_security"] = res["security"]
    row["repo_utility"] = res["utility"]["pass"]
    row["termination_reason"] = res["termination_reason"]
    row["name"] = name
    return row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["repro", "fuzz"])
    ap.add_argument("out")
    ap.add_argument("--examples", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    if a.mode == "repro":
        from .e2e_repros import REPROS
        rows = []
        for name, (cell, script) in REPROS.items():
            rows.append(run_and_compare(out, name, pick(*cell), script(CANARIES)))
        (out / "repros.json").write_text(json.dumps(rows, indent=1, default=str))
        for r in rows:
            print(json.dumps({"name": r["name"], "termination": r["termination_reason"],
                              "diffs": [d for d in r["diffs"] if d[0] not in ("display_label",)
                                        and not (d[0] == "event.disposition_observed")]}, default=str)[:3000])
        return 0
    from .e2e_fuzz import fuzz
    return fuzz(out, a.examples, a.seed)


if __name__ == "__main__":
    sys.exit(main())
