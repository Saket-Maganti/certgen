"""Inception-V3 pool3 (2048-d) extractor for FID/KID-family features.

Note on reproduction fidelity: exact published FID/KID numbers are tied to the
specific TF-ported "pt_inception" weights and a [-1, 1] input convention. This
adapter defaults to torchvision Inception-V3 weights and records the exact
weights id, interpolation, and normalization in the sidecar so any reproduction
gap is detectable rather than silent. Swap ``model_id`` / preprocessing to match
the canonical pipeline when reproducing a specific paper's number.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from certgen.features.extractors.base import FeatureExtractor

_INTERPOLATION = {"bilinear": "BILINEAR", "bicubic": "BICUBIC", "nearest": "NEAREST"}
_NORMALIZATION = {
    "inception": ((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    "imagenet": ((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
}


class InceptionV3Pool3Extractor(FeatureExtractor):
    def __init__(self) -> None:
        super().__init__("inception_v3_pool3", 2048, ["torch", "torchvision"])

    def _load_backbone(self, device: str, model_id: str | None, preprocessing: dict[str, Any] | None) -> tuple[Any, Any]:
        import torch
        from torchvision import transforms
        from torchvision.models import Inception_V3_Weights, inception_v3

        preprocessing = preprocessing or {}
        size = int(preprocessing.get("image_size", 299))
        interp_name = _INTERPOLATION.get(str(preprocessing.get("interpolation", "bilinear")), "BILINEAR")
        mean, std = _NORMALIZATION.get(str(preprocessing.get("normalization", "inception")), _NORMALIZATION["inception"])
        interpolation = getattr(transforms.InterpolationMode, interp_name)

        asset = getattr(self, "runtime_asset_context", {})
        weights = Inception_V3_Weights.IMAGENET1K_V1
        if asset:
            if asset.get("local_files_only") is not True:
                raise ValueError("Inception authenticated asset must be local-files-only")
            weight_path = asset.get("runtime_weight_file")
            if not weight_path:
                raise ValueError("Inception authenticated asset has no exact local state-dict file")
            model = inception_v3(weights=None, aux_logits=True)
            state_dict = torch.load(str(weight_path), map_location="cpu", weights_only=True)
            model.load_state_dict(state_dict, strict=True)
            self.resolved_local_files_only = True
            self.resolved_local_snapshot_inventory_sha256 = asset.get("inventory_sha256")
        else:
            model = inception_v3(weights=weights, aux_logits=True)
            self.resolved_local_files_only = False
        self.resolved_model_id = "torchvision_inception_v3_IMAGENET1K_V1"
        self.resolved_model_revision = (
            "torchvision_0.22.1__Inception_V3_Weights.IMAGENET1K_V1"
        )
        self.resolved_weights_id = weights.name
        self.resolved_weights_url = None if asset else weights.url
        self.resolved_license_status = "unknown"
        self.resolved_model_class = "torchvision.models.Inception3"
        self.resolved_processor_identity = "torchvision.transforms.Compose"
        self.resolved_feature_layer = "final_global_average_pool_before_fc_2048d"
        self.resolved_feature_normalization = "none"
        model.fc = torch.nn.Identity()
        model.eval().to(device)

        transform = transforms.Compose(
            [
                transforms.Resize((size, size), interpolation=interpolation),
                transforms.ToTensor(),
                transforms.Normalize(mean, std),
            ]
        )
        return model, transform

    def _forward(self, model: Any, batch: Any) -> np.ndarray:
        output = model(batch)
        if isinstance(output, tuple):
            output = output[0]
        return output.detach().to("cpu").float().numpy()
