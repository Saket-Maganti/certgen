from pathlib import Path

import yaml

from certgen.cvpr.contracts import configuration_hash
from certgen.cvpr.runtime_planner import DERIVED_FROM_MEASURED_PREFLIGHT, PLANNING_LABELS, build_runtime_plan


def test_runtime_planner_builds_labeled_session_and_resource_plan(tmp_path: Path) -> None:
    config = {
        "schema_version": "certgen.cvpr.runtime_plan_config.v1",
        "run_id": "fixture-runtime-plan",
        "scale": "1k",
        "model_count": 2,
        "images_per_model": 150,
        "reference_images": 100,
        "gpu_count": 2,
        "shard_count": 2,
        "session_limit_minutes": 20,
        "fixed_setup_minutes": 5,
        "model_download_cache_minutes_per_model": 2,
        "generation_images_per_second_per_gpu": {"min": 1.0, "max": 2.0},
        "generation_batch_size": 32,
        "average_encoded_image_bytes": 1000,
        "extractors": [
            {"feature_space_id": "fixture", "images_per_second_per_gpu": {"min": 2.0, "max": 4.0}, "feature_dimension": 8, "bytes_per_value": 4, "batch_size": 16}
        ],
        "merge_minutes": 1,
        "local_validation_minutes": 2,
        "archive_overhead_fraction": 0.1,
        "planning_ram_gib": 8,
        "planning_vram_per_gpu_gib": 16,
        "claim_allowed": False,
    }
    config["configuration_hash"] = configuration_hash(config)
    path = tmp_path / "runtime.yaml"
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    result = build_runtime_plan(path, tmp_path / "runtime.json")
    assert result["labels"] == PLANNING_LABELS
    assert result["inputs"]["image_count"] == 300
    assert result["resources"]["expected_total_output_zip_bytes"] > 0
    assert result["session_plan"]["estimated_number_of_sessions"] >= 1
    assert result["session_plan"]["sessions"][0]["failure_recovery_command"]
    assert result["evidence_class"] == "planning_only"
    assert result["claim_allowed"] is False

    preflight = tmp_path / "preflight.json"
    preflight.write_text(
        '{"seconds_per_image": 0.25, "effective_batch_size": 8, "peak_VRAM": 7.5, '
        '"download_cache_seconds": 12.0, "claim_allowed": false}',
        encoding="utf-8",
    )
    measured = build_runtime_plan(path, tmp_path / "measured.json", preflight_report=preflight)
    assert measured["value_class"] == DERIVED_FROM_MEASURED_PREFLIGHT
    assert measured["inputs"]["generation_batch_size"] == 8
    assert measured["throughput"]["generation_images_per_second_per_gpu"]["minimum"] == 4.0
    assert measured["resources"]["planning_vram_per_gpu_gib"] == 7.5
