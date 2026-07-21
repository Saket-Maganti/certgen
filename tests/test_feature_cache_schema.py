
import numpy as np

from certgen.core.hashing import file_sha256
from certgen.core.io import write_json
from certgen.features.preprocessing import PreprocessingPolicy
from certgen.features.validate_cache import validate_feature_cache_manifest


def _manifest(tmp_path, feature_path):
    return {
        "cache_id": "cache_smoke",
        "dataset_id": "dataset",
        "split": "test",
        "sample_source_type": "smoke_fixture",
        "model_or_generator_id": "model",
        "feature_extractor": "clip",
        "feature_extractor_version": "smoke",
        "preprocessing_policy_id": "policy",
        "resize_size": "none",
        "crop_policy": "none",
        "interpolation": "nearest",
        "normalization": "none",
        "num_samples": 4,
        "feature_dim": 2,
        "feature_file_path": str(feature_path),
        "feature_file_sha256": file_sha256(feature_path),
        "source_license_status": "smoke_fixture",
        "download_or_local_source_note": "NO_REAL_EVIDENCE",
        "evidence_status": "smoke_only",
        "created_at": "2026-06-23T00:00:00Z",
    }


def test_valid_smoke_feature_cache_manifest(tmp_path):
    feature_path = tmp_path / "features.npz"
    np.savez_compressed(feature_path, features=np.zeros((4, 2)))
    manifest_path = tmp_path / "manifest.json"
    write_json(_manifest(tmp_path, feature_path), manifest_path)
    assert validate_feature_cache_manifest(manifest_path) == []


def test_invalid_feature_cache_manifest_errors(tmp_path):
    feature_path = tmp_path / "features.npz"
    np.savez_compressed(feature_path, features=np.zeros((4, 2)))
    manifest = _manifest(tmp_path, feature_path)
    manifest["interpolation"] = "default"
    manifest["source_license_status"] = "unknown"
    manifest["num_samples"] = 5
    manifest["feature_file_sha256"] = "bad"
    path = tmp_path / "manifest.json"
    write_json(manifest, path)
    errors = validate_feature_cache_manifest(path)
    assert any("interpolation" in error for error in errors)
    assert any("source_license_status" in error for error in errors)
    assert any("shape mismatch" in error for error in errors)
    assert any("sha256" in error for error in errors)


def test_preprocessing_policy_rejects_vague_defaults():
    policy = PreprocessingPolicy("p", "default", "none", "nearest", "none", "clip")
    try:
        policy.validate()
    except ValueError as exc:
        assert "resize_size" in str(exc)
    else:
        raise AssertionError("expected validation failure")
