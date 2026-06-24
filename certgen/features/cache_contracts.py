"""V3 feature-cache contract objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class V3FeatureCacheValidation:
    passed: bool
    errors: list[str]
    warnings: list[str]
    evidence_status: str
    claim_allowed: bool
    feature_shape: tuple[int, int] | None = None
    sidecar: dict[str, Any] | None = None
