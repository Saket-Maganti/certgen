"""Prospective resolution planning for bounded paired-MMD contributions."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from certgen.icml2027.common import load_mapping, write_csv, write_json
from certgen.stats.bounds import hoeffding_union_radius


def run_power_planning(config_path: str | Path, out_dir: str | Path) -> dict[str, Any]:
    config = load_mapping(config_path)
    rows: list[dict[str, Any]] = []
    alpha = float(config.get("alpha", 0.05))
    for sample_budget in config["budgets"]:
        units = int(sample_budget) // 2
        radius = hoeffding_union_radius(units, alpha, -3.0, 3.0)
        for effect_scaled in config["effect_grid_scaled_to_support"]:
            for standard_deviation_scaled in config["standard_deviation_grid_scaled_to_support"]:
                raw_effect = 3.0 * float(effect_scaled)
                raw_standard_deviation = 3.0 * float(standard_deviation_scaled)
                normal_signal_to_noise = raw_effect * math.sqrt(units) / max(raw_standard_deviation, 1e-12)
                rows.append(
                    {
                        "status": "EXPECTED_RESOLUTION_PLANNING_ONLY",
                        "sample_budget_per_distribution": int(sample_budget),
                        "paired_stream_units": units,
                        "effect_scaled_to_unit_support": float(effect_scaled),
                        "standard_deviation_scaled_to_unit_support": float(standard_deviation_scaled),
                        "union_hoeffding_radius_raw": radius,
                        "effect_exceeds_anytime_radius_at_budget": raw_effect > radius,
                        "normal_approximation_signal_to_noise_descriptive": normal_signal_to_noise,
                        "synthetic_validation_only": True,
                        "not_real_generator_evidence": True,
                        "not_empirical_paper_evidence": True,
                        "claim_allowed": False,
                    }
                )
    target = Path(out_dir)
    write_csv(target / "POWER_AWARE_PLANNING.csv", rows)
    summary = {
        "schema_version": "certgen.icml2027.power_aware_planning.v1",
        "status": "EXPECTED_RESOLUTION_PLANNING_ONLY",
        "rows": len(rows),
        "budget_resolution_counts": {
            str(budget): sum(
                bool(row["effect_exceeds_anytime_radius_at_budget"])
                for row in rows
                if row["sample_budget_per_distribution"] == int(budget)
            )
            for budget in config["budgets"]
        },
        "claim_allowed": False,
    }
    write_json(target / "POWER_AWARE_PLANNING.summary.json", summary)
    return summary
