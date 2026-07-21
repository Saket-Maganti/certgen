"""Portable, deterministic Kaggle package I/O used by all canonical notebooks."""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.image_manifest import read_image_manifest


def safe_extract_one_input_package(
    *,
    mount_root: str | Path = "/kaggle/input",
    destination: str | Path = "/kaggle/working/certgen-input",
    maximum_members: int = 200_000,
    maximum_bytes: int = 20 * 1024**3,
) -> Path:
    mount = Path(mount_root)
    direct = sorted(mount.glob("*/configuration.yaml"))
    if len(direct) == 1:
        return direct[0].parent
    if len(direct) > 1:
        raise RuntimeError("multiple direct CertGen configurations found")
    archives = sorted(mount.glob("*/*.zip"))
    if len(archives) != 1:
        raise RuntimeError(f"expected exactly one CertGen input ZIP; found {len(archives)}")
    source = archives[0]
    output = Path(destination)
    source_hash = file_sha256(source)
    marker = output / ".source_sha256"
    if output.is_dir() and marker.is_file() and marker.read_text(encoding="utf-8").strip() == source_hash:
        verify_input_integrity(output)
        return output
    if output.exists():
        raise FileExistsError("input destination exists with a different or missing source hash")
    temporary = output.with_name(f".{output.name}.partial")
    if temporary.exists():
        shutil.rmtree(temporary)
    total = 0
    seen: set[str] = set()
    with zipfile.ZipFile(source) as archive:
        if archive.testzip() is not None or len(archive.infolist()) > maximum_members:
            raise ValueError("input ZIP failed CRC/member-count validation")
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            key = path.as_posix().casefold()
            mode = (info.external_attr >> 16) & 0o170000
            if path.is_absolute() or ".." in path.parts or "\\" in info.filename or key in seen or mode == 0o120000:
                raise ValueError(f"unsafe input ZIP member: {info.filename}")
            if key.endswith((".zip", ".tar", ".tgz", ".tar.gz")):
                raise ValueError(f"nested archive refused: {info.filename}")
            total += info.file_size
            seen.add(key)
        if total > maximum_bytes:
            raise ValueError("input ZIP expansion limit exceeded")
        archive.extractall(temporary)
    (temporary / ".source_sha256").write_text(source_hash + "\n", encoding="utf-8")
    os.replace(temporary, output)
    verify_input_integrity(output, ignored={".source_sha256"})
    return output


def verify_input_integrity(root: str | Path, ignored: set[str] | None = None) -> dict[str, Any]:
    base = Path(root)
    manifest_path = base / "package_integrity_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("package integrity manifest is missing")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = payload.get("files", [])
    declared = {row["path"]: row for row in rows}
    skip = {"package_integrity_manifest.json", *(ignored or set())}
    actual = {
        path.relative_to(base).as_posix(): path
        for path in base.rglob("*")
        if path.is_file() and path.relative_to(base).as_posix() not in skip
    }
    if set(actual) != set(declared):
        raise ValueError("input package membership differs from integrity manifest")
    for name, path in actual.items():
        row = declared[name]
        if path.stat().st_size != row["size"] or file_sha256(path) != row["sha256"]:
            raise ValueError(f"input integrity mismatch: {name}")
    return payload


def load_frozen_configuration(root: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load((Path(root) / "configuration.yaml").read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("configuration must be a mapping")
    declared = payload.get("configuration_hash")
    observed = stable_hash_json({key: value for key, value in payload.items() if key != "configuration_hash"})
    if declared != observed:
        raise ValueError("configuration-hash validation failed")
    if payload.get("claim_allowed") is not False:
        raise ValueError("configuration must set claim_allowed=false")
    return payload


def disk_guard(path: str | Path, required_bytes: int, safety_margin_bytes: int = 2 * 1024**3) -> dict[str, int]:
    usage = shutil.disk_usage(path)
    required = int(required_bytes) + int(safety_margin_bytes)
    if usage.free < required:
        raise RuntimeError(f"insufficient disk: free={usage.free}, required_with_margin={required}")
    return {"free_bytes": usage.free, "required_bytes": int(required_bytes), "safety_margin_bytes": int(safety_margin_bytes)}


def write_integrity_manifest(root: str | Path) -> dict[str, Any]:
    base = Path(root)
    manifest_path = base / "integrity_manifest.json"
    files = [
        {"path": path.relative_to(base).as_posix(), "size": path.stat().st_size, "sha256": file_sha256(path)}
        for path in sorted(base.rglob("*"))
        if path.is_file()
        and path != manifest_path
        and ".partial" not in path.parts
        and ".cache" not in path.relative_to(base).parts
    ]
    payload = {"files": files, "evidence_class": "run_log_only", "claim_allowed": False}
    temporary = manifest_path.with_name(f".{manifest_path.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, manifest_path)
    return payload


def deterministic_zip(root: str | Path, output: str | Path) -> dict[str, Any]:
    base = Path(root)
    target = Path(output)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite output ZIP: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, "x") as archive:
        for path in sorted(base.rglob("*")):
            if (
                not path.is_file()
                or ".partial" in path.parts
                or ".cache" in path.relative_to(base).parts
            ):
                continue
            info = zipfile.ZipInfo(path.relative_to(base).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    return {"path": str(target), "sha256": file_sha256(target), "size": target.stat().st_size}


def all_worker_statuses_complete(payload: Mapping[str, Any]) -> bool:
    workers = payload.get("workers")
    return isinstance(workers, list) and bool(workers) and all(
        isinstance(row, dict) and row.get("status") in {"COMPLETE", "REUSED_VALID_COMPLETION"} for row in workers
    )


def copyback_instructions(kind: str, zip_path: str | Path) -> str:
    import_kind = "features" if kind == "features" else kind
    return (
        f"Copy `{zip_path}` back without renaming or unpacking it. Preserve its SHA-256, then run "
        f"`python3 -m certgen import {import_kind} <copied-back-zip>`. This output is run-log-only, "
        "not paper evidence, and claim_allowed=false.\n"
    )


def assert_unique_shards(rows: Iterable[Mapping[str, Any]]) -> None:
    ids = [str(row["shard_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("non-overlapping shard assignment failed")


def validate_feature_input_images(root: str | Path, config: Mapping[str, Any]) -> dict[str, Any]:
    """Decode and hash-check every feature image before any GPU worker starts."""

    package_root = Path(root)
    manifest = package_root / "manifests" / "images.jsonl"
    mode = config.get("feature_input_mode")
    if mode == "EMBED_IMAGES_IN_PACKAGE":
        image_root = package_root
    elif mode == "MOUNT_EXTERNAL_IMAGE_DATASET":
        image_root = Path(str(config.get("expected_mount_path", "")))
        mount_manifest = package_root / "mount_manifest.json"
        if not image_root.is_dir() or not mount_manifest.is_file():
            raise FileNotFoundError("declared external image mount or mount manifest is unavailable")
        payload = json.loads(mount_manifest.read_text(encoding="utf-8"))
        if payload.get("mount_manifest_hash") != config.get("mount_manifest_hash"):
            raise ValueError("mounted dataset manifest hash differs from frozen configuration")
    else:
        raise ValueError("unsupported feature_input_mode")
    rows = read_image_manifest(manifest, root=image_root, decode=True)
    return {
        "status": "ALL_FEATURE_IMAGE_PATHS_RESOLVED",
        "mode": mode,
        "images": len(rows),
        "manifest_sha256": file_sha256(manifest),
        "claim_allowed": False,
    }
