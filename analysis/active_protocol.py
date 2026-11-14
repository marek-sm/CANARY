"""Generate and validate ``protocol/active.json`` (W8-T3).

This is the committed generator SPEC.md Section 10 ("Active-protocol manifest")
and Section 12 require. It reads the project-lead tier inputs (tier, active-
contributor count, funded budget, model decision or explicit no-model reason,
non-personal reason category) and the frozen artifact hashes, recomputes the
Section 12 arithmetic, shows it agrees with the row's official trial count, and
emits a schema-valid manifest.

It never *chooses* a tier and never *computes a freeze hash*: the tier and the
hashes are inputs. Before the Gate 3 step those hashes may be absent, in which
case the generator emits a well-formed draft manifest with null-with-reason
hash fields; the final ``protocol/active.json`` is produced in the Gate 3 step
from the merged W8 freezes (TASKS.md, decision 0025). Run generation,
denominators, and estimands elsewhere read this file; nothing hard-codes 20
bases or three channels (SPEC.md Section 10).

Usage:
    python -m analysis.active_protocol --tier F20 --out protocol/active.json
    python -m analysis.active_protocol --check protocol/active.json
"""

from __future__ import annotations

import argparse
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Optional

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"

# SPEC.md Section 12 operating tiers. Each row is the exact geometry and the
# official trial count the row states. The generator recomputes the count from
# the components and refuses to emit a manifest whose arithmetic disagrees, so a
# transcription error cannot silently ship. These are the published rows; the
# generator does not invent a tier.
#
# primary = bases * tasks_per_geometry? No: SPEC states the product explicitly as
# bases * channels * conditions * configurations * repeats, where "tasks" ride on
# bases (two bases per task template at F20). The official count is that product
# plus the C1 controls (c1_controls * 1 config * c1_repeats).
TIERS: dict[str, dict[str, Any]] = {
    "F20": {"tier_class": "ALL", "bases": 20, "tasks": 10, "channels": 3, "conditions": 2,
            "configurations": 3, "repeats": 3, "c1_controls": 4, "c1_repeats": 3, "official": 1092},
    "R15": {"tier_class": "ALL", "bases": 15, "tasks": 8, "channels": 3, "conditions": 2,
            "configurations": 3, "repeats": 3, "c1_controls": 4, "c1_repeats": 3, "official": 822},
    "M10-ALL": {"tier_class": "ALL", "bases": 10, "tasks": 6, "channels": 2, "conditions": 2,
                "configurations": 3, "repeats": 3, "c1_controls": 3, "c1_repeats": 3, "official": 369},
    "M10-ONE": {"tier_class": "ONE", "bases": 10, "tasks": 6, "channels": 2, "conditions": 2,
                "configurations": 2, "repeats": 3, "c1_controls": 3, "c1_repeats": 3, "official": 249},
    "M10-BASE": {"tier_class": "BASE", "bases": 10, "tasks": 6, "channels": 2, "conditions": 2,
                 "configurations": 1, "repeats": 3, "c1_controls": 3, "c1_repeats": 3, "official": 129},
    "L8-ONE": {"tier_class": "ONE", "bases": 8, "tasks": 5, "channels": 1, "conditions": 2,
               "configurations": 2, "repeats": 3, "c1_controls": 2, "c1_repeats": 3, "official": 102},
    "L8-BASE": {"tier_class": "BASE", "bases": 8, "tasks": 5, "channels": 1, "conditions": 2,
                "configurations": 1, "repeats": 3, "c1_controls": 2, "c1_repeats": 3, "official": 54},
    "R6-ONE": {"tier_class": "ONE", "bases": 6, "tasks": 4, "channels": 1, "conditions": 2,
               "configurations": 2, "repeats": 3, "c1_controls": 2, "c1_repeats": 3, "official": 78},
    "R6-BASE": {"tier_class": "BASE", "bases": 6, "tasks": 4, "channels": 1, "conditions": 2,
                "configurations": 1, "repeats": 3, "c1_controls": 2, "c1_repeats": 3, "official": 42},
    "ENGINEERING": {"tier_class": "ENGINEERING", "bases": 0, "tasks": 0, "channels": 0, "conditions": 0,
                    "configurations": 0, "repeats": 0, "c1_controls": 0, "c1_repeats": 0, "official": 0},
    "STOP": {"tier_class": "STOP", "bases": 0, "tasks": 0, "channels": 0, "conditions": 0,
             "configurations": 0, "repeats": 0, "c1_controls": 0, "c1_repeats": 0, "official": 0},
}

