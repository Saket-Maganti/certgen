"""V5 result contracts for paper tables, figures, and cards."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from certgen.core.io import read_json, write_json


PLACEHOLDER_TOKEN = "TBD_REAL_RUN_REQUIRED"

REQUIRED_TABLES = {
    "table_1_audit_summary": ["benchmark", "metric", "number_of_model_pairs", "decided_A_better", "decided_B_better", "not_decided_at_budget", "invalid_or_rejected", "undecided_fraction", "claim_status"],
    "table_2_samples_to_decision": ["benchmark", "model_A", "model_B", "metric", "reported_sample_size", "budget", "samples_to_decision", "verdict", "alpha_policy", "preprocessing_lock_id"],
    "table_3_metric_agreement": ["benchmark", "model_pair", "FID_direction_descriptive", "KID_certificate_verdict", "CMMD_certificate_verdict", "DINO_or_other_verdict", "disagreement_flag", "claim_status"],
    "table_4_ranking_stability": ["benchmark", "metric", "naive_rank_order", "certified_partial_order", "number_of_rank_changes", "undecided_edges", "claim_status"],
}

REQUIRED_FIGURES = {
    "figure_1_conceptual_pipeline": ["released_samples", "feature_cache", "metric_stream", "cs_or_eprocess", "decision_certificate", "audit_report"],
    "figure_2_optional_stopping_validity_lab": ["synthetic_lab_summary"],
    "figure_3_samples_to_decision_curves": ["first_real_pilot_summary"],
    "figure_4_decidedness_ranking_stability_heatmap": ["decidedness_audit", "ranking_stability_report"],
    "figure_5_metric_disagreement_cards": ["metric_agreement_table", "result_cards"],
}


def _contract_item(artifact_id: str, artifact_type: str, required_inputs: list[str], allowed_pre_run: bool) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "required_inputs": required_inputs,
        "required_evidence_status": "claim_eligible" if not allowed_pre_run else "template_only",
        "allowed_pre_run": allowed_pre_run,
        "placeholder_required_before_run": True,
        "placeholder_token": PLACEHOLDER_TOKEN,
        "claim_allowed_condition": "claim_allowed=true only after result injection, claim trace, and V5 audit pass with claim_eligible evidence",
        "validation_command": "python3 -m certgen.audit.v5_audit --out docs/V5_FINAL_AUDIT.md --json-out data/results/v5_final_audit.json",
    }


def default_result_contracts() -> dict[str, Any]:
    items = []
    for artifact_id, columns in REQUIRED_TABLES.items():
        item = _contract_item(artifact_id, "table", columns, False)
        item["columns"] = columns
        items.append(item)
    for artifact_id, inputs in REQUIRED_FIGURES.items():
        items.append(_contract_item(artifact_id, "figure", inputs, artifact_id == "figure_1_conceptual_pipeline"))
    items.append(_contract_item("comparison_result_card_template", "card", ["claim_trace", "certificate"], False))
    return {"contract_version": "0.5.0", "placeholder_token": PLACEHOLDER_TOKEN, "items": items, "claim_allowed": False, "evidence_status": "template_only"}


def write_result_contracts(path: str | Path = "data/contracts/result_contracts_v5.json") -> dict[str, Any]:
    payload = default_result_contracts()
    write_json(payload, path)
    return payload


def load_result_contracts(path: str | Path = "data/contracts/result_contracts_v5.json") -> dict[str, Any]:
    return read_json(path)


def validate_result_contracts(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    items = payload.get("items", [])
    ids = {item.get("artifact_id") for item in items}
    for required in list(REQUIRED_TABLES) + list(REQUIRED_FIGURES):
        if required not in ids:
            errors.append(f"missing result contract item: {required}")
    for item in items:
        for field in ["artifact_id", "artifact_type", "required_inputs", "required_evidence_status", "allowed_pre_run", "placeholder_required_before_run", "claim_allowed_condition", "validation_command"]:
            if field not in item:
                errors.append(f"{item.get('artifact_id')}: missing {field}")
        if item.get("placeholder_required_before_run") and item.get("placeholder_token") != PLACEHOLDER_TOKEN:
            errors.append(f"{item.get('artifact_id')}: missing exact placeholder token")
    return errors


def validate_placeholder_artifact(artifact: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if artifact.get("claim_allowed") is True and artifact.get("evidence_status") != "claim_eligible":
        errors.append("claim_allowed=true requires claim_eligible evidence")
    if artifact.get("evidence_status") in {"template_only", "dry_run_only", "pilot_candidate"}:
        numeric_fields = [key for key, value in artifact.items() if not isinstance(value, bool) and isinstance(value, (int, float))]
        numeric_strings = [
            key
            for key, value in artifact.items()
            if isinstance(value, str) and PLACEHOLDER_TOKEN not in value and re.search(r"\b\d+(?:\.\d+)?\b", value)
        ]
        if numeric_fields or numeric_strings:
            errors.append("numeric-looking result in pre-run artifact without placeholder")
    return errors
