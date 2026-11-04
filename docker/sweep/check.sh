#!/bin/sh
# make sweep-container-check: decision 0028 item 9's checks inside the sweep image (prototype).
#
# PROTOTYPE for a decision the project lead hasn't taken; decision 0025 item 12 keeps
# the host run. Steps and what to do when one fails: docs/SWEEP_CONTAINER.md.
#
# Runs, each in a fresh container from the same image, and stops at the first failure:
#   1 preflight      the daemon, the image's platform, and file sharing for uid 10001
#   2 sandbox        make sandbox-check (checkout writable, see launch.sh), no network
#   3 redteam        tests/redteam/, no network
#   4 egress         docker/sweep/egress_probe.py under --network egress
#   5 grid           the full mock grid, then verify, read-only checkout, no network
#   6 kill/resume    a second grid killed with SIGKILL part-way, resumed, verified, and
#                    compared with step 5 by docker/sweep/outcome_digest.py
# The one live smoke (make live-smoke) is NOT here: it spends, needs the lead's key,
# and is run by hand afterwards.
#
# Provider contact: none, except step 4's single TLS handshake to api.anthropic.com
# (no request, no key). --no-handshake skips it.
#
# Usage: sh docker/sweep/check.sh [--image REF] [--no-handshake] [--apparmor-unconfined]
#        [--kill-after N] [--keep]
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
CHECKOUT=$(cd "$HERE/../.." && pwd)
IMAGE="canary-sweep:local"
PROBE_ARGS=""
LAUNCH_ARGS=""
KILL_AFTER=30
KEEP=0
while [ $# -gt 0 ]; do
  case "$1" in
    --image) IMAGE=$2; shift 2 ;;
    --no-handshake) PROBE_ARGS="--no-handshake"; shift ;;
    --apparmor-unconfined) LAUNCH_ARGS="--apparmor-unconfined"; shift ;;
    --kill-after) KILL_AFTER=$2; shift 2 ;;
    --keep) KEEP=1; shift ;;
    *) echo "check.sh: unknown option $1" >&2; exit 2 ;;
  esac
done

STAMP=$(date +%Y%m%dT%H%M%S)
RUN_HOST="$CHECKOUT/results/development/sweep-container-check-$STAMP"
RUN="/app/results/development/sweep-container-check-$STAMP"
KILLED_NAME="canary-sweep-kill-$$"
STEP="setup"
fail() {
  echo "" >&2
  echo "sweep-container-check: FAILED at step $STEP: $*" >&2
  echo "See docs/SWEEP_CONTAINER.md, 'If a step fails'. Results kept in $RUN_HOST" >&2
  exit 1
}
launch() { sh "$HERE/launch.sh" --image "$IMAGE" --checkout "$CHECKOUT" $LAUNCH_ARGS "$@"; }
say() { echo ""; echo "== step $STEP"; }

STEP="1 preflight"; say
docker info --format 'daemon {{.ServerVersion}} on {{.OperatingSystem}} {{.Architecture}}, kernel {{.KernelVersion}}, security {{.SecurityOptions}}, cgroup v{{.CgroupVersion}}' \
  || fail "docker isn't reachable; start Docker Desktop"
SERVER_ARCH=$(docker version --format '{{.Server.Arch}}')
IMAGE_ID=$(docker image inspect "$IMAGE" --format '{{.Id}}' 2>/dev/null) || fail "no image $IMAGE; run make sweep-image"
IMAGE_PLATFORM=$(docker image inspect "$IMAGE" --format '{{.Os}}/{{.Architecture}}')
echo "image $IMAGE = $IMAGE_ID ($IMAGE_PLATFORM)"
[ "$IMAGE_PLATFORM" = "linux/$SERVER_ARCH" ] \
  || fail "the image is $IMAGE_PLATFORM but the daemon is linux/$SERVER_ARCH; an emulated image proves nothing here"
# uid 10001 must write results and read the checkout (Docker Desktop file sharing, Linux ownership).
launch -- sh -c "mkdir -p $RUN && touch $RUN/.write-probe && rm $RUN/.write-probe && test -r /app/pyproject.toml \
  && git -C /app rev-parse HEAD >/dev/null && echo 'file sharing: uid 10001 reads the checkout, writes results, runs git'" \
  || fail "uid 10001 can't write $RUN_HOST or read the checkout"

STEP="2 sandbox"; say
launch --writable-checkout -- make sandbox-check || fail "make sandbox-check failed in the image"

STEP="3 redteam"; say
launch --writable-checkout -- python -m pytest -q -p no:cacheprovider tests/redteam/ || fail "tests/redteam/ failed in the image"

STEP="4 egress"; say
launch --network egress -- python docker/sweep/egress_probe.py $PROBE_ARGS || fail "the egress probe found reach it shouldn't, or none it should"

STEP="5 grid"; say
launch -- sh -c "python -m runner.grid_dev mock --out $RUN/grid && python -m runner.grid_dev verify $RUN/grid" \
  || fail "the full mock grid didn't run and verify"

STEP="6 kill/resume"; say
launch --name "$KILLED_NAME" -- python -m runner.grid_dev mock --out "$RUN/killed" >"$RUN_HOST/killed-first.log" 2>&1 &
LAUNCHER=$!
while :; do
  DONE=$(find "$RUN_HOST/killed" -name results.jsonl 2>/dev/null | wc -l | tr -d ' ')
  [ "$DONE" -lt "$KILL_AFTER" ] || break
  kill -0 "$LAUNCHER" 2>/dev/null || fail "the grid to be killed ended before $KILL_AFTER trials (see killed-first.log)"
  sleep 1
done
docker kill --signal KILL "$KILLED_NAME" >/dev/null || fail "couldn't kill the running grid"
wait "$LAUNCHER" 2>/dev/null || true
DONE=$(find "$RUN_HOST/killed" -name results.jsonl | wc -l | tr -d ' ')
echo "killed with SIGKILL after $DONE of 90 trials had results"
[ "$DONE" -lt 90 ] || fail "the grid finished before the kill; raise nothing, lower --kill-after"
launch -- sh -c "python -m runner.grid_dev mock --out $RUN/killed --resume && python -m runner.grid_dev verify $RUN/killed" \
  || fail "the killed grid didn't resume and verify"
launch -- python docker/sweep/outcome_digest.py "$RUN/grid" "$RUN/killed" > "$RUN_HOST/outcomes.jsonl" \
  || fail "couldn't summarize the two grids"
cat "$RUN_HOST/outcomes.jsonl"
COUNT=$(sed 's/.*"outcome_sha256": "\([0-9a-f]*\)".*/\1/' "$RUN_HOST/outcomes.jsonl" | sort -u | wc -l | tr -d ' ')
[ "$COUNT" = 1 ] || fail "the killed-and-resumed grid found something the uninterrupted one didn't"
grep -c "\"container_digests\": \[\"$IMAGE_ID\"\]" "$RUN_HOST/outcomes.jsonl" | grep -qx 2 \
  || fail "a result doesn't carry this image's container_digest $IMAGE_ID"
grep -c '"trials": 90' "$RUN_HOST/outcomes.jsonl" | grep -qx 2 || fail "a grid doesn't hold 90 trials"

echo ""
echo "sweep-container-check: PASSED, image $IMAGE_ID ($IMAGE_PLATFORM)"
echo "Not run here: make live-smoke inside the image, which needs the lead's key (docs/SWEEP_CONTAINER.md)."
[ "$KEEP" = 1 ] || rm -rf "$RUN_HOST"
