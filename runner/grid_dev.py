"""W7-T3: the Section 9 ninety-cell development grid orchestration.

Loads the committed schedule spec, validates trial count and identifiers, and
runs the W6-T3 executor with tool-result delivery (``runner.delivery``), so each
configuration runs its real defense path: D1_POLICY_GATE decides before every
dispatch and D2_DATAMARKING marks every tool result. ``verify`` checks that
behavior in the stored events, not just the configuration label, hashes the
resource each cell actually delivered, and recomputes every stored result from
its events, refusing any difference. Mock runs use the delivery mock; live runs
refuse until paid runs open (the paid-run condition and the paid-path tool
sandbox, decision 0023), and write raw records only where Git can't take them.

Usage:
  python -m runner.grid_dev validate [--spec PATH]
  python -m runner.grid_dev mock [--out DIR] [--resume] [--spec PATH]
  python -m runner.grid_dev verify RUN [--spec PATH] [--corpus-root PATH]
  python -m runner.grid_dev summary RUN [--spec PATH] [--corpus-root PATH]
  python -m runner.grid_dev live [--out DIR] [--env-file PATH] [--provider anthropic|openai]
      (openai runs protocol/development_grid_spec_fallback.json unless --spec names another)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from jsonschema import ValidationError

from analysis.floor_count import load_run
from defenses.interfaces import DATAMARK_MARKER
from runner import delivery, execute, paid_run
from runner.mock_provider import MOCK_MODEL_ID
from runner.mock_slice import EVENTS_FILE, RESULTS_FILE, REPO_ROOT, read_jsonl, sha256_text, validator
from runner.provider_config import load_api_key
from runner.schedule import CONFIGURATIONS, ScheduledTrial, generate_schedule
from tasks import registry

DEFAULT_SPEC = REPO_ROOT / "protocol" / "development_grid_spec.json"
# The declared fallback's grid (decision 0010 item 3): the same spec on gpt-6-luna, so
# the one mock preflight the paid-run record checks covers both, and the record hashes both.
FALLBACK_SPEC = REPO_ROOT / "protocol" / "development_grid_spec_fallback.json"
PROVIDER_SPECS = {"anthropic": DEFAULT_SPEC, "openai": FALLBACK_SPEC}
EXPECTED_TRIALS = 90
DEFAULT_MOCK_OUT = REPO_ROOT / "results" / "development" / "grid-mock"
DEFAULT_LIVE_OUT = REPO_ROOT / "results" / "development" / "grid-live"
MAX_PROVIDER_ATTEMPTS_PER_STEP = 3  # one initial + two retries (SPEC.md Section 9)
# What a stored run that can't be checked raises, so a command prints a refusal, not a traceback.
REFUSALS = (OSError, ValueError, KeyError, StopIteration, ValidationError)


def load_spec(path: Path | None = None) -> dict[str, Any]:
    spec_path = path or DEFAULT_SPEC
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if not isinstance(spec, dict):
        raise ValueError(f"{spec_path}: spec must be a JSON object")
    return spec


def committed_spec(provider_name: str) -> dict[str, Any]:
    """The committed grid spec a live grid on ``provider_name`` runs."""
    return load_spec(PROVIDER_SPECS[provider_name])


def validate_grid_spec(spec: Mapping[str, Any]) -> list[ScheduledTrial]:
    validator("schedule_spec").validate(dict(spec))
    schedule = generate_schedule(spec)
    if len(schedule) != EXPECTED_TRIALS:
        raise ValueError(
            f"development grid must have {EXPECTED_TRIALS} logical trials; got {len(schedule)}"
        )
    ids = [t.logical_trial_id for t in schedule]
    if len(set(ids)) != len(ids):
        raise ValueError("development grid schedule minted duplicate logical_trial_id values")
    return schedule


def missing_bases(corpus_root: Path, spec: Mapping[str, Any]) -> list[str]:
    missing = []
    for base_id in spec["base_case_ids"]:
        if not (corpus_root / f"{base_id}.json").is_file():
            missing.append(base_id)
    return missing


def run_mock_grid(
    out_dir: Path,
    *,
    spec: Mapping[str, Any],
    resume: bool = False,
    corpus_root: Optional[Path] = None,
    provider_factory: Optional[Any] = None,
) -> Path:
    root = corpus_root or execute.DEFAULT_CORPUS_ROOT
    absent = missing_bases(root, spec)
    if absent:
        raise ValueError(
            f"corpus missing development bases {absent}; merge W6-T2 (#34) before running the full grid"
        )
    mock_spec = dict(spec)
    mock_spec["model_id"] = MOCK_MODEL_ID
    schedule = validate_grid_spec(mock_spec)
    return execute.run_schedule(
        out_dir,
        schedule,
        corpus_root=root,
        resume=resume,
        spec=mock_spec,
        provider_factory=provider_factory,
        delivery=True,
    )


def _provider_env_refusal() -> Optional[str]:
    """Same guard as runner.live_smoke.refusal without importing adapter modules."""
    if "CI" in os.environ:
        return "CI is set; paid calls never run in CI"
    ambient = sorted(name for name in os.environ if name.startswith(("ANTHROPIC_", "OPENAI_")))
    if ambient:
        return "unset ambient provider variables first: " + ", ".join(ambient)
    return None


def new_trials(out_dir: Optional[Path], spec: Mapping[str, Any]) -> int:
    """How many of the grid's trials ``out_dir`` hasn't started, for Section 9's ceiling."""
    schedule = validate_grid_spec(spec)
    if out_dir is None:
        return len(schedule)
    return sum(not (Path(out_dir) / execute.trial_slug(trial) / EVENTS_FILE).exists() for trial in schedule)


