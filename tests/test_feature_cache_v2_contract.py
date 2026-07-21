import copy
import json

import numpy as np

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.core.io import write_json
from certgen.features.cache_v2 import SCHEMA_VERSION, validate_feature_cache_v2


def _fixture(tmp_path):
    features = tmp_path / "features.npz"
    ids = ["r0", "r1", "r2", "r3"]
    np.savez_compressed(features, features=np.arange(12, dtype=np.float32).reshape(4, 3), sample_ids=np.asarray(ids))
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text("\n".join(json.dumps({"sample_id": item, "role": "reference"}) for item in ids) + "\n")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "cache_id": "fixture-reference",
        "role": "reference",
        "benchmark": {"dataset_id": "fixture", "split": "test", "source_manifest_path": "manifest.jsonl", "source_manifest_sha256": file_sha256(manifest)},
        "producer": {"model_or_generator_id": "reference", "checkpoint_or_revision": "dataset-v1", "checkpoint_sha256": None},
        "extractor": {"name": "fixture", "resolved_model_id": "fixture/model", "resolved_revision": "a" * 40, "checkpoint_sha256": None, "package_versions": {"numpy": np.__version__}, "output_layer": "pool", "feature_dim": 3},
        "preprocessing": {"resize": "32x32", "interpolation": "none", "crop": "none", "color_mode": "rgb", "pixel_range": "0..1", "normalization": "none", "feature_normalization": "none"},
        "array": {"path": "features.npz", "sha256": file_sha256(features), "dtype": "float32", "shape": [4, 3], "features_key": "features", "sample_ids_key": "sample_ids", "ordered_sample_ids_sha256": stable_hash_json(ids)},
        "shard": {"shard_id": 0, "num_shards": 1, "selection_policy": "manifest_order", "input_shard_manifest_sha256": file_sha256(manifest)},
        "runtime": {"device": "cpu", "precision": "float32", "batch_size": 4, "determinism_policy": "fixture", "created_by": "test", "created_at": "2026-07-11T00:00:00Z", "certgen_version": "0.5.0"},
        "source": {"license_status": "verified_test_fixture", "provenance_ledger_sha256": "b" * 64},
        "evidence": {"status": "synthetic_only", "claim_allowed": False},
    }
    sidecar = tmp_path / "features.v2.json"
    write_json(payload, sidecar)
    return features, sidecar, payload


def test_v2_cache_contract_accepts_exact_hash_bound_fixture(tmp_path):
    features, sidecar, _ = _fixture(tmp_path)
    result = validate_feature_cache_v2(features_path=features, sidecar_path=sidecar, artifact_root=tmp_path)
    assert result["passed"], result["errors"]
    assert result["claim_allowed"] is False


def test_v2_cache_contract_rejects_reordered_ids_and_tampered_array(tmp_path):
    features, sidecar, payload = _fixture(tmp_path)
    reordered = copy.deepcopy(payload)
    reordered["array"]["ordered_sample_ids_sha256"] = stable_hash_json(["r1", "r0", "r2", "r3"])
    write_json(reordered, sidecar)
    result = validate_feature_cache_v2(features_path=features, sidecar_path=sidecar, artifact_root=tmp_path)
    assert not result["passed"]
    assert any("SAMPLE_IDS_REORDERED" in error for error in result["errors"])
    np.savez_compressed(features, features=np.ones((4, 3), dtype=np.float32), sample_ids=np.asarray(["r0", "r1", "r2", "r3"]))
    result = validate_feature_cache_v2(features_path=features, sidecar_path=sidecar, artifact_root=tmp_path)
    assert not result["passed"]
    assert any("ARRAY_HASH_MISMATCH" in error or "EMPTY_CACHE" in error for error in result["errors"])


def test_v2_cache_contract_rejects_legacy_schema_and_claim_promotion(tmp_path):
    features, sidecar, payload = _fixture(tmp_path)
    payload["schema_version"] = "legacy"
    payload["evidence"]["claim_allowed"] = True
    write_json(payload, sidecar)
    result = validate_feature_cache_v2(features_path=features, sidecar_path=sidecar, artifact_root=tmp_path)
    assert not result["passed"]
    assert any("SCHEMA_VERSION_UNSUPPORTED" in error for error in result["errors"])
    assert any("EVIDENCE_BOUNDARY_INVALID" in error for error in result["errors"])
