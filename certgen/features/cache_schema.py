"""Feature cache manifest schema for V2."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class FeatureCacheManifest:
    cache_id: str
    dataset_id: str
    split: str
    sample_source_type: str
    model_or_generator_id: str
    feature_extractor: str
    feature_extractor_version: str
    preprocessing_policy_id: str
    resize_size: str
    crop_policy: str
    interpolation: str
    normalization: str
    num_samples: int
    feature_dim: int
    feature_file_path: str
    feature_file_sha256: str
    source_license_status: str
    download_or_local_source_note: str
    evidence_status: str
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)
