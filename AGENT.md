# mdportal

Flask Markdown viewer. Docs use `{{ fenced_include("$root/path") }}` / `{{ include(...) }}` from named roots. `$currentDir` = dir of the current doc.

## roots.yaml

| type | required | mounts |
|------|----------|--------|
| `dir` | `path` | bind host dir at `path` |
| `github` | `repo` | env `GITHUB_TOKEN` optional |
| `http` | `url` | headers / tokens via env |
| `s3` | `bucket` | boto3 env/IAM |

`${ENV}` expanded; empty dropped. Schema: `roots.linkml.yaml` → `sh regenerate_models.sh` → `roots_models.py`. Validate: `make validate` / `make test`.

## Docker

App reads only `MDPORTAL_CONFIG` (default `/config/roots.yaml`). Mount that file, then mount each dir `path:`. Remote roots need env only — no binds. Shipped `/data/portal` + `/data/shared` are example paths, not required.

```bash
make test          # local smoke (roots.test.yaml + sample/)
./run.sh           # docker demo
```
