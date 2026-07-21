"""Fail-closed validators for the prospective CVPR registries."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import stable_hash_json
from certgen.cvpr.contracts import atomic_write_json, configuration_hash


BENCHMARK_FIELDS = {
    "benchmark_id", "display_name", "domain", "resolution", "conditioning", "reference_source",
    "reference_split", "license", "expected_reference_count", "download_size_estimate",
    "official_url_placeholder", "local_source_formats", "feature_spaces_supported",
    "evaluation_protocols", "known_preprocessing_risks", "cvpr_relevance", "execution_tier", "status", "blocker",
}
MODEL_FIELDS = {
    "model_id", "display_name", "family", "benchmark_id", "task", "architecture",
    "checkpoint_or_sample_source", "revision", "license", "authentication_required",
    "released_samples_available", "checkpoint_available", "sample_count_available", "resolution",
    "conditioning", "generation_cost_estimate", "feature_only_possible", "adapter", "preflight_required",
    "status", "blocker", "cvpr_recognition", "asset_policy", "asset_manifest_required",
    "online_preflight_supported", "offline_cache_supported", "expected_cache_size",
}
FEATURE_FIELDS = {
    "feature_space_id", "model_identifier", "revision", "package", "expected_dimension", "input_resolution",
    "resize", "crop", "interpolation", "pixel_range", "normalization", "feature_normalization", "precision",
    "batch_size_default", "device_support", "license", "cache_schema_version", "status",
    "asset_policy", "asset_manifest_required", "online_preflight_supported", "offline_cache_supported",
    "expected_cache_size",
}
CAPABILITY_FIELDS = {
    "adapter_id", "model_ids", "supports_batching", "supports_generator_list", "supports_class_conditioning",
    "supports_prompt_batching", "supports_scheduler_override", "supports_mixed_precision", "supports_resume",
    "known_memory_risk", "status",
}
COMPARISON_FIELDS = {
    "comparison_id", "benchmark_id", "model_a", "model_b", "comparison_type", "source_of_pair",
    "prospective_or_posthoc", "primary_or_secondary", "expected_gap_class", "feature_spaces", "metrics",
    "sample_budgets", "family_id", "status", "blocker",
}
PUBLISHED_CLAIM_FIELDS = {
    "claim_id", "paper_title", "paper_year", "venue", "paper_url_or_identifier", "benchmark", "model_a",
    "model_b", "reported_metric", "reported_a", "reported_b", "sample_count", "feature_extractor",
    "preprocessing", "released_samples_available", "checkpoint_available", "license", "reproduction_possible",
    "selection_reason", "prospective_status", "notes",
}
PREREG_FIELDS = {
    "study_id", "version", "primary_question", "primary_outcomes", "secondary_outcomes", "benchmarks", "models",
    "model_pairs", "feature_spaces", "metrics", "kernel", "bandwidth_protocol", "alpha", "multiplicity_families",
    "sample_budgets", "stopping_rule", "reference_draw_protocol", "exclusion_rules", "failure_rules", "resume_rules",
    "missing_data_rules", "censoring_rules", "claim_thresholds", "scale_up_rules", "pivot_rules", "configuration_hash", "frozen",
}


def _load_yaml(path: str | Path) -> Any:
    with Path(path).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _items(payload: Any, key: str) -> list[dict[str, Any]]:
    rows = payload.get(key) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError(f"registry must contain a list under {key!r}")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"all {key} rows must be mappings")
    return rows


def _validate_rows(rows: list[dict[str, Any]], required: set[str], identity: str) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=1):
        missing = sorted(required - set(row))
        if missing:
            errors.append(f"row {index} missing fields: {', '.join(missing)}")
        value = str(row.get(identity, "")).strip()
        if not value:
            errors.append(f"row {index} has empty {identity}")
        elif value in seen:
            errors.append(f"duplicate {identity}: {value}")
        seen.add(value)
        if row.get("claim_allowed") is True:
            errors.append(f"row {index} illegally sets claim_allowed=true")
        if str(row.get("status", "")).lower() in {"ready", "verified", "available"}:
            if str(row.get("license", "")).lower() in {"", "unknown", "unverified", "tbd"}:
                errors.append(f"row {index} cannot be ready with an unverified license")
    return errors


def validate_yaml_registry(path: str | Path, *, key: str, required: set[str], identity: str) -> dict[str, Any]:
    try:
        rows = _items(_load_yaml(path), key)
    except (OSError, yaml.YAMLError, ValueError) as exc:
        return {"passed": False, "path": str(path), "rows": 0, "errors": [str(exc)], "claim_allowed": False}
    errors = _validate_rows(rows, required, identity)
    return {"passed": not errors, "path": str(path), "rows": len(rows), "errors": errors, "claim_allowed": False}


def validate_csv_registry(path: str | Path, *, required: set[str], identity: str, allow_empty: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    try:
        with Path(path).open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            missing = sorted(required - fields)
            if missing:
                errors.append("missing columns: " + ", ".join(missing))
            rows = list(reader)
    except OSError as exc:
        errors.append(str(exc))
    if not rows and not allow_empty:
        errors.append("registry has no rows")
    errors.extend(_validate_rows(rows, required, identity))
    return {"passed": not errors, "path": str(path), "rows": len(rows), "errors": errors, "claim_allowed": False}


def validate_preregistration(path: str | Path, *, require_frozen: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    try:
        payload = _load_yaml(path)
    except (OSError, yaml.YAMLError) as exc:
        payload = {}
        errors.append(str(exc))
    if not isinstance(payload, dict):
        payload = {}
        errors.append("preregistration must be a mapping")
    missing = sorted(PREREG_FIELDS - set(payload))
    if missing:
        errors.append("missing fields: " + ", ".join(missing))
    if payload.get("claim_allowed") is not False:
        errors.append("pre-execution preregistration must explicitly set claim_allowed=false")
    frozen = payload.get("frozen") is True
    if require_frozen and not frozen:
        errors.append("preregistration must be frozen before claim-bearing analysis")
    expected_hash = configuration_hash(payload)
    declared_hash = payload.get("configuration_hash")
    if frozen and declared_hash != expected_hash:
        errors.append("frozen preregistration configuration_hash mismatch")
    def placeholder_paths(value: Any, prefix: str = "") -> list[str]:
        if isinstance(value, dict):
            return [item for key, child in value.items() if key != "configuration_hash" for item in placeholder_paths(child, f"{prefix}.{key}" if prefix else str(key))]
        if isinstance(value, list):
            return [item for index, child in enumerate(value) for item in placeholder_paths(child, f"{prefix}[{index}]")]
        return [prefix] if isinstance(value, str) and ("TBD" in value or "<" in value or ">" in value) else []
    if frozen:
        placeholders = placeholder_paths(payload)
        if placeholders:
            errors.append("frozen preregistration contains unresolved placeholders: " + ", ".join(placeholders[:20]))
    for name in ("benchmarks", "models", "model_pairs", "feature_spaces", "metrics", "sample_budgets", "multiplicity_families"):
        value = payload.get(name)
        if not isinstance(value, list) or not value:
            errors.append(f"{name} must be a non-empty prospective list")
    alpha = payload.get("alpha")
    if not isinstance(alpha, (float, int)) or isinstance(alpha, bool) or not 0.0 < float(alpha) < 1.0:
        errors.append("alpha must be in (0,1)")
    budgets = payload.get("sample_budgets")
    if isinstance(budgets, list) and (any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in budgets) or len(budgets) != len(set(budgets))):
        errors.append("sample_budgets must be unique positive integers")
    pairs = payload.get("model_pairs")
    if isinstance(pairs, list):
        pair_ids = [str(row.get("comparison_id", "")) for row in pairs if isinstance(row, dict)]
        if len(pair_ids) != len(pairs) or any(not value for value in pair_ids) or len(pair_ids) != len(set(pair_ids)):
            errors.append("model_pairs must contain unique comparison_id mappings")
    return {
        "passed": not errors,
        "path": str(path),
        "frozen": frozen,
        "declared_configuration_hash": declared_hash,
        "computed_configuration_hash": expected_hash,
        "errors": sorted(set(errors)),
        "claim_allowed": False,
    }


def build_family_record(
    *, family_id: str, analysis_scope: str, benchmark: str, feature_space: str, metric: str,
    kernel: str, bandwidth: str, model_pairs: Iterable[str], alpha_total: float, status: str = "planned",
    preregistered_at: str | None = None, dimensions: Mapping[str, Iterable[Any]] | None = None,
) -> dict[str, Any]:
    pairs = sorted({str(pair) for pair in model_pairs})
    if not pairs:
        raise ValueError("multiplicity family requires at least one model pair")
    if not 0.0 < float(alpha_total) < 1.0:
        raise ValueError("alpha_total must be in (0,1)")
    dimension_values = {str(key): sorted({str(item) for item in values}) for key, values in (dimensions or {}).items()}
    multiplier = 1
    for values in dimension_values.values():
        if not values:
            raise ValueError("multiplicity dimensions must not be empty")
        multiplier *= len(values)
    number = len(pairs) * multiplier
    record: dict[str, Any] = {
        "family_id": family_id,
        "analysis_scope": analysis_scope,
        "benchmark": benchmark,
        "feature_space": feature_space,
        "metric": metric,
        "kernel": kernel,
        "bandwidth": bandwidth,
        "model_pairs": pairs,
        "dimensions": dimension_values,
        "alpha_total": float(alpha_total),
        "number_of_hypotheses": number,
        "alpha_per_hypothesis": float(alpha_total) / number,
        "status": status,
        "preregistered_at": preregistered_at,
        "claim_allowed": False,
    }
    record["configuration_hash"] = stable_hash_json(record)
    return record


def validate_family_record(record: Mapping[str, Any], *, require_frozen: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    pairs = record.get("model_pairs")
    if not isinstance(pairs, list) or not pairs or len(pairs) != len(set(map(str, pairs))):
        errors.append("model_pairs must be a non-empty unique list")
    number = record.get("number_of_hypotheses")
    alpha_total = record.get("alpha_total")
    alpha_pair = record.get("alpha_per_hypothesis")
    if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
        errors.append("number_of_hypotheses must be positive")
    if not isinstance(alpha_total, (float, int)) or isinstance(alpha_total, bool) or not 0.0 < float(alpha_total) < 1.0:
        errors.append("alpha_total must be in (0,1)")
    if not isinstance(alpha_pair, (float, int)) or isinstance(alpha_pair, bool):
        errors.append("alpha_per_hypothesis must be numeric")
    if (
        isinstance(alpha_pair, (float, int))
        and not isinstance(alpha_pair, bool)
        and isinstance(alpha_total, (float, int))
        and not isinstance(alpha_total, bool)
        and isinstance(number, int)
        and not isinstance(number, bool)
        and number > 0
        and abs(float(alpha_pair) - float(alpha_total) / number) > 1e-15
    ):
        errors.append("alpha_per_hypothesis is not the Bonferroni allocation")
    if require_frozen and record.get("status") != "frozen":
        errors.append("multiplicity family must be prospectively frozen")
    without_hash = {key: value for key, value in record.items() if key != "configuration_hash"}
    if record.get("configuration_hash") != stable_hash_json(without_hash):
        errors.append("multiplicity family configuration_hash mismatch")
    if record.get("claim_allowed") is not False:
        errors.append("family record must keep claim_allowed=false in this build")
    return {"passed": not errors, "errors": errors, "family_id": record.get("family_id"), "claim_allowed": False}


def write_frozen_family(record: Mapping[str, Any], path: str | Path) -> dict[str, Any]:
    payload = dict(record)
    payload["status"] = "frozen"
    payload["configuration_hash"] = stable_hash_json({key: value for key, value in payload.items() if key != "configuration_hash"})
    verdict = validate_family_record(payload, require_frozen=True)
    if not verdict["passed"]:
        raise ValueError("invalid family record: " + "; ".join(verdict["errors"]))
    atomic_write_json(payload, path)
    return payload


def validate_all_cvpr_registries(root: str | Path = ".") -> dict[str, Any]:
    base = Path(root)
    checks = [
        validate_yaml_registry(base / "registry/cvpr/benchmark_registry.yaml", key="benchmarks", required=BENCHMARK_FIELDS, identity="benchmark_id"),
        validate_yaml_registry(base / "registry/cvpr/model_registry.yaml", key="models", required=MODEL_FIELDS, identity="model_id"),
        validate_yaml_registry(base / "registry/cvpr/feature_space_registry.yaml", key="feature_spaces", required=FEATURE_FIELDS, identity="feature_space_id"),
        validate_yaml_registry(base / "registry/cvpr/model_adapter_capabilities.yaml", key="adapters", required=CAPABILITY_FIELDS, identity="adapter_id"),
        validate_csv_registry(base / "registry/cvpr/comparison_registry.csv", required=COMPARISON_FIELDS, identity="comparison_id"),
        validate_csv_registry(base / "registry/cvpr/published_claim_registry.csv", required=PUBLISHED_CLAIM_FIELDS, identity="claim_id", allow_empty=True),
        validate_preregistration(base / "configs/cvpr/certgen_cvpr_preregistration_template.yaml"),
    ]
    return {"passed": all(item["passed"] for item in checks), "checks": checks, "claim_allowed": False}
