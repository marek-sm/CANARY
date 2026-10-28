"""W7-T3: the Section 9 ninety-cell development grid orchestration.

Loads the committed schedule spec, validates trial count and identifiers, and
runs the W6-T3 executor with tool-result delivery (``runner.delivery``), so each
configuration runs its real defense path: D1_POLICY_GATE decides before every
dispatch and D2_DATAMARKING marks every tool result. ``verify`` checks that
behavior in the stored events, not just the configuration label. Mock runs use
the delivery mock; live runs refuse until paid runs open (the paid-run condition
and the paid-path tool sandbox, audit F-01).

Usage:
  python -m runner.grid_dev validate [--spec PATH]
  python -m runner.grid_dev mock [--out DIR] [--resume] [--spec PATH]
  python -m runner.grid_dev verify RUN [--spec PATH]
  python -m runner.grid_dev summary RUN [--spec PATH]
  python -m runner.grid_dev live [--out DIR] [--env-file PATH] [--provider anthropic|openai]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from analysis.floor_count import load_run
from defenses.interfaces import DATAMARK_MARKER
from runner import execute, paid_run
from runner.mock_provider import MOCK_MODEL_ID
from runner.mock_slice import EVENTS_FILE, RESULTS_FILE, REPO_ROOT, read_jsonl, validator
from runner.provider_config import load_api_key
from runner.schedule import ScheduledTrial, generate_schedule

DEFAULT_SPEC = REPO_ROOT / "protocol" / "development_grid_spec.json"
EXPECTED_TRIALS = 90
DEFAULT_MOCK_OUT = REPO_ROOT / "results" / "development" / "grid-mock"
DEFAULT_LIVE_OUT = REPO_ROOT / "results" / "development" / "grid-live"
MAX_PROVIDER_ATTEMPTS_PER_STEP = 3  # one initial + two retries (SPEC.md Section 9)


def load_spec(path: Path | None = None) -> dict[str, Any]:
    spec_path = path or DEFAULT_SPEC
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if not isinstance(spec, dict):
        raise ValueError(f"{spec_path}: spec must be a JSON object")
    return spec


def validate_grid_spec(spec: Mapping[str, Any]) -> list[ScheduledTrial]:
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


def live_run_refusal(corpus_root: Path, spec: Mapping[str, Any]) -> Optional[str]:
    """Fail closed before any paid call. The specific reasons come first so an
    operator sees what else is wrong; the path opens only when ``runner.paid_run``
    finds the project lead's record valid for this code and sandbox, and every
    trial checks that again before its first call."""
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
    return paid_run.paid_run_refusal()


def _adapter_with_pinned_decoding(adapter: Any, decoding: Mapping[str, Any]) -> Any:
    """execute.run_schedule passes mock decoding; live runs pin decision 0010 settings."""

    class _Provider:
        adapter_version = adapter.adapter_version

        def complete(
            self,
            messages: Any,
            tool_schemas: Any,
            _decoding: Mapping[str, Any],
            model_request: Mapping[str, Any],
        ) -> dict[str, Any]:
            return adapter.complete(messages, tool_schemas, decoding, model_request)

    return _Provider()


def build_live_provider_factory(adapter: Any, decoding: Mapping[str, Any]) -> Callable[..., Any]:
    provider = _adapter_with_pinned_decoding(adapter, decoding)

    def factory(_trial: ScheduledTrial, _canaries: list[str]) -> Any:
        return provider

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
    reason = live_run_refusal(root, spec)
    if reason:
        raise ValueError(reason)

    from runner import live_smoke

    provider_cfg = live_smoke.PROVIDERS[provider_name]
    resolved_model = model or spec.get("model_id") or provider_cfg["model"]
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
    factory = build_live_provider_factory(adapter, provider_cfg["decoding"])
    return execute.run_schedule(
        out_dir,
        schedule,
        corpus_root=root,
        resume=resume,
        spec=dict(spec),
        provider_factory=factory,
        delivery=True,
    )


def _spec_for_run_verification(run_dir: Path, spec: Mapping[str, Any]) -> dict[str, Any]:
    """Reconstruct schedule IDs using the model recorded on trials (not the spec file alone)."""
    sched_spec = dict(spec)
    for results_path in sorted(Path(run_dir).glob(f"*/{RESULTS_FILE}")):
        for line in results_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            meta = record.get("run_metadata") or {}
            # logical_trial_id uses the requested model; resolved may differ after adapter routing.
            model = meta.get("model_requested") or meta.get("model_resolved")
            if isinstance(model, str) and model:
                sched_spec["model_id"] = model
                return sched_spec
    # No results yet: only used to rebuild expected IDs; verify still fails on missing trials.
    sched_spec["model_id"] = MOCK_MODEL_ID
    return sched_spec


def verify_grid_run(run_dir: Path, spec: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed if the run is missing trials, duplicates ids, or replays tool facts."""
    schedule = validate_grid_spec(_spec_for_run_verification(run_dir, spec))
    expected = {t.logical_trial_id: t for t in schedule}
    found_ids: list[str] = []
    schema_errors: list[str] = []

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
            _check_no_repeated_dispatch(events)
            _check_no_repeated_effect(events)
            _check_no_repeated_sink(events)
            _check_defense_behavior(record, events)

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

    return {
        "experiment_id": spec["experiment_id"],
        "trials_expected": EXPECTED_TRIALS,
        "trials_found": len(found_ids),
        "complete": len(missing) == 0 and len(duplicates) == 0,
    }


