"""V4 preprocessing locks."""

from __future__ import annotations

from pathlib import Path

from certgen.core.hashing import stable_hash_json
from certgen.core.io import write_json, read_json


REQUIRED_LOCK_FIELDS = [
    "lock_id",
    "image_size",
    "resize_policy",
    "interpolation",
    "center_crop",
    "normalization",
    "color_mode",
    "feature_extractor",
    "feature_extractor_version",
    "batch_size",
    "dtype",
    "sample_order_policy",
    "reference_set_policy",
]


def make_preprocessing_lock(name: str, out: str | Path, **overrides) -> dict:
    lock = {
        "lock_id": name,
        "image_size": overrides.get("image_size", 299),
        "resize_policy": overrides.get("resize_policy", "resize_shorter_side_then_center"),
        "interpolation": overrides.get("interpolation", "bicubic"),
        "center_crop": overrides.get("center_crop", True),
        "normalization": overrides.get("normalization", "feature_extractor_default"),
        "color_mode": overrides.get("color_mode", "rgb"),
        "feature_extractor": overrides.get("feature_extractor", "inception_v3_pool3"),
        "feature_extractor_version": overrides.get("feature_extractor_version", "manual_user_verified"),
        "batch_size": overrides.get("batch_size", 32),
        "dtype": overrides.get("dtype", "float32"),
        "sample_order_policy": overrides.get("sample_order_policy", "manifest_order_seeded"),
        "reference_set_policy": overrides.get("reference_set_policy", "declared_manifest"),
    }
    lock["hash"] = stable_hash_json(lock)
    write_json(lock, out)
    return lock


def validate_preprocessing_lock(path: str | Path, *, strict: bool = True) -> list[str]:
    lock = read_json(path)
    errors = []
    for field in REQUIRED_LOCK_FIELDS:
        if field not in lock or lock[field] in {"", "unknown", "TBD", None}:
            errors.append(f"missing or unknown lock field: {field}")
    expected = lock.get("hash")
    body = {k: v for k, v in lock.items() if k != "hash"}
    if expected and expected != stable_hash_json(body):
        errors.append("lock hash mismatch")
    if strict and any(lock.get(field) in {"unknown", "TBD"} for field in REQUIRED_LOCK_FIELDS):
        errors.append("strict mode rejects unknown preprocessing")
    return errors
