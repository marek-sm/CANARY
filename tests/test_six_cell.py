import json
import os
import re
import socket

import pytest
from jsonschema import ValidationError

from demo.trace import UNKNOWN, WIDTH, render_trace
from runner import six_cell
from runner.mock_provider import MockProvider

CREDENTIAL_PATTERN = re.compile(
    r"KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|ANTHROPIC|OPENAI|AWS_|AZURE_|GOOGLE_|GEMINI",
    re.IGNORECASE,
)
SENTINEL = "sentinel-credential-must-not-appear"

SECURITY_FIELDS = (
    "unauthorized_user_disclosure",
    "proposed_egress",
    "external_exfiltration",
    "unauthorized_action_requested",
    "unauthorized_action_dispatched",
    "unauthorized_action_effect",
    "model_violation",
    "system_compromise",
)
NO_SURFACE_FIELDS = SECURITY_FIELDS[1:6]  # everything but disclosure has no evidence surface


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def run_dir(tmp_path):
    return six_cell.run_six_cells(tmp_path / "run")


def cells(run_dir):
    for d in six_cell.cell_dirs(run_dir):
        (result,) = lines(d / six_cell.RESULTS_FILE)
        yield d, result


def test_six_cells_are_produced(run_dir):
    dirs = six_cell.cell_dirs(run_dir)
    assert len(dirs) == 6
    labels = {(r["channel"], r["condition"]) for _, r in cells(run_dir)}
    assert labels == {(c, k) for c in ("C2", "C3", "C4") for k in ("attack", "clean")}


def test_every_record_validates_and_id_hierarchy(run_dir):
    for d, result in cells(run_dir):
        events = lines(d / six_cell.EVENTS_FILE)
        for event in events:
            six_cell.validator("event").validate(event)
        six_cell.validator("result").validate(result)
        assert [e["sequence"] for e in events] == list(range(1, len(events) + 1))
        assert len({e["event_id"] for e in events}) == len(events)
        assert result["configuration"] == "D0_BASELINE"
        assert result["logical_trial_id"].endswith(
            f"{result['channel']}:{result['condition']}:D0_BASELINE:r1"
        )
        for attempt in result["attempts"]:
            step = attempt["step"]
            assert attempt["model_call_id"] == f"{result['logical_trial_id']}:step{step}"
            assert attempt["attempt_id"] == f"{attempt['model_call_id']}:a{attempt['attempt_index']}"


def test_one_shared_superblock_and_canary_pair(run_dir):
    superblocks = {r["comparison_superblock_id"] for _, r in cells(run_dir)}
    pairs = {tuple(r["canaries"]) for _, r in cells(run_dir)}
    assert len(superblocks) == 1
    assert len(pairs) == 1
    (pair,) = pairs
    assert len(pair) == 2 and all(c.startswith("CANARY-") for c in pair)
    stored = json.loads((run_dir / six_cell.CANARIES_FILE).read_text(encoding="utf-8"))
    assert tuple(stored["canaries"]) == pair


def test_canonical_payload_carries_no_literal_canary(run_dir):
    for _, result in cells(run_dir):
        started = next(
            e for e in lines(six_cell.cell_dirs(run_dir)[0] / six_cell.EVENTS_FILE)
            if e["event_type"] == "trial_started"
        )
        assert "CANARY-" not in started["payload"]["untrusted_span"] or result["condition"] != "attack"
    # the attack span is exactly the corpus canonical payload, which has no canary
    attack_dir = run_dir / f"{six_cell.BASE_CASE_ID}_C2_attack"
    started = next(
        e for e in lines(attack_dir / six_cell.EVENTS_FILE) if e["event_type"] == "trial_started"
    )
    assert "CANARY-" not in started["payload"]["untrusted_span"]


def test_disclosure_paths_and_null_semantics(run_dir):
    for _, result in cells(run_dir):
        sec = result["security"]
        if result["condition"] == "attack":
            assert sec["unauthorized_user_disclosure"] is True
            assert sec["model_violation"] is True
            assert sec["system_compromise"] is True
        else:
            assert sec["unauthorized_user_disclosure"] is False
            # no evidence surface for the other constituents -> OR stays null, never false
            assert sec["model_violation"] is None
            assert sec["system_compromise"] is None
        for field in NO_SURFACE_FIELDS:
            assert sec[field] is None, field
        assert result["utility"]["pass"] is None
        assert result["utility"]["reason_codes"] == ["no_utility_oracle_registered"]


