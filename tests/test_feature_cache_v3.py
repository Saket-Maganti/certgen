
import numpy as np

from certgen.core.hashing import file_sha256
from certgen.core.io import write_json
from certgen.features.cache_validate import validate_v3_feature_cache


def _sidecar(path, feature_path, *, license_status="verified_free", n=4, d=2, hash_value=None):
    write_json(
        {
            "cache_id": "cache",
            "benchmark_id": "bench",
            "model_id": "model",
            "split": "test",
            "feature_extractor": "custom",
            "feature_dim": d,
            "n_samples": n,
            "preprocessing": {"resize": "none", "interpolation": "none", "crop": "none", "normalization": "none"},
            "source": {"type": "precomputed_features", "uri_or_path": str(feature_path), "license_status": license_status},
            "hashes": {"features_sha256": hash_value or file_sha256(feature_path), "source_manifest_sha256": "smoke"},
            "created_by": "test",
            "created_at": "2026-06-23T00:00:00Z",
            "certgen_version": "0.3.0",
        },
        path,
    )


def test_valid_and_invalid_v3_feature_caches(tmp_path):
    features = tmp_path / "features.npz"
    np.savez_compressed(features, features=np.arange(8, dtype=float).reshape(4, 2), sample_ids=np.arange(4), source_paths=np.array(["a", "b", "c", "d"]))
    sidecar = tmp_path / "sidecar.json"
    _sidecar(sidecar, features)
    assert validate_v3_feature_cache(features_path=features, sidecar_path=sidecar, strict_hash=True).passed

    nan = tmp_path / "nan.npz"
    np.savez_compressed(nan, features=np.array([[float("nan"), 1.0], [0.0, 2.0]]))
    _sidecar(tmp_path / "nan.json", nan, n=2)
    assert not validate_v3_feature_cache(features_path=nan, sidecar_path=tmp_path / "nan.json").passed

    zeros = tmp_path / "zeros.npz"
    np.savez_compressed(zeros, features=np.zeros((4, 2)))
    _sidecar(tmp_path / "zeros.json", zeros)
    assert not validate_v3_feature_cache(features_path=zeros, sidecar_path=tmp_path / "zeros.json").passed

    _sidecar(tmp_path / "restricted.json", features, license_status="restricted")
    assert not validate_v3_feature_cache(features_path=features, sidecar_path=tmp_path / "restricted.json").passed
