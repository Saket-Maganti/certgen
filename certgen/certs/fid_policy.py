"""V2 FID/FD policy enforcement."""

from __future__ import annotations

from certgen.core.enums import FidRigorStatus, MetricFamily


FID_LIKE_FAMILIES = {MetricFamily.FID.value, MetricFamily.FD_DINOV2.value, "fid", "fd_dinov2"}


def assert_no_rigorous_fid_claim(certificate: dict) -> None:
    metric = str(certificate.get("metric_label") or certificate.get("metric_name") or "").lower()
    family = str(certificate.get("metric_family") or "").lower()
    rigorous_flag = bool(certificate.get("rigorous_anytime_certificate"))
    decision = str(certificate.get("decision") or certificate.get("status") or "").lower()
    theory_status = str(certificate.get("theory_status") or "").lower()
    if "fid" in metric or "fd_dinov2" in metric or family in FID_LIKE_FAMILIES:
        if rigorous_flag or "rigorous" in theory_status or "certified" in decision:
            raise ValueError("FID/FD-DINOv2 cannot claim rigorous anytime certification in V2")


def fid_policy_summary(metric_label: str) -> dict:
    is_fid_like = "fid" in metric_label.lower() or "fd_dinov2" in metric_label.lower()
    return {
        "metric_label": metric_label,
        "is_fid_like": is_fid_like,
        "fid_rigor_status": FidRigorStatus.DESCRIPTIVE_ONLY.value if is_fid_like else None,
        "rigorous_anytime_certificate_allowed": False if is_fid_like else True,
        "claim_basis_allowed": False if is_fid_like else None,
    }
