"""Shared string enums for claim-safe CertGen artifacts."""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    """Python 3.10-compatible string enum base."""

    def __str__(self) -> str:
        return self.value


class EvidenceStatus(StrEnum):
    REAL_EVIDENCE_CANDIDATE = "real_evidence_candidate"
    NON_EVIDENCE_SMOKE = "non_evidence_smoke"
    NON_EVIDENCE_MOCK = "non_evidence_mock"
    NON_EVIDENCE_SYNTHETIC = "non_evidence_synthetic"
    NON_EVIDENCE_PLANNED = "non_evidence_planned"
    SMOKE_ONLY = "smoke_only"
    DEMO_ONLY = "demo_only"
    DRY_RUN_ONLY = "dry_run_only"
    PLANNED = "planned"
    SYNTHETIC_ONLY = "synthetic_only"
    PLANNED_ONLY = "planned_only"
    REAL_FEATURES_UNVALIDATED = "real_features_unvalidated"
    REAL_FEATURES_VALIDATED = "real_features_validated"
    REAL_PILOT_PENDING = "real_pilot_pending"
    PILOT_ONLY = "pilot_only"
    REAL_PILOT_NON_CLAIM = "real_pilot_non_claim"
    REAL_PILOT_CLAIM_BLOCKED = "real_pilot_claim_blocked"
    REAL_PILOT_CLAIM_ELIGIBLE = "real_pilot_claim_eligible"
    ELIGIBLE_AFTER_REAL_RUN = "eligible_after_real_run"
    DESCRIPTIVE_ONLY = "descriptive_only"


class MetricFamily(StrEnum):
    FID = "fid"
    KID = "kid"
    MMD = "mmd"
    CMMD = "cmmd"
    FD_DINOV2 = "fd_dinov2"
    PRECISION_RECALL = "precision_recall"


class CertificateStatus(StrEnum):
    CERTIFIED_A_BETTER = "certified_a_better"
    CERTIFIED_B_BETTER = "certified_b_better"
    NOT_DECIDED_AT_BUDGET = "not_decided_at_budget"
    INVALID_NOT_EVIDENCE = "invalid_not_evidence"
    DESCRIPTIVE_ONLY = "descriptive_only"
    FAILED_POLICY_GATE = "failed_policy_gate"


class FidRigorStatus(StrEnum):
    DESCRIPTIVE_ONLY = "descriptive_only"
    BLOCK_CS_EXPERIMENTAL = "block_cs_experimental"
    BIAS_CORRECTED_EXPERIMENTAL = "bias_corrected_experimental"
    RIGOROUS_PROOF_REQUIRED = "rigorous_proof_required"


NON_EVIDENCE_STATUSES = {
    EvidenceStatus.NON_EVIDENCE_SMOKE.value,
    EvidenceStatus.NON_EVIDENCE_MOCK.value,
    EvidenceStatus.NON_EVIDENCE_SYNTHETIC.value,
    EvidenceStatus.NON_EVIDENCE_PLANNED.value,
    EvidenceStatus.SMOKE_ONLY.value,
    EvidenceStatus.DEMO_ONLY.value,
    EvidenceStatus.DRY_RUN_ONLY.value,
    EvidenceStatus.PLANNED.value,
    EvidenceStatus.SYNTHETIC_ONLY.value,
    EvidenceStatus.PLANNED_ONLY.value,
    EvidenceStatus.REAL_FEATURES_UNVALIDATED.value,
    EvidenceStatus.REAL_FEATURES_VALIDATED.value,
    EvidenceStatus.REAL_PILOT_PENDING.value,
    EvidenceStatus.PILOT_ONLY.value,
    EvidenceStatus.REAL_PILOT_NON_CLAIM.value,
    EvidenceStatus.REAL_PILOT_CLAIM_BLOCKED.value,
    EvidenceStatus.ELIGIBLE_AFTER_REAL_RUN.value,
    EvidenceStatus.DESCRIPTIVE_ONLY.value,
}

CLAIM_ELIGIBLE_STATUSES = {
    EvidenceStatus.REAL_PILOT_CLAIM_ELIGIBLE.value,
}

V3_EVIDENCE_STATUSES = {
    EvidenceStatus.SMOKE_ONLY.value,
    EvidenceStatus.SYNTHETIC_ONLY.value,
    EvidenceStatus.DRY_RUN_ONLY.value,
    EvidenceStatus.PLANNED_ONLY.value,
    EvidenceStatus.REAL_FEATURES_UNVALIDATED.value,
    EvidenceStatus.REAL_FEATURES_VALIDATED.value,
    EvidenceStatus.REAL_PILOT_PENDING.value,
    EvidenceStatus.PILOT_ONLY.value,
    EvidenceStatus.REAL_PILOT_NON_CLAIM.value,
    EvidenceStatus.REAL_PILOT_CLAIM_BLOCKED.value,
    EvidenceStatus.REAL_PILOT_CLAIM_ELIGIBLE.value,
}

SMOKE_ALLOWED_STATUSES = NON_EVIDENCE_STATUSES


def normalize_enum_value(value: str | Enum | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)
