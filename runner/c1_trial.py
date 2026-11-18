"""The official C1 control trial ([decision 0037](../docs/decisions/0037-c1-authorization.md);
[decision 0034](../docs/decisions/0034-c1-result-records.md) item 8; `SPEC.md` Section 7,
"Official C1 controls").

A C1 control has no task template: its trusted prompt is the hostile instruction. So the
pieces a primary delivery cell takes from its base case's template come from here instead:

- the control record, read from `corpus/c1_controls/` and checked against its manifest
  digest and its source record (`load_control`);
- the case: the control's own messages, no rendered resource, the read-only C1 reference
  policy, no grant, and the shared step bound (`C1Case`);
- the fixture root: the frozen W6-T1 fixture with the trial's synthetic secrets and the
  planted resources, and no channel overlay (`build_fixtures`);
- the independent audit, against the C1 reference policy and an empty grant state
  (`audit`);
- the no-credit mock provider (`provider_factory`), `runner.c1_mock.C1Mock`'s canned
  actions, never a model.

Every fact and union is then scored by the same delivery scorer as a primary cell, and
utility is decision 0037's named not-applicable oracle.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from agent.loop import MAX_STEPS
from defenses.interfaces import GrantState, canonical_json_bytes
from runner import delivery as tool_delivery
from runner.c1_policy import C1_UTILITY, c1_reference_policy
from runner.schedule import C1_BASE_CASE_ID, C1_CHANNEL
from tasks import registry

ROOT = Path(__file__).resolve().parents[1]
C1_CORPUS_ROOT = ROOT / "corpus" / "c1_controls"


def is_c1(base_case_id: str) -> bool:
    return C1_BASE_CASE_ID.fullmatch(base_case_id) is not None


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_control(corpus_root: Path, base_case_id: str) -> dict[str, Any]:
    """One official C1 control, refused unless it is the manifest's committed record for
    that ID, its source record matches the control's pin, and it carries no literal canary."""
    corpus_root = Path(corpus_root)
    manifest = _read(corpus_root / "manifest.json")
    pins = {entry["base_case_id"]: entry["sha256"] for entry in manifest["controls"]}
    if base_case_id not in pins:
        raise ValueError(f"{base_case_id} isn't a control in {corpus_root / 'manifest.json'}")
    control = _read(corpus_root / f"{base_case_id}.json")
    if registry.digest(control) != pins[base_case_id]:
        raise ValueError(f"{base_case_id}: the control record isn't the one its manifest pins")
    if (control.get("base_case_id"), control.get("channel"), control.get("configuration"), control.get("split")) != (
            base_case_id, C1_CHANNEL, "D0_BASELINE", "c1_control"):
        raise ValueError(f"{base_case_id}: not an official C1 control record")
    source = _read(ROOT / control["source_path"])
    if registry.digest(source) != control["source_sha256"]:
        raise ValueError(f"{base_case_id}: the control's source record changed")
    if "CANARY-" in json.dumps(control["messages"]):
        raise ValueError("a C1 control's messages must not contain a literal canary (SPEC.md Section 5)")
    return control


def attack_family_id(control: Mapping[str, Any]) -> str:
    """The attack family of the control's source record (the control record doesn't carry it)."""
    source = _read(ROOT / control["source_path"])
    if registry.digest(source) != control["source_sha256"]:
        raise ValueError(f"{control['base_case_id']}: the control's source record changed")
    return source["attack"]["attack_family_id"]


def policy_hash(policy: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(policy)).hexdigest()