CHANNELS_BY_COUNT = ["C2", "C3", "C4"]
C1_MANIFEST = ROOT / "corpus" / "c1_controls" / "manifest.json"


def c1_control_ids_for(tier: str, manifest_path: Path = C1_MANIFEST) -> list[str]:
    """The tier's ordered C1 controls, from the committed C1 prefix (decisions 0018 and 0034).

    ``corpus/c1_controls/manifest.json`` keys its prefixes by geometry family (``M10`` for
    ``M10-ALL``/``M10-ONE``/``M10-BASE``). Fails closed when the prefix length disagrees with the
    Section 12 row's C1 count, so the manifest and the tier arithmetic can't drift apart.
    """
    row = TIERS[tier]
    if row["tier_class"] in ("ENGINEERING", "STOP"):
        return []
    prefixes = json.loads(Path(manifest_path).read_text(encoding="utf-8"))["tier_prefixes"]
    family = tier.split("-")[0]
    if family not in prefixes:
        raise ValueError(f"{tier}: no C1 prefix for {family!r} in {manifest_path}")
    ids = list(prefixes[family])
    if len(ids) != row["c1_controls"]:
        raise ArithmeticError_(
            f"{tier}: the C1 prefix has {len(ids)} controls, the Section 12 row has {row['c1_controls']}"
        )
    return ids
# Configuration retention by tier class (SPEC Section 12): ALL keeps both
# defenses, ONE keeps D1_POLICY_GATE plus baseline (the retained defense is a
# lead input; D1 is the documented default-ready ONE defense), BASE keeps only
# the baseline.
CONFIGS_ALL = ["D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING"]


class ArithmeticError_(ValueError):
    """Raised when a tier row's recomputed count disagrees with its official count."""


def compute_arithmetic(tier: str) -> dict[str, int]:
    """Recompute the Section 12 official trial count from the row components.

    Returns the arithmetic block; raises if the recomputed total disagrees with
    the published official count for the tier.
    """
    row = TIERS[tier]
    primary = row["bases"] * row["channels"] * row["conditions"] * row["configurations"] * row["repeats"]
    c1 = row["c1_controls"] * row["c1_repeats"]  # one config (D0_BASELINE), implicit factor 1
    computed = primary + c1
    if computed != row["official"]:
        raise ArithmeticError_(
            f"{tier}: recomputed official trial count {computed} "
            f"(primary {primary} + C1 {c1}) disagrees with published {row['official']}"
        )
    return {
        "bases": row["bases"],
        "tasks": row["tasks"],
        "channels": row["channels"],
        "conditions": row["conditions"],
        "configurations": row["configurations"],
        "repeats": row["repeats"],
        "c1_controls": row["c1_controls"],
        "c1_repeats": row["c1_repeats"],
        "primary_trials": primary,
        "c1_trials": c1,
        "computed_official_trial_count": computed,
    }


def retained_configurations(tier: str, retained_one_defense: Optional[str] = None) -> list[str]:
    """Configurations retained by the tier class.

    ALL -> all three; ONE -> baseline + the one retained defense (lead input,
    default D1_POLICY_GATE); BASE/ENGINEERING/STOP -> baseline only or none.
    """
    cls = TIERS[tier]["tier_class"]
    if cls in ("ENGINEERING", "STOP"):
        return []
    if cls == "ALL":
        return list(CONFIGS_ALL)
    if cls == "BASE":
        return ["D0_BASELINE"]
    # ONE
    defense = retained_one_defense or "D1_POLICY_GATE"
    if defense not in ("D1_POLICY_GATE", "D2_DATAMARKING"):
        raise ValueError(f"retained_one_defense must be a defense configuration, got {defense!r}")
    return ["D0_BASELINE", defense]


