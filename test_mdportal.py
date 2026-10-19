#!/usr/bin/env python3
"""Smoke-test mdportal: validate roots config, boot app, fetch pages."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

def step(msg: str) -> None:
    print(f"→ {msg}")


def main() -> int:
    config = Path(os.environ.get("MDPORTAL_CONFIG", ROOT / "roots.test.yaml"))
    if not config.is_file():
        print(f"FAIL: config not found: {config}")
        return 1

    # 1) LinkML/Pydantic validation
    step(f"validate {config.name}")
    from load_roots_config import load_roots_config
    from pydantic import ValidationError

    try:
        cfg = load_roots_config(config)
    except ValidationError as e:
        print("FAIL — roots validation")
        print(e)
        return 1

    home_root = cfg.home.split("/", 1)[0]
    if home_root not in cfg.roots:
        print(f"FAIL — home root {home_root!r} missing")
        return 1

    for name, spec in cfg.roots.items():
        print(f"   ${name}: type={spec.type} → {type(spec).__name__}")

    # 2) Boot Flask app with this config
    step("create_app")
    os.environ["MDPORTAL_CONFIG"] = str(config)
    from app import create_app

    app = create_app(str(config))
    client = app.test_client()

    # 3) Home redirects to view
    step("GET /")
    r = client.get("/")
    if r.status_code not in (301, 302):
        print(f"FAIL — / status {r.status_code}")
        return 1
    loc = r.headers.get("Location", "")
    print(f"   redirect → {loc}")

    # 4) Render home doc
    step("GET /view/portalRoot/index.md")
    r = client.get("/view/portalRoot/index.md")
    if r.status_code != 200:
        print(f"FAIL — view status {r.status_code}: {r.data[:300]!r}")
        return 1
    body = r.data.decode("utf-8", errors="replace")
    if "Portal home" not in body and "portal" not in body.lower():
        pass
    if "<main" not in body and "<main>" not in body:
        print("FAIL — no <main> in response")
        return 1
    print(f"   ok ({len(body)} bytes)")

    # 5) Guide page
    step("GET /view/portalRoot/guide/index.md")
    r = client.get("/view/portalRoot/guide/index.md")
    if r.status_code != 200:
        print(f"FAIL — guide status {r.status_code}")
        return 1
    print(f"   ok ({len(r.data)} bytes)")

    # 6) Missing doc → 404
    step("GET missing doc (expect 404)")
    r = client.get("/view/portalRoot/nope.md")
    if r.status_code != 404:
        print(f"FAIL — expected 404, got {r.status_code}")
        return 1
    print("   ok 404")

    print()
    print("PASS — mdportal smoke test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
