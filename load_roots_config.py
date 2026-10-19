"""Load roots.yaml into LinkML-generated Pydantic models (type-designated subclasses)."""
from __future__ import annotations

from pathlib import Path

import yaml

from roots_models import RootsConfig


def load_roots_config(path: str | Path) -> RootsConfig:
    """Parse and validate roots.yaml.

    YAML maps use the key as the root name; LinkML models that as RootSpec.name.
    Inject the key before validation (inlined-dict convention).
    Concrete kind is selected by the type designator (dir|github|http|s3).
    """
    data = yaml.safe_load(Path(path).read_text())
    roots = data.get("roots") or {}
    if isinstance(roots, dict):
        data["roots"] = {
            name: {**spec, "name": spec.get("name", name)}
            for name, spec in roots.items()
            if isinstance(spec, dict)
        }
    return RootsConfig.model_validate(data)


if __name__ == "__main__":
    import sys

    cfg = load_roots_config(sys.argv[1] if len(sys.argv) > 1 else "roots.yaml")
    print("home:", cfg.home)
    for name, spec in cfg.roots.items():
        print(f"  ${name}: type={spec.type} class={type(spec).__name__}")
