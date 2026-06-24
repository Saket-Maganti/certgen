from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ComparisonRecord:
    comparison_id: str
    dataset_id: str
    model_a_id: str
    model_b_id: str
    reference_id: str
    metric_name: str
    alpha: float
    max_samples: int
    evidence_status: str
