"""Portable, deterministic Kaggle package I/O used by all canonical notebooks."""

from __future__ import annotations

import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.image_manifest import read_image_manifest


def safe_extract_one_input_package(
    *,
    mount_root: str | Path = "/kaggle/input",
    destination: str | Path = "/kaggle/working/certgen-input",
    search_roots: Iterable[str | Path] | None = None,
    expected_stage: str | None = None,
    expected_package_type: str | None = None,
    expected_study_hash: str | None = None,
    expected_configuration_hash: str | None = None,
    expected_run_id: str | None = None,
    maximum_depth: int = 12,
    maximum_candidates: int = 10_000,
    maximum_members: int = 200_000,
    maximum_bytes: int = 20 * 1024**3,
) -> Path:
    from certgen.discovery import (
        DiscoveryLimits,
        PackageRequirement,
        PackageType,
        SelectionStatus,
        discover_packages,
        materialize_selected_package,
    )

    roots = tuple(search_roots or (mount_root, "/kaggle/working"))
    package_type = PackageType(expected_package_type) if expected_package_type else (
        PackageType[f"{expected_stage.upper()}_INPUT"] if expected_stage else None
    )
    requirement = PackageRequirement(
        expected_package_type=package_type,
        expected_stage=expected_stage,
        expected_study_hash=expected_study_hash,
        expected_configuration_hash=expected_configuration_hash,
        expected_run_id=expected_run_id,
        required_completion_status="INPUT_PACKAGE_READY",
    )
    limits = DiscoveryLimits(
        maximum_depth=maximum_depth,
        maximum_candidates=maximum_candidates,
        maximum_package_members=maximum_members,
        maximum_uncompressed_bytes=maximum_bytes,
    )
    result = discover_packages(roots, requirement=requirement, limits=limits)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    if result.status is not SelectionStatus.SELECTED_UNIQUE_VALID_PACKAGE or result.selected is None:
        raise RuntimeError(
            f"universal package discovery failed: {result.status.value}; "
            f"inspect the candidate identities and remediation in the discovery report"
        )
    return materialize_selected_package(result.selected, destination=destination, limits=limits)


def verify_input_integrity(root: str | Path, ignored: set[str] | None = None) -> dict[str, Any]:
    base = Path(root)
    manifest_path = base / "package_integrity_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("package integrity manifest is missing")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = payload.get("files", [])
    declared = {row["path"]: row for row in rows}
    skip = {
        "package_integrity_manifest.json",
        ".source_sha256",
        ".certgen_runtime_location.json",
        *(ignored or set()),
    }
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
        f"Copy `{zip_path}` back; the downloaded file may be renamed. Preserve its SHA-256, then run "
        f"`python3 scripts/run_all_available_cpu_stages.py --resume --explain --search-root <download-folder>` "
        f"or `python3 -m certgen import {import_kind} <copied-back-zip>`. This output is run-log-only, "
        "not paper evidence, and claim_allowed=false.\n"
    )


def assert_unique_shards(rows: Iterable[Mapping[str, Any]]) -> None:
    ids = [str(row["shard_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("non-overlapping shard assignment failed")


def validate_feature_input_images(
    root: str | Path,
    config: Mapping[str, Any],
    *,
    search_roots: Iterable[str | Path] | None = None,
) -> dict[str, Any]:
    """Decode and hash-check every feature image before any GPU worker starts."""

    package_root = Path(root)
    manifest = package_root / "manifests" / "images.jsonl"
    mode = config.get("feature_input_mode")
    if mode == "EMBED_IMAGES_IN_PACKAGE":
        image_root = package_root
    elif mode == "MOUNT_EXTERNAL_IMAGE_DATASET":
        from certgen.discovery import discover_dataset_root

        resolution = discover_dataset_root(
            search_roots or ("/kaggle/input", "/kaggle/working"),
            expected_manifest_hash=str(config.get("mount_manifest_hash", "")),
            expected_role_counts=config.get("expected_role_counts"),
        )
        selected = resolution.get("selected")
        if not isinstance(selected, dict) or not selected.get("root"):
            raise RuntimeError(f"external dataset discovery failed: {resolution['status']}")
        image_root = Path(str(selected["root"]))
    else:
        raise ValueError("unsupported feature_input_mode")
    rows = read_image_manifest(manifest, root=image_root, decode=True)
    return {
        "status": "ALL_FEATURE_IMAGE_PATHS_RESOLVED",
        "mode": mode,
        "images": len(rows),
        "resolved_image_root": str(image_root),
        "manifest_sha256": file_sha256(manifest),
        "claim_allowed": False,
    }
