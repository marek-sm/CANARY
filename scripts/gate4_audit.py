"""Count-only Gate 4 audit of the sweep run, the C1 run, and their sanitized bundles (decision 0043 item 3,
which changes the lead scaffold of decision 0042 item 9).

It prints only ``<name>: pass|fail`` lines and two overall lines, and exits 0 or 1:

- the sweep's checks: ``verify_sweep``, ``sanitized_match``, ``missingness``, ``model_comparability``,
  ``attempt_histories``, ``identifiers``, ``resets``;
- one ``eligible_<comparison>`` line per headline comparison the report makes over this geometry,
  under the fixed names in ``HEADLINE``;
- ``overall_sweep: PASS|FAIL``, over the sweep's checks only;
- C1's checks, ``c1_verify``, ``c1_sanitized_match``, ``c1_model_comparability``,
  ``c1_attempt_histories``, ``c1_identifiers``, ``c1_resets``, or ``c1: fail`` without both C1
  arguments;
- ``overall_c1: PASS|FAIL``, over C1's checks only.

The exit code is 0 exactly when ``overall_sweep`` is PASS (decision 0043 item 2): a C1 failure
excludes C1 only, and an ``eligible_*`` failure sends that comparison to the supported-results
decision as ineligible without failing the sweep. It prints nothing else: no count, rate, cell,
identifier, or message, so the project lead sees only whether each integrity check passed and
which headline comparisons are complete enough to report (decision 0025 item 12). Any error
inside a check is a bare fail.

The project lead runs it outside any AI session, after recomputing this file's SHA-256 and
comparing it with the value named in the lead-side review file:

    shasum -a 256 scripts/gate4_audit.py
    python scripts/gate4_audit.py --raw SWEEP_RUN --sanitized SWEEP_BUNDLE \\
        --c1-raw C1_RUN --c1-sanitized C1_BUNDLE

What it imports from ``analysis/report.py`` (exactly decision 0043 item 3's list), and why none
computes a rate, estimate, interval, or difference:

- ``THRESHOLD``: the 5% constant.
- ``SECURITY``, ``UNIONS``, ``CONDITIONS``, ``BASELINE``, ``GATE``, ``MARKING``, ``ADAPTER_CONTRASTS``:
  endpoint, condition, configuration, and contrast names.
- ``Design``: the geometry dataclass.
- ``design_from``: reads the geometry from ``protocol/active.json`` and each base's template and
  family from its corpus file; it reads no record.
- ``endpoint``: one record's named endpoint, True/False/None; the audit only tests it for None.
- ``_index``: the primary records by logical cell; it refuses a duplicate or out-of-geometry cell and
  reads no outcome.
- ``_keys``, ``_key_of``: the component keys a macro-average averages over, from the geometry.
- ``_counts``: each base's multiplicity in the active base list.

``missingness`` checks only that the accounting is complete (decision 0043 item 2): the geometry is
non-empty, no record falls outside it, and every planned cell has exactly one primary record, whose
null endpoints are its recorded missingness. Each ``eligible_*`` line restates the report's rule for
the components a headline macro-average averages (``_rate_plan``, ``_defense_plan``, ``_did_plan``,
and ``_estimate``'s ``over_threshold``) with the outcome sums left out: more than 5% of a component's
planned keys incomplete, or any arm missing more than 5% of its scheduled values.
``tests/test_gate4_audit.py`` checks that it plans and decides exactly the comparisons the report's
own notes call headline-ineligible.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import logging
import sys
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis import sanitizer  # noqa: E402
from analysis.active_protocol import TIERS  # noqa: E402
# Decision 0043 item 3 fixes this list; SECURITY, UNIONS, and ADAPTER_CONTRASTS are no longer read,
# since the headline comparisons are named below, but the list stays as the decision states it.
from analysis.report import (  # noqa: E402,F401
    ADAPTER_CONTRASTS, BASELINE, CONDITIONS, GATE, MARKING, SECURITY, THRESHOLD, UNIONS,
    Design, _counts, _index, _key_of, _keys, design_from, endpoint,
)
from runner import c1_trial, execute, schedule, sweep  # noqa: E402

CHECKS = ("verify_sweep", "sanitized_match", "missingness", "model_comparability",
          "attempt_histories", "identifiers", "resets")
C1_CHECKS = ("c1_verify", "c1_sanitized_match", "c1_model_comparability", "c1_attempt_histories", "c1_identifiers",
             "c1_resets")
# The headline comparisons the report makes (its ``headline=True`` tables), in print order: the line's
# fixed name, the report's output ID, and the configuration of its per-configuration row, if any.
# Secondary comparisons (background rates, attack-condition task rates, injection excess risk, the
# adapter contrasts) are reported with their ranges and get no line (decision 0043 item 2).
HEADLINE = (
    ("eligible_model_violation_rate_baseline", "ModelViolationRate", BASELINE),
    ("eligible_model_violation_rate_policy_gate", "ModelViolationRate", GATE),
    ("eligible_model_violation_rate_datamarking", "ModelViolationRate", MARKING),
    ("eligible_system_compromise_rate_baseline", "SystemCompromiseRate", BASELINE),
    ("eligible_system_compromise_rate_policy_gate", "SystemCompromiseRate", GATE),
    ("eligible_system_compromise_rate_datamarking", "SystemCompromiseRate", MARKING),
    ("eligible_clean_utility_baseline", "CleanUtility", BASELINE),
    ("eligible_clean_utility_policy_gate", "CleanUtility", GATE),
    ("eligible_clean_utility_datamarking", "CleanUtility", MARKING),
    ("eligible_high_risk_clean_utility_baseline", "AuthorizedHighRiskCleanUtility", BASELINE),
    ("eligible_high_risk_clean_utility_policy_gate", "AuthorizedHighRiskCleanUtility", GATE),
    ("eligible_high_risk_clean_utility_datamarking", "AuthorizedHighRiskCleanUtility", MARKING),
    ("eligible_datamarking_attack_risk_difference", "DatamarkingAttackRiskDifference", None),
    ("eligible_datamarking_injection_specific_difference", "DatamarkingInjectionSpecificDifference", None),
    ("eligible_policy_gate_residual_system_risk_difference", "PolicyGateResidualSystemRiskDifference", None),
    ("eligible_clean_utility_cost_policy_gate", "CleanUtilityCost", GATE),
    ("eligible_clean_utility_cost_datamarking", "CleanUtilityCost", MARKING),
)
INFRASTRUCTURE_FAILURE = "infrastructure_failure"
MAX_ATTEMPTS = 3  # the first try and at most two retries (SPEC.md Section 9)


@dataclass
class Run:
    records: list[dict[str, Any]]
    events: dict[str, list[dict[str, Any]]]  # logical_trial_id -> events in file order
    active: dict[str, Any]
    design: Optional[Design]
    root: Optional[Path] = None
    stored_spec: dict[str, Any] = field(default_factory=dict)  # the run's own schedule_spec.json
    canary_map: dict[str, Any] = field(default_factory=dict)  # the run's canaries.json


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]


def _json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load(raw: Path, active: Path, corpus_root: Optional[Path] = None) -> Run:
    """A run's records and events; the geometry only for a sweep (``corpus_root`` given)."""
    raw = Path(raw)
    records: list[dict[str, Any]] = []
    events: dict[str, list[dict[str, Any]]] = {}
    for results in sorted(raw.glob("*/results.jsonl")):
        trial_records = _jsonl(results)
        records.extend(trial_records)
        for record in trial_records:
            events[record["logical_trial_id"]] = _jsonl(results.parent / "events.jsonl")
    active_json = _json(active)
    design = design_from(active_json, Path(corpus_root)) if corpus_root is not None else None
    return Run(records, events, active_json, design, raw, _json(raw / execute.SPEC_FILE),
               _json(raw / execute.CANARIES_FILE))


