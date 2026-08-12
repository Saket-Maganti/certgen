"""Pure NumPy kernels for V2 clean-core metrics."""

from __future__ import annotations

import numpy as np


def as_2d_float64(array: np.ndarray, *, name: str = "array") -> np.ndarray:
    value = np.asarray(array, dtype=np.float64)
    if value.ndim != 2:
        raise ValueError(f"{name} must be a 2D array, got shape {value.shape}")
    if not np.all(np.isfinite(value)):
        raise ValueError(f"{name} contains non-finite values")
    return value


def _validate_pair(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x = as_2d_float64(x, name="x")
    y = as_2d_float64(y, name="y")
    if x.shape[1] != y.shape[1]:
        raise ValueError(f"feature dimensions must match, got {x.shape[1]} and {y.shape[1]}")
    return x, y


def l2_normalize_rows(array: np.ndarray, *, name: str = "array") -> np.ndarray:
    value = as_2d_float64(array, name=name)
    norms = np.linalg.norm(value, axis=1)
    if np.any(norms <= 0.0):
        raise ValueError(f"{name} contains zero-norm rows; cannot certify normalized bounded kernel stream")
    return value / norms[:, None]


def linear_kernel(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    x, y = _validate_pair(x, y)
    return x @ y.T


def polynomial_kernel(x: np.ndarray, y: np.ndarray, *, degree: int = 3, gamma: float | None = None, coef0: float = 1.0) -> np.ndarray:
    x, y = _validate_pair(x, y)
    gamma = gamma if gamma is not None else 1.0 / max(1, x.shape[1])
    return (gamma * (x @ y.T) + coef0) ** degree


def rbf_kernel(x: np.ndarray, y: np.ndarray, *, gamma: float | None = None) -> np.ndarray:
    x, y = _validate_pair(x, y)
    gamma = gamma if gamma is not None else 1.0 / max(1, x.shape[1])
    gamma = float(gamma)
    if not np.isfinite(gamma) or gamma <= 0.0:
        raise ValueError("RBF gamma must be finite and strictly positive")
    x_norm = np.sum(x * x, axis=1)[:, None]
    y_norm = np.sum(y * y, axis=1)[None, :]
    distances = np.maximum(x_norm + y_norm - 2.0 * x @ y.T, 0.0)
    return np.exp(-gamma * distances)


def rbf_kernel_paired(
    x: np.ndarray,
    y: np.ndarray,
    *,
    gamma: float | None = None,
    chunk_size: int = 4096,
) -> np.ndarray:
    """Evaluate only ``k(x[i], y[i])`` in O(ND) time and chunk memory.

    Unlike ``diag(rbf_kernel(x, y))``, this primitive never constructs an
    ``N x N`` Gram matrix.  It accepts float32 or float64 arrays (including
    memory maps), performs the distance accumulation in float64 for stable
    parity with :func:`rbf_kernel`, and returns one float64 value per row.
    """

    left = np.asanyarray(x)
    right = np.asanyarray(y)
    if left.ndim != 2 or right.ndim != 2:
        raise ValueError(f"x and y must be 2D arrays, got {left.shape} and {right.shape}")
    if left.shape != right.shape:
        raise ValueError(f"paired kernel inputs must have identical shapes, got {left.shape} and {right.shape}")
    if left.dtype not in (np.dtype(np.float32), np.dtype(np.float64)):
        raise TypeError("x must have dtype float32 or float64")
    if right.dtype not in (np.dtype(np.float32), np.dtype(np.float64)):
        raise TypeError("y must have dtype float32 or float64")
    if isinstance(chunk_size, bool) or int(chunk_size) != chunk_size or int(chunk_size) <= 0:
        raise ValueError("chunk_size must be a positive integer")
    resolved_gamma = 1.0 / max(1, left.shape[1]) if gamma is None else float(gamma)
    if not np.isfinite(resolved_gamma) or resolved_gamma <= 0.0:
        raise ValueError("RBF gamma must be finite and strictly positive")

    result = np.empty(left.shape[0], dtype=np.float64)
    for start in range(0, left.shape[0], int(chunk_size)):
        stop = min(start + int(chunk_size), left.shape[0])
        left_chunk = np.asarray(left[start:stop], dtype=np.float64)
        right_chunk = np.asarray(right[start:stop], dtype=np.float64)
        if not np.all(np.isfinite(left_chunk)) or not np.all(np.isfinite(right_chunk)):
            raise ValueError("paired RBF inputs contain non-finite values")
        squared_distance = np.sum((left_chunk - right_chunk) ** 2, axis=1, dtype=np.float64)
        result[start:stop] = np.exp(-resolved_gamma * np.maximum(squared_distance, 0.0))
    return result


def kernel_matrix(x: np.ndarray, y: np.ndarray, kernel_config: dict | None = None) -> np.ndarray:
    kernel_config = kernel_config or {"name": "polynomial"}
    name = kernel_config.get("name") or kernel_config.get("kernel") or "polynomial"
    normalize = kernel_config.get("normalize")
    if normalize in {True, "l2", "unit", "unit_l2"}:
        x = l2_normalize_rows(x, name="x")
        y = l2_normalize_rows(y, name="y")
    if name in {"linear", "linear_kernel"}:
        return linear_kernel(x, y)
    if name in {"polynomial", "poly", "kid_polynomial"}:
        return polynomial_kernel(
            x,
            y,
            degree=int(kernel_config.get("degree", 3)),
            gamma=kernel_config.get("gamma"),
            coef0=float(kernel_config.get("coef0", 1.0)),
        )
    if name in {"rbf", "mmd_rbf"}:
        gamma = kernel_config.get("gamma")
        if gamma is None and normalize in {True, "l2", "unit", "unit_l2"}:
            # Unit-normalized features have squared distances in [0, 4], so an
            # inverse-feature-dimension default collapses toward a constant
            # kernel for high-dimensional CLIP/Inception features.  This fixed
            # value is data-independent and therefore can be preregistered.
            gamma = 0.5
        return rbf_kernel(x, y, gamma=gamma)
    raise ValueError(f"unsupported kernel: {name}")


def certified_kernel_bounds(kernel_config: dict | None = None) -> dict:
    kernel_config = kernel_config or {"name": "rbf", "normalize": "l2"}
    name = kernel_config.get("name") or kernel_config.get("kernel") or "polynomial"
    if name in {"rbf", "mmd_rbf", "cmmd_clip_mmd"}:
        gamma = kernel_config.get("gamma")
        if gamma is not None and (not np.isfinite(float(gamma)) or float(gamma) <= 0.0):
            return {
                "kernel_name": "rbf",
                "bounded_by_construction": False,
                "reason": "RBF gamma must be finite and strictly positive",
            }
        return {
            "kernel_name": "rbf",
            "feature_normalization": kernel_config.get("normalize") or "l2",
            "gamma": None if gamma is None else float(gamma),
            "bandwidth_protocol": kernel_config.get("bandwidth_protocol", "unspecified"),
            "kernel_lower": 0.0,
            "kernel_upper": 1.0,
            "mmd_contribution_lower": -2.0,
            "mmd_contribution_upper": 2.0,
            # The implementation uses the same reference pair for A and B, so
            # k(R1, R2) cancels exactly.  Three [0,1] terms enter positively and
            # three negatively in each difference contribution.
            "delta_lower": -3.0,
            "delta_upper": 3.0,
            "bounded_by_construction": True,
        }
    return {
        "kernel_name": str(name),
        "bounded_by_construction": False,
        "reason": "kernel does not have a declared finite bound for rigorous clean CS mode",
    }
