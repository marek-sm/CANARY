"""Data-driven, deterministic schedule generation for the general runner (W6-T3 A1/A6).

Turns a small schedule *spec* (plain data: base cases, channels, conditions,
configurations, a repeat count, a committed seed, the experiment id, and the
model id) into an ordered, deterministic list of logical trials. Nothing here is
hardcoded to the six-cell dev prototype: the same generator serves any tier by
reading the components the caller supplies, mirroring SPEC.md Section 9's
"analysis code does not hard-code 20 bases, three channels, or both defenses".

The product generated is SPEC.md Section 9's:

    base case x channel x attack/clean x configuration x repeat (run_index)

Ordering follows SPEC.md Section 9 randomized interleaving: the
``(base_case_id, run_index)`` comparison superblocks are shuffled, then the
channel/condition/configuration cells inside each superblock are shuffled, both
from one committed seed. Superblocks stay contiguous so a resumed run mints and
reloads one canary pair per superblock before that superblock's first cell
(SPEC.md Section 3).

This module is pure: no I/O, no clock, no randomness beyond the committed seed,
and it never mutates its inputs. ``generate_schedule`` fails closed if the spec
would mint two identical ``logical_trial_id`` values (A6: globally unique ids),
or if an identifier could name a path outside the run directory or a value
outside the result schema's channel, condition, and configuration sets.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Any, Mapping

# Development split: no frozen protocol_version exists yet, so the id namespace
# carries the same sentinel the prototype uses (runner/six_cell.py).
PROTOCOL_SENTINEL = "unfrozen"

# The result schema's closed sets (schemas/result.schema.json, 1.1.0).
# C1 is decision 0034's direct-injection control channel. It only ever runs as
# the attack condition under D0_BASELINE (SPEC.md Sections 3, 9, and 12), and a
# schedule holds either C1 or the indirect channels, never both: one run
# directory holds one split and one analysis role (decision 0034 item 8).
INDIRECT_CHANNELS = ("C2", "C3", "C4")
C1_CHANNEL = "C1"
CHANNELS = (*INDIRECT_CHANNELS, C1_CHANNEL)
CONDITIONS = ("attack", "clean")
CONFIGURATIONS = ("D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING")
C1_CONDITION = "attack"
C1_CONFIGURATION = "D0_BASELINE"
# A C1 control's base id (decision 0034 item 2): c1-NNN, never a development base.
C1_BASE_CASE_ID = re.compile(r"c1-[0-9]{3}")

# Identifiers become file names and ':'-separated id parts, so they carry no
# path separator, no ':' and can't be '.' or '..'.
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")

_SPEC_KEYS = (
    "experiment_id",
    "model_id",
    "seed",
    "base_case_ids",
    "channels",
    "conditions",
    "configurations",
    "repeats",
)


@dataclass(frozen=True)
class ScheduledTrial:
    """One ordered logical trial and its derived, globally-unique identifiers.

    ``schedule_index`` is the trial's position in the committed interleaving and
    is reused as the result ``run_metadata.schedule_index``. ``seed`` is the
    committed schedule seed. Every id is deterministic in the spec, so two runs
    of the same spec produce byte-identical ids (A6).
    """

    schedule_index: int
    experiment_id: str
    model_id: str
    protocol_sentinel: str
    base_case_id: str
    channel: str
    condition: str
    configuration: str
    run_index: int
    seed: str
    logical_trial_id: str
    comparison_superblock_id: str


def logical_trial_id(
    experiment_id: str,
    model_id: str,
    base_case_id: str,
    channel: str,
    condition: str,
    configuration: str,
    run_index: int,
    protocol_sentinel: str = PROTOCOL_SENTINEL,
) -> str:
    """The deterministic, globally-unique trial id (SPEC.md Section 8 hierarchy)."""
    return (
        f"{experiment_id}:{protocol_sentinel}:{model_id}:{base_case_id}:"
        f"{channel}:{condition}:{configuration}:r{run_index}"
    )


def comparison_superblock_id(
    experiment_id: str,
    model_id: str,
    base_case_id: str,
    run_index: int,
    protocol_sentinel: str = PROTOCOL_SENTINEL,
) -> str:
    """The ``(base_case_id, run_index)`` superblock id its cells share (SPEC.md Section 3)."""
    return (
        f"{experiment_id}:{protocol_sentinel}:{model_id}:{base_case_id}:r{run_index}"
    )


def _check_id(name: str, value: Any) -> None:
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise ValueError(f"schedule {name} {value!r} is not a safe identifier")


def _check_member(name: str, value: Any, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        raise ValueError(f"schedule {name} {value!r} is not one of {list(allowed)}")


def _validate_spec(spec: Mapping[str, Any]) -> None:
    missing = [k for k in _SPEC_KEYS if k not in spec]
    if missing:
        raise ValueError(f"schedule spec is missing required keys: {sorted(missing)}")
    for key in ("base_case_ids", "channels", "conditions", "configurations"):
        if not spec[key]:
            raise ValueError(f"schedule spec '{key}' must be a non-empty list")
    if int(spec["repeats"]) < 1:
        raise ValueError("schedule spec 'repeats' must be at least 1")
    _check_id("experiment_id", spec["experiment_id"])
    _check_id("protocol_sentinel", spec.get("protocol_sentinel", PROTOCOL_SENTINEL))
    for base in spec["base_case_ids"]:
        _check_id("base_case_id", base)
    for channel in spec["channels"]:
        _check_member("channel", channel, CHANNELS)
    for condition in spec["conditions"]:
        _check_member("condition", condition, CONDITIONS)
    for configuration in spec["configurations"]:
        _check_member("configuration", configuration, CONFIGURATIONS)
    _check_c1_spec(spec)


def is_c1_spec(spec: Mapping[str, Any]) -> bool:
    """True when the spec schedules C1 direct-injection controls (decision 0034)."""
    return C1_CHANNEL in spec["channels"]


def _check_c1_spec(spec: Mapping[str, Any]) -> None:
    """A C1 spec runs only C1, only the attack condition, only D0_BASELINE, and only c1-NNN bases.

    Fails closed on a spec that would mix C1 with indirect channels: one run directory holds one
    split and one analysis role, so C1 runs as its own run directory (decision 0034 item 8).
    """
    if not is_c1_spec(spec):
        return
    if list(spec["channels"]) != [C1_CHANNEL]:
        raise ValueError(f"a C1 schedule runs only channel {C1_CHANNEL}, never beside {list(INDIRECT_CHANNELS)}; "
                         f"C1 runs as its own run directory (decision 0034)")
    if list(spec["conditions"]) != [C1_CONDITION]:
        raise ValueError(f"a C1 schedule runs only the {C1_CONDITION!r} condition (SPEC.md Section 3)")
    if list(spec["configurations"]) != [C1_CONFIGURATION]:
        raise ValueError(f"a C1 schedule runs only {C1_CONFIGURATION} (SPEC.md Sections 3 and 12)")
    for base in spec["base_case_ids"]:
        if not C1_BASE_CASE_ID.fullmatch(base):
            raise ValueError(f"C1 base_case_id {base!r} isn't a c1-NNN control (decision 0034 item 2)")


def validate_trial(trial: "ScheduledTrial") -> None:
    """Re-check one trial's path-bearing fields, for trials not built by ``generate_schedule``."""
    _check_id("experiment_id", trial.experiment_id)
    _check_id("base_case_id", trial.base_case_id)
    _check_member("channel", trial.channel, CHANNELS)
    _check_member("condition", trial.condition, CONDITIONS)
    _check_member("configuration", trial.configuration, CONFIGURATIONS)
    if trial.channel == C1_CHANNEL and (
        trial.condition != C1_CONDITION
        or trial.configuration != C1_CONFIGURATION
        or not C1_BASE_CASE_ID.fullmatch(trial.base_case_id)
    ):
        raise ValueError(f"C1 trial {trial.logical_trial_id!r} must be a c1-NNN control, "
                         f"{C1_CONDITION}, {C1_CONFIGURATION} (decision 0034)")
    if not isinstance(trial.run_index, int) or isinstance(trial.run_index, bool) or trial.run_index < 1:
        raise ValueError(f"schedule run_index {trial.run_index!r} must be a positive integer")
    if not isinstance(trial.schedule_index, int) or isinstance(trial.schedule_index, bool) or trial.schedule_index < 0:
        raise ValueError(f"schedule_index {trial.schedule_index!r} must be a non-negative integer")


