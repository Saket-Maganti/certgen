"""FID-specific policy gate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from certgen.core.enums import EvidenceStatus, FidRigorStatus, MetricFamily, NON_EVIDENCE_STATUSES, normalize_enum_value


@dataclass
class PolicyDecision:
    passed: bool
    reason: str


def _field(record: Any, name: str) -> Any:
    if isinstance(record, dict):
        return record.get(name)
    return getattr(record, name, None)


def validate_fid_certificate_request(
    metric_record: Any,
    requested_rigor: str,
    mode: str,
    *,
    evidence_status: str | None = None,
    limitations: list[str] | None = None,
) -> PolicyDecision:
    family = normalize_enum_value(_field(metric_record, "metric_family"))
    rigor = normalize_enum_value(_field(metric_record, "fid_rigor_status"))
    requested = normalize_enum_value(requested_rigor)
    status = normalize_enum_value(evidence_status or _field(metric_record, "evidence_status"))
    limitations = limitations or []

    if family not in {MetricFamily.FID.value, MetricFamily.FD_DINOV2.value}:
        return PolicyDecision(True, "non-FID metric may use the normal policy path")

    if requested in {"clean_cs", "rigorous", "anytime_valid"}:
        return PolicyDecision(False, "FID-like metrics cannot enter the clean CS path in V1")

    if rigor == FidRigorStatus.DESCRIPTIVE_ONLY.value:
        if requested in {"descriptive", "descriptive_only", None}:
            return PolicyDecision(True, "FID-like metric allowed as descriptive-only V1 output")
        return PolicyDecision(False, f"requested FID rigor {requested} is not allowed for descriptive-only metric")

    if rigor == FidRigorStatus.BLOCK_CS_EXPERIMENTAL.value:
        if status not in NON_EVIDENCE_STATUSES:
            return PolicyDecision(False, "experimental FID block path must be non-evidence")
        if not any("experimental" in item.lower() for item in limitations):
            return PolicyDecision(False, "experimental FID block path must include an experimental limitation")
        return PolicyDecision(True, "experimental non-evidence FID block path allowed")

    if mode == "v1" or mode == "smoke":
        return PolicyDecision(False, "no V1 FID-like path may claim rigorous proof")

    return PolicyDecision(False, "unrecognized FID policy request")
