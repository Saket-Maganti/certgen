"""Canonical, hash-bound feature-cache contract for claim-bearing pilot inputs.

Legacy cache readers remain available for smoke fixtures.  A real-like
certificate must use this schema so row identity, extractor identity,
preprocessing, and immutable array content cannot be inferred from aliases.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.core.io import read_json, write_json


SCHEMA_VERSION = "certgen.feature_cache.v2"
ALLOWED_ROLES = {"reference", "model_a", "model_b", "generated", "model"}
REQUIRED_PREPROCESSING = {
    "resize",
    "interpolation",
    "crop",
    "color_mode",
    "pixel_range",
    "normalization",
    "feature_normalization",
}


def _object(payload: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key.upper()}_MISSING: {key} must be an object")
        return {}
    return value


def _resolve_portable(root: Path, value: Any, field: str, errors: list[str]) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field.upper().replace('.', '_')}_MISSING: portable path is required")
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        errors.append(f"{field.upper().replace('.', '_')}_UNSAFE: path must be relative to artifact root")
        return None
    candidate = (root / path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{field.upper().replace('.', '_')}_UNSAFE: path escapes artifact root")
        return None
    return candidate


def _manifest_ids(path: Path, role: str) -> tuple[list[str], list[str]]:
    ids: list[str] = []
    errors: list[str] = []
    try:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row_role = str(row.get("role", ""))
            if row_role and row_role not in {role, "reference" if role == "reference" else role}:
                continue
            sample_id = str(row.get("sample_id", ""))
            if not sample_id:
                errors.append(f"SOURCE_MANIFEST_MISMATCH: line {line_no} lacks sample_id")
            else:
                ids.append(sample_id)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"SOURCE_MANIFEST_MISMATCH: {exc}")
    return ids, errors


def validate_feature_cache_v2(
    *,
    features_path: str | Path,
    sidecar_path: str | Path,
    artifact_root: str | Path | None = None,
    require_source_manifest: bool = True,
) -> dict[str, Any]:
    """Validate content, ordered row identity, and protocol metadata fail-closed."""

    features_path = Path(features_path)
    sidecar_path = Path(sidecar_path)
    root = Path(artifact_root) if artifact_root is not None else sidecar_path.parent
    errors: list[str] = []
    warnings: list[str] = []
    if not features_path.is_file():
        errors.append(f"ARRAY_MISSING: {features_path}")
    if not sidecar_path.is_file():
        errors.append(f"SIDECAR_MISSING: {sidecar_path}")
    if errors:
        return {"passed": False, "errors": errors, "warnings": warnings, "claim_allowed": False}

    try:
        payload = read_json(sidecar_path)
    except Exception as exc:
        return {
            "passed": False,
            "errors": [f"SIDECAR_INVALID: {exc}"],
            "warnings": [],
            "claim_allowed": False,
        }
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("SCHEMA_VERSION_UNSUPPORTED: expected certgen.feature_cache.v2")
    benchmark = _object(payload, "benchmark", errors)
    producer = _object(payload, "producer", errors)
    extractor = _object(payload, "extractor", errors)
    preprocessing = _object(payload, "preprocessing", errors)
    array_meta = _object(payload, "array", errors)
    shard = _object(payload, "shard", errors)
    runtime = _object(payload, "runtime", errors)
    source = _object(payload, "source", errors)
    evidence = _object(payload, "evidence", errors)

    role = str(payload.get("role", ""))
    if role not in ALLOWED_ROLES:
        errors.append(f"ROLE_MISMATCH: unsupported role {role!r}")
    for key in ("dataset_id", "split", "source_manifest_path", "source_manifest_sha256"):
        if not benchmark.get(key):
            errors.append(f"BENCHMARK_METADATA_MISSING: benchmark.{key}")
    for key in ("model_or_generator_id", "checkpoint_or_revision"):
        if producer.get(key) in {None, "", "unknown", "TBD"}:
            errors.append(f"PRODUCER_METADATA_MISSING: producer.{key}")
    for key in ("name", "resolved_model_id", "resolved_revision", "output_layer", "feature_dim"):
        if extractor.get(key) in {None, "", "unknown", "TBD"}:
            errors.append(f"EXTRACTOR_METADATA_MISSING: extractor.{key}")
    missing_preprocessing = sorted(REQUIRED_PREPROCESSING - set(preprocessing))
    if missing_preprocessing:
        errors.append("PREPROCESSING_MISMATCH: missing " + ", ".join(missing_preprocessing))
    if preprocessing.get("color_mode") != "rgb":
        errors.append("PREPROCESSING_MISMATCH: color_mode must be rgb")
    if evidence.get("claim_allowed") is not False:
        errors.append("EVIDENCE_BOUNDARY_INVALID: evidence.claim_allowed must be false")
    if not str(evidence.get("status", "")):
        errors.append("EVIDENCE_BOUNDARY_INVALID: evidence.status is required")
    if source.get("license_status") in {None, "", "unknown", "restricted", "not_allowed"}:
        errors.append("LICENSE_BLOCKED: explicit usable license_status is required")
    for key in ("shard_id", "num_shards", "selection_policy", "input_shard_manifest_sha256"):
        if shard.get(key) in {None, "", "unknown", "TBD"}:
            errors.append(f"SHARD_METADATA_MISSING: shard.{key}")
    for key in ("device", "precision", "batch_size", "determinism_policy", "created_by", "created_at", "certgen_version"):
        if runtime.get(key) in {None, "", "unknown", "TBD"}:
            errors.append(f"RUNTIME_METADATA_MISSING: runtime.{key}")

    declared_array = _resolve_portable(root, array_meta.get("path"), "array.path", errors)
    if declared_array is not None and declared_array != features_path.resolve():
        errors.append("ARRAY_PATH_MISMATCH: sidecar path does not identify the validated NPZ")
    try:
        with np.load(features_path, allow_pickle=False) as loaded:
            if "features" not in loaded:
                errors.append("ARRAY_SCHEMA_INVALID: features key is missing")
                features = np.empty((0, 0), dtype=float)
            else:
                features = np.asarray(loaded["features"])
            if "sample_ids" not in loaded:
                errors.append("SAMPLE_IDS_MISSING: sample_ids key is required")
                ids: list[str] = []
            else:
                raw_ids = np.asarray(loaded["sample_ids"])
                if raw_ids.ndim != 1:
                    errors.append("SAMPLE_IDS_MISSING: sample_ids must be one-dimensional")
                    ids = []
                else:
                    ids = [str(value) for value in raw_ids.tolist()]
    except (OSError, ValueError) as exc:
        errors.append(f"ARRAY_SCHEMA_INVALID: {exc}")
        features = np.empty((0, 0), dtype=float)
        ids = []
    if features.ndim != 2 or not features.size:
        errors.append(f"EMPTY_CACHE: expected a non-empty 2D array, found {features.shape}")
    elif not np.issubdtype(features.dtype, np.floating):
        errors.append("ARRAY_DTYPE_INVALID: features must use a floating dtype")
    elif not np.all(np.isfinite(features)):
        errors.append("NONFINITE_FEATURES: feature array contains NaN or Inf")
    elif float(np.std(features)) < 1e-12:
        errors.append("EMPTY_CACHE: constant or near-constant features are not pilot-capable")
    if any(not value for value in ids):
        errors.append("SAMPLE_IDS_MISSING: sample IDs must be non-empty")
    if len(ids) != len(set(ids)):
        errors.append("SAMPLE_IDS_DUPLICATED: sample IDs must be unique")
    if features.ndim == 2 and len(ids) != features.shape[0]:
        errors.append("SAMPLE_IDS_REORDERED: sample-ID count does not match feature rows")
    expected_shape = [int(value) for value in features.shape] if features.ndim == 2 else []
    if array_meta.get("shape") != expected_shape:
        errors.append("FEATURE_DIM_MISMATCH: array.shape does not match NPZ")
    if array_meta.get("dtype") != str(features.dtype):
        errors.append("ARRAY_DTYPE_INVALID: array.dtype does not match NPZ")
    if extractor.get("feature_dim") != (expected_shape[1] if len(expected_shape) == 2 else None):
        errors.append("FEATURE_DIM_MISMATCH: extractor.feature_dim does not match NPZ")
    if array_meta.get("sha256") != file_sha256(features_path):
        errors.append("ARRAY_HASH_MISMATCH: NPZ SHA-256 differs from sidecar")
    if array_meta.get("ordered_sample_ids_sha256") != stable_hash_json(ids):
        errors.append("SAMPLE_IDS_REORDERED: ordered sample-ID hash differs")

    manifest_path = _resolve_portable(root, benchmark.get("source_manifest_path"), "benchmark.source_manifest_path", errors)
    if manifest_path is not None:
        if not manifest_path.is_file():
            message = f"SOURCE_MANIFEST_MISMATCH: manifest missing: {manifest_path}"
            (errors if require_source_manifest else warnings).append(message)
        else:
            if benchmark.get("source_manifest_sha256") != file_sha256(manifest_path):
                errors.append("SOURCE_MANIFEST_MISMATCH: manifest SHA-256 differs")
            manifest_ids, manifest_errors = _manifest_ids(manifest_path, role)
            errors.extend(manifest_errors)
            if manifest_ids != ids:
                errors.append("SOURCE_MANIFEST_MISMATCH: role-filtered manifest IDs do not match NPZ row order")

    return {
        "passed": not errors,
        "schema_version": payload.get("schema_version"),
        "features_path": str(features_path),
        "sidecar_path": str(sidecar_path),
        "feature_shape": expected_shape,
        "ordered_sample_ids_sha256": stable_hash_json(ids),
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "evidence_status": "real_features_validated" if not errors else "real_features_unvalidated",
        "claim_allowed": False,
    }


def migrate_legacy_feature_cache(
    *,
    features_path: str | Path,
    legacy_sidecar_path: str | Path,
    out_sidecar_path: str | Path,
    artifact_root: str | Path,
    role: str,
    dataset_id: str,
    split: str,
    source_manifest_path: str,
    model_or_generator_id: str,
    checkpoint_or_revision: str,
) -> dict[str, Any]:
    """Write a new v2 sidecar without modifying legacy inputs."""

    features_path = Path(features_path)
    legacy_sidecar_path = Path(legacy_sidecar_path)
    out_sidecar_path = Path(out_sidecar_path)
    root = Path(artifact_root).resolve()
    if out_sidecar_path.exists():
        raise FileExistsError(f"refusing to overwrite migrated sidecar: {out_sidecar_path}")
    legacy = read_json(legacy_sidecar_path)
    with np.load(features_path, allow_pickle=False) as loaded:
        if "features" not in loaded or "sample_ids" not in loaded:
            raise ValueError("legacy cache migration requires features and sample_ids arrays")
        features = np.asarray(loaded["features"])
        ids = [str(value) for value in np.asarray(loaded["sample_ids"]).tolist()]
    if features.ndim != 2 or len(ids) != features.shape[0] or len(ids) != len(set(ids)):
        raise ValueError("legacy cache has invalid shape or sample IDs")
    try:
        array_rel = features_path.resolve().relative_to(root).as_posix()
        manifest_abs = (root / source_manifest_path).resolve()
        manifest_abs.relative_to(root)
    except ValueError as exc:
        raise ValueError("features and source manifest must be portable paths below artifact_root") from exc
    preprocessing = dict(legacy.get("preprocessing") or {})
    preprocessing.setdefault("crop", preprocessing.get("crop_policy", "none"))
    preprocessing.setdefault("color_mode", "rgb")
    preprocessing.setdefault("pixel_range", "unresolved")
    preprocessing.setdefault("feature_normalization", "none")
    blockers: list[str] = []
    for field in sorted(REQUIRED_PREPROCESSING):
        if preprocessing.get(field) in {None, "", "unknown", "TBD", "unresolved"}:
            blockers.append(f"preprocessing.{field}")
    resolved_model = legacy.get("resolved_model_id") or legacy.get("model_id") or legacy.get("weights_id")
    resolved_revision = legacy.get("resolved_revision") or legacy.get("model_revision")
    if not resolved_model:
        blockers.append("extractor.resolved_model_id")
    if not resolved_revision:
        blockers.append("extractor.resolved_revision")
    manifest_hash = file_sha256(manifest_abs) if manifest_abs.is_file() else None
    if manifest_hash is None:
        blockers.append("benchmark.source_manifest_sha256")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "cache_id": stable_hash_json({"array": file_sha256(features_path), "role": role})[:24],
        "role": role,
        "benchmark": {
            "dataset_id": dataset_id,
            "split": split,
            "source_manifest_path": source_manifest_path,
            "source_manifest_sha256": manifest_hash,
        },
        "producer": {
            "model_or_generator_id": model_or_generator_id,
            "checkpoint_or_revision": checkpoint_or_revision,
            "checkpoint_sha256": legacy.get("checkpoint_sha256"),
        },
        "extractor": {
            "name": legacy.get("extractor") or legacy.get("feature_extractor") or legacy.get("feature_type"),
            "resolved_model_id": resolved_model,
            "resolved_revision": resolved_revision,
            "checkpoint_sha256": legacy.get("extractor_checkpoint_sha256"),
            "package_versions": legacy.get("dependency_versions", {}),
            "output_layer": legacy.get("output_layer") or "unresolved",
            "feature_dim": int(features.shape[1]),
        },
        "preprocessing": preprocessing,
        "array": {
            "path": array_rel,
            "sha256": file_sha256(features_path),
            "dtype": str(features.dtype),
            "shape": [int(value) for value in features.shape],
            "features_key": "features",
            "sample_ids_key": "sample_ids",
            "ordered_sample_ids_sha256": stable_hash_json(ids),
        },
        "shard": {
            "shard_id": legacy.get("shard_id", 0),
            "num_shards": legacy.get("num_shards", 1),
            "selection_policy": legacy.get("selection_policy") or "legacy_order_preserved",
            "input_shard_manifest_sha256": legacy.get("input_shard_manifest_sha256")
            or legacy.get("source_manifest_sha256")
            or manifest_hash,
        },
        "runtime": {
            "device": legacy.get("device") or "unresolved",
            "precision": legacy.get("precision") or str(features.dtype),
            "batch_size": legacy.get("batch_size") or "unresolved",
            "determinism_policy": legacy.get("determinism_policy") or "unresolved",
            "created_by": "certgen.features.cache_v2.migrate_legacy_feature_cache",
            "created_at": legacy.get("created_at") or "unresolved",
            "certgen_version": legacy.get("certgen_version") or "0.5.0",
        },
        "source": {
            "license_status": (legacy.get("source") or {}).get("license_status") or "unknown",
            "provenance_ledger_sha256": legacy.get("provenance_ledger_sha256"),
        },
        "evidence": {"status": "real_features_unvalidated", "claim_allowed": False},
        "migration": {
            "legacy_sidecar_sha256": file_sha256(legacy_sidecar_path),
            "legacy_sidecar_path": str(legacy_sidecar_path),
            "converter": "certgen.feature_cache.v2.migrator.v1",
            "unresolved_fields": sorted(set(blockers)),
            "automatic_evidence_promotion": False,
        },
    }
    write_json(payload, out_sidecar_path)
    result = validate_feature_cache_v2(
        features_path=features_path,
        sidecar_path=out_sidecar_path,
        artifact_root=root,
    )
    result["migration_blockers"] = sorted(set(blockers))
    result["out_sidecar_path"] = str(out_sidecar_path)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate or migrate a CertGen feature cache.")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--features", required=True)
    validate.add_argument("--sidecar", required=True)
    validate.add_argument("--artifact-root")
    migrate = sub.add_parser("migrate")
    migrate.add_argument("--features", required=True)
    migrate.add_argument("--legacy-sidecar", required=True)
    migrate.add_argument("--out-sidecar", required=True)
    migrate.add_argument("--artifact-root", required=True)
    migrate.add_argument("--role", required=True, choices=sorted(ALLOWED_ROLES))
    migrate.add_argument("--dataset-id", required=True)
    migrate.add_argument("--split", required=True)
    migrate.add_argument("--source-manifest", required=True)
    migrate.add_argument("--model-id", required=True)
    migrate.add_argument("--checkpoint", required=True)
    args = parser.parse_args(argv)
    if args.command == "validate":
        result = validate_feature_cache_v2(
            features_path=args.features,
            sidecar_path=args.sidecar,
            artifact_root=args.artifact_root,
        )
    else:
        result = migrate_legacy_feature_cache(
            features_path=args.features,
            legacy_sidecar_path=args.legacy_sidecar,
            out_sidecar_path=args.out_sidecar,
            artifact_root=args.artifact_root,
            role=args.role,
            dataset_id=args.dataset_id,
            split=args.split,
            source_manifest_path=args.source_manifest,
            model_or_generator_id=args.model_id,
            checkpoint_or_revision=args.checkpoint,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
