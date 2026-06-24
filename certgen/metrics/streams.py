"""Linear-time MMD/KID/CMMD contribution streams."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from certgen.metrics.kernels import as_2d_float64, certified_kernel_bounds, kernel_matrix, l2_normalize_rows
from certgen.stats.design_contracts import ComparisonStream


@dataclass
class ClippedStream:
    values: list[float]
    metadata: dict[str, Any]


def _paired_mmd_contributions(x: np.ndarray, y: np.ndarray, kernel_config: dict) -> np.ndarray:
    count = min(len(x), len(y))
    if count < 4:
        raise ValueError("linear-time MMD stream requires at least four samples per array")
    if count % 2:
        count -= 1
    x = x[:count]
    y = y[:count]
    x1 = x[0::2]
    x2 = x[1::2]
    y1 = y[0::2]
    y2 = y[1::2]
    k_xx = np.diag(kernel_matrix(x1, x2, kernel_config))
    k_yy = np.diag(kernel_matrix(y1, y2, kernel_config))
    k_xy_1 = np.diag(kernel_matrix(x1, y2, kernel_config))
    k_xy_2 = np.diag(kernel_matrix(x2, y1, kernel_config))
    return k_xx + k_yy - k_xy_1 - k_xy_2


def _normalise_certified_features(array: np.ndarray, kernel_config: dict, *, name: str) -> np.ndarray:
    if kernel_config.get("normalize") in {True, "l2", "unit", "unit_l2"}:
        return l2_normalize_rows(array, name=name)
    return array


def _block_average(values: np.ndarray, block_size: int | None) -> list[float]:
    if block_size is None:
        return values.astype(float).tolist()
    block_size = int(block_size)
    if block_size <= 0:
        raise ValueError("block_size must be positive")
    averaged: list[float] = []
    for start in range(0, len(values), block_size):
        block = values[start : start + block_size]
        if len(block):
            averaged.append(float(np.mean(block)))
    return averaged


def mmd_difference_stream(
    features_a: np.ndarray,
    features_b: np.ndarray,
    features_r: np.ndarray,
    kernel_config: dict | None,
    seed: int = 0,
    max_units: int | None = None,
    metric_label: str = "mmd_rbf",
    comparison_id: str = "comparison",
    evidence_status: str = "smoke_only",
    block_size: int | None = None,
    require_bounded_kernel: bool = True,
) -> ComparisonStream:
    a = as_2d_float64(features_a, name="features_a")
    b = as_2d_float64(features_b, name="features_b")
    r = as_2d_float64(features_r, name="features_r")
    if not (a.shape[1] == b.shape[1] == r.shape[1]):
        raise ValueError("feature dimensions for A, B, and R must match")
    count = min(len(a), len(b), len(r))
    if count < 4:
        raise ValueError("at least four aligned samples are required")
    rng = np.random.default_rng(seed)
    indices = np.arange(count)
    rng.shuffle(indices)
    a = a[indices]
    b = b[indices]
    r = r[indices]
    kernel = kernel_config or {"name": "rbf", "normalize": "l2"}
    bounds = certified_kernel_bounds(kernel)
    if require_bounded_kernel and not bounds.get("bounded_by_construction"):
        raise ValueError(f"kernel is not certified-bounded for rigorous clean CS mode: {bounds.get('reason')}")
    if bounds.get("bounded_by_construction"):
        kernel = {**kernel, "normalize": kernel.get("normalize") or "l2"}
        a = _normalise_certified_features(a, kernel, name="features_a")
        b = _normalise_certified_features(b, kernel, name="features_b")
        r = _normalise_certified_features(r, kernel, name="features_r")
        kernel_for_matrix = {**kernel, "normalize": None}
    else:
        kernel_for_matrix = kernel
    a_minus_r = _paired_mmd_contributions(a, r, kernel_for_matrix)
    b_minus_r = _paired_mmd_contributions(b, r, kernel_for_matrix)
    raw_values = (a_minus_r - b_minus_r).astype(float)
    values = _block_average(raw_values, block_size)
    if max_units is not None:
        values = values[: int(max_units)]
    lower_bound = float(bounds.get("delta_lower", np.nan)) if bounds.get("bounded_by_construction") else None
    upper_bound = float(bounds.get("delta_upper", np.nan)) if bounds.get("bounded_by_construction") else None
    return ComparisonStream(
        comparison_id=comparison_id,
        metric_label=metric_label,
        values=values,
        evidence_status=evidence_status,
        bounded=bool(bounds.get("bounded_by_construction")),
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        metadata={
            "seed": seed,
            "kernel_config": kernel,
            "direction": "negative stream mean means A closer to R; positive means B closer",
            "num_raw_samples_aligned": int(count),
            "block_size": block_size,
            "num_unblocked_contributions": int(len(raw_values)),
            "boundedness_metadata": bounds,
        },
    )


def clip_stream_values(values: list[float] | np.ndarray, lower: float, upper: float) -> ClippedStream:
    if lower >= upper:
        raise ValueError("clip lower must be smaller than clip upper")
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1:
        raise ValueError("stream values must be one-dimensional")
    if not np.all(np.isfinite(arr)):
        raise ValueError("stream values must be finite")
    clipped = np.clip(arr, lower, upper)
    low = int(np.sum(arr < lower))
    high = int(np.sum(arr > upper))
    total = int(arr.size)
    metadata = {
        "lower_bound": float(lower),
        "upper_bound": float(upper),
        "num_clipped_low": low,
        "num_clipped_high": high,
        "fraction_clipped": float((low + high) / total) if total else 0.0,
    }
    return ClippedStream(values=clipped.astype(float).tolist(), metadata=metadata)
