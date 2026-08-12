"""CPU-only power, variance-reduction, and prospective kernel planning studies."""

from __future__ import annotations

import csv
import math
import time
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from certgen.icml2027.common import derive_seed, write_csv, write_json
from certgen.icml2027.production_mmd import (
    _scenario_arrays,
    binomial_wilson_interval,
    evaluate_production_contributions,
)
from certgen.icml2027.scientific_closure import classify_scenario
from certgen.metrics.streams import paired_mmd_difference_contributions
from certgen.stats.bounds import hoeffding_union_radius


SYNTHETIC_GATE = {
    "synthetic_validation_only": True,
    "not_real_generator_evidence": True,
    "not_empirical_paper_evidence": True,
    "claim_allowed": False,
}


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def recompute_true_alternative_power(
    source_paths: Iterable[str | Path],
    *,
    resolution_out: str | Path,
    summary_out: str | Path,
) -> dict[str, Any]:
    rows = [row for path in source_paths for row in _read_csv(path)]
    included = [
        row
        for row in rows
        if classify_scenario(row["scenario"])
        in {"EASY_ALTERNATIVE", "HARD_ALTERNATIVE", "REPRESENTATION_SPECIFIC_ALTERNATIVE"}
    ]
    grouped: dict[tuple[str, int, int], list[dict[str, str]]] = {}
    for row in included:
        key = (row["scenario"], int(row["dimension"]), int(row["sample_budget"]))
        grouped.setdefault(key, []).append(row)
    resolution_rows: list[dict[str, Any]] = []
    for (scenario, dimension, budget), selected in sorted(grouped.items()):
        correct = sum(row["decision"] == row["expected_direction"] for row in selected)
        unresolved = sum(row["decision"] == "UNRESOLVED" for row in selected)
        effects = np.asarray([float(row["mean_delta"]) for row in selected], dtype=float)
        effect = float(np.mean(effects))
        effect_sd = float(np.std(effects, ddof=1)) if len(effects) > 1 else None
        standardized = effect / effect_sd if effect_sd and effect_sd > 0 else None
        stream_units = max(int(row["stream_units"]) for row in selected)
        alpha = 0.025
        fixed_n = (
            math.ceil(18.0 * math.log(2.0 / alpha) / (effect * effect))
            if abs(effect) > 1e-12
            else None
        )
        stopping = np.asarray([int(row["stopping_time"]) for row in selected])
        resolution_rows.append(
            {
                "scenario": scenario,
                "dimension": dimension,
                "sample_budget": budget,
                "stream_units": stream_units,
                "replicates": len(selected),
                "paired_mmd_stream_mean": effect,
                "paired_mmd_between_replicate_sd": effect_sd,
                "standardized_effect_descriptive": standardized,
                "terminal_union_hoeffding_radius_alpha_0_025": hoeffding_union_radius(
                    stream_units, alpha, -3.0, 3.0
                ),
                "fixed_n_bounded_mean_required_units_approx": fixed_n,
                "correct_resolution_rate": correct / len(selected),
                "correct_resolution_wilson_95": binomial_wilson_interval(correct, len(selected)),
                "unresolved_fraction": unresolved / len(selected),
                "unresolved_wilson_95": binomial_wilson_interval(unresolved, len(selected)),
                "observed_stopping_median": float(np.median(stopping)),
                "observed_stopping_mean": float(np.mean(stopping)),
                "observed_stopping_p90": float(np.quantile(stopping, 0.90)),
                **SYNTHETIC_GATE,
            }
        )
    correct = sum(row["decision"] == row["expected_direction"] for row in included)
    unresolved = sum(row["decision"] == "UNRESOLVED" for row in included)
    power = correct / max(1, len(included))
    unresolved_fraction = unresolved / max(1, len(included))
    utility = "GREEN" if power > 0.60 else ("YELLOW" if power >= 0.20 else "RED")
    summary = {
        "schema_version": "certgen.icml2027.true_alternative_power.v2",
        "source_records": [str(path) for path in source_paths],
        "true_alternative_runs": len(included),
        "correct_resolutions": correct,
        "corrected_true_alternative_power": power,
        "corrected_true_alternative_power_wilson_95": binomial_wilson_interval(
            correct, len(included)
        ),
        "true_alternative_unresolved_fraction": unresolved_fraction,
        "true_alternative_unresolved_wilson_95": binomial_wilson_interval(
            unresolved, len(included)
        ),
        "minimum_utility_gate": utility,
        "invariance_controls_excluded": ["scale_shift", "variance_inflation"],
        "nulls_and_reference_stress_excluded": True,
        **SYNTHETIC_GATE,
    }
    write_csv(resolution_out, resolution_rows)
    write_json(summary_out, summary)
    return summary