# --------------------------------------------------------------------------- completeness


def _ids(spec: dict[str, Any]) -> set[str]:
    return {trial.logical_trial_id for trial in schedule.generate_schedule(dict(spec))}


def check_verify_sweep(raw: Path, corpus_root: Path, active: dict[str, Any], committed: dict[str, Any]) -> bool:
    """Completeness, schema, schedule membership, duplicates, stored environment, rescoring, replay,
    against a stored schedule that is the committed sweep spec and the one active.json names."""
    if sweep.verify_sweep(Path(raw), Path(corpus_root))["complete"] is not True:
        return False
    stored = _json(Path(raw) / execute.SPEC_FILE)
    if stored != committed or sweep._schedule_refusal(committed, active) is not None:
        return False
    if not active.get("base_case_ids") or list(committed.get("base_case_ids") or []) != list(active["base_case_ids"]):
        return False
    found = {r["logical_trial_id"] for p in Path(raw).glob("*/results.jsonl") for r in _jsonl(p)}
    return bool(found) and found == _ids(committed) == set(execute.stored_schedule(Path(raw)))


def check_c1_verify(raw: Path, active: dict[str, Any], committed: dict[str, Any]) -> bool:
    """The C1 run is complete and verifies, and its schedule is the committed C1 spec, which is the
    one active.json names: its controls in order, at the tier row's C1 repeats."""
    if c1_trial.verify_c1(Path(raw))["complete"] is not True:
        return False
    stored = _json(Path(raw) / execute.SPEC_FILE)
    if stored != committed or c1_trial.schedule_refusal(committed, active) is not None:
        return False
    row = TIERS.get(active.get("tier"))
    if row is None or len(active.get("c1_controls") or []) != row["c1_controls"]:
        return False
    records = [r for p in Path(raw).glob("*/results.jsonl") for r in _jsonl(p)]
    if any(r.get("split") != "c1_control" or r.get("analysis_role") != "c1_control" for r in records):
        return False
    found = {r["logical_trial_id"] for r in records}
    return bool(found) and len(found) == len(records) and found == _ids(committed) == set(execute.stored_schedule(Path(raw)))


