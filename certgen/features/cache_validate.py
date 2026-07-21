"""Strict V3 feature-cache validation."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from certgen.core.hashing import file_sha256
from certgen.core.io import read_json, write_json
from certgen.features.cache_contracts import V3FeatureCacheValidation


def validate_v3_feature_cache(
    *,
    features_path: str | Path,
    sidecar_path: str | Path,
    strict_hash: bool = False,
    metric: str | None = None,
    allow_constant: bool = False,
) -> V3FeatureCacheValidation:
    errors: list[str] = []
    warnings: list[str] = []
    features_path = Path(features_path)
    sidecar_path = Path(sidecar_path)
    if not features_path.exists():
        errors.append(f"features file missing: {features_path}")
        return V3FeatureCacheValidation(False, errors, warnings, "real_features_unvalidated", False)
    if not sidecar_path.exists():
        errors.append(f"sidecar missing: {sidecar_path}")
        return V3FeatureCacheValidation(False, errors, warnings, "real_features_unvalidated", False)
    sidecar = read_json(sidecar_path)
    with np.load(features_path, allow_pickle=False) as loaded:
        if "features" not in loaded:
            errors.append("npz missing features array")
            arr = np.empty((0, 0))
        else:
            arr = np.asarray(loaded["features"])
        for optional in ["sample_ids", "source_paths"]:
            if optional not in loaded:
                warnings.append(f"{optional} absent")
    if arr.ndim != 2:
        errors.append(f"features must be 2D, got {arr.shape}")
    elif not np.issubdtype(arr.dtype, np.floating):
        errors.append("features must be float32 or float64")
    elif not np.all(np.isfinite(arr)):
        errors.append("features contain NaN/Inf")
    elif not allow_constant and (np.allclose(arr, 0) or float(np.std(arr)) < 1e-12):
        errors.append("features are all constant or near-zero")
    preprocessing = sidecar.get("preprocessing") or {}
    source = sidecar.get("source") or {}
    hashes = sidecar.get("hashes") or {}
    expected_n_samples = sidecar.get("n_samples", sidecar.get("num_items"))
    expected_feature_dim = sidecar.get("feature_dim")
    if expected_n_samples != int(arr.shape[0] if arr.ndim == 2 else -1):
        errors.append("n_samples mismatch")
    if expected_feature_dim != int(arr.shape[1] if arr.ndim == 2 else -1):
        errors.append("feature_dim mismatch")
    resize_value = preprocessing.get("resize", preprocessing.get("image_size", preprocessing.get("resize_policy")))
    if resize_value in {None, "", "default", "unknown", "TBD"}:
        errors.append("preprocessing.resize missing or vague")
    if preprocessing.get("interpolation") in {None, "", "default", "unknown", "TBD"}:
        errors.append("preprocessing.interpolation missing or vague")
    crop_value = preprocessing.get("crop", preprocessing.get("crop_policy", "none"))
    if crop_value in {"", "default", "unknown", "TBD"}:
        errors.append("preprocessing.crop missing or vague")
    if preprocessing.get("normalization") in {None, "", "default", "unknown", "TBD"}:
        errors.append("preprocessing.normalization missing or vague")
    if source.get("license_status") in {"restricted", "not_allowed"}:
        errors.append("source license blocks use")
    elif source.get("license_status") == "unknown":
        warnings.append("license unknown")
    if not sidecar.get("created_by"):
        warnings.append("created_by absent")
    source_manifest_hash = hashes.get("source_manifest_sha256") or sidecar.get("source_manifest_sha256")
    if not source_manifest_hash:
        warnings.append("source_manifest_sha256 absent")
    actual = file_sha256(features_path)
    declared_features_hash = hashes.get("features_sha256") or sidecar.get("features_sha256") or sidecar.get("hash")
    if strict_hash and declared_features_hash != actual:
        errors.append("features_sha256 mismatch")
    extractor = sidecar.get("feature_extractor") or sidecar.get("extractor") or sidecar.get("feature_type", "")
    if metric and metric.lower().startswith("fid") and "inception" not in extractor and extractor != "custom":
        errors.append("feature extractor incompatible with requested FID metric")
    evidence_status = "real_features_validated" if not errors else "real_features_unvalidated"
    return V3FeatureCacheValidation(not errors, errors, warnings, evidence_status, False, tuple(arr.shape) if arr.ndim == 2 else None, sidecar)


def write_v3_feature_cache_report(result: V3FeatureCacheValidation, out: str | Path, json_out: str | Path) -> None:
    payload = {
        "passed": result.passed,
        "errors": result.errors,
        "warnings": result.warnings,
        "evidence_status": result.evidence_status,
        "claim_allowed": result.claim_allowed,
        "feature_shape": list(result.feature_shape) if result.feature_shape else None,
    }
    lines = ["# Feature Cache Validation V3", "", "`NO_REAL_EVIDENCE`", "", f"Passed: `{result.passed}`", f"Evidence status: `{result.evidence_status}`", "Claim allowed: `False`", "", "## Errors"]
    lines.extend(f"- {e}" for e in result.errors or ["none"])
    lines.append("")
    lines.append("## Warnings")
    lines.extend(f"- {w}" for w in result.warnings or ["none"])
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
