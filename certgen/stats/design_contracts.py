"""Typed V2 statistical contracts.

Direction convention: stream values estimate Delta_AB = d(A, R) - d(B, R).
Negative means model A is closer to the reference under the chosen clean metric;
positive means model B is closer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FeatureSet:
    feature_id: str
    features: Any
    feature_type: str
    evidence_status: str
    source_path: str | None = None
    sha256: str | None = None


@dataclass
class ComparisonStream:
    comparison_id: str
    metric_label: str
    values: list[float]
    direction: str = "negative_mean_A_better_positive_mean_B_better"
    evidence_status: str = "smoke_only"
    bounded: bool = False
    lower_bound: float | None = None
    upper_bound: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def mean(self) -> float:
        if not self.values:
            raise ValueError("empty comparison stream")
        return float(sum(self.values) / len(self.values))


@dataclass
class CSConfig:
    alpha: float
    budget_units: int
    lower_bound: float
    upper_bound: float
    method: str = "betting"
    seed: int = 0


@dataclass
class CSResult:
    method_label: str
    theory_status: str
    time_uniform: bool
    sample_units_seen: int
    budget_units: int
    mean_estimate: float
    lower: float
    upper: float
    states: list[dict[str, float]]


@dataclass
class DecisionCertificate:
    metric_label: str
    comparison_id: str
    alpha: float
    method_label: str
    time_uniform: bool
    sample_units_seen: int
    budget_units: int
    mean_estimate: float
    lower: float
    upper: float
    decision: str
    evidence_status: str
    theory_status: str
    boundedness_metadata: dict[str, Any]
    created_at: str
    feature_hashes: dict[str, str] = field(default_factory=dict)
    stream_hash: str | None = None
    command_provenance: dict[str, Any] = field(default_factory=dict)
    software_version: str | None = None
    claim_allowed: bool = False
    limitations: list[str] = field(default_factory=list)


def direction_for_mean(mean_value: float) -> str:
    if mean_value < 0:
        return "A_better_direction"
    if mean_value > 0:
        return "B_better_direction"
    return "no_direction"
