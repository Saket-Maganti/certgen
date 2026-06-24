"""Paper-facing figure specs with non-evidence labels."""

from __future__ import annotations


def figure_specs() -> list[dict]:
    names = [
        "optional_stopping_validity",
        "samples_to_decision_curve",
        "ranking_stability_graph",
        "decidedness_audit_bar_chart",
        "metric_disagreement_panel",
    ]
    return [{"figure_id": name, "watermark": "NON-EVIDENCE / TEMPLATE / SYNTHETIC", "claim_allowed": False} for name in names]
