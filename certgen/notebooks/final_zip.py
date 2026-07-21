"""Idempotent final output ZIP reuse, rebuild, restart, and recovery."""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from certgen.core.hashing import file_sha256
from certgen.cvpr.contracts import atomic_write_json
from certgen.notebooks.kaggle_io import deterministic_zip, write_integrity_manifest


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def validate_final_zip(root: str | Path, archive_path: str | Path) -> dict[str, Any]:
    base = Path(root)
    archive_path = Path(archive_path)
    errors: list[str] = []
    expected = {
        path.relative_to(base).as_posix(): (path.stat().st_size, file_sha256(path))
        for path in base.rglob("*")
        if path.is_file()
        and ".partial" not in path.parts
        and ".cache" not in path.relative_to(base).parts
    }
    try:
        with zipfile.ZipFile(archive_path) as archive:
            if archive.testzip() is not None:
                errors.append("final ZIP CRC failure")
            infos = {info.filename: info for info in archive.infolist() if not info.is_dir()}
            if set(infos) != set(expected):
                errors.append("final ZIP membership differs from completed run")
            for name, (size, digest) in expected.items():
                info = infos.get(name)
                if info is None:
                    continue
                data = archive.read(name)
                import hashlib

                if info.file_size != size or hashlib.sha256(data).hexdigest() != digest:
                    errors.append(f"final ZIP member mismatch: {name}")
    except (OSError, zipfile.BadZipFile) as exc:
        errors.append(f"final ZIP invalid: {exc}")
    return {"passed": not errors, "errors": errors, "claim_allowed": False}


def _quarantine(path: Path, reason: str) -> Path:
    quarantine = path.parent / "quarantine" / f"{_timestamp()}_{reason}" / path.name
    quarantine.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), quarantine)
    return quarantine


def finalize_output_zip(
    root: str | Path,
    output: str | Path,
    *,
    mode: str,
    configuration_hash: str,
    asset_manifest_hash: str,
) -> dict[str, Any]:
    if mode not in {"resume", "restart", "force_new_run"}:
        raise ValueError("final ZIP mode must be resume, restart, or force_new_run")
    base = Path(root)
    target = Path(output)
    write_integrity_manifest(base)
    prior_status_path = target.with_suffix(target.suffix + ".status.json")
    prior_status: dict[str, Any] = {}
    if prior_status_path.is_file():
        try:
            prior_status = json.loads(prior_status_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            prior_status = {}
    if target.exists() and mode == "resume":
        validation = validate_final_zip(base, target)
        identity_matches = (
            prior_status.get("configuration_hash") == configuration_hash
            and prior_status.get("asset_manifest_hash") == asset_manifest_hash
            and prior_status.get("archive_sha256") == file_sha256(target)
        )
        if validation["passed"] and identity_matches:
            return {
                "status": "REUSED_VALID_FINAL_ZIP",
                "path": str(target),
                "sha256": file_sha256(target),
                "configuration_hash": configuration_hash,
                "asset_manifest_hash": asset_manifest_hash,
                "claim_allowed": False,
            }
        _quarantine(target, "resume_invalid_final_zip")
    elif target.exists() and mode == "restart":
        _quarantine(target, "explicit_restart")
    elif target.exists() and mode == "force_new_run":
        raise FileExistsError("force_new_run requires a new run-specific final ZIP path")
    temporary = target.with_name(f".{target.name}.partial")
    if temporary.exists():
        temporary.unlink()
    result = deterministic_zip(base, temporary)
    os.replace(temporary, target)
    rebuilt = validate_final_zip(base, target)
    if not rebuilt["passed"]:
        raise RuntimeError("rebuilt final ZIP failed validation: " + "; ".join(rebuilt["errors"]))
    status = {
        "schema_version": "certgen.final_zip.v2",
        "status": "REBUILT_FINAL_ZIP",
        "path": str(target),
        "archive_sha256": file_sha256(target),
        "size": target.stat().st_size,
        "configuration_hash": configuration_hash,
        "asset_manifest_hash": asset_manifest_hash,
        "claim_allowed": False,
    }
    atomic_write_json(status, prior_status_path)
    return {**status, "sha256": status["archive_sha256"], "original_build": result}


def write_multipart_fallback(
    archive_path: str | Path,
    *,
    maximum_part_bytes: int = 4 * 1024**3,
) -> dict[str, Any]:
    """Split one already-validated output ZIP into deterministic copy-back parts."""

    source = Path(archive_path)
    if not source.is_file() or not zipfile.is_zipfile(source):
        raise ValueError("multipart source must be a valid ZIP")
    if maximum_part_bytes <= 0:
        raise ValueError("maximum_part_bytes must be positive")
    members: list[dict[str, Any]] = []
    with source.open("rb") as handle:
        index = 0
        while True:
            data = handle.read(maximum_part_bytes)
            if not data:
                break
            index += 1
            part = source.with_suffix(source.suffix + f".part{index:04d}")
            if part.exists() and part.read_bytes() != data:
                raise FileExistsError(f"refusing to overwrite different multipart member: {part}")
            if not part.exists():
                temporary = part.with_name(f".{part.name}.partial")
                temporary.write_bytes(data)
                os.replace(temporary, part)
            members.append(
                {
                    "path": part.name,
                    "index": index,
                    "size": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
    payload = {
        "schema_version": "certgen.multipart_output.v1",
        "source_zip": source.name,
        "source_zip_sha256": file_sha256(source),
        "source_zip_size": source.stat().st_size,
        "parts": members,
        "claim_allowed": False,
    }
    atomic_write_json(payload, source.with_suffix(source.suffix + ".parts.json"))
    return payload


def validate_multipart_fallback(manifest_path: str | Path) -> dict[str, Any]:
    manifest = Path(manifest_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    errors: list[str] = []
    data = bytearray()
    expected_indices = list(range(1, len(payload.get("parts", [])) + 1))
    observed_indices = [row.get("index") for row in payload.get("parts", [])]
    if observed_indices != expected_indices:
        errors.append("multipart indices are missing, duplicated, or out of order")
    for row in payload.get("parts", []):
        part = manifest.parent / str(row.get("path", ""))
        if not part.is_file():
            errors.append(f"multipart member missing: {part.name}")
            continue
        chunk = part.read_bytes()
        if len(chunk) != row.get("size") or hashlib.sha256(chunk).hexdigest() != row.get("sha256"):
            errors.append(f"multipart member corrupt: {part.name}")
        data.extend(chunk)
    if len(data) != payload.get("source_zip_size") or hashlib.sha256(data).hexdigest() != payload.get("source_zip_sha256"):
        errors.append("reassembled multipart payload differs from source ZIP")
    return {"passed": not errors, "errors": errors, "claim_allowed": False}
