"""V2 clean-core certificate construction."""

from __future__ import annotations

from dataclasses import asdict

from certgen.core.enums import NON_EVIDENCE_STATUSES
from certgen.core.hashing import stable_hash_json
from certgen.core.provenance import utc_now_iso
from certgen.stats.cs import confidence_sequence
from certgen.stats.design_contracts import CSConfig, ComparisonStream, DecisionCertificate
from certgen.stats.streams import require_bounded_stream


def decision_from_interval(lower: float, upper: float) -> str:
    if upper < 0:
        return "A_certified_better"
    if lower > 0:
        return "B_certified_better"
    return "not_decided_at_budget"


def make_clean_metric_certificate(
    stream: ComparisonStream,
    config: CSConfig,
    *,
    feature_hashes: dict[str, str] | None = None,
    command_provenance: dict | None = None,
) -> DecisionCertificate:
    if stream.evidence_status not in NON_EVIDENCE_STATUSES and stream.evidence_status != "eligible_after_real_run":
        raise ValueError("V2 clean certificate refuses real-evidence status without gates")
    if not stream.bounded:
        raise ValueError("clean metric certificates require a bounded stream")
    require_bounded_stream(stream)
    result = confidence_sequence(stream.values, config)
    chosen_state = result.states[-1]
    decision = "not_decided_at_budget"
    if result.time_uniform:
        for state in result.states:
            candidate = decision_from_interval(float(state["lower"]), float(state["upper"]))
            if candidate != "not_decided_at_budget":
                chosen_state = state
                decision = candidate
                break
    sample_units_seen = int(chosen_state["n"])
    limitations = [
        "NO_REAL_EVIDENCE",
        "R0 clean-core certificate path over bounded kernel-derived streams",
        "Claim export remains blocked until real provenance and registry gates pass",
    ]
    if not result.time_uniform:
        limitations.append("METHOD_NOT_CERTIFICATE_CAPABLE: unresolved time-uniform proof obligation")
    return DecisionCertificate(
        metric_label=stream.metric_label,
        comparison_id=stream.comparison_id,
        alpha=config.alpha,
        method_label=result.method_label,
        time_uniform=result.time_uniform,
        sample_units_seen=sample_units_seen,
        budget_units=result.budget_units,
        mean_estimate=float(chosen_state["mean"]),
        lower=float(chosen_state["lower"]),
        upper=float(chosen_state["upper"]),
        decision=decision,
        evidence_status=stream.evidence_status,
        theory_status=result.theory_status,
        boundedness_metadata=stream.metadata.get("boundedness_metadata", {}),
        created_at=utc_now_iso(),
        feature_hashes=feature_hashes or {},
        stream_hash=stable_hash_json(stream.values[:sample_units_seen]),
        command_provenance=command_provenance or {},
        software_version="0.2.0",
        claim_allowed=False,
        limitations=limitations,
    )


def certificate_to_dict(certificate: DecisionCertificate) -> dict:
    return asdict(certificate)
