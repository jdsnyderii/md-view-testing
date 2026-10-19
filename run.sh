#!/bin/sh
# Run mdportal. Config file defines every root; mounts must satisfy its dir paths.
#
#   ./run.sh
#   CONFIG=./my-roots.yaml PORTAL=./docs SHARED=./lib ./run.sh
#   GITHUB_TOKEN=ghp_… ./run.sh
#
# Arbitrary layout: write a roots.yaml whose path: values you can mount, then
#   docker run --rm -p 8000:8000 \
#     -e MDPORTAL_CONFIG=/config/roots.yaml \
#     -v "$PWD/my-roots.yaml:/config/roots.yaml:ro" \
#     -v "$PWD/docs:/whatever/path/in/yaml:ro" \
#     -e GITHUB_TOKEN -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
#     mdportal

set -e
cd "$(dirname "$0")"

IMAGE="${IMAGE:-mdportal}"
PORT="${PORT:-8000}"
CONFIG="${CONFIG:-$PWD/roots.yaml}"
PORTAL="${PORTAL:-$PWD/sample/portal}"
SHARED="${SHARED:-$PWD/sample/shared}"

docker build -t "$IMAGE" .

# Resolve to absolute paths for Docker Desktop / remote engines
CONFIG="$(cd "$(dirname "$CONFIG")" && pwd)/$(basename "$CONFIG")"
PORTAL="$(cd "$PORTAL" && pwd)"
SHARED="$(cd "$SHARED" && pwd)"

exec docker run --rm -p "$PORT:8000" \
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
