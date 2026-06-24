"""Descriptive FD-DINOv2 wrapper over DINOv2-like feature arrays."""

from __future__ import annotations

import numpy as np

from certgen.core.enums import EvidenceStatus, FidRigorStatus, MetricFamily
from certgen.metrics.fid import frechet_distance
from certgen.schemas.metric import MetricRecord


def fd_dinov2_distance(x: np.ndarray, y: np.ndarray) -> float:
    return frechet_distance(x, y)


def fd_dinov2_metric_record(*, evidence_status: str = EvidenceStatus.NON_EVIDENCE_SMOKE.value) -> MetricRecord:
    return MetricRecord(
        metric_name="fd_dinov2",
        metric_family=MetricFamily.FD_DINOV2.value,
        feature_type="dinov2",
        estimator_type="fixed_n_descriptive",
        supports_clean_cs=False,
        fid_rigor_status=FidRigorStatus.DESCRIPTIVE_ONLY.value,
        evidence_status=evidence_status,
    )
