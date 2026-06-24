"""Comparison result-card specs."""


def comparison_result_card(comparison_id: str, source_claim: str = "template") -> dict:
    return {
        "comparison_id": comparison_id,
        "source_claim": source_claim,
        "sample_availability": "template",
        "preprocessing_lock": "template",
        "reproduction_status": "not_run",
        "certificate_decision": "not_run",
        "samples_to_decision": None,
        "evidence_status": "planned_only",
        "claim_allowed": False,
    }
