"""High-dimensional CPU validation for the production paired-MMD stream."""

from __future__ import annotations

import math
import resource
import time
from pathlib import Path
from typing import Any

import numpy as np

from certgen.icml2027.common import derive_seed, load_mapping, write_csv, write_json
from certgen.metrics.streams import mmd_difference_stream
from certgen.stats.cs import confidence_sequence
from certgen.stats.design_contracts import CSConfig


SCENARIOS = (
    "identical_distribution_null",
    "exact_sample_identical_null",
    "tiny_mean_shift",
    "obvious_mean_shift",
    "near_tie",
    "scale_shift",
    "variance_inflation",
    "covariance_perturbation",
    "symmetric_multimodal_shift",
    "mode_dropping",
    "rare_mode_shift",
    "anisotropy",
    "heavy_tails",
    "mixture_alternative",
    "contamination_1pct",
    "contamination_2pct",
    "contamination_5pct",
    "contamination_10pct",
    "low_rank_manifold_shift",
    "sparse_high_dimensional_shift",
    "dense_weak_high_dimensional_shift",
    "finite_reference_with_replacement",
    "declared_reference_reuse",
)

SCENARIO_DIFFERENCES: dict[str, dict[str, bool]] = {
    "identical_distribution_null": {},
    "exact_sample_identical_null": {},
    "tiny_mean_shift": {"mean": True},
    "obvious_mean_shift": {"mean": True},
    "near_tie": {"mean": True},
    "scale_shift": {"covariance": True},
    "variance_inflation": {"covariance": True},
    "covariance_perturbation": {"covariance": True},
    "symmetric_multimodal_shift": {"higher_moments": True, "modes": True},
    "mode_dropping": {"higher_moments": True, "modes": True},
    "rare_mode_shift": {"higher_moments": True, "modes": True},
    "anisotropy": {"covariance": True},
    "heavy_tails": {"higher_moments": True},
    "mixture_alternative": {"mean": True, "higher_moments": True, "modes": True},
    "contamination_1pct": {"higher_moments": True, "contamination": True},
    "contamination_2pct": {"higher_moments": True, "contamination": True},
    "contamination_5pct": {"higher_moments": True, "contamination": True},
    "contamination_10pct": {"higher_moments": True, "contamination": True},
    "low_rank_manifold_shift": {"covariance": True, "manifold": True},
    "sparse_high_dimensional_shift": {"mean": True},
    "dense_weak_high_dimensional_shift": {"mean": True},
    "finite_reference_with_replacement": {},
    "declared_reference_reuse": {},
}


def binomial_wilson_interval(successes: int, trials: int, *, z: float = 1.959963984540054) -> list[float | None]:
    if trials <= 0:
        return [None, None]
    proportion = successes / trials
    denominator = 1.0 + z * z / trials
    center = (proportion + z * z / (2.0 * trials)) / denominator
    radius = z * math.sqrt(proportion * (1.0 - proportion) / trials + z * z / (4.0 * trials * trials)) / denominator
    lower = 0.0 if successes == 0 else max(0.0, center - radius)
    upper = 1.0 if successes == trials else min(1.0, center + radius)
    return [lower, upper]


def _normal(rng: np.random.Generator, count: int, dimension: int) -> np.ndarray:
    return rng.normal(size=(count, dimension)).astype(np.float32)


