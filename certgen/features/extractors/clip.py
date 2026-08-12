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
_DEFAULT_REVISION = "32bd64288804d66eefd0ccbe215aa642df71cc41"


class ClipVitExtractor(FeatureExtractor):
    def __init__(self) -> None:
        super().__init__("clip_vit", 768, ["torch", "transformers"])
        self._processor: Any = None

    def _load_backbone(self, device: str, model_id: str | None, preprocessing: dict[str, Any] | None) -> tuple[Any, Any]:
        from transformers import CLIPModel, CLIPProcessor

        asset = getattr(self, "runtime_asset_context", {})
        configured_model_id = str(asset.get("model_identifier") or model_id or _DEFAULT_MODEL)
        if configured_model_id != _DEFAULT_MODEL:
            raise ValueError("non-default CLIP model requires an explicitly implemented immutable revision lock")
        if asset:
            if asset.get("local_files_only") is not True or asset.get("revision") != _DEFAULT_REVISION:
                raise ValueError("CLIP authenticated local asset identity mismatch")
            snapshot = str(asset["runtime_snapshot_root"])
            model = CLIPModel.from_pretrained(snapshot, local_files_only=True)
            self._processor = CLIPProcessor.from_pretrained(snapshot, local_files_only=True)
            self.resolved_local_files_only = True
            self.resolved_local_snapshot_inventory_sha256 = asset.get("inventory_sha256")
        else:
            model = CLIPModel.from_pretrained(configured_model_id, revision=_DEFAULT_REVISION)
            self._processor = CLIPProcessor.from_pretrained(
                configured_model_id, revision=_DEFAULT_REVISION
            )
            self.resolved_local_files_only = False
        model.eval().to(device)
        self.resolved_model_id = configured_model_id
        self.resolved_model_revision = _DEFAULT_REVISION
        self.resolved_weights_id = "huggingface_commit"
        self.resolved_weights_url = (
            None
            if asset
            else f"https://huggingface.co/{configured_model_id}/tree/{_DEFAULT_REVISION}"
        )
        self.resolved_license_status = "unknown"
        self.resolved_model_class = "transformers.CLIPModel"
        self.resolved_processor_identity = "transformers.CLIPProcessor"
        self.resolved_feature_layer = "projected_image_embedding_from_CLIPModel.get_image_features"
        self.resolved_feature_normalization = "l2"
        projection_dim = model.config.projection_dim
        if projection_dim is None:
            raise ValueError("CLIP model has no projection dimension")
        self.feature_dim = int(projection_dim)
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