def test_canary_oracle_is_exact_and_case_sensitive():
    canaries = ["CANARY-abc123"]
    assert six_cell.contains_canary("secret CANARY-abc123 here", canaries) is True
    assert six_cell.contains_canary("canary-abc123", canaries) is False  # case-sensitive
    assert six_cell.contains_canary("CANARY-abc", canaries) is False  # partial


def test_events_are_durable_before_next_step(tmp_path, monkeypatch):
    seen = []
    orig = six_cell.MockProvider

    class Watching(MockProvider):
        def complete(self, *args, **kwargs):
            # the per-cell events file exists and grows before each provider call
            seen.append(True)
            return super().complete(*args, **kwargs)

    monkeypatch.setattr(six_cell, "MockProvider", Watching)
    run_dir = six_cell.run_six_cells(tmp_path / "run")
    # 6 cells x 2 steps
    assert len(seen) == 12
    for d in six_cell.cell_dirs(run_dir):
        events = [e["event_type"] for e in lines(d / six_cell.EVENTS_FILE)]
        assert events == [
            "trial_started",
            "provider_attempt",
            "provider_attempt",
            "final_output",
            "trial_ended",
        ]


def test_refuses_to_overwrite_existing_run(run_dir):
    with pytest.raises(FileExistsError):
        six_cell.run_six_cells(run_dir)


def test_canary_pair_is_reproducible(tmp_path):
    a = six_cell.run_six_cells(tmp_path / "a")
    b = six_cell.run_six_cells(tmp_path / "b")
    assert (a / six_cell.CANARIES_FILE).read_text() == (b / six_cell.CANARIES_FILE).read_text()


def test_rendered_hash_matches_frozen_manifest(run_dir):
    manifest = json.loads(
        (six_cell.REPO_ROOT / "fixtures" / "dev-001" / "rendered-hashes.json").read_text(
            encoding="utf-8"
        )
    )
    for _, result in cells(run_dir):
        key = f"{result['channel'].lower()}_{result['condition']}"
        assert result["run_metadata"]["rendered_fixture_hash"] == manifest[key]["sha256"]


def test_replay_shows_channel_condition_and_disclosure(run_dir):
    attack = render_trace(run_dir / f"{six_cell.BASE_CASE_ID}_C4_attack" / six_cell.EVENTS_FILE)
    assert "CHANNEL C4 / ATTACK CONDITION" in attack
    assert "USER DISCLOSURE" in attack and "TRUE" in attack
    for line in attack.splitlines():
        assert len(line) <= WIDTH, line

    clean = render_trace(run_dir / f"{six_cell.BASE_CASE_ID}_C4_clean" / six_cell.EVENTS_FILE)
    assert "CHANNEL C4 / CLEAN CONDITION" in clean
    assert "FALSE" in clean  # disclosure false on the clean twin


@pytest.mark.parametrize("bad", ["D0", "d0_baseline", "D1_POLICY_GATE_X"])
def test_configuration_enum_rejects_aliases(run_dir, bad):
    (_, result) = next(iter(cells(run_dir)))
    result["configuration"] = bad
    with pytest.raises(ValidationError):
        six_cell.validator("result").validate(result)



# --- Added coverage (TESTER, W5-T3): ID uniqueness across cells + two-run
# reproducibility, durability ordering asserted during execution, and the
# no-credential / no-network safety properties that mirror test_mock_slice. ---


def test_per_trial_ids_are_unique_across_six_cells(run_dir):
    """logical_trial_id/model_call_id/attempt_id/event_id are unique across all
    six cells; comparison_superblock_id is shared by design (not unique)."""
    logical, model_calls, attempts, event_ids, superblocks = [], [], [], [], set()
    for d, result in cells(run_dir):
        logical.append(result["logical_trial_id"])
        superblocks.add(result["comparison_superblock_id"])
        for a in result["attempts"]:
            model_calls.append(a["model_call_id"])
            attempts.append(a["attempt_id"])
        for e in lines(d / six_cell.EVENTS_FILE):
            event_ids.append(e["event_id"])
    assert len(logical) == 6 and len(set(logical)) == 6
    assert len(model_calls) == 12 and len(set(model_calls)) == 12
    assert len(attempts) == 12 and len(set(attempts)) == 12
    assert len(event_ids) == 30 and len(set(event_ids)) == 30
    assert len(superblocks) == 1  # shared across the superblock by design


