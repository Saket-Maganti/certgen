"""Pinned DINOv2 robustness adapter contract; no weights are downloaded locally."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from certgen.icml2027.common import file_sha256, stable_hash


@dataclass(frozen=True)
class DinoV2Contract:
    model_identifier: str = "facebook/dinov2-base"
    revision: str = "f9e44c814b77203eaa57a6bdbbd535f21ede1415"
    package: str = "transformers"
    model_class: str = "Dinov2Model"
    processor: str = "AutoImageProcessor"
    feature_layer: str = "last_hidden_state[:,0,:]"
    feature_normalization: str = "none"
    dimension: int = 768
    input_resolution: int = 224
    resize_shortest_edge: int = 256
    crop: str = "center_crop_224"
    interpolation: str = "bicubic_pil_resample_3"
    pixel_normalization: str = "imagenet_mean_std"
    precision: str = "float32_output"
    license: str = "Apache-2.0"
    license_status: str = "SOURCE_VERIFIED_REVIEW_REQUIRED_BEFORE_REDISTRIBUTION"
    source_url: str = "https://huggingface.co/facebook/dinov2-base"
    upstream_model_card: str = "https://github.com/facebookresearch/dinov2/blob/main/MODEL_CARD.md"
    redistribution_allowed: bool = False
    claim_allowed: bool = False

    @property
    def preprocessing_hash(self) -> str:
        return stable_hash(
            {
                "input_resolution": self.input_resolution,
                "resize_shortest_edge": self.resize_shortest_edge,
                "crop": self.crop,
                "interpolation": self.interpolation,
                "pixel_normalization": self.pixel_normalization,
                "feature_normalization": self.feature_normalization,
            }
        )

    @property
    def contract_hash(self) -> str:
        return stable_hash(asdict(self))


def validate_asset_manifest(manifest_path: str | Path, asset_root: str | Path) -> dict[str, Any]:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    contract = DinoV2Contract()
    errors: list[str] = []
    if manifest.get("model_identifier") != contract.model_identifier:
        errors.append("model identifier mismatch")
    if manifest.get("revision") != contract.revision:
        errors.append("revision mismatch")
    if manifest.get("license_status") not in {"reviewed_approved", "source_verified_reviewed"}:
        errors.append("license review approval missing")
    root = Path(asset_root).resolve()
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        errors.append("asset file inventory missing")
        files = []
    for row in files:
        relative = Path(str(row.get("path", "")))
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"unsafe asset path: {relative}")
            continue
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            errors.append(f"asset path escapes root: {relative}")
            continue
        if not path.is_file():
            errors.append(f"asset missing: {relative}")
        elif row.get("sha256") != file_sha256(path):
            errors.append(f"asset hash mismatch: {relative}")
    return {
        "schema_version": "certgen.icml2027.dinov2_asset_validation.v1",
        "passed": not errors,
        "errors": errors,
        "contract_hash": contract.contract_hash,
        "preprocessing_hash": contract.preprocessing_hash,
        "claim_allowed": False,
    }


class DinoV2Adapter:
    """Offline-only adapter used by Kaggle workers after asset authentication."""

    def __init__(self, contract: DinoV2Contract | None = None) -> None:
        self.contract = contract or DinoV2Contract()

    def load(self, asset_root: str | Path, device: str) -> tuple[Any, Any]:
        from transformers import AutoImageProcessor, Dinov2Model

        root = str(Path(asset_root).resolve())
        processor = AutoImageProcessor.from_pretrained(root, local_files_only=True)
        model = Dinov2Model.from_pretrained(root, local_files_only=True)
        if int(model.config.hidden_size) != self.contract.dimension:
            raise ValueError("DINOv2 hidden dimension does not match frozen contract")
        model.eval().to(device)
        return model, processor

    def extract(self, paths: list[str], asset_root: str | Path, device: str = "cuda:0", batch_size: int = 32) -> np.ndarray:
        import torch
        from PIL import Image

        model, processor = self.load(asset_root, device)
        chunks: list[np.ndarray] = []
        for start in range(0, len(paths), max(1, batch_size)):
            images = []
            for path in paths[start : start + batch_size]:
                with Image.open(path) as image:
                    images.append(image.convert("RGB"))
            inputs = processor(images=images, return_tensors="pt").to(device)
            with torch.no_grad():
                output = model(**inputs).last_hidden_state[:, 0, :]
            chunks.append(output.detach().cpu().float().numpy())
        result = np.concatenate(chunks, axis=0) if chunks else np.empty((0, self.contract.dimension), dtype=np.float32)
        if result.shape != (len(paths), self.contract.dimension) or not np.all(np.isfinite(result)):
            raise ValueError("DINOv2 output violates frozen cache contract")
        return result


def deterministic_sample_id(path: str | Path, image_hash: str) -> str:
    return "dinov2_" + hashlib.sha256(f"{Path(path).name}\0{image_hash}".encode()).hexdigest()[:24]
