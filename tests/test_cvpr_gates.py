from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.core.io import write_json
from certgen.cvpr.contracts import configuration_hash
from certgen.cvpr.gates import run_metric_reproduction_gate, run_sanity_controls
from certgen.features.cache_v2 import SCHEMA_VERSION


def _write_cache(root: Path, *, role: str, values: np.ndarray) -> tuple[Path, Path, dict]:
    root.mkdir(parents=True)
    ids = [f"{role}-{index}" for index in range(len(values))]
    features_path = root / "features.npz"
    np.savez_compressed(features_path, features=values.astype(np.float32), sample_ids=np.asarray(ids))
    manifest = root / "manifest.jsonl"
    manifest.write_text(
        "\n".join(json.dumps({"sample_id": sample_id, "role": role}) for sample_id in ids) + "\n",
        encoding="utf-8",
    )
    extractor = {
        "name": "fixture",
        "resolved_model_id": "fixture/extractor",
        "resolved_revision": "a" * 40,
        "checkpoint_sha256": None,
        "package_versions": {"numpy": np.__version__},
        "output_layer": "pool",
        "feature_dim": int(values.shape[1]),
    }
    preprocessing = {
        "resize": "32x32",
        "interpolation": "none",
        "crop": "none",
        "color_mode": "rgb",
        "pixel_range": "0..1",
        "normalization": "none",
        "feature_normalization": "l2_in_metric",
    }
    sidecar_payload = {
        "schema_version": SCHEMA_VERSION,
        "cache_id": f"fixture-{role}",
        "role": role,
        "benchmark": {
            "dataset_id": "fixture",
            "split": "test",
            "source_manifest_path": "manifest.jsonl",
            "source_manifest_sha256": file_sha256(manifest),
        },
        "producer": {
            "model_or_generator_id": "reference" if role == "reference" else "fixture-generator",
            "checkpoint_or_revision": "fixture-v1",
            "checkpoint_sha256": None,
        },
        "extractor": extractor,
        "preprocessing": preprocessing,
        "array": {
            "path": "features.npz",
            "sha256": file_sha256(features_path),
            "dtype": "float32",
            "shape": list(values.shape),
            "features_key": "features",
            "sample_ids_key": "sample_ids",
            "ordered_sample_ids_sha256": stable_hash_json(ids),
        },
        "shard": {
            "shard_id": 0,
            "num_shards": 1,
            "selection_policy": "manifest_order",
            "input_shard_manifest_sha256": file_sha256(manifest),
        },
        "runtime": {
            "device": "cpu",
            "precision": "float32",
            "batch_size": len(values),
            "determinism_policy": "fixture",
            "created_by": "test",
            "created_at": "2026-07-13T00:00:00Z",
            "certgen_version": "0.5.0",
        },
        "source": {"license_status": "verified_test_fixture", "provenance_ledger_sha256": "b" * 64},
        "evidence": {"status": "synthetic_only", "claim_allowed": False},
    }
    sidecar_path = root / "features.v2.json"
    write_json(sidecar_payload, sidecar_path)
    return features_path, sidecar_path, sidecar_payload


def _independent_unbiased_rbf_mmd(x: np.ndarray, y: np.ndarray, gamma: float) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    x = x / np.linalg.norm(x, axis=1, keepdims=True)
    y = y / np.linalg.norm(y, axis=1, keepdims=True)

    def kernel(left: np.ndarray, right: np.ndarray) -> np.ndarray:
        return np.exp(-gamma * np.sum((left[:, None, :] - right[None, :, :]) ** 2, axis=2))

    kxx = kernel(x, x)
    kyy = kernel(y, y)
    kxy = kernel(x, y)
    return float(
        (kxx.sum() - np.trace(kxx)) / (len(x) * (len(x) - 1))
        + (kyy.sum() - np.trace(kyy)) / (len(y) * (len(y) - 1))
        - 2 * kxy.mean()
    )


