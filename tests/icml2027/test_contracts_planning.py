from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml  # type: ignore[import-untyped]

from certgen.icml2027.cache import build_cache_sidecar, validate_cache_sidecar
from certgen.icml2027.common import stable_hash
from certgen.icml2027.cross_family import CrossFamilyContract, conformance_smoke, validate_generated_batch
from certgen.icml2027.dinov2 import DinoV2Contract, validate_asset_manifest
from certgen.icml2027.evidence import audit_evidence
from certgen.icml2027.gates import audit_go_no_go
from certgen.icml2027.planning import plan_compute, plan_study_selection


def test_benchmark_independent_cache_round_trip(tmp_path: Path) -> None:
    features = tmp_path / "features.npz"
    ids = ["a", "b"]
    np.savez_compressed(features, features=np.ones((2, 3), dtype=np.float32), sample_ids=np.asarray(ids))
    metadata = {
        "benchmark_id": "fixture",
        "dataset_role": "reference",
        "source_manifest_hash": "a" * 64,
        "feature_space_id": "fixture",
        "extractor_revision": "r1",
        "preprocessing_hash": "b" * 64,
        "dtype": "float32",
        "dimension": 3,
        "row_order_hash": stable_hash(ids),
    }
    sidecar = tmp_path / "sidecar.json"
    payload = build_cache_sidecar(features, ids, ["c" * 64, "d" * 64], metadata, sidecar)
    assert payload["schema_version"] == "certgen.feature_cache.v3"
    assert validate_cache_sidecar(features, sidecar)["passed"]


def test_dinov2_and_cross_family_contracts_fail_closed(tmp_path: Path) -> None:
    contract = DinoV2Contract()
    assert contract.dimension == 768
    assert contract.revision == "f9e44c814b77203eaa57a6bdbbd535f21ede1415"
    asset = tmp_path / "asset"
    asset.mkdir()
    weight = asset / "model.safetensors"
    weight.write_bytes(b"fixture")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "model_identifier": contract.model_identifier,
                "revision": contract.revision,
                "license_status": "reviewed_approved",
                "files": [{"path": weight.name, "sha256": __import__("hashlib").sha256(weight.read_bytes()).hexdigest()}],
            }
        ),
        encoding="utf-8",
    )
    assert validate_asset_manifest(manifest, asset)["passed"]
    assert CrossFamilyContract().ddpm_pipeline_compatibility_assumed is False
    assert conformance_smoke()["status"] == "BLOCKED_REQUIRES_REAL_SOURCE_VERIFICATION"
    images: np.ndarray = np.zeros((2, 32, 32, 3), dtype=np.uint8)
    assert validate_generated_batch(images, [1, 2])["passed"]


def test_compute_selection_evidence_and_gate_planners(tmp_path: Path) -> None:
    compute_config = tmp_path / "compute.yaml"
    compute_config.write_text(
        yaml.safe_dump({"model_count": 2, "sample_count": 100, "gpu_count": 2, "session_limit_hours": 12, "planning_images_per_second": 2, "planning_extractor_throughput": 10}),
        encoding="utf-8",
    )
    compute = plan_compute(compute_config, tmp_path / "compute.json")
    assert compute["estimate_label"] == "PLANNING_ESTIMATE_NOT_MEASURED"
    criteria = [
        "scientific_value", "model_family_diversity", "benchmark_diversity", "public_availability", "license_clarity",
        "compute_cost", "released_sample_availability", "feature_compatibility", "preflight_complexity", "reviewer_value", "risk",
    ]
    selection_config = tmp_path / "selection.yaml"
    selection_config.write_text(
        yaml.safe_dump({"candidates": [{"candidate_id": "x", "scores": {name: 3 for name in criteria}, "gates": {}, "blocker": "blocked"}]}),
        encoding="utf-8",
    )
    selection = plan_study_selection(selection_config, tmp_path / "selection.csv")
    assert selection["ranked_candidates"][0]["go_no_go"] == "NO_GO"
    claims = tmp_path / "claims.yaml"
    claims.write_text(yaml.safe_dump({"claims": [{"claim_id": "c", "level": "C3", "evidence": [], "claim_allowed": False}]}), encoding="utf-8")
    assert not audit_evidence(claims, tmp_path / "claims.csv")["errors"]
    registry = tmp_path / "registry.yaml"
    registry.write_text(yaml.safe_dump({"records": [{"record_id": "x", "gates": {}, "blocker": "blocked"}]}), encoding="utf-8")
    gate = audit_go_no_go(registry, tmp_path / "gates.csv")
    assert gate["no_go"] == 1
