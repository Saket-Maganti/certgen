import numpy as np
import pytest

from certgen.audit.metric_reproduction import run_metric_reproduction_audit
from certgen.core.hashing import file_sha256
from certgen.core.io import write_json
from certgen.metrics.mmd import unbiased_mmd2


def _cache(tmp_path, name, arr):
    npz = tmp_path / f"{name}.npz"
    np.savez_compressed(npz, features=arr, sample_ids=np.arange(len(arr)), source_paths=np.array([str(i) for i in range(len(arr))]))
    sidecar = tmp_path / f"{name}.json"
    write_json(
        {
            "cache_id": name,
            "benchmark_id": "bench",
            "model_id": name,
            "split": "test",
            "feature_extractor": "custom",
            "feature_dim": arr.shape[1],
            "n_samples": arr.shape[0],
            "preprocessing": {"resize": "none", "interpolation": "none", "crop": "none", "normalization": "none"},
            "source": {"type": "precomputed_features", "uri_or_path": str(npz), "license_status": "verified_free"},
            "hashes": {"features_sha256": file_sha256(npz), "source_manifest_sha256": "smoke"},
            "created_by": "test",
            "created_at": "2026-06-23",
            "certgen_version": "0.3.0",
        },
        sidecar,
    )
    return npz, sidecar


def test_metric_reproduction_expected_modes(tmp_path):
    ref_npz, ref_json = _cache(tmp_path, "ref", np.arange(24, dtype=float).reshape(12, 2))
    model_npz, model_json = _cache(tmp_path, "model", np.arange(24, dtype=float).reshape(12, 2))
    config = tmp_path / "cfg.json"
    write_json(
        {
            "metric": "kid",
            "reference_features": {"npz": str(ref_npz), "sidecar": str(ref_json)},
            "model_features": {"npz": str(model_npz), "sidecar": str(model_json)},
            "expected": {"source": "internal_fixture", "value": 0.0, "tolerance_abs": 1e-9},
            "sample_count": 12,
        },
        config,
    )
    result = run_metric_reproduction_audit(config, tmp_path / "out.md", tmp_path / "out.json")
    assert result["within_tolerance"] is True
    assert result["claim_allowed"] is False
    write_json({**result, "dummy": "unused"}, tmp_path / "ignored.json")


def test_metric_reproduction_mismatch_and_fid_descriptive(tmp_path):
    ref_npz, ref_json = _cache(tmp_path, "ref", np.arange(24, dtype=float).reshape(12, 2))
    model_npz, model_json = _cache(tmp_path, "model", np.ones((12, 2)))
    config = tmp_path / "cfg.json"
    write_json(
        {
            "metric": "fid",
            "reference_features": {"npz": str(ref_npz), "sidecar": str(ref_json)},
            "model_features": {"npz": str(model_npz), "sidecar": str(model_json)},
            "expected": {"source": "none"},
            "sample_count": 12,
        },
        config,
    )
    result = run_metric_reproduction_audit(config, tmp_path / "out.md", tmp_path / "out.json")
    assert result["fid_descriptive_only"] is True
    assert result["rigorous_certification_supported"] is False


def test_mmd_rbf_reproduction_matches_certificate_l2_convention(tmp_path):
    reference = np.array([[1.0, 0.0], [2.0, 0.0], [3.0, 0.0], [4.0, 0.0]])
    model = np.array([[1.0, 1.0], [2.0, 1.0], [3.0, 1.0], [4.0, 1.0]])
    ref_npz, ref_json = _cache(tmp_path, "ref", reference)
    model_npz, model_json = _cache(tmp_path, "model", model)
    expected = unbiased_mmd2(model, reference, kernel="rbf", normalize="l2")
    unnormalised = unbiased_mmd2(model, reference, kernel="rbf")
    assert expected != pytest.approx(unnormalised)

    config = tmp_path / "cfg.json"
    write_json(
        {
            "metric": "mmd_rbf",
            "reference_features": {"npz": str(ref_npz), "sidecar": str(ref_json)},
            "model_features": {"npz": str(model_npz), "sidecar": str(model_json)},
            "expected": {"source": "internal_fixture", "value": expected, "tolerance_abs": 1e-12},
            "sample_count": 4,
        },
        config,
    )

    result = run_metric_reproduction_audit(config, tmp_path / "out.md", tmp_path / "out.json")

    assert result["computed_value"] == pytest.approx(expected)
    assert result["within_tolerance"] is True
