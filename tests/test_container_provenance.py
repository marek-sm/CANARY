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
