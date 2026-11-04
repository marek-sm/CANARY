#!/bin/sh
# Run one CANARY command in the sweep image, tools still sandboxed (prototype).
#
# PROTOTYPE for decision 0028 item 9, which the project lead hasn't taken. Decision
# 0025 item 12 keeps the official sweep on the host. Steps: docs/SWEEP_CONTAINER.md.
#
# This is host-side operator tooling, like the Makefile: it starts docker, never a
# tool. It is POSIX sh so a Mac needs nothing but Docker to run it.
#
# Options that loosen Docker's defaults (each measured as necessary; see the report):
#   --security-opt seccomp=docker/sweep/seccomp-bwrap.json
#   --security-opt systempaths=unconfined
#   --security-opt apparmor=unconfined   only with --apparmor-unconfined, for hosts
#                                        whose Docker applies AppArmor (Ubuntu CI)
# Options that tighten: --user 10001:10001 --cap-drop ALL no-new-privileges
#   --read-only --tmpfs /tmp(noexec) --pids-limit, and --network none by default.
#
# The image binding: create the container by image ID, ask the daemon which image
# that container runs, write both into /run/canary/container.json (read-only), and
# only then start it. runner/container.py refuses a file for another container.
#
# Usage:
#   docker/sweep/launch.sh [--image REF] [--checkout DIR] [--results DIR]
#       [--writable-protocol] [--key-file FILE] [--network none|egress]
#       [--name NAME] [--apparmor-unconfined] [--writable-checkout] -- COMMAND...
#
#   --results DIR   host directory mounted read-write at /app/results/development
#                   (default: the checkout's own results/development)
#   --network egress  the runner joins an --internal network whose only peer is
#                   docker/sweep/egress_proxy.py, which forwards TLS for
#                   api.anthropic.com:443 and nothing else. Tools have no network
#                   in either mode (bwrap --unshare-net).
#   --writable-checkout  mount the checkout read-write. Only for the sandbox tests:
#                   their controls write the repository unsandboxed, so on a
#                   read-only checkout a refusal would prove nothing. Never for a
#                   grid, a record, or a paid run.
#   --key-file FILE mounted read-only at /run/secrets/provider.env for the outer
#                   runner. Never pass a key with -e.
set -eu

LAUNCHER_VERSION="sweep-launch-0.2.0"
HERE=$(cd "$(dirname "$0")" && pwd)
IMAGE="canary-sweep:local"
CHECKOUT=$(cd "$HERE/../.." && pwd)
RESULTS=""
WRITABLE_PROTOCOL=0
KEY_FILE=""
NETWORK="none"
NAME=""
APPARMOR=0
CHECKOUT_MODE=",readonly"

die() { echo "launch.sh: $*" >&2; exit 2; }

while [ $# -gt 0 ]; do
  case "$1" in
    --image) IMAGE=$2; shift 2 ;;
    --checkout) CHECKOUT=$(cd "$2" && pwd); shift 2 ;;
    --results) RESULTS=$2; shift 2 ;;
    --writable-protocol) WRITABLE_PROTOCOL=1; shift ;;
    --key-file) KEY_FILE=$2; shift 2 ;;
    --network) NETWORK=$2; shift 2 ;;
    --name) NAME=$2; shift 2 ;;
    --apparmor-unconfined) APPARMOR=1; shift ;;
    --writable-checkout) CHECKOUT_MODE=""; shift ;;
    --) shift; break ;;
    *) die "unknown option $1 (put the command after --)" ;;
  esac
done
[ $# -gt 0 ] || die "no command after --"
case "$NETWORK" in none|egress) ;; *) die "--network is none or egress, not $NETWORK" ;; esac
case "$IMAGE" in *[!A-Za-z0-9._:/@-]*) die "image reference holds an unexpected character" ;; esac
case "$NAME" in *[!A-Za-z0-9_.-]*) die "container name holds an unexpected character" ;; esac

[ -n "$RESULTS" ] || RESULTS="$CHECKOUT/results/development"
mkdir -p "$RESULTS"
RESULTS=$(cd "$RESULTS" && pwd)
SECCOMP="$HERE/seccomp-bwrap.json"
[ -f "$SECCOMP" ] || die "missing $SECCOMP"
if [ -n "$KEY_FILE" ]; then
  [ -f "$KEY_FILE" ] || die "no key file at $KEY_FILE"
  KEY_FILE=$(cd "$(dirname "$KEY_FILE")" && pwd)/$(basename "$KEY_FILE")
fi

