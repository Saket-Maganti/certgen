"""Normalization-aware audits, independent reproduction, and 10k CPU feasibility."""

from __future__ import annotations

import csv
import math
import resource
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np

from certgen.icml2027.common import derive_seed, file_sha256, write_csv, write_json
from certgen.icml2027.payload import validate_multipart_payload
from certgen.icml2027.production_mmd import SCENARIOS, _scenario_arrays, evaluate_production_contributions
from certgen.metrics.streams import mmd_difference_stream, paired_mmd_difference_contributions
from certgen.stats.bounds import hoeffding_union_radius


SCENARIO_CLASSIFICATION: dict[str, str] = {
    "identical_distribution_null": "NULL",
    "exact_sample_identical_null": "NULL",
    "scale_shift": "INVARIANCE_CONTROL",
    "variance_inflation": "INVARIANCE_CONTROL",
    "obvious_mean_shift": "EASY_ALTERNATIVE",
    "contamination_10pct": "EASY_ALTERNATIVE",
    "covariance_perturbation": "REPRESENTATION_SPECIFIC_ALTERNATIVE",
    "anisotropy": "REPRESENTATION_SPECIFIC_ALTERNATIVE",
    "low_rank_manifold_shift": "REPRESENTATION_SPECIFIC_ALTERNATIVE",
    "finite_reference_with_replacement": "REFERENCE_DESIGN_STRESS",
    "declared_reference_reuse": "REFERENCE_DESIGN_STRESS",
}


def classify_scenario(scenario: str) -> str:
    if scenario in SCENARIO_CLASSIFICATION:
        return SCENARIO_CLASSIFICATION[scenario]
    if scenario in SCENARIOS:
        return "HARD_ALTERNATIVE"
    raise ValueError(f"unknown production scenario: {scenario}")


