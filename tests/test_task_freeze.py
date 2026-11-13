"""Freeze integrity checks, including source/data mutation and inventory drift."""
import json
import shutil

import pytest

from tasks import freeze, registry
from runner import coverage, delivery
from defenses.interfaces import DATAMARKING_SYSTEM_INSTRUCTION


def test_committed_component_candidate_is_current():
    assert freeze.main(["--check"]) == 0
    manifest = freeze.build()
    assert manifest["status"] == "pending_lead_review"
    assert len(manifest["task_ids"]) == 10
    assert set(manifest["common_hashes"]) == {"task_registry", "prompt_tool", "schema", "oracle_scorer"}
    assert manifest["corpus_hash"] == json.loads((freeze.ROOT / "corpus/freeze.json").read_text())["corpus_hash"]


@pytest.fixture
def snapshot(tmp_path):
    manifest = freeze.build()
    files = {name for component in manifest["components"].values() for name in component["files"]}
    corpus = json.loads((freeze.ROOT / "corpus/freeze.json").read_text())
    files.update(corpus["corpus_files"])
    files.update(corpus["source_ledger_files"])
    files.add("corpus/freeze.json")
    for name in files:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(freeze.ROOT / name, target)
    return tmp_path


@pytest.mark.parametrize("name,component", [
    ("tasks/registry.py", "prompt_tool"), ("tools/no_exec.py", "sandbox"),
    ("schemas/policy.schema.json", "schema"),
    ("oracles/utility/task_suite.py", "oracle_scorer"),
    ("runner/coverage.py", "validators"),
])
def test_source_drift_changes_its_component(snapshot, name, component):
    before = freeze.build(snapshot)["components"][component]["sha256"]
    path = snapshot / name
    path.write_bytes(path.read_bytes() + b"\n")
    assert freeze.build(snapshot)["components"][component]["sha256"] != before


def test_added_input_and_missing_required_input_cannot_escape(snapshot):
    before = freeze.build(snapshot)
    (snapshot / "tools/new_tool.py").write_text("# synthetic inventory mutation\n")
    assert freeze.build(snapshot) != before
    (snapshot / "tools/no_exec.py").unlink()
    with pytest.raises(ValueError, match="missing freeze input"):
        freeze.build(snapshot)


def test_symlink_input_is_refused(snapshot):
    path = snapshot / "tools/new_tool.py"
    path.symlink_to(snapshot / "tools/no_exec.py")
    with pytest.raises(ValueError, match="regular freeze input"):
        freeze.build(snapshot)


def test_policy_change_changes_the_independent_policy_hash(snapshot):
    before = freeze.build(snapshot)["authorization_policy_hash"]
    path = snapshot / "tasks/templates/open-ticket-ids.json"
    task = json.loads(path.read_text())
    task["variants"]["C2"]["policy"]["version"] = "synthetic-mutation"
    path.write_text(json.dumps(task))
    assert freeze.build(snapshot)["authorization_policy_hash"] != before


def test_fixture_and_existing_corpus_drift_fail_closed(snapshot):
    path = snapshot / "fixtures/w6-t1/tickets/open.txt"
    original = path.read_bytes()
    path.write_bytes(original + b"\n")
    with pytest.raises(ValueError, match="fixture manifest drift"):
        freeze.build(snapshot)
    path.write_bytes(original)
    path = next((snapshot / "corpus/evaluation").glob("eval-*.json"))
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="W8-T2"):
        freeze.build(snapshot)


@pytest.mark.parametrize("tid", sorted(coverage.CANONICAL))
@pytest.mark.parametrize("configuration", ["D0_BASELINE", "D1_POLICY_GATE", "D2_DATAMARKING"])
def test_trusted_json_contract_reaches_every_coverage_cell(tid, configuration):
    case, template = coverage.expected_case(tid)
    channel = coverage.CANONICAL[tid]
    prepared = delivery.prepare_case(case, channel, "clean", configuration, template)
    expected = registry.SYSTEM_PROMPT
    if configuration == "D2_DATAMARKING":
        expected += "\n\n" + DATAMARKING_SYSTEM_INSTRUCTION
    assert prepared.messages[0] == {"role": "system", "content": expected}
    assert "without Markdown code fences" in expected
    assert prepared.messages[1]["content"] == registry.load(tid)["variants"][channel]["prompt_template"]
