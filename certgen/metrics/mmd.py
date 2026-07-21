"""CPU-safe MMD helpers over feature arrays."""

from __future__ import annotations

import numpy as np

from certgen.metrics.kernels import kernel_matrix


def _as_2d_float(array: np.ndarray) -> np.ndarray:
    value = np.asarray(array, dtype=float)
    if value.ndim != 2:
        raise ValueError(f"Expected a 2D feature array, got shape {value.shape}")
    return value


def _kernel_matrix(x: np.ndarray, y: np.ndarray, *, kernel: str, **kwargs) -> np.ndarray:
    return kernel_matrix(x, y, {"name": kernel, **kwargs})


def unbiased_mmd2(x: np.ndarray, y: np.ndarray, *, kernel: str = "poly", **kwargs) -> float:
    x = _as_2d_float(x)
    y = _as_2d_float(y)
    if x.shape[1] != y.shape[1]:
        raise ValueError(f"Feature dimensions must match, got {x.shape[1]} and {y.shape[1]}")
    if len(x) < 2 or len(y) < 2:
        raise ValueError("Unbiased MMD requires at least two samples in each array")
    if np.array_equal(x, y):
        return 0.0

    kxx = _kernel_matrix(x, x, kernel=kernel, **kwargs)
    kyy = _kernel_matrix(y, y, kernel=kernel, **kwargs)
    kxy = _kernel_matrix(x, y, kernel=kernel, **kwargs)

    np.fill_diagonal(kxx, 0.0)
    np.fill_diagonal(kyy, 0.0)
    m = len(x)
    n = len(y)
    return float(kxx.sum() / (m * (m - 1)) + kyy.sum() / (n * (n - 1)) - 2.0 * kxy.mean())


def block_mmd2_estimates(
    x: np.ndarray,
    y: np.ndarray,
    *,
    block_size: int = 16,
    kernel: str = "poly",
    **kwargs,
) -> list[float]:
    x = _as_2d_float(x)
    y = _as_2d_float(y)
    count = min(len(x), len(y))
    estimates: list[float] = []
    for start in range(0, count, block_size):
        stop = min(start + block_size, count)
        if stop - start >= 2:
            estimates.append(unbiased_mmd2(x[start:stop], y[start:stop], kernel=kernel, **kwargs))
    return estimates


def delta_stream_from_blocks(
    model_a: np.ndarray,
    model_b: np.ndarray,
    reference: np.ndarray,
    *,
    block_size: int = 16,
    kernel: str = "poly",
    **kwargs,
) -> list[float]:
    a = _as_2d_float(model_a)
    b = _as_2d_float(model_b)
    r = _as_2d_float(reference)
    count = min(len(a), len(b), len(r))
    deltas: list[float] = []
    for start in range(0, count, block_size):
        stop = min(start + block_size, count)
        if stop - start >= 2:
            a_dist = unbiased_mmd2(a[start:stop], r[start:stop], kernel=kernel, **kwargs)
            b_dist = unbiased_mmd2(b[start:stop], r[start:stop], kernel=kernel, **kwargs)
            deltas.append(float(a_dist - b_dist))
    return deltas
