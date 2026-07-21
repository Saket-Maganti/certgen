"""Frozen post-cache metric and sanity gate configuration builders.

These builders consume validated cache-v2 artifacts and frozen study/family
metadata.  They do not create empirical claims; they only prepare and execute
fail-closed implementation and control checks before any certificate may run.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.contracts import configuration_hash
from certgen.cvpr.registries import validate_family_record
from certgen.cvpr.study import require_frozen_study
from certgen.features.cache_v2 import validate_feature_cache_v2
from certgen.packaging.artifact_registry import append_artifact_entry, build_artifact_entry


CONTROL_MODELS = {
    "reference_split_a",
    "reference_split_b",
    "reference_clean",
    "reference_mild_corruption",
    "reference_moderate_corruption",
    "reference_severe_corruption",
}


def _json(path: Path) -> dict[str, Any]:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _family(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if source.is_dir():
        source = source / "family.json"
    payload = _json(source)
    verdict = validate_family_record(payload, require_frozen=True)
    if not verdict["passed"]:
        raise ValueError("family invalid: " + "; ".join(verdict["errors"]))
    return payload


def _role(model_id: str) -> str:
    if model_id == "reference":
        return "reference"
    if model_id in CONTROL_MODELS:
        return f"control__{model_id}"
    return f"model__{model_id}"


def _cache(feature_root: Path, feature_space: str, role_id: str) -> tuple[Path, Path, dict[str, Any], np.ndarray, list[str]]:
    group = feature_root / feature_space / role_id
    features_path = group / "features.npz"
    sidecar_path = group / "sidecar.json"
    verdict = validate_feature_cache_v2(
        features_path=features_path,
        sidecar_path=sidecar_path,
        artifact_root=feature_root,
    )
    if not verdict["passed"]:
        raise ValueError(
            f"cache-v2 role {feature_space}/{role_id} invalid: " + "; ".join(verdict["errors"])
        )
    sidecar = _json(sidecar_path)
    with np.load(features_path, allow_pickle=False) as loaded:
        matrix = np.asarray(loaded["features"], dtype=np.float64)
        sample_ids = [str(value) for value in np.asarray(loaded["sample_ids"]).tolist()]
    if matrix.ndim != 2 or len(matrix) != len(sample_ids) or len(sample_ids) < 2:
        raise ValueError(f"cache-v2 role {feature_space}/{role_id} has invalid rows")
    return features_path, sidecar_path, sidecar, matrix, sample_ids


def _normalise(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if np.any(norms <= 0) or not np.all(np.isfinite(norms)):
        raise ValueError("feature cache contains a zero or nonfinite vector")
    return matrix / norms


def _independent_unbiased_rbf_mmd(x: np.ndarray, y: np.ndarray, gamma: float) -> float:
    if len(x) < 2 or len(y) < 2:
        raise ValueError("unbiased MMD requires at least two rows per sample")
    x = _normalise(np.asarray(x, dtype=np.float64))
    y = _normalise(np.asarray(y, dtype=np.float64))

    def kernel(left: np.ndarray, right: np.ndarray) -> np.ndarray:
        squared = np.sum((left[:, None, :] - right[None, :, :]) ** 2, axis=2)
        return np.exp(-gamma * squared)

    kxx = kernel(x, x)
    kyy = kernel(y, y)
    kxy = kernel(x, y)
    return float(
        (kxx.sum() - np.trace(kxx)) / (len(x) * (len(x) - 1))
        + (kyy.sum() - np.trace(kyy)) / (len(y) * (len(y) - 1))
        - 2.0 * kxy.mean()
    )


def _cache_config(
    features_path: Path,
    sidecar_path: Path,
    sidecar: Mapping[str, Any],
    sample_ids: list[str],
) -> dict[str, Any]:
    return {
        "features": str(features_path.resolve()),
        "sidecar": str(sidecar_path.resolve()),
        "artifact_root": str(features_path.parents[2].resolve()),
        "array_sha256": file_sha256(features_path),
        "ordered_sample_ids_sha256": stable_hash_json(sample_ids),
        "sample_count": len(sample_ids),
        "role": sidecar.get("role"),
    }


def _first_model_id(family: Mapping[str, Any]) -> str:
    for hypothesis in family.get("hypotheses", []):
        if not isinstance(hypothesis, Mapping):
            continue
        for field in ("model_a", "model_b"):
            model_id = str(hypothesis.get(field, ""))
            if model_id and model_id != "reference" and model_id not in CONTROL_MODELS:
                return model_id
    raise ValueError("frozen family contains no generated-model role for metric reproduction")


def _write_yaml(payload: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(dict(payload), sort_keys=False)
    if path.exists():
        current = yaml.safe_load(path.read_text(encoding="utf-8"))
        if current == dict(payload):
            return
        raise FileExistsError(f"refusing to overwrite non-identical frozen gate config: {path}")
    path.write_text(text, encoding="utf-8")


def prepare_post_cache_gates(
    *,
    study_path: str | Path,
    family_path: str | Path,
    feature_run: str | Path,
    metric_out: str | Path = "configs/cvpr/frozen_metric_reproduction.yaml",
    sanity_out: str | Path = "configs/cvpr/frozen_sanity.yaml",
    registry_path: str | Path = "data/artifact_registry.jsonl",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Freeze executable metric-reproduction and sanity configurations."""

    study = require_frozen_study(study_path)
    family = _family(family_path)
    if family.get("study_hash") != study.get("configuration_hash"):
        raise ValueError("family and study hashes differ")
    feature_root = Path(feature_run).resolve()
    if not feature_root.is_dir():
        raise FileNotFoundError(f"merged feature run missing: {feature_root}")
    feature_spaces = [str(value) for value in family.get("feature_spaces", [])]
    if not feature_spaces:
        raise ValueError("frozen family has no feature spaces")
    gamma = float((study.get("kernel") or {}).get("gamma", 0.5))
    if not math.isfinite(gamma) or gamma <= 0:
        raise ValueError("frozen study RBF gamma must be finite and positive")
    model_id = _first_model_id(family)

    metric_path = Path(metric_out)
    sanity_path = Path(sanity_out)
    metric_dir = metric_path.parent / "metric_reproduction_members"
    member_paths: list[str] = []
    sanity_gates: list[dict[str, Any]] = []
    thresholds = dict(study.get("sanity_thresholds") or {})
    null_max = float(thresholds.get("null_max_absolute", 0.05))
    minimum_gap = float(thresholds.get("obvious_gap_minimum", 1e-8))
    batching_feature_max = float(
        thresholds.get("repeated_batching_max_feature_difference", 1e-5)
    )
    batching_metric_max = float(
        thresholds.get("repeated_batching_max_metric_difference", 1e-7)
    )
    shard_feature_max = float(
        thresholds.get("repeated_shard_merge_max_feature_difference", 0.0)
    )
    shard_metric_max = float(
        thresholds.get("repeated_shard_merge_max_metric_difference", 0.0)
    )
    ladder_minimum = float(
        thresholds.get("corruption_ladder_minimum_aggregate_step", minimum_gap)
    )

    for feature_space in feature_spaces:
        ref = _cache(feature_root, feature_space, "reference")
        generated = _cache(feature_root, feature_space, _role(model_id))
        target_value = _independent_unbiased_rbf_mmd(ref[3], generated[3], gamma)
        member = {
            "schema_version": "certgen.cvpr.metric_reproduction_config.v1",
            "gate_id": f"metric-reproduction__{feature_space}",
            "run_id": f"{family['family_id']}__{feature_space}",
            "reference_cache": _cache_config(ref[0], ref[1], ref[2], ref[4]),
            "generated_cache": _cache_config(generated[0], generated[1], generated[2], generated[4]),
            "metric": {
                "name": "unbiased_mmd2",
                "convention": "unbiased_u_statistic_full_pairwise",
                "feature_extractor_hash": stable_hash_json(ref[2]["extractor"]),
                "preprocessing_hash": stable_hash_json(ref[2]["preprocessing"]),
                "kernel": {"name": "rbf", "normalize": "l2", "gamma": gamma},
            },
            "target": {
                "class": "cross_implementation_consistency",
                "implementation_id": "certgen.cvpr.post_cache.independent_numpy_rbf_u_statistic.v1",
                "provenance": "Frozen independent NumPy formula over the exact validated cache-v2 arrays.",
                "value": target_value,
                "tolerance_abs": 1e-7,
                "tolerance_rel": 1e-7,
            },
            "evidence_class": "sanity_artifact",
            "claim_allowed": False,
        }
        member["configuration_hash"] = configuration_hash(member)
        member_path = metric_dir / f"{feature_space}.yaml"
        member_paths.append(str(member_path.resolve()))
        if not dry_run:
            _write_yaml(member, member_path)

        null_a = _cache(feature_root, feature_space, "control__reference_split_a")
        null_b = _cache(feature_root, feature_space, "control__reference_split_b")
        clean = _cache(feature_root, feature_space, "control__reference_clean")
        mild = _cache(feature_root, feature_space, "control__reference_mild_corruption")
        moderate = _cache(
            feature_root, feature_space, "control__reference_moderate_corruption"
        )
        corrupt = _cache(feature_root, feature_space, "control__reference_severe_corruption")
        null_value = _independent_unbiased_rbf_mmd(null_a[3], null_b[3], gamma)
        gap_value = _independent_unbiased_rbf_mmd(clean[3], corrupt[3], gamma)
        ladder_values = [
            0.0,
            _independent_unbiased_rbf_mmd(clean[3], mild[3], gamma),
            _independent_unbiased_rbf_mmd(clean[3], moderate[3], gamma),
            gap_value,
        ]
        protocol_checks = generated[2].get("protocol_checks")
        if not isinstance(protocol_checks, Mapping):
            raise ValueError(
                f"merged cache lacks measured protocol checks: {feature_space}/{model_id}"
            )
        batching_reports = protocol_checks.get("repeated_batching")
        merge_report = protocol_checks.get("independent_shard_merge")
        if (
            not isinstance(batching_reports, list)
            or not batching_reports
            or not all(
                isinstance(row, Mapping) and row.get("passed") is True
                for row in batching_reports
            )
        ):
            raise ValueError(f"repeated-batching evidence is missing or failed: {feature_space}")
        if not isinstance(merge_report, Mapping) or merge_report.get("passed") is not True:
            raise ValueError(f"independent shard-merge evidence is missing or failed: {feature_space}")
        batching_max_feature = max(
            float(row["maximum_feature_difference"]) for row in batching_reports
        )
        batching_max_metric = max(float(row["metric_difference"]) for row in batching_reports)
        merge_max_feature = float(merge_report["maximum_feature_difference"])
        merge_max_metric = float(merge_report["metric_difference"])
        half = len(generated[3]) // 2
        if half < 2:
            raise ValueError(f"model cache too small for independent-sample sanity control: {feature_space}")
        same_model_value = _independent_unbiased_rbf_mmd(
            generated[3][:half], generated[3][half : 2 * half], gamma
        )
        prefix = feature_space
        sanity_gates.extend(
            [
                {"gate_id": f"{prefix}__reference_split_vs_reference_split", "family": "null", "control_type": "reference_split_vs_reference_split", "inputs": {"feature_space": feature_space}, "measured_values": {"value": null_value}, "tolerances": {"max_absolute": null_max}},
                {"gate_id": f"{prefix}__same_model_independent_samples", "family": "null", "control_type": "same_model_independent_samples", "inputs": {"feature_space": feature_space, "model_id": model_id}, "measured_values": {"value": same_model_value}, "tolerances": {"max_absolute": null_max}},
                {"gate_id": f"{prefix}__repeated_batching", "family": "null", "control_type": "repeated_batching", "inputs": {"feature_space": feature_space, "batch_reports": batching_reports}, "measured_values": {"maximum_feature_difference": batching_max_feature, "metric_difference": batching_max_metric}, "tolerances": {"maximum_feature_difference": batching_feature_max, "metric_difference": batching_metric_max}},
                {"gate_id": f"{prefix}__repeated_shard_merge", "family": "null", "control_type": "repeated_shard_merge", "inputs": {"feature_space": feature_space, "merge_report": merge_report}, "measured_values": {"maximum_feature_difference": merge_max_feature, "metric_difference": merge_max_metric}, "tolerances": {"maximum_feature_difference": shard_feature_max, "metric_difference": shard_metric_max}},
                {"gate_id": f"{prefix}__reference_vs_severe_corruption", "family": "obvious_gap", "control_type": "reference_vs_severe_corruption", "inputs": {"feature_space": feature_space}, "measured_values": {"gap": gap_value}, "tolerances": {"minimum_gap": minimum_gap, "expected_sign": 1}},
                {"gate_id": f"{prefix}__gaussian_blur_severity_ladder", "family": "direction", "control_type": "gaussian_blur_severity_ladder", "inputs": {"feature_space": feature_space, "corruption_type": "gaussian_blur", "severities": [0.0, 0.5, 1.0, 2.0]}, "measured_values": {"ordered_values": ladder_values}, "tolerances": {"expected_direction": "increasing", "minimum_aggregate_step": ladder_minimum}},
                {"gate_id": f"{prefix}__identity_mismatch_rejection", "family": "protocol", "control_type": "identity_mismatch_rejection", "inputs": {"cases": [
                    {"mismatch_field": "preprocessing_hash", "baseline": {"preprocessing_hash": stable_hash_json(ref[2]["preprocessing"])}, "candidate": {"preprocessing_hash": "intentional-mismatch"}},
                    {"mismatch_field": "feature_space", "baseline": {"feature_space": feature_space}, "candidate": {"feature_space": f"{feature_space}__mismatch"}},
                    {"mismatch_field": "bandwidth", "baseline": {"bandwidth": family["bandwidth"]}, "candidate": {"bandwidth": "intentional-mismatch"}},
                    {"mismatch_field": "reference_population_hash", "baseline": {"reference_population_hash": ref[2]["benchmark"]["source_manifest_sha256"]}, "candidate": {"reference_population_hash": "intentional-mismatch"}},
                ]}, "measured_values": {}, "tolerances": {"all_mismatches_must_be_rejected": True}},
            ]
        )

    suite = {
        "schema_version": "certgen.cvpr.metric_reproduction_suite.v1",
        "run_id": f"{family['family_id']}__metric-reproduction-suite",
        "study_hash": study["configuration_hash"],
        "family_id": family["family_id"],
        "gates": member_paths,
        "evidence_class": "sanity_artifact",
        "claim_allowed": False,
    }
    suite["configuration_hash"] = configuration_hash(suite)
    sanity = {
        "schema_version": "certgen.cvpr.sanity_gate_config.v1",
        "run_id": f"{family['family_id']}__sanity-controls",
        "study_hash": study["configuration_hash"],
        "family_id": family["family_id"],
        "gates": sanity_gates,
        "evidence_class": "sanity_artifact",
        "claim_allowed": False,
    }
    sanity["configuration_hash"] = configuration_hash(sanity)
    if not dry_run:
        _write_yaml(suite, metric_path)
        _write_yaml(sanity, sanity_path)
        for path, artifact_type in (
            (metric_path, "cvpr_metric_gate_config"),
            (sanity_path, "cvpr_sanity_gate_config"),
        ):
            append_artifact_entry(
                build_artifact_entry(
                    path=path,
                    artifact_type=artifact_type,
                    stage="post_cache_gates",
                    run_id=str(family["family_id"]),
                    source=str(feature_root),
                    validation_status="frozen_gate_configuration",
                    evidence_class="sanity_artifact",
                    notes="Frozen post-cache gate configuration; claim_allowed=false.",
                ),
                registry_path,
            )
    return {
        "status": "POST_CACHE_GATE_CONFIGS_READY",
        "metric_config": str(metric_path),
        "sanity_config": str(sanity_path),
        "metric_members": member_paths,
        "feature_spaces": feature_spaces,
        "dry_run": dry_run,
        "claim_allowed": False,
    }
