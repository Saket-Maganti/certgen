"""Content-addressed discovery for references, model assets, and wheelhouses."""

from __future__ import annotations

import hashlib
import json
import platform
import sysconfig
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name, parse_wheel_filename

from certgen.discovery.models import DiscoveryLimits
from certgen.discovery.scan import iter_bounded_files


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not path.parts or path.is_absolute() or ".." in path.parts or "\\" in value:
        raise ValueError(f"unsafe manifest path: {value}")
    return path


def discover_reference(
    search_roots: Iterable[str | Path],
    *,
    expected_kind: str,
    limits: DiscoveryLimits | None = None,
) -> dict[str, Any]:
    if expected_kind != "cifar10_python":
        raise ValueError(f"unsupported reference kind: {expected_kind}")
    selected_limits = limits or DiscoveryLimits()
    files = iter_bounded_files((Path(root) for root in search_roots), limits=selected_limits)
    possible: set[Path] = set()
    required_batches = {*(f"data_batch_{index}" for index in range(1, 6)), "test_batch"}
    for path in files:
        if path.suffix.casefold() in {".zip", ".tar", ".tgz", ".gz"}:
            possible.add(path)
        if path.name in required_batches:
            possible.add(path.parent)
    rows: list[dict[str, Any]] = []
    from certgen.cvpr.reference import validate_reference_source

    for path in sorted(possible, key=lambda value: str(value).casefold()):
        verdict = validate_reference_source(path)
        rows.append({"path": str(path), **verdict})
    matches = [row for row in rows if row.get("passed") is True]
    status = "SELECTED_UNIQUE_VALID_REFERENCE" if len(matches) == 1 else (
        "NO_MATCHING_REFERENCE" if not matches else "AMBIGUOUS_MATCHING_REFERENCES"
    )
    return {
        "schema_version": "certgen.discovery.reference.v1",
        "status": status,
        "expected_kind": expected_kind,
        "candidates": rows,
        "selected": matches[0] if len(matches) == 1 else None,
        "claim_allowed": False,
    }


def discover_dataset_root(
    search_roots: Iterable[str | Path],
    *,
    expected_manifest_hash: str,
    expected_role_counts: Mapping[str, int] | None = None,
    limits: DiscoveryLimits | None = None,
) -> dict[str, Any]:
    """Resolve an external image dataset without freezing its mount location."""

    if len(expected_manifest_hash) != 64:
        raise ValueError("dataset manifest hash must be a SHA-256")
    selected_limits = limits or DiscoveryLimits()
    files = iter_bounded_files((Path(root) for root in search_roots), limits=selected_limits)
    rows: list[dict[str, Any]] = []
    from certgen.cvpr.image_manifest import read_image_manifest

    for path in files:
        if path.suffix.casefold() != ".jsonl" or _hash(path) != expected_manifest_hash:
            continue
        errors: list[str] = []
        images: list[dict[str, Any]] = []
        try:
            images = read_image_manifest(path, root=path.parent, decode=True)
        except (OSError, ValueError) as exc:
            errors.append(f"dataset decode/integrity validation failed: {exc}")
        observed_counts: dict[str, int] = {}
        for image in images:
            role = str(image.get("role"))
            observed_counts[role] = observed_counts.get(role, 0) + 1
        if expected_role_counts is not None and observed_counts != dict(expected_role_counts):
            errors.append("dataset role counts differ from frozen identity")
        rows.append(
            {
                "manifest": str(path),
                "root": str(path.parent),
                "manifest_sha256": expected_manifest_hash,
                "role_counts": observed_counts,
                "images": len(images),
                "passed": not errors,
                "errors": errors,
                "claim_allowed": False,
            }
        )
    matches = [row for row in rows if row["passed"]]
    status = "SELECTED_UNIQUE_VALID_DATASET" if len(matches) == 1 else (
        "NO_MATCHING_DATASET" if not matches else "AMBIGUOUS_MATCHING_DATASETS"
    )
    return {
        "schema_version": "certgen.discovery.dataset.v1",
        "status": status,
        "dataset_manifest_hash": expected_manifest_hash,
        "candidates": rows,
        "selected": matches[0] if len(matches) == 1 else None,
        "claim_allowed": False,
    }


def _validate_aggregate_asset_manifest(
    manifest: Path,
    required_assets: Mapping[str, str | None],
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"path": str(manifest), "passed": False, "errors": [str(exc)]}
    if not isinstance(payload, dict) or payload.get("claim_allowed") is not False:
        errors.append("asset manifest must be an object with claim_allowed=false")
    rows = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows:
        errors.append("asset manifest requires non-empty files rows")
        rows = []
    covered: dict[str, set[str]] = {}
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"asset row {index} is not an object")
            continue
        raw = str(row.get("path") or "")
        try:
            relative = _safe_relative(raw)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if relative.as_posix().casefold() in seen:
            errors.append(f"duplicate case-folded asset path: {raw}")
            continue
        seen.add(relative.as_posix().casefold())
        path = manifest.parent.joinpath(*relative.parts)
        if not path.is_file() or path.is_symlink():
            errors.append(f"asset file missing or symlinked: {raw}")
            continue
        if row.get("size") != path.stat().st_size or row.get("sha256") != _hash(path):
            errors.append(f"asset file size/hash mismatch: {raw}")
        asset_id = str(row.get("asset_id") or "")
        revision = str(row.get("revision") or "")
        if not asset_id or not revision or not row.get("license_status"):
            errors.append(f"asset identity metadata incomplete: {raw}")
        covered.setdefault(asset_id, set()).add(revision)
    for required_asset_id, expected_revision in required_assets.items():
        if required_asset_id not in covered:
            errors.append(f"required asset is missing: {required_asset_id}")
        elif expected_revision is not None and expected_revision not in covered[required_asset_id]:
            errors.append(f"required asset revision is missing: {required_asset_id}@{expected_revision}")
    return {
        "path": str(manifest),
        "root": str(manifest.parent),
        "passed": not errors,
        "errors": errors,
        "asset_ids": sorted(covered),
        "claim_allowed": False,
    }


