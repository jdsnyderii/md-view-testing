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

Mounts the example `roots.yaml` plus `sample/portal` → `/data/portal` and `sample/shared` → `/data/shared`.

### Your own trees (same path layout as the example)

```bash
CONFIG=./roots.yaml PORTAL=./docs SHARED=./lib ./run.sh
```

### Fully custom layout

Write any `roots.yaml`, mount it, and mount each dir `path:`:

```bash
docker build -t mdportal .
docker run --rm -p 8000:8000 \
  -e MDPORTAL_CONFIG=/config/roots.yaml \
  -v "$PWD/my-roots.yaml:/config/roots.yaml:ro" \
  -v "$PWD/docs:/srv/docs:ro" \
  -v "$PWD/shared:/srv/shared:ro" \
  -e GITHUB_TOKEN \
  mdportal
```

with `my-roots.yaml` using `path: /srv/docs` and `path: /srv/shared` (or whatever you mount).

## Local (no Docker)

```bash
make test          # validate roots + HTTP smoke test
make run           # Flask on :5000 using roots.test.yaml
make validate CONFIG=roots.yaml
```

## Docs syntax

```
{{ fenced_include("$portalRoot/path", "python") }}
{{ include("$currentDir/partial.md") }}
```