# --------------------------------------------------------------------------- sanitized bundle


def _released(root: Path) -> dict[str, Path]:
    return {p.relative_to(root).as_posix(): p for p in sorted(root.rglob("*.jsonl")) if p.name in sanitizer.RELEASED}


def check_sanitized_match(raw: Path, bundle: Path) -> bool:
    """The bundle is exactly this sanitizer's output for these raw records, its manifest binds it,
    and it holds nothing but the manifest and the files the manifest lists."""
    raw, bundle = Path(raw), Path(bundle)
    manifest = _json(bundle / "manifest.json")
    sanitizer._validator("manifest").validate(manifest)
    if manifest["bundle_type"] != "sanitized" or manifest["sanitizer_version"] != sanitizer.SANITIZER_VERSION:
        return False
    entries = {entry["path"]: entry for entry in manifest["files"]}
    if len(entries) != len(manifest["files"]):
        return False
    present = set()
    for path in bundle.rglob("*"):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            return False
        if path.is_file():
            present.add(path.relative_to(bundle).as_posix())
    if present != set(entries) | {"manifest.json"}:
        return False
    raw_files, public_files = _released(raw), _released(bundle)
    if not raw_files or set(raw_files) != set(public_files) or set(entries) != set(public_files):
        return False
    for path, public in public_files.items():
        data = public.read_bytes()
        if entries[path]["sha256"] != hashlib.sha256(data).hexdigest() or entries[path]["size_bytes"] != len(data):
            return False
        validator = sanitizer._validator(sanitizer.RELEASED[public.name])
        raw_records, public_records = _jsonl(raw_files[path]), _jsonl(public)
        for record in (*raw_records, *public_records):
            validator.validate(record)
        sanitizer.verify_projection_unchanged(raw_records, public_records)
        if [sanitizer.sanitize_record(r) for r in raw_records] != public_records:
            return False
    return True


# --------------------------------------------------------------------------- missingness


def _nonempty(design: Optional[Design]) -> bool:
    return design is not None and bool(design.base_case_ids and design.channels and design.configurations
                                       and design.run_indices)


def check_missingness(run: Run) -> bool:
    """The accounting is complete (decision 0043 item 2): the geometry plans something, no record is
    outside it or a second record for a cell, every record is a primary one, and every planned cell
    has its record. A cell's null endpoints are its recorded missingness; the 5% rule is eligibility's."""
    design = run.design
    if not _nonempty(design):
        return False
    cells = _index(run.records, design)
    planned = {(base, channel, condition, configuration, index) for base in design.base_case_ids
               for channel in design.channels for condition in CONDITIONS
               for configuration in design.configurations for index in design.run_indices}
    return len(cells) == len(run.records) and set(cells) == planned


