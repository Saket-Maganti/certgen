"""Configuration-driven runtime and session planning without execution."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from certgen.cvpr.contracts import atomic_write_json, configuration_hash


PLANNING_LABELS = [
    "planning estimate",
    "hardware-dependent",
    "not an empirical project result",
]
PLANNING_ESTIMATE = "PLANNING_ESTIMATE"
MEASURED_PREFLIGHT = "MEASURED_PREFLIGHT"
DERIVED_FROM_MEASURED_PREFLIGHT = "DERIVED_FROM_MEASURED_PREFLIGHT"


def _load(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    raw = json.loads(source.read_text(encoding="utf-8")) if source.suffix == ".json" else yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("runtime plan configuration must be an object")
    return raw


def _positive_number(config: dict[str, Any], field: str) -> float:
    try:
        value = float(config[field])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a positive finite number") from exc
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{field} must be a positive finite number")
    return value


def _positive_integer(config: dict[str, Any], field: str) -> int:
    value = _positive_number(config, field)
    if not value.is_integer():
        raise ValueError(f"{field} must be an integer")
    return int(value)


def _range(config: dict[str, Any], field: str) -> tuple[float, float]:
    value = config.get(field)
    if not isinstance(value, dict):
        raise ValueError(f"{field} must contain min and max")
    minimum = _positive_number(value, "min")
    maximum = _positive_number(value, "max")
    if minimum > maximum:
        raise ValueError(f"{field}.min cannot exceed {field}.max")
    return minimum, maximum


def build_runtime_plan(
    config_path: str | Path,
    out: str | Path,
    *,
    preflight_report: str | Path | None = None,
) -> dict[str, Any]:
    """Calculate prospective resource/session ranges from a frozen plan."""

    config = _load(config_path)
    if config.get("claim_allowed") is not False:
        raise ValueError("runtime plan must set claim_allowed=false")
    if config.get("configuration_hash") != configuration_hash(config):
        raise ValueError("runtime plan configuration_hash mismatch")
    run_id = str(config.get("run_id", ""))
    scale = str(config.get("scale", ""))
    if not run_id or run_id.startswith("TBD") or scale not in {"preflight", "1k", "10k", "50k"}:
        raise ValueError("resolved run_id and supported scale are required")

    model_count = _positive_integer(config, "model_count")
    images_per_model = _positive_integer(config, "images_per_model")
    reference_images = _positive_integer(config, "reference_images")
    gpu_count = _positive_integer(config, "gpu_count")
    shard_count = _positive_integer(config, "shard_count")
    session_limit_minutes = _positive_number(config, "session_limit_minutes")
    setup_minutes = _positive_number(config, "fixed_setup_minutes")
    cache_minutes = _positive_number(config, "model_download_cache_minutes_per_model")
    merge_minutes = _positive_number(config, "merge_minutes")
    local_validation_minutes = _positive_number(config, "local_validation_minutes")
    generation_min, generation_max = _range(config, "generation_images_per_second_per_gpu")
    image_bytes = _positive_integer(config, "average_encoded_image_bytes")
    ram_gib = _positive_number(config, "planning_ram_gib")
    vram_gib = _positive_number(config, "planning_vram_per_gpu_gib")
    batch_size = _positive_integer(config, "generation_batch_size")
    value_class = PLANNING_ESTIMATE
    measured: dict[str, Any] | None = None
    measured_extractor_rows: dict[str, dict[str, Any]] = {}
    if preflight_report is not None:
        report = _load(preflight_report)
        if report.get("claim_allowed") is not False:
            raise ValueError("preflight runtime report must set claim_allowed=false")
        if "seconds_per_image" in report:
            seconds_per_image = _positive_number(report, "seconds_per_image")
            measured_throughput = 1.0 / seconds_per_image
        else:
            measured_throughput = _positive_number(report, "images_per_second")
            seconds_per_image = 1.0 / measured_throughput
        effective_batch_size = _positive_integer(
            {"value": report.get("effective_batch_size", report.get("safe_batch_size"))}, "value"
        )
        peak_vram = _positive_number(
            {"value": report.get("peak_VRAM", report.get("peak_vram_gib"))}, "value"
        )
        download_seconds = float(report.get("download_cache_seconds", report.get("download_time_seconds", 0.0)))
        if not math.isfinite(download_seconds) or download_seconds < 0:
            raise ValueError("download_cache_seconds must be finite and nonnegative")
        generation_min = generation_max = measured_throughput
        batch_size = effective_batch_size
        cache_minutes = download_seconds / 60 / model_count
        vram_gib = peak_vram
        value_class = DERIVED_FROM_MEASURED_PREFLIGHT
        raw_extractors = report.get("extractors", [])
        if raw_extractors is not None and not isinstance(raw_extractors, list):
            raise ValueError("preflight extractors must be a list")
        measured_extractor_rows = {
            str(row.get("feature_space_id")): dict(row)
            for row in raw_extractors or []
            if isinstance(row, dict) and row.get("feature_space_id")
        }
        measured = {
            "download_time_seconds": {"value": download_seconds, "value_class": MEASURED_PREFLIGHT},
            "model_load_time_seconds": {"value": float(report.get("model_load_time_seconds", 0.0)), "value_class": MEASURED_PREFLIGHT},
            "smoke_generation_time_seconds": {"value": float(report.get("smoke_generation_time_seconds", 0.0)), "value_class": MEASURED_PREFLIGHT},
            "seconds_per_image": {"value": seconds_per_image, "value_class": MEASURED_PREFLIGHT},
            "images_per_minute": {"value": measured_throughput * 60, "value_class": MEASURED_PREFLIGHT},
            "effective_batch_size": {"value": effective_batch_size, "value_class": MEASURED_PREFLIGHT},
            "peak_VRAM": {"value": peak_vram, "value_class": MEASURED_PREFLIGHT},
            "source_report": str(preflight_report),
        }
    extractors = config.get("extractors")
    if not isinstance(extractors, list) or not extractors:
        raise ValueError("extractors must be a non-empty list")
    total_generated = model_count * images_per_model
    total_feature_images = total_generated + reference_images
    generation_seconds_fast = total_generated / (generation_max * gpu_count)
    generation_seconds_slow = total_generated / (generation_min * gpu_count)
    fixed_minutes = setup_minutes + cache_minutes * model_count + merge_minutes
    generation_minutes = {
        "minimum": fixed_minutes + generation_seconds_fast / 60,
        "maximum": fixed_minutes + generation_seconds_slow / 60,
    }

    extractor_rows: list[dict[str, Any]] = []
    feature_bytes = 0
    feature_minutes_min = setup_minutes
    feature_minutes_max = setup_minutes
    for raw in extractors:
        if not isinstance(raw, dict):
            raise ValueError("extractor entries must be objects")
        extractor_id = str(raw.get("feature_space_id", ""))
        if not extractor_id or extractor_id.startswith("TBD"):
            raise ValueError("each extractor requires a resolved feature_space_id")
        throughput_min, throughput_max = _range(raw, "images_per_second_per_gpu")
        dimension = _positive_integer(raw, "feature_dimension")
        bytes_per_value = _positive_integer(raw, "bytes_per_value")
        extractor_batch = _positive_integer(raw, "batch_size")
        measured_extractor = measured_extractor_rows.get(extractor_id)
        extractor_value_class = PLANNING_ESTIMATE
        if measured_extractor is not None:
            measured_rate = _positive_number(measured_extractor, "images_per_second")
            throughput_min = throughput_max = measured_rate
            extractor_batch = _positive_integer(
                {"value": measured_extractor.get("safe_batch_size", measured_extractor.get("batch_size"))},
                "value",
            )
            extractor_value_class = MEASURED_PREFLIGHT
        minutes_min = total_feature_images / (throughput_max * gpu_count) / 60
        minutes_max = total_feature_images / (throughput_min * gpu_count) / 60
        bytes_required = total_feature_images * dimension * bytes_per_value
        feature_bytes += bytes_required
        feature_minutes_min += minutes_min
        feature_minutes_max += minutes_max
        extractor_rows.append(
            {
                "feature_space_id": extractor_id,
                "image_count": total_feature_images,
                "batch_size": extractor_batch,
                "throughput_images_per_second_per_gpu": {"minimum": throughput_min, "maximum": throughput_max},
                "runtime_minutes": {"minimum": minutes_min, "maximum": minutes_max},
                "feature_bytes": bytes_required,
                "labels": PLANNING_LABELS,
                "value_class": extractor_value_class,
            }
        )

    generated_image_bytes = total_generated * image_bytes
    integrity_overhead = float(config.get("archive_overhead_fraction", 0.15))
    if not math.isfinite(integrity_overhead) or integrity_overhead < 0:
        raise ValueError("archive_overhead_fraction must be finite and nonnegative")
    output_bytes = math.ceil((generated_image_bytes + feature_bytes) * (1 + integrity_overhead))
    generation_sessions = max(1, math.ceil(generation_minutes["maximum"] / session_limit_minutes))
    feature_sessions = max(1, math.ceil(feature_minutes_max / session_limit_minutes))
    required_sessions = max(generation_sessions, feature_sessions)
    if required_sessions > shard_count:
        raise ValueError("shard_count is insufficient for the conservative session plan")

    shard_ids = [f"shard_{index:04d}" for index in range(shard_count)]
    session_rows = []
    for session_index in range(required_sessions):
        assigned = shard_ids[session_index::required_sessions]
        session_rows.append(
            {
                "session_id": f"session_{session_index + 1:03d}",
                "shard_ids": assigned,
                "expected_zip_bytes": math.ceil(output_bytes * len(assigned) / shard_count),
                "copyback_checkpoint": f"after all {len(assigned)} assigned shards have complete status and integrity hashes",
                "resume_point": "next incomplete shard under the identical configuration hash",
                "failure_recovery_command": "python3 -m certgen import <stage> <blocked-diagnostic.zip>",
                "models": config.get("model_ids", [f"registered_model_{index + 1}" for index in range(model_count)]),
                "expected_duration_minutes": generation_minutes,
                "resume_command": "rerun the same canonical notebook with mode=resume and the identical hashes",
                "copy_back_zip": f"certgen_cvpr_session_{session_index + 1:03d}.zip",
                "labels": PLANNING_LABELS,
                "value_class": value_class,
            }
        )

    payload = {
        "schema_version": "certgen.cvpr.runtime_plan.v2",
        "run_id": run_id,
        "scale": scale,
        "configuration_hash": str(config["configuration_hash"]),
        "labels": PLANNING_LABELS,
        "value_class": value_class,
        "measurement_taxonomy": [PLANNING_ESTIMATE, MEASURED_PREFLIGHT, DERIVED_FROM_MEASURED_PREFLIGHT],
        "measured_preflight": measured,
        "inputs": {
            "model_count": model_count,
            "images_per_model": images_per_model,
            "reference_images": reference_images,
            "image_count": total_generated,
            "feature_image_count": total_feature_images,
            "generation_batch_size": batch_size,
            "gpu_count": gpu_count,
            "shard_count": shard_count,
            "value_class": value_class,
        },
        "runtime_minutes": {
            "fixed_setup": setup_minutes,
            "model_download_cache": cache_minutes * model_count,
            "generation": generation_minutes,
            "feature_extraction": {"minimum": feature_minutes_min, "maximum": feature_minutes_max},
            "merge": merge_minutes,
            "local_validation": local_validation_minutes,
            "value_class": value_class,
        },
        "throughput": {
            "generation_images_per_second_per_gpu": {"minimum": generation_min, "maximum": generation_max, "value_class": value_class},
            "extractors": extractor_rows,
        },
        "resources": {
            "expected_generated_image_bytes": generated_image_bytes,
            "expected_feature_bytes": feature_bytes,
            "expected_total_output_zip_bytes": output_bytes,
            "planning_ram_gib": ram_gib,
            "planning_vram_per_gpu_gib": vram_gib,
            "minimum_kaggle_working_disk_gib": 10,
            "value_class": value_class,
        },
        "session_plan": {
            "session_limit_minutes": session_limit_minutes,
            "estimated_generation_sessions": generation_sessions,
            "estimated_feature_sessions": feature_sessions,
            "estimated_number_of_sessions": required_sessions,
            "sessions": session_rows,
            "value_class": value_class,
        },
        "resumability": "configuration-hash-bound deterministic shards only",
        "evidence_class": "planning_only",
        "claim_allowed": False,
    }
    atomic_write_json(payload, out)
    return payload
