"""DINOv2 CLS-token extractor for FD-DINOv2 features.

FD-DINOv2 is treated as a *descriptive* metric in CertGen (a Frechet distance,
not a streamable bounded-mean estimator), so these features are for descriptive
reporting and qualitative agreement checks, not for rigorous certificates.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from certgen.features.extractors.base import FeatureExtractor

_DEFAULT_MODEL = "facebook/dinov2-base"


class DinoV2Extractor(FeatureExtractor):
    def __init__(self) -> None:
        super().__init__("dinov2", 768, ["torch", "transformers"])
        self._processor = None

    def _load_backbone(self, device: str, model_id: str | None, preprocessing: dict[str, Any] | None) -> tuple[Any, Any]:
        from transformers import AutoImageProcessor, AutoModel

        model_id = model_id or _DEFAULT_MODEL
        model = AutoModel.from_pretrained(model_id)
        model.eval().to(device)
        self._processor = AutoImageProcessor.from_pretrained(model_id)
        self.feature_dim = int(model.config.hidden_size)
        return model, self._processor

    def _embed_paths(self, model: Any, transform: Any, paths: list[str], device: str, batch_size: int) -> np.ndarray:
        import torch

        chunks: list[np.ndarray] = []
        for start in range(0, len(paths), max(1, batch_size)):
            images = [self._load_image(path) for path in paths[start : start + max(1, batch_size)]]
            inputs = transform(images=images, return_tensors="pt").to(device)
            with torch.no_grad():
                outputs = model(**inputs)
            cls_token = outputs.last_hidden_state[:, 0, :]
            chunks.append(cls_token.detach().to("cpu").float().numpy())
        return np.concatenate(chunks, axis=0) if chunks else np.empty((0, self.feature_dim), dtype=np.float32)
