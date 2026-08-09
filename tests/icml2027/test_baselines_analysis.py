from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import yaml  # type: ignore[import-untyped]

from certgen.icml2027.analysis import cost_to_decision, deterministic_prefix_ids, samples_to_decision
from certgen.icml2027.baselines import BASELINES, run_baseline


def _bundle(path: Path) -> None:
    rng = np.random.default_rng(9)
    count = 40
    np.savez_compressed(
        path,
        reference=rng.normal(0, 1, (count, 4)),
        model_a=rng.normal(0.05, 1, (count, 4)),
        model_b=rng.normal(0.4, 1, (count, 4)),
        reference_ids=np.asarray([f"r{i}" for i in range(count)]),
        model_a_ids=np.asarray([f"a{i}" for i in range(count)]),
        model_b_ids=np.asarray([f"b{i}" for i in range(count)]),
        delta_stream=np.asarray([0.2] * 32),
    )


def test_all_baselines_run_on_identity_aligned_synthetic_features(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle.npz"
    _bundle(bundle)
    study = tmp_path / "study.yaml"
    study.write_text(
        yaml.safe_dump(
            {
                "alpha": 0.05,
                "master_seed": 4,
                "baseline_repetitions": 9,
                "family_size": 2,
                "true_mean": 0.2,
                "synthetic_validation_only": True,
                "claim_allowed": False,
            }
        ),
        encoding="utf-8",
    )
    for baseline_id in BASELINES:
        payload = run_baseline(baseline_id, bundle, study, tmp_path / f"{baseline_id}.json")
        assert payload["baseline_id"] == baseline_id
        assert payload["claim_allowed"] is False
        assert payload["sample_ids_hashes"]["reference"]


def test_prefixes_are_frozen_and_cost_types_do_not_mix(tmp_path: Path) -> None:
    ids = [f"s{i}" for i in range(20)]
    assert deterministic_prefix_ids(ids, 4) == ids[:4]
    input_path = tmp_path / "streams.json"
    input_path.write_text(
        json.dumps(
            [
                {
                    "method": "certgen_anytime",
                    "comparison": "a_vs_b",
                    "feature_space": "synthetic",
                    "alpha": 0.05,
                    "stopping_rule": "anytime",
                    "stream": [0.8] * 20,
                    "sample_ids": ids,
                }
            ]
        ),
        encoding="utf-8",
    )
    summary = samples_to_decision(input_path, tmp_path / "prefix.csv", prefixes=(4, 8, 20))
    assert summary["prefixes"] == [4, 8, 20]
    with (tmp_path / "prefix.csv").open(encoding="utf-8") as handle:
        assert all(row["outcome_adaptive_prefix_selection"] == "False" for row in csv.DictReader(handle))
    cost_path = tmp_path / "cost.json"
    cost_path.write_text(
        json.dumps(
            [
                {"study_id": "s", "stage": "cpu", "measurement_status": "measured", "CPU_seconds": 2.0},
                {"study_id": "s", "stage": "gpu", "measurement_status": "planning_estimate", "GPU_seconds": 3.0},
                {"study_id": "s", "stage": "unknown", "measurement_status": "unknown"},
            ]
        ),
        encoding="utf-8",
    )
    result = cost_to_decision(cost_path, tmp_path / "cost.csv")
    assert result["totals_kept_separate"]["measured"]["CPU_seconds"] == 2.0
    assert result["totals_kept_separate"]["planning_estimate"]["GPU_seconds"] == 3.0