@lru_cache(maxsize=None)
def _validator(name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _hash_or_none(value: Optional[str]) -> Optional[str]:
    return value if value else None


def generate(
    tier: str,
    *,
    protocol_id: str,
    protocol_version: str,
    active_contributor_count: int,
    selection_reason_category: str,
    accountable_roles: list[str],
    data_cutoff: str,
    base_case_ids: Optional[list[str]] = None,
    c1_control_ids: Optional[list[str]] = None,
    run_indices: Optional[list[int]] = None,
    retained_one_defense: Optional[str] = None,
    budget_cap_usd: Optional[float] = None,
    common_hashes: Optional[Mapping[str, Optional[str]]] = None,
    empirical: Optional[Mapping[str, Any]] = None,
    engineering_fallback: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Build an active-protocol manifest for ``tier``.

    The tier is an input, not a choice. Geometry lists default to the tier's
    sizes but may be supplied by the selection script's committed prefix. Hashes
    and the empirical block default to null-with-reason so a pre-Gate-3 draft is
    well-formed; the Gate 3 step supplies the frozen values.
    """
    if tier not in TIERS:
        raise ValueError(f"unknown tier {tier!r}; must be one of {sorted(TIERS)}")
    row = TIERS[tier]
    cls = row["tier_class"]
    arithmetic = compute_arithmetic(tier)
    configs = retained_configurations(tier, retained_one_defense)
    channels = CHANNELS_BY_COUNT[: row["channels"]]
    runs = list(run_indices) if run_indices is not None else list(range(1, row["repeats"] + 1))

    is_engineering = cls == "ENGINEERING"
    is_stop = cls == "STOP"

    # Geometry: empty for ENGINEERING/STOP, else default placeholders sized to the row.
    if is_engineering or is_stop:
        bases: list[str] = []
        c1s: list[str] = []
        channels = []
        configs = []
        runs = []
    else:
        bases = list(base_case_ids) if base_case_ids is not None else [f"PENDING-base-{i + 1:02d}" for i in range(row["bases"])]
        c1s = list(c1_control_ids) if c1_control_ids is not None else c1_control_ids_for(tier)
        if len(c1s) != row["c1_controls"]:
            raise ArithmeticError_(f"{tier}: {len(c1s)} C1 controls given, the Section 12 row has {row['c1_controls']}")

    ch = dict(common_hashes or {})
    common = {
        "task_registry": _hash_or_none(ch.get("task_registry")),
        "prompt_tool": _hash_or_none(ch.get("prompt_tool")),
        "code_commit": ch.get("code_commit"),
        "container_digest": ch.get("container_digest"),
        "schema": _hash_or_none(ch.get("schema")),
        "oracle_scorer": _hash_or_none(ch.get("oracle_scorer")),
    }

    if is_engineering:
        emp = {
            "experiment_id": None,
            "model_requested": None,
            "model_resolved": None,
            "model_endpoint": None,
            "reasoning_effort": None,
            "defense_hash": None,
            "corpus_hash": None,
            "analysis_hash": None,
            "schedule_seed": None,
            "schedule_concurrency": None,
            "development_floor": None,
            "null_reasons": dict((empirical or {}).get("null_reasons", {}))
            or {"official": "ENGINEERING tier runs no official model experiment (SPEC Section 12)"},
        }
    else:
        e = dict(empirical or {})
        emp = {
            "experiment_id": e.get("experiment_id"),
            "model_requested": e.get("model_requested"),
            "model_resolved": e.get("model_resolved"),
            "model_endpoint": e.get("model_endpoint"),
            "reasoning_effort": e.get("reasoning_effort"),
            "defense_hash": _hash_or_none(e.get("defense_hash")),
            "corpus_hash": _hash_or_none(e.get("corpus_hash")),
            "analysis_hash": _hash_or_none(e.get("analysis_hash")),
            "schedule_seed": e.get("schedule_seed"),
            "schedule_concurrency": e.get("schedule_concurrency"),
            "development_floor": e.get("development_floor"),
            "null_reasons": dict(e.get("null_reasons", {})),
        }

    ef = dict(engineering_fallback or {})
    fallback = {
        "validation_id": ef.get("validation_id"),
        "source_ledger_hash": _hash_or_none(ef.get("source_ledger_hash")),
        "validation_plan_hash": _hash_or_none(ef.get("validation_plan_hash")),
        "validation_schema_hash": _hash_or_none(ef.get("validation_schema_hash")),
        "report_generator_hash": _hash_or_none(ef.get("report_generator_hash")),
    }

    manifest = {
        "schema_version": "0.1.0",
        "protocol_id": protocol_id,
        "protocol_version": protocol_version,
        "tier": tier,
        "tier_class": cls,
        "active_contributor_count": active_contributor_count,
        "selection_reason_category": selection_reason_category,
        "accountable_roles": list(accountable_roles),
        "tier_arithmetic": arithmetic,
        "base_case_ids": bases,
        "base_case_count": len(bases),
        "channels": channels,
        "c1_controls": c1s,
        "configurations": configs,
        "run_indices": runs,
        "stage_configurations": list(configs),
        "stage_configuration_count": len(configs),
        "official_trial_count": arithmetic["computed_official_trial_count"],
        "common_hashes": common,
        "empirical": emp,
        "engineering_fallback": fallback,
        "budget_cap_usd": budget_cap_usd,
        "data_cutoff": data_cutoff,
    }
    validate(manifest)
    return manifest


def validate(manifest: Mapping[str, Any]) -> None:
    """Schema-validate and cross-check the Section 12 arithmetic agrees."""
    _validator("active_protocol").validate(manifest)
    tier = manifest["tier"]
    recomputed = compute_arithmetic(tier)  # raises if the row itself is inconsistent
    if manifest["tier_arithmetic"] != recomputed:
        raise ArithmeticError_(f"{tier}: stored tier_arithmetic does not match the recomputed Section 12 row")
    if manifest["official_trial_count"] != recomputed["computed_official_trial_count"]:
        raise ArithmeticError_(
            f"{tier}: official_trial_count {manifest['official_trial_count']} "
            f"!= recomputed {recomputed['computed_official_trial_count']}"
        )


def load(path: Path) -> dict[str, Any]:
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    validate(manifest)
    return manifest


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tier", choices=sorted(TIERS), help="tier to generate a draft manifest for")
    parser.add_argument("--out", type=Path, help="write the generated manifest here")
    parser.add_argument("--check", type=Path, help="validate an existing manifest and its arithmetic")
    parser.add_argument("--protocol-id", default="PENDING-protocol")
    parser.add_argument("--protocol-version", default="0.1.0")
    parser.add_argument("--contributors", type=int, default=0)
    parser.add_argument("--reason", default="pre-freeze draft")
    parser.add_argument("--data-cutoff", default="PENDING")
    args = parser.parse_args(argv)

    if args.check is not None:
        load(args.check)
        print(f"{args.check}: valid; arithmetic agrees")
        return 0
    if not args.tier:
        parser.error("--tier is required unless --check is given")
    manifest = generate(
        args.tier,
        protocol_id=args.protocol_id,
        protocol_version=args.protocol_version,
        active_contributor_count=args.contributors,
        selection_reason_category=args.reason,
        accountable_roles=[],
        data_cutoff=args.data_cutoff,
    )
    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"wrote {args.out} (tier {args.tier}, {manifest['official_trial_count']} official trials)")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
