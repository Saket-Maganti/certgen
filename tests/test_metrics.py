import numpy as np
import pytest

from certgen.core.io import make_feature_manifest, save_feature_npz, validate_feature_manifest
from certgen.metrics.cmmd import cmmd_polynomial
from certgen.metrics.fid import frechet_distance, fid_metric_record
from certgen.metrics.kid import kid_polynomial
from certgen.metrics.mmd import unbiased_mmd2


def test_mmd_zero_for_identical_arrays():
    x = np.arange(20, dtype=float).reshape(10, 2)
    assert unbiased_mmd2(x, x) == 0.0


def test_mmd_positive_for_shifted_toy_distributions():
    x = np.zeros((10, 2))
    y = np.ones((10, 2))
    assert unbiased_mmd2(x, y) > 0


def test_kid_wrapper_uses_mmd_logic():
    x = np.zeros((10, 2))
    y = np.ones((10, 2))
    assert kid_polynomial(x, y) == unbiased_mmd2(x, y)


def test_cmmd_wrapper_accepts_arbitrary_feature_arrays():
    x = np.zeros((10, 4))
    y = np.ones((10, 4))
    assert cmmd_polynomial(x, y) > 0


def test_fid_zero_for_identical_arrays():
    x = np.arange(40, dtype=float).reshape(10, 4)
    assert abs(frechet_distance(x, x)) < 1e-12


def test_fid_metric_record_is_descriptive_only():
    record = fid_metric_record()
    assert record.supports_clean_cs is False
    assert record.fid_rigor_status == "descriptive_only"


def test_feature_manifest_rejects_shape_mismatch(tmp_path):
    path = tmp_path / "features.npz"
    save_feature_npz(np.zeros((4, 2)), path)
    manifest = make_feature_manifest("toy", "toy_feature", str(path), {}, "non_evidence_smoke")
    manifest.num_items = 5
    with pytest.raises(ValueError, match="shape mismatch"):
        validate_feature_manifest(manifest)
