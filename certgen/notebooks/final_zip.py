"""Idempotent final output ZIP reuse, rebuild, restart, and recovery."""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import file_sha256
from certgen.cvpr.contracts import atomic_write_json
from certgen.discovery.classify import package_identity_payload
from certgen.discovery.models import PackageType
from certgen.notebooks.kaggle_io import deterministic_zip, write_integrity_manifest


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_output_identity(
    root: Path, input_identity: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    identity_path = root / "package_identity.json"
    if identity_path.is_file():
        payload = json.loads(identity_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("claim_allowed") is not False:
            raise ValueError("existing output package identity is invalid")
        if input_identity is not None and (
            payload.get("input_package_sha256") != input_identity.get("package_sha256")
            or payload.get("input_scientific_identity_hash") != input_identity.get("scientific_identity_hash")
        ):
            raise ValueError("existing output package belongs to a different authenticated input identity")
        return payload
    config_path = root / "configuration.yaml"
    if not config_path.is_file():
        return None
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("output frozen configuration must be a mapping")
    stage = "features" if config.get("kind") == "feature" else str(config.get("kind"))
    status_files = {
        "diagnostic": "diagnostic_status.json",
        "preflight": "checkpoint_preflight_status.json",
        "generation": "generation_status.json",
        "features": "feature_extraction_status.json",
    }
    package_types = {
        "diagnostic": PackageType.DIAGNOSTIC_OUTPUT,
        "preflight": PackageType.PREFLIGHT_OUTPUT,
        "generation": PackageType.GENERATION_OUTPUT,
        "features": PackageType.FEATURE_OUTPUT,
    }
    if stage not in status_files:
        raise ValueError(f"unsupported output package stage: {stage}")
    status_path = root / status_files[stage]
    if not status_path.is_file():
        return None
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if not isinstance(status, dict) or not status.get("status_code"):
        raise ValueError("canonical output status is missing")
    payload = package_identity_payload(
        config,
        package_type=package_types[stage],
        integrity_manifest="integrity_manifest.json",
        completion_status=str(status["status_code"]),
        created_at_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    if input_identity is not None:
        payload["input_package_sha256"] = input_identity.get("package_sha256")
        payload["input_scientific_identity_hash"] = input_identity.get("scientific_identity_hash")
    atomic_write_json(payload, identity_path)
    return payload


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
    input_identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if mode not in {"resume", "restart", "force_new_run"}:
        raise ValueError("final ZIP mode must be resume, restart, or force_new_run")
    base = Path(root)
    target = Path(output)
    if input_identity is not None:
        atomic_write_json(
            {
                "schema_version": "certgen.output_input_identity.v1",
                **input_identity,
                "claim_allowed": False,
            },
            base / "input_identity.json",
        )
    _write_output_identity(base, input_identity)
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
    if not isinstance(payload, dict) or payload.get("schema_version") != "certgen.multipart_output.v1" or payload.get("claim_allowed") is not False:
        return {"passed": False, "errors": ["multipart manifest schema or safety label is invalid"], "claim_allowed": False}
    rows = payload.get("parts")
    if not isinstance(rows, list) or not rows:
        return {"passed": False, "errors": ["multipart manifest requires non-empty parts"], "claim_allowed": False}
    expected_indices = list(range(1, len(rows) + 1))
    observed_indices = [row.get("index") if isinstance(row, dict) else None for row in rows]
    if observed_indices != expected_indices:
        errors.append("multipart indices are missing, duplicated, or out of order")
    digest = hashlib.sha256()
    total = 0
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("multipart row is not an object")
            continue
        raw = str(row.get("path", ""))
        relative = PurePosixPath(raw)
        if not raw or relative.is_absolute() or ".." in relative.parts or "\\" in raw or raw.casefold() in seen:
            errors.append(f"unsafe or duplicate multipart member path: {raw}")
            continue
        seen.add(raw.casefold())
        part = manifest.parent.joinpath(*relative.parts)
        if not part.is_file():
            errors.append(f"multipart member missing: {part.name}")
            continue
        if part.is_symlink():
            errors.append(f"multipart member is symlinked: {part.name}")
            continue
        chunk_hash = hashlib.sha256()
        size = 0
        with part.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                size += len(chunk)
                total += len(chunk)
                chunk_hash.update(chunk)
                digest.update(chunk)
        if size != row.get("size") or chunk_hash.hexdigest() != row.get("sha256"):
            errors.append(f"multipart member corrupt: {part.name}")
    if total != payload.get("source_zip_size") or digest.hexdigest() != payload.get("source_zip_sha256"):
        errors.append("reassembled multipart payload differs from source ZIP")
    return {"passed": not errors, "errors": errors, "claim_allowed": False}


def reassemble_multipart_fallback(
    manifest_path: str | Path,
    *,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    manifest = Path(manifest_path)
    validation = validate_multipart_fallback(manifest)
    if not validation["passed"]:
        return {**validation, "status": "MULTIPART_VALIDATION_FAILED", "path": None}
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    target = Path(output_path) if output_path is not None else manifest.parent / str(payload["source_zip"])
    if target.exists() and file_sha256(target) == payload["source_zip_sha256"]:
        status = "REUSED_VALID_REASSEMBLED_ZIP"
    else:
        if target.exists():
            raise FileExistsError("refusing to overwrite a different multipart output ZIP")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.partial")
        if temporary.exists():
            temporary.unlink()
        with temporary.open("xb") as output:
            for row in payload["parts"]:
                relative = PurePosixPath(str(row["path"]))
                with manifest.parent.joinpath(*relative.parts).open("rb") as source:
                    shutil.copyfileobj(source, output, 1024 * 1024)
        if temporary.stat().st_size != payload["source_zip_size"] or file_sha256(temporary) != payload["source_zip_sha256"]:
            temporary.unlink()
            raise RuntimeError("atomic multipart rebuild differs from the declared final ZIP")
        os.replace(temporary, target)
        status = "REASSEMBLED_VALID_FINAL_ZIP"
    from certgen.discovery import classify_package

    package = classify_package(target)
    return {
        "passed": package.valid,
        "status": status if package.valid else "REASSEMBLED_ZIP_PACKAGE_INVALID",
        "path": str(target),
        "sha256": file_sha256(target),
        "package": package.to_dict(),
        "errors": list(package.errors),
        "claim_allowed": False,
    }
