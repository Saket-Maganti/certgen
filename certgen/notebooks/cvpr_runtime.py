"""Uploaded runtime adapters used by the canonical Kaggle feature notebooks.

Imports are intentionally lazy so local-safe validation never loads or
downloads a vision model.
"""

from __future__ import annotations

from typing import Any


def build_extractor(config: dict[str, Any], *, device: str) -> tuple[Any, Any]:
    """Build one frozen extractor and a per-image tensor transform."""

    feature_space = str(config.get("feature_space_id"))
    model_identifier = str(config.get("model_identifier"))
    revision = str(config.get("revision"))
    local_only = bool(config.get("local_files_only", False))
    if not revision or revision.startswith("TBD"):
        raise ValueError("extractor revision must be pinned before Kaggle execution")
    if feature_space == "inception":
        import torch
        from torchvision.models import Inception_V3_Weights, inception_v3  # type: ignore[import-untyped]

        weights = Inception_V3_Weights.IMAGENET1K_V1
        if model_identifier != "torchvision_inception_v3_IMAGENET1K_V1":
            raise ValueError("unsupported Inception model identifier")
        model = inception_v3(weights=weights)
        model.fc = torch.nn.Identity()
        model.eval().to(device)
        return model, weights.transforms()
    if feature_space == "clip":
        import torch
        from transformers import CLIPImageProcessor, CLIPVisionModelWithProjection

        processor = CLIPImageProcessor.from_pretrained(model_identifier, revision=revision, local_files_only=local_only)
        backbone = CLIPVisionModelWithProjection.from_pretrained(model_identifier, revision=revision, local_files_only=local_only).eval().to(device)

        class ClipWrapper(torch.nn.Module):
            def __init__(self, model: Any) -> None:
                super().__init__()
                self.model = model

            def forward(self, pixel_values: Any) -> Any:
                return self.model(pixel_values=pixel_values).image_embeds

        return ClipWrapper(backbone).eval().to(device), lambda image: processor(images=image, return_tensors="pt")["pixel_values"][0]
    if feature_space == "dinov2":
        import torch
        from transformers import AutoImageProcessor, AutoModel

        processor = AutoImageProcessor.from_pretrained(model_identifier, revision=revision, local_files_only=local_only)
        backbone = AutoModel.from_pretrained(model_identifier, revision=revision, local_files_only=local_only).eval().to(device)

        class DinoWrapper(torch.nn.Module):
            def __init__(self, model: Any) -> None:
                super().__init__()
                self.model = model

            def forward(self, pixel_values: Any) -> Any:
                output = self.model(pixel_values=pixel_values)
                pooler = getattr(output, "pooler_output", None)
                return pooler if pooler is not None else output.last_hidden_state[:, 0]

        return DinoWrapper(backbone).eval().to(device), lambda image: processor(images=image, return_tensors="pt")["pixel_values"][0]
    raise ValueError(f"unsupported feature space: {feature_space}")
