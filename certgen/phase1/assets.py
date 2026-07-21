"""Fail-closed validation for user-provided Kaggle asset mounts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


def validate_private_asset_mount(
    mount_root: str | Path,
    required_asset_ids: Iterable[str],
) -> dict[str, Any]:
    root = Path(mount_root)
    manifest_path = root / "asset_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"private asset manifest is missing: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = payload.get("files")
    if not isinstance(rows, list) or not rows:
        raise ValueError("private asset manifest must contain non-empty files rows")
    required = set(required_asset_ids)
    covered: set[str] = set()
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("private asset manifest row is not an object")
        relative = str(row.get("path", ""))
        path = PurePosixPath(relative)
        if path.is_absolute() or ".." in path.parts or "\\" in relative or relative in seen:
            raise ValueError(f"unsafe or duplicate private asset path: {relative}")
        candidate = root / relative
        if not candidate.is_file() or candidate.is_symlink():
            raise FileNotFoundError(f"private asset file is missing or symlinked: {candidate}")
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if candidate.stat().st_size != row.get("size") or digest != row.get("sha256"):
            raise ValueError(f"private asset size/hash mismatch: {relative}")
        asset_id = str(row.get("asset_id", ""))
        if not asset_id or not row.get("revision") or not row.get("license_status"):
            raise ValueError(f"private asset identity metadata incomplete: {relative}")
        covered.add(asset_id)
        seen.add(relative)
    missing = sorted(required - covered)
    if missing:
        raise FileNotFoundError("private asset IDs are missing: " + ", ".join(missing))
    return {
        "schema_version": "certgen.kaggle.private_asset_validation.v1",
        "passed": True,
        "required_asset_ids": sorted(required),
        "covered_asset_ids": sorted(covered),
        "files": len(rows),
        "claim_allowed": False,
    }
