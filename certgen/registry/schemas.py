"""V2 registry dataclasses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CandidateModelPairV2:
    comparison_id: str
    benchmark_id: str
    model_a_id: str
    model_b_id: str
    paper_or_source_id: str
    reported_metric_name: str
    reported_metric_a: str
    reported_metric_b: str
    reported_sample_size: str
    reported_preprocessing_note: str
    released_samples_a_status: str
    released_samples_b_status: str
    checkpoint_a_status: str
    checkpoint_b_status: str
    feature_cache_status: str
    license_status: str
    audit_eligibility: str
    blocker_reason: str


@dataclass
class ReportedMetricClaimV2:
    claim_id: str
    comparison_id: str
    metric_name: str
    claimed_winner: str
    reported_value_a: str
    reported_value_b: str
    reported_gap: str
    sample_size: str
    source_reference: str
    recomputed_status: str
    certificate_status: str
    claim_evidence_status: str