def test_metric_reproduction_gate_binds_exact_inputs_and_cross_implementation_label(tmp_path: Path) -> None:
    reference = np.asarray([[1, 0, 1], [0, 1, 1], [1, 1, 0], [2, 1, 1]], dtype=np.float32)
    generated = np.asarray([[1, 0, 2], [0, 2, 1], [2, 1, 0], [2, 2, 1]], dtype=np.float32)
    ref_features, ref_sidecar, ref_payload = _write_cache(tmp_path / "reference", role="reference", values=reference)
    gen_features, gen_sidecar, _ = _write_cache(tmp_path / "generated", role="generated", values=generated)
    target = _independent_unbiased_rbf_mmd(reference, generated, 0.5)
    config = {
        "schema_version": "certgen.cvpr.metric_reproduction_config.v1",
        "gate_id": "fixture-metric",
        "run_id": "fixture-run",
        "reference_cache": {
            "features": str(ref_features),
            "sidecar": str(ref_sidecar),
            "artifact_root": str(ref_features.parent),
            "array_sha256": file_sha256(ref_features),
            "ordered_sample_ids_sha256": ref_payload["array"]["ordered_sample_ids_sha256"],
            "sample_count": 4,
            "role": "reference",
        },
        "generated_cache": {
            "features": str(gen_features),
            "sidecar": str(gen_sidecar),
            "artifact_root": str(gen_features.parent),
            "array_sha256": file_sha256(gen_features),
            "ordered_sample_ids_sha256": read_sidecar_ids_hash(gen_sidecar),
            "sample_count": 4,
            "role": "generated",
        },
        "metric": {
            "name": "unbiased_mmd2",
            "convention": "unbiased_u_statistic_full_pairwise",
            "feature_extractor_hash": stable_hash_json(ref_payload["extractor"]),
            "preprocessing_hash": stable_hash_json(ref_payload["preprocessing"]),
            "kernel": {"name": "rbf", "normalize": "l2", "gamma": 0.5},
        },
        "target": {
            "class": "cross_implementation_consistency",
            "implementation_id": "fixture_direct_numpy_formula",
            "provenance": "synthetic unit-test fixture, independently coded formula",
            "value": target,
            "tolerance_abs": 1e-7,
            "tolerance_rel": 1e-7,
        },
        "evidence_class": "synthetic_validation_only",
        "claim_allowed": False,
    }
    config["configuration_hash"] = configuration_hash(config)
    config_path = tmp_path / "metric.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    result = run_metric_reproduction_gate(config_path, tmp_path / "metric.json")
    assert result["status"] == "PASS", result["failure_reason"]
    assert result["reproduction_class"] == "cross_implementation_consistency"
    assert result["not_external_reproduction"] is True
    assert result["claim_allowed"] is False


def read_sidecar_ids_hash(path: Path) -> str:
    return str(json.loads(path.read_text(encoding="utf-8"))["array"]["ordered_sample_ids_sha256"])


def test_sanity_gate_runs_all_required_families_and_keeps_synthetic_boundary(tmp_path: Path) -> None:
    fields = ["preprocessing_hash", "feature_space", "bandwidth", "reference_population_hash"]
    ordinary_null_controls = [
        "reference_split_vs_reference_split",
        "same_model_independent_samples",
    ]
    protocol_null_controls = [
        "repeated_batching",
        "repeated_shard_merge",
    ]
    config = {
        "schema_version": "certgen.cvpr.sanity_gate_config.v1",
        "run_id": "fixture-sanity",
        "gates": [
            *[{"gate_id": name, "family": "null", "control_type": name, "inputs": {"fixture": True}, "measured_values": {"value": 0.001}, "tolerances": {"max_absolute": 0.01}} for name in ordinary_null_controls],
            *[{"gate_id": name, "family": "null", "control_type": name, "inputs": {"synthetic_validation_only": True}, "measured_values": {"maximum_feature_difference": 0.0, "metric_difference": 0.0}, "tolerances": {"maximum_feature_difference": 0.0, "metric_difference": 0.0}} for name in protocol_null_controls],
            {"gate_id": "reference_vs_severe_corruption", "family": "obvious_gap", "control_type": "reference_vs_severe_corruption", "inputs": {"fixture": True}, "measured_values": {"gap": 0.8}, "tolerances": {"minimum_gap": 0.5, "expected_sign": 1}},
            {"gate_id": "gaussian_blur_severity_ladder", "family": "direction", "control_type": "gaussian_blur_severity_ladder", "inputs": {"severities": [0.0, 0.5, 1.0, 2.0]}, "measured_values": {"ordered_values": [0.0, 0.1, 0.3, 0.9]}, "tolerances": {"expected_direction": "increasing", "minimum_aggregate_step": 0.5}},
            {"gate_id": "protocol", "family": "protocol", "control_type": "identity_mismatch_rejection", "inputs": {"cases": [{"mismatch_field": field, "baseline": {field: "a"}, "candidate": {field: "b"}} for field in fields]}, "measured_values": {}, "tolerances": {"all_mismatches_must_be_rejected": True}},
        ],
        "evidence_class": "synthetic_validation_only",
        "claim_allowed": False,
    }
    config["configuration_hash"] = configuration_hash(config)
    config_path = tmp_path / "sanity.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    result = run_sanity_controls(config_path, tmp_path / "sanity.json")
    assert result["status"] == "PASS", result["failure_reason"]
    assert result["summary"]["passed"] == 7
    assert result["synthetic_results_are_not_paper_evidence"] is True
    assert all(gate["claim_allowed"] is False for gate in result["gates"])
