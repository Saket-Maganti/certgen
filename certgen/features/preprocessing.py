"""Strict preprocessing policy contracts for feature caches."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class PreprocessingPolicy:
    preprocessing_policy_id: str
    resize_size: str
    crop_policy: str
    interpolation: str
    normalization: str
    feature_extractor: str

    def validate(self) -> None:
        fields = asdict(self)
        for key, value in fields.items():
            if value in {None, "", "default", "unknown", "TBD"}:
                raise ValueError(f"preprocessing field {key} must be explicit")
