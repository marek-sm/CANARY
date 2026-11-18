"""Defense freeze manifest (W8-T4; SPEC.md Section 11 Gate 3).

    python -m defenses.freeze          # write defenses/freeze.json
    python -m defenses.freeze --check  # fail if any frozen file changed since

Records the SHA-256 of every file the retained defenses rest on, in two sets:

- `defense_hash`, the value `protocol/active.json` is to carry as its defense hash: every module in
  `defenses/` (the D1_POLICY_GATE and D2_DATAMARKING implementations), the
  declarative policy schema, the event schema, the defense contract that states the
  event meanings (`docs/DEFENSES_AND_POLICY.md`), and the datamarking specification
  vectors;
- `test_evidence_hash`: the tests that exercise those defenses and where the runner
  applies them, the reviewed allow/deny golden vectors with their schema, and the
  independent audit evaluator and conformance code the differential tests compare
  the gate against.

`configuration_hashes` repeats, per configuration, the `defense_hash` each run
record carries (runner.delivery.defense_hash), so a record ties to this freeze.
Each set hash is SHA-256 over its sorted `path<TAB>sha256` lines, as in
corpus/freeze.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "defenses" / "freeze.json"

DEFENSE_GLOBS = (
    "defenses/*.py",
    "defenses/vectors/*.json",
    "schemas/policy.schema.json",
    "schemas/event.schema.json",
    "docs/DEFENSES_AND_POLICY.md",
)
# The freeze tool is not part of what it freezes.
EXCLUDED = ("defenses/freeze.py",)
TEST_EVIDENCE_GLOBS = (
    "tests/test_datamarking.py",
    "tests/test_defense_contracts.py",
    "tests/test_defense_mutants.py",
    "tests/test_defense_readiness.py",
    "tests/test_gate_audit_differential.py",
    "tests/test_gate_audit_typed_params.py",
    "tests/test_gate_canonicalizer_mutants.py",
    "tests/test_grid_dev_defenses.py",
    "tests/test_policy_gate.py",
    "tests/test_tool_event_scoring.py",
    "tests/test_delivery.py",
    "tests/test_delivery_mutants.py",
    "tests/test_contract_lock.py",
    "oracles/authorization/golden/*.json",
    "oracles/authorization/audit.py",
    "oracles/authorization/conformance.py",
    "schemas/authorization_vectors.schema.json",
)
CONFIGURATIONS = ("D1_POLICY_GATE", "D2_DATAMARKING")


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(globs) -> dict[str, str]:
    out = {}
    for pattern in globs:
        matches = sorted(p for p in ROOT.glob(pattern) if p.is_file() and p.relative_to(ROOT).as_posix() not in EXCLUDED)
        if not matches:
            raise FileNotFoundError(f"nothing to freeze matches {pattern!r}")
        for path in matches:
            out[path.relative_to(ROOT).as_posix()] = file_sha(path)
    return dict(sorted(out.items()))


def set_hash(entries: dict[str, str]) -> str:
    lines = "\n".join(f"{path}\t{sha}" for path, sha in sorted(entries.items()))
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def configuration_hashes() -> dict[str, str]:
    from runner import delivery

    return {configuration: delivery.defense_hash(configuration) for configuration in CONFIGURATIONS}


def build() -> dict:
    defense = files(DEFENSE_GLOBS)
    evidence = files(TEST_EVIDENCE_GLOBS)
    return {
        "rule": "W8-T4 defense freeze; SPEC.md Section 11 Gate 3",
        "configurations": list(CONFIGURATIONS),
        "defense_hash": set_hash(defense),
        "test_evidence_hash": set_hash(evidence),
        "configuration_hashes": configuration_hashes(),
        "defense_files": defense,
        "test_evidence_files": evidence,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write or check the defense freeze manifest.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    text = json.dumps(build(), indent=2) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print("defenses/freeze.json is missing or a frozen file changed; a change after freeze follows SPEC.md Section 11", file=sys.stderr)
            return 1
        return 0
    OUT.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
