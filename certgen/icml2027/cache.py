"""Benchmark-independent cache-v3 sidecar layered above legacy cache-v2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from certgen.icml2027.common import file_sha256, stable_hash, write_json


SCHEMA_VERSION = "certgen.feature_cache.v3"
REQUIRED = {
    "benchmark_id",
    "dataset_role",
    "source_manifest_hash",
    "feature_space_id",
    "extractor_revision",
    "preprocessing_hash",
    "dtype",
    "dimension",
    "row_order_hash",
}


def build_cache_sidecar(
    features_path: str | Path,
    sample_ids: list[str],
    image_hashes: list[str],
    metadata: dict[str, Any],
    out_path: str | Path,
) -> dict[str, Any]:
    missing = sorted(REQUIRED - set(metadata))
    if missing:
        raise ValueError(f"cache metadata missing fields: {missing}")
    if len(sample_ids) != len(image_hashes) or len(sample_ids) != len(set(sample_ids)):
        raise ValueError("sample IDs and image hashes must be aligned and IDs unique")
    with np.load(features_path, allow_pickle=False) as loaded:
        features = np.asarray(loaded["features"])
        stored_ids = [str(value) for value in np.asarray(loaded["sample_ids"]).tolist()]
    if stored_ids != sample_ids or features.ndim != 2 or features.shape != (len(sample_ids), int(metadata["dimension"])):
        raise ValueError("cache rows, IDs, or dimensions do not match metadata")
    if str(features.dtype) != str(metadata["dtype"]):
        raise ValueError("cache dtype does not match metadata")
    if stable_hash(sample_ids) != metadata["row_order_hash"]:
        raise ValueError("row_order_hash does not match sample IDs")
    payload = {
        "schema_version": SCHEMA_VERSION,
        **metadata,
        "sample_ids": sample_ids,
        "image_hashes": image_hashes,
        "sample_id": "per-row in sample_ids",
        "image_hash": "per-row in image_hashes",
        "features_sha256": file_sha256(features_path),
        "shape": list(features.shape),
        "claim_allowed": False,
    }
    write_json(out_path, payload)
    return payload


def validate_cache_sidecar(features_path: str | Path, sidecar_path: str | Path) -> dict[str, Any]:
    import json

    payload = json.loads(Path(sidecar_path).read_text(encoding="utf-8"))
    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("unsupported schema")
    errors.extend(f"missing {field}" for field in sorted(REQUIRED - set(payload)))
    if payload.get("features_sha256") != file_sha256(features_path):
        errors.append("feature hash mismatch")
    if stable_hash(payload.get("sample_ids", [])) != payload.get("row_order_hash"):
        errors.append("row order hash mismatch")
    if len(payload.get("sample_ids", [])) != len(payload.get("image_hashes", [])):
        errors.append("row identity arrays are misaligned")
    return {"passed": not errors, "errors": errors, "schema_version": payload.get("schema_version"), "claim_allowed": False}