def live_run_refusal(corpus_root: Path, spec: Mapping[str, Any], out_dir: Optional[Path] = None, *,
                     provider_name: str = "anthropic") -> Optional[str]:
    """Fail closed before any paid call. The specific reasons come first so an
    operator sees what else is wrong; the path opens only when ``runner.paid_run``
    finds the project lead's record valid for this code and sandbox, and every
    trial checks that again before its first call, with the spend so far."""
    if os.environ.get("CANARY_PAID_RUN_ACK") != "1":
        return (
            "set CANARY_PAID_RUN_ACK=1 only after the project lead confirms "
            "tool-result delivery on main and request-to-effect ablation on main, and "
            "after a full mock 90-cell preflight (TASKS.md W7-T3)"
        )
    reason = _provider_env_refusal()
    if reason:
        return reason
    absent = missing_bases(corpus_root, spec)
    if absent:
        return (
            f"corpus/development missing development bases {absent}; "
            "merge W6-T2 (#34) before a live grid run"
        )
    if Path(corpus_root).resolve() != execute.DEFAULT_CORPUS_ROOT.resolve():
        return "a live grid runs only on corpus/development, the corpus its paid-run record hashed"
    committed = PROVIDER_SPECS[provider_name]
    if dict(spec) != load_spec(committed):
        return (f"a {provider_name} live grid runs only {committed.relative_to(REPO_ROOT)}, "
                "the spec its paid-run record hashed")
    return paid_run.paid_run_refusal(new_trials=new_trials(out_dir, spec))


def _existing_run_refusal(out: Path, resume: bool) -> Optional[str]:
    if resume or not out.exists():
        return None
    return f"{out} already holds a run: pass --out DIR for a new one, or --resume to continue this one"


def build_live_provider_factory(adapter: Any) -> Callable[..., Any]:
    def factory(_trial: ScheduledTrial, _canaries: list[str]) -> Any:
        return adapter

    return factory


