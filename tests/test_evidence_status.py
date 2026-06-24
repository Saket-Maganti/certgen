from certgen.core.enums import EvidenceStatus
from certgen.gates.evidence_gate import (
    certificate_evidence_status_for_inputs,
    validate_evidence_status,
    validate_records,
)


def test_real_evidence_blocked_in_smoke_mode():
    decision = validate_evidence_status(EvidenceStatus.REAL_EVIDENCE_CANDIDATE.value, mode="smoke")
    assert not decision.passed


def test_smoke_records_allowed():
    records = [{"evidence_status": EvidenceStatus.NON_EVIDENCE_SMOKE.value}]
    assert validate_records(records, mode="smoke").passed


def test_non_evidence_inputs_cannot_promote_requested_real_evidence():
    status = certificate_evidence_status_for_inputs(
        [EvidenceStatus.NON_EVIDENCE_SMOKE.value],
        requested_status=EvidenceStatus.REAL_EVIDENCE_CANDIDATE.value,
    )
    assert status == EvidenceStatus.NON_EVIDENCE_SMOKE.value