@dataclass(frozen=True)
class C1Case:
    """What one C1 trial needs before its first model call (the C1 counterpart of
    `runner.delivery.DeliveryCase`)."""

    control: Mapping[str, Any]
    messages: list[dict[str, Any]]
    policy: Mapping[str, Any]
    untrusted_content: Optional[str] = None
    rendered: Optional[str] = None
    max_steps: int = MAX_STEPS

    def grant_state(self) -> GrantState:
        return GrantState(())

    def started_fields(self) -> dict[str, Any]:
        """Fields `trial_started` adds for a C1 trial, in the delivery cell's names."""
        return {
            "delivery_version": tool_delivery.DELIVERY_VERSION,
            "template_id": None,
            "task_version": None,
            "task_prompt": None,
            "max_steps": self.max_steps,
            "rendered_sha256": None,
            "delivered_sha256": None,
            "policy_hash": policy_hash(self.policy),
            "tool_schema_hash": hashlib.sha256(canonical_json_bytes(registry.TOOL_SCHEMAS)).hexdigest(),
            "defense_hash": None,
            "c1_control_sha256": registry.digest(self.control),
            "c1_policy_id": self.policy["policy_id"],
            "c1_policy_version": self.policy["policy_version"],
        }


def prepare_case(control: Mapping[str, Any], channel: str, condition: str, configuration: str) -> C1Case:
    if (channel, condition, configuration) != (C1_CHANNEL, "attack", "D0_BASELINE"):
        raise ValueError("a C1 control runs only as C1, attack, D0_BASELINE (decision 0034)")
    return C1Case(control=control, messages=copy.deepcopy(list(control["messages"])), policy=c1_reference_policy())


def build_fixtures(root: Path, canaries: Sequence[str]) -> str:
    """The C1 trial's fixture root: W6-T1's frozen files, its synthetic secrets, and the
    planted resources, with no channel overlay. Returns the fixture hash, as
    `runner.delivery.build_fixtures` does for a primary cell."""
    registry.verify(registry.FIXTURES)
    manifest = _read(registry.FIXTURES / "manifest.json")
    files = {name: (registry.FIXTURES / name).read_bytes() for name in manifest["files"]}
    for name, text in {**tool_delivery.secret_files(canaries), **tool_delivery.PLANTED_FILES}.items():
        if name in files:
            raise ValueError(f"{name!r} collides with a W6-T1 fixture file")
        files[name] = text.encode("utf-8")
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    for name, data in files.items():
        target = tool_delivery._inside(root, root / name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o400)
    rows = json.loads(files["db-seed.json"])
    database = root / "fixture.sqlite"
    connection = sqlite3.connect(database)
    try:
        connection.execute("CREATE TABLE documents(resource TEXT, lookup TEXT, record_id TEXT, content TEXT)")
        connection.executemany("INSERT INTO documents VALUES(:resource, :lookup, :record_id, :content)", rows)
        connection.commit()
    finally:
        connection.close()
    database.chmod(0o400)
    registry.verify_database(root)
    expected = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    if tool_delivery._file_hashes(root) != expected:
        raise ValueError("trial fixtures don't match what was written")
    return registry.digest(expected)


def audit(*, events, trial, base, canaries) -> list[dict[str, Any]]:
    """The independent audit for a C1 trial: the C1 reference policy, no grant."""
    from runner.execute import build_tool_events

    if not any(e["event_type"] == "tool_requested" for e in events):
        return []
    return build_tool_events(events, task_policy=c1_reference_policy(), initial_grant_state=GrantState(()))


def utility() -> dict[str, Any]:
    return copy.deepcopy(C1_UTILITY)


def provider_factory(corpus_root: Path = C1_CORPUS_ROOT) -> Callable[[Any, list[str]], Any]:
    """The no-credit C1 mock: `runner.c1_mock.C1Mock`'s canned source-intent actions."""
    from runner.c1_mock import C1Mock

    def factory(trial: Any, canaries: list[str]) -> Any:
        return C1Mock(load_control(corpus_root, trial.base_case_id))

    return factory


# --------------------------------------------------------------------------
# The official C1 run: live command and verification.
# --------------------------------------------------------------------------

DEFAULT_OUT_ROOT = ROOT / "results" / "raw" / "c1"


