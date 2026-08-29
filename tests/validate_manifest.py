#!/usr/bin/env python3
"""Local manifest validation; release CI uses aw-marketplace's canonical validator."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema

root = Path(__file__).resolve().parent.parent
manifest_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else root / "aw-app.json"
schema_path = root.parent / "aw-marketplace" / "schemas" / "aw-app.schema.json"
if not schema_path.is_file():
    raise SystemExit(f"canonical schema not found: {schema_path}")

manifest = json.loads(manifest_path.read_text())
jsonschema.validate(manifest, json.loads(schema_path.read_text()))
frontend = (manifest.get("contributes") or {}).get("frontend") or {}
bundle = frontend.get("bundle")
if bundle and not (manifest_path.parent / bundle).is_file():
    raise SystemExit(f"frontend bundle missing: {bundle}; run npm run build in ui/")
for window in (manifest.get("contributes") or {}).get("windows") or []:
    if not window["id"].startswith(f"{manifest['id']}."):
        raise SystemExit(f"window id is not namespaced: {window['id']}")
print("OK: manifest and referenced frontend bundle are valid")
