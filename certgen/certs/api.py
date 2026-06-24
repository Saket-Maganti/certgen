"""High-level V2 clean metric certificate API."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from certgen.certs.clean_core import make_clean_metric_certificate
from certgen.certs.io import feature_hashes, load_feature_array
from certgen.core.enums import EvidenceStatus, NON_EVIDENCE_STATUSES
from certgen.core.io import write_json
from certgen.core.provenance import build_provenance
from certgen.metrics.streams import mmd_difference_stream
from certgen.stats.design_contracts import CSConfig


METRIC_TO_KERNEL = {
    "cmmd_clip_mmd": {"name": "rbf", "gamma": None, "normalize": "l2"},
    "mmd_rbf": {"name": "rbf", "gamma": None, "normalize": "l2"},
}
DESCRIPTIVE_ONLY_METRICS = {"kid_polynomial", "kid", "kid_poly", "cmmd_poly", "mmd_poly"}
REPRODUCTION_REQUIRED_STATUSES = {
    EvidenceStatus.REAL_FEATURES_VALIDATED.value,
    EvidenceStatus.REAL_PILOT_NON_CLAIM.value,
    EvidenceStatus.REAL_PILOT_CLAIM_BLOCKED.value,
    EvidenceStatus.ELIGIBLE_AFTER_REAL_RUN.value,
}


def _normalise_kernel(metric_label: str, kernel_config: dict[str, Any] | None) -> dict[str, Any]:
    if metric_label in DESCRIPTIVE_ONLY_METRICS:
        raise ValueError("polynomial KID/CMMD/MMD is descriptive-only and blocked from rigorous certificate mode by default")
    if kernel_config:
        kernel = dict(kernel_config)
        if (kernel.get("name") or kernel.get("kernel")) in {"polynomial", "poly", "kid_polynomial"}:
            raise ValueError("polynomial kernels are not certified by default; use mmd_rbf or cmmd_clip_mmd")
        kernel.setdefault("normalize", "l2")
        return kernel
    if metric_label not in METRIC_TO_KERNEL:
        raise ValueError(f"unsupported clean metric label: {metric_label}")
    return dict(METRIC_TO_KERNEL[metric_label])


def _require_metric_reproduction_gate(evidence_status: str, cs_config: dict[str, Any]) -> None:
    if evidence_status not in REPRODUCTION_REQUIRED_STATUSES:
        return
    audit_path = cs_config.get("metric_reproduction_audit")
    if not audit_path:
        raise ValueError("real-pilot certificate runs require metric_reproduction_audit with within_tolerance=true")
    audit = Path(str(audit_path))
    if not audit.exists():
        raise ValueError(f"metric reproduction audit missing: {audit}")
    from certgen.core.io import read_json

    payload = read_json(audit)
    if payload.get("within_tolerance") is not True:
        raise ValueError("metric reproduction gate failed: within_tolerance is not true")
    if payload.get("claim_allowed") is True:
        raise ValueError("metric reproduction audit cannot set claim_allowed=true before certificate run")


def certify_clean_metric_comparison(
    features_a_path: str,
    features_b_path: str,
    features_r_path: str,
    metric_label: str,
    kernel_config: dict,
    cs_config: dict,
    comparison_id: str,
    evidence_status: str,
    out_path: str,
) -> Any:
    if evidence_status in {"real_evidence", EvidenceStatus.REAL_EVIDENCE_CANDIDATE.value}:
        raise ValueError("V2 refuses real evidence status until registry/provenance gates exist and pass")
    if evidence_status not in NON_EVIDENCE_STATUSES:
        raise ValueError(f"unsupported V2 evidence status: {evidence_status}")
    _require_metric_reproduction_gate(evidence_status, cs_config)

    a = load_feature_array(features_a_path)
    b = load_feature_array(features_b_path)
    r = load_feature_array(features_r_path)
    if not (a.shape[1] == b.shape[1] == r.shape[1]):
        raise ValueError("feature dimensionality mismatch")

    seed = int(cs_config.get("seed", 0))
    budget = int(cs_config.get("budget_units", min(len(a), len(b), len(r)) // 2))
    kernel = _normalise_kernel(metric_label, kernel_config)
    stream = mmd_difference_stream(
        a,
        b,
        r,
        kernel,
        seed=seed,
        max_units=budget,
        metric_label=metric_label,
        comparison_id=comparison_id,
        evidence_status=evidence_status,
        block_size=cs_config.get("block_size"),
        require_bounded_kernel=True,
    )
    if stream.lower_bound is None or stream.upper_bound is None:
        raise ValueError("bounded kernel stream failed to declare finite bounds")

    config = CSConfig(
        alpha=float(cs_config.get("alpha", 0.05)),
        budget_units=budget,
        lower_bound=stream.lower_bound,
        upper_bound=stream.upper_bound,
        method=str(cs_config.get("method", "betting")),
        seed=seed,
    )
    provenance = build_provenance(
        command="python -m certgen.cli.certify_clean_metric",
        input_paths=[features_a_path, features_b_path, features_r_path],
        notes=["NO_REAL_EVIDENCE", "R0 bounded-kernel clean metric API"],
    )
    provenance["parameters"] = {
        "metric_label": metric_label,
        "kernel_config": kernel,
        "seed": seed,
        "method": config.method,
        "budget_units": budget,
        "block_size": cs_config.get("block_size"),
        "metric_reproduction_audit": cs_config.get("metric_reproduction_audit"),
    }
    certificate = make_clean_metric_certificate(
        stream,
        config,
        feature_hashes=feature_hashes(
            features_a_path=features_a_path,
            features_b_path=features_b_path,
            features_r_path=features_r_path,
        ),
        command_provenance=provenance,
    )
    output = asdict(certificate)
    output["claim_allowed"] = False
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    write_json(output, out_path)
    return certificate
