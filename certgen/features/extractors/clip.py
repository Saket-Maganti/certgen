"""CLIP image-embedding extractor for CMMD-family features.

CMMD is canonically computed on CLIP ViT-L/14 image embeddings. The default
``model_id`` follows that; pass a smaller model id for cheap debugging. The
embedding dimension is read from the loaded model so the declared ``feature_dim``
always matches what is written.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from certgen.features.extractors.base import FeatureExtractor

_DEFAULT_MODEL = "openai/clip-vit-large-patch14"


class ClipVitExtractor(FeatureExtractor):
    def __init__(self) -> None:
        super().__init__("clip_vit", 768, ["torch", "transformers"])
        self._processor = None

    def _load_backbone(self, device: str, model_id: str | None, preprocessing: dict[str, Any] | None) -> tuple[Any, Any]:
        from transformers import CLIPModel, CLIPProcessor

        model_id = model_id or _DEFAULT_MODEL
        model = CLIPModel.from_pretrained(model_id)
        model.eval().to(device)
        self._processor = CLIPProcessor.from_pretrained(model_id)
        self.feature_dim = int(model.config.projection_dim)
        return model, self._processor

    def _embed_paths(self, model: Any, transform: Any, paths: list[str], device: str, batch_size: int) -> np.ndarray:
        import torch

        chunks: list[np.ndarray] = []
        for start in range(0, len(paths), max(1, batch_size)):
            images = [self._load_image(path) for path in paths[start : start + max(1, batch_size)]]
            inputs = transform(images=images, return_tensors="pt").to(device)
            with torch.no_grad():
                features = model.get_image_features(**inputs)
            chunks.append(features.detach().to("cpu").float().numpy())
        return np.concatenate(chunks, axis=0) if chunks else np.empty((0, self.feature_dim), dtype=np.float32)