IMAGE_ID=$(docker image inspect "$IMAGE" --format '{{.Id}}') || die "no image $IMAGE; build it with make sweep-image"
case "$IMAGE_ID" in sha256:????????????????????????????????????????????????????????????????) ;;
  *) die "the daemon reported $IMAGE_ID for $IMAGE, which isn't a sha256 digest" ;; esac

STATE=$(mktemp -d "${TMPDIR:-/tmp}/canary-container-XXXXXX")
chmod 755 "$STATE"
CID=""
PROXY=""
NET_INTERNAL=""
NET_EGRESS=""
cleanup() {
  [ -z "$CID" ] || docker rm --force "$CID" >/dev/null 2>&1 || true
  [ -z "$PROXY" ] || docker rm --force "$PROXY" >/dev/null 2>&1 || true
  [ -z "$NET_INTERNAL" ] || docker network rm "$NET_INTERNAL" >/dev/null 2>&1 || true
  [ -z "$NET_EGRESS" ] || docker network rm "$NET_EGRESS" >/dev/null 2>&1 || true
  rm -rf "$STATE"
}
trap cleanup EXIT
trap 'exit 130' INT TERM HUP

NETWORK_OPTS="--network none"
if [ "$NETWORK" = egress ]; then
  TAG="canary-sweep-$$-$(date +%s)"
  NET_INTERNAL="$TAG-internal"
  NET_EGRESS="$TAG-egress"
  docker network create --internal "$NET_INTERNAL" >/dev/null
  docker network create "$NET_EGRESS" >/dev/null
  # The proxy runs in the same pinned image, from the checkout's own file, read-only.
  PROXY=$(docker create --user 10001:10001 --cap-drop ALL --security-opt no-new-privileges --read-only \
      --pids-limit 64 --network "$NET_EGRESS" \
      --mount "type=bind,src=$HERE/egress_proxy.py,dst=/proxy/egress_proxy.py,readonly" \
      "$IMAGE_ID" python /proxy/egress_proxy.py)
  docker network connect "$NET_INTERNAL" "$PROXY"
  docker start "$PROXY" >/dev/null
  PROXY_IP=$(docker container inspect "$PROXY" \
      --format "{{(index .NetworkSettings.Networks \"$NET_INTERNAL\").IPAddress}}")
  [ -n "$PROXY_IP" ] || die "the egress proxy has no address on $NET_INTERNAL"
  # The provider name resolves to the proxy; nothing else resolves (DNS at a dead address).
  NETWORK_OPTS="--network $NET_INTERNAL --add-host api.anthropic.com:$PROXY_IP --dns 127.0.0.1"
fi

# "$@" is the command. Prepend the image, then every option, so the command stays last.
set -- "$IMAGE_ID" "$@"
set -- \
  --user 10001:10001 \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --security-opt "seccomp=$SECCOMP" \
  --security-opt systempaths=unconfined \
  --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=256m \
  --pids-limit 512 \
  --mount "type=bind,src=$CHECKOUT,dst=/app$CHECKOUT_MODE" \
  --mount "type=bind,src=$RESULTS,dst=/app/results/development" \
  --mount "type=bind,src=$STATE,dst=/run/canary,readonly" \
  --label "org.canary.launcher=$LAUNCHER_VERSION" \
  "$@"
[ "$APPARMOR" = 0 ] || set -- --security-opt apparmor=unconfined "$@"
[ "$WRITABLE_PROTOCOL" = 0 ] || set -- --mount "type=bind,src=$CHECKOUT/protocol,dst=/app/protocol" "$@"
[ -z "$KEY_FILE" ] || set -- --mount "type=bind,src=$KEY_FILE,dst=/run/secrets/provider.env,readonly" "$@"
[ -z "$NAME" ] || set -- --name "$NAME" "$@"
# shellcheck disable=SC2086 # NETWORK_OPTS is a fixed, checked word list
set -- $NETWORK_OPTS "$@"

# Created by ID, so a tag moved meanwhile can't change the image.
CID=$(docker create "$@" 2>"$STATE/create.err") || { cat "$STATE/create.err" >&2; die "docker create failed"; }
RUNNING=$(docker container inspect "$CID" --format '{{.Image}}')
[ "$RUNNING" = "$IMAGE_ID" ] || die "the container runs $RUNNING, not $IMAGE_ID"
printf '{"container_id": "%s", "image_digest": "%s", "image_ref": "%s", "launcher": "%s", "network": "%s"}\n' \
  "$CID" "$RUNNING" "$IMAGE" "$LAUNCHER_VERSION" "$NETWORK" > "$STATE/container.json"
chmod 644 "$STATE/container.json"
cat "$STATE/container.json" >&2
set +e
docker start --attach "$CID"
STATUS=$?
set -e
exit "$STATUS"