def _check_defense_behavior(record: Mapping[str, Any], events: list[Mapping[str, Any]]) -> None:
    """Each configuration's label must match its defense path in the stored evidence.

    Every trial ran through tool-result delivery and its own audit: each event
    names the delivery version, and each tool record carries the audit's
    decision. Under D1_POLICY_GATE the events name the gate's version and the
    gate decided every dispatched call; no other configuration has either.
    Under D2_DATAMARKING the events name the transform's version and every tool
    result stores the hash of its unmarked observation; no other configuration
    has either, and no other configuration's tool result carries the datamark.
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
            },
        )
        totals["trials"] += 1
        totals["provider_requests"] += int(usage.get("provider_requests") or 0)
        totals["input_tokens"] += int(usage.get("input_tokens") or 0)
        totals["output_tokens"] += int(usage.get("output_tokens") or 0)
        ended = next((e for e in events if e["event_type"] == "trial_ended"), None)
        if ended:
            totals["steps_used"] += int(ended["payload"].get("steps_used") or 0)
    return {
        f"{channel}/{configuration}": values
        for (channel, configuration), values in sorted(buckets.items())
    }


def summarize_grid_run(run_dir: Path, spec: Mapping[str, Any]) -> dict[str, Any]:
    verify = verify_grid_run(run_dir, spec)
    trials = load_run(run_dir)
    return {
        **verify,
        "usage_by_channel_configuration": usage_by_channel_configuration(trials),
    }


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

    summary_parser = sub.add_parser("summary", help="verify and print usage aggregates")
    summary_parser.add_argument("run_dir", type=Path)
    summary_parser.add_argument("--spec", type=Path, default=None)

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
        help="defaults to the committed spec model_id or the provider's decision 0010 model",
    )

    args = parser.parse_args(argv)

    if args.command == "live":
        spec = load_spec(args.spec)
        out = args.out or DEFAULT_LIVE_OUT
        reason = live_run_refusal(execute.DEFAULT_CORPUS_ROOT, spec)
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
        report = summarize_grid_run(out, spec)
        print(json.dumps(report, indent=2, sort_keys=True))
        print(f"grid live run directory: {out}")
        return 0

    spec = load_spec(getattr(args, "spec", None))

    if args.command == "validate":
        validate_grid_spec(spec)
        print(f"ok: {EXPECTED_TRIALS} trials for experiment_id={spec['experiment_id']!r}")
        return 0

    if args.command == "mock":
        out = args.out or DEFAULT_MOCK_OUT
        run_mock_grid(
            out,
            spec=spec,
            resume=args.resume,
            corpus_root=args.corpus_root,
        )
        report = summarize_grid_run(out, spec)
        print(json.dumps(report, indent=2, sort_keys=True))
        print(f"grid mock run directory: {out}")
        return 0

    if args.command == "verify":
        print(json.dumps(verify_grid_run(args.run_dir, spec), indent=2, sort_keys=True))
        return 0

    print(json.dumps(summarize_grid_run(args.run_dir, spec), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
