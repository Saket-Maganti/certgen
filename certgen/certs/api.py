"""High-level V2 clean metric certificate API."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from certgen.certs.clean_core import make_clean_metric_certificate
from certgen.certs.io import feature_hashes, load_feature_array, load_feature_sample_ids
from certgen.core.enums import EvidenceStatus, NON_EVIDENCE_STATUSES
from certgen.core.hashing import stable_hash_json
from certgen.core.io import write_json
from certgen.core.provenance import build_provenance
from certgen.metrics.streams import mmd_difference_stream
from certgen.gates.evidence_classification import enforce_declared_status
from certgen.features.cache_v2 import validate_feature_cache_v2
from certgen.stats.design_contracts import CSConfig
from certgen.stats.reference_sampling import materialize_reference_draws


METRIC_TO_KERNEL = {
    "cmmd_clip_mmd": {
        "name": "rbf",
        "gamma": 0.5,
        "normalize": "l2",
        "bandwidth_protocol": "fixed_unit_sphere_gamma_0.5_v1",
    },
    "mmd_rbf": {
        "name": "rbf",
        "gamma": 0.5,
        "normalize": "l2",
        "bandwidth_protocol": "fixed_unit_sphere_gamma_0.5_v1",
    },
}
DESCRIPTIVE_ONLY_METRICS = {"kid_polynomial", "kid", "kid_poly", "cmmd_poly", "mmd_poly"}
REPRODUCTION_REQUIRED_STATUSES = {
    EvidenceStatus.REAL_FEATURES_VALIDATED.value,
    EvidenceStatus.PILOT_ONLY.value,
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
        if kernel.get("gamma") is None:
            kernel["gamma"] = 0.5
            kernel.setdefault("bandwidth_protocol", "fixed_unit_sphere_gamma_0.5_v1")
        else:
            kernel.setdefault("bandwidth_protocol", "explicit_gamma_preregistration_not_verified")
        return kernel
    if metric_label not in METRIC_TO_KERNEL:
        raise ValueError(f"unsupported clean metric label: {metric_label}")
    return dict(METRIC_TO_KERNEL[metric_label])


def _require_metric_reproduction_gate(
    evidence_status: str,
    cs_config: dict[str, Any],
    *,
    metric_label: str,
    kernel_config: dict[str, Any],
    features_a_path: str,
    features_b_path: str,
    features_r_path: str,
    reference_draw_plan_sha256: str | None,
) -> None:
    if evidence_status not in REPRODUCTION_REQUIRED_STATUSES:
        return
    audit_path = cs_config.get("metric_reproduction_audit")
    if not audit_path:
        raise ValueError("real-pilot certificate runs require a hash-bound metric_reproduction_audit")
    audit = Path(str(audit_path))
    if not audit.exists():
        raise ValueError(f"metric reproduction audit missing: {audit}")
    from certgen.core.io import read_json

    payload = read_json(audit)
    if payload.get("within_tolerance") is not True:
        raise ValueError("metric reproduction gate failed: within_tolerance is not true")
    if payload.get("claim_allowed") is True:
        raise ValueError("metric reproduction audit cannot set claim_allowed=true before certificate run")
    if payload.get("reproduction_class") not in {"trusted_target", "independent_implementation"}:
        raise ValueError("metric reproduction gate requires trusted_target or independent_implementation agreement")
    if payload.get("metric") != metric_label:
        raise ValueError("metric reproduction audit metric does not match the certificate metric")
    if payload.get("errors") not in ([], None):
        raise ValueError("metric reproduction audit contains unresolved errors")
    specification = payload.get("metric_specification")
    specification_hash = payload.get("metric_specification_sha256")
    if not isinstance(specification, dict) or specification_hash != stable_hash_json(specification):
        raise ValueError("metric reproduction audit has a missing or invalid metric specification hash")
    if specification.get("metric_label") != metric_label or specification.get("kernel_config") != kernel_config:
        raise ValueError("metric reproduction specification does not match the certificate configuration")
    if specification.get("reference_draw_plan_sha256") != reference_draw_plan_sha256:
        raise ValueError("metric reproduction specification does not match the reference draw plan")
    expected_hashes = feature_hashes(
        features_a_path=features_a_path,
        features_b_path=features_b_path,
        features_r_path=features_r_path,
    )
    if payload.get("feature_hashes") != expected_hashes:
        raise ValueError("metric reproduction audit is not bound to the certificate feature hashes")


def _require_v2_feature_cache_contracts(
    evidence_status: str,
    *,
    features_a_path: str,
    features_b_path: str,
    features_r_path: str,
) -> None:
    if evidence_status not in REPRODUCTION_REQUIRED_STATUSES:
        return
    for role, value in {
        "model_a": features_a_path,
        "model_b": features_b_path,
        "reference": features_r_path,
    }.items():
        features = Path(value)
        migrated_sidecar = features.with_name(f"{features.stem}.certgen-v2.json")
        legacy_named_sidecar = features.with_suffix(".json")
        sidecar = migrated_sidecar if migrated_sidecar.is_file() else legacy_named_sidecar
        validation = validate_feature_cache_v2(
            features_path=features,
            sidecar_path=sidecar,
            artifact_root=features.parent,
        )
        if not validation["passed"]:
            detail = "; ".join(validation["errors"][:5])
            raise ValueError(f"{role} cache failed certgen.feature_cache.v2 validation: {detail}")


def _materialize_reference_sampling_contract(
    evidence_status: str,
    cs_config: dict[str, Any],
    *,
    features_r_path: str,
    reference_features: Any,
    min_draws: int,
) -> tuple[Any, dict[str, Any]]:
    if evidence_status not in REPRODUCTION_REQUIRED_STATUSES:
        return reference_features, {
            "sampling_scheme": "iid_rows_precommitted_assumption_unverified",
            "plan_sha256": None,
            "claim_allowed": False,
        }
    plan_path = cs_config.get("reference_draw_plan")
    if not plan_path:
        raise ValueError(
            "real-pilot certificate runs require a precommitted IID-with-replacement reference_draw_plan"
        )
    path = Path(str(plan_path))
    if not path.exists():
        raise ValueError(f"reference draw plan missing: {path}")
    from certgen.core.io import read_json

    plan = read_json(path)
    source_ids = load_feature_sample_ids(features_r_path)
    drawn, draw_ids, validation = materialize_reference_draws(
        reference_features,
        source_ids,
        plan,
        min_draws=min_draws,
    )
    return drawn, {
        "sampling_scheme": validation["sampling_scheme"],
        "plan_sha256": validation["plan_sha256"],
        "num_draws": validation["num_draws"],
        "num_unique_source_rows": validation["num_unique_source_rows"],
        "draw_ids_sha256": stable_hash_json(draw_ids),
        "claim_allowed": False,
    }


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
    enforce_declared_status(
        evidence_status,
        [features_a_path, features_b_path, features_r_path],
    )
    a = load_feature_array(features_a_path)
    b = load_feature_array(features_b_path)
    r = load_feature_array(features_r_path)
    if not (a.shape[1] == b.shape[1] == r.shape[1]):
        raise ValueError("feature dimensionality mismatch")

    seed = int(cs_config.get("seed", 0))
    block_size = int(cs_config.get("block_size") or 1)
    if block_size <= 0:
        raise ValueError("block_size must be positive")
    default_budget = min(len(a), len(b), len(r)) // (2 * block_size)
    budget = int(cs_config.get("budget_units", default_budget))
    if budget <= 0:
        raise ValueError("budget_units must be positive and feasible for the feature arrays")
    required_draws = 2 * budget * block_size
    if len(a) < required_draws or len(b) < required_draws:
        raise ValueError(
            f"budget requires at least {required_draws} rows from each model cache for block_size={block_size}"
        )
    r, reference_sampling = _materialize_reference_sampling_contract(
        evidence_status,
        cs_config,
        features_r_path=features_r_path,
        reference_features=r,
        min_draws=required_draws,
    )
    if len(r) < required_draws:
        raise ValueError(
            f"budget requires at least {required_draws} reference draws for block_size={block_size}"
        )
    _require_v2_feature_cache_contracts(
        evidence_status,
        features_a_path=features_a_path,
        features_b_path=features_b_path,
        features_r_path=features_r_path,
    )
    kernel = _normalise_kernel(metric_label, kernel_config)
    _require_metric_reproduction_gate(
        evidence_status,
        cs_config,
        metric_label=metric_label,
        kernel_config=kernel,
        features_a_path=features_a_path,
        features_b_path=features_b_path,
        features_r_path=features_r_path,
        reference_draw_plan_sha256=reference_sampling.get("plan_sha256"),
    )
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
        block_size=block_size,
        require_bounded_kernel=True,
        reference_sampling_metadata=reference_sampling,
    )
    if len(stream.values) != budget:
        raise ValueError(f"requested {budget} stream units but constructed {len(stream.values)}")
    if stream.lower_bound is None or stream.upper_bound is None:
        raise ValueError("bounded kernel stream failed to declare finite bounds")

    config = CSConfig(
        alpha=float(cs_config.get("alpha", 0.05)),
        budget_units=budget,
        lower_bound=stream.lower_bound,
        upper_bound=stream.upper_bound,
        method=str(cs_config.get("method", "hoeffding")),
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
        "block_size": block_size,
        "metric_reproduction_audit": cs_config.get("metric_reproduction_audit"),
        "reference_draw_plan": cs_config.get("reference_draw_plan"),
        "reference_draw_plan_sha256": reference_sampling.get("plan_sha256"),
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
