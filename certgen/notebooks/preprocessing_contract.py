"""Observed-versus-expected feature preprocessing contracts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from certgen.cvpr.contracts import atomic_write_json


PLACEHOLDERS = {"TBD", "TBD_EXACT", "UNKNOWN", "TBD_BY_SELECTED_VARIANT", "preprocessing_lock_required"}


@dataclass(frozen=True)
class PreprocessingContract:
    extractor_id: str
    model_identifier: str
    revision: str
    processor_class: str
    input_resolution: int
    resize_size: int | tuple[int, int]
    crop_size: int | tuple[int, int]
    crop_mode: str
    interpolation: str
    antialias: bool
    pixel_range: str
    channel_order: str
    mean: tuple[float, ...]
    std: tuple[float, ...]
    feature_normalization: str
    precision: str
    output_dimension: int
    package_versions: Mapping[str, str]


def normalize_contract(raw: PreprocessingContract | Mapping[str, Any]) -> dict[str, Any]:
    payload = asdict(raw) if isinstance(raw, PreprocessingContract) else dict(raw)
    for key in ("resize_size", "crop_size", "mean", "std"):
        if isinstance(payload.get(key), tuple):
            payload[key] = list(payload[key])
    if isinstance(payload.get("package_versions"), Mapping):
        payload["package_versions"] = dict(sorted(payload["package_versions"].items()))
    return payload


def unresolved_fields(payload: Mapping[str, Any], prefix: str = "") -> list[str]:
    unresolved: list[str] = []
    for key, value in payload.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, Mapping):
            unresolved.extend(unresolved_fields(value, name))
        elif value is None or (isinstance(value, str) and (value in PLACEHOLDERS or "TBD" in value or "UNKNOWN" in value)):
            unresolved.append(name)
    return unresolved


def compare_preprocessing(
    expected: PreprocessingContract | Mapping[str, Any],
    observed: PreprocessingContract | Mapping[str, Any],
    *,
    difference_report: str | Path | None = None,
) -> dict[str, Any]:
    expected_payload = normalize_contract(expected)
    observed_payload = normalize_contract(observed)
    placeholders = unresolved_fields(expected_payload)
    if placeholders:
        raise ValueError("expected preprocessing contains unresolved fields: " + ", ".join(placeholders))
    keys = sorted(set(expected_payload) | set(observed_payload))
    differences = {
        key: {"expected": expected_payload.get(key), "observed": observed_payload.get(key)}
        for key in keys
        if expected_payload.get(key) != observed_payload.get(key)
    }
    payload = {
        "status": "MATCH" if not differences else "MISMATCH",
        "expected": expected_payload,
        "observed": observed_payload,
        "differences": differences,
        "evidence_class": "run_log_only",
        "claim_allowed": False,
    }
    if difference_report is not None:
        atomic_write_json(payload, difference_report)
    if differences:
        raise ValueError("observed preprocessing differs from the frozen expected contract: " + ", ".join(differences))
    return payload


def _processor_value(processor: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if hasattr(processor, name):
            return getattr(processor, name)
    return default


def observe_transformers_processor(
    *,
    extractor_id: str,
    model_identifier: str,
    revision: str,
    processor: Any,
    output_dimension: int,
    package_versions: Mapping[str, str],
    precision: str = "float32",
    feature_normalization: str = "l2",
) -> PreprocessingContract:
    image_processor = getattr(processor, "image_processor", processor)
    size = _processor_value(image_processor, "crop_size", "size")
    shortest = size.get("shortest_edge") if isinstance(size, dict) else size
    height = size.get("height") if isinstance(size, dict) else size
    selected_resolution = height or shortest
    if not isinstance(selected_resolution, (str, int, float)):
        raise ValueError("processor does not expose a numeric input resolution")
    resolution = int(selected_resolution)
    resize = _processor_value(image_processor, "size", default=resolution)
    if isinstance(resize, dict):
        resize = resize.get("shortest_edge") or resize.get("height") or resolution
    crop = _processor_value(image_processor, "crop_size", default=resolution)
    if isinstance(crop, dict):
        crop = (int(crop.get("height", resolution)), int(crop.get("width", resolution)))
    resample = _processor_value(image_processor, "resample", default="bicubic")
    if hasattr(resample, "name"):
        interpolation = str(resample.name).lower()
    elif isinstance(resample, int):
        interpolation = {0: "nearest", 1: "lanczos", 2: "bilinear", 3: "bicubic"}.get(resample, str(resample))
    else:
        interpolation = str(resample).lower()
    mean = tuple(float(value) for value in _processor_value(image_processor, "image_mean", default=()))
    std = tuple(float(value) for value in _processor_value(image_processor, "image_std", default=()))
    return PreprocessingContract(
        extractor_id=extractor_id,
        model_identifier=model_identifier,
        revision=revision,
        processor_class=type(processor).__name__,
        input_resolution=resolution,
        resize_size=int(resize),
        crop_size=crop,
        crop_mode="center" if bool(_processor_value(image_processor, "do_center_crop", default=True)) else "none",
        interpolation=interpolation,
        antialias=True,
        pixel_range="uint8_0_255_to_float_0_1",
        channel_order="RGB",
        mean=mean,
        std=std,
        feature_normalization=feature_normalization,
        precision=precision,
        output_dimension=output_dimension,
        package_versions=package_versions,
    )


def observe_inception_contract(*, package_versions: Mapping[str, str]) -> PreprocessingContract:
    return PreprocessingContract(
        extractor_id="inception",
        model_identifier="torchvision_inception_v3_IMAGENET1K_V1",
        revision="torchvision_0.22.1__Inception_V3_Weights.IMAGENET1K_V1",
        processor_class="torchvision.transforms._presets.ImageClassification",
        input_resolution=299,
        resize_size=342,
        crop_size=299,
        crop_mode="center",
        interpolation="bilinear",
        antialias=True,
        pixel_range="uint8_0_255_to_float_0_1",
        channel_order="RGB",
        mean=(0.485, 0.456, 0.406),
        std=(0.229, 0.224, 0.225),
        feature_normalization="none",
        precision="float32",
        output_dimension=2048,
        package_versions=package_versions,
    )


def load_expected_contract(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("preprocessing contract must be an object")
    if unresolved_fields(payload):
        raise ValueError("real preprocessing contract contains unresolved fields")
    return payload