def run_live_grid(
    out_dir: Path,
    *,
    spec: Mapping[str, Any],
    env_file: Path,
    provider_name: str = "anthropic",
    model: Optional[str] = None,
    resume: bool = False,
    corpus_root: Optional[Path] = None,
) -> Path:
    root = corpus_root or execute.DEFAULT_CORPUS_ROOT
    reason = live_run_refusal(root, spec, out_dir, provider_name=provider_name) or execute.raw_evidence_refusal(out_dir)
    if reason:
        raise ValueError(reason)

    from runner import live_smoke

    provider_cfg = live_smoke.PROVIDERS[provider_name]
    # Every trial sends the spec's model, so the provider, the spec, and --model must all name one.
    # The fallback runs its own committed spec (FALLBACK_SPEC); activating it is still a decision (decision 0010 item 3).
    expected = provider_cfg["model"]
    if spec.get("model_id") != expected or model not in (None, expected):
        raise ValueError(
            f"a {provider_name} grid runs only {expected}, but the spec names {spec.get('model_id')} and --model {model}"
        )
    provider_cfg["check"](provider_cfg["decoding"])

    try:
        key = load_api_key(env_file, provider_cfg["key"])
    except (OSError, ValueError) as exc:
        raise ValueError(
            f"{env_file} must hold exactly one {provider_cfg['key']}= line"
        ) from exc
    if not key:
        raise ValueError(f"{provider_cfg['key']} in {env_file} is empty")

    adapter = provider_cfg["adapter"](provider_cfg["module"].build_client(key))
    del key

    schedule = validate_grid_spec(spec)
    # Decision 0010's settings are sent with every request and recorded in every trial.
    return execute.run_schedule(
        out_dir,
        schedule,
        corpus_root=root,
        resume=resume,
        spec=dict(spec),
        provider_factory=build_live_provider_factory(adapter),
        delivery=True,
        decoding=provider_cfg["decoding"],
    )


def _spec_for_run_verification(run_dir: Path, spec: Mapping[str, Any]) -> dict[str, Any]:
    """Reconstruct schedule IDs using the model recorded on trials (not the spec file alone)."""
    sched_spec = dict(spec)
    for results_path in sorted(Path(run_dir).glob(f"*/{RESULTS_FILE}")):
        for record in registry.jsonl_records(results_path.read_text(encoding="utf-8")):
            meta = record.get("run_metadata") or {}
            # logical_trial_id uses the requested model; resolved may differ after adapter routing.
            model = meta.get("model_requested") or meta.get("model_resolved")
            if isinstance(model, str) and model:
                sched_spec["model_id"] = model
                return sched_spec
    # No results yet: only used to rebuild expected IDs; verify still fails on missing trials.
    sched_spec["model_id"] = MOCK_MODEL_ID
    return sched_spec


def verify_grid_run(run_dir: Path, spec: Mapping[str, Any], corpus_root: Optional[Path] = None) -> dict[str, Any]:
    """Fail closed if the run is missing trials, duplicates ids, replays tool facts,
    delivered anything but its pinned resource, or holds a result its events don't produce."""
    schedule = validate_grid_spec(_spec_for_run_verification(run_dir, spec))
    expected = {t.logical_trial_id: t for t in schedule}
    found_ids: list[str] = []
    schema_errors: list[str] = []
    checked: Counter[str] = Counter()

    for results_path in sorted(Path(run_dir).glob(f"*/{RESULTS_FILE}")):
        trial_dir = results_path.parent
        events_path = trial_dir / EVENTS_FILE
        for record in read_jsonl(results_path, "result"):
            try:
                validator("result").validate(record)
            except Exception as exc:
                schema_errors.append(f"{record.get('logical_trial_id')}: {exc}")
            found_ids.append(record["logical_trial_id"])
            events = read_jsonl(events_path, "event")
            for event in events:
                validator("event").validate(event)
            checked[record["configuration"]] += check_trial_behavior(record, events)

    counts = Counter(found_ids)
    duplicates = sorted(tid for tid, n in counts.items() if n > 1)
    missing = sorted(set(expected) - set(found_ids))
    extra = sorted(set(found_ids) - set(expected))
    if duplicates or missing or extra or schema_errors:
        raise ValueError(
            f"grid verify failed: duplicates={duplicates}, missing={len(missing)}, "
            f"extra={len(extra)}, schema_errors={schema_errors[:3]}"
        )

    retry_violations = []
    for results_path in Path(run_dir).glob(f"*/{RESULTS_FILE}"):
        for record in read_jsonl(results_path, "result"):
            for attempt in record.get("attempts") or []:
                # attempt_index 4+ exceeds one initial call plus two retries (SPEC.md Section 9).
                if attempt.get("attempt_index", 0) > MAX_PROVIDER_ATTEMPTS_PER_STEP:
                    retry_violations.append(record["logical_trial_id"])
    if retry_violations:
        raise ValueError(f"provider retries exceeded bound for {retry_violations[:5]}")

    # Last, so a record that fails a named check above says which one.
    execute.check_stored_run(run_dir, [
        (expected[record["logical_trial_id"]], record)
        for results_path in sorted(Path(run_dir).glob(f"*/{RESULTS_FILE}"))
        for record in read_jsonl(results_path, "result")
    ], corpus_root=corpus_root)

    return {
        "experiment_id": spec["experiment_id"],
        "trials_expected": EXPECTED_TRIALS,
        "trials_found": len(found_ids),
        "complete": len(missing) == 0 and len(duplicates) == 0,
        # How many cells' delivered resources were hashed; a cell that never retrieved its resource adds none.
        "delivered_resources_checked": {name: checked[name] for name in CONFIGURATIONS},
    }