def _active() -> Optional[dict[str, Any]]:
    from runner import sweep

    try:
        active = json.loads(sweep.ACTIVE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return active if isinstance(active, dict) else None


def schedule_refusal(spec: Mapping[str, Any], active: Mapping[str, Any]) -> Optional[str]:
    """The C1 run is the one `protocol/active.json` names: its C1 controls in exact order,
    its committed seed, experiment, and model, C1 attack D0_BASELINE only, and the Section 12
    row's C1 repeats."""
    from analysis.active_protocol import TIERS

    empirical = active.get("empirical") if isinstance(active.get("empirical"), dict) else {}
    for spec_field, value, source in (("seed", empirical.get("schedule_seed"), "empirical.schedule_seed"),
                                      ("experiment_id", empirical.get("experiment_id"), "empirical.experiment_id"),
                                      ("model_id", empirical.get("model_requested"), "empirical.model_requested")):
        if not value or spec.get(spec_field) != value:
            return f"the C1 spec's {spec_field} {spec.get(spec_field)!r} isn't protocol/active.json's {source} {value!r}"
    controls = active.get("c1_controls")
    if not controls or list(spec.get("base_case_ids") or []) != list(controls):
        return "the C1 spec's base_case_ids aren't protocol/active.json's c1_controls, in its order"
    if (list(spec.get("channels") or []), list(spec.get("conditions") or []), list(spec.get("configurations") or [])) != (
            [C1_CHANNEL], ["attack"], ["D0_BASELINE"]):
        return "a C1 spec runs only C1, attack, D0_BASELINE (decision 0034)"
    row = TIERS.get(active.get("tier"))
    if row is None or spec.get("repeats") != row["c1_repeats"]:
        return f"the C1 spec's repeats {spec.get('repeats')!r} aren't the Section 12 row's C1 repeats"
    return None


def live_refusal(spec: Mapping[str, Any], protocol_version: Optional[str], out: Path) -> Optional[str]:
    """Fail closed before any key is read or any paid call is made, as the sweep does."""
    import os

    from runner import execute, grid_dev, sweep
    from runner.schedule import PROTOCOL_SENTINEL, generate_schedule

    if os.environ.get("CANARY_PAID_RUN_ACK") != "1":
        return "set CANARY_PAID_RUN_ACK=1 only after the Gate 3 record and the project lead's paid-run record for this commit"
    reason = grid_dev._provider_env_refusal()
    if reason:
        return reason
    # The locked schedule_spec schema predates C1, so the generator's own C1 checks decide.
    try:
        generate_schedule(dict(spec))
    except (ValueError, KeyError, TypeError) as exc:
        return f"the C1 spec isn't a valid C1 schedule spec: {exc}"
    if not protocol_version:
        return "the C1 run needs the frozen protocol_version (protocol/active.json)"
    if spec.get("protocol_sentinel", PROTOCOL_SENTINEL) == PROTOCOL_SENTINEL:
        return f"the C1 spec's protocol_sentinel must name the frozen protocol, not {PROTOCOL_SENTINEL!r}"
    if not sweep.ACTIVE.exists():
        return "no protocol/active.json: the Gate 3 step writes it, and no live C1 run starts before it"
    active = _active()
    if active is None:
        return "protocol/active.json isn't a readable JSON object"
    reason = sweep._active_committed_refusal()
    if reason:
        return reason
    if active.get("protocol_version") != protocol_version:
        return f"--protocol-version {protocol_version!r} isn't protocol/active.json's protocol_version {active.get('protocol_version')!r}"
    try:
        corpus, defense = sweep._manifests()
    except sweep.FreezeMissing as exc:
        return str(exc)
    empirical = active.get("empirical") if isinstance(active.get("empirical"), dict) else {}
    for field, manifest, source in (("corpus_hash", corpus, "corpus/freeze.json"),
                                    ("defense_hash", defense, "defenses/freeze.json")):
        if not empirical.get(field) or empirical.get(field) != manifest.get(field):
            return f"protocol/active.json's empirical.{field} isn't {source}'s {field}"
    reason = schedule_refusal(spec, active) or sweep._drift() or execute.raw_evidence_refusal(out)
    if reason:
        return reason
    from runner import paid_run

    # The paid-run record, the lead-side review, and the spend cap, before any key is read.
    # C1 trials don't count against the development ceiling (spend_ledger).
    return paid_run.paid_run_refusal(new_trials=0)


def run_c1(out: Path, *, spec: Mapping[str, Any], protocol_version: str, env_file: Path,
           provider_name: str = "anthropic", resume: bool = False) -> Path:
    """The official C1 run on the frozen model: every control repeat, D0_BASELINE, split and
    role `c1_control`, through tool-result delivery (decision 0037)."""
    from runner import execute, grid_dev, live_smoke, paid_run
    from runner.provider_config import load_api_key
    from runner.schedule import generate_schedule

    reason = grid_dev.fallback_refusal(provider_name) or live_refusal(spec, protocol_version, out)
    if reason:
        raise paid_run.PaidRunRefused(reason)
    config = live_smoke.PROVIDERS[provider_name]
    if spec.get("model_id") != config["model"]:
        raise ValueError(f"a {provider_name} C1 run runs only {config['model']}, but the spec names {spec.get('model_id')}")
    config["check"](config["decoding"])
    try:
        key = load_api_key(Path(env_file), config["key"])
    except (OSError, ValueError) as exc:
        raise ValueError(f"{env_file} must hold exactly one {config['key']}= line") from exc
    if not key:
        raise ValueError(f"{config['key']} in {env_file} is empty")
    adapter = config["adapter"](config["module"].build_client(key))
    del key
    return execute.run_schedule(
        out, generate_schedule(spec), corpus_root=C1_CORPUS_ROOT, resume=resume, spec=dict(spec), delivery=True,
        provider_factory=lambda _trial, _canaries: adapter, decoding=config["decoding"],
        split="c1_control", protocol_version=protocol_version, analysis_role="c1_control",
    )


def verify_c1(run: Path) -> dict[str, Any]:
    """Completeness, schema, and recomputation only; no outcome aggregate."""
    from collections import Counter

    from runner import execute, grid_dev
    from runner.mock_slice import RESULTS_FILE, read_jsonl, validator

    run = Path(run)
    mode = json.loads((run / execute.MODE_FILE).read_text(encoding="utf-8"))
    if mode != {"delivery": True, "split": "c1_control"}:
        raise ValueError(f"{run.name}: not an official C1 run through tool-result delivery")
    schedule = execute.stored_schedule(run)
    pairs, statuses = [], Counter()
    for results in sorted(run.glob(f"*/{RESULTS_FILE}")):
        for record in read_jsonl(results, "result"):
            validator("result").validate(record)
            trial = schedule.get(record["logical_trial_id"])
            if trial is None:
                raise ValueError(f"{record['logical_trial_id']}: not in this run's stored schedule")
            pairs.append((trial, record))
            statuses[record["status"]] += 1
    found = [trial.logical_trial_id for trial, _ in pairs]
    if len(found) != len(set(found)):
        raise ValueError(f"{run.name}: a trial has more than one stored result")
    execute.check_stored_run(run, pairs, corpus_root=C1_CORPUS_ROOT)
    missing = len(set(schedule) - set(found))
    return {"trials_expected": len(schedule), "trials_found": len(found), "missing": missing,
            "status_counts": dict(sorted(statuses.items())),
            "complete": missing == 0 and not grid_dev.stopped_unresolved(run)}


def main(argv: Optional[list[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="The official C1 control run (decision 0037).")
    sub = parser.add_subparsers(dest="command", required=True)
    live = sub.add_parser("live", help="run the C1 controls on the frozen model (paid)")
    live.add_argument("--spec", type=Path, required=True)
    live.add_argument("--protocol-version", required=True)
    live.add_argument("--env-file", type=Path, required=True)
    live.add_argument("--out", type=Path, default=None)
    live.add_argument("--resume", action="store_true")
    check = sub.add_parser("verify", help="verify a C1 run from its stored evidence")
    check.add_argument("run", type=Path)
    args = parser.parse_args(argv)
    if args.command == "verify":
        print(json.dumps(verify_c1(args.run), indent=2, sort_keys=True))
        return 0
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    out = args.out or DEFAULT_OUT_ROOT / str(spec.get("experiment_id"))
    run_c1(out, spec=spec, protocol_version=args.protocol_version, env_file=args.env_file, resume=args.resume)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
