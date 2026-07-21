"""Measured feature-extraction invariance checks used by real sanity gates."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np

from certgen.metrics.mmd import unbiased_mmd2


def _matrix_hash(matrix: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(matrix)
    digest = hashlib.sha256()
    digest.update(str(contiguous.dtype).encode("utf-8"))
    digest.update(np.asarray(contiguous.shape, dtype=np.int64).tobytes())
    digest.update(contiguous.tobytes())
    return digest.hexdigest()


def _ordered_half_metric(matrix: np.ndarray, gamma: float) -> float:
    half = len(matrix) // 2
    if half < 2:
        raise ValueError("protocol metric requires at least four ordered rows")
    return float(
        unbiased_mmd2(
            matrix[:half],
            matrix[half : 2 * half],
            kernel="rbf",
            normalize="l2",
            gamma=gamma,
        )
    )


def compare_feature_runs(
    sample_ids_a: Sequence[str],
    features_a: np.ndarray,
    sample_ids_b: Sequence[str],
    features_b: np.ndarray,
    *,
    gamma: float = 0.5,
    maximum_feature_difference: float = 1e-5,
    maximum_metric_difference: float = 1e-7,
) -> dict[str, Any]:
    """Compare two real executions over the same prospectively ordered inputs."""

    left = np.asarray(features_a)
    right = np.asarray(features_b)
    same_ids = list(map(str, sample_ids_a)) == list(map(str, sample_ids_b))
    same_shape = left.shape == right.shape and left.ndim == 2
    same_dtype = left.dtype == right.dtype
    finite = bool(np.isfinite(left).all() and np.isfinite(right).all())
    max_difference = (
        float(np.max(np.abs(left.astype(np.float64) - right.astype(np.float64))))
        if same_shape and left.size
        else float("inf")
    )
    try:
        left_metric = _ordered_half_metric(left, gamma)
        right_metric = _ordered_half_metric(right, gamma)
        metric_difference = abs(left_metric - right_metric)
    except (TypeError, ValueError, FloatingPointError):
        left_metric = right_metric = metric_difference = float("inf")
    passed = bool(
        same_ids
        and same_shape
        and same_dtype
        and finite
        and max_difference <= maximum_feature_difference
        and metric_difference <= maximum_metric_difference
    )
    return {
        "passed": passed,
        "same_ordered_sample_ids": same_ids,
        "same_shape": same_shape,
        "same_dtype": same_dtype,
        "finite": finite,
        "shape_a": list(left.shape),
        "shape_b": list(right.shape),
        "dtype_a": str(left.dtype),
        "dtype_b": str(right.dtype),
        "features_hash_a": _matrix_hash(left),
        "features_hash_b": _matrix_hash(right),
        "maximum_feature_difference": max_difference,
        "metric_a": left_metric,
        "metric_b": right_metric,
        "metric_difference": metric_difference,
        "tolerances": {
            "maximum_feature_difference": maximum_feature_difference,
            "maximum_metric_difference": maximum_metric_difference,
        },
        "claim_allowed": False,
    }


def repeated_batching_check(
    *,
    extract_batch: Callable[[list[Any]], Any],
    images: Sequence[Any],
    sample_ids: Sequence[str],
    batch_sizes: Sequence[int],
    expected_dimension: int,
    gamma: float = 0.5,
) -> dict[str, Any]:
    """Run identical ordered images through two actual extractor batch sizes."""

    sizes = sorted({int(value) for value in batch_sizes if int(value) > 0})
    if len(sizes) < 2:
        raise ValueError("repeated batching requires two distinct positive batch sizes")
    if len(images) != len(sample_ids) or len(images) < 4:
        raise ValueError("repeated batching requires at least four aligned inputs")
    outputs: list[np.ndarray] = []
    for size in sizes[:2]:
        chunks: list[np.ndarray] = []
        for start in range(0, len(images), size):
            raw = extract_batch(list(images[start : start + size]))
            matrix = raw.float().cpu().numpy()
            if matrix.shape != (len(images[start : start + size]), expected_dimension):
                raise ValueError("repeated-batching extractor output shape mismatch")
            chunks.append(matrix)
        outputs.append(np.concatenate(chunks, axis=0))
    comparison = compare_feature_runs(
        sample_ids,
        outputs[0],
        sample_ids,
        outputs[1],
        gamma=gamma,
    )
    return {
        "schema_version": "certgen.feature_repeated_batching.v1",
        "batch_sizes": sizes[:2],
        "ordered_sample_ids": list(map(str, sample_ids)),
        **comparison,
    }


def independent_shard_merge_check(
    sample_ids: Sequence[str],
    features: np.ndarray,
    *,
    gamma: float = 0.5,
) -> dict[str, Any]:
    """Build equivalent canonical arrays through independent one/two-shard paths."""

    matrix = np.asarray(features)
    ids = list(map(str, sample_ids))
    if matrix.ndim != 2 or len(ids) != len(matrix) or len(ids) < 4:
        raise ValueError("shard-merge validation requires at least four aligned rows")
    if len(ids) != len(set(ids)):
        raise ValueError("shard-merge validation refuses duplicate sample IDs")

    one_shard = sorted(zip(ids, matrix, strict=True), key=lambda row: row[0])
    partitions = [
        sorted(one_shard[index::2], key=lambda row: row[0])
        for index in range(2)
    ]
    cursors = [0, 0]
    two_shard: list[tuple[str, np.ndarray]] = []
    while cursors[0] < len(partitions[0]) or cursors[1] < len(partitions[1]):
        available = [
            index
            for index in range(2)
            if cursors[index] < len(partitions[index])
        ]
        chosen = min(
            available,
            key=lambda index: partitions[index][cursors[index]][0],
        )
        two_shard.append(partitions[chosen][cursors[chosen]])
        cursors[chosen] += 1

    one_ids = [row[0] for row in one_shard]
    two_ids = [row[0] for row in two_shard]
    one_matrix = np.stack([row[1] for row in one_shard])
    two_matrix = np.stack([row[1] for row in two_shard])
    comparison = compare_feature_runs(
        one_ids,
        one_matrix,
        two_ids,
        two_matrix,
        gamma=gamma,
        maximum_feature_difference=0.0,
        maximum_metric_difference=0.0,
    )
    return {
        "schema_version": "certgen.feature_independent_shard_merge.v1",
        "one_shard_rows": len(one_ids),
        "two_shard_rows": len(two_ids),
        "row_coverage_equal": set(one_ids) == set(two_ids),
        "one_shard_order_hash": hashlib.sha256("\n".join(one_ids).encode()).hexdigest(),
        "two_shard_order_hash": hashlib.sha256("\n".join(two_ids).encode()).hexdigest(),
        **comparison,
    }
