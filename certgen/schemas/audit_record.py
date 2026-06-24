from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AuditClaimRecord:
    claim_id: str
    pair_id: str
    claim_text: str
    metric_name: str
    reported_direction: str
    recomputed_direction: str | None
    certificate_status: str | None
    decided_at_n: int | None
    evidence_status: str
    limitations: list[str]
