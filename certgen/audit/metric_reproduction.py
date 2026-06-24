"""Metric reproduction audit for validated feature caches."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from certgen.certs.io import load_feature_array
from certgen.core.io import write_json
from certgen.features.cache_validate import validate_v3_feature_cache
from certgen.metrics.fid import frechet_distance
from certgen.metrics.cmmd import cmmd_rbf
from certgen.metrics.kid import kid_polynomial
from certgen.metrics.mmd import unbiased_mmd2


def _load_config(path: str | Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    if Path(path).suffix == ".json":
        import json

        return json.loads(text)
    import yaml

    return yaml.safe_load(text)


def run_metric_reproduction_audit(config_path: str | Path, out: str | Path, json_out: str | Path) -> dict[str, Any]:
    config = _load_config(config_path)
    metric = str(config["metric"]).lower()
    ref = config["reference_features"]
    model = config["model_features"]
    ref_validation = validate_v3_feature_cache(features_path=ref["npz"], sidecar_path=ref["sidecar"], strict_hash=False, metric=metric, allow_constant=True)
    model_validation = validate_v3_feature_cache(features_path=model["npz"], sidecar_path=model["sidecar"], strict_hash=False, metric=metric, allow_constant=True)
    warnings = ref_validation.warnings + model_validation.warnings
    errors = ref_validation.errors + model_validation.errors
    ref_sidecar = ref_validation.sidecar or {}
    model_sidecar = model_validation.sidecar or {}
    preprocessing_match = ref_sidecar.get("preprocessing") == model_sidecar.get("preprocessing")
    if not preprocessing_match:
        errors.append("preprocessing mismatch")
    ref_features = load_feature_array(ref["npz"])
    model_features = load_feature_array(model["npz"])
    sample_count = int(config.get("sample_count") or min(len(ref_features), len(model_features)))
    ref_features = ref_features[:sample_count]
    model_features = model_features[:sample_count]
    if metric in {"kid", "kid_polynomial"}:
        computed = kid_polynomial(model_features, ref_features)
        rigorous_certification_supported = False
        fid_descriptive_only = False
    elif metric in {"cmmd", "cmmd_clip_mmd"}:
        computed = cmmd_rbf(model_features, ref_features)
        rigorous_certification_supported = True
        fid_descriptive_only = False
    elif metric in {"mmd", "mmd_rbf"}:
        computed = unbiased_mmd2(model_features, ref_features, kernel="rbf")
        rigorous_certification_supported = True
        fid_descriptive_only = False
    elif metric.startswith("fid") or metric.startswith("fd"):
        computed = frechet_distance(model_features, ref_features)
        rigorous_certification_supported = False
        fid_descriptive_only = True
    else:
        raise ValueError(f"unsupported metric: {metric}")
    expected = config.get("expected") or {"source": "none"}
    expected_value = expected.get("value")
    within_tolerance = None
    reproduction_status = "not_applicable_no_expected_value"
    if expected.get("source") != "none" and expected_value is not None:
        tolerance_abs = float(expected.get("tolerance_abs", 0.0))
        tolerance_rel = float(expected.get("tolerance_rel", 0.0))
        diff = abs(float(computed) - float(expected_value))
        allowed = max(tolerance_abs, tolerance_rel * abs(float(expected_value)))
        within_tolerance = diff <= allowed
        reproduction_status = "within_tolerance" if within_tolerance else "outside_tolerance"
        if not within_tolerance:
            warnings.append("computed metric outside expected tolerance")
    else:
        warnings.append("no published reproduction claim possible")
    payload = {
        "audit_name": "metric_reproduction",
        "metric": metric,
        "computed_value": float(computed),
        "expected_value": expected_value,
        "within_tolerance": within_tolerance,
        "reproduction_status": reproduction_status,
        "preprocessing_match": preprocessing_match,
        "feature_caches_validated": ref_validation.passed and model_validation.passed,
        "rigorous_certification_supported": rigorous_certification_supported,
        "fid_descriptive_only": fid_descriptive_only,
        "errors": errors,
        "warnings": warnings,
        "evidence_status": "real_features_validated" if not errors else "real_features_unvalidated",
        "claim_allowed": False,
    }
    lines = ["# Metric Reproduction Audit", "", "`NO_REAL_EVIDENCE`", "", f"- Metric: `{metric}`", f"- Computed value: `{payload['computed_value']}`", f"- Reproduction status: `{reproduction_status}`", f"- Evidence status: `{payload['evidence_status']}`", "- Claim allowed: `False`", "", "## Errors"]
    lines.extend(f"- {e}" for e in errors or ["none"])
    lines.append("")
    lines.append("## Warnings")
    lines.extend(f"- {w}" for w in warnings or ["none"])
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(payload, json_out)
    return payload
