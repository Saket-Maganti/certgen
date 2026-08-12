"""Conservatism benchmark for the canonical union-Hoeffding boundary."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np

from certgen.icml2027.common import derive_seed, load_mapping, write_csv, write_json
from certgen.icml2027.production_mmd import binomial_wilson_interval, evaluate_production_contributions
from certgen.stats.bounds import hoeffding_union_radius


def run_boundary_benchmark(config_path: str | Path, out_dir: str | Path) -> dict[str, Any]:
    config = load_mapping(config_path)
    replicates = int(config.get("replicates", 100))
    units = int(config.get("stream_units", 5000))
    alpha = float(config.get("alpha", 0.05))
    effects = [float(value) for value in config.get("effects", [0.0, 0.15, 0.3, 0.6, 1.0])]
    master_seed = int(config.get("master_seed", 20270812))
    records: list[dict[str, Any]] = []
    for effect in effects:
        for replicate in range(replicates):
            rng = np.random.default_rng(derive_seed(master_seed, "boundary", effect, replicate))
            values = np.clip(rng.normal(effect, 0.75, units), -3.0, 3.0).astype(float).tolist()
            union = evaluate_production_contributions(values, alpha=alpha)
            mean = float(np.mean(values))
            fixed_radius = 6.0 * math.sqrt(math.log(2.0 / alpha) / (2.0 * units))
            fixed_decision = "B_BETTER" if mean - fixed_radius > 0 else (
                "A_BETTER" if mean + fixed_radius < 0 else "UNRESOLVED"
            )
            for method, decision, stopping_time in (
                ("union_hoeffding_canonical", union["decision"], union["stopping_time"]),
                ("fixed_n_hoeffding_comparator", fixed_decision, units),
            ):
                records.append(
                    {
                        "method": method,
                        "effect": effect,
                        "replicate": replicate,
                        "decision": decision,
                        "correct_resolution": decision == "B_BETTER" if effect > 0 else False,
                        "false_positive": effect == 0.0 and decision != "UNRESOLVED",
                        "unresolved": decision == "UNRESOLVED",
                        "stopping_time": stopping_time,
                        "synthetic_validation_only": True,
                        "not_real_generator_evidence": True,
                        "not_empirical_paper_evidence": True,
                        "claim_allowed": False,
                    }
                )
    summary_rows: list[dict[str, Any]] = []
    for method in sorted({str(row["method"]) for row in records}):
        for effect in effects:
            selected = [row for row in records if row["method"] == method and row["effect"] == effect]
            successes = sum(bool(row["correct_resolution"]) for row in selected)
            false_positives = sum(bool(row["false_positive"]) for row in selected)
            unresolved = sum(bool(row["unresolved"]) for row in selected)
            summary_rows.append(
                {
                    "method": method,
                    "effect": effect,
                    "replicates": len(selected),
                    "power": successes / len(selected),
                    "power_wilson_95": binomial_wilson_interval(successes, len(selected)),
                    "type1": false_positives / len(selected),
                    "type1_wilson_95": binomial_wilson_interval(false_positives, len(selected)),
                    "unresolved_fraction": unresolved / len(selected),
                    "unresolved_wilson_95": binomial_wilson_interval(unresolved, len(selected)),
                    "mean_stopping_time": float(np.mean([int(row["stopping_time"]) for row in selected])),
                    "confirmatory_eligible": method == "union_hoeffding_canonical",
                    "claim_allowed": False,
                }
            )
    target = Path(out_dir)
    write_csv(target / "ANYTIME_BOUNDARY_COMPARISON.csv", summary_rows)
    write_csv(target / "raw_records.csv", records)
    summary = {
        "schema_version": "certgen.icml2027.anytime_boundary_benchmark.v1",
        "passed": True,
        "replicates": replicates,
        "stream_units": units,
        "canonical": {
            "method": "union_hoeffding_canonical",
            "formula": "(upper-lower)*sqrt(log(pi^2*n^2/(3*alpha))/(2*n))",
            "support": [-3.0, 3.0],
            "optional_stopping_guarantee": "countable-union fixed-time Hoeffding construction",
            "proof_status": "CANONICAL_LOCAL_CONTRACT",
            "confirmatory_eligible": True,
        },
        "sharper_boundaries": [
            {"method": "empirical_bernstein", "proof_status": "NOT_PROVEN", "confirmatory_eligible": False},
            {"method": "finite_grid_betting", "proof_status": "NOT_PROVEN", "confirmatory_eligible": False},
            {"method": "stitched_hoeffding", "proof_status": "NOT_IMPLEMENTED_NOT_VERIFIED", "confirmatory_eligible": False},
            {"method": "mixture_boundary", "proof_status": "NOT_IMPLEMENTED_NOT_VERIFIED", "confirmatory_eligible": False},
        ],
        "terminal_radius": hoeffding_union_radius(units, alpha, -3.0, 3.0),
        "synthetic_validation_only": True,
        "not_real_generator_evidence": True,
        "not_empirical_paper_evidence": True,
        "claim_allowed": False,
    }
    write_json(target / "ANYTIME_BOUNDARY_COMPARISON.summary.json", summary)
    return summary
