"""Safe V5 result injection for future real runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from certgen.audit.analysis_plan_audit import analysis_plan_hash
from certgen.core.io import read_json, write_json
from certgen.reporting.result_contracts import PLACEHOLDER_TOKEN, validate_placeholder_artifact


def default_result_card(result_card_id: str = "template_result_card") -> dict[str, Any]:
    return {
        "result_card_id": result_card_id,
        "benchmark": PLACEHOLDER_TOKEN,
        "model_pair": PLACEHOLDER_TOKEN,
        "metric": PLACEHOLDER_TOKEN,
        "verdict": PLACEHOLDER_TOKEN,
        "samples_to_decision": PLACEHOLDER_TOKEN,
        "undecided_fraction_contribution": PLACEHOLDER_TOKEN,
        "claim_allowed": False,
        "evidence_status": "template_only",
    }


def validate_claim_trace(trace: dict[str, Any]) -> list[str]:
    required = [
        "claim_id",
        "paper_location",
        "result_artifact_id",
        "source_provenance_id",
        "feature_cache_id",
        "preprocessing_lock_id",
        "metric_reproduction_id",
        "certificate_id",
        "audit_id",
        "evidence_status",
        "claim_allowed",
    ]
    return [f"missing claim trace field: {field}" for field in required if field not in trace]


def validate_injection_inputs(
    result_card: dict[str, Any],
    claim_trace: dict[str, Any],
    analysis_plan: dict[str, Any],
    recorded_hash: str,
    *,
    paper_claim: bool = False,
) -> list[str]:
    errors = validate_placeholder_artifact(result_card)
    errors.extend(validate_claim_trace(claim_trace))
    current_hash = analysis_plan_hash(analysis_plan)
    if recorded_hash and current_hash != recorded_hash:
        errors.append("analysis-plan hash mismatch")
    evidence_status = result_card.get("evidence_status", "template_only")
    if paper_claim and evidence_status != "claim_eligible":
        errors.append("paper claims require claim_eligible evidence")
    elif evidence_status not in {"template_only", "dry_run_only", "pilot_candidate", "pilot_nonclaim", "evidence_candidate", "claim_eligible"}:
        errors.append(f"unsupported evidence_status: {evidence_status}")
    if claim_trace.get("claim_allowed") is True and claim_trace.get("evidence_status") != "claim_eligible":
        errors.append("claim trace cannot allow claims before claim_eligible")
    metric = str(result_card.get("metric", "")).lower()
    if ("fid" in metric or "fd" in metric) and result_card.get("claim_allowed") and not result_card.get("fid_policy_approved"):
        errors.append("FID-sensitive claim lacks FID policy approval")
    return errors


def inject_results(
    result_card_path: str | Path,
    claim_trace_path: str | Path,
    analysis_plan_path: str | Path,
    lock_hash_path: str | Path,
    out_dir: str | Path,
    *,
    paper_claim: bool = False,
) -> dict[str, Any]:
    result_card = read_json(result_card_path)
    claim_trace = read_json(claim_trace_path)
    analysis_plan = read_json(analysis_plan_path)
    recorded_hash = Path(lock_hash_path).read_text(encoding="utf-8").strip() if Path(lock_hash_path).exists() else ""
    errors = validate_injection_inputs(result_card, claim_trace, analysis_plan, recorded_hash, paper_claim=paper_claim)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if errors:
        payload = {"injected": False, "errors": errors, "claim_allowed": False, "evidence_status": result_card.get("evidence_status", "template_only")}
    else:
        injected = result_card.get("evidence_status") in {"evidence_candidate", "claim_eligible"} and (not paper_claim or result_card.get("claim_allowed") is True)
        payload = {
            "injected": bool(injected),
            "errors": [],
            "claim_allowed": bool(result_card.get("claim_allowed")) and result_card.get("evidence_status") == "claim_eligible",
            "evidence_status": result_card.get("evidence_status", "template_only"),
            "placeholder_retained": not injected,
        }
    lines = ["# V5 Result Injection Report", "", "`NO_REAL_EVIDENCE`" if not payload["injected"] else "`REAL_EVIDENCE_REVIEW_REQUIRED`", "", f"Injected: `{payload['injected']}`", f"Claim allowed: `{payload['claim_allowed']}`", "", "## Errors"]
    lines.extend(f"- {error}" for error in payload["errors"] or ["none"])
    (out_dir / "result_injection_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, out_dir / "result_injection_report.json")
    return payload
