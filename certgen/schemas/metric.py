from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MetricRecord:
    metric_name: str
    metric_family: str
    feature_type: str
    estimator_type: str
    supports_clean_cs: bool
    fid_rigor_status: str | None
    evidence_status: str