def discover_asset_mount(
    search_roots: Iterable[str | Path],
    *,
    required_assets: Mapping[str, str | None],
    limits: DiscoveryLimits | None = None,
) -> dict[str, Any]:
    selected_limits = limits or DiscoveryLimits()
    files = iter_bounded_files((Path(root) for root in search_roots), limits=selected_limits)
    manifests = [path for path in files if path.name == "asset_manifest.json"]
    rows = [_validate_aggregate_asset_manifest(path, required_assets) for path in manifests]
    matches = [row for row in rows if row["passed"]]
    status = "SELECTED_UNIQUE_VALID_ASSET_MOUNT" if len(matches) == 1 else (
        "NO_MATCHING_ASSET_MOUNT" if not matches else "AMBIGUOUS_MATCHING_ASSET_MOUNTS"
    )
    return {
        "schema_version": "certgen.discovery.assets.v1",
        "status": status,
        "required_assets": dict(required_assets),
        "candidates": rows,
        "selected": matches[0] if len(matches) == 1 else None,
        "claim_allowed": False,
    }


def _wheel_distributions(root: Path, rows: list[dict[str, Any]], errors: list[str]) -> set[str]:
    distributions: set[str] = set()
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"wheelhouse row {index} is not an object")
            continue
        raw = str(row.get("path") or "")
        try:
            relative = _safe_relative(raw)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        key = relative.as_posix().casefold()
        if key in seen:
            errors.append(f"duplicate case-folded wheel path: {raw}")
            continue
        seen.add(key)
        path = root.joinpath(*relative.parts)
        if path.suffix.casefold() != ".whl" or not path.is_file() or path.is_symlink():
            errors.append(f"wheelhouse member is missing, symlinked, or not a wheel: {raw}")
            continue
        if row.get("size") != path.stat().st_size or row.get("sha256") != _hash(path):
            errors.append(f"wheelhouse member size/hash mismatch: {raw}")
        try:
            distribution, _, _, _ = parse_wheel_filename(path.name)
        except ValueError as exc:
            errors.append(f"invalid wheel filename {path.name}: {exc}")
        else:
            distributions.add(canonicalize_name(distribution))
    return distributions


def discover_wheelhouse(
    search_roots: Iterable[str | Path],
    *,
    profile: str,
    limits: DiscoveryLimits | None = None,
    required_requirements: Iterable[str] | None = None,
) -> dict[str, Any]:
    from certgen.notebooks.environment_bootstrap import COMPATIBILITY_PROFILES

    if profile not in COMPATIBILITY_PROFILES:
        raise ValueError(f"unknown compatibility profile: {profile}")
    requirements = tuple(required_requirements or COMPATIBILITY_PROFILES[profile])
    required = {canonicalize_name(Requirement(raw).name) for raw in requirements}
    selected_limits = limits or DiscoveryLimits()
    files = iter_bounded_files((Path(root) for root in search_roots), limits=selected_limits)
    manifests = [path for path in files if path.name == "wheelhouse_manifest.json"]
    candidates: list[dict[str, Any]] = []
    for manifest in manifests:
        errors: list[str] = []
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            candidates.append({"path": str(manifest), "passed": False, "errors": [str(exc)]})
            continue
        if not isinstance(payload, dict) or payload.get("claim_allowed") is not False:
            errors.append("wheelhouse manifest must be an object with claim_allowed=false")
            payload = {}
        if payload.get("schema_version") != "certgen.wheelhouse_manifest.v1":
            errors.append("wheelhouse manifest schema version mismatch")
        profiles = payload.get("profiles") or [payload.get("profile")]
        if profile not in profiles:
            errors.append(f"wheelhouse does not declare profile: {profile}")
        python_version = str(payload.get("python_version") or "")
        if python_version and python_version != platform.python_version_tuple()[0] + "." + platform.python_version_tuple()[1]:
            errors.append(f"wheelhouse Python version mismatch: {python_version}")
        supported_platforms = payload.get("platforms") or []
        current_platform = sysconfig.get_platform()
        if supported_platforms and "any" not in supported_platforms and current_platform not in supported_platforms:
            errors.append(f"wheelhouse platform mismatch: {current_platform}")
        rows = payload.get("files")
        if not isinstance(rows, list) or not rows:
            errors.append("wheelhouse manifest requires non-empty files rows")
            rows = []
        distributions = _wheel_distributions(manifest.parent, rows, errors)
        missing = sorted(required - distributions)
        if missing:
            errors.append("wheelhouse is missing required distributions: " + ", ".join(missing))
        candidates.append(
            {
                "path": str(manifest),
                "root": str(manifest.parent),
                "passed": not errors,
                "errors": errors,
                "distributions": sorted(distributions),
                "claim_allowed": False,
            }
        )
    matches = [row for row in candidates if row["passed"]]
    status = "SELECTED_UNIQUE_VALID_WHEELHOUSE" if len(matches) == 1 else (
        "NO_MATCHING_WHEELHOUSE" if not matches else "AMBIGUOUS_MATCHING_WHEELHOUSES"
    )
    return {
        "schema_version": "certgen.discovery.wheelhouse.v1",
        "status": status,
        "profile": profile,
        "required_distributions": sorted(required),
        "candidates": candidates,
        "selected": matches[0] if len(matches) == 1 else None,
        "claim_allowed": False,
    }
