"""Feature and certificate IO helpers for V2 clean certificates."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from certgen.core.hashing import file_sha256


def load_feature_array(path: str | Path) -> np.ndarray:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(str(path))
    if path.suffix == ".npz":
        with np.load(path, allow_pickle=False) as loaded:
            if "features" not in loaded:
                raise ValueError(f"{path} must contain a 'features' array")
            array = loaded["features"]
    elif path.suffix == ".npy":
        array = np.load(path, allow_pickle=False)
    elif path.suffix == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    obj = json.loads(line)
                    rows.append(obj["features"] if isinstance(obj, dict) and "features" in obj else obj)
        array = np.asarray(rows, dtype=float)
    else:
        raise ValueError(f"unsupported feature format: {path.suffix}")
    array = np.asarray(array, dtype=float)
    if array.ndim != 2:
        raise ValueError(f"features must be 2D, got shape {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError("features contain NaN or Inf")
    return array


def load_feature_sample_ids(path: str | Path) -> list[str]:
    """Load row-aligned sample IDs required by real reference draw plans."""

    path = Path(path)
    if path.suffix != ".npz":
        raise ValueError("reference draw plans currently require an NPZ cache with sample_ids")
    with np.load(path, allow_pickle=False) as loaded:
        if "sample_ids" not in loaded:
            raise ValueError(f"{path} must contain sample_ids for reference draw-plan validation")
        values = np.asarray(loaded["sample_ids"])
    if values.ndim != 1:
        raise ValueError("feature sample_ids must be one-dimensional")
    ids = [str(item) for item in values.tolist()]
    if not ids or any(not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("feature sample_ids must be non-empty and unique")
    return ids


def feature_hashes(*, features_a_path: str, features_b_path: str, features_r_path: str) -> dict[str, str]:
    return {
        "features_a_sha256": file_sha256(features_a_path),
        "features_b_sha256": file_sha256(features_b_path),
        "features_r_sha256": file_sha256(features_r_path),
    }
