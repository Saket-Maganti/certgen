"""Prospective practical-equivalence decisions; exploratory pending theory audit."""

from __future__ import annotations

from typing import Any

from certgen.icml2027.sequential import evaluate_stream


def decide_equivalence(
    values: list[float],
    *,
    alpha: float,
    margin: float,
    margin_type: str = "absolute",
    normalization_scale: float | None = None,
) -> dict[str, Any]:
    if margin <= 0:
        raise ValueError("equivalence margin must be positive")
    if margin_type not in {"absolute", "normalized", "representation_specific"}:
        raise ValueError("unsupported equivalence margin type")
    resolved_margin = margin
    if margin_type == "normalized":
        if normalization_scale is None or normalization_scale <= 0:
            raise ValueError("normalized margin requires positive normalization_scale")
        resolved_margin *= normalization_scale
    trace = evaluate_stream(
        values,
        alpha=alpha,
        rule="anytime",
        true_mean=0.0,
        equivalence_margin=resolved_margin,
    )
    return {
        "schema_version": "certgen.icml2027.equivalence_decision.v1",
        "decision": trace.decision,
        "stopping_time": trace.stopping_time,
        "ci_lower": trace.lower,
        "ci_upper": trace.upper,
        "margin": resolved_margin,
        "margin_type": margin_type,
        "exploratory_until_theory_verified": True,
        "synthetic_validation_only": True,
        "not_real_generator_evidence": True,
        "not_empirical_paper_evidence": True,
        "claim_allowed": False,
    }