def generate_schedule(spec: Mapping[str, Any]) -> list[ScheduledTrial]:
    """Return the ordered, deterministic schedule for ``spec``.

    The order is the committed randomized interleaving (SPEC.md Section 9); the
    content is the full ``base x channel x condition x configuration x repeat``
    product. Fails closed on a duplicate cell so every ``logical_trial_id`` is
    globally unique (A6).
    """
    _validate_spec(spec)
    experiment_id = str(spec["experiment_id"])
    model_id = str(spec["model_id"])
    seed = str(spec["seed"])
    protocol = str(spec.get("protocol_sentinel", PROTOCOL_SENTINEL))
    bases = list(spec["base_case_ids"])
    channels = list(spec["channels"])
    conditions = list(spec["conditions"])
    configurations = list(spec["configurations"])
    repeats = int(spec["repeats"])

    superblocks = [(base, run_index) for base in bases for run_index in range(1, repeats + 1)]
    # One committed seed drives every shuffle. Superblock order and each
    # superblock's internal order each get an independently seeded stream so the
    # internal order of a superblock never depends on where it landed overall.
    random.Random(f"{seed}:superblocks").shuffle(superblocks)

    trials: list[ScheduledTrial] = []
    seen: set[str] = set()
    index = 0
    for base, run_index in superblocks:
        sb_id = comparison_superblock_id(experiment_id, model_id, base, run_index, protocol)
        cells = [
            (channel, condition, configuration)
            for channel in channels
            for condition in conditions
            for configuration in configurations
        ]
        random.Random(f"{seed}:{sb_id}").shuffle(cells)
        for channel, condition, configuration in cells:
            trial_id = logical_trial_id(
                experiment_id, model_id, base, channel, condition, configuration, run_index, protocol
            )
            if trial_id in seen:
                raise ValueError(
                    f"duplicate logical_trial_id {trial_id!r}: the schedule spec repeats a cell"
                )
            seen.add(trial_id)
            trials.append(
                ScheduledTrial(
                    schedule_index=index,
                    experiment_id=experiment_id,
                    model_id=model_id,
                    protocol_sentinel=protocol,
                    base_case_id=base,
                    channel=channel,
                    condition=condition,
                    configuration=configuration,
                    run_index=run_index,
                    seed=seed,
                    logical_trial_id=trial_id,
                    comparison_superblock_id=sb_id,
                )
            )
            index += 1
    return trials


