from __future__ import annotations

import numpy as np
import pytest

from certgen.metrics.kernels import rbf_kernel, rbf_kernel_paired
from certgen.metrics.streams import mmd_difference_stream, paired_mmd_difference_contributions
from certgen.icml2027.production_mmd import binomial_wilson_interval


@pytest.mark.parametrize("dimension", [2, 16, 64, 768, 2048])
@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_paired_rbf_matches_small_matrix_diagonal(dimension: int, dtype: np.dtype) -> None:
    rng = np.random.default_rng(2027 + dimension)
    x = rng.normal(size=(18, dimension)).astype(dtype)
    y = rng.normal(size=(18, dimension)).astype(dtype)
    expected = np.diag(rbf_kernel(x, y, gamma=0.5))
    actual = rbf_kernel_paired(x, y, gamma=0.5, chunk_size=5)
    np.testing.assert_allclose(actual, expected, rtol=2e-6, atol=2e-7)


def test_paired_difference_matches_legacy_small_matrix_path() -> None:
    rng = np.random.default_rng(19)
    arrays = [rng.normal(size=(20, 7)).astype(np.float64) for _ in range(3)]
    kernel = {"name": "rbf", "gamma": 0.5, "normalize": "l2"}
    order = np.random.default_rng(4).permutation(20)
    normalized = [value / np.linalg.norm(value, axis=1, keepdims=True) for value in arrays]
    a, b, r = [value[order] for value in normalized]
    expected = (
        np.diag(rbf_kernel(a[0::2], a[1::2], gamma=0.5))
        - np.diag(rbf_kernel(b[0::2], b[1::2], gamma=0.5))
        - np.diag(rbf_kernel(a[0::2], r[1::2], gamma=0.5))
        - np.diag(rbf_kernel(a[1::2], r[0::2], gamma=0.5))
        + np.diag(rbf_kernel(b[0::2], r[1::2], gamma=0.5))
        + np.diag(rbf_kernel(b[1::2], r[0::2], gamma=0.5))
    )
    actual = paired_mmd_difference_contributions(
        arrays[0], arrays[1], arrays[2], kernel, indices=order, chunk_size=3
    )
    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)


def test_paired_path_supports_memory_maps_without_materializing_gram_matrix(tmp_path) -> None:
    shape = (128, 64)
    paths = [tmp_path / f"features_{index}.npy" for index in range(3)]
    rng = np.random.default_rng(21)
    for path in paths:
        np.save(path, rng.normal(size=shape).astype(np.float32))
    arrays = [np.load(path, mmap_mode="r") for path in paths]
    stream = mmd_difference_stream(
        arrays[0],
        arrays[1],
        arrays[2],
        {"name": "rbf", "gamma": 0.5, "normalize": "l2"},
        kernel_chunk_size=11,
    )
    assert stream.metadata["kernel_computation"] == "paired_rbf_o_nd_no_gram_matrix"
    assert stream.metadata["input_memory_mapping_preserved"] is True
    assert len(stream.values) == 64
    assert np.all(np.isfinite(stream.values))


@pytest.mark.integration_audit
@pytest.mark.parametrize("dimension", [768, 2048])
def test_large_cache_memmap_path_10k_rows(dimension: int, tmp_path) -> None:
    arrays = []
    for index in range(3):
        path = tmp_path / f"large_{dimension}_{index}.npy"
        array = np.lib.format.open_memmap(path, mode="w+", dtype=np.float32, shape=(10_000, dimension))
        array[:, 0] = 1.0
        array.flush()
        arrays.append(np.load(path, mmap_mode="r"))
    stream = mmd_difference_stream(
        arrays[0],
        arrays[1],
        arrays[2],
        {"name": "rbf", "gamma": 0.5, "normalize": "l2"},
        kernel_chunk_size=256,
    )
    assert len(stream.values) == 5000
    assert set(stream.values) == {0.0}
    assert stream.metadata["input_memory_mapping_preserved"] is True


@pytest.mark.parametrize("bad_dtype", [np.int64, np.float16])
def test_paired_kernel_rejects_unsupported_dtypes(bad_dtype: np.dtype) -> None:
    with pytest.raises(TypeError):
        rbf_kernel_paired(np.ones((4, 2), dtype=bad_dtype), np.ones((4, 2), dtype=bad_dtype))


def test_wilson_interval_records_replication_uncertainty() -> None:
    lower, upper = binomial_wilson_interval(0, 20)
    assert lower == 0.0
    assert upper is not None and upper > 0.0
    assert binomial_wilson_interval(0, 0) == [None, None]
