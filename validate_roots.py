#!/usr/bin/env python3
"""Validate roots.yaml via LinkML-generated Pydantic models (designated types)."""
from __future__ import annotations

import sys
from pathlib import Path

from load_roots_config import load_roots_config


def main(path: Path) -> int:
    try:
        cfg = load_roots_config(path)
    except Exception as e:
        print("FAIL — pydantic validation")
        print(f"  {e}")
        return 1

    home_root = cfg.home.split("/", 1)[0]
    if home_root not in cfg.roots:
        print(f"FAIL — home root {home_root!r} is not defined in roots")
        return 1

    print(f"models: roots_models.py  (from roots.linkml.yaml via gen-pydantic)")
    print(f"data:   {path}")
    print(f"home:   {cfg.home}")
    for name, spec in cfg.roots.items():
        print(f"  ${name}: type={spec.type} → {type(spec).__name__}")
    print("PASS")
    return 0


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "roots.yaml"
    sys.exit(main(path))
