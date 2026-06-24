from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FeatureManifest:
    feature_manifest_id: str
    dataset_or_model_id: str
    feature_type: str
    num_items: int
    feature_dim: int
    preprocessing: dict[str, Any]
    feature_path: str
    hash: str
    evidence_status: str
