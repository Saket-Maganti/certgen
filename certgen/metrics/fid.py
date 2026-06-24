"""Descriptive FID implementation for feature arrays."""

from __future__ import annotations

import numpy as np

from certgen.core.enums import EvidenceStatus, FidRigorStatus, MetricFamily
from certgen.schemas.metric import MetricRecord


def frechet_distance(x: np.ndarray, y: np.ndarray, *, eps: float = 1e-6) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.ndim != 2 or y.ndim != 2:
        raise ValueError("FID expects 2D feature arrays")
    if x.shape[1] != y.shape[1]:
        raise ValueError(f"Feature dimensions must match, got {x.shape[1]} and {y.shape[1]}")
    if np.array_equal(x, y):
        return 0.0
    try:
        from scipy.linalg import sqrtm
    except Exception as exc:  # pragma: no cover - exercised only when scipy is unavailable
        raise RuntimeError("scipy is required for descriptive FID sqrtm computation") from exc

    mu_x = x.mean(axis=0)
    mu_y = y.mean(axis=0)
    cov_x = np.cov(x, rowvar=False)
    cov_y = np.cov(y, rowvar=False)
    if cov_x.ndim == 0:
        cov_x = np.array([[float(cov_x)]])
        cov_y = np.array([[float(cov_y)]])

    covmean = sqrtm((cov_x + eps * np.eye(cov_x.shape[0])) @ (cov_y + eps * np.eye(cov_y.shape[0])))
    if np.iscomplexobj(covmean):
        covmean = covmean.real
    diff = mu_x - mu_y
    fid = diff @ diff + np.trace(cov_x + cov_y - 2.0 * covmean)
    return float(max(fid, 0.0))


def fid_metric_record(*, evidence_status: str = EvidenceStatus.NON_EVIDENCE_SMOKE.value) -> MetricRecord:
    return MetricRecord(
        metric_name="fid_inception",
        metric_family=MetricFamily.FID.value,
        feature_type="inception",
        estimator_type="fixed_n_descriptive",
        supports_clean_cs=False,
        fid_rigor_status=FidRigorStatus.DESCRIPTIVE_ONLY.value,
        evidence_status=evidence_status,
    )
