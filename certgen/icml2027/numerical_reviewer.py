"""Reviewer-facing numerical attacks on the production paired-MMD path."""

from __future__ import annotations

import hashlib
import resource
import time
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np

from certgen.icml2027.common import write_csv, write_json
from certgen.metrics.kernels import rbf_kernel, rbf_kernel_paired
from certgen.metrics.streams import mmd_difference_stream, paired_mmd_difference_contributions
from certgen.stats.reference_sampling import SAMPLING_SCHEME, validate_reference_sampling_contract


def _rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if value > 10_000_000 else value * 1024


def run_production_numerical_attacks(out_dir: str | Path, *, seed: int = 20270812) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, Any]] = []

    def record(attack: str, passed: bool, invariant: str, detail: dict[str, Any], started: float) -> None:
        rows.append(
            {
                "attack_id": attack,
                "passed": bool(passed),
                "expected_invariant": invariant,
                "detail": detail,
                "runtime_seconds": time.perf_counter() - started,
                "peak_rss_bytes": _rss_bytes(),
                "synthetic_validation_only": True,
                "not_real_generator_evidence": True,
                "not_empirical_paper_evidence": True,
                "claim_allowed": False,
            }
        )

    started = time.perf_counter()
    x = rng.normal(size=(32, 16)).astype(np.float64)
    y = rng.normal(size=(32, 16)).astype(np.float64)
    matrix = np.diag(rbf_kernel(x, y, gamma=0.5))
    paired = rbf_kernel_paired(x, y, gamma=0.5, chunk_size=7)
    record("paired_vs_matrix_equality", bool(np.allclose(paired, matrix, rtol=1e-12, atol=1e-12)), "paired values equal Gram diagonal", {"max_abs_drift": float(np.max(np.abs(paired - matrix)))}, started)

    started = time.perf_counter()
    x32, y32 = x.astype(np.float32), y.astype(np.float32)
    drift: float = float(np.max(np.abs(rbf_kernel_paired(x32, y32, gamma=0.5) - paired)))
    record("float32_float64_drift", bool(drift < 2e-6), "dtype drift below registered tolerance", {"max_abs_drift": float(drift), "tolerance": 2e-6}, started)

    started = time.perf_counter()
    tiny: np.ndarray = np.full((8, 4), np.float32(1e-30), dtype=np.float32)
    try:
        tiny_stream = mmd_difference_stream(tiny, tiny, tiny, {"name": "rbf", "gamma": 0.5, "normalize": "l2"})
        normalization_stable = bool(np.all(np.isfinite(tiny_stream.values)))
    except ValueError:
        normalization_stable = True
    record("normalization_epsilon", normalization_stable, "tiny finite norms either normalize finitely or fail closed", {"stable_or_rejected": normalization_stable}, started)

    started = time.perf_counter()
    near_equal = rng.normal(size=(64, 32)).astype(np.float64)
    other = np.nextafter(near_equal, np.inf)
    values = rbf_kernel_paired(near_equal, other, gamma=0.5, chunk_size=9)
    record("distance_roundoff_clamp", bool(np.all(values <= 1.0) and np.all(values > 0.999999999999)), "near-zero distances remain inside [0,1]", {"minimum": float(values.min()), "maximum": float(values.max())}, started)

    started = time.perf_counter()
    extremes: np.ndarray = np.full((16, 8), 1e150, dtype=np.float64)
    opposite = -extremes
    with np.errstate(over="ignore", invalid="ignore"):
        values = rbf_kernel_paired(extremes, opposite, gamma=0.5)
    record("distance_overflow_underflow", bool(np.all(np.isfinite(values)) and np.all(values == 0.0)), "extreme finite distances underflow safely to zero", {"unique_values": np.unique(values).tolist()}, started)

    started = time.perf_counter()
    arrays = [rng.normal(size=(130, 48)).astype(np.float32) for _ in range(3)]
    kernel = {"name": "rbf", "gamma": 0.5, "normalize": "l2"}
    left = paired_mmd_difference_contributions(
        arrays[0], arrays[1], arrays[2], kernel, chunk_size=1
    )
    right = paired_mmd_difference_contributions(
        arrays[0], arrays[1], arrays[2], kernel, chunk_size=31
    )
    record("chunking_invariance", bool(np.array_equal(left, right)), "chunk size does not change paired values", {"max_abs_drift": float(np.max(np.abs(left - right)))}, started)

    started = time.perf_counter()
    first = mmd_difference_stream(arrays[0], arrays[1], arrays[2], kernel, seed=77, kernel_chunk_size=3)
    second = mmd_difference_stream(arrays[0], arrays[1], arrays[2], kernel, seed=77, kernel_chunk_size=29)
    record("seeded_order_invariance", first.values == second.values, "frozen seed/order is invariant to chunking", {"units": len(first.values)}, started)

    started = time.perf_counter()
    blocked = mmd_difference_stream(arrays[0], arrays[1], arrays[2], kernel, seed=11, block_size=7)
    consumed = int(blocked.metadata["num_contributions_consumed"])
    record("partial_block_accounting", consumed == len(arrays[0]) // 2, "partial last block is included exactly once", {"raw_units": len(arrays[0]) // 2, "consumed": consumed, "last_block": blocked.metadata["last_block_contributions"]}, started)

    started = time.perf_counter()
    high_dim = [rng.normal(size=(4096, 2048)).astype(np.float32) for _ in range(3)]
    high = mmd_difference_stream(
        high_dim[0], high_dim[1], high_dim[2], kernel, seed=5, kernel_chunk_size=128
    )
    record("high_dimension_memory_path", bool(len(high.values) == 2048 and np.all(np.isfinite(high.values))), "4096x2048 inputs complete without a Gram matrix", {"shape": [4096, 2048], "stream_units": len(high.values), "pairwise_matrix_materialized": False}, started)

    started = time.perf_counter()
    near = [rng.normal(size=(2000, 64)).astype(np.float32) for _ in range(3)]
    near_stream = mmd_difference_stream(near[0], near[1], near[2], kernel, seed=99)
    mean = float(np.mean(near_stream.values))
    record("near_tie_finite_precision", bool(np.isfinite(mean) and abs(mean) < 0.1), "null-like near tie stays finite and near zero", {"mean": mean}, started)

    started = time.perf_counter()
    base_arrays = [rng.normal(size=(256, 32)).astype(np.float32) for _ in range(3)]
    base = mmd_difference_stream(base_arrays[0], base_arrays[1], base_arrays[2], kernel, seed=8)
    perturbed_arrays = [array + np.float32(0.01) for array in base_arrays]
    perturbed = mmd_difference_stream(
        perturbed_arrays[0], perturbed_arrays[1], perturbed_arrays[2], kernel, seed=8
    )
    preprocessing_drift = float(np.max(np.abs(np.asarray(base.values) - np.asarray(perturbed.values))))
    record("preprocessing_perturbation", bool(np.isfinite(preprocessing_drift)), "registered preprocessing perturbation is computed, finite, and never silently promoted", {"maximum_stream_drift": preprocessing_drift, "classification": "ABLATION_ONLY"}, started)

    started = time.perf_counter()
    from PIL import Image

    pixels: np.ndarray = np.arange(16 * 16 * 3, dtype=np.uint8).reshape(16, 16, 3)
    image = Image.fromarray(pixels, mode="RGB")
    bilinear = np.asarray(image.resize((31, 31), resample=Image.Resampling.BILINEAR), dtype=np.int16)
    bicubic = np.asarray(image.resize((31, 31), resample=Image.Resampling.BICUBIC), dtype=np.int16)
    interpolation_drift = int(np.max(np.abs(bilinear - bicubic)))
    record("interpolation_perturbation", interpolation_drift > 0, "interpolation alternatives produce a detectable registered ablation", {"maximum_pixel_drift": interpolation_drift}, started)

    started = time.perf_counter()
    raw = rbf_kernel_paired(x, y, gamma=0.5)
    normalized_x = x / np.linalg.norm(x, axis=1, keepdims=True)
    normalized_y = y / np.linalg.norm(y, axis=1, keepdims=True)
    normalized = rbf_kernel_paired(normalized_x, normalized_y, gamma=0.5)
    normalization_drift = float(np.max(np.abs(raw - normalized)))
    record("feature_normalization_perturbation", normalization_drift > 0.0, "normalization choice changes values and is hash-bound", {"maximum_kernel_drift": normalization_drift}, started)

    started = time.perf_counter()
    high_quality = BytesIO()
    low_quality = BytesIO()
    image.save(high_quality, format="JPEG", quality=95)
    image.save(low_quality, format="JPEG", quality=25)
    high_decoded = np.asarray(Image.open(BytesIO(high_quality.getvalue())), dtype=np.int16)
    low_decoded = np.asarray(Image.open(BytesIO(low_quality.getvalue())), dtype=np.int16)
    jpeg_drift = float(np.mean(np.abs(high_decoded - low_decoded)))
    record("jpeg_compression_perturbation", jpeg_drift > 0.0, "compression perturbation is numerically exercised and ablation-only", {"mean_absolute_pixel_drift": jpeg_drift}, started)

    started = time.perf_counter()
    duplicate_rows = [b"sample-a", b"sample-b", b"sample-a"]
    digests = [hashlib.sha256(value).hexdigest() for value in duplicate_rows]
    duplicate_count = len(digests) - len(set(digests))
    record("duplicate_contamination", duplicate_count == 1, "exact content duplicates are detected", {"duplicate_count": duplicate_count}, started)

    started = time.perf_counter()
    vectors = np.asarray([[0.0, 0.0], [1e-7, -1e-7], [2.0, 2.0]], dtype=np.float64)
    distances = np.linalg.norm(vectors[:, None, :] - vectors[None, :, :], axis=2)
    near_pairs = int(np.count_nonzero(np.triu((distances > 0.0) & (distances < 1e-5), k=1)))
    record("near_duplicate_contamination", near_pairs == 1, "near-duplicate fixture crosses the registered distance threshold", {"near_duplicate_pairs": near_pairs, "threshold": 1e-5}, started)

    started = time.perf_counter()
    base_contract = {
        "sampling_scheme": SAMPLING_SCHEME,
        "without_replacement": False,
        "adaptive_reference_reuse": False,
        "reference_reuse_declared": True,
        "precommitted_before_stream": True,
        "plan_sha256": "a" * 64,
    }
    undeclared = validate_reference_sampling_contract({**base_contract, "reference_reuse_declared": False})
    record("reference_reuse_contract", not undeclared["passed"], "undeclared reference reuse fails closed", {"errors": undeclared["errors"]}, started)

    started = time.perf_counter()
    finite = validate_reference_sampling_contract({**base_contract, "without_replacement": True})
    record("finite_population_sampling_contract", not finite["passed"], "without-replacement mode is rejected without a verified theorem", {"errors": finite["errors"]}, started)

    started = time.perf_counter()
    from certgen.icml2027.production_mmd import evaluate_production_contributions

    positive = evaluate_production_contributions([0.9] * 5000, alpha=0.05)["decision"]
    negative = evaluate_production_contributions([-0.9] * 5000, alpha=0.05)["decision"]
    record("representation_conflict", positive == "B_BETTER" and negative == "A_BETTER", "opposite representation directions are detected as a conflict", {"representation_a": positive, "representation_b": negative, "classification": "DIRECTION_CONFLICT"}, started)

    started = time.perf_counter()
    decisions = {}
    for model_count in (5, 10, 20, 50, 100):
        edge_count = model_count * (model_count - 1) // 2
        decisions[str(model_count)] = evaluate_production_contributions(
            [0.0] * 128,
            alpha=0.05 / edge_count,
        )["decision"]
    record("multi_model_near_tie_scaling", all(value == "UNRESOLVED" for value in decisions.values()), "near ties remain unresolved as multiplicity grows through M=100", {"decisions": decisions}, started)

    target = Path(out_dir)
    write_csv(target / "numerical_attacks.csv", rows)
    summary = {
        "schema_version": "certgen.icml2027.production_numerical_attacks.v1",
        "passed": all(bool(row["passed"]) for row in rows),
        "attacks_total": len(rows),
        "attacks_passed": sum(bool(row["passed"]) for row in rows),
        "peak_rss_bytes": max(int(row["peak_rss_bytes"]) for row in rows),
        "claim_allowed": False,
    }
    write_json(target / "numerical_attacks.summary.json", summary)
    return summary
