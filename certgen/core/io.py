"""JSON and local feature-array IO helpers."""

from __future__ import annotations

import dataclasses
import json
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

from certgen.core.hashing import file_sha256, make_jsonable, stable_hash_json
from certgen.schemas.feature_manifest import FeatureManifest


def to_json_dict(obj: Any) -> dict[str, Any]:
    value = make_jsonable(obj)
    if not isinstance(value, dict):
        raise TypeError(f"Expected object convertible to dict, got {type(obj).__name__}")
    return value


def write_json(obj: Any, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(make_jsonable(obj), handle, indent=2, sort_keys=True)
        handle.write("\n")


def read_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def save_feature_npz(features: np.ndarray, path: str | Path) -> dict[str, Any]:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    array = np.asarray(features)
    np.savez_compressed(path, features=array)
    return feature_array_info(path)


def load_feature_npz(path: str | Path) -> np.ndarray:
    with np.load(Path(path), allow_pickle=False) as loaded:
        if "features" not in loaded:
            raise ValueError(f"{path} does not contain a 'features' array")
        array = loaded["features"]
    if array.ndim != 2:
        raise ValueError(f"Feature array must be 2D, got shape {array.shape}")
    return array


def feature_array_info(path: str | Path) -> dict[str, Any]:
    array = load_feature_npz(path)
    return {
        "path": str(Path(path)),
        "shape": list(array.shape),
        "dtype": str(array.dtype),
        "hash": file_sha256(path),
    }


def validate_feature_manifest(manifest: FeatureManifest, feature_path: str | Path | None = None) -> bool:
    path = Path(feature_path or manifest.feature_path)
    array = load_feature_npz(path)
    expected_shape = (int(manifest.num_items), int(manifest.feature_dim))
    if tuple(array.shape) != expected_shape:
        raise ValueError(f"Feature shape mismatch for {path}: expected {expected_shape}, got {tuple(array.shape)}")
    actual_hash = file_sha256(path)
    if manifest.hash and manifest.hash != actual_hash:
        raise ValueError(f"Feature hash mismatch for {path}: expected {manifest.hash}, got {actual_hash}")
    return True


def make_feature_manifest(
    dataset_or_model_id: str,
    feature_type: str,
    feature_path: str,
    preprocessing: dict[str, Any],
    evidence_status: str,
) -> FeatureManifest:
    array = load_feature_npz(feature_path)
    return FeatureManifest(
        feature_manifest_id=stable_hash_json(
            {
                "dataset_or_model_id": dataset_or_model_id,
                "feature_type": feature_type,
                "feature_path": str(feature_path),
                "shape": list(array.shape),
                "preprocessing": preprocessing,
                "evidence_status": evidence_status,
            }
        )[:16],
        dataset_or_model_id=dataset_or_model_id,
        feature_type=feature_type,
        num_items=int(array.shape[0]),
        feature_dim=int(array.shape[1]),
        preprocessing=preprocessing,
        feature_path=str(feature_path),
        hash=file_sha256(feature_path),
        evidence_status=evidence_status,
    )


__all__ = [
    "to_json_dict",
    "write_json",
    "read_json",
    "stable_hash_json",
    "save_feature_npz",
    "load_feature_npz",
    "feature_array_info",
    "validate_feature_manifest",
    "make_feature_manifest",
]
