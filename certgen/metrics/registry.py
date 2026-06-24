"""Metric registry for V1 smoke metrics."""

from __future__ import annotations

from typing import Callable

from certgen.core.enums import EvidenceStatus, FidRigorStatus, MetricFamily
from certgen.metrics.cmmd import cmmd_polynomial, cmmd_rbf
from certgen.metrics.fid import frechet_distance
from certgen.metrics.fd_dinov2 import fd_dinov2_distance
from certgen.metrics.kid import kid_polynomial
from certgen.metrics.mmd import unbiased_mmd2
from certgen.schemas.metric import MetricRecord


METRIC_REGISTRY: dict[str, dict[str, object]] = {
    "kid_poly": {
        "family": MetricFamily.KID.value,
        "feature_type": "generic_or_inception",
        "supports_clean_cs": False,
        "descriptive_only": True,
        "fid_rigor_status": None,
        "estimator_type": "unbounded_polynomial_mmd_descriptive",
        "callable": kid_polynomial,
    },
    "cmmd_poly": {
        "family": MetricFamily.CMMD.value,
        "feature_type": "clip_like",
        "supports_clean_cs": False,
        "descriptive_only": True,
        "fid_rigor_status": None,
        "estimator_type": "unbounded_polynomial_mmd_descriptive",
        "callable": cmmd_polynomial,
    },
    "mmd_poly": {
        "family": MetricFamily.MMD.value,
        "feature_type": "generic",
        "supports_clean_cs": False,
        "descriptive_only": True,
        "fid_rigor_status": None,
        "estimator_type": "unbounded_polynomial_mmd_descriptive",
        "callable": kid_polynomial,
    },
    "mmd_rbf": {
        "family": MetricFamily.MMD.value,
        "feature_type": "normalized_features",
        "supports_clean_cs": True,
        "descriptive_only": False,
        "fid_rigor_status": None,
        "estimator_type": "bounded_rbf_mmd",
        "callable": lambda x, y: unbiased_mmd2(x, y, kernel="rbf", normalize="l2"),
    },
    "cmmd_clip_mmd": {
        "family": MetricFamily.CMMD.value,
        "feature_type": "clip_like_normalized",
        "supports_clean_cs": True,
        "descriptive_only": False,
        "fid_rigor_status": None,
        "estimator_type": "bounded_clip_feature_rbf_mmd",
        "callable": cmmd_rbf,
    },
    "fid_inception": {
        "family": MetricFamily.FID.value,
        "feature_type": "inception",
        "supports_clean_cs": False,
        "descriptive_only": True,
        "fid_rigor_status": FidRigorStatus.DESCRIPTIVE_ONLY.value,
        "estimator_type": "fixed_n_descriptive",
        "callable": frechet_distance,
    },
    "fd_dinov2": {
        "family": MetricFamily.FD_DINOV2.value,
        "feature_type": "dinov2",
        "supports_clean_cs": False,
        "descriptive_only": True,
        "fid_rigor_status": FidRigorStatus.DESCRIPTIVE_ONLY.value,
        "estimator_type": "fixed_n_descriptive",
        "callable": fd_dinov2_distance,
    },
}


def metric_record_from_registry(metric_name: str, *, evidence_status: str = EvidenceStatus.NON_EVIDENCE_SMOKE.value) -> MetricRecord:
    if metric_name not in METRIC_REGISTRY:
        raise KeyError(f"Unknown metric: {metric_name}")
    entry = METRIC_REGISTRY[metric_name]
    return MetricRecord(
        metric_name=metric_name,
        metric_family=str(entry["family"]),
        feature_type=str(entry["feature_type"]),
        estimator_type=str(entry["estimator_type"]),
        supports_clean_cs=bool(entry["supports_clean_cs"]),
        fid_rigor_status=entry["fid_rigor_status"] if entry["fid_rigor_status"] is None else str(entry["fid_rigor_status"]),
        evidence_status=evidence_status,
    )


def estimator_for(metric_name: str) -> Callable:
    if metric_name not in METRIC_REGISTRY:
        raise KeyError(f"Unknown metric: {metric_name}")
    return METRIC_REGISTRY[metric_name]["callable"]  # type: ignore[return-value]
