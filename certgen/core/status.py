"""V3 evidence-status and claim-allowance policy."""

from __future__ import annotations

from dataclasses import dataclass

from certgen.core.enums import CLAIM_ELIGIBLE_STATUSES, V3_EVIDENCE_STATUSES, normalize_enum_value


@dataclass
class ClaimPolicyDecision:
    passed: bool
    evidence_status: str
    claim_allowed: bool
    claim_blockers: list[str]


def validate_v3_evidence_status(evidence_status: str) -> bool:
    return normalize_enum_value(evidence_status) in V3_EVIDENCE_STATUSES


def evaluate_claim_policy(evidence_status: str, claim_allowed: bool, blockers: list[str] | None = None) -> ClaimPolicyDecision:
    status = normalize_enum_value(evidence_status) or ""
    blockers = list(blockers or [])
    if status not in V3_EVIDENCE_STATUSES:
        return ClaimPolicyDecision(False, status, bool(claim_allowed), [f"unknown evidence_status: {status}"])
    if claim_allowed and status not in CLAIM_ELIGIBLE_STATUSES:
        blockers.append(f"claim_allowed=true is forbidden for evidence_status={status}")
        return ClaimPolicyDecision(False, status, True, blockers)
    if status not in CLAIM_ELIGIBLE_STATUSES and not blockers:
        blockers.append("claim blocked until all real-pilot gates pass")
    return ClaimPolicyDecision(True, status, bool(claim_allowed), blockers)


def non_claim_artifact(evidence_status: str, blockers: list[str] | None = None) -> dict:
    decision = evaluate_claim_policy(evidence_status, False, blockers)
    if not decision.passed:
        raise ValueError("; ".join(decision.claim_blockers))
    return {
        "evidence_status": decision.evidence_status,
        "claim_allowed": False,
        "claim_blockers": decision.claim_blockers,
    }
