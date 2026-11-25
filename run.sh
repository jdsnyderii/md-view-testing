#!/bin/sh
# Run mdportal. Config file defines every root; mounts must satisfy its dir paths.
#
#   ./run.sh
#   CONFIG=./my-roots.yaml PORTAL=./docs SHARED=./lib ./run.sh
#   PYTHON_VERSION=3.12 APP_PORT=9000 PORT=9000 ./run.sh
#   GITHUB_TOKEN=ghp_… ./run.sh
#
# Relative CONFIG, PORTAL, and SHARED paths are resolved from the caller's
# working directory. Defaults are relative to this script.
# Arbitrary layout: write a roots.yaml whose path: values you can mount, then
#   docker run --rm -p 127.0.0.1:8000:8000 \
#     -e MDPORTAL_CONFIG=/config/roots.yaml \
#     -v "$PWD/my-roots.yaml:/config/roots.yaml:ro" \
#     -v "$PWD/docs:/whatever/path/in/yaml:ro" \
#     -e GITHUB_TOKEN -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
#     mdportal

set -e
CALLER_DIR=$(pwd)
SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd)
cd "$SCRIPT_DIR"

IMAGE="${IMAGE:-mdportal}"
PYTHON_VERSION="${PYTHON_VERSION:-3.13}"
APP_PORT="${APP_PORT:-8000}"
PORT="${PORT:-$APP_PORT}"
# Docker expects an IP address here; 127.0.0.1 is localhost.
HOST_BIND_ADDRESS="${HOST_BIND_ADDRESS:-127.0.0.1}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-2}"
# Gunicorn must listen on the container interface for bridge port forwarding.
GUNICORN_BIND_ADDRESS="${GUNICORN_BIND_ADDRESS:-0.0.0.0}"
APP_UID="${APP_UID:-10001}"
CONFIG="${CONFIG:-$SCRIPT_DIR/roots.yaml}"
PORTAL="${PORTAL:-$SCRIPT_DIR/sample/portal}"
SHARED="${SHARED:-$SCRIPT_DIR/sample/shared}"

absolute_file_path() {
  case "$1" in
    /*) path=$1 ;;
    *) path=$CALLER_DIR/$1 ;;
  esac
  directory=$(CDPATH= cd "$(dirname "$path")" && pwd) || return 1
  printf '%s/%s\n' "$directory" "$(basename "$path")"
}

absolute_dir_path() {
  case "$1" in
    /*) path=$1 ;;
    *) path=$CALLER_DIR/$1 ;;
  esac
  CDPATH= cd "$path" && pwd
}

# Resolve to absolute paths for Docker Desktop / remote engines.
CONFIG=$(absolute_file_path "$CONFIG")
PORTAL=$(absolute_dir_path "$PORTAL")
SHARED=$(absolute_dir_path "$SHARED")

docker build \
  --build-arg "PYTHON_VERSION=$PYTHON_VERSION" \
  --build-arg "APP_PORT=$APP_PORT" \
  --build-arg "GUNICORN_WORKERS=$GUNICORN_WORKERS" \
  --build-arg "GUNICORN_BIND_ADDRESS=$GUNICORN_BIND_ADDRESS" \
  --build-arg "APP_UID=$APP_UID" \
  -t "$IMAGE" .

case "$HOST_BIND_ADDRESS" in
  0.0.0.0|127.0.0.1|::|::1) CONNECTION_HOST=localhost ;;
  *) CONNECTION_HOST=$HOST_BIND_ADDRESS ;;
esac
printf 'Open http://%s:%s/ in your browser.\n' "$CONNECTION_HOST" "$PORT"

exec docker run --rm -p "$HOST_BIND_ADDRESS:$PORT:$APP_PORT" \
  -e MDPORTAL_CONFIG=/config/roots.yaml \
  -v "$CONFIG:/config/roots.yaml:ro" \
  -v "$PORTAL:/data/portal:ro" \
  -v "$SHARED:/data/shared:ro" \
  ${GITHUB_TOKEN:+-e GITHUB_TOKEN} \
  ${AWS_ACCESS_KEY_ID:+-e AWS_ACCESS_KEY_ID} \
  ${AWS_SECRET_ACCESS_KEY:+-e AWS_SECRET_ACCESS_KEY} \
  ${AWS_DEFAULT_REGION:+-e AWS_DEFAULT_REGION} \
  ${DOCS_TOKEN:+-e DOCS_TOKEN} \
  "$IMAGE"
