"""Dry-run-safe feature extractor adapters."""

from certgen.features.extractors.base import OptionalDependencyMissing
from certgen.features.extractors.clip import ClipVitExtractor
from certgen.features.extractors.dinov2 import DinoV2Extractor
from certgen.features.extractors.inception import InceptionV3Pool3Extractor

EXTRACTORS = {
    "inception_v3_pool3": InceptionV3Pool3Extractor,
    "clip_vit": ClipVitExtractor,
    "dinov2": DinoV2Extractor,
}

__all__ = ["EXTRACTORS", "OptionalDependencyMissing"]