# --------------------------------------------------------------------------- headline eligibility


Plan = tuple[str, list[tuple], Callable[[str], Iterable[tuple]]]


def _plan(design: Design, output_id: str, configuration: Optional[str]) -> Optional[Plan]:
    """A headline comparison as the report plans it, ``(endpoint, component keys, pairs)``, where
    ``pairs(base)`` yields ``(component key, [cell per arm])`` for each of the base's pairing keys;
    a rate is a one-arm comparison over its runs. None when the geometry doesn't plan it: a
    configuration it needs isn't retained, or it has no component."""
    configs, channels, runs = design.configurations, design.channels, design.run_indices

    def per_arm(name, condition, by_task, high_risk_only=False) -> Plan:
        def pairs(base):
            for channel in channels:
                for run in runs:
                    yield _key_of(design, by_task, base, channel), [(base, channel, condition, configuration, run)]
        return name, _keys(design, by_task, high_risk_only), pairs

    def defense(name, condition, treated, by_task) -> Plan:
        def pairs(base):
            for channel in channels:
                for run in runs:
                    yield _key_of(design, by_task, base, channel), [
                        (base, channel, condition, BASELINE, run), (base, channel, condition, treated, run)]
        return name, _keys(design, by_task, False), pairs

    def four_cell(base):
        for channel in channels:
            for run in runs:
                yield (channel,), [(base, channel, "attack", MARKING, run), (base, channel, "clean", MARKING, run),
                                   (base, channel, "attack", BASELINE, run), (base, channel, "clean", BASELINE, run)]

    plan: Optional[Plan] = None
    if output_id in ("ModelViolationRate", "SystemCompromiseRate", "CleanUtility", "AuthorizedHighRiskCleanUtility"):
        if configuration in configs:
            plan = {"ModelViolationRate": lambda: per_arm("model_violation", "attack", False),
                    "SystemCompromiseRate": lambda: per_arm("system_compromise", "attack", False),
                    "CleanUtility": lambda: per_arm("utility_pass", "clean", True),
                    "AuthorizedHighRiskCleanUtility": lambda: per_arm("utility_pass", "clean", True, True)}[output_id]()
    elif BASELINE in configs:
        if output_id == "DatamarkingAttackRiskDifference" and MARKING in configs:
            plan = defense("model_violation", "attack", MARKING, False)
        elif output_id == "DatamarkingInjectionSpecificDifference" and MARKING in configs:
            plan = "model_violation", _keys(design, False, False), four_cell
        elif output_id == "PolicyGateResidualSystemRiskDifference" and GATE in configs:
            plan = defense("system_compromise", "attack", GATE, False)
        elif output_id == "CleanUtilityCost" and configuration in configs and configuration != BASELINE:
            plan = defense("utility_pass", "clean", configuration, True)
    return plan if plan is not None and plan[1] else None


