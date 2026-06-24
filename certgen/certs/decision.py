"""Decision-certificate construction."""

from __future__ import annotations

from typing import Any, Iterable

from certgen.certs.confidence_sequence import update_empirical_bernstein_cs
from certgen.certs.stopping import status_from_interval
from certgen.core.enums import CertificateStatus, FidRigorStatus, MetricFamily, normalize_enum_value
from certgen.core.hashing import stable_hash_json
from certgen.core.provenance import build_provenance
from certgen.gates.evidence_gate import certificate_evidence_status_for_inputs
from certgen.schemas.certificate import DecisionCertificate


def _field(record: Any, name: str) -> Any:
    if isinstance(record, dict):
        return record.get(name)
    return getattr(record, name, None)


def make_decision_certificate(
    comparison_record: Any,
    delta_stream: Iterable[float],
    alpha: float,
    max_samples: int,
    metric_record: Any,
    evidence_status: str,
) -> DecisionCertificate:
    values = [float(value) for value in list(delta_stream)[:max_samples]]
    comparison_id = str(_field(comparison_record, "comparison_id"))
    metric_name = str(_field(metric_record, "metric_name"))
    metric_family = normalize_enum_value(_field(metric_record, "metric_family"))
    supports_clean_cs = bool(_field(metric_record, "supports_clean_cs"))
    fid_rigor_status = normalize_enum_value(_field(metric_record, "fid_rigor_status"))
    final_evidence_status = certificate_evidence_status_for_inputs(
        [evidence_status, _field(metric_record, "evidence_status"), _field(comparison_record, "evidence_status")],
        requested_status=evidence_status,
    )
    point_estimate = sum(values) / len(values) if values else None

    if metric_family in {MetricFamily.FID.value, MetricFamily.FD_DINOV2.value} or not supports_clean_cs:
        return DecisionCertificate(
            certificate_id=stable_hash_json({"comparison_id": comparison_id, "metric": metric_name, "values": values})[:16],
            comparison_id=comparison_id,
            metric_name=metric_name,
            alpha=float(alpha),
            status=CertificateStatus.DESCRIPTIVE_ONLY.value,
            n_at_decision=None,
            max_samples=int(max_samples),
            lower=None,
            upper=None,
            point_estimate=point_estimate,
            optional_stopping_valid=False,
            fid_rigor_status=fid_rigor_status or FidRigorStatus.DESCRIPTIVE_ONLY.value,
            evidence_status=final_evidence_status,
            limitations=[
                "descriptive-only metric path",
                "clean optional-stopping certificate not available for this metric in V1",
                "smoke-only contract validation",
            ],
            provenance=build_provenance(notes=["V1 descriptive-only certificate artifact"]),
        )

    value_range = (-4.0, 4.0) if metric_name in {"mmd_rbf", "cmmd_clip_mmd"} else (-1.0, 1.0)
    states = update_empirical_bernstein_cs(values, alpha=alpha, value_range=value_range)
    status = CertificateStatus.NOT_DECIDED_AT_BUDGET.value
    n_at_decision = None
    chosen_state = states[-1] if states else None
    for state in states:
        status = status_from_interval(state.lower, state.upper)
        if status != CertificateStatus.NOT_DECIDED_AT_BUDGET.value:
            n_at_decision = state.n
            chosen_state = state
            break
    if chosen_state is None:
        lower = upper = None
        optional_stopping_valid = False
        method = "empty_stream"
    else:
        lower = chosen_state.lower
        upper = chosen_state.upper
        optional_stopping_valid = chosen_state.optional_stopping_valid
        method = chosen_state.method

    return DecisionCertificate(
        certificate_id=stable_hash_json({"comparison_id": comparison_id, "metric": metric_name, "values": values})[:16],
        comparison_id=comparison_id,
        metric_name=metric_name,
        alpha=float(alpha),
        status=status,
        n_at_decision=n_at_decision,
        max_samples=int(max_samples),
        lower=lower,
        upper=upper,
        point_estimate=point_estimate,
        optional_stopping_valid=optional_stopping_valid,
        fid_rigor_status=fid_rigor_status,
        evidence_status=final_evidence_status,
        limitations=[
            "toy smoke stream",
            "not for paper claims",
            f"V1 method: {method}",
        ],
        provenance=build_provenance(notes=["V1 smoke decision certificate"]),
    )
