"""V5 claim contract and forbidden-claim audit."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from certgen.core.io import read_json, write_json


CLAIM_TYPES = {"method", "protocol", "statistical", "empirical", "reproducibility", "limitation"}
PLACEHOLDER_TOKEN = "TBD_REAL_RUN_REQUIRED"

FORBIDDEN_PRE_RUN_PHRASES = [
    "published wins are undecided",
    "most published wins are wrong",
    "most papers are wrong",
    "fid is useless",
    "fid is wrong",
    "fid-certified",
    "fid certified",
    "rigorous fid certificate",
    "ranking changes",
    "ranking movement",
    "compute savings",
    "model a beats model b",
    "model a is better",
    "% of claims fail",
]

SCAN_EXEMPT_NAMES = {
    "FORBIDDEN_CLAIMS.md",
    "CLAIM_CONTRACT.md",
    "CLAIM_LANGUAGE_POLICY_V4.md",
    "V5_FINAL_AUDIT.md",
}


def default_claim_contract() -> dict[str, Any]:
    claims = [
        {
            "claim_id": "C_METHOD_SCAFFOLD",
            "claim_text": "CertGen implements a design scaffold for metric-agnostic decision certification.",
            "claim_type": "method",
            "allowed_before_real_runs": True,
            "required_artifact_types": ["code", "docs"],
            "required_evidence_status": ["template_only", "dry_run_only"],
            "blocked_reason_if_pre_run": "",
            "fid_sensitive": False,
            "requires_citation": False,
            "citation_status": "not_needed",
        },
        {
            "claim_id": "C_CLEAN_CORE_IMPLEMENTED",
            "claim_text": "Clean-core KID/MMD/CMMD-style certificate scaffolds are implemented for non-evidence validation.",
            "claim_type": "statistical",
            "allowed_before_real_runs": True,
            "required_artifact_types": ["tests", "audit"],
            "required_evidence_status": ["smoke_only", "synthetic_only", "dry_run_only"],
            "blocked_reason_if_pre_run": "",
            "fid_sensitive": False,
            "requires_citation": True,
            "citation_status": "needed_unverified",
        },
        {
            "claim_id": "C_FID_DESCRIPTIVE_ONLY",
            "claim_text": "FID and FD-style metrics are descriptive-only unless a separate rigorous audit is added.",
            "claim_type": "limitation",
            "allowed_before_real_runs": True,
            "required_artifact_types": ["fid_policy"],
            "required_evidence_status": ["template_only", "dry_run_only"],
            "blocked_reason_if_pre_run": "",
            "fid_sensitive": True,
            "requires_citation": True,
            "citation_status": "needed_unverified",
        },
        {
            "claim_id": "C_UNDECIDED_FRACTION",
            "claim_text": "The first-benchmark undecided fraction has a numeric value.",
            "claim_type": "empirical",
            "allowed_before_real_runs": False,
            "required_artifact_types": ["real_pilot", "claim_trace", "certificate_audit"],
            "required_evidence_status": ["claim_eligible"],
            "blocked_reason_if_pre_run": "TBD_REAL_RUN_REQUIRED",
            "fid_sensitive": False,
            "requires_citation": False,
            "citation_status": "not_needed",
        },
    ]
    return {
        "contract_version": "0.5.0",
        "preferred_title": "How Many Samples Until You Know? Anytime-Valid Certificates for Generative Model Comparison",
        "title_candidates": [
            "How Many Samples Until You Know? Anytime-Valid Certificates for Generative Model Comparison",
            "CertGen: Anytime-Valid, Metric-Agnostic Decision Certificates for Generative-Model Comparison",
            "Are Generative-Model Wins Statistically Decided? A Peeking-Safe Audit of Visual Generation Metrics",
        ],
        "allowed_pre_run_claims": [
            "CertGen implements a design/scaffold for metric-agnostic decision certification.",
            "Clean-core KID/MMD/CMMD-style certificates are implemented or planned, depending on actual code state.",
            "FID is descriptive-only unless rigorously handled.",
            "Smoke/dry-run artifacts are non-evidence.",
            "The project is zero-cost/released-samples-oriented by design.",
        ],
        "forbidden_pre_run_claims": [
            "any undecided-fraction value",
            "any claim that published wins are undecided",
            "any ranking movement claim",
            "any compute-savings number",
            "any real benchmark result",
            "any rigorous FID certificate claim unless audited",
            "any claim that CertGen is a new metric",
            "any claim that FID is useless/wrong",
            "any claim that most papers are wrong",
        ],
        "claims": claims,
        "claim_allowed": False,
        "evidence_status": "template_only",
    }


def validate_claim_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for idx, claim in enumerate(contract.get("claims", []), start=1):
        for field in [
            "claim_id",
            "claim_text",
            "claim_type",
            "allowed_before_real_runs",
            "required_artifact_types",
            "required_evidence_status",
            "blocked_reason_if_pre_run",
            "fid_sensitive",
            "requires_citation",
            "citation_status",
        ]:
            if field not in claim:
                errors.append(f"claim {idx}: missing {field}")
        if claim.get("claim_type") not in CLAIM_TYPES:
            errors.append(f"{claim.get('claim_id')}: invalid claim_type")
        if not claim.get("allowed_before_real_runs") and not claim.get("blocked_reason_if_pre_run"):
            errors.append(f"{claim.get('claim_id')}: blocked reason required")
        if claim.get("requires_citation") and claim.get("citation_status") == "verified":
            errors.append(f"{claim.get('claim_id')}: verified citations are not allowed without source audit")
    return errors


def _scan_file(path: Path) -> list[str]:
    upper_name = path.name.upper()
    if path.name in SCAN_EXEMPT_NAMES or any(token in upper_name for token in ["POLICY", "CLAIM", "AUDIT", "HANDOFF", "NO_RESULTS", "STOP_CONDITION", "KILL_LIST"]):
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    lowered = text.lower()
    for safe_phrase in [
        "must not be used to claim a decidedness fraction, ranking movement",
        "no ranking movement claim",
        "no real ranking movement claim",
        "no ranking-change conclusion",
    ]:
        lowered = lowered.replace(safe_phrase, "")
    violations: list[str] = []
    for phrase in FORBIDDEN_PRE_RUN_PHRASES:
        if phrase in lowered:
            violations.append(f"{path}: forbidden phrase '{phrase}'")
    if re.search(r"\b\d{1,3}(?:\.\d+)?\s*%\b", text) and PLACEHOLDER_TOKEN not in text:
        violations.append(f"{path}: percent-like result number without placeholder")
    if re.search(r"\b(?:fid|kid|cmmd|mmd)\s*(?:=|:)\s*-?\d+(?:\.\d+)?", lowered) and PLACEHOLDER_TOKEN not in text:
        violations.append(f"{path}: metric-like result number without placeholder")
    return violations


def audit_claim_contract(contract_path: str | Path = "data/contracts/claim_contract_v5.json", roots: tuple[str, ...] = ("docs", "paper", "data/results")) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    path = Path(contract_path)
    if not path.exists():
        errors.append(f"missing claim contract: {path}")
        contract = {}
    else:
        contract = read_json(path)
        errors.extend(validate_claim_contract(contract))
    for root_name in roots:
        root = Path(root_name)
        if not root.exists():
            continue
        for file_path in root.glob("**/*"):
            if file_path.is_file() and file_path.suffix.lower() in {".md", ".tex", ".json"}:
                text = file_path.read_text(encoding="utf-8", errors="ignore").lower()
                if '"claim_allowed": true' in text:
                    errors.append(f"{file_path}: unsupported claim_allowed=true")
                errors.extend(_scan_file(file_path))
    return {
        "audit_name": "v5_claim_contract_audit",
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "claim_allowed": False,
        "evidence_status": "template_only",
    }


def write_claim_contract(path: str | Path = "data/contracts/claim_contract_v5.json") -> dict[str, Any]:
    contract = default_claim_contract()
    write_json(contract, path)
    return contract
