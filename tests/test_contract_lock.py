"""Decision 0009's checks: the measurement-contract lock (SPEC.md Section 11,
"End of week 5"). The Section 5 corpus rules stay pinned by
tests/test_corpus_rules_freeze.py under decision 0007."""
import hashlib
import json
import math
import re
from pathlib import Path

import pytest

from defenses import interfaces as di
from runner import mock_slice
from tasks import ticket

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "SPEC.md"
LOCKED = "1.0.0"
CONTRACT_SCHEMAS = ("event", "result", "policy", "authorization_vectors")

# The SPEC.md v1.4.0 text that Section 11 freezes at this lock. Changing any of
# it needs Section 11 change control, then a deliberate update of its value.
FROZEN_SECTIONS = {
    "### Predeclared result sentence": "e68400d435e3765c0c0174fdafe79c4edb3b78395b9e7230703f59ec42f23f07",
    "## 3. Threat model and safety boundary": "8b1e24d3a171101efa71bb9d1e5fd078f1c43d544e7b25df1f6f407461e967e3",
    "## 7. Deterministic oracles and event model": "00b83dfa3182bf9f68a9973212f0bd2febad8ff28278ca8ab1eb04fd490f89b5",
    "## 8. Data contracts": "f5f662783b51312dca18bcf602dc0fc5acd6a7e2a256915b5d2824f8e2e18e37",
    "### Model selection and pinning": "1f76713f72586c3f004a8d15d28e04a587ee493c3e61a4684efdebec88fb21af",
    "### Trial generation": "08741e828df688a468229a7e02ed9fb697b2f47b947c5a9c68e6297b605e4b4a",
    "### Failure and retry policy": "1bdd4e5896589586edab78f1d3dd539d0ea8161600dc54a13a9bc84de3aa680b",
    "### Primary estimands": "a0b1860f36989bcc307fe4094ee5e44c807e5ce82f0876b1a927e9114ad47bfb",
    "### Uncertainty": "fbec10c0260ce2b8d7ac42148ba70dc998991424746669649e9dd21ef7b4e33d",
    "### Interpretation rules": "05626da33a72e16348c482964561bdb413e6e5f1c648bb423dddd6c630ba07b7",
}


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def spec_section(heading):
    """From `heading` up to the next heading of the same or a higher level, or a
    `---` rule, so a subsection added after a pinned one doesn't change its text."""
    text = SPEC.read_text(encoding="utf-8")
    assert text.count(f"\n{heading}\n") == 1, heading
    start = text.index(f"\n{heading}\n") + 1
    level = len(heading.split(" ", 1)[0])
    end = re.compile(rf"^(?:#{{1,{level}}} |---$)", re.M).search(text, start + len(heading))
    return text[start:end.start() if end else len(text)]


@pytest.mark.parametrize("heading", sorted(FROZEN_SECTIONS))
def test_locked_spec_sections_match_the_lock(heading):
    digest = hashlib.sha256(spec_section(heading).encode("utf-8")).hexdigest()
    assert digest == FROZEN_SECTIONS[heading]


def test_contract_schemas_are_versioned_at_the_lock():
    for name in CONTRACT_SCHEMAS:
        schema = load(f"schemas/{name}.schema.json")
        assert schema["$id"] == f"urn:CANARY:schema:{name}:{LOCKED}"
        assert schema["properties"]["schema_version"] == {"const": LOCKED}


def test_w5_t4_interface_versions_are_frozen():
    assert di.INTERFACE_VERSION == "defense-interfaces-v1.0.0"
    assert di.POLICY_OBSERVATION_VERSION == "policy-observation-v1.0.0"
    assert di.DATAMARKING_SPEC_VERSION == "datamarking-spec-v1.0.0"


def test_committed_records_carry_the_locked_versions():
    for path in sorted((ROOT / "oracles/authorization/golden").glob("*.json")):
        golden = load(path.relative_to(ROOT))
        assert golden["schema_version"] == LOCKED, path.name
        assert golden["interface_version"] == di.INTERFACE_VERSION, path.name
        assert {policy["schema_version"] for policy in golden["policies"].values()} == {LOCKED}, path.name
    marking = load("defenses/vectors/datamarking-w5-t4.json")
    assert marking["schema_version"] == LOCKED
    assert marking["spec_version"] == di.DATAMARKING_SPEC_VERSION
    assert load("tasks/ticket.json")["policy"]["schema_version"] == LOCKED
    for path in sorted((ROOT / "tasks/templates").glob("*.json")):
        task = load(path.relative_to(ROOT))
        assert {variant["policy"]["schema_version"] for variant in task["variants"].values()} == {LOCKED}, path.name
    for fixture in sorted((ROOT / "tests" / "fixtures" / "result").glob("*.json")):
        assert load(fixture.relative_to(ROOT))["schema_version"] == LOCKED, fixture.name


def test_runner_hashes_use_the_canonical_json_rule():
    for value in ({"b": 1, "a": [True, None, 2.5]}, {"path": "inbox/ticket-100.txt"}, {"name": "Zoë π"}):
        assert mock_slice.sha256_json(value) == hashlib.sha256(di.canonical_json_bytes(value)).hexdigest()
    with pytest.raises(ValueError):
        mock_slice.sha256_json({"x": math.nan})


def test_ticket_fixture_digest_uses_the_canonical_rule(tmp_path, monkeypatch):
    (tmp_path / "π.txt").write_bytes(b"x")
    files = {"π.txt": hashlib.sha256(b"x").hexdigest()}
    monkeypatch.setattr(ticket, "manifest", lambda: {"files": files})
    assert ticket.verify(tmp_path) == hashlib.sha256(di.canonical_json_bytes(files)).hexdigest()


def test_the_canonical_rule_leaves_the_committed_fixture_digest_unchanged():
    files = ticket.manifest()["files"]
    before_the_lock = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert ticket.verify(ROOT / "fixtures" / "w5-t1") == before_the_lock


def test_result_schema_reason_codes_are_the_frozen_vocabulary():
    decision = load("schemas/result.schema.json")["$defs"]["decision"]
    assert decision["properties"]["reason_codes"]["items"] == {"enum": list(di.REASON_CODES)}


def test_development_floor_rule_is_predeclared():
    rules = spec_section("### Interpretation rules")
    assert "**Development floor.**" in rules
    assert "fewer than 3" in rules