def check_trial_behavior(record: Mapping[str, Any], events: list[Mapping[str, Any]]) -> int:
    """No repeated tool fact and the configuration's real defense path, in one trial's
    stored evidence; returns how many delivered resources it hashed."""
    _check_no_repeated_dispatch(events)
    _check_no_repeated_effect(events)
    _check_no_repeated_sink(events)
    return _check_defense_behavior(record, events)


def _check_defense_behavior(record: Mapping[str, Any], events: list[Mapping[str, Any]]) -> int:
    """Each configuration's label must match its defense path in the stored evidence.

    Every trial ran through tool-result delivery and its own audit: each event
    names the delivery version, and each tool record carries the audit's
    decision. Under D1_POLICY_GATE the events name the gate's version and the
    gate decided every dispatched call; no other configuration has either.
    Under D2_DATAMARKING the events name the transform's version and every tool
    result stores the hash of its unmarked observation; no other configuration
    has either, and no other configuration's tool result carries the datamark.
    Returns how many delivered resources ``_check_delivered_resource`` hashed.
    """
    trial_id = record.get("logical_trial_id")
    configuration = record.get("configuration")
    started = next((e for e in events if e["event_type"] == "trial_started"), None)
    versions = (started or {}).get("component_versions") or {}
    if started is None or "tool_result_delivery" not in versions:
        raise ValueError(f"{trial_id}: not run through tool-result delivery")
    for tool_event in record.get("tool_events") or []:
        decision = tool_event.get("audit_decision") or {}
        if not decision.get("evaluator_version"):
            raise ValueError(f"{trial_id}: tool call {tool_event.get('call_id')} has no audit decision")

    decided = {
        e["payload"].get("call_id") for e in events if e["event_type"] == "authorization_decision"
    }
    dispatched = {e["payload"].get("call_id") for e in events if e["event_type"] == "tool_dispatch"}
    if configuration == "D1_POLICY_GATE":
        if "d1_policy_gate" not in versions:
            raise ValueError(f"{trial_id}: D1_POLICY_GATE ran without the gate")
        if not dispatched <= decided:
            raise ValueError(f"{trial_id}: D1_POLICY_GATE dispatch without a gate decision")
    elif decided or "d1_policy_gate" in versions:
        raise ValueError(f"{trial_id}: {configuration} ran the D1_POLICY_GATE gate")

    results = [e["payload"] for e in events if e["event_type"] == "tool_result"]
    if configuration == "D2_DATAMARKING":
        if "d2_datamarking" not in versions:
            raise ValueError(f"{trial_id}: D2_DATAMARKING ran without the transform")
        if any(not r.get("unmarked_observation_sha256") for r in results):
            raise ValueError(f"{trial_id}: D2_DATAMARKING tool result was never marked")
    else:
        marked = any(
            "unmarked_observation_sha256" in r
            or DATAMARK_MARKER in json.dumps(r.get("observation"), ensure_ascii=False)
            for r in results
        )
        if "d2_datamarking" in versions or marked:
            raise ValueError(f"{trial_id}: {configuration} delivered datamarked content")
    return _check_delivered_resource(trial_id, configuration, started["payload"], events)


