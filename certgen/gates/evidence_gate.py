"""Evidence-status gates for V1 smoke and planned artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from certgen.core.enums import EvidenceStatus, NON_EVIDENCE_STATUSES, normalize_enum_value


@dataclass
class EvidenceGateDecision:
    passed: bool
    reason: str
    offending_statuses: list[str]


def _status_from_record(record: Any) -> str | None:
    if isinstance(record, dict):
        return normalize_enum_value(record.get("evidence_status"))
    return normalize_enum_value(getattr(record, "evidence_status", None))


def validate_evidence_status(evidence_status: str, *, mode: str = "smoke") -> EvidenceGateDecision:
    status = normalize_enum_value(evidence_status)
    if mode == "smoke" and status == EvidenceStatus.REAL_EVIDENCE_CANDIDATE.value:
        return EvidenceGateDecision(False, "real_evidence_candidate is blocked in smoke mode", [status])
    if mode == "smoke" and status not in NON_EVIDENCE_STATUSES:
        return EvidenceGateDecision(False, f"{status} is not allowed in smoke mode", [status or "missing"])
    return EvidenceGateDecision(True, "evidence status allowed", [])


def validate_records(records: Iterable[Any], *, mode: str = "smoke") -> EvidenceGateDecision:
    offending = []
    for record in records:
        status = _status_from_record(record)
        decision = validate_evidence_status(status or "missing", mode=mode)
        if not decision.passed:
            offending.extend(decision.offending_statuses)
    if offending:
        return EvidenceGateDecision(False, "one or more records fail the evidence gate", offending)
    return EvidenceGateDecision(True, "all records pass the evidence gate", [])


def certificate_evidence_status_for_inputs(input_statuses: Iterable[str], *, requested_status: str) -> str:
    statuses = {normalize_enum_value(status) for status in input_statuses}
    if EvidenceStatus.REAL_EVIDENCE_CANDIDATE.value in statuses:
        return requested_status
    if statuses and not statuses.issubset(NON_EVIDENCE_STATUSES):
        return EvidenceStatus.NON_EVIDENCE_SMOKE.value
    if requested_status == EvidenceStatus.REAL_EVIDENCE_CANDIDATE.value:
        return EvidenceStatus.NON_EVIDENCE_SMOKE.value
    return requested_status


def contains_real_evidence_status(value: Any) -> bool:
    if isinstance(value, dict):
        return any(contains_real_evidence_status(v) for v in value.values())
    if isinstance(value, list):
        return any(contains_real_evidence_status(v) for v in value)
    return normalize_enum_value(value) == EvidenceStatus.REAL_EVIDENCE_CANDIDATE.value
