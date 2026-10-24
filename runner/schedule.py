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

# The result schema's closed sets (schemas/result.schema.json).
CHANNELS = ("C2", "C3", "C4")
CONDITIONS = ("attack", "clean")
CONFIGURATIONS = ("D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING")

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


def validate_trial(trial: "ScheduledTrial") -> None:
    """Re-check one trial's path-bearing fields, for trials not built by ``generate_schedule``."""
    _check_id("experiment_id", trial.experiment_id)
    _check_id("base_case_id", trial.base_case_id)
    _check_member("channel", trial.channel, CHANNELS)
    _check_member("condition", trial.condition, CONDITIONS)
    _check_member("configuration", trial.configuration, CONFIGURATIONS)
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
