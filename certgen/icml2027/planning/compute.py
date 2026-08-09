"""Typed planning estimates that never masquerade as measurements."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from certgen.icml2027.common import load_mapping, write_json


def plan_compute(config_path: str | Path, out_path: str | Path) -> dict[str, Any]:
    config = load_mapping(config_path)
    model_count = int(config["model_count"])
    sample_count = int(config["sample_count"])
    gpu_count = int(config.get("gpu_count", 2))
    session_limit_hours = float(config.get("session_limit_hours", 12.0))
    images_per_second = config.get("measured_images_per_second")
    feature_throughput = config.get("measured_extractor_throughput")
    if model_count <= 0 or sample_count <= 0 or gpu_count <= 0 or session_limit_hours <= 0:
        raise ValueError("counts, GPU count, and session limit must be positive")
    measurement_status = "measured" if images_per_second is not None and feature_throughput is not None else "planning_estimate"
    if images_per_second is None:
        images_per_second = float(config.get("planning_images_per_second", 4.0)) * gpu_count
    if feature_throughput is None:
        feature_throughput = float(config.get("planning_extractor_throughput", 32.0)) * gpu_count
    images_per_second = float(images_per_second)
    feature_throughput = float(feature_throughput)
    if images_per_second <= 0 or feature_throughput <= 0:
        raise ValueError("throughput values must be positive")
    total_images = model_count * sample_count + int(config.get("reference_count", sample_count))
    generation_seconds = model_count * sample_count / images_per_second
    feature_seconds = total_images / feature_throughput
    overhead_fraction = float(config.get("overhead_fraction", 0.2))
    total_gpu_seconds = (generation_seconds + feature_seconds) * (1 + overhead_fraction)
    session_seconds = session_limit_hours * 3600
    sessions = max(1, math.ceil(total_gpu_seconds / session_seconds))
    bytes_per_image = int(config.get("expected_bytes_per_image", 50_000))
    feature_dimension = int(config.get("feature_dimension", 768))
    feature_spaces = int(config.get("feature_space_count", 3))
    expected_disk = total_images * (bytes_per_image + 4 * feature_dimension * feature_spaces)
    output_fraction = float(config.get("output_zip_fraction", 0.85))
    shard_size = min(
        int(config.get("maximum_shard_size", 5000)),
        max(100, math.floor(session_seconds * images_per_second / max(model_count, 1) * 0.7)),
    )
    payload = {
        "schema_version": "certgen.icml2027.compute_plan.v1",
        "measurement_status": measurement_status,
        "estimate_label": "AUTHENTICATED_MEASUREMENT_DERIVED" if measurement_status == "measured" else "PLANNING_ESTIMATE_NOT_MEASURED",
        "inputs": config,
        "estimated_GPU_hours": total_gpu_seconds / 3600,
        "generation_GPU_hours": generation_seconds / 3600,
        "feature_GPU_hours": feature_seconds / 3600,
        "estimated_sessions": sessions,
        "expected_disk_bytes": expected_disk,
        "expected_ZIP_bytes": int(expected_disk * output_fraction),
        "recommended_shard_size": shard_size,
        "copyback_cadence": "after_each_shard" if sessions > 1 else "end_of_stage_plus_final_validation",
        "planning_only": True,
        "claim_allowed": False,
    }
    write_json(out_path, payload)
    return payload