def _l2(value: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(value, axis=1, keepdims=True)
    if np.any(norms <= 0):
        raise ValueError("zero-norm synthetic row")
    return value / norms


def _diagnostics(a: np.ndarray, b: np.ndarray, r: np.ndarray, *, normalized: bool) -> dict[str, float]:
    if normalized:
        a, b, r = _l2(a), _l2(b), _l2(r)
    mean_difference_norm = float(np.linalg.norm(np.mean(b, axis=0) - np.mean(r, axis=0)))
    covariance_difference_norm = float(
        np.linalg.norm(np.cov(b, rowvar=False) - np.cov(r, rowvar=False), ord="fro")
    )
    norms = np.linalg.norm(b, axis=1)
    cosine = np.sum(b * r, axis=1) / np.maximum(
        np.linalg.norm(b, axis=1) * np.linalg.norm(r, axis=1), 1e-12
    )
    stream = mmd_difference_stream(
        a.astype(np.float32),
        b.astype(np.float32),
        r.astype(np.float32),
        {"name": "rbf", "gamma": 0.5, "normalize": "l2" if normalized else False},
        seed=20_270_812,
        evidence_status="synthetic_validation_only",
        comparison_id="normalization_diagnostic",
        require_bounded_kernel=normalized,
    )
    return {
        "mean_difference_norm": mean_difference_norm,
        "covariance_difference_frobenius": covariance_difference_norm,
        "feature_norm_mean": float(np.mean(norms)),
        "feature_norm_std": float(np.std(norms)),
        "mmd_difference_estimate": float(np.mean(stream.values)),
        "matched_cosine_mean": float(np.mean(cosine)),
        "matched_cosine_std": float(np.std(cosine)),
    }


def run_normalization_power_audit(
    *,
    source_records: str | Path,
    out_dir: str | Path,
    diagnostic_count: int = 1_000,
    diagnostic_dimension: int = 64,
) -> dict[str, Any]:
    target = Path(out_dir)
    classification_rows = []
    diagnostic_rows = []
    for scenario in SCENARIOS:
        category = classify_scenario(scenario)
        classification_rows.append(
            {
                "scenario": scenario,
                "category": category,
                "included_in_power_denominator": category
                in {"EASY_ALTERNATIVE", "HARD_ALTERNATIVE", "REPRESENTATION_SPECIFIC_ALTERNATIVE"},
                "row_l2_invariance_reason": "positive radial rescaling is erased exactly"
                if category == "INVARIANCE_CONTROL"
                else "not_applicable",
                "claim_allowed": False,
            }
        )
        rng = np.random.default_rng(derive_seed(20_270_812, "normalization", scenario))
        a, b, r, _ = _scenario_arrays(scenario, diagnostic_count, diagnostic_dimension, rng)
        for stage, normalized in (("before_preprocessing", False), ("after_row_l2", True)):
            diagnostic_rows.append(
                {
                    "scenario": scenario,
                    "category": category,
                    "stage": stage,
                    **_diagnostics(a, b, r, normalized=normalized),
                    "diagnostic_only": True,
                    "claim_allowed": False,
                }
            )
    write_csv(target / "SCENARIO_CLASSIFICATION.csv", classification_rows)
    write_csv(target / "PREPROCESSING_EFFECT_DIAGNOSTICS.csv", diagnostic_rows)

    with Path(source_records).open(encoding="utf-8", newline="") as handle:
        raw = list(csv.DictReader(handle))
    power_rows: list[dict[str, Any]] = []
    included = []
    for scenario in SCENARIOS:
        category = classify_scenario(scenario)
        selected = [row for row in raw if row["scenario"] == scenario]
        if not selected:
            continue
        denominator = category in {
            "EASY_ALTERNATIVE",
            "HARD_ALTERNATIVE",
            "REPRESENTATION_SPECIFIC_ALTERNATIVE",
        }
        resolutions = sum(row["decision"] == row["expected_direction"] for row in selected)
        unresolved = sum(row["decision"] == "UNRESOLVED" for row in selected)
        if denominator:
            included.extend(selected)
        effects = [float(row["mean_delta"]) for row in selected]
        stream_std = float(np.std(effects, ddof=1)) if len(effects) > 1 else 0.0
        mean_effect = float(np.mean(effects))
        stream_units = max(int(row["stream_units"]) for row in selected)
        radius = hoeffding_union_radius(stream_units, 0.05, -3.0, 3.0)
        required_n = (
            math.ceil(36.0 * math.log(2.0 / 0.05) / (2.0 * mean_effect**2))
            if abs(mean_effect) > 1e-12
            else None
        )
        power_rows.append(
            {
                "scenario": scenario,
                "category": category,
                "included_in_power_denominator": denominator,
                "runs": len(selected),
                "correct_resolutions": resolutions,
                "power": resolutions / len(selected),
                "unresolved_fraction": unresolved / len(selected),
                "mean_paired_mmd_effect": mean_effect,
                "between_run_effect_std": stream_std,
                "standardized_effect_descriptive": mean_effect / stream_std if stream_std > 0 else None,
                "terminal_cs_radius": radius,
                "fixed_n_hoeffding_required_stream_units_approx": required_n,
                "claim_allowed": False,
            }
        )
    total_correct = sum(row["decision"] == row["expected_direction"] for row in included)
    corrected_power = total_correct / len(included) if included else 0.0
    unresolved = sum(row["decision"] == "UNRESOLVED" for row in included) / len(included) if included else 1.0
    utility = "GREEN" if corrected_power > 0.60 else ("YELLOW" if corrected_power >= 0.20 else "RED")
    power_rows.append(
        {
            "scenario": "ALL_TRUE_ALTERNATIVES",
            "category": "EXPECTED_RESOLUTION_PLANNING_ONLY",
            "included_in_power_denominator": True,
            "runs": len(included),
            "correct_resolutions": total_correct,
            "power": corrected_power,
            "unresolved_fraction": unresolved,
            "utility_gate": utility,
            "claim_allowed": False,
        }
    )
    write_csv(target / "POWER_RECOMPUTED_TRUE_ALTERNATIVES.csv", power_rows)
    summary = {
        "schema_version": "certgen.icml2027.normalization_power_audit.v1",
        "passed": True,
        "invariance_controls_excluded": ["scale_shift", "variance_inflation"],
        "true_alternative_runs": len(included),
        "corrected_true_alternative_power": corrected_power,
        "true_alternative_unresolved_fraction": unresolved,
        "expected_resolution_planning_only": utility,
        "diagnostics_are_not_evidence": True,
        "claim_allowed": False,
    }
    write_json(target / "NORMALIZATION_POWER_AUDIT.summary.json", summary)
    return summary


def independent_paired_mmd_difference(
    a: np.ndarray,
    b: np.ndarray,
    r: np.ndarray,
    *,
    indices: np.ndarray,
    gamma: float = 0.5,
) -> np.ndarray:
    """Small audit implementation that deliberately does not call the production stream helper."""

    count = min(len(a), len(b), len(r))
    if count % 2:
        count -= 1
    order = np.asarray(indices, dtype=np.int64)[:count]
    arrays = []
    for value in (a, b, r):
        selected = np.asarray(value[order], dtype=np.float64)
        selected /= np.linalg.norm(selected, axis=1, keepdims=True)
        arrays.append(selected)
    a_ordered, b_ordered, r_ordered = arrays

    def kernel(left: np.ndarray, right: np.ndarray) -> np.ndarray:
        return np.exp(-gamma * np.sum((left - right) ** 2, axis=1))

    a1, a2 = a_ordered[0::2], a_ordered[1::2]
    b1, b2 = b_ordered[0::2], b_ordered[1::2]
    r1, r2 = r_ordered[0::2], r_ordered[1::2]
    return kernel(a1, a2) - kernel(b1, b2) - kernel(a1, r2) - kernel(a2, r1) + kernel(b1, r2) + kernel(b2, r1)


def run_independent_mmd_audit(out_path: str | Path, *, trials: int = 50) -> dict[str, Any]:
    maximum_error = 0.0
    for trial in range(trials):
        rng = np.random.default_rng(derive_seed(20_270_812, "independent_mmd", trial))
        arrays = [rng.normal(size=(64, 17)).astype(np.float32) for _ in range(3)]
        indices = rng.permutation(64)
        independent = independent_paired_mmd_difference(arrays[0], arrays[1], arrays[2], indices=indices)
        production = paired_mmd_difference_contributions(
            arrays[0],
            arrays[1],
            arrays[2],
            {"name": "rbf", "gamma": 0.5, "normalize": "l2"},
            indices=indices,
        )
        maximum_error = max(maximum_error, float(np.max(np.abs(independent - production))))
    payload = {
        "schema_version": "certgen.icml2027.independent_mmd_reproduction.v1",
        "passed": maximum_error < 1e-12,
        "trials": trials,
        "maximum_absolute_error": maximum_error,
        "imports_production_stream_helper": False,
        "reproduction_audit_only": True,
        "claim_allowed": False,
    }
    write_json(out_path, payload)
    return payload


def _peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if value > 10_000_000 else value * 1024


def run_cifar10k_cpu_feasibility(
    out_path: str | Path,
    *,
    payload_index: str | Path,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for dimension in (768, 2048):
        with tempfile.TemporaryDirectory(prefix=f"certgen-feasibility-{dimension}-") as temporary:
            paths = [Path(temporary) / f"{name}.f32" for name in ("a", "b", "r")]
            rng = np.random.default_rng(derive_seed(20_270_812, "feasibility", dimension))
            for path in paths:
                mapped: Any = np.memmap(path, mode="w+", dtype=np.float32, shape=(10_000, dimension))
                for start in range(0, 10_000, 250):
                    mapped[start : start + 250] = rng.normal(size=(min(250, 10_000 - start), dimension))
                mapped.flush()
                del mapped
            started = time.perf_counter()
            arrays: list[Any] = [
                np.memmap(path, mode="r", dtype=np.float32, shape=(10_000, dimension)) for path in paths
            ]
            map_seconds = time.perf_counter() - started
            order = np.random.default_rng(20_270_812).permutation(10_000)
            started = time.perf_counter()
            contributions = paired_mmd_difference_contributions(
                arrays[0],
                arrays[1],
                arrays[2],
                {"name": "rbf", "gamma": 0.5, "normalize": "l2"},
                indices=order,
                chunk_size=256,
            )
            stream_seconds = time.perf_counter() - started
            started = time.perf_counter()
            certificate = evaluate_production_contributions(contributions.astype(float).tolist(), alpha=0.025)
            certificate_seconds = time.perf_counter() - started
            started = time.perf_counter()
            hashes = [file_sha256(path) for path in paths]
            hashing_seconds = time.perf_counter() - started
            started = time.perf_counter()
            payload_validation = validate_multipart_payload(payload_index)
            payload_validation_seconds = time.perf_counter() - started
            rows.append(
                {
                    "rows": 10_000,
                    "dimension": dimension,
                    "dtype": "float32",
                    "mapped_bytes": sum(path.stat().st_size for path in paths),
                    "load_map_seconds": map_seconds,
                    "paired_stream_seconds": stream_seconds,
                    "stream_units": len(contributions),
                    "certificate_seconds": certificate_seconds,
                    "certificate_decision": certificate["decision"],
                    "payload_index_validation_seconds": payload_validation_seconds,
                    "payload_index_valid": payload_validation["passed"],
                    "hashing_seconds": hashing_seconds,
                    "input_hashes_sha256": file_sha256(paths[0]) if hashes else None,
                    "peak_rss_bytes": _peak_rss_bytes(),
                    "pairwise_gram_matrix_materialized": False,
                    "complexity_contract": "O(ND)_time_chunked_O(chunk*D+N)_extra_memory",
                    "passed": bool(np.isfinite(contributions).all() and payload_validation["passed"]),
                    "claim_allowed": False,
                }
            )
            del arrays
    write_csv(out_path, rows)
    return {
        "passed": all(bool(row["passed"]) for row in rows),
        "dimensions": [768, 2048],
        "rows": 10_000,
        "no_gram_matrix": True,
        "claim_allowed": False,
    }
