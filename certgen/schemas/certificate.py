from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DecisionCertificate:
    certificate_id: str
    comparison_id: str
    metric_name: str
    alpha: float
    status: str
    n_at_decision: int | None
    max_samples: int
    lower: float | None
    upper: float | None
    point_estimate: float | None
    optional_stopping_valid: bool
    fid_rigor_status: str | None
    evidence_status: str
    limitations: list[str]
    provenance: dict[str, Any]