def run_variance_reduction_study(
    out_path: str | Path,
    *,
    replicates: int = 100,
    budget: int = 2_000,
    dimension: int = 64,
) -> dict[str, Any]:
    scenarios = ("obvious_mean_shift", "dense_weak_high_dimensional_shift")
    records: list[dict[str, Any]] = []
    for scenario in scenarios:
        for replicate in range(replicates):
            rng = np.random.default_rng(derive_seed(20270812, "variance", scenario, replicate))
            a, b, r, expected = _scenario_arrays(scenario, budget, dimension, rng)
            streams = []
            for pairing in range(4):
                order = np.random.default_rng(
                    derive_seed(20270812, "pairing", scenario, replicate, pairing)
                ).permutation(budget)
                streams.append(
                    paired_mmd_difference_contributions(
                        a,
                        b,
                        r,
                        {"name": "rbf", "gamma": 0.5, "normalize": "l2"},
                        indices=order,
                    )
                )
            strategies = {
                "single_prospectively_fixed_pairing": streams[0],
                "four_frozen_pairings_reuse_exploratory": np.mean(np.stack(streams), axis=0),
                "nonoverlapping_block_mean_4": np.mean(
                    streams[0][: len(streams[0]) // 4 * 4].reshape(-1, 4), axis=1
                ),
            }
            for strategy, values in strategies.items():
                trace = evaluate_production_contributions(values.astype(float).tolist(), alpha=0.025)
                records.append(
                    {
                        "scenario": scenario,
                        "strategy": strategy,
                        "replicate": replicate,
                        "expected_direction": expected,
                        "decision": trace["decision"],
                        "correct_resolution": trace["decision"] == expected,
                        "incorrect_direction": trace["decision"] not in {expected, "UNRESOLVED"},
                        "stream_units": len(values),
                        "stream_mean": float(np.mean(values)),
                        "stream_variance": float(np.var(values, ddof=1)),
                        "terminal_width": trace["confidence_width"],
                        "stopping_time": trace["stopping_time"],
                        "validity_status": "VERIFIED_DIAGNOSTIC_ONLY"
                        if strategy in {
                            "single_prospectively_fixed_pairing",
                            "nonoverlapping_block_mean_4",
                        }
                        else "IMPLEMENTED_NOT_VERIFIED",
                        **SYNTHETIC_GATE,
                    }
                )
    summary_rows: list[dict[str, Any]] = []
    for scenario in scenarios:
        baseline_means = [
            float(row["stream_mean"])
            for row in records
            if row["scenario"] == scenario
            and row["strategy"] == "single_prospectively_fixed_pairing"
        ]
        baseline_mean = float(np.mean(baseline_means))
        for strategy in sorted({str(row["strategy"]) for row in records}):
            selected = [
                row
                for row in records
                if row["scenario"] == scenario and row["strategy"] == strategy
            ]
            correct = sum(bool(row["correct_resolution"]) for row in selected)
            wrong = sum(bool(row["incorrect_direction"]) for row in selected)
            means = [float(row["stream_mean"]) for row in selected]
            summary_rows.append(
                {
                    "scenario": scenario,
                    "strategy": strategy,
                    "replicates": len(selected),
                    "mean_effect": float(np.mean(means)),
                    "bias_vs_single_pairing_mean": float(np.mean(means)) - baseline_mean,
                    "between_replicate_variance": float(np.var(means, ddof=1)),
                    "power": correct / len(selected),
                    "power_wilson_95": binomial_wilson_interval(correct, len(selected)),
                    "incorrect_direction_rate": wrong / len(selected),
                    "incorrect_direction_wilson_95": binomial_wilson_interval(
                        wrong, len(selected)
                    ),
                    "mean_terminal_width": float(
                        np.mean([float(row["terminal_width"]) for row in selected])
                    ),
                    "mean_stopping_time": float(
                        np.mean([int(row["stopping_time"]) for row in selected])
                    ),
                    "validity_status": selected[0]["validity_status"],
                    **SYNTHETIC_GATE,
                }
            )
    write_csv(out_path, summary_rows)
    return {
        "schema_version": "certgen.icml2027.variance_reduction.v1",
        "replicates_per_scenario": replicates,
        "scenarios": list(scenarios),
        "strategies": sorted({str(row["strategy"]) for row in records}),
        "outcome_adaptive_pairing_used": False,
        "confirmatory_policy_changed": False,
        **SYNTHETIC_GATE,
    }


def run_kernel_power_study(
    out_path: str | Path,
    *,
    replicates: int = 25,
    budget: int = 1_000,
) -> dict[str, Any]:
    gammas = (0.125, 0.25, 0.5, 1.0, 2.0)
    scenarios = (
        "near_tie",
        "covariance_perturbation",
        "symmetric_multimodal_shift",
        "mode_dropping",
        "dense_weak_high_dimensional_shift",
    )
    records: list[dict[str, Any]] = []
    started = time.perf_counter()
    for dimension in (64, 768):
        for scenario in scenarios:
            for replicate in range(replicates):
                rng = np.random.default_rng(
                    derive_seed(20270812, "kernel_power", dimension, scenario, replicate)
                )
                a, b, r, expected = _scenario_arrays(scenario, budget, dimension, rng)
                order = np.random.default_rng(
                    derive_seed(20270812, "kernel_order", dimension, scenario, replicate)
                ).permutation(budget)
                for gamma in gammas:
                    values = paired_mmd_difference_contributions(
                        a,
                        b,
                        r,
                        {"name": "rbf", "gamma": gamma, "normalize": "l2"},
                        indices=order,
                    )
                    trace = evaluate_production_contributions(
                        values.astype(float).tolist(), alpha=0.025
                    )
                    records.append(
                        {
                            "scenario": scenario,
                            "dimension": dimension,
                            "gamma": gamma,
                            "replicate": replicate,
                            "expected_direction": expected,
                            "decision": trace["decision"],
                            "correct_resolution": trace["decision"] == expected,
                            "effect_mean": float(np.mean(values)),
                            "effect_sd": float(np.std(values, ddof=1)),
                            "stopping_time": trace["stopping_time"],
                            **SYNTHETIC_GATE,
                        }
                    )
    summary_rows: list[dict[str, Any]] = []
    for dimension in (64, 768):
        for scenario in scenarios:
            for gamma in gammas:
                selected = [
                    row
                    for row in records
                    if row["dimension"] == dimension
                    and row["scenario"] == scenario
                    and row["gamma"] == gamma
                ]
                correct = sum(bool(row["correct_resolution"]) for row in selected)
                effects = [float(row["effect_mean"]) for row in selected]
                summary_rows.append(
                    {
                        "scenario": scenario,
                        "dimension": dimension,
                        "gamma": gamma,
                        "frozen_confirmatory_gamma": gamma == 0.5,
                        "replicates": len(selected),
                        "mean_effect": float(np.mean(effects)),
                        "between_replicate_effect_sd": float(np.std(effects, ddof=1)),
                        "power": correct / len(selected),
                        "power_wilson_95": binomial_wilson_interval(correct, len(selected)),
                        "mean_stopping_time": float(
                            np.mean([int(row["stopping_time"]) for row in selected])
                        ),
                        "policy_status": "FROZEN_CONFIRMATORY_UNCHANGED"
                        if gamma == 0.5
                        else "PROSPECTIVE_PLANNING_ONLY_NEW_STUDY_REQUIRED",
                        **SYNTHETIC_GATE,
                    }
                )
    write_csv(out_path, summary_rows)
    return {
        "schema_version": "certgen.icml2027.kernel_power.v1",
        "rows": len(summary_rows),
        "replicates_per_cell": replicates,
        "budget": budget,
        "dimensions": [64, 768],
        "gammas": list(gammas),
        "frozen_gamma": 0.5,
        "frozen_study_modified": False,
        "cpu_seconds": time.perf_counter() - started,
        **SYNTHETIC_GATE,
    }
