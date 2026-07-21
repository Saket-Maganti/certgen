"""Typed online/offline model-asset policy and cache-manifest validation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

from certgen.core.hashing import stable_hash_json
from certgen.cvpr.contracts import atomic_write_json


class AssetPolicy(str, Enum):
    ONLINE_PREFLIGHT_DOWNLOAD = "ONLINE_PREFLIGHT_DOWNLOAD"
    OFFLINE_PACKAGED_CACHE = "OFFLINE_PACKAGED_CACHE"


REQUIRED_MANIFEST_FIELDS = {
    "asset_id",
    "model_or_extractor_id",
    "revision",
    "source",
    "license",
    "authentication_required",
    "files",
    "file_hashes",
    "total_size",
    "cache_root",
    "asset_root",
    "snapshot_path",
    "source_repo",
    "layout_type",
    "loader_type",
    "policy",
    "validated_at",
    "validation_status",
    "preflight_status",
    "redistribution_allowed",
    "public_archive_included",
    "user_provided",
    "private_mount_required",
    "license_source",
    "license_status",
}
UNKNOWN_LICENSES = {"", "unknown", "unverified", "unverified_requires_manual_review", "model_and_package_review_required"}


@dataclass(frozen=True)
class AssetRequirement:
    asset_id: str
    model_or_extractor_id: str
    revision: str
    source: str
    license: str
    authentication_required: bool | str
    expected_files: tuple[str, ...]

    def validate(self) -> None:
        values = (self.asset_id, self.model_or_extractor_id, self.revision, self.source)
        if any(not value or "TBD" in value or value == "UNKNOWN" for value in values):
            raise ValueError("asset identifiers, source, and revision must be pinned")
        if self.license.lower() in UNKNOWN_LICENSES:
            raise PermissionError(f"asset {self.asset_id} has no approved license status")
        if not self.expected_files:
            raise ValueError("asset must declare expected files")


def _safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"unsafe asset path: {value}")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_policy_preconditions(
    requirement: AssetRequirement,
    *,
    policy: AssetPolicy,
    internet_enabled: bool,
    token_present: bool,
    cache_root: str | Path,
) -> None:
    requirement.validate()
    if policy is AssetPolicy.ONLINE_PREFLIGHT_DOWNLOAD:
        if not internet_enabled:
            raise RuntimeError("ONLINE_PREFLIGHT_DOWNLOAD requires Kaggle internet to be enabled")
        if requirement.authentication_required is True and not token_present:
            raise PermissionError("authenticated asset requires a token in the preflight worker")
    else:
        if internet_enabled:
            raise RuntimeError("OFFLINE_PACKAGED_CACHE requires internet disabled")
        if not Path(cache_root).is_dir():
            raise FileNotFoundError(f"offline cache root missing: {cache_root}")


def inventory_cache(requirement: AssetRequirement, cache_root: str | Path, policy: AssetPolicy) -> dict[str, Any]:
    root = Path(cache_root).resolve()
    requirement.validate()
    files: list[str] = []
    hashes: dict[str, str] = {}
    total = 0
    missing: list[str] = []
    for raw in requirement.expected_files:
        rel = _safe_relative(raw)
        path = root.joinpath(*rel.parts)
        if not path.is_file():
            missing.append(rel.as_posix())
            continue
    # Bind the manifest to every runtime-visible snapshot file, not only the
    # small required-file sentinel set used to detect incomplete downloads.
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".cache" in path.relative_to(root).parts:
            continue
        inventory_rel = path.relative_to(root).as_posix()
        files.append(inventory_rel)
        hashes[inventory_rel] = _sha256(path)
        total += path.stat().st_size
    status = "VALIDATED" if not missing else "BLOCKED_MISSING_ASSETS"
    restricted_clip = (
        requirement.model_or_extractor_id.lower() == "clip"
        or "openai/clip" in requirement.source.lower()
    )
    return {
        "schema_version": "certgen.model_asset_manifest.v2",
        "asset_id": requirement.asset_id,
        "model_or_extractor_id": requirement.model_or_extractor_id,
        "revision": requirement.revision,
        "source": requirement.source,
        "license": requirement.license,
        "authentication_required": requirement.authentication_required,
        "files": files,
        "file_hashes": hashes,
        "total_size": total,
        "cache_root": str(root),
        "asset_root": str(root),
        "snapshot_path": str(root),
        "source_repo": requirement.source,
        "layout_type": "direct_local_snapshot",
        "loader_type": "from_pretrained_local_snapshot",
        "policy": policy.value,
        "validated_at": "runtime_generated",
        "validation_status": status,
        "preflight_status": "ASSET_VALIDATED" if status == "VALIDATED" else "ASSET_BLOCKED",
        "redistribution_allowed": False,
        "public_archive_included": False,
        "user_provided": True,
        "private_mount_required": restricted_clip,
        "license_source": requirement.source,
        "license_status": requirement.license,
        "missing_files": missing,
        "local_files_only": policy is AssetPolicy.OFFLINE_PACKAGED_CACHE,
        "evidence_class": "non_evidence_preflight",
        "claim_allowed": False,
    }


def write_asset_manifest(payload: Mapping[str, Any], path: str | Path) -> None:
    validate_asset_manifest(payload)
    atomic_write_json(dict(payload), path)


def validate_asset_manifest(
    payload: Mapping[str, Any],
    *,
    expected_hashes: Mapping[str, str] | None = None,
    cache_root: str | Path | None = None,
    manifest_root: str | Path | None = None,
) -> None:
    missing_fields = sorted(REQUIRED_MANIFEST_FIELDS - set(payload))
    if missing_fields:
        raise ValueError("asset manifest missing fields: " + ", ".join(missing_fields))
    if payload.get("claim_allowed") is not False:
        raise ValueError("asset manifest must set claim_allowed=false")
    for field in (
        "redistribution_allowed", "public_archive_included", "user_provided", "private_mount_required"
    ):
        if not isinstance(payload.get(field), bool):
            raise ValueError(f"asset manifest {field} must be boolean")
    if payload.get("public_archive_included") is True and payload.get("redistribution_allowed") is not True:
        raise PermissionError("public archive inclusion requires explicitly verified redistribution permission")
    if not str(payload.get("license_source", "")).strip() or not str(payload.get("license_status", "")).strip():
        raise ValueError("asset manifest requires an explicit license source and status")
    AssetPolicy(str(payload["policy"]))
    if payload.get("layout_type") not in {
        "direct_local_snapshot",
        "huggingface_cache",
        "torchvision_weight_enum",
        "package_resource",
        "torchvision_local_weight_file",
    }:
        raise ValueError("asset manifest has unsupported layout_type")
    if payload.get("loader_type") not in {
        "from_pretrained_local_snapshot",
        "from_pretrained_hf_cache",
        "torchvision_weight_enum",
        "package_resource",
        "torchvision_local_state_dict",
    }:
        raise ValueError("asset manifest has unsupported loader_type")
    base = Path(manifest_root).resolve() if manifest_root is not None else Path.cwd().resolve()
    snapshot_raw = Path(str(payload["snapshot_path"]))
    asset_root_raw = Path(str(payload["asset_root"]))
    if cache_root is not None and payload.get("portable_snapshot_root") is True and not snapshot_raw.is_absolute():
        snapshot = Path(cache_root).resolve()
        asset_root = snapshot.parent
    else:
        snapshot = snapshot_raw if snapshot_raw.is_absolute() else base / snapshot_raw
        asset_root = asset_root_raw if asset_root_raw.is_absolute() else base / asset_root_raw
    try:
        snapshot.resolve().relative_to(asset_root.resolve())
    except ValueError as exc:
        raise ValueError("snapshot_path must be inside asset_root") from exc
    files = payload.get("files")
    hashes = payload.get("file_hashes")
    if not isinstance(files, list) or not isinstance(hashes, dict) or set(files) != set(hashes):
        raise ValueError("asset manifest files and hashes must match exactly")
    if payload.get("validation_status") != "VALIDATED":
        raise ValueError("asset manifest is not validated")
    if expected_hashes is not None and dict(hashes) != dict(expected_hashes):
        raise ValueError("asset manifest hash inventory differs from the approved preflight manifest")
    if cache_root is not None:
        root = Path(cache_root).resolve()
        if snapshot.resolve() != root:
            raise ValueError("runtime cache root differs from canonical snapshot_path")
        for raw in files:
            rel = _safe_relative(str(raw))
            path = root.joinpath(*rel.parts)
            if not path.is_file() or _sha256(path) != hashes[raw]:
                raise ValueError(f"offline asset hash mismatch: {raw}")


def validate_asset_identity(
    payload: Mapping[str, Any], *, model_or_extractor_id: str, revision: str
) -> None:
    """Bind a validated cache manifest to the exact configured runtime identity."""

    if payload.get("model_or_extractor_id") != model_or_extractor_id or payload.get("revision") != revision:
        raise ValueError("asset manifest does not match configured model/revision")


def resolve_local_snapshot(
    payload: Mapping[str, Any],
    *,
    manifest_root: str | Path | None = None,
    runtime_cache_root: str | Path | None = None,
) -> Path:
    """Return a validated direct snapshot path for local-only loaders."""

    validate_asset_manifest(payload, manifest_root=manifest_root, cache_root=runtime_cache_root)
    if runtime_cache_root is not None and payload.get("portable_snapshot_root") is True:
        snapshot = Path(runtime_cache_root)
    else:
        snapshot = Path(str(payload["snapshot_path"]))
        if not snapshot.is_absolute():
            snapshot = Path(manifest_root or ".") / snapshot
    if not snapshot.is_dir():
        raise FileNotFoundError(f"validated local snapshot is unavailable: {snapshot}")
    if payload.get("layout_type") == "direct_local_snapshot" and payload.get("loader_type") != "from_pretrained_local_snapshot":
        raise ValueError("direct snapshot requires from_pretrained(local_snapshot_path, local_files_only=True)")
    return snapshot


def portable_asset_manifest(
    payload: Mapping[str, Any],
    *,
    snapshot_path: str,
    preflight_manifest_sha256: str,
) -> dict[str, Any]:
    """Rebase only location fields while preserving the approved file inventory."""

    relative = _safe_relative(snapshot_path).as_posix()
    rebased = dict(payload)
    rebased.update(
        {
            "cache_root": relative,
            "asset_root": ".",
            "snapshot_path": relative,
            "portable_snapshot_root": True,
            "preflight_manifest_sha256": preflight_manifest_sha256,
            "preflight_file_inventory_hash": stable_hash_json(dict(payload["file_hashes"])),
        }
    )
    validate_asset_manifest(rebased, manifest_root=".")
    return rebased


def load_asset_manifest(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("asset manifest must be an object")
    validate_asset_manifest(payload)
    return payload


def validate_registry_asset_fields(rows: Iterable[Mapping[str, Any]]) -> list[str]:
    required = {
        "asset_policy",
        "asset_manifest_required",
        "online_preflight_supported",
        "offline_cache_supported",
        "expected_cache_size",
    }
    errors: list[str] = []
    for index, row in enumerate(rows):
        missing = sorted(required - set(row))
        if missing:
            errors.append(f"row {index}: missing " + ", ".join(missing))
        try:
            AssetPolicy(str(row.get("asset_policy")))
        except ValueError:
            errors.append(f"row {index}: invalid asset_policy")
    return errors
