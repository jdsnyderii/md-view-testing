# mdportal

Markdown viewer with named roots (`dir`, `github`, `http`, `s3`).

## Mount contract

**The image does not define your roots.** `roots.yaml` does.

1. Set `MDPORTAL_CONFIG` to a config file in the container (default `/config/roots.yaml`).
2. For each `type: dir` root, bind-mount a host directory at that entry's `path`.
3. For `github` / `http` / `s3`, pass credentials in the environment — no binds required.

### Default demo

```bash
./run.sh
# or: make docker
```

### Local (no Docker)

```bash
make test          # validate roots + HTTP smoke test
make run           # Flask on :5000 using roots.test.yaml
make validate CONFIG=roots.yaml
```

### Docs syntax

```
{{ fenced_include("$portalRoot/path", "python") }}
{{ include("$currentDir/partial.md") }}
```

See `AGENT.md` for agent-oriented notes.