def c1_schedule_spec(
    control_ids: list[str],
    *,
    experiment_id: str,
    model_id: str,
    seed: str,
    protocol_sentinel: str = PROTOCOL_SENTINEL,
    repeats: int = 3,
) -> dict[str, Any]:
    """The schedule spec for one C1 run directory (decision 0034 item 8; SPEC.md Sections 9 and 12).

    ``control_ids`` is the tier's ordered C1 prefix (``corpus/c1_controls/manifest.json``). Every
    empirical row runs its controls at three repeats under D0_BASELINE, attack only. Each
    ``(control, repeat)`` is its own comparison superblock, so each repeat mints its own canary
    pair (SPEC.md Section 9). The result passes ``_validate_spec``.
    """
    spec = {
        "experiment_id": experiment_id,
        "model_id": model_id,
        "seed": seed,
        "protocol_sentinel": protocol_sentinel,
        "base_case_ids": list(control_ids),
        "channels": [C1_CHANNEL],
        "conditions": [C1_CONDITION],
        "configurations": [C1_CONFIGURATION],
        "repeats": repeats,
    }
    _validate_spec(spec)
    return spec


def superblock_groups(schedule: list[ScheduledTrial]) -> dict[str, list[ScheduledTrial]]:
    """Group an ordered schedule by comparison superblock, preserving order.

    Because ``generate_schedule`` keeps each superblock contiguous, the returned
    mapping iterates superblocks in schedule order and each value lists that
    superblock's trials in schedule order. This is the grouping the executor uses
    to mint/reload exactly one canary pair per superblock (SPEC.md Section 3).
    """
    groups: dict[str, list[ScheduledTrial]] = {}
    for trial in schedule:
        groups.setdefault(trial.comparison_superblock_id, []).append(trial)
    return groups