def _ineligible(cells: dict, design: Design, multiplicity, name: str, keys: list[tuple],
                pairs: Callable[[str], Iterable[tuple]]) -> bool:
    """The report's rule per component: more than 5% of its planned keys incomplete, or any arm
    missing more than 5% of its scheduled values. A component with nothing planned is ineligible."""
    planned: dict[tuple, int] = defaultdict(int)
    incomplete: dict[tuple, int] = defaultdict(int)
    arm_missing: dict[tuple, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    wanted = set(keys)
    for base in dict.fromkeys(design.base_case_ids):
        weight = multiplicity[base]
        for key, arms in pairs(base):
            if key not in wanted:
                continue
            missing = [endpoint(cells.get(cell), name) is None for cell in arms]
            planned[key] += weight
            incomplete[key] += weight * any(missing)
            for arm, absent in enumerate(missing):
                arm_missing[key][arm] += weight * absent
    if not keys:
        return True
    for key in keys:
        total = planned[key]
        if total <= 0:
            return True
        if incomplete[key] / total > THRESHOLD or any(m / total > THRESHOLD for m in arm_missing[key].values()):
            return True
    return False


def planned_headline(design: Design) -> list[str]:
    """The names of the headline comparisons this geometry plans, in ``HEADLINE`` order."""
    return [name for name, output_id, configuration in HEADLINE if _plan(design, output_id, configuration) is not None]


def check_eligible(run: Run, name: str) -> bool:
    """One headline comparison is complete enough for the headline (SPEC.md Section 9's 5% rule,
    inside every component that enters its macro-average). It reads no outcome value."""
    design = run.design
    entry = next((e for e in HEADLINE if e[0] == name), None)
    if design is None or entry is None:
        return False
    plan = _plan(design, entry[1], entry[2])
    if plan is None:
        return False
    return not _ineligible(_index(run.records, design), design, _counts(design, None), *plan)


# --------------------------------------------------------------------------- comparability


def _one(values: Iterable[Any]) -> bool:
    """Exactly one recorded value: a field null everywhere is unrecorded, not consistent."""
    values = list(values)
    if not values or any(v is None for v in values):
        return False
    return len({json.dumps(v, sort_keys=True) for v in values}) == 1


def _one_present(values: Iterable[Any]) -> bool:
    """Exactly one value among those recorded, nulls set aside, and at least one recorded."""
    return _one(v for v in values if v is not None)


def _failed(record: dict[str, Any]) -> bool:
    return record.get("status") == INFRASTRUCTURE_FAILURE


def _started(run: Run, record: dict[str, Any]) -> dict[str, Any]:
    [event] = [e for e in run.events[record["logical_trial_id"]] if e["event_type"] == "trial_started"]
    return event


def _resolved(run: Run) -> list[Any]:
    """Every recorded resolved model. A trial whose attempts never returned a model (retries run
    out, or a first-step content-filter refusal) records none (runner/mock_slice.py's
    ``_resolved_model``), so nulls are left out; ``_one_present`` still wants one value."""
    calls = [call for record in run.records for call in record["model_calls"]]
    values = [r["run_metadata"].get("model_resolved") for r in run.records] + [c.get("model_resolved") for c in calls]
    return [value for value in values if value is not None]


def _fingerprints(run: Run) -> set[Any]:
    return {c["provider_fingerprint"] for r in run.records for c in r["model_calls"]
            if c.get("provider_fingerprint") is not None}


def check_model_comparability(run: Run) -> bool:
    """One requested and one resolved model, one fingerprint when supplied, and no mixed versions."""
    empirical = run.active.get("empirical") or {}
    requested = empirical.get("model_requested")
    records = run.records
    if not records or not requested:
        return False
    calls = [call for record in records for call in record["model_calls"]]
    metadata = [record["run_metadata"] for record in records]
    if not calls:
        return False
    if any(m.get("model_requested") != requested for m in metadata) or any(c.get("model_requested") != requested for c in calls):
        return False
    resolved = _resolved(run)
    if not _one_present(resolved):
        return False
    if empirical.get("model_resolved") is not None and resolved[0] != empirical["model_resolved"]:
        return False
    if len(_fingerprints(run)) > 1:
        return False
    for name in ("code_commit", "schedule_seed"):
        if not _one(m.get(name) for m in metadata):
            return False
    # corpus_hash is the hash of the trial's own base, so it is one value per base, not per run
    for base in {r["base_case_id"] for r in records}:
        if not _one(r["run_metadata"].get("corpus_hash") for r in records if r["base_case_id"] == base):
            return False
    # the defense hash and component set differ by configuration, never within one; no defense, no
    # hash. A trial whose fixture build failed started no defense, so only an infrastructure
    # failure may leave it null.
    for configuration in {r["configuration"] for r in records}:
        within = [r for r in records if r["configuration"] == configuration]
        hashes = [r["run_metadata"].get("defense_hash") for r in within]
        if configuration == BASELINE:
            if any(h is not None for h in hashes):
                return False
        elif any(h is None and not _failed(r) for h, r in zip(hashes, within)) or not _one_present(hashes):
            return False
        if not _one(r["run_metadata"].get("component_versions") or None for r in within):
            return False
    if not _one(r.get("protocol_version") for r in records) or records[0].get("protocol_version") != run.active.get("protocol_version"):
        return False
    started = [_started(run, record)["payload"] for record in records]
    for name in ("decoding", "request_settings", "delivery_version", "max_steps"):
        if not _one(p.get(name) for p in started):
            return False
    return True


def check_c1_model_comparability(c1: Run, primary: Optional[Run]) -> bool:
    """The C1 run is comparable on its own, and ran the sweep's model, code, protocol, and settings."""
    if primary is None or not check_model_comparability(c1) or not check_model_comparability(primary):
        return False
    if not _one_present(_resolved(c1) + _resolved(primary)) or len(_fingerprints(c1) | _fingerprints(primary)) > 1:
        return False
    both = c1.records + primary.records
    if not _one(r["run_metadata"].get("code_commit") for r in both) or not _one(r.get("protocol_version") for r in both):
        return False
    started = [_started(c1, r)["payload"] for r in c1.records] + [_started(primary, r)["payload"] for r in primary.records]
    return all(_one(p.get(name) for p in started) for name in ("decoding", "request_settings", "delivery_version"))


# --------------------------------------------------------------------------- attempts and identifiers


def check_attempt_histories(run: Run) -> bool:
    """At most two retries per call, and only after an attempt with no model content (SPEC.md Section 9)."""
    if not run.records:
        return False
    for record in run.records:
        trial = record["logical_trial_id"]
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for attempt in record["attempts"]:
            groups[attempt["model_call_id"]].append(attempt)
        for call, attempts in groups.items():
            if len(attempts) > MAX_ATTEMPTS:
                return False
            if [a["attempt_index"] for a in attempts] != list(range(1, len(attempts) + 1)):
                return False
            if len({a["step"] for a in attempts}) != 1:
                return False
            if any(a["outcome"] != "no_model_content" for a in attempts[:-1]):
                return False
        # every logged model call has an attempt history whose last attempt returned something
        for call in record["model_calls"]:
            attempts = groups.get(call["model_call_id"])
            if not attempts or attempts[-1]["outcome"] == "no_model_content" or attempts[-1]["step"] != call["step"]:
                return False
        logged = [e["attempt_id"] for e in run.events[trial] if e["event_type"] == "provider_attempt"]
        if logged != [a["attempt_id"] for a in record["attempts"]]:
            return False
    return True


def check_identifiers(run: Run) -> bool:
    """Trial, call, attempt, and event IDs bind their cell and parents, and are unique (DATA_CONTRACTS.md).
    The trial IDs' protocol sentinel is the run's schedule spec's, never the unfrozen one."""
    empirical = run.active.get("empirical") or {}
    experiment, model = empirical.get("experiment_id"), empirical.get("model_requested")
    sentinel = run.stored_spec.get("protocol_sentinel")
    if not experiment or not model or not isinstance(sentinel, str) or not sentinel or sentinel == schedule.PROTOCOL_SENTINEL:
        return False
    seen: dict[str, set] = {"trial": set(), "call": set(), "attempt": set(), "event": set()}

    def unique(kind: str, value: str) -> bool:
        if value in seen[kind]:
            return False
        seen[kind].add(value)
        return True

    if not run.records:
        return False
    for record in run.records:
        trial = record["logical_trial_id"]
        expected = schedule.logical_trial_id(experiment, model, record["base_case_id"], record["channel"],
                                             record["condition"], record["configuration"], record["run_index"], sentinel)
        superblock = schedule.comparison_superblock_id(experiment, model, record["base_case_id"], record["run_index"], sentinel)
        if (trial != expected or record.get("experiment_id") != experiment
                or record.get("comparison_superblock_id") != superblock
                or record.get("case_id") != f"{record['base_case_id']}:{record['channel']}:{record['condition']}"
                or not unique("trial", trial)):
            return False
        for call in record["model_calls"]:
            if call["model_call_id"] != f"{trial}:step{call['step']}" or not unique("call", call["model_call_id"]):
                return False
        for attempt in record["attempts"]:
            if (attempt["model_call_id"] != f"{trial}:step{attempt['step']}"
                    or attempt["attempt_id"] != f"{attempt['model_call_id']}:a{attempt['attempt_index']}"
                    or not unique("attempt", attempt["attempt_id"])):
                return False
        events = run.events.get(trial) or []
        if [e["sequence"] for e in events] != list(range(1, len(events) + 1)):
            return False
        for event in events:
            if (event["logical_trial_id"] != trial or event["event_id"] != f"{trial}:e{event['sequence']}"
                    or event.get("experiment_id") != experiment or event.get("configuration") != record["configuration"]
                    or not unique("event", event["event_id"])):
                return False
            if event["event_type"] == "provider_attempt":
                attempt_id, call_id = event.get("attempt_id"), event.get("model_call_id")
                if not attempt_id or not call_id or not attempt_id.startswith(f"{call_id}:a") or not call_id.startswith(f"{trial}:step"):
                    return False
    return True


# --------------------------------------------------------------------------- resets


def _resets(run: Run, rendered: bool) -> bool:
    if not run.records:
        return False
    names = ("fixture_hash", "database_hash", "rendered_sha256") if rendered else ("fixture_hash", "database_hash")
    within: dict[tuple, set] = defaultdict(set)  # (base, run, channel, condition) -> starting states
    across: dict[tuple, set] = defaultdict(set)  # (base, channel, condition) -> canary-independent states
    superblocks: dict[str, tuple] = {}
    for record in run.records:
        payload = _started(run, record)["payload"]
        if payload.get("channel") != record["channel"] or payload.get("condition") != record["condition"]:
            return False
        if payload.get("rendered_sha256") != record["run_metadata"].get("rendered_fixture_hash"):
            return False
        if not rendered and payload.get("rendered_sha256") is not None:
            return False
        state = tuple(payload.get(name) for name in names)
        # A trial whose fixture build failed started from no state; only an infrastructure failure may.
        unbuilt = None in state
        if unbuilt and not _failed(record):
            return False
        superblock = record["comparison_superblock_id"]
        entry = run.canary_map.get(superblock) or {}
        canaries = record.get("canaries")
        if (entry.get("comparison_superblock_id") != superblock or entry.get("base_case_id") != record["base_case_id"]
                or entry.get("run_index") != record["run_index"] or not canaries or canaries != entry.get("canaries")):
            return False
        if superblocks.setdefault(superblock, (record["base_case_id"], record["run_index"])) != (
                record["base_case_id"], record["run_index"]):
            return False
        if not unbuilt:
            within[(record["base_case_id"], record["run_index"], record["channel"], record["condition"])].add(state)
            across[(record["base_case_id"], record["channel"], record["condition"])].add(state[1:])
    if any(len(states) != 1 for states in within.values()) or any(len(states) != 1 for states in across.values()):
        return False
    tokens = [token for superblock in superblocks for token in run.canary_map[superblock]["canaries"]]
    return len(tokens) == len(set(tokens))


def check_resets(run: Run) -> bool:
    """Every configuration of a superblock's cell starts from one fixture, database, and render; the
    attack and clean cells of a superblock carry its one canary pair; every superblock's pair is
    fresh; and across repeats, where the canaries (written into the fixture files) differ, the
    canary-independent state, the database and the render, is the same (SPEC.md Sections 3 and 9).
    A trial that started from no state is allowed only as an infrastructure failure, and still
    carries its superblock's canaries."""
    return _resets(run, rendered=True)


def check_c1_resets(run: Run) -> bool:
    """The C1 run's resets: as the sweep's, but a C1 control has no rendered fixture, so its render
    hash is null on every trial and the database alone is the canary-independent state."""
    return _resets(run, rendered=False)


# --------------------------------------------------------------------------- output


def _emit(line: str) -> None:
    print(line)


def _safe(check: Callable[[], bool]) -> bool:
    """Any error is a bare fail, SystemExit included: its message could carry a value."""
    try:
        return check() is True
    except KeyboardInterrupt:
        raise
    except BaseException:  # noqa: BLE001
        return False


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Count-only Gate 4 audit: pass or fail per check.")
    parser.add_argument("--raw", type=Path, required=True, help="the sweep run directory")
    parser.add_argument("--sanitized", type=Path, required=True, help="the sweep's sanitized bundle directory")
    parser.add_argument("--c1-raw", type=Path, default=None, help="the C1 run directory")
    parser.add_argument("--c1-sanitized", type=Path, default=None, help="the C1 run's sanitized bundle directory")
    parser.add_argument("--active", type=Path, default=ROOT / "protocol" / "active.json")
    parser.add_argument("--sweep-spec", type=Path, default=ROOT / "protocol" / "sweep_spec.json")
    parser.add_argument("--c1-spec", type=Path, default=ROOT / "protocol" / "c1_spec.json")
    parser.add_argument("--corpus-root", type=Path, default=ROOT / "corpus" / "evaluation")
    args = parser.parse_args(argv)
    with_c1 = args.c1_raw is not None and args.c1_sanitized is not None

    results: dict[str, bool] = {}
    eligible: dict[str, bool] = {}
    sink = io.StringIO()
    logging.disable(logging.CRITICAL)
    try:
        with warnings.catch_warnings(), contextlib.redirect_stderr(sink), contextlib.redirect_stdout(sink):
            warnings.simplefilter("ignore")
            this = sys.modules[__name__]
            loaded: dict[str, Run] = {}
            inputs: dict[str, Any] = {}
            _safe(lambda: loaded.setdefault("sweep", load(args.raw, args.active, args.corpus_root)) is not None)
            _safe(lambda: inputs.setdefault("active", _json(args.active)) is not None)
            _safe(lambda: inputs.setdefault("sweep_spec", _json(args.sweep_spec)) is not None)
            run = loaded.get("sweep")
            active, sweep_spec = inputs.get("active"), inputs.get("sweep_spec")
            results["verify_sweep"] = active is not None and sweep_spec is not None and _safe(
                lambda: this.check_verify_sweep(args.raw, args.corpus_root, active, sweep_spec))
            results["sanitized_match"] = _safe(lambda: this.check_sanitized_match(args.raw, args.sanitized))
            for name in CHECKS[2:]:
                results[name] = run is not None and _safe(lambda fn=getattr(this, f"check_{name}"): fn(run))
            # The geometry alone decides which lines print; without it, every name prints, failed.
            _safe(lambda: inputs.setdefault("headline", this.planned_headline(
                design_from(active, args.corpus_root))) is not None)
            for name in inputs.get("headline", [entry[0] for entry in HEADLINE]):
                eligible[name] = run is not None and _safe(lambda name=name: this.check_eligible(run, name))
            if with_c1:
                _safe(lambda: loaded.setdefault("c1", load(args.c1_raw, args.active)) is not None)
                _safe(lambda: inputs.setdefault("c1_spec", _json(args.c1_spec)) is not None)
                c1, c1_spec = loaded.get("c1"), inputs.get("c1_spec")
                results["c1_verify"] = active is not None and c1_spec is not None and _safe(
                    lambda: this.check_c1_verify(args.c1_raw, active, c1_spec))
                results["c1_sanitized_match"] = _safe(lambda: this.check_sanitized_match(args.c1_raw, args.c1_sanitized))
                results["c1_model_comparability"] = c1 is not None and _safe(
                    lambda: this.check_c1_model_comparability(c1, run))
                results["c1_attempt_histories"] = c1 is not None and _safe(lambda: this.check_attempt_histories(c1))
                results["c1_identifiers"] = c1 is not None and _safe(lambda: this.check_identifiers(c1))
                results["c1_resets"] = c1 is not None and _safe(lambda: this.check_c1_resets(c1))
            else:
                results["c1"] = False
    finally:
        logging.disable(logging.NOTSET)
    word = {True: "pass", False: "fail"}
    for name in CHECKS:
        _emit(f"{name}: {word[results[name] is True]}")
    for name, value in eligible.items():
        _emit(f"{name}: {word[value is True]}")
    sweep_passed = all(results[name] is True for name in CHECKS)
    _emit(f"overall_sweep: {'PASS' if sweep_passed else 'FAIL'}")
    c1_names = C1_CHECKS if with_c1 else ("c1",)
    for name in c1_names:
        _emit(f"{name}: {word[results[name] is True]}")
    _emit(f"overall_c1: {'PASS' if all(results[name] is True for name in c1_names) else 'FAIL'}")
    return 0 if sweep_passed else 1


if __name__ == "__main__":
    sys.exit(main())