def _check_delivered_resource(
    trial_id: Any, configuration: Any, started: Mapping[str, Any], events: list[Mapping[str, Any]]
) -> int:
    """Hash what each call for the case resource actually returned, and compare it
    with what ``trial_started`` claims was delivered; that claim is computed before
    any call, so it says nothing by itself. The D2_DATAMARKING marker is required
    exactly when the transform changes the pinned render: strings with no whitespace
    (the native ticket rows) have nothing to mark. No D2_DATAMARKING result may carry
    the unmarked render, even from a call with other arguments. A cell that never
    retrieved its resource hashes nothing, and the caller's count shows it.
    """
    template_id = started.get("template_id")
    if not template_id:
        return 0
    rendered, delivered = started.get("rendered_sha256"), started.get("delivered_sha256")
    call = delivery.resource_call(template_id, started["channel"])
    requests = {e["payload"]["call_id"]: e["payload"] for e in events if e["event_type"] == "tool_requested"}
    checked = 0
    for event in events:
        if event["event_type"] != "tool_result":
            continue
        result = event["payload"]
        resources = {sha256_text(text): text for text in delivery.observed_resources(result.get("observation"))}
        if configuration == "D2_DATAMARKING" and rendered != delivered and rendered in resources:
            raise ValueError(f"{trial_id}: D2_DATAMARKING delivered the unmarked resource")
        request = requests.get(result.get("call_id"))
        if not resources or request is None or request["tool"] != call["tool"] or request["normalized_args"] != call["args"]:
            continue
        if delivered not in resources:
            raise ValueError(f"{trial_id}: {configuration} delivered something other than its pinned resource")
        if configuration == "D2_DATAMARKING" and rendered != delivered and DATAMARK_MARKER not in resources[delivered]:
            raise ValueError(f"{trial_id}: D2_DATAMARKING delivered its resource with no marker")
        checked += 1
    return checked


def gate_conformance_refusal(record: Mapping[str, Any]) -> Optional[str]:
    """Why a preflight record breaks SPEC.md Section 6, or ``None``. The paid-run record
    refuses on this; ``verify`` doesn't, because in a paid grid the same facts are
    evidence the conformance table counts and the repair rule acts on.

    D1_POLICY_GATE "never dispatches a request the independent audit evaluator
    rejects", and any gate/scorer disagreement invalidates the block. Under the
    mock, every task makes a request and every request reaches both evaluators, so
    a cell with no request, or an unknown match, shows the gate wasn't exercised.
    """
    if record.get("configuration") != "D1_POLICY_GATE":
        return None
    trial_id = record.get("logical_trial_id")
    tool_events = record.get("tool_events") or []
    if not tool_events:
        return f"{trial_id}: D1_POLICY_GATE recorded no tool request, so it decided nothing"
    for tool_event in tool_events:
        call_id = tool_event.get("call_id")
        if tool_event.get("authorized") is False and tool_event.get("dispatched") is True:
            return f"{trial_id}: D1_POLICY_GATE dispatched {call_id}, a request the audit rejected"
        if tool_event.get("gate_audit_match") is False:
            return f"{trial_id}: the gate and the audit disagreed on {call_id}"
        if tool_event.get("gate_audit_match") is not True:
            return f"{trial_id}: whether the gate and the audit agreed on {call_id} is unknown"
    return None


def _check_no_repeated_dispatch(events: list[Mapping[str, Any]]) -> None:
    """Each tool call_id may dispatch at most once (resume must replay, not re-dispatch)."""
    _check_no_repeated_positive_tool_fact(
        events, event_type="tool_dispatch", fact_key="dispatched"
    )


