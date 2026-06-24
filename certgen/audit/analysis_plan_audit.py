"""V5 preregistration and analysis-plan lock audit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from certgen.core.hashing import stable_hash_json
from certgen.core.io import read_json, write_json


def default_analysis_plan() -> dict[str, Any]:
    return {
        "analysis_plan_version": "0.5.0",
        "primary_question": "When is one generative model certifiably better than another under a chosen metric, with optional-stopping-safe validity and a sample budget?",
        "primary_pilot_endpoint": "first_benchmark_undecided_fraction_among_preselected_contestable_pairs",
        "primary_metrics": ["kid_mmd_style", "cmmd_clip_mmd", "dino_mmd_optional", "fid_descriptive_only"],
        "primary_decision_rule": "stop_when_anytime_valid_cs_for_delta_excludes_zero_or_budget_exhausted",
        "outcomes": ["A_certified_better", "B_certified_better", "not_decided_at_budget", "invalid_or_rejected"],
        "go_no_go_thresholds": {"strong_go_min_undecided_fraction": 0.25, "conditional_go_min_undecided_fraction": 0.05, "weak_headline_below": 0.05},
        "multiple_comparisons": {"default": "bonferroni_family_wise_alpha", "alpha": 0.05},
        "dependence_diagnostics_required": True,
        "preprocessing_lock_required_fields": ["sample_size", "resize", "interpolation", "crop", "color_mode", "feature_extractor", "reference_set"],
        "exclusions": ["unverifiable_sample_provenance", "unavailable_feature_cache", "license_uncertainty", "failed_metric_reproduction", "mismatched_preprocessing"],
        "result_placeholder": "TBD_REAL_RUN_REQUIRED",
        "claim_allowed": False,
        "evidence_status": "template_only",
    }


def analysis_plan_hash(plan: dict[str, Any]) -> str:
    body = {k: v for k, v in plan.items() if k != "lock_hash"}
    return stable_hash_json(body)


def write_analysis_plan_lock(path: str | Path = "data/contracts/analysis_plan_lock_v5.json", hash_out: str | Path = "data/results/analysis_plan_lock_hash_v5.txt") -> dict[str, Any]:
    plan = default_analysis_plan()
    digest = analysis_plan_hash(plan)
    plan["lock_hash"] = digest
    write_json(plan, path)
    Path(hash_out).parent.mkdir(parents=True, exist_ok=True)
    Path(hash_out).write_text(digest + "\n", encoding="utf-8")
    return plan


def audit_analysis_plan_lock(path: str | Path = "data/contracts/analysis_plan_lock_v5.json", hash_path: str | Path = "data/results/analysis_plan_lock_hash_v5.txt", amendment_path: str | Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    plan_path = Path(path)
    hash_file = Path(hash_path)
    if not plan_path.exists():
        errors.append(f"missing analysis plan: {plan_path}")
        plan = {}
    else:
        plan = read_json(plan_path)
    if not hash_file.exists():
        errors.append(f"missing analysis plan hash: {hash_file}")
        recorded = ""
    else:
        recorded = hash_file.read_text(encoding="utf-8").strip()
    if plan:
        current = analysis_plan_hash(plan)
        embedded = plan.get("lock_hash", "")
        if embedded and embedded != current:
            errors.append("embedded analysis-plan hash mismatch")
        if recorded and recorded != current:
            if amendment_path and Path(amendment_path).exists():
                amendment = read_json(amendment_path)
                if amendment.get("posthoc") is not True or amendment.get("paper_claim_scope") != "exploratory":
                    errors.append("analysis-plan amendment is not marked posthoc exploratory")
                else:
                    warnings.append("analysis-plan hash differs under posthoc exploratory amendment")
            else:
                errors.append("recorded analysis-plan hash mismatch")
        for field in ["primary_question", "primary_pilot_endpoint", "primary_decision_rule", "outcomes", "exclusions"]:
            if not plan.get(field):
                errors.append(f"missing analysis-plan field: {field}")
    return {"passed": not errors, "errors": errors, "warnings": warnings, "claim_allowed": False, "evidence_status": "template_only"}
