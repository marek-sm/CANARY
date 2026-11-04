"""docker/sweep/launch.sh (prototype) against a stub ``docker``: the options it passes,
the image binding it writes, and its refusals. No daemon and no container run here;
the in-image evidence is ``make sweep-container-check``."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LAUNCH = ROOT / "docker" / "sweep" / "launch.sh"
IMAGE_ID = "sha256:" + "a" * 64
OTHER_ID = "sha256:" + "b" * 64
CID = "c" * 64

STUB = r"""#!/bin/sh
# Records every call; answers like a daemon would.
printf '%s\n' "$*" >> "$STUB_LOG"
case "$1 $2" in
  "image inspect") echo "$STUB_IMAGE_ID" ;;
  "container inspect")
    case "$*" in
      *IPAddress*) echo 172.30.0.2 ;;
      *) echo "$STUB_RUNNING" ;;
    esac ;;
  "network create"|"network connect"|"network rm") ;;
  "start --attach")
    dir=$(grep '^create .*dst=/run/canary' "$STUB_LOG" | tail -1 | sed 's/.*src=\([^,]*\),dst=\/run\/canary.*/\1/')
    cp "$dir/container.json" "$STUB_SEEN" ;;
  "start "*) ;;
  "create "*)
    case "$*" in *egress_proxy.py*) echo proxy-id ;; *) echo "$STUB_CID" ;; esac ;;
  "rm --force") ;;
esac
exit 0
"""


@pytest.fixture
def stub(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "docker").write_text(STUB, encoding="utf-8")
    (bin_dir / "docker").chmod(0o755)
    env = {"PATH": f"{bin_dir}:{os.defpath}", "STUB_LOG": str(tmp_path / "calls"), "STUB_SEEN": str(tmp_path / "seen"),
           "STUB_IMAGE_ID": IMAGE_ID, "STUB_RUNNING": IMAGE_ID, "STUB_CID": CID, "TMPDIR": str(tmp_path)}
    checkout = tmp_path / "checkout"
    shutil.copytree(ROOT / "docker", checkout / "docker")
    (checkout / "protocol").mkdir()

    def run(*args, **overrides):
        done = subprocess.run(["sh", str(checkout / "docker" / "sweep" / "launch.sh"), *args],
                              env={**env, **overrides}, capture_output=True, text=True, timeout=30)
        calls = (tmp_path / "calls").read_text(encoding="utf-8").splitlines() if (tmp_path / "calls").exists() else []
        seen = tmp_path / "seen"
        return done, calls, json.loads(seen.read_text(encoding="utf-8")) if seen.exists() else None
    run.checkout = checkout
    run.tmp = tmp_path
    return run


def _create(calls):
    return next(call for call in calls if call.startswith("create ") and "egress_proxy.py" not in call)


def test_the_runner_gets_the_measured_option_set_and_the_image_by_id(stub):
    done, calls, _ = stub("--", "make", "sandbox-check")
    assert done.returncode == 0, done.stderr
    create = _create(calls)
    for option in ("--user 10001:10001", "--cap-drop ALL", "--security-opt no-new-privileges", "--read-only",
                   "--security-opt systempaths=unconfined", "--pids-limit 512", "--network none",
                   "--tmpfs /tmp:rw,nosuid,nodev,noexec,size=256m", "dst=/app,readonly", "dst=/run/canary,readonly"):
        assert option in create
    assert "seccomp=" + str(stub.checkout / "docker" / "sweep" / "seccomp-bwrap.json") in create
    assert create.endswith(f"{IMAGE_ID} make sandbox-check")
    for loosening in ("--privileged", "apparmor=unconfined", "seccomp=unconfined", "--cap-add", "docker.sock"):
        assert loosening not in create


def test_the_container_file_names_the_daemon_reported_image_and_this_container(stub):
    done, _, seen = stub("--", "true")
    assert done.returncode == 0, done.stderr
    assert seen == {"container_id": CID, "image_digest": IMAGE_ID, "image_ref": "canary-sweep:local",
                    "launcher": "sweep-launch-0.2.0", "network": "none"}


def test_a_container_running_another_image_never_starts(stub):
    done, calls, seen = stub("--", "true", STUB_RUNNING=OTHER_ID)
    assert done.returncode != 0
    assert "not " + IMAGE_ID in done.stderr
    assert not any(call.startswith("start") for call in calls)
    assert seen is None
    assert f"rm --force {CID}" in calls


@pytest.mark.parametrize("reported", ["", "canary-sweep:local", "sha256:abc"])
def test_an_image_id_that_isnt_a_digest_refuses(stub, reported):
    done, calls, _ = stub("--", "true", STUB_IMAGE_ID=reported)
    assert done.returncode != 0
    assert not any(call.startswith("create") for call in calls)


def test_only_the_sandbox_tests_option_makes_the_checkout_writable(stub):
    done, calls, _ = stub("--writable-checkout", "--", "make", "sandbox-check")
    assert done.returncode == 0, done.stderr
    create = _create(calls)
    assert f"src={stub.checkout},dst=/app " in create + " "
    assert "dst=/app,readonly" not in create


def test_egress_puts_the_runner_on_an_internal_network_whose_only_peer_is_the_proxy(stub):
    done, calls, seen = stub("--network", "egress", "--", "true")
    assert done.returncode == 0, done.stderr
    internal = next(call for call in calls if call.startswith("network create --internal")).split()[-1]
    proxy = next(call for call in calls if call.startswith("create ") and "egress_proxy.py" in call)
    assert "--cap-drop ALL" in proxy and "--read-only" in proxy and "--user 10001:10001" in proxy
    assert f"network connect {internal} proxy-id" in calls
    create = _create(calls)
    assert f"--network {internal} --add-host api.anthropic.com:172.30.0.2 --dns 127.0.0.1" in create
    assert seen["network"] == "egress"
    assert f"network rm {internal}" in calls
    assert "rm --force proxy-id" in calls


def test_the_key_file_is_mounted_read_only_never_passed_as_a_variable(stub):
    key = stub.tmp / "provider.env"
    key.write_text("ANTHROPIC_API_KEY=not-a-key\n", encoding="utf-8")
    done, calls, _ = stub("--key-file", str(key), "--", "true")
    assert done.returncode == 0, done.stderr
    create = _create(calls)
    assert f"src={key},dst=/run/secrets/provider.env,readonly" in create
    assert " -e " not in create and "--env" not in create and "not-a-key" not in create


@pytest.mark.parametrize("args", [["--network", "bridge", "--", "true"], ["--network", "host", "--", "true"],
                                  ["--image", "x;rm", "--", "true"], ["--name", "a b", "--", "true"], []])
def test_bad_arguments_refuse_before_any_container(stub, args):
    done, calls, _ = stub(*args)
    assert done.returncode != 0
    assert not any(call.startswith("create") for call in calls)


def test_the_launcher_and_check_are_posix_sh():
    for name in ("launch.sh", "check.sh"):
        assert subprocess.run(["sh", "-n", str(ROOT / "docker" / "sweep" / name)]).returncode == 0


def test_the_ledger_is_mounted_only_when_named_so_a_paid_command_otherwise_refuses(stub):
    done, calls, _ = stub("--", "true")
    assert "/home/canary/.canary" not in _create(calls)
    ledger = stub.tmp / "ledger"
    ledger.mkdir()
    done, calls, _ = stub("--ledger", str(ledger), "--", "true")
    assert done.returncode == 0, done.stderr
    assert f"src={ledger},dst=/home/canary/.canary" in [c for c in calls if c.startswith("create ")][-1]
