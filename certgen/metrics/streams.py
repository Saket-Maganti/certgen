"""Linear-time MMD/KID/CMMD contribution streams."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from certgen.metrics.kernels import certified_kernel_bounds, kernel_matrix, rbf_kernel_paired
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


def _validate_feature_arrays(
    a: np.ndarray, b: np.ndarray, r: np.ndarray, *, chunk_size: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    arrays = tuple(np.asanyarray(value) for value in (a, b, r))
    for name, value in zip(("features_a", "features_b", "features_r"), arrays):
        if value.ndim != 2:
            raise ValueError(f"{name} must be a 2D array, got shape {value.shape}")
        if value.dtype not in (np.dtype(np.float32), np.dtype(np.float64)):
            raise TypeError(f"{name} must have dtype float32 or float64")
        for start in range(0, len(value), chunk_size):
            if not np.all(np.isfinite(value[start : start + chunk_size])):
                raise ValueError(f"{name} contains non-finite values")
    if not (arrays[0].shape[1] == arrays[1].shape[1] == arrays[2].shape[1]):
        raise ValueError("feature dimensions for A, B, and R must match")
    return arrays  # type: ignore[return-value]


def _paired_rows(
    array: np.ndarray,
    first_indices: np.ndarray,
    second_indices: np.ndarray,
    *,
    normalize: bool,
) -> tuple[np.ndarray, np.ndarray]:
    first = np.asarray(array[first_indices], dtype=np.float64)
    second = np.asarray(array[second_indices], dtype=np.float64)
    if normalize:
        first_norms = np.linalg.norm(first, axis=1)
        second_norms = np.linalg.norm(second, axis=1)
        if np.any(first_norms <= 0.0) or np.any(second_norms <= 0.0):
            raise ValueError("features contain zero-norm rows; cannot certify normalized bounded kernel stream")
        first = first / first_norms[:, None]
        second = second / second_norms[:, None]
    return first, second


def paired_mmd_difference_contributions(
    a: np.ndarray,
    b: np.ndarray,
    r: np.ndarray,
    kernel_config: dict,
    *,
    indices: np.ndarray | None = None,
    chunk_size: int = 1024,
) -> np.ndarray:
    """Disjoint-pair unbiased contributions for MMD^2(A,R)-MMD^2(B,R).

    The same reference pair is used within a stream unit, so the two
    ``k(R1, R2)`` terms cancel algebraically.  Different units use disjoint
    A/B/R rows; independence still requires the input rows to be mutually
    independent IID draws and all preprocessing/kernel choices to be fixed
    before this stream is inspected.
    """

    if isinstance(chunk_size, bool) or int(chunk_size) != chunk_size or int(chunk_size) <= 0:
        raise ValueError("chunk_size must be a positive integer")
    a, b, r = _validate_feature_arrays(a, b, r, chunk_size=int(chunk_size))
    kernel_name = kernel_config.get("name") or kernel_config.get("kernel") or "rbf"
    if kernel_name not in {"rbf", "mmd_rbf", "cmmd_clip_mmd"}:
        raise ValueError("production paired MMD contributions currently require an RBF kernel")
    gamma_value = kernel_config.get("gamma")
    gamma = 0.5 if gamma_value is None else float(gamma_value)
    normalize = kernel_config.get("normalize") in {True, "l2", "unit", "unit_l2"}
    count = min(len(a), len(b), len(r))
    if count < 4:
        raise ValueError("linear-time MMD difference stream requires at least four samples per array")
    if count % 2:
        count -= 1
    order = np.arange(count, dtype=np.int64) if indices is None else np.asarray(indices, dtype=np.int64)
    if order.ndim != 1 or len(order) < count:
        raise ValueError("indices must be a one-dimensional permutation covering the aligned rows")
    order = order[:count]
    if np.any(order < 0) or np.any(order >= min(len(a), len(b), len(r))) or len(np.unique(order)) != count:
        raise ValueError("indices must be unique and inside the aligned feature range")

    contributions: np.ndarray = np.empty(count // 2, dtype=np.float64)
    for start in range(0, count // 2, int(chunk_size)):
        stop = min(start + int(chunk_size), count // 2)
        first_indices = order[2 * start : 2 * stop : 2]
        second_indices = order[2 * start + 1 : 2 * stop : 2]
        a1, a2 = _paired_rows(a, first_indices, second_indices, normalize=normalize)
        b1, b2 = _paired_rows(b, first_indices, second_indices, normalize=normalize)
        r1, r2 = _paired_rows(r, first_indices, second_indices, normalize=normalize)
        contributions[start:stop] = (
            rbf_kernel_paired(a1, a2, gamma=gamma, chunk_size=int(chunk_size))
            - rbf_kernel_paired(b1, b2, gamma=gamma, chunk_size=int(chunk_size))
            - rbf_kernel_paired(a1, r2, gamma=gamma, chunk_size=int(chunk_size))
            - rbf_kernel_paired(a2, r1, gamma=gamma, chunk_size=int(chunk_size))
            + rbf_kernel_paired(b1, r2, gamma=gamma, chunk_size=int(chunk_size))
            + rbf_kernel_paired(b2, r1, gamma=gamma, chunk_size=int(chunk_size))
        )
    return contributions


def _block_average(values: np.ndarray, block_size: int | None) -> tuple[list[float], list[int]]:
    if block_size is None:
        return values.astype(float).tolist(), [1] * len(values)
    block_size = int(block_size)
    if block_size <= 0:
        raise ValueError("block_size must be positive")
    averaged: list[float] = []
    block_lengths: list[int] = []
    for start in range(0, len(values), block_size):
        block = values[start : start + block_size]
        if len(block):
            averaged.append(float(np.mean(block)))
            block_lengths.append(int(len(block)))
    return averaged, block_lengths


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
    reference_sampling_metadata: dict[str, Any] | None = None,
    kernel_chunk_size: int = 1024,
) -> ComparisonStream:
    if isinstance(kernel_chunk_size, bool) or int(kernel_chunk_size) != kernel_chunk_size or int(kernel_chunk_size) <= 0:
        raise ValueError("kernel_chunk_size must be a positive integer")
    a, b, r = _validate_feature_arrays(features_a, features_b, features_r, chunk_size=int(kernel_chunk_size))
    count = min(len(a), len(b), len(r))
    if count < 4:
        raise ValueError("at least four aligned samples are required")
    rng = np.random.default_rng(seed)
    indices = np.arange(count)
    rng.shuffle(indices)
    kernel = dict(kernel_config or {"name": "rbf", "normalize": "l2"})
    kernel_name = kernel.get("name") or kernel.get("kernel") or "rbf"
    if kernel_name in {"rbf", "mmd_rbf", "cmmd_clip_mmd"} and kernel.get("gamma") is None:
        kernel["gamma"] = 0.5
        kernel.setdefault("bandwidth_protocol", "fixed_unit_sphere_gamma_0.5_v1")
    elif kernel_name in {"rbf", "mmd_rbf", "cmmd_clip_mmd"}:
        kernel.setdefault("bandwidth_protocol", "explicit_gamma_preregistration_not_verified")
    bounds = certified_kernel_bounds(kernel)
    if require_bounded_kernel and not bounds.get("bounded_by_construction"):
        raise ValueError(f"kernel is not certified-bounded for rigorous clean CS mode: {bounds.get('reason')}")
    if bounds.get("bounded_by_construction"):
        kernel = {**kernel, "normalize": kernel.get("normalize") or "l2"}
    raw_values: np.ndarray = paired_mmd_difference_contributions(
        a, b, r, kernel, indices=indices, chunk_size=int(kernel_chunk_size)
    ).astype(float)
    values, block_lengths = _block_average(raw_values, block_size)
    if max_units is not None:
        values = values[: int(max_units)]
        block_lengths = block_lengths[: int(max_units)]
    lower_bound = float(bounds.get("delta_lower", np.nan)) if bounds.get("bounded_by_construction") else None
    upper_bound = float(bounds.get("delta_upper", np.nan)) if bounds.get("bounded_by_construction") else None
    reference_sampling_metadata = reference_sampling_metadata or {
        "sampling_scheme": "iid_rows_precommitted_assumption_unverified",
        "plan_sha256": None,
        "claim_allowed": False,
    }
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
            "num_samples_per_distribution_available_for_pairing": int(count - (count % 2)),
            "pairing_scheme": "seeded_permutation_then_disjoint_pairs",
            "reference_reuse": "same_reference_pair_within_A_vs_B_unit; source rows may repeat only under a validated with-replacement draw plan",
            "reference_sampling": reference_sampling_metadata,
            "stream_unit": "one disjoint A-pair, B-pair, and R-pair; optionally averaged over nonoverlapping contribution blocks",
            "estimand": "MMD_squared(A,R)-MMD_squared(B,R) for the fixed extractor, preprocessing, RBF gamma, and populations",
            "filtration": "sigma field generated by preceding disjoint stream units in the seeded order",
            "independence_requirement": "mutually independent IID A/B/R rows; no duplicates or adaptive cache/kernel selection",
            "adaptive_choices_allowed": "stopping based on the valid confidence sequence only",
            "block_size": 1 if block_size is None else int(block_size),
            "last_block_contributions": int(block_lengths[-1]) if block_lengths else 0,
            "num_unblocked_contributions": int(len(raw_values)),
            "num_contributions_consumed": int(sum(block_lengths)),
            "samples_per_distribution_consumed": int(2 * sum(block_lengths)),
            "total_feature_rows_consumed": int(6 * sum(block_lengths)),
            "bandwidth_protocol": kernel.get("bandwidth_protocol"),
            "kernel_computation": "paired_rbf_o_nd_no_gram_matrix",
            "kernel_chunk_size": int(kernel_chunk_size),
            "input_memory_mapping_preserved": any(isinstance(value, np.memmap) for value in (a, b, r)),
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
