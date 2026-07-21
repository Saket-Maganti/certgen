import numpy as np
import pytest

from certgen.cvpr.image_manifest import normalize_row
from certgen.features.protocol_checks import (
    compare_feature_runs,
    independent_shard_merge_check,
)


def test_protocol_checks_measure_real_differences_and_independent_merge() -> None:
    sample_ids = ["s3", "s1", "s4", "s2"]
    features = np.asarray(
        [[1.0, 0.0], [0.9, 0.1], [0.1, 0.9], [0.0, 1.0]],
        dtype=np.float32,
    )

    batching = compare_feature_runs(sample_ids, features, sample_ids, features.copy())
    merge = independent_shard_merge_check(sample_ids, features)

    assert batching["passed"] is True
    assert batching["maximum_feature_difference"] == 0.0
    assert batching["metric_difference"] == 0.0
    assert merge["passed"] is True
    assert merge["row_coverage_equal"] is True
    assert merge["one_shard_order_hash"] == merge["two_shard_order_hash"]


def test_protocol_comparison_fails_on_order_or_numeric_drift() -> None:
    sample_ids = ["s0", "s1", "s2", "s3"]
    features = np.eye(4, dtype=np.float32)
    drifted = features.copy()
    drifted[0, 0] += 0.01

    assert not compare_feature_runs(sample_ids, features, sample_ids[::-1], features)["passed"]
    assert not compare_feature_runs(sample_ids, features, sample_ids, drifted)["passed"]


def test_control_manifest_requires_and_preserves_complete_lineage() -> None:
    row = {
        "sample_id": "control-1",
        "role": "control_obvious_corrupted",
        "model_id": "reference_severe_corruption",
        "relative_image_path": "controls/control-1.png",
        "image_hash": "a" * 64,
        "seed": 0,
        "prompt_or_class_id": 1,
        "width": 32,
        "height": 32,
        "mode": "RGB",
        "source_run_id": "control-builder",
        "source_manifest_hash": "b" * 64,
        "source_id": "reference-1",
        "source_role": "reference",
        "clean_or_corrupted": "corrupted",
        "corruption_type": "gaussian_blur",
        "corruption_severity": 2.0,
        "corruption_seed": 0,
        "reference_draw_id": "reference-1",
        "study_hash": "c" * 64,
        "preprocessing_hash": "d" * 64,
    }

    normalized = normalize_row(row)

    assert normalized["source_id"] == "reference-1"
    assert normalized["corruption_severity"] == 2.0
    with pytest.raises(ValueError, match="missing lineage"):
        normalize_row({key: value for key, value in row.items() if key != "study_hash"})
