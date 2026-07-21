"""Optional CPU-only Monte Carlo diagnostics; permanently synthetic evidence."""

from __future__ import annotations

from math import sqrt
from typing import Any

import numpy as np

from certgen.certs.clean_core import make_clean_metric_certificate
from certgen.stats.design_contracts import CSConfig, ComparisonStream


def _wilson(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        raise ValueError("total must be positive")
    center = (successes + z * z / 2) / (total + z * z)
    radius = z * sqrt((successes * (total - successes) / total + z * z / 4) / (total + z * z)) / (total + z * z) ** 0.5
    return max(0.0, center - radius), min(1.0, center + radius)


def run_extended_synthetic_validation(*, repetitions: int = 200, budget_units: int = 500, alpha: float = 0.05, seed: int = 20260713) -> dict[str, Any]:
    if repetitions <= 0 or budget_units <= 0:
        raise ValueError("repetitions and budget_units must be positive")
    rng = np.random.default_rng(seed)
    null_decisions = 0
    positive_correct = 0
    positive_wrong = 0
    negative_correct = 0
    negative_wrong = 0
    censored_null = 0
    for repetition in range(repetitions):
        streams = {
            "null": rng.uniform(-3.0, 3.0, budget_units),
            "positive": np.clip(rng.normal(1.0, 0.25, budget_units), -3.0, 3.0),
            "negative": np.clip(rng.normal(-1.0, 0.25, budget_units), -3.0, 3.0),
        }
        decisions: dict[str, str] = {}
        for name, values in streams.items():
            stream = ComparisonStream(comparison_id=f"synthetic_{name}_{repetition}", metric_label="synthetic_bounded_mean", values=values.tolist(), evidence_status="synthetic_only", bounded=True, lower_bound=-3.0, upper_bound=3.0, metadata={"boundedness_metadata": {"delta_lower": -3.0, "delta_upper": 3.0}})
            certificate = make_clean_metric_certificate(stream, CSConfig(alpha=alpha, budget_units=budget_units, lower_bound=-3.0, upper_bound=3.0, method="hoeffding"))
            decisions[name] = certificate.decision
        null_decisions += decisions["null"] != "not_decided_at_budget"
        censored_null += decisions["null"] == "not_decided_at_budget"
        positive_correct += decisions["positive"] == "B_certified_better"
        positive_wrong += decisions["positive"] == "A_certified_better"
        negative_correct += decisions["negative"] == "A_certified_better"
        negative_wrong += decisions["negative"] == "B_certified_better"
    interval = _wilson(null_decisions, repetitions)
    return {
        "schema_version": "certgen.cvpr.synthetic_validation.v1",
        "repetitions": repetitions,
        "budget_units": budget_units,
        "alpha": alpha,
        "seed": seed,
        "null_any_decision_count": null_decisions,
        "null_any_decision_rate": null_decisions / repetitions,
        "null_rate_wilson_95": list(interval),
        "null_censored_count": censored_null,
        "positive_correct_count": positive_correct,
        "positive_false_direction_count": positive_wrong,
        "negative_correct_count": negative_correct,
        "negative_false_direction_count": negative_wrong,
        "synthetic_validation_only": True,
        "not_model_evidence": True,
        "claim_allowed": False,
    }