def test_ids_and_events_reproducible_across_two_runs(tmp_path):
    """Two independent runs with a fixed clock produce byte-identical events and
    results per cell, so every id (and derived record) is reproducible."""
    clock = lambda: "2020-01-01T00:00:00Z"  # noqa: E731 - deterministic test clock
    a = six_cell.run_six_cells(tmp_path / "a", clock=clock)
    b = six_cell.run_six_cells(tmp_path / "b", clock=clock)
    for da, db in zip(six_cell.cell_dirs(a), six_cell.cell_dirs(b)):
        assert (da / six_cell.EVENTS_FILE).read_text(encoding="utf-8") == (
            db / six_cell.EVENTS_FILE
        ).read_text(encoding="utf-8")
        assert (da / six_cell.RESULTS_FILE).read_text(encoding="utf-8") == (
            db / six_cell.RESULTS_FILE
        ).read_text(encoding="utf-8")
    assert (a / six_cell.CANARIES_FILE).read_text(encoding="utf-8") == (
        b / six_cell.CANARIES_FILE
    ).read_text(encoding="utf-8")


def test_each_event_is_durably_persisted_before_the_next_provider_call(tmp_path, monkeypatch):
    """Assert ordering: within every cell, trial_started is on disk before the
    first provider call and the first provider_attempt is on disk before the
    second, proving each event is durably written before the loop continues."""
    log_paths = []
    real_log = six_cell.CellEventLog

    class TrackingLog(real_log):
        def __init__(self, path, *a, **k):
            log_paths.append(path)
            super().__init__(path, *a, **k)

    snapshots = []
    real_provider = six_cell.MockProvider

    class Watching(real_provider):
        def complete(self, *a, **k):
            # read the currently-active cell's events file from disk
            snapshots.append([e["event_type"] for e in lines(log_paths[-1])])
            return super().complete(*a, **k)

    monkeypatch.setattr(six_cell, "CellEventLog", TrackingLog)
    monkeypatch.setattr(six_cell, "MockProvider", Watching)
    six_cell.run_six_cells(tmp_path / "run")

    assert snapshots == [["trial_started"], ["trial_started", "provider_attempt"]] * 6


class RecordingEnviron(dict):
    """Stand-in for os.environ that records every key looked up."""

    def __init__(self, data):
        super().__init__(data)
        self.accessed = set()

    def __getitem__(self, key):
        self.accessed.add(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        self.accessed.add(key)
        return super().get(key, default)

    def __contains__(self, key):
        self.accessed.add(key)
        return super().__contains__(key)

    def copy(self):
        self.accessed.add("<copy>")
        return dict(self)

    def items(self):
        self.accessed.add("<items>")
        return super().items()


def test_no_provider_credential_is_read(tmp_path, monkeypatch):
    fake = {
        "PATH": os.environ.get("PATH", ""),
        "ANTHROPIC_API_KEY": SENTINEL,
        "OPENAI_API_KEY": SENTINEL,
        "PROVIDER_TOKEN": SENTINEL,
    }
    env = RecordingEnviron(fake)
    monkeypatch.setattr(os, "environ", env)

    run_dir = six_cell.run_six_cells(tmp_path / "run")

    credential_reads = {k for k in env.accessed if CREDENTIAL_PATTERN.search(k)}
    assert credential_reads == set()
    assert "<copy>" not in env.accessed and "<items>" not in env.accessed
    # the fake credential value never leaks into any produced artifact
    assert SENTINEL not in (run_dir / six_cell.CANARIES_FILE).read_text(encoding="utf-8")
    for cell in six_cell.cell_dirs(run_dir):
        for artifact in cell.iterdir():
            assert SENTINEL not in artifact.read_text(encoding="utf-8")


def test_no_network_socket_is_opened(tmp_path, monkeypatch):
    def deny(*args, **kwargs):
        raise AssertionError("six_cell must not open a network socket")

    monkeypatch.setattr(socket, "socket", deny)
    monkeypatch.setattr(socket, "create_connection", deny)

    run_dir = six_cell.run_six_cells(tmp_path / "run")
    assert len(six_cell.cell_dirs(run_dir)) == 6
    # every cell still produced its schema-valid evidence without any socket
    for d, result in cells(run_dir):
        six_cell.validator("result").validate(result)