def _check_no_repeated_effect(events: list[Mapping[str, Any]]) -> None:
    """Each tool call_id may observe an effect at most once after resume."""
    _check_no_repeated_positive_tool_fact(
        events, event_type="effect_observation", fact_key="effect_observed"
    )


def _check_no_repeated_sink(events: list[Mapping[str, Any]]) -> None:
    """Each tool call_id may record sink receipt at most once after resume."""
    _check_no_repeated_positive_tool_fact(
        events, event_type="sink_receipt", fact_key="sink_received"
    )


def _check_no_repeated_positive_tool_fact(
    events: list[Mapping[str, Any]],
    *,
    event_type: str,
    fact_key: str,
) -> None:
    seen: set[str] = set()
    for event in events:
        if event["event_type"] != event_type:
            continue
        payload = event["payload"]
        if payload.get(fact_key) is not True:
            continue
        call_id = payload.get("call_id")
        if not isinstance(call_id, str) or not call_id:
            continue
        if call_id in seen:
            raise ValueError(f"repeated {event_type} for call_id {call_id}")
        seen.add(call_id)


def usage_by_channel_configuration(trials: list[tuple[Mapping[str, Any], Any]]) -> dict[str, Any]:
    """Aggregate provider usage from grid results (W7-T3 measurement)."""
    buckets: dict[tuple[str, str], dict[str, int]] = {}
    for record, events in trials:
        key = (record["channel"], record["configuration"])
        usage = record.get("usage") or {}
        totals = buckets.setdefault(
            key,
            {
                "trials": 0,
                "provider_requests": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "steps_used": 0,
                "usage_unknown_trials": 0,
            },
        )
        totals["trials"] += 1
        totals["provider_requests"] += int(usage.get("provider_requests") or 0)
        # A null total is unknown, not zero: count it apart so the sums aren't read as complete.
        if any(not isinstance(usage.get(k), int) for k in ("input_tokens", "output_tokens")):
            totals["usage_unknown_trials"] += 1
        totals["input_tokens"] += int(usage.get("input_tokens") or 0)
        totals["output_tokens"] += int(usage.get("output_tokens") or 0)
        ended = next((e for e in events if e["event_type"] == "trial_ended"), None)
        if ended:
            totals["steps_used"] += int(ended["payload"].get("steps_used") or 0)
    return {
        f"{channel}/{configuration}": values
        for (channel, configuration), values in sorted(buckets.items())
    }


def gate_audit_disagreements(trials: list[tuple[Mapping[str, Any], Any]]) -> dict[str, Any]:
    """D1_POLICY_GATE requests where the gate and the independent audit disagree, or
    the audit calls a dispatched request unauthorized. Null is unknown and counts as
    neither. The other configurations dispatch whatever the audit says, by design."""
    mismatched = unauthorized = 0
    affected = []
    for record, _ in trials:
        if record["configuration"] != "D1_POLICY_GATE":
            continue
        tool_events = record.get("tool_events") or []
        counts = (sum(e.get("gate_audit_match") is False for e in tool_events),
                  sum(e.get("authorized") is False and e.get("dispatched") is True for e in tool_events))
        mismatched, unauthorized = mismatched + counts[0], unauthorized + counts[1]
        if any(counts):
            affected.append(record["logical_trial_id"])
    return {"trials": len(affected), "gate_audit_mismatch": mismatched, "unauthorized_dispatched": unauthorized,
            "logical_trial_ids": sorted(affected)}


def summarize_grid_run(run_dir: Path, spec: Mapping[str, Any], corpus_root: Optional[Path] = None) -> dict[str, Any]:
    verify = verify_grid_run(run_dir, spec, corpus_root)
    trials = load_run(run_dir, corpus_root)
    return {
        **verify,
        "usage_by_channel_configuration": usage_by_channel_configuration(trials),
        "gate_audit_disagreements": gate_audit_disagreements(trials),
    }


