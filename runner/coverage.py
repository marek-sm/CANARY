"""W7-T1's predeclared, excluded clean task-coverage checks.

Uses the W6-T3 durable runner and real local task tools, not answer injection.
The native W6-T1 fixture is already the canonical adapter for these tasks; no
attack/clean overlay is appropriate (in particular, the ticket query has two
rows). All provider execution here is mock-only and earns no development credit.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path

from channels.render import INSERTION_MARKER
from runner import execute
from runner.mock_provider import MOCK_MODEL_ID
from runner.mock_slice import EVENTS_FILE, RESULTS_FILE, read_jsonl
from runner.schedule import CONFIGURATIONS, generate_schedule
from tasks import registry

ROOT = registry.ROOT
CASES = ROOT / "corpus/task_coverage"
MANIFEST = ROOT / "tasks/coverage-smokes.json"
VERSION = "task-coverage-v0.1.0"
# Fixed before outcomes; complement of the development-base task assignment.
CANONICAL = {
    "invoice-receipt-email": "C3",
    "maintenance-confirm-email": "C3",
    "open-ticket-ids": "C2",
    "read-ticket-status": "C3",
    "service-hours-extract": "C4",
}


def digest_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def native_resource(template, channel):
    """Exact content retrieved by the canonical read; no expected-answer values."""
    call = template["variants"][channel]["required_calls"][0]
    args = call["args"]
    if channel == "C3":
        return (registry.FIXTURES / args["path"]).read_text(encoding="utf-8")
    if channel == "C4":
        routes = json.loads((registry.FIXTURES / "routes.json").read_text())
        pages = json.loads((registry.FIXTURES / "pages.json").read_text())
        return pages[routes[args["url"]]]
    from tools.query_db import QUERIES
    parameter, resource = QUERIES[args["query_id"]]
    rows = json.loads((registry.FIXTURES / "db-seed.json").read_text())
    matched = sorted((r for r in rows if r["resource"] == resource and r["lookup"] == args["params"][parameter]), key=lambda r: r["record_id"])
    return json.dumps([{"record_id": r["record_id"], "content": r["content"]} for r in matched], ensure_ascii=False)


def expected_case(template_id):
    template = registry.load(template_id)
    channel = CANONICAL[template_id]
    if template["canonical_adapter"] != channel:
        raise ValueError("canonical adapter changed; review predeclaration")
    rendered = native_resource(template, channel)
    fixture_template = rendered + INSERTION_MARKER
    base_id = "coverage-" + template_id
    record = {
        "schema_version": "1.0.0", "base_case_id": base_id,
        "split": "development", "fixture_mode": "native-task-coverage-v1",
        "task": {"template_id": template_id, "template_sha256": registry.digest(template)},
        "attack": {"canonical_payload": "", "attack_family_id": None},
        "fixture": {
            "template_path": f"fixtures/task_coverage/{base_id}.txt",
            "template_sha256": digest_text(fixture_template),
            "clean_replacement": "", "native_resource_sha256": digest_text(rendered),
            "source_fixture_hash": registry.verify(registry.FIXTURES),
        },
        "channels": [channel],
        "excluded_from_estimates": True,
    }
    return record, fixture_template


def verify_case(base, channel):
    template_id = base["task"]["template_id"]
    if template_id not in CANONICAL or channel != CANONICAL[template_id]:
        raise ValueError("not a predeclared canonical coverage cell")
    expected, _ = expected_case(template_id)
    if base != expected:
        raise ValueError("coverage case drift")
    return native_resource(registry.load(template_id), channel)


def manifest():
    development = {json.loads(p.read_text())["task"]["template_id"] for p in (ROOT / "corpus/development").glob("dev-*.json")}
    if set(registry.templates()) - development != set(CANONICAL):
        raise ValueError("coverage is not the five-template development complement")
    return {"version": VERSION, "scope": "development_only_clean_task_coverage", "excluded_from_estimates": True,
            "repeats": 1, "condition": "clean", "configurations": list(CONFIGURATIONS),
            "cases": [{"base_case_id": "coverage-" + t, "template_id": t, "channel": c,
                       "case_sha256": registry.digest(expected_case(t)[0])} for t, c in CANONICAL.items()]}


def build(check=False):
    outputs = {MANIFEST: json.dumps(manifest(), indent=2) + "\n"}
    for template_id in CANONICAL:
        record, fixture = expected_case(template_id)
        outputs[CASES / f"{record['base_case_id']}.json"] = json.dumps(record, indent=2) + "\n"
        outputs[ROOT / record["fixture"]["template_path"]] = fixture
    for path, text in outputs.items():
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                raise ValueError(f"coverage artifact drift: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")


def schedule(experiment_id="w7-t1-coverage-mock", seed="w7-t1-coverage-v1"):
    build(check=True)
    result = []
    for case in manifest()["cases"]:
        spec = {"experiment_id": experiment_id, "model_id": MOCK_MODEL_ID, "seed": seed,
                "base_case_ids": [case["base_case_id"]], "channels": [case["channel"]],
                "conditions": ["clean"], "configurations": list(CONFIGURATIONS), "repeats": 1}
        for trial in generate_schedule(spec):
            result.append(replace(trial, schedule_index=len(result)))
    return result


def run(out, resume=False):
    trials = schedule()
    execute.run_schedule(out, trials, corpus_root=CASES, delivery=True, resume=resume,
                         spec={"coverage_manifest": manifest(), "provider": "mock_only"})
    cells = []
    for trial in trials:
        directory = out / execute.trial_slug(trial)
        result, = read_jsonl(directory / RESULTS_FILE, "result")
        events = read_jsonl(directory / EVENTS_FILE, "event")
        base = json.loads((CASES / f"{trial.base_case_id}.json").read_text())
        audited = execute.delivery_audit(events=events, trial=trial, base=base, canaries=result["canaries"])
        recomputed = execute.assemble_result(trial, events, result["canaries"], None, tool_events=audited, base=base)
        if result != recomputed:
            raise ValueError("stored coverage result does not recompute")
        cells.append({"logical_trial_id": trial.logical_trial_id, "utility_pass": result["utility"]["pass"],
                      "result_sha256": digest_text((directory / RESULTS_FILE).read_text()),
                      "events_sha256": digest_text((directory / EVENTS_FILE).read_text())})
    report = {"version": VERSION, "provider": "mock_only", "development_credit": 0,
              "excluded_from_estimates": True, "cells": cells, "passed": sum(c["utility_pass"] is True for c in cells)}
    (out / "coverage-summary.json").write_text(json.dumps(report, indent=2) + "\n")
    if report["passed"] != 15:
        raise ValueError(f"only {report['passed']}/15 mock coverage cells passed")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.build or args.check:
        build(check=args.check)
    if args.out:
        print(json.dumps(run(args.out, args.resume), indent=2))
    if not (args.build or args.check or args.out):
        parser.error("choose --build, --check, or --out")


if __name__ == "__main__":
    main()
