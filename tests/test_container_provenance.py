"""Prototype (cloud/container-sweep): container_digest comes from the launcher's
daemon-reported file and refuses one that names another container."""

import json

import pytest

from runner import container

ID_A = "a" * 64
ID_B = "b" * 64
DIGEST = "sha256:" + "c" * 64


def _mountinfo(tmp_path, container_id):
    path = tmp_path / "mountinfo"
    path.write_text(
        "98 1 0:50 / / ro,relatime - overlay overlay rw\n"
        f"116 98 254:0 /var/lib/docker/containers/{container_id}/hostname /etc/hostname rw,relatime - ext4 /dev/vda rw\n",
        encoding="utf-8",
    )
    return path


def _record(tmp_path, **fields):
    path = tmp_path / "container.json"
    path.write_text(json.dumps({"container_id": ID_A, "image_digest": DIGEST, **fields}), encoding="utf-8")
    return path


def test_no_launcher_file_is_unknown_not_a_claim(tmp_path):
    assert container.container_digest(tmp_path / "absent.json", _mountinfo(tmp_path, ID_A)) is None


def test_the_daemon_reported_digest_for_this_container(tmp_path):
    assert container.container_digest(_record(tmp_path), _mountinfo(tmp_path, ID_A)) == DIGEST


def test_a_file_for_another_container_refuses(tmp_path):
    with pytest.raises(container.ContainerMismatch, match="written for container"):
        container.container_digest(_record(tmp_path), _mountinfo(tmp_path, ID_B))


def test_a_file_outside_any_container_refuses(tmp_path):
    with pytest.raises(container.ContainerMismatch):
        container.container_digest(_record(tmp_path), tmp_path / "no-mountinfo")


@pytest.mark.parametrize("fields", [{"image_digest": "canary-sweep:proto"}, {"image_digest": None},
                                    {"container_id": ID_A[:12]}])
def test_a_hand_written_value_that_isnt_a_digest_refuses(tmp_path, fields):
    with pytest.raises(container.ContainerMismatch):
        container.container_digest(_record(tmp_path, **fields), _mountinfo(tmp_path, ID_A))


def test_the_host_mount_table_names_no_container(tmp_path):
    path = tmp_path / "mountinfo"
    path.write_text("22 1 254:0 / / rw,relatime - ext4 /dev/vda rw\n", encoding="utf-8")
    assert container.kernel_container_id(path) is None


# --- the paid-run gate sees the image (decision 0028 item 9; container-ready item 1) -----------

from runner import execute, paid_run  # noqa: E402
from runner.mock_slice import EVENTS_FILE, RESULTS_FILE, validator  # noqa: E402

IMAGE_X = "sha256:" + "1" * 64
IMAGE_Y = "sha256:" + "2" * 64


def _in_image(monkeypatch, digest):
    """This process runs in ``digest``'s image, as the launcher's file would say (``None``: the host)."""
    monkeypatch.setattr(container, "container_digest", lambda *args, **kwargs: digest)


def _rewrite_jsonl(path, edit):
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for line in lines:
        edit(line)
    path.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")


def _trial_in_image(trial_dir, digest):
    def started(event):
        if event["event_type"] == "trial_started":
            event["payload"]["container_digest"] = digest
    _rewrite_jsonl(trial_dir / EVENTS_FILE, started)
    _rewrite_jsonl(trial_dir / RESULTS_FILE, lambda r: r["run_metadata"].update(container_digest=digest))


def _grid_in_image(gate, digest):
    """The gate's mock grid as it would be had every invocation and trial run in ``digest``'s image."""
    _rewrite_jsonl(gate.mock / paid_run.PROVENANCE_FILE, lambda line: line.update(container_digest=digest))
    for trial_dir in gate.mock.iterdir():
        if (trial_dir / RESULTS_FILE).is_file():
            _trial_in_image(trial_dir, digest)


@pytest.fixture
def fresh_reads(monkeypatch):
    monkeypatch.setattr(paid_run, "_READ_MOCK_RUNS", {})


def test_a_host_record_states_a_null_image_and_stays_open_on_the_host(gate, fresh_reads):
    record = gate.record()
    assert record["container_digest"] is None
    validator("paid_run_record").validate(record)
    assert gate.refusal(gate.commit_record(record)) is None


