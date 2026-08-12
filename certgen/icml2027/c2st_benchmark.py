"""Deterministic high-dimensional C2ST benchmark on production scenarios."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from certgen.icml2027.baselines.runner import _c2st_accuracy, _c2st_logistic
from certgen.icml2027.common import derive_seed, write_csv, write_json
from certgen.icml2027.production_mmd import _scenario_arrays


def run_c2st_benchmark(out_dir: str | Path, *, seed: int = 20270812) -> dict[str, Any]:
    scenarios = (
        "identical_distribution_null",
        "obvious_mean_shift",
        "covariance_perturbation",
        "symmetric_multimodal_shift",
        "mode_dropping",
        "heavy_tails",
    )
    rows: list[dict[str, Any]] = []
    for dimension in (64, 768):
        for scenario in scenarios:
            scenario_seed = derive_seed(seed, "c2st", dimension, scenario)
            rng = np.random.default_rng(scenario_seed)
            a, b, r, expected = _scenario_arrays(scenario, 120, dimension, rng)
            centroid_rng = np.random.default_rng(scenario_seed + 1)
            centroid_a = _c2st_accuracy(r, a, centroid_rng, folds=5)
            centroid_b = _c2st_accuracy(r, b, centroid_rng, folds=5)
            logistic_a = _c2st_logistic(r, a, seed=scenario_seed + 101, folds=5, permutations=9)
            logistic_b = _c2st_logistic(r, b, seed=scenario_seed + 211, folds=5, permutations=9)
            rows.append(
                {
                    "scenario": scenario,
                    "dimension": dimension,
                    "expected_mmd_direction": expected,
                    "c2st_centroid_reference_vs_a": centroid_a,
                    "c2st_centroid_reference_vs_b": centroid_b,
                    "c2st_logistic_reference_vs_a": logistic_a["accuracy"],
                    "c2st_logistic_reference_vs_b": logistic_b["accuracy"],
                    "c2st_logistic_p_reference_vs_a": logistic_a["permutation_p_value"],
                    "c2st_logistic_p_reference_vs_b": logistic_b["permutation_p_value"],
                    "folds": 5,
                    "permutations": 9,
                    "normalization": "StandardScaler_fit_inside_training_fold",
                    "synthetic_validation_only": True,
                    "not_real_generator_evidence": True,
                    "not_empirical_paper_evidence": True,
                    "claim_allowed": False,
                }
            )
    target = Path(out_dir)
    write_csv(target / "C2ST_HIGH_DIMENSION.csv", rows)
    summary = {
        "schema_version": "certgen.icml2027.c2st_high_dimension.v1",
        "passed": True,
        "rows": len(rows),
        "dimensions": [64, 768],
        "scenarios": list(scenarios),
        "centroid_preserved_as": "c2st_centroid",
        "logistic_baseline": "c2st_logistic",
        "permutation_calibrated": True,
        "claim_allowed": False,
    }
    write_json(target / "C2ST_HIGH_DIMENSION.summary.json", summary)
    return summary
