"""Actual extractor provenance normalization and fail-closed expectation checks."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from certgen.icml2027.common import stable_hash


REQUIRED_ACTUAL_FIELDS = {
    "schema_version",
    "extractor_id",
    "runtime_extractor",
    "model_identifier",
    "model_revision",
    "model_class",
    "processor_identity",
    "asset_id",
    "asset_revision",
    "asset_manifest_sha256",
    "asset_inventory_sha256",
    "aggregate_manifest_sha256",
    "preprocessing_sha256",
    "preprocessing_config",
    "feature_layer",
    "dimension",
    "dtype",
    "normalization",
    "source_role",
    "source_manifest_sha256",
    "source_payload_sha256",
    "source_sample_ids_sha256",
    "row_order_sha256",
    "row_count",
    "output_schema_version",
    "local_files_only",
    "claim_allowed",
}


def build_actual_extractor_provenance(
    sidecar: Mapping[str, Any],
    *,
    extractor_id: str,
    source_role: str,
    source_manifest_sha256: str,
    source_payload_sha256: str,
    sample_ids: Sequence[str],
    asset_identity: Mapping[str, Any],
    output_schema_version: str,
) -> dict[str, Any]:
    """Build provenance from observed runtime sidecar values, never intended spec values."""

    preprocessing = sidecar.get("preprocessing")
    if not isinstance(preprocessing, dict):
        raise ValueError("actual extractor sidecar has no preprocessing mapping")
    observed_ids = [str(value) for value in sidecar.get("sample_ids", [])]
    if observed_ids != [str(value) for value in sample_ids]:
        raise ValueError("actual extractor sidecar row order differs from the feature payload")
    row_hash = stable_hash(observed_ids)
    payload = {
        "schema_version": "certgen.icml2027.actual_extractor_provenance.v1",
        "extractor_id": extractor_id,
        "runtime_extractor": sidecar.get("extractor"),
        "model_identifier": sidecar.get("model_id"),
        "model_revision": sidecar.get("model_revision"),
        "model_class": sidecar.get("model_class"),
        "processor_identity": sidecar.get("processor_identity"),
        "asset_id": asset_identity.get("asset_id"),
        "asset_revision": asset_identity.get("revision"),
        "asset_manifest_sha256": asset_identity.get("asset_manifest_sha256"),
        "asset_inventory_sha256": asset_identity.get("inventory_sha256"),
        "aggregate_manifest_sha256": asset_identity.get("aggregate_manifest_sha256"),
        "preprocessing_sha256": sidecar.get("preprocessing_sha256"),
        "preprocessing_config": preprocessing,
        "feature_layer": sidecar.get("feature_layer"),
        "dimension": sidecar.get("feature_dim"),
        "dtype": sidecar.get("dtype"),
        "normalization": sidecar.get("feature_normalization"),
        "source_role": source_role,
        "source_manifest_sha256": source_manifest_sha256,
        "source_payload_sha256": source_payload_sha256,
        "source_sample_ids_sha256": row_hash,
        "row_order_sha256": row_hash,
        "row_count": len(observed_ids),
        "output_schema_version": output_schema_version,
        "local_files_only": sidecar.get("local_files_only"),
        "dependency_versions": sidecar.get("dependency_versions", {}),
        "runtime_device": sidecar.get("device"),
        "runtime_snapshot_root": asset_identity.get("runtime_snapshot_root"),
        "runtime_paths_are_scientific_identity": False,
        "claim_allowed": False,
    }
    missing = [field for field in sorted(REQUIRED_ACTUAL_FIELDS) if payload.get(field) is None]
    if missing:
        raise ValueError("actual extractor provenance is incomplete: " + ", ".join(missing))
    payload["actual_provenance_sha256"] = stable_hash(payload)
    return payload


def validate_actual_extractor_provenance(
    actual: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> dict[str, Any]:
    errors: list[str] = []
    missing = sorted(REQUIRED_ACTUAL_FIELDS - set(actual))
    errors.extend(f"missing actual field: {field}" for field in missing)
    if actual.get("schema_version") != "certgen.icml2027.actual_extractor_provenance.v1":
        errors.append("actual extractor provenance schema mismatch")
    if actual.get("claim_allowed") is not False:
        errors.append("actual extractor provenance must keep claim_allowed=false")
    if actual.get("local_files_only") is not True:
        errors.append("actual extractor provenance does not prove offline local loading")
    for field, expected_value in expected.items():
        if field in {"claim_allowed"}:
            continue
        if actual.get(field) != expected_value:
            errors.append(f"actual extractor provenance mismatch: {field}")
    declared = actual.get("actual_provenance_sha256")
    if declared != stable_hash(
        {key: value for key, value in actual.items() if key != "actual_provenance_sha256"}
    ):
        errors.append("actual extractor provenance self-hash mismatch")
    return {
        "schema_version": "certgen.icml2027.actual_extractor_provenance_validation.v1",
        "passed": not errors,
        "errors": errors,
        "actual_provenance_sha256": declared,
        "claim_allowed": False,
    }
