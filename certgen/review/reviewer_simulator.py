"""V5 reviewer attack bank and score simulator."""

from __future__ import annotations

from typing import Any


REQUIRED_ATTACKS = [
    "This is just KID/CMMD with a stopping rule.",
    "Anytime-valid CS is known; where is the vision contribution?",
    "FID is not certifiable by your method.",
    "You do not propose a new metric.",
    "The audit is small / only toy datasets.",
    "Released samples are biased or cherry-picked.",
    "Preprocessing differences invalidate comparisons.",
    "Multiple comparisons inflate false discoveries.",
    "Dependence between comparisons invalidates your inference.",
    "Results are obvious: small gaps are uncertain.",
    "The paper is a statistics paper, not CVPR.",
    "The contribution overlaps with recent anytime-valid evaluation work.",
    "No human preference validation.",
    "No video results.",
    "Your result does not prove prior papers are wrong.",
]


def reviewer_attack_bank() -> list[dict[str, Any]]:
    cards = []
    for idx, attack in enumerate(REQUIRED_ATTACKS, start=1):
        fid = "FID" in attack
        cards.append(
            {
                "attack_id": f"V5A{idx:02d}",
                "attack": attack,
                "severity": "high" if idx in {1, 2, 3, 8, 9, 11, 12} else "medium",
                "response": (
                    "FID and FD are descriptive-only unless a separate rigorous policy audit is added; the clean-core certificate is for valid stream metrics."
                    if fid
                    else "Response is conditional before real runs: CertGen is a decision layer and audit protocol, and empirical strength remains blocked until the first real pilot."
                ),
                "paper_section": "limitations" if fid else "method_or_experiments",
                "requires_real_results": idx in {5, 10, 14, 15},
                "claim_allowed": False,
            }
        )
    return cards


def author_response_bank() -> list[dict[str, Any]]:
    return [{"attack_id": card["attack_id"], "draft_response": card["response"], "result_sensitive": card["requires_real_results"]} for card in reviewer_attack_bank()]


def simulate_v5_scorecard(real_results_present: bool = False) -> dict[str, Any]:
    return {
        "novelty": "medium",
        "technical_correctness": "draft_reviewable",
        "empirical_strength": "blocked_until_real_runs" if not real_results_present else "requires_audit_review",
        "cvpr_fit": "conditional_on_visual_audit_story",
        "reproducibility": "ready_except_runs",
        "clarity": "draft",
        "risk_of_incremental_rejection": "high_before_real_results",
        "risk_of_stats_only_rejection": "high_before_real_results",
        "claim_allowed": False,
    }
