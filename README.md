# mdportal

Markdown viewer with named roots (`dir`, `github`, `http`, `s3`).

## Mount contract

**The image does not define your roots.** `roots.yaml` does.

1. Set `MDPORTAL_CONFIG` to a config file in the container (default `/config/roots.yaml`).
2. For each `type: dir` root, bind-mount a host directory at that entry’s `path`.
3. For `github` / `http` / `s3`, pass credentials in the environment — no binds required.

Example config (shipped as `/config/roots.yaml`):

```yaml
home: portalRoot/index.md
roots:
  portalRoot:
    type: dir
    path: /data/portal
  sharedRoot:
    type: dir
    path: /data/shared
  flaskRepo:
    type: github
    repo: pallets/flask
    ref: main
    token: ${GITHUB_TOKEN}
```

### Default demo

```bash
./run.sh
# or: make docker
```

The image contains the application and its runtime dependencies. This script mounts the example `roots.yaml`, `sample/portal` → `/data/portal`, and `sample/shared` → `/data/shared`.

### Build options

The Dockerfile build arguments select the Python image tag, container port, Gunicorn bind address and worker count, and runtime UID. Defaults are `PYTHON_VERSION=3.13`, `APP_PORT=8000`, `GUNICORN_BIND_ADDRESS=0.0.0.0`, `GUNICORN_WORKERS=2`, and `APP_UID=10001`. The final image runs as this numeric non-root UID and matching GID; builds reject zero or non-numeric UIDs. The dedicated account has a non-login shell and a private writable home for Gunicorn.

```bash
docker build \
  --build-arg PYTHON_VERSION=3.12 \
  --build-arg APP_PORT=9000 \
  --build-arg GUNICORN_BIND_ADDRESS=0.0.0.0 \
  --build-arg GUNICORN_WORKERS=4 \
  --build-arg APP_UID=10002 \
  -t mdportal .
docker run --rm -p 127.0.0.1:9000:9000 \
  -e MDPORTAL_CONFIG=/config/roots.yaml \
  -v "$PWD/roots.yaml:/config/roots.yaml:ro" \
  -v "$PWD/sample/portal:/data/portal:ro" \
  -v "$PWD/sample/shared:/data/shared:ro" \
  mdportal
```

`run.sh` forwards those build settings from environment variables. `APP_PORT` sets the container listener, and `PORT` sets the host port (defaulting to `APP_PORT`). `GUNICORN_BIND_ADDRESS` sets Gunicorn's container-side listener (`0.0.0.0` by default so Docker can forward traffic); `HOST_BIND_ADDRESS` sets the published host address (`127.0.0.1`, localhost, by default):

```bash
PYTHON_VERSION=3.12 APP_PORT=9000 PORT=9000 GUNICORN_WORKERS=4 APP_UID=10002 ./run.sh
# To override the host-side bind: HOST_BIND_ADDRESS=0.0.0.0 ./run.sh
```

The bind settings are separate: Gunicorn must listen on the container interface for Docker's bridge forwarding, while the host-side published port remains localhost-only by default. Gunicorn's INFO-level startup messages are suppressed by default so its container-side bind is not mistaken for the browser URL; warnings and errors remain visible. `run.sh` prints the URL to open after the image builds.

Docker uses a pinned official `uv` image in its build stage and syncs production dependencies with `uv.lock` before copying application source. LinkML is a runtime dependency and is included in the image; development dependencies and the `uv` executable are not copied into the final runtime stage.

### Your own trees (same path layout as the example)

Relative `CONFIG`, `PORTAL`, and `SHARED` values are resolved from the directory where you invoke `run.sh`; the defaults are relative to the script.

```bash
CONFIG=./roots.yaml PORTAL=./docs SHARED=./lib ./run.sh
```

### Fully custom layout

Write any `roots.yaml`, mount it, and mount each dir `path:`:

```bash
docker build -t mdportal .
docker run --rm -p 127.0.0.1:8000:8000 \
  -e MDPORTAL_CONFIG=/config/roots.yaml \
  -v "$PWD/my-roots.yaml:/config/roots.yaml:ro" \
  -v "$PWD/docs:/srv/docs:ro" \
  -v "$PWD/shared:/srv/shared:ro" \
  -e GITHUB_TOKEN \
  mdportal
```

with `my-roots.yaml` using `path: /srv/docs` and `path: /srv/shared` (or whatever you mount).

## Local (no Docker)

Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/), then create the locked project environment:

```bash
uv sync --locked
uv lock --check
make validate      # validate roots.test.yaml
make test          # validation + HTTP smoke test
make models        # regenerate roots_models.py with LinkML
make run           # Flask on :5000 using roots.test.yaml
```

`pyproject.toml` declares the project and its direct runtime dependencies; `uv.lock` records the resolved versions used by local commands and Docker. After changing dependencies in `pyproject.toml`, run `uv lock` and commit both files. Targets that accept a config path can be run with, for example, `make validate CONFIG=roots.yaml`.

## Docs syntax

```
{{ fenced_include("$portalRoot/path", "python") }}
{{ include("$currentDir/partial.md") }}
```
