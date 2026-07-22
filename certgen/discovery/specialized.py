"""Content-addressed discovery for references, model assets, and wheelhouses."""

from __future__ import annotations

import hashlib
import json
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
    asset_rows: dict[str, list[dict[str, Any]]] = {}
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
        asset_rows.setdefault(asset_id, []).append({**row, "path": relative.as_posix()})
    for required_asset_id, expected_revision in required_assets.items():
        if required_asset_id not in covered:
            errors.append(f"required asset is missing: {required_asset_id}")
        elif expected_revision is not None and expected_revision not in covered[required_asset_id]:
            errors.append(f"required asset revision is missing: {required_asset_id}@{expected_revision}")
    resolution_map: dict[str, dict[str, Any]] = {}
    for asset_id, grouped in sorted(asset_rows.items()):
        revisions = {str(row.get("revision") or "") for row in grouped}
        loaders = {str(row.get("loader_type") or payload.get("loader_type") or "legacy_local_snapshot") for row in grouped}
        licenses = {str(row.get("license_status") or "") for row in grouped}
        snapshot_roots = {str(row.get("snapshot_root") or ".") for row in grouped}
        if len(revisions) != 1:
            errors.append(f"ASSET_REVISION_MISMATCH: conflicting revisions for {asset_id}")
        if len(loaders) != 1 or len(snapshot_roots) != 1:
            errors.append(f"conflicting loader or snapshot-root contract for {asset_id}")
        loader_type = sorted(loaders)[0]
        if payload.get("schema_version") == "certgen.aggregate_asset_manifest.v2" and loader_type not in {
            "from_pretrained_local_snapshot", "torchvision_local_state_dict", "package_resource"
        }:
            errors.append(f"unsupported loader type for {asset_id}: {loader_type}")
        if any(not license_value or license_value.casefold() in {"unknown", "unverified"} for license_value in licenses):
            errors.append(f"asset license status is not approved: {asset_id}")
        try:
            snapshot_relative = _safe_relative(sorted(snapshot_roots)[0]) if sorted(snapshot_roots)[0] != "." else PurePosixPath(".")
        except ValueError as exc:
            errors.append(str(exc))
            continue
        snapshot_root = manifest.parent if snapshot_relative.as_posix() == "." else manifest.parent.joinpath(*snapshot_relative.parts)
        try:
            snapshot_root.resolve().relative_to(manifest.parent.resolve())
        except ValueError:
            errors.append(f"asset snapshot root escapes aggregate mount: {asset_id}")
            continue
        if not snapshot_root.is_dir() or snapshot_root.is_symlink():
            errors.append(f"asset snapshot root is missing or symlinked: {asset_id}")
        inventory = [
            {"path": str(row["path"]), "size": row.get("size"), "sha256": row.get("sha256")}
            for row in sorted(grouped, key=lambda value: str(value["path"]))
        ]
        inventory_hash = hashlib.sha256(
            json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        per_asset_manifest_raw = next(
            (str(row.get("asset_manifest")) for row in grouped if row.get("asset_manifest")), ""
        )
        per_asset_manifest_path: Path | None = None
        per_asset_manifest_hash: str | None = None
        if per_asset_manifest_raw:
            try:
                per_asset_relative = _safe_relative(per_asset_manifest_raw)
                per_asset_manifest_path = manifest.parent.joinpath(*per_asset_relative.parts)
                if not per_asset_manifest_path.is_file() or per_asset_manifest_path.is_symlink():
                    errors.append(f"per-asset manifest is missing or symlinked: {asset_id}")
                else:
                    per_asset_manifest_hash = _hash(per_asset_manifest_path)
            except ValueError as exc:
                errors.append(str(exc))
        elif payload.get("schema_version") == "certgen.aggregate_asset_manifest.v2":
            errors.append(f"per-asset manifest is required: {asset_id}")
        resolution_map[asset_id] = {
            "asset_id": asset_id,
            "model_or_extractor_id": str(grouped[0].get("model_or_extractor_id") or asset_id.removesuffix("__asset")),
            "revision": sorted(revisions)[0] if revisions else None,
            "snapshot_root": str(snapshot_root),
            "inventory_hash": inventory_hash,
            "asset_manifest": str(per_asset_manifest_path) if per_asset_manifest_path else None,
            "asset_manifest_sha256": per_asset_manifest_hash,
            "loader_type": loader_type,
            "license_status": sorted(licenses)[0] if licenses else None,
            "local_files_only": True,
            "runtime_only": True,
            "claim_allowed": False,
        }
    if payload.get("schema_version") == "certgen.aggregate_asset_manifest.v2":
        declared_paths = {str(row.get("path")) for row in rows if isinstance(row, dict)}
        declared_paths.update(
            str(row.get("asset_manifest")) for row in rows if isinstance(row, dict) and row.get("asset_manifest")
        )
        actual_paths = {
            path.relative_to(manifest.parent).as_posix()
            for path in manifest.parent.rglob("*")
            if path.is_file() and not path.is_symlink() and path != manifest
        }
        if actual_paths != declared_paths:
            errors.append("aggregate asset exact membership mismatch")
    content_identity_hash = hashlib.sha256(
        json.dumps(
            {
                asset_id: {
                    key: value
                    for key, value in row.items()
                    if key not in {"snapshot_root", "asset_manifest"}
                }
                for asset_id, row in sorted(resolution_map.items())
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    return {
        "path": str(manifest),
        "root": str(manifest.parent),
        "aggregate_manifest_sha256": _hash(manifest),
        "content_identity_hash": content_identity_hash,
        "passed": not errors,
        "errors": errors,
        "asset_ids": sorted(covered),
        "resolution_map": resolution_map,
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
    identities = {row.get("content_identity_hash") for row in matches}
    selected = sorted(matches, key=lambda row: str(row["path"]).casefold())[0] if matches and len(identities) == 1 else None
    status = "SELECTED_UNIQUE_VALID_ASSET_MOUNT" if len(matches) == 1 else (
        "NO_MATCHING_ASSET_MOUNT" if not matches else
        "DUPLICATE_IDENTICAL_COPY_DEDUPED" if len(identities) == 1 else
        "AMBIGUOUS_DIFFERENT_CONTENT"
    )
    return {
        "schema_version": "certgen.discovery.assets.v1",
        "status": status,
        "required_assets": dict(required_assets),
        "candidates": rows,
        "selected": selected,
        "claim_allowed": False,
    }


def write_asset_resolution_report(resolution: Mapping[str, Any], path: str | Path) -> dict[str, Any]:
    selected = resolution.get("selected")
    if not isinstance(selected, dict) or not isinstance(selected.get("resolution_map"), dict):
        raise ValueError(f"asset resolution is not selectable: {resolution.get('status')}")
    payload = {
        "schema_version": "certgen.asset_resolution_report.v1",
        "status": resolution.get("status"),
        "aggregate_manifest_sha256": selected.get("aggregate_manifest_sha256"),
        "assets": [selected["resolution_map"][key] for key in sorted(selected["resolution_map"])],
        "runtime_only": True,
        "claim_allowed": False,
    }
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.partial")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)
    return payload


def validate_resolved_asset(
    report_path: str | Path,
    *,
    asset_id: str,
    expected_revision: str,
) -> dict[str, Any]:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    if not isinstance(report, dict) or report.get("claim_allowed") is not False or report.get("runtime_only") is not True:
        raise ValueError("asset resolution report is invalid")
    rows = report.get("assets")
    if not isinstance(rows, list):
        raise ValueError("asset resolution report has no asset rows")
    matches = [row for row in rows if isinstance(row, dict) and row.get("asset_id") == asset_id]
    if len(matches) != 1:
        raise ValueError(f"asset resolution requires exactly one row for {asset_id}")
    row = matches[0]
    if row.get("revision") != expected_revision:
        raise ValueError(f"ASSET_REVISION_MISMATCH: {asset_id}")
    if row.get("local_files_only") is not True or row.get("runtime_only") is not True:
        raise ValueError("offline resolved asset must be runtime-only and local-files-only")
    root = Path(str(row.get("snapshot_root")))
    if not root.is_dir() or root.is_symlink():
        raise FileNotFoundError(f"resolved asset snapshot is missing or symlinked: {asset_id}")
    manifest_raw = row.get("asset_manifest")
    if not manifest_raw:
        raise ValueError(f"resolved asset has no per-asset manifest: {asset_id}")
    manifest = Path(str(manifest_raw))
    if not manifest.is_file() or manifest.is_symlink() or _hash(manifest) != row.get("asset_manifest_sha256"):
        raise ValueError(f"ASSET_HASH_MISMATCH: per-asset manifest for {asset_id}")
    from certgen.notebooks.model_assets import validate_asset_manifest

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    validate_asset_manifest(payload, manifest_root=manifest.parent, cache_root=root)
    return dict(row)


def _wheel_distributions(
    root: Path,
    rows: list[dict[str, Any]],
    errors: list[str],
    *,
    target_python: str,
    target_platform: str,
    exact: bool,
) -> dict[str, list[dict[str, Any]]]:
    distributions: dict[str, list[dict[str, Any]]] = {}
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
            distribution, version, _, tags = parse_wheel_filename(path.name)
        except ValueError as exc:
            errors.append(f"invalid wheel filename {path.name}: {exc}")
        else:
            canonical = canonicalize_name(distribution)
            compatible_tags = []
            for tag in tags:
                interpreter_ok = tag.interpreter in {target_python, "py3", "py311"}
                abi_ok = tag.abi in {"none", "abi3", target_python}
                platform_ok = tag.platform == "any" or (
                    tag.platform.endswith("_x86_64")
                    and (tag.platform.startswith("manylinux") or tag.platform == "linux_x86_64")
                    and target_platform in {"manylinux_x86_64", "linux_x86_64"}
                )
                if interpreter_ok and abi_ok and platform_ok:
                    compatible_tags.append(str(tag))
            if exact and not compatible_tags:
                errors.append(f"WHEEL_TAG_INCOMPATIBLE: {path.name} for {target_python}/{target_platform}")
            distributions.setdefault(canonical, []).append(
                {
                    "path": raw,
                    "version": str(version),
                    "tags": sorted(str(tag) for tag in tags),
                    "compatible_tags": sorted(compatible_tags),
                    "sha256": row.get("sha256"),
                }
            )
    return distributions


def discover_wheelhouse(
    search_roots: Iterable[str | Path],
    *,
    profile: str,
    limits: DiscoveryLimits | None = None,
    required_requirements: Iterable[str] | None = None,
    target_python: str = "cp311",
    target_platform: str = "manylinux_x86_64",
) -> dict[str, Any]:
    from certgen.notebooks.environment_bootstrap import COMPATIBILITY_PROFILES

    if profile not in COMPATIBILITY_PROFILES:
        raise ValueError(f"unknown compatibility profile: {profile}")
    requirements = tuple(required_requirements or COMPATIBILITY_PROFILES[profile])
    parsed_requirements = tuple(Requirement(raw) for raw in requirements)
    required = {canonicalize_name(requirement.name) for requirement in parsed_requirements}
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
        schema_version = payload.get("schema_version")
        if schema_version not in {"certgen.wheelhouse_manifest.v1", "certgen.wheelhouse_manifest.v2"}:
            errors.append("wheelhouse manifest schema version mismatch")
        exact = schema_version == "certgen.wheelhouse_manifest.v2"
        profiles = payload.get("profiles") or [payload.get("profile")]
        if profile not in profiles:
            errors.append(f"wheelhouse does not declare profile: {profile}")
        python_version = str(payload.get("target_python") or payload.get("python_version") or "")
        accepted_python_values = {target_python, "3.11" if target_python == "cp311" else target_python.removeprefix("cp")}
        if python_version and python_version not in accepted_python_values:
            errors.append(f"wheelhouse Python target mismatch: {python_version}")
        supported_platforms = payload.get("platforms") or []
        if supported_platforms and "any" not in supported_platforms and target_platform not in supported_platforms:
            errors.append(f"wheelhouse platform target mismatch: {target_platform}")
        rows = payload.get("files")
        if not isinstance(rows, list) or not rows:
            errors.append("wheelhouse manifest requires non-empty files rows")
            rows = []
        distributions = _wheel_distributions(
            manifest.parent,
            rows,
            errors,
            target_python=target_python,
            target_platform=target_platform,
            exact=exact,
        )
        missing = sorted(required - set(distributions))
        if missing:
            errors.append("wheelhouse is missing required distributions: " + ", ".join(missing))
        if exact:
            for requirement in parsed_requirements:
                canonical = canonicalize_name(requirement.name)
                wheels = distributions.get(canonical, [])
                compatible_versions = [row for row in wheels if row["version"] in requirement.specifier and row["compatible_tags"]]
                if wheels and not compatible_versions:
                    errors.append(
                        f"WHEEL_VERSION_MISMATCH: {requirement}; observed="
                        + ",".join(sorted({str(row['version']) for row in wheels}))
                    )
                distinct_versions = {row["version"] for row in compatible_versions}
                if len(distinct_versions) > 1:
                    errors.append(f"conflicting compatible wheel versions for {requirement.name}")
            declared_paths = {str(row.get("path")) for row in rows if isinstance(row, dict)}
            actual_files = {
                path.relative_to(manifest.parent).as_posix()
                for path in manifest.parent.rglob("*")
                if path.is_file() and path != manifest
            }
            if any(path.casefold().endswith((".tar.gz", ".zip", ".tgz")) for path in actual_files):
                errors.append("source distributions are forbidden in an exact wheelhouse")
            if actual_files != declared_paths:
                errors.append("exact wheelhouse manifest membership mismatch")
        content_identity_hash = hashlib.sha256(
            json.dumps(distributions, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        candidates.append(
            {
                "path": str(manifest),
                "root": str(manifest.parent),
                "passed": not errors,
                "errors": errors,
                "distributions": sorted(distributions),
                "wheels": distributions,
                "content_identity_hash": content_identity_hash,
                "claim_allowed": False,
            }
        )
    matches = [row for row in candidates if row["passed"]]
    identities = {row.get("content_identity_hash") for row in matches}
    selected = sorted(matches, key=lambda row: str(row["path"]).casefold())[0] if matches and len(identities) == 1 else None
    status = "SELECTED_UNIQUE_VALID_WHEELHOUSE" if len(matches) == 1 else (
        "NO_MATCHING_WHEELHOUSE" if not matches else
        "DUPLICATE_IDENTICAL_COPY_DEDUPED" if len(identities) == 1 else
        "AMBIGUOUS_DIFFERENT_CONTENT"
    )
    return {
        "schema_version": "certgen.discovery.wheelhouse.v1",
        "status": status,
        "profile": profile,
        "required_distributions": sorted(required),
        "candidates": candidates,
        "target_python": target_python,
        "target_platform": target_platform,
        "selected": selected,
        "claim_allowed": False,
    }