def _print_report(build: Callable[[], Mapping[str, Any]]) -> int:
    try:
        report = build()
    except REFUSALS as exc:
        print(f"refusing: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate", help="check the committed spec generates 90 trials")
    validate_parser.add_argument("--spec", type=Path, default=None)

    mock_parser = sub.add_parser("mock", help="run the full grid on the mock provider (paid-run preflight)")
    mock_parser.add_argument("--out", type=Path, default=None)
    mock_parser.add_argument("--resume", action="store_true")
    mock_parser.add_argument("--spec", type=Path, default=None)
    mock_parser.add_argument(
        "--corpus-root",
        type=Path,
        default=None,
        help="development corpus directory (default corpus/development)",
    )

    verify_parser = sub.add_parser("verify", help="verify a completed grid run directory")
    verify_parser.add_argument("run_dir", type=Path)
    verify_parser.add_argument("--spec", type=Path, default=None)
    verify_parser.add_argument("--corpus-root", type=Path, default=None, help="the corpus a mock ran on, if not this checkout's corpus/development")

    summary_parser = sub.add_parser("summary", help="verify and print usage aggregates")
    summary_parser.add_argument("run_dir", type=Path)
    summary_parser.add_argument("--spec", type=Path, default=None)
    summary_parser.add_argument("--corpus-root", type=Path, default=None, help="the corpus a mock ran on, if not this checkout's corpus/development")

    live_parser = sub.add_parser(
        "live",
        help="run the full grid on a real provider (hand only; paid-run gate applies)",
    )
    live_parser.add_argument("--out", type=Path, default=None)
    live_parser.add_argument("--resume", action="store_true")
    live_parser.add_argument("--spec", type=Path, default=None)
    live_parser.add_argument(
        "--provider",
        choices=("anthropic", "openai"),
        default="anthropic",
    )
    live_parser.add_argument("--env-file", type=Path, default=REPO_ROOT / ".env")
    live_parser.add_argument(
        "--model",
        default=None,
        help="must be the committed spec's model_id and the provider's decision 0010 model",
    )

    args = parser.parse_args(argv)

    if args.command == "live":
        spec = load_spec(args.spec or PROVIDER_SPECS[args.provider])
        out = args.out or DEFAULT_LIVE_OUT
        reason = _existing_run_refusal(out, args.resume) or live_run_refusal(
            execute.DEFAULT_CORPUS_ROOT, spec, out, provider_name=args.provider)
        if reason:
            print(f"refusing: {reason}", file=sys.stderr)
            return 2
        try:
            run_live_grid(
                out,
                spec=spec,
                env_file=args.env_file,
                provider_name=args.provider,
                model=args.model,
                resume=args.resume,
            )
        except (OSError, ValueError) as exc:
            print(f"refusing: {exc}", file=sys.stderr)
            return 2
        code = _print_report(lambda: summarize_grid_run(out, spec))
        print(f"grid live run directory: {out}")
        return code

    spec = load_spec(getattr(args, "spec", None))

    if args.command == "validate":
        try:
            validate_grid_spec(spec)
        except REFUSALS as exc:
            print(f"refusing: {exc}", file=sys.stderr)
            return 1
        print(f"ok: {EXPECTED_TRIALS} trials for experiment_id={spec['experiment_id']!r}")
        return 0

    if args.command == "mock":
        out = args.out or DEFAULT_MOCK_OUT
        reason = _existing_run_refusal(out, args.resume)
        if reason:
            print(f"refusing: {reason}", file=sys.stderr)
            return 2
        run_mock_grid(
            out,
            spec=spec,
            resume=args.resume,
            corpus_root=args.corpus_root,
        )
        code = _print_report(lambda: summarize_grid_run(out, spec, args.corpus_root))
        print(f"grid mock run directory: {out}")
        return code

    if args.command == "verify":
        return _print_report(lambda: verify_grid_run(args.run_dir, spec, args.corpus_root))

    return _print_report(lambda: summarize_grid_run(args.run_dir, spec, args.corpus_root))


if __name__ == "__main__":
    raise SystemExit(main())
