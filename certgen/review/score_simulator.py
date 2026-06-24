"""Internal CVPR scorecard simulator."""


def simulate_scorecard() -> dict:
    return {
        "disclaimer": "internal triage only, not an acceptance predictor",
        "novelty": "medium",
        "technical_correctness": "blocked_until_real_audit",
        "empirical_strength": "blocked_until_real_pilot",
        "reproducibility": "strong_infrastructure",
        "clarity": "draft",
        "significance": "depends_on_undecided_fraction",
        "limitations_honesty": "strong",
    }