def test_a_host_record_refuses_a_run_in_an_image(gate, fresh_reads, monkeypatch):
    path = gate.open()
    _in_image(monkeypatch, IMAGE_X)
    assert "image" in gate.refusal(path)


def test_an_image_record_opens_only_in_that_image(gate, fresh_reads, monkeypatch):
    _grid_in_image(gate, IMAGE_X)
    _in_image(monkeypatch, IMAGE_X)
    record = gate.record()
    assert record["container_digest"] == IMAGE_X
    path = gate.commit_record(record)
    assert gate.refusal(path) is None
    for elsewhere in (IMAGE_Y, None):
        _in_image(monkeypatch, elsewhere)
        assert "image" in gate.refusal(path)


def test_the_record_refuses_a_grid_from_another_image(gate, fresh_reads, monkeypatch):
    _grid_in_image(gate, IMAGE_X)
    _in_image(monkeypatch, IMAGE_Y)
    with pytest.raises(paid_run.PaidRunRefused, match="image"):
        gate.record()


def test_the_record_refuses_a_host_grid_in_an_image(gate, fresh_reads, monkeypatch):
    _in_image(monkeypatch, IMAGE_X)
    with pytest.raises(paid_run.PaidRunRefused, match="image"):
        gate.record()


def test_the_record_refuses_one_trial_from_another_image(gate, fresh_reads, monkeypatch):
    _grid_in_image(gate, IMAGE_X)
    _trial_in_image(gate.trial("D0_BASELINE", "clean"), IMAGE_Y)
    _in_image(monkeypatch, IMAGE_X)
    with pytest.raises(paid_run.PaidRunRefused, match="image"):
        gate.record()


def test_a_record_without_the_image_field_is_refused(gate, fresh_reads):
    record = gate.record()
    del record["container_digest"]
    assert "validate" in gate.refusal(gate.commit_record(record))


@pytest.mark.parametrize("value", ["canary-sweep:proto", "sha256:abc", ""])
def test_a_record_naming_a_tag_or_short_digest_is_refused(gate, fresh_reads, value):
    record = gate.record()
    record["container_digest"] = value
    assert "validate" in gate.refusal(gate.commit_record(record))


def test_a_launcher_file_for_another_container_refuses_in_words(gate, fresh_reads, monkeypatch):
    path = gate.open()

    def mismatch(*args, **kwargs):
        raise container.ContainerMismatch("written for container ffffffffffff, not this one (6b5b61fa964b)")
    monkeypatch.setattr(container, "container_digest", mismatch)
    assert "written for container" in gate.refusal(path)


def test_a_trial_records_the_image_it_ran_in_and_its_result_derives_from_that(tmp_path, monkeypatch):
    from tests.test_execute import _run

    _in_image(monkeypatch, IMAGE_X)
    _run(tmp_path / "run")
    trial_dir = next(path.parent for path in (tmp_path / "run").glob(f"*/{RESULTS_FILE}"))
    started = json.loads((trial_dir / EVENTS_FILE).read_text(encoding="utf-8").splitlines()[0])
    assert started["event_type"] == "trial_started"
    assert started["payload"]["container_digest"] == IMAGE_X
    result = json.loads((trial_dir / RESULTS_FILE).read_text(encoding="utf-8"))
    assert result["run_metadata"]["container_digest"] == IMAGE_X
    # Recomputed elsewhere (a host verify, say), the result still names the image the trial ran in.
    _in_image(monkeypatch, None)
    events = [json.loads(line) for line in (trial_dir / EVENTS_FILE).read_text(encoding="utf-8").splitlines()]
    assert execute.assemble_result.__module__ == "runner.execute"
    from runner.mock_slice import assemble_result
    assert assemble_result(events)["run_metadata"]["container_digest"] == IMAGE_X


def test_a_host_trial_keeps_a_null_digest_and_no_new_event_field(tmp_path, monkeypatch):
    from tests.test_execute import _run

    _in_image(monkeypatch, None)
    _run(tmp_path / "run")
    trial_dir = next(path.parent for path in (tmp_path / "run").glob(f"*/{RESULTS_FILE}"))
    started = json.loads((trial_dir / EVENTS_FILE).read_text(encoding="utf-8").splitlines()[0])
    assert "container_digest" not in started["payload"]
    assert json.loads((trial_dir / RESULTS_FILE).read_text(encoding="utf-8"))["run_metadata"]["container_digest"] is None