def _scenario_arrays(
    scenario: str, count: int, dimension: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    r = _normal(rng, count, dimension)
    a = _normal(rng, count, dimension)
    expected = "UNRESOLVED"
    if scenario == "identical_distribution_null":
        b = _normal(rng, count, dimension)
    elif scenario == "exact_sample_identical_null":
        a = r.copy()
        b = r.copy()
    elif scenario in {"tiny_mean_shift", "near_tie"}:
        b = _normal(rng, count, dimension) + np.float32(0.025 if scenario == "tiny_mean_shift" else 0.008)
        expected = "A_BETTER"
    elif scenario == "obvious_mean_shift":
        b = _normal(rng, count, dimension) + np.float32(5.0)
        expected = "A_BETTER"
    elif scenario == "scale_shift":
        b = _normal(rng, count, dimension) * np.float32(1.35)
        expected = "A_BETTER"
    elif scenario == "variance_inflation":
        b = _normal(rng, count, dimension) * np.float32(1.8)
        expected = "A_BETTER"
    elif scenario == "covariance_perturbation":
        b = _normal(rng, count, dimension)
        if dimension > 1:
            b[:, 1] = np.float32(0.8) * b[:, 0] + np.float32(0.6) * b[:, 1]
        expected = "A_BETTER"
    elif scenario == "symmetric_multimodal_shift":
        r_component = (rng.integers(0, 2, size=count).astype(np.float32) * 2.0 - 1.0)[:, None]
        a_component = (rng.integers(0, 2, size=count).astype(np.float32) * 2.0 - 1.0)[:, None]
        b_component = (rng.integers(0, 2, size=count).astype(np.float32) * 2.0 - 1.0)[:, None]
        r += r_component * np.float32(0.8)
        a += a_component * np.float32(0.8)
        b = _normal(rng, count, dimension) + b_component * np.float32(1.8)
        expected = "A_BETTER"
    elif scenario == "mode_dropping":
        r_component = (rng.integers(0, 2, size=count).astype(np.float32) * 2.0 - 1.0)[:, None]
        a_component = (rng.integers(0, 2, size=count).astype(np.float32) * 2.0 - 1.0)[:, None]
        r += r_component * np.float32(1.2)
        a += a_component * np.float32(1.2)
        # Retaining one symmetric component and recentering it produces this
        # unimodal zero-mean law: modes differ without an artificial mean gap.
        b = _normal(rng, count, dimension)
        expected = "A_BETTER"
    elif scenario == "rare_mode_shift":
        rare_probability = np.float32(0.05)
        rare_r = (rng.random(count) < rare_probability).astype(np.float32)[:, None]
        rare_a = (rng.random(count) < rare_probability).astype(np.float32)[:, None]
        common_offset = np.float32(-3.0) * rare_probability / (np.float32(1.0) - rare_probability)
        r += np.where(rare_r > 0, np.float32(3.0), common_offset)
        a += np.where(rare_a > 0, np.float32(3.0), common_offset)
        b = _normal(rng, count, dimension)
        expected = "A_BETTER"
    elif scenario == "anisotropy":
        r[:, 0] *= np.float32(2.5)
        a[:, 0] *= np.float32(2.5)
        b = _normal(rng, count, dimension)
        b[:, 0] *= np.float32(2.5)
        if dimension > 1:
            first = b[:, 0].copy()
            second = b[:, 1].copy()
            factor = np.float32(1.0 / np.sqrt(2.0))
            b[:, 0] = factor * (first - second)
            b[:, 1] = factor * (first + second)
        expected = "A_BETTER"
    elif scenario == "heavy_tails":
        b = rng.standard_t(2.2, size=(count, dimension)).astype(np.float32)
        expected = "A_BETTER"
    elif scenario == "mixture_alternative":
        mixture = (rng.random(count) < 0.30).astype(np.float32)[:, None]
        b = _normal(rng, count, dimension) + mixture * np.float32(1.5)
        expected = "A_BETTER"
    elif scenario.startswith("contamination_"):
        contamination_probability: float = {
            "contamination_1pct": 0.01,
            "contamination_2pct": 0.02,
            "contamination_5pct": 0.05,
            "contamination_10pct": 0.10,
        }[scenario]
        contaminated = (rng.random(count) < contamination_probability).astype(np.float32)[:, None]
        signs = (rng.integers(0, 2, size=count).astype(np.float32) * 2.0 - 1.0)[:, None]
        b = _normal(rng, count, dimension) + contaminated * signs * np.float32(5.0)
        expected = "A_BETTER"
    elif scenario == "low_rank_manifold_shift":
        rank = min(4, dimension)
        r = np.zeros((count, dimension), dtype=np.float32)
        a = np.zeros((count, dimension), dtype=np.float32)
        b = np.zeros((count, dimension), dtype=np.float32)
        r[:, :rank] = _normal(rng, count, rank)
        a[:, :rank] = _normal(rng, count, rank)
        b[:, -rank:] = _normal(rng, count, rank)
        noise = np.float32(0.02)
        r += noise * _normal(rng, count, dimension)
        a += noise * _normal(rng, count, dimension)
        b += noise * _normal(rng, count, dimension)
        expected = "A_BETTER"
    elif scenario == "sparse_high_dimensional_shift":
        b = _normal(rng, count, dimension)
        b[:, 0] += np.float32(0.75)
        expected = "A_BETTER"
    elif scenario == "dense_weak_high_dimensional_shift":
        b = _normal(rng, count, dimension) + np.float32(0.05)
        expected = "A_BETTER"
    elif scenario == "finite_reference_with_replacement":
        pool_count = max(8, min(count // 2, 512))
        pool = _normal(rng, pool_count, dimension)
        r = pool[rng.integers(0, pool_count, size=count, endpoint=False)]
        b = _normal(rng, count, dimension)
    elif scenario == "declared_reference_reuse":
        b = _normal(rng, count, dimension)
        r[1::2] = r[0::2][: len(r[1::2])]
    else:
        raise ValueError(f"unsupported production MMD scenario: {scenario}")
    return a, b, r, expected


def _cases(config: dict[str, Any]) -> list[tuple[str, int, int]]:
    dimensions = [int(value) for value in config["dimensions"]]
    budgets = [int(value) for value in config["sample_budgets"]]
    cases = [("identical_distribution_null", dimension, budget) for dimension in dimensions for budget in budgets]
    representative_dimensions = [int(value) for value in config.get("representative_dimensions", [64, 768])]
    representative_budgets = [int(value) for value in config.get("representative_budgets", [1000])]
    for scenario in SCENARIOS[1:]:
        for dimension in representative_dimensions:
            for budget in representative_budgets:
                cases.append((scenario, dimension, budget))
    return cases


def _peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if value > 10_000_000 else value * 1024


def evaluate_production_contributions(values: list[float], *, alpha: float) -> dict[str, Any]:
    """Evaluate the exact certificate-path union-Hoeffding confidence sequence."""

    result = confidence_sequence(
        values,
        CSConfig(
            alpha=alpha,
            budget_units=len(values),
            lower_bound=-3.0,
            upper_bound=3.0,
            method="hoeffding",
            seed=0,
        ),
    )
    decision = "UNRESOLVED"
    stopping_time = len(values)
    selected = result.states[-1]
    for state in result.states:
        if float(state["upper"]) < 0.0:
            decision = "A_BETTER"
        elif float(state["lower"]) > 0.0:
            decision = "B_BETTER"
        else:
            continue
        stopping_time = int(state["n"])
        selected = state
        break
    return {
        "decision": decision,
        "stopping_time": stopping_time,
        "mean": float(selected["mean"]),
        "lower": float(selected["lower"]),
        "upper": float(selected["upper"]),
        "confidence_width": float(selected["upper"] - selected["lower"]),
        "states": result.states,
        "method_label": result.method_label,
        "theory_status": result.theory_status,
    }


def run_production_mmd_validation(config_path: str | Path, out_dir: str | Path) -> dict[str, Any]:
    config = load_mapping(config_path)
    profile = str(config.get("profile", "quick"))
    alpha = float(config.get("alpha", 0.05))
    replicates = int(config.get("replicates", 1))
    master_seed = int(config.get("master_seed", 20270812))
    chunk_size = int(config.get("kernel_chunk_size", 512))
    rows: list[dict[str, Any]] = []
    for scenario, dimension, budget in _cases(config):
        for replicate in range(replicates):
            started = time.perf_counter()
            rng = np.random.default_rng(
                derive_seed(master_seed, profile, scenario, dimension, budget, replicate)
            )
            a, b, r, expected = _scenario_arrays(scenario, budget, dimension, rng)
            stream = mmd_difference_stream(
                a,
                b,
                r,
                {
                    "name": "rbf",
                    "gamma": float(config.get("gamma", 0.5)),
                    "normalize": "l2",
                    "bandwidth_protocol": "fixed_unit_sphere_gamma_0.5_v1",
                },
                seed=derive_seed(master_seed, "stream_order", scenario, dimension, budget, replicate),
                evidence_status="synthetic_validation_only",
                comparison_id=f"{scenario}_d{dimension}_n{budget}_r{replicate}",
                kernel_chunk_size=chunk_size,
                reference_sampling_metadata={
                    "sampling_scheme": "iid_with_replacement_from_fixed_empirical_population"
                    if scenario == "finite_reference_with_replacement"
                    else "synthetic_iid_rows",
                    "reference_reuse_declared": scenario == "declared_reference_reuse",
                    "claim_allowed": False,
                },
            )
            trace = evaluate_production_contributions(stream.values, alpha=alpha)
            decision = str(trace["decision"])
            false_positive = expected == "UNRESOLVED" and decision in {"A_BETTER", "B_BETTER"}
            directional_error = expected in {"A_BETTER", "B_BETTER"} and decision not in {
                expected,
                "UNRESOLVED",
            }
            null_coverage = None
            if expected == "UNRESOLVED":
                null_coverage = all(float(state["lower"]) <= 0.0 <= float(state["upper"]) for state in trace["states"])
            differences = SCENARIO_DIFFERENCES[scenario]
            rows.append(
                {
                    "profile": profile,
                    "scenario": scenario,
                    "dimension": dimension,
                    "sample_budget": budget,
                    "replicate": replicate,
                    "stream_units": len(stream.values),
                    "expected_direction": expected,
                    "decision": decision,
                    "false_positive": false_positive,
                    "directional_error": directional_error,
                    "unresolved": decision == "UNRESOLVED",
                    "null_coverage": null_coverage,
                    "confidence_width": trace["confidence_width"],
                    "stopping_time": trace["stopping_time"],
                    "samples_saved_vs_full_budget": len(stream.values) - int(trace["stopping_time"]),
                    "mean_delta": float(np.mean(stream.values)),
                    "mean_differs": bool(differences.get("mean", False)),
                    "covariance_differs": bool(differences.get("covariance", False)),
                    "higher_moments_differ": bool(differences.get("higher_moments", False)),
                    "modes_differ": bool(differences.get("modes", False)),
                    "contamination_differs": bool(differences.get("contamination", False)),
                    "manifold_differs": bool(differences.get("manifold", False)),
                    "production_cs_method": trace["method_label"],
                    "compute_seconds": time.perf_counter() - started,
                    "peak_rss_bytes": _peak_rss_bytes(),
                    "kernel_chunk_size": chunk_size,
                    "pairwise_matrix_materialized": False,
                    "complexity_contract": "O(ND)_time_O(chunk*D+N)_extra_memory",
                    "synthetic_validation_only": True,
                    "not_real_generator_evidence": True,
                    "not_empirical_paper_evidence": True,
                    "claim_allowed": False,
                }
            )
    target = Path(out_dir)
    write_csv(target / "raw_records.csv", rows)
    null_rows = [row for row in rows if row["expected_direction"] == "UNRESOLVED"]
    alternative_rows = [row for row in rows if row["expected_direction"] != "UNRESOLVED"]
    false_positives = sum(bool(row["false_positive"]) for row in null_rows)
    directional_errors = sum(bool(row["directional_error"]) for row in alternative_rows)
    correct_resolutions = sum(row["decision"] == row["expected_direction"] for row in alternative_rows)
    unresolved = sum(bool(row["unresolved"]) for row in rows)
    covered = sum(bool(row["null_coverage"]) for row in null_rows)
    summary = {
        "schema_version": "certgen.icml2027.production_mmd_validation.v1",
        "profile": profile,
        "passed": not any(bool(row["directional_error"]) for row in rows)
        and all(math.isfinite(float(row["confidence_width"])) for row in rows),
        "runs": len(rows),
        "scenarios": sorted({str(row["scenario"]) for row in rows}),
        "dimensions": sorted({int(row["dimension"]) for row in rows}),
        "sample_budgets": sorted({int(row["sample_budget"]) for row in rows}),
        "null_false_positive_rate": false_positives / max(1, len(null_rows)),
        "null_false_positive_wilson_95": binomial_wilson_interval(false_positives, len(null_rows)),
        "directional_error_rate": directional_errors / max(1, len(alternative_rows)),
        "directional_error_wilson_95": binomial_wilson_interval(directional_errors, len(alternative_rows)),
        "empirical_power": correct_resolutions / max(1, len(alternative_rows)),
        "empirical_power_wilson_95": binomial_wilson_interval(correct_resolutions, len(alternative_rows)),
        "unresolved_rate": unresolved / max(1, len(rows)),
        "unresolved_wilson_95": binomial_wilson_interval(unresolved, len(rows)),
        "null_anytime_coverage_rate": covered / max(1, len(null_rows)),
        "null_anytime_coverage_wilson_95": binomial_wilson_interval(covered, len(null_rows)),
        "mean_confidence_width": float(np.mean([float(row["confidence_width"]) for row in rows])),
        "mean_stopping_time": float(np.mean([int(row["stopping_time"]) for row in rows])),
        "median_stopping_time": float(np.median([int(row["stopping_time"]) for row in rows])),
        "p90_stopping_time": float(np.quantile([int(row["stopping_time"]) for row in rows], 0.90)),
        "p95_stopping_time": float(np.quantile([int(row["stopping_time"]) for row in rows], 0.95)),
        "mean_samples_saved_vs_full_budget": float(np.mean([int(row["samples_saved_vs_full_budget"]) for row in rows])),
        "mean_compute_seconds": float(np.mean([float(row["compute_seconds"]) for row in rows])),
        "peak_rss_bytes": max(int(row["peak_rss_bytes"]) for row in rows),
        "kernel_computation": "paired_rbf_o_nd_no_gram_matrix",
        "finite_population_without_replacement_status": "EXPERIMENTAL_NOT_SUPPORTED",
        "synthetic_validation_only": True,
        "not_real_generator_evidence": True,
        "not_empirical_paper_evidence": True,
        "claim_allowed": False,
    }
    write_json(target / "summary.json", summary)
    write_csv(
        target / "summary.csv",
        [{key: value for key, value in summary.items() if not isinstance(value, (list, dict))}],
    )
    return summary
