"""W7-T1's predeclared, excluded clean task-coverage checks.

Uses the W6-T3 durable runner and real local task tools, not answer injection.
The native W6-T1 fixture is already the canonical adapter for these tasks; no
attack/clean overlay is appropriate (in particular, the ticket query has two
rows). A mock run earns no development credit and never counts as a smoke.

The project lead's live smokes (``--live``, decision 0023 item 8) run the same 15
cells on a real provider. They open only through ``runner.paid_run``'s gate, which
this path checks first and every cell checks again, and they write raw records
only where Git can't take them. ``--verify`` is the 15-cell check decision 0025
item 5 calls the matching check for the smokes: every result recomputes from its
events, and each cell's evidence holds. It makes no provider call.

Usage:
  python -m runner.coverage --build | --check
  python -m runner.coverage --out DIR [--resume]
  python -m runner.coverage --verify RUN
  python -m runner.coverage --live [--out DIR] [--resume] [--provider anthropic|openai] [--env-file PATH] [--model ID]
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import sys

from channels.render import INSERTION_MARKER
from runner import execute, grid_dev, paid_run
from runner.mock_provider import MOCK_MODEL_ID
from runner.mock_slice import EVENTS_FILE, RESULTS_FILE, read_jsonl
from runner.schedule import CONFIGURATIONS, generate_schedule
from tasks import registry

ROOT = registry.ROOT
CASES = ROOT / "corpus/task_coverage"
MANIFEST = ROOT / "tasks/coverage-smokes.json"
VERSION = "task-coverage-v0.1.0"
SUMMARY_VERSION = "coverage-summary-v0.2.0"
SUMMARY_FILE = "coverage-summary.json"
DEFAULT_LIVE_OUT = ROOT / "results/development/coverage-live"
MOCK_EXPERIMENT = "w7-t1-coverage-mock"
LIVE_EXPERIMENT = "w7-t1-coverage-live"
SEED = "w7-t1-coverage-v1"
EXPECTED_CELLS = 15
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


def schedule(experiment_id=MOCK_EXPERIMENT, seed=SEED, model=MOCK_MODEL_ID):
    build(check=True)
    result = []
    for case in manifest()["cases"]:
        spec = {"experiment_id": experiment_id, "model_id": model, "seed": seed,
                "base_case_ids": [case["base_case_id"]], "channels": [case["channel"]],
                "conditions": ["clean"], "configurations": list(CONFIGURATIONS), "repeats": 1}
        for trial in generate_schedule(spec):
            result.append(replace(trial, schedule_index=len(result)))
    return result


def _run_spec(provider, experiment_id, model):
    return {"coverage_manifest": manifest(), "provider": provider, "experiment_id": experiment_id,
            "seed": SEED, "model_id": model}


def _one_value(values, what):
    """The one value a whole run recorded; a run that recorded two is refused."""
    distinct = {json.dumps(v, sort_keys=True) for v in values}
    if len(distinct) != 1:
        raise ValueError(f"the run didn't record one {what}: {sorted(distinct)[:3]}")
    return json.loads(distinct.pop())


def verify(out):
    """Fail closed unless ``out`` holds exactly the 15 predeclared cells, each with no
    repeated tool fact, its real defense path, its pinned resource, and a result that
    recomputes from its events. Returns the summary; a mock run says it is one."""
    out = Path(out)
    spec = json.loads((out / execute.SPEC_FILE).read_text(encoding="utf-8"))
    if spec.get("coverage_manifest") != manifest():
        raise ValueError(f"{out.name} ran another manifest than this checkout predeclares; check it from the run's own commit")
    trials = schedule(spec["experiment_id"], spec["seed"], spec["model_id"])
    expected = {execute.trial_slug(trial) for trial in trials}
    found = {path.parent.name for path in out.glob(f"*/{RESULTS_FILE}")}
    directories = {path.name for path in out.iterdir() if path.is_dir()}
    missing, extra = sorted(expected - found), sorted(directories - expected)
    if missing or extra:
        raise ValueError(f"coverage verify failed: missing={missing[:3]}, extra={extra[:3]}")

    cells, pairs, sandboxes = [], [], []
    checked, statuses = Counter(), Counter()
    for trial in trials:
        directory = out / execute.trial_slug(trial)
        records = read_jsonl(directory / RESULTS_FILE, "result")
        if len(records) != 1:
            raise ValueError(f"{trial.logical_trial_id}: expected one result, found {len(records)}")
        result = records[0]
        events = read_jsonl(directory / EVENTS_FILE, "event")
        checked[trial.configuration] += grid_dev.check_trial_behavior(result, events)
        pairs.append((trial, result))
        statuses[result["status"]] += 1
        sandboxes.append(events[0]["component_versions"].get("tool_sandbox"))
        cells.append({"logical_trial_id": trial.logical_trial_id, "utility_pass": result["utility"]["pass"],
                      "result_sha256": hashlib.sha256((directory / RESULTS_FILE).read_bytes()).hexdigest(),
                      "events_sha256": hashlib.sha256((directory / EVENTS_FILE).read_bytes()).hexdigest()})
    execute.check_stored_run(out, pairs, corpus_root=CASES)

    lines = registry.jsonl_records((out / paid_run.PROVENANCE_FILE).read_text(encoding="utf-8"))
    # What the paid gate compares: hashed code, not commits, so a docs-only commit between a kill
    # and its resume runs the same code. It names the first invocation's commit, so no resume changes it.
    code = _one_value([{key: line.get(key) for key in ("code_digest", "dirty_paths")} for line in lines], "code version")
    mock = spec["provider"] == "mock_only"
    return {
        "version": VERSION, "summary_version": SUMMARY_VERSION, "provider": spec["provider"],
        "model_requested": spec["model_id"], "mock": mock,
        "development_credit": 0 if mock else len(cells), "excluded_from_estimates": True,
        "trials_expected": EXPECTED_CELLS, "trials_found": len(cells),
        "manifest_sha256": registry.digest(manifest()),
        "case_hashes": {case["base_case_id"]: case["case_sha256"] for case in manifest()["cases"]},
        "tool_sandbox": _one_value(sandboxes, "tool sandbox"),
        "code_provenance": {"code_commit": lines[0].get("code_commit"), **code},
        "delivered_resources_checked": {name: checked[name] for name in CONFIGURATIONS},
        "status_counts": dict(sorted(statuses.items())),
        "cells": cells, "passed": sum(c["utility_pass"] is True for c in cells),
    }


def _execute(out, spec, *, resume, provider_factory=None, decoding=execute.DECODING):
    trials = schedule(spec["experiment_id"], spec["seed"], spec["model_id"])
    execute.run_schedule(out, trials, corpus_root=CASES, delivery=True, resume=resume, spec=spec,
                         provider_factory=provider_factory, decoding=decoding)
    report = verify(out)
    summary = out / SUMMARY_FILE
    text = json.dumps(report, indent=2) + "\n"
    # A completed run's summary is evidence: a resume checks it and never rewrites it.
    if resume and summary.exists():
        if summary.read_text(encoding="utf-8") != text:
            raise ValueError(f"{SUMMARY_FILE} differs from what this run's evidence produces")
    else:
        execute._write_durably(summary, text)
    return report


def run(out, resume=False):
    report = _execute(out, _run_spec("mock_only", MOCK_EXPERIMENT, MOCK_MODEL_ID), resume=resume)
    if report["passed"] != EXPECTED_CELLS:
        raise ValueError(f"only {report['passed']}/{EXPECTED_CELLS} mock coverage cells passed")
    return report


def live_refusal():
    """Why a live smoke can't start here, or ``None``: the paid-run gate's own answer."""
    if os.environ.get("CANARY_PAID_RUN_ACK") != "1":
        return ("set CANARY_PAID_RUN_ACK=1 only after the project lead confirms the paid-run condition "
                "(TASKS.md) and writes the paid-run record")
    return paid_run.paid_run_refusal()


def run_live(out, env_file, provider_name="anthropic", model=None, resume=False):
    """The 15 smokes on a real provider. A wrong answer is data, not a failed run."""
    reason = live_refusal() or grid_dev.fallback_refusal(provider_name) or execute.raw_evidence_refusal(out)
    if reason:
        raise paid_run.PaidRunRefused(reason)

    from runner import live_smoke
    from runner.provider_config import load_api_key

    config = live_smoke.PROVIDERS[provider_name]
    if model is not None and model != config["model"]:
        # The ledger prices every trial at this provider's frozen rates, so another model
        # could spend past the cap while the ledger reads under it.
        raise paid_run.PaidRunRefused(f"coverage --live on {provider_name} runs only {config['model']}, not {model}")
    config["check"](config["decoding"])
    try:
        key = load_api_key(Path(env_file), config["key"])
    except (OSError, ValueError) as exc:
        raise ValueError(f"{env_file} must hold exactly one {config['key']}= line") from exc
    if not key:
        raise ValueError(f"{config['key']} in {env_file} is empty")
    adapter = config["adapter"](config["module"].build_client(key))
    del key
    paid_run.require_paid_run(adapter)  # the gate on this provider; execute_trial asks again for every cell
    spec = _run_spec(provider_name, LIVE_EXPERIMENT, model or config["model"])
    return _execute(out, spec, resume=resume, provider_factory=lambda trial, canaries: adapter,
                    decoding=config["decoding"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--verify", type=Path, metavar="RUN", help="check a run's 15 cells; makes no provider call")
    parser.add_argument("--live", action="store_true", help="run on a real provider (hand only; paid-run gate applies)")
    parser.add_argument("--provider", choices=("anthropic", "openai"), default="anthropic")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--model", default=None, help="the provider's decision 0010 model; any other refuses")
    args = parser.parse_args(argv)
    if args.build or args.check:
        build(check=args.check)
    if args.verify:
        try:
            print(json.dumps(verify(args.verify), indent=2))
        except grid_dev.REFUSALS as exc:
            print(f"coverage: {exc}", file=sys.stderr)
            return 1
    elif args.live:
        try:
            report = run_live(args.out or DEFAULT_LIVE_OUT, args.env_file, args.provider, args.model, args.resume)
        except grid_dev.REFUSALS as exc:  # PaidRunRefused is a ValueError
            print(f"refusing: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(report, indent=2))
    elif args.out:
        print(json.dumps(run(args.out, args.resume), indent=2))
    elif not (args.build or args.check):
        parser.error("choose --build, --check, --out, --verify, or --live")
    return 0


if __name__ == "__main__":
    sys.exit(main())
