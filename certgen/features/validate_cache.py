"""Feature-cache manifest validation."""

from __future__ import annotations

from pathlib import Path


from certgen.certs.io import load_feature_array
from certgen.core.enums import NON_EVIDENCE_STATUSES
from certgen.core.hashing import file_sha256
from certgen.core.io import read_json


REQUIRED_MANIFEST_FIELDS = {
    "cache_id",
    "dataset_id",
    "split",
    "sample_source_type",
    "model_or_generator_id",
    "feature_extractor",
    "feature_extractor_version",
    "preprocessing_policy_id",
    "resize_size",
    "crop_policy",
    "interpolation",
    "normalization",
    "num_samples",
    "feature_dim",
    "feature_file_path",
    "feature_file_sha256",
    "source_license_status",
    "download_or_local_source_note",
    "evidence_status",
    "created_at",
}


def validate_feature_cache_manifest(path: str | Path) -> list[str]:
    manifest = read_json(path)
    errors: list[str] = []
    missing = sorted(REQUIRED_MANIFEST_FIELDS - set(manifest))
    errors.extend(f"missing field: {field}" for field in missing)
    for field in ["resize_size", "crop_policy", "interpolation", "normalization", "feature_extractor"]:
        if manifest.get(field) in {None, "", "default", "unknown", "TBD"}:
            errors.append(f"{field} must be explicit")
    if manifest.get("source_license_status") in {None, "", "unknown", "TBD"}:
        errors.append("source_license_status must be known")
    status = manifest.get("evidence_status")
    if status not in NON_EVIDENCE_STATUSES:
        errors.append("real-evidence feature caches require future provenance gates")
    feature_path = Path(manifest.get("feature_file_path", ""))
    if not feature_path.exists():
        errors.append(f"feature file missing: {feature_path}")
        return errors
    try:
        features = load_feature_array(feature_path)
        expected_shape = (int(manifest.get("num_samples")), int(manifest.get("feature_dim")))
        if tuple(features.shape) != expected_shape:
            errors.append(f"shape mismatch: expected {expected_shape}, got {tuple(features.shape)}")
        actual_hash = file_sha256(feature_path)
        if manifest.get("feature_file_sha256") != actual_hash:
            errors.append("feature_file_sha256 mismatch")
    except Exception as exc:
        errors.append(str(exc))
    return errors
