"""Fail-closed metric-reproduction and sanity gates for the CVPR workflow.

The functions in this module are execution machinery, not evidence.  They can
consume future validated cache-v2 artifacts, while fixture runs remain
``synthetic_validation_only`` and every output keeps ``claim_allowed=false``.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.core.io import read_json
from certgen.cvpr.analysis import validate_gate_result
from certgen.cvpr.contracts import atomic_write_json, configuration_hash
from certgen.features.cache_v2 import validate_feature_cache_v2
from certgen.metrics.mmd import unbiased_mmd2


METRIC_GATE_SCHEMA = "certgen.cvpr.metric_reproduction.v1"
SANITY_GATE_SCHEMA = "certgen.cvpr.sanity_gates.v1"
REPRODUCTION_CLASSES = {"external_target", "cross_implementation_consistency"}
SANITY_FAMILIES = {"null", "obvious_gap", "direction", "protocol"}
CONTROL_TYPES_BY_FAMILY = {
    "null": {
        "reference_split_vs_reference_split",
        "same_model_independent_samples",
        "repeated_batching",
        "repeated_shard_merge",
    },
    "obvious_gap": {
        "reference_vs_severe_corruption",
    },
    "direction": {
        "gaussian_blur_severity_ladder",
    },
    "protocol": {"identity_mismatch_rejection"},
}
REQUIRED_CONTROL_TYPES = set().union(*CONTROL_TYPES_BY_FAMILY.values())
PROTOCOL_IDENTITY_FIELDS = {
    "preprocessing_hash",
    "feature_space",
    "bandwidth",
    "reference_population_hash",
}


def _load_mapping(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    raw = json.loads(text) if source.suffix.lower() == ".json" else yaml.safe_load(text)
    if not isinstance(raw, dict):
        raise ValueError(f"configuration must be an object: {source}")
    return raw


def _require_text(payload: Mapping[str, Any], field: str, errors: list[str]) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip() or value.startswith("TBD"):
        errors.append(f"{field} must be a resolved non-empty string")
        return ""
    return value


def _cache_config(payload: Mapping[str, Any], name: str, errors: list[str]) -> dict[str, Any]:
    value = payload.get(name)
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    for field in ("features", "sidecar", "artifact_root", "array_sha256", "ordered_sample_ids_sha256"):
        field_value = value.get(field)
        if not isinstance(field_value, str) or not field_value.strip() or field_value.startswith("TBD"):
            errors.append(f"{name}.{field} must be a resolved non-empty string")
    expected_count = value.get("sample_count")
    if not isinstance(expected_count, int) or expected_count < 2:
        errors.append(f"{name}.sample_count must be an integer >= 2")
    return dict(value)


def _load_cache_arrays(config: Mapping[str, Any]) -> tuple[np.ndarray, list[str]]:
    with np.load(Path(str(config["features"])), allow_pickle=False) as loaded:
        features = np.asarray(loaded["features"])
        sample_ids = [str(value) for value in np.asarray(loaded["sample_ids"]).tolist()]
    return features, sample_ids


def _cache_identity_errors(
    *,
    name: str,
    config: Mapping[str, Any],
    validation: Mapping[str, Any],
    sidecar: Mapping[str, Any],
    features: np.ndarray,
    sample_ids: list[str],
) -> list[str]:
    errors: list[str] = []
    if not validation.get("passed"):
        errors.extend(f"{name}: {item}" for item in validation.get("errors", []))
    if config.get("array_sha256") != file_sha256(str(config["features"])):
        errors.append(f"{name}: exact array SHA-256 does not match the configuration")
    if config.get("ordered_sample_ids_sha256") != stable_hash_json(sample_ids):
        errors.append(f"{name}: exact ordered sample-ID hash does not match the configuration")
    if config.get("sample_count") != len(sample_ids) or len(sample_ids) != len(features):
        errors.append(f"{name}: exact sample count does not match cache rows")
    declared_role = config.get("role")
    if declared_role is not None and declared_role != sidecar.get("role"):
        errors.append(f"{name}: role does not match the cache sidecar")
    return errors


def _metric_gate_base(config: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": METRIC_GATE_SCHEMA,
        "gate_id": str(config.get("gate_id", "metric_reproduction")),
        "run_id": str(config.get("run_id", "unresolved")),
        "inputs": {
            "reference_cache": config.get("reference_cache"),
            "generated_cache": config.get("generated_cache"),
        },
        "configuration_hash": str(config.get("configuration_hash", "")),
        "status": "BLOCKED",
        "measured_values": {},
        "tolerances": {},
        "failure_reason": None,
        "evidence_class": str(config.get("evidence_class", "sanity_artifact")),
        "claim_allowed": False,
    }


def _run_metric_reproduction_suite(config_path: str | Path, config: Mapping[str, Any], out: str | Path) -> dict[str, Any]:
    errors: list[str] = []
    if config.get("configuration_hash") != configuration_hash(config):
        errors.append("configuration_hash mismatch")
    if config.get("claim_allowed") is not False:
        errors.append("configuration claim_allowed must be false")
    gates = config.get("gates")
    if not isinstance(gates, list) or not gates:
        errors.append("metric reproduction suite gates must be a non-empty list")
        gates = []
    source = Path(config_path)
    results: list[dict[str, Any]] = []
    result_dir = Path(out).with_suffix("").with_name(Path(out).stem + "_members")
    result_dir.mkdir(parents=True, exist_ok=True)
    for index, raw in enumerate(gates):
        if not isinstance(raw, str) or not raw.strip():
            errors.append(f"metric suite gate {index} must be a config path")
            continue
        member = Path(raw)
        if not member.is_absolute():
            candidates = [Path.cwd() / member, source.parent / member]
            member = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
        if not member.is_file():
            errors.append(f"metric suite member missing: {member}")
            continue
        member_out = result_dir / f"{index:03d}_{member.stem}.json"
        results.append(run_metric_reproduction_gate(member, member_out))
    passed = not errors and bool(results) and all(row.get("status") == "PASS" for row in results)
    payload = {
        "schema_version": "certgen.cvpr.metric_reproduction_suite_result.v1",
        "run_id": str(config.get("run_id", "unresolved")),
        "configuration_hash": str(config.get("configuration_hash", "")),
        "status": "PASS" if passed else ("BLOCKED" if errors else "FAIL"),
        "members": results,
        "summary": {
            "expected": len(gates),
            "completed": len(results),
            "passed": sum(row.get("status") == "PASS" for row in results),
            "failed": sum(row.get("status") != "PASS" for row in results),
        },
        "failure_reason": None if passed else "; ".join(errors) or "one or more metric reproduction members failed",
        "evidence_class": str(config.get("evidence_class", "sanity_artifact")),
        "claim_allowed": False,
    }
    atomic_write_json(payload, out)
    return payload


def run_metric_reproduction_gate(config_path: str | Path, out: str | Path) -> dict[str, Any]:
    """Validate exact cache/metric identity and compare with a declared target."""

    config = _load_mapping(config_path)
    if config.get("schema_version") == "certgen.cvpr.metric_reproduction_suite.v1":
        return _run_metric_reproduction_suite(config_path, config, out)
    result = _metric_gate_base(config)
    errors: list[str] = []
    _require_text(config, "gate_id", errors)
    _require_text(config, "run_id", errors)
    if config.get("claim_allowed") is not False:
        errors.append("configuration claim_allowed must be false")
    if config.get("configuration_hash") != configuration_hash(config):
        errors.append("configuration_hash mismatch")
    if config.get("evidence_class") not in {"sanity_artifact", "synthetic_validation_only"}:
        errors.append("evidence_class must be sanity_artifact or synthetic_validation_only")

    reference_config = _cache_config(config, "reference_cache", errors)
    generated_config = _cache_config(config, "generated_cache", errors)
    metric = config.get("metric")
    if not isinstance(metric, dict):
        errors.append("metric must be an object")
        metric = {}
    if metric.get("name") != "unbiased_mmd2":
        errors.append("metric.name must be unbiased_mmd2 for the canonical bounded-RBF gate")
    if metric.get("convention") != "unbiased_u_statistic_full_pairwise":
        errors.append("metric.convention must be unbiased_u_statistic_full_pairwise")
    kernel = metric.get("kernel")
    if not isinstance(kernel, dict):
        errors.append("metric.kernel must be an object")
        kernel = {}
    if kernel.get("name") != "rbf" or kernel.get("normalize") != "l2":
        errors.append("metric.kernel must declare name=rbf and normalize=l2")
    try:
        gamma = float(str(kernel.get("gamma")))
        if not math.isfinite(gamma) or gamma <= 0:
            raise ValueError
    except (TypeError, ValueError):
        gamma = float("nan")
        errors.append("metric.kernel.gamma must be finite and positive")

    target = config.get("target")
    if not isinstance(target, dict):
        errors.append("target must be an object")
        target = {}
    target_class = target.get("class")
    if target_class not in REPRODUCTION_CLASSES:
        errors.append("target.class must be external_target or cross_implementation_consistency")
    _require_text(target, "provenance", errors)
    _require_text(target, "implementation_id", errors)
    try:
        target_value = float(str(target.get("value")))
        tolerance_abs = float(str(target.get("tolerance_abs")))
        tolerance_rel = float(str(target.get("tolerance_rel")))
        if not all(math.isfinite(value) for value in (target_value, tolerance_abs, tolerance_rel)):
            raise ValueError
        if tolerance_abs < 0 or tolerance_rel < 0:
            raise ValueError
    except (TypeError, ValueError):
        target_value = float("nan")
        tolerance_abs = float("nan")
        tolerance_rel = float("nan")
        errors.append("target value and nonnegative finite absolute/relative tolerances are required")

    reference_validation: dict[str, Any] = {"passed": False, "errors": ["configuration invalid"]}
    generated_validation: dict[str, Any] = {"passed": False, "errors": ["configuration invalid"]}
    reference_sidecar: dict[str, Any] = {}
    generated_sidecar: dict[str, Any] = {}
    reference_features = np.empty((0, 0))
    generated_features = np.empty((0, 0))
    reference_ids: list[str] = []
    generated_ids: list[str] = []
    caches_loaded = False
    if reference_config and generated_config and not any("must be" in error for error in errors):
        try:
            reference_validation = validate_feature_cache_v2(
                features_path=str(reference_config["features"]),
                sidecar_path=str(reference_config["sidecar"]),
                artifact_root=str(reference_config["artifact_root"]),
            )
            generated_validation = validate_feature_cache_v2(
                features_path=str(generated_config["features"]),
                sidecar_path=str(generated_config["sidecar"]),
                artifact_root=str(generated_config["artifact_root"]),
            )
            reference_sidecar = read_json(str(reference_config["sidecar"]))
            generated_sidecar = read_json(str(generated_config["sidecar"]))
            reference_features, reference_ids = _load_cache_arrays(reference_config)
            generated_features, generated_ids = _load_cache_arrays(generated_config)
            caches_loaded = True
        except (OSError, ValueError, KeyError) as exc:
            errors.append(f"cache load failed: {exc}")
    errors.extend(
        _cache_identity_errors(
            name="reference_cache",
            config=reference_config,
            validation=reference_validation,
            sidecar=reference_sidecar,
            features=reference_features,
            sample_ids=reference_ids,
        )
        if caches_loaded
        else []
    )
    errors.extend(
        _cache_identity_errors(
            name="generated_cache",
            config=generated_config,
            validation=generated_validation,
            sidecar=generated_sidecar,
            features=generated_features,
            sample_ids=generated_ids,
        )
        if caches_loaded
        else []
    )

    reference_extractor = reference_sidecar.get("extractor")
    generated_extractor = generated_sidecar.get("extractor")
    reference_preprocessing = reference_sidecar.get("preprocessing")
    generated_preprocessing = generated_sidecar.get("preprocessing")
    if reference_extractor != generated_extractor:
        errors.append("exact feature-extractor identity mismatch")
    if reference_preprocessing != generated_preprocessing:
        errors.append("exact preprocessing identity mismatch")
    if metric.get("feature_extractor_hash") != stable_hash_json(reference_extractor):
        errors.append("metric.feature_extractor_hash does not bind the validated extractor")
    if metric.get("preprocessing_hash") != stable_hash_json(reference_preprocessing):
        errors.append("metric.preprocessing_hash does not bind the validated preprocessing")
    if reference_features.ndim == 2 and generated_features.ndim == 2 and reference_features.shape[1:] != generated_features.shape[1:]:
        errors.append("feature dimensions differ")

    result["inputs"] = {
        "reference": {
            "array_sha256": reference_config.get("array_sha256"),
            "ordered_sample_ids_sha256": reference_config.get("ordered_sample_ids_sha256"),
            "sample_count": reference_config.get("sample_count"),
        },
        "generated": {
            "array_sha256": generated_config.get("array_sha256"),
            "ordered_sample_ids_sha256": generated_config.get("ordered_sample_ids_sha256"),
            "sample_count": generated_config.get("sample_count"),
        },
        "feature_extractor_hash": metric.get("feature_extractor_hash"),
        "preprocessing_hash": metric.get("preprocessing_hash"),
        "metric_convention": metric.get("convention"),
        "kernel": kernel,
        "target_provenance": target.get("provenance"),
    }
    result["tolerances"] = {"absolute": tolerance_abs, "relative": tolerance_rel}
    result["reproduction_class"] = target_class
    result["not_external_reproduction"] = target_class == "cross_implementation_consistency"
    result["cache_validations"] = {"reference": reference_validation, "generated": generated_validation}

    if errors:
        result["failure_reason"] = "; ".join(sorted(set(errors)))
    else:
        computed = unbiased_mmd2(reference_features, generated_features, kernel="rbf", normalize="l2", gamma=gamma)
        difference = abs(computed - target_value)
        allowed = max(tolerance_abs, tolerance_rel * abs(target_value))
        passed = difference <= allowed
        result["status"] = "PASS" if passed else "FAIL"
        result["measured_values"] = {
            "computed_value": computed,
            "target_value": target_value,
            "absolute_difference": difference,
            "allowed_difference": allowed,
        }
        result["failure_reason"] = None if passed else "computed value is outside the preregistered tolerance"
    schema_errors = validate_gate_result(result)
    if schema_errors:
        raise AssertionError(f"invalid metric gate result: {schema_errors}")
    atomic_write_json(result, out)
    return result


def _evaluate_sanity_gate(row: Mapping[str, Any], run_id: str, config_hash: str, evidence_class: str) -> dict[str, Any]:
    gate_id = str(row.get("gate_id", "unresolved"))
    family = str(row.get("family", ""))
    control_type = str(row.get("control_type", ""))
    measured_raw = row.get("measured_values")
    tolerances_raw = row.get("tolerances")
    inputs_raw = row.get("inputs")
    measured: dict[str, Any] = dict(measured_raw) if isinstance(measured_raw, dict) else {}
    tolerances: dict[str, Any] = dict(tolerances_raw) if isinstance(tolerances_raw, dict) else {}
    inputs: dict[str, Any] | list[Any] = inputs_raw if isinstance(inputs_raw, (dict, list)) else {}
    errors: list[str] = []
    if family not in SANITY_FAMILIES:
        errors.append(f"unsupported sanity family: {family}")
    elif control_type not in CONTROL_TYPES_BY_FAMILY[family]:
        errors.append(f"unsupported {family} control_type: {control_type}")
    passed = False
    try:
        if family == "null":
            if control_type in {"repeated_batching", "repeated_shard_merge"}:
                feature_difference = float(measured["maximum_feature_difference"])
                metric_difference = float(measured["metric_difference"])
                feature_maximum = float(tolerances["maximum_feature_difference"])
                metric_maximum = float(tolerances["metric_difference"])
                passed = all(
                    math.isfinite(value) and value >= 0
                    for value in (
                        feature_difference,
                        metric_difference,
                        feature_maximum,
                        metric_maximum,
                    )
                ) and feature_difference <= feature_maximum and metric_difference <= metric_maximum
            else:
                absolute_value = abs(float(measured["value"]))
                maximum = float(tolerances["max_absolute"])
                passed = math.isfinite(absolute_value) and math.isfinite(maximum) and maximum >= 0 and absolute_value <= maximum
        elif family == "obvious_gap":
            gap = float(measured["gap"])
            minimum = float(tolerances["minimum_gap"])
            expected_sign = int(tolerances.get("expected_sign", 1))
            passed = expected_sign in {-1, 1} and math.isfinite(gap) and math.isfinite(minimum) and minimum >= 0 and expected_sign * gap >= minimum
        elif family == "direction":
            values = [float(value) for value in measured["ordered_values"]]
            direction = str(tolerances["expected_direction"])
            minimum_step = float(tolerances.get("minimum_aggregate_step", 0.0))
            differences = np.diff(np.asarray(values, dtype=float))
            aggregate_step = float(values[-1] - values[0])
            measured = {**measured, "aggregate_step": aggregate_step, "adjacent_differences": differences.tolist()}
            minimum_points = 4 if control_type == "gaussian_blur_severity_ladder" else 2
            if direction == "increasing":
                passed = len(values) >= minimum_points and aggregate_step >= minimum_step and bool(np.all(differences >= 0))
            elif direction == "decreasing":
                passed = len(values) >= minimum_points and -aggregate_step >= minimum_step and bool(np.all(differences <= 0))
            else:
                errors.append("direction tolerance must be increasing or decreasing")
        elif family == "protocol":
            cases = inputs.get("cases") if isinstance(inputs, dict) else None
            if not isinstance(cases, list) or not cases:
                errors.append("protocol gate requires non-empty inputs.cases")
            else:
                seen: set[str] = set()
                case_results: list[dict[str, Any]] = []
                for case in cases:
                    if not isinstance(case, dict):
                        errors.append("protocol cases must be objects")
                        continue
                    field = str(case.get("mismatch_field", ""))
                    baseline_raw = case.get("baseline")
                    candidate_raw = case.get("candidate")
                    baseline = dict(baseline_raw) if isinstance(baseline_raw, dict) else {}
                    candidate = dict(candidate_raw) if isinstance(candidate_raw, dict) else {}
                    rejected = field in PROTOCOL_IDENTITY_FIELDS and baseline.get(field) != candidate.get(field)
                    seen.add(field)
                    case_results.append({"mismatch_field": field, "rejected": rejected})
                missing = sorted(PROTOCOL_IDENTITY_FIELDS - seen)
                if missing:
                    errors.append("protocol cases missing required mismatches: " + ", ".join(missing))
                measured = {**measured, "case_results": case_results}
                passed = not missing and bool(case_results) and all(item["rejected"] for item in case_results)
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        errors.append(f"invalid sanity measurement: {exc}")
    if not passed and not errors:
        errors.append("measured control is outside the preregistered tolerance")
    result = {
        "gate_id": gate_id,
        "run_id": run_id,
        "inputs": inputs,
        "configuration_hash": config_hash,
        "status": "PASS" if passed and not errors else "FAIL",
        "measured_values": measured,
        "tolerances": tolerances,
        "failure_reason": None if passed and not errors else "; ".join(errors),
        "evidence_class": evidence_class,
        "claim_allowed": False,
        "sanity_family": family,
        "control_type": control_type,
    }
    schema_errors = validate_gate_result(result)
    if schema_errors:
        raise AssertionError(f"invalid sanity gate result: {schema_errors}")
    return result


def run_sanity_controls(config_path: str | Path, out: str | Path) -> dict[str, Any]:
    """Evaluate all required config-driven control families without promotion."""

    config = _load_mapping(config_path)
    errors: list[str] = []
    run_id = _require_text(config, "run_id", errors)
    if config.get("configuration_hash") != configuration_hash(config):
        errors.append("configuration_hash mismatch")
    if config.get("claim_allowed") is not False:
        errors.append("configuration claim_allowed must be false")
    evidence_class = str(config.get("evidence_class", "sanity_artifact"))
    if evidence_class not in {"sanity_artifact", "synthetic_validation_only"}:
        errors.append("evidence_class must be sanity_artifact or synthetic_validation_only")
    rows = config.get("gates")
    if not isinstance(rows, list) or not rows:
        errors.append("gates must be a non-empty list")
        rows = []
    gates = [
        _evaluate_sanity_gate(row, run_id, str(config.get("configuration_hash", "")), evidence_class)
        for row in rows
        if isinstance(row, dict)
    ]
    present = {row["sanity_family"] for row in gates}
    missing = sorted(SANITY_FAMILIES - present)
    if missing:
        errors.append("missing required sanity families: " + ", ".join(missing))
    present_controls = {row["control_type"] for row in gates}
    missing_controls = sorted(REQUIRED_CONTROL_TYPES - present_controls)
    if missing_controls:
        errors.append("missing required sanity controls: " + ", ".join(missing_controls))
    passed = not errors and all(row["status"] == "PASS" for row in gates)
    result = {
        "schema_version": SANITY_GATE_SCHEMA,
        "run_id": run_id,
        "configuration_hash": str(config.get("configuration_hash", "")),
        "status": "PASS" if passed else ("BLOCKED" if errors else "FAIL"),
        "gates": gates,
        "summary": {
            "required_families": sorted(SANITY_FAMILIES),
            "present_families": sorted(present),
            "required_controls": sorted(REQUIRED_CONTROL_TYPES),
            "present_controls": sorted(present_controls),
            "passed": sum(row["status"] == "PASS" for row in gates),
            "failed": sum(row["status"] != "PASS" for row in gates),
        },
        "failure_reason": None if passed else "; ".join(errors) or "one or more sanity gates failed",
        "evidence_class": evidence_class,
        "synthetic_results_are_not_paper_evidence": True,
        "claim_allowed": False,
    }
    atomic_write_json(result, out)
    return result
