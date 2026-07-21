"""Multiple-comparison policies for V4 batch audits."""

from __future__ import annotations

import numpy as np


def allocate_alpha(alpha: float, num_comparisons: int, policy: str) -> dict:
    if not (0.0 < float(alpha) < 1.0):
        raise ValueError("alpha must be in (0, 1)")
    if num_comparisons <= 0:
        raise ValueError("num_comparisons must be positive")
    if policy == "bonferroni":
        return {"policy": policy, "alpha_used": alpha / num_comparisons, "adjusted_for_multiplicity": True, "claim_allowed": False}
    if policy == "unadjusted_exploratory":
        return {"policy": policy, "alpha_used": alpha, "adjusted_for_multiplicity": False, "claim_allowed": False, "warning": "exploratory_non_claim"}
    raise ValueError(f"unknown multiple-comparison policy: {policy}")


def plan_e_bh(alpha: float, num_hypotheses: int) -> dict:
    if not (0.0 < float(alpha) < 1.0):
        raise ValueError("alpha must be in (0, 1)")
    if num_hypotheses <= 0:
        raise ValueError("num_hypotheses must be positive")
    return {
        "policy": "e_bh_design_scaffold",
        "alpha": float(alpha),
        "num_hypotheses": int(num_hypotheses),
        "inputs_required": ["valid e-values from bounded-stream e-processes"],
        "implemented_for_claims": False,
        "claim_allowed": False,
    }


def e_bh(e_values: list[float], alpha: float) -> dict:
    """e-Benjamini-Hochberg (Wang & Ramdas, 2022).

    Given valid e-values e_1, ..., e_K (each E[e_i] <= 1 under its null), reject
    the k* hypotheses with the largest e-values where

        k* = max { k : e_(k) >= K / (alpha * k) }

    over the descending-sorted e-values e_(1) >= ... >= e_(K). This controls FDR
    at level alpha under arbitrary dependence between valid input e-values.
    This function is a fixed-analysis-time multiplicity operator.  It does not
    establish that locally stopped e-processes remain valid under a stopping
    time chosen from the global, dependent multi-comparison filtration.
    """

    if not (0.0 < float(alpha) < 1.0):
        raise ValueError("alpha must be in (0, 1)")
    e = np.asarray(e_values, dtype=float)
    if e.ndim != 1 or e.size == 0:
        raise ValueError("e_values must be a non-empty 1D sequence")
    if np.any(~np.isfinite(e)) or np.any(e < 0.0):
        raise ValueError("e-values must be finite and nonnegative")
    k = e.size
    order = np.argsort(-e, kind="stable")
    sorted_e = e[order]
    ranks = np.arange(1, k + 1)
    thresholds = k / (float(alpha) * ranks)
    meets = sorted_e >= thresholds
    k_star = int(np.max(np.where(meets)[0]) + 1) if np.any(meets) else 0
    rejected = sorted(int(i) for i in order[:k_star])
    return {
        "policy": "e_bh",
        "alpha": float(alpha),
        "num_hypotheses": int(k),
        "rejection_threshold_e_value": float(k / (float(alpha) * k_star)) if k_star else None,
        "num_rejections": int(k_star),
        "rejected_indices": rejected,
        "fdr_controlled_under_arbitrary_dependence": True,
        "validity_scope": "fixed_predeclared_analysis_time_with_valid_marginal_evalues",
        "global_optional_stopping_supported": False,
        "directional_fdr_supported": False,
        "claim_allowed": False,
    }


def audit_comparisons_with_fdr(comparisons: list[dict], alpha: float) -> dict:
    """Decidedness audit over many comparisons under FDR control.

    ``comparisons`` is a list of dicts with at least ``comparison_id`` and
    ``e_value`` (terminal betting e-value for the point null Delta = 0). Returns a
    per-comparison point-null rejection table.  Rejection means evidence against
    exact equality; it is not a directional certificate or ranking edge.
    """

    if not comparisons:
        raise ValueError("at least one comparison is required")
    e_values = [float(c["e_value"]) for c in comparisons]
    result = e_bh(e_values, alpha)
    rejected = set(result["rejected_indices"])
    table = []
    for index, comparison in enumerate(comparisons):
        decided = index in rejected
        table.append(
            {
                "comparison_id": comparison.get("comparison_id", f"comparison_{index}"),
                "e_value": float(comparison["e_value"]),
                "decided_under_fdr": bool(decided),
                "point_null_rejected_under_fdr": bool(decided),
                "status": "point_null_rejected" if decided else "point_null_not_rejected_at_budget",
            }
        )
    num = len(comparisons)
    decided_n = result["num_rejections"]
    return {
        "alpha": float(alpha),
        "num_comparisons": int(num),
        "num_decided": int(decided_n),
        "num_undecided": int(num - decided_n),
        "decided_fraction": float(decided_n / num),
        "undecided_fraction": float((num - decided_n) / num),
        "multiplicity_policy": "e_bh",
        "estimand_scope": "point_null_mean_difference_equals_zero",
        "directional_claim_supported": False,
        "global_optional_stopping_supported": False,
        "comparisons": table,
        "claim_allowed": False,
        "labels": ["not_paper_claim", "requires_real_runs_and_scaling"],
    }
