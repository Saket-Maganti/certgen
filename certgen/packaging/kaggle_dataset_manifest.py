from __future__ import annotations

import hashlib
import json
from pathlib import Path


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(folder: str | Path, *, dataset_name: str) -> dict[str, object]:
    folder = Path(folder)
    files = []
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            files.append(
                {
                    "path": str(path.relative_to(folder)),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    return {
        "dataset_name": dataset_name,
        "files": files,
        "claim_allowed": False,
        "evidence_status": "run_log_only",
        "contains_secrets": False,
    }


def write_manifest(folder: str | Path, *, dataset_name: str) -> dict[str, object]:
    payload = build_manifest(folder, dataset_name=dataset_name)
    Path(folder, "manifest.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload
