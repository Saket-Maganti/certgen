from __future__ import annotations

import io
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from certgen.icml2027.common import stable_hash
from certgen.icml2027.dependency_lifecycle import (
    ensure_dependency_lifecycle,
    load_dependency_profile,
    validate_restart_marker,
)
from certgen.icml2027.execution_contract import (
    CONFIG_SHA256,
    REFERENCE_PLAN_SHA256,
    STUDY_HASH,
    STUDY_ID,
    build_execution_contract,
    build_feature_jobs,
    build_generation_jobs,
    build_generator_seed_manifest,
    seed_collision_audit,
    validate_feature_job_partition,
    validate_generation_job_partition,
    validate_generator_seed_manifest,
    validate_worker_spec,
)
from certgen.icml2027.payload import build_multipart_payload, validate_multipart_payload
from certgen.icml2027.scientific_closure import (
    classify_scenario,
    independent_paired_mmd_difference,
)
from certgen.metrics.streams import paired_mmd_difference_contributions


ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "registry/icml2027/dependency_profiles.json"


def _exact_versions(lane: str) -> dict[str, str]:
    profile = load_dependency_profile(lane, PROFILE_PATH)
    return {str(row["distribution"]): str(row["version"]) for row in profile["lock"]}


def _verify(_: object) -> dict[str, object]:
    return {"pip_check": "PASS", "imports": ["fixture"], "claim_allowed": False}


def test_dependency_marker_identity_restart_and_idempotence(tmp_path: Path) -> None:
    installed = _exact_versions("cifar_10k_generation")
    first = ensure_dependency_lifecycle(
        lane="cifar_10k_generation",
        input_zip_sha256="a" * 64,
        source_tree_sha256="b" * 64,
        profile_path=PROFILE_PATH,
        marker_path=tmp_path / "marker.json",
        report_path=tmp_path / "first.json",
        mode="USE_PREINSTALLED_VALIDATED",
        installed_versions_override=installed,
        verify_hook=_verify,
        python_version="fixture",
        platform_id="fixture",
    )
    second = ensure_dependency_lifecycle(
        lane="cifar_10k_generation",
        input_zip_sha256="a" * 64,
        source_tree_sha256="b" * 64,
        profile_path=PROFILE_PATH,
        marker_path=tmp_path / "marker.json",
        report_path=tmp_path / "second.json",
        mode="USE_PREINSTALLED_VALIDATED",
        installed_versions_override=installed,
        verify_hook=_verify,
        python_version="fixture",
        platform_id="fixture",
    )
    assert first["passed"] and not first["restart_required"]
    assert second["second_pass_identity_verified"] and not second["restart_required"]
    marker = json.loads((tmp_path / "marker.json").read_text())
    expected = dict(marker)
    expected["lane"] = "cifar_10k_features"
    assert not validate_restart_marker(marker, expected)["passed"]
    marker["source_tree_sha256"] = "0" * 64
    (tmp_path / "marker.json").write_text(json.dumps(marker))
    with pytest.raises(RuntimeError, match="stale or wrong"):
        ensure_dependency_lifecycle(
            lane="cifar_10k_generation",
            input_zip_sha256="a" * 64,
            source_tree_sha256="b" * 64,
            profile_path=PROFILE_PATH,
            marker_path=tmp_path / "marker.json",
            report_path=tmp_path / "stale.json",
            mode="USE_PREINSTALLED_VALIDATED",
            installed_versions_override=installed,
            verify_hook=_verify,
            python_version="fixture",
            platform_id="fixture",
        )


def test_dependency_install_offline_and_verification_failures(tmp_path: Path) -> None:
    calls: list[str] = []
    report = ensure_dependency_lifecycle(
        lane="cifar_10k_generation",
        input_zip_sha256="c" * 64,
        source_tree_sha256="d" * 64,
        profile_path=PROFILE_PATH,
        marker_path=tmp_path / "install.marker.json",
        report_path=tmp_path / "install.json",
        mode="PRIVATE_WHEELHOUSE_OFFLINE",
        wheelhouse=tmp_path,
        installed_versions_override={},
        install_hook=lambda _profile, mode, _wheelhouse: calls.append(mode),
        verify_hook=_verify,
    )
    assert report["restart_required"] and calls == ["PRIVATE_WHEELHOUSE_OFFLINE"]
    with pytest.raises(RuntimeError, match="preinstalled"):
        ensure_dependency_lifecycle(
            lane="cifar_10k_generation",
            input_zip_sha256="e" * 64,
            source_tree_sha256="f" * 64,
            profile_path=PROFILE_PATH,
            marker_path=tmp_path / "missing.marker.json",
            report_path=tmp_path / "missing.json",
            mode="USE_PREINSTALLED_VALIDATED",
            installed_versions_override={},
            verify_hook=_verify,
        )
    with pytest.raises(RuntimeError, match="pip check"):
        ensure_dependency_lifecycle(
            lane="cifar_10k_generation",
            input_zip_sha256="1" * 64,
            source_tree_sha256="2" * 64,
            profile_path=PROFILE_PATH,
            marker_path=tmp_path / "verify.marker.json",
            report_path=tmp_path / "verify.json",
            mode="USE_PREINSTALLED_VALIDATED",
            installed_versions_override=_exact_versions("cifar_10k_generation"),
            verify_hook=lambda _: (_ for _ in ()).throw(RuntimeError("pip check failure")),
        )


def test_seed_manifest_regeneration_separation_and_100k_collision_audit() -> None:
    manifest = build_generator_seed_manifest(count_per_model=100)
    validation = validate_generator_seed_manifest(manifest)
    assert validation["passed"] and validation["records"] == 200
    assert all(row["sample_id"] != str(row["generator_seed"]) for row in manifest["records"])
    assert seed_collision_audit()["passed"]
    mutated = json.loads(json.dumps(manifest))
    mutated["records"][0]["generator_seed"] += 1
    assert not validate_generator_seed_manifest(mutated)["passed"]


def test_generation_and_feature_partitions_fail_closed() -> None:
    manifest = build_generator_seed_manifest(count_per_model=100)
    jobs = build_generation_jobs(manifest, shard_size=50)
    assert validate_generation_job_partition(jobs, manifest)["passed"]
    assert not validate_generation_job_partition(jobs[:-1], manifest)["passed"]
    assert not validate_generation_job_partition([*jobs, jobs[0]], manifest)["passed"]
    source_hash = "a" * 64
    feature_jobs = build_feature_jobs(source_sample_order_sha256=source_hash, expected_shards=2)
    roles = ["reference", "google_ddpm_cifar10_candidate", "frank_ddpm_ema_cifar10_candidate"]
    assert validate_feature_job_partition(
        feature_jobs,
        required_extractors=["inception", "clip"],
        required_roles=roles,
        expected_shards=2,
        source_sample_order_sha256=source_hash,
    )["passed"]
    assert not validate_feature_job_partition(
        feature_jobs[:-1],
        required_extractors=["inception", "clip"],
        required_roles=roles,
        expected_shards=2,
        source_sample_order_sha256=source_hash,
    )["passed"]
    wrong = json.loads(json.dumps(feature_jobs))
    wrong[0]["extractor_id"] = "wrong"
    assert not validate_feature_job_partition(
        wrong,
        required_extractors=["inception", "clip"],
        required_roles=roles,
        expected_shards=2,
        source_sample_order_sha256=source_hash,
    )["passed"]


def test_worker_spec_scientific_identity_mutations_fail() -> None:
    manifest = build_generator_seed_manifest(count_per_model=100)
    contract = build_execution_contract(manifest, root=ROOT)
    spec = {
        "schema_version": "certgen.icml2027.worker_spec.v1",
        "lane": "cifar_10k_generation",
        "study_id": STUDY_ID,
        "study_hash": STUDY_HASH,
        "configuration_sha256": CONFIG_SHA256,
        "input_package_sha256": "a" * 64,
        "reference_plan_sha256": REFERENCE_PLAN_SHA256,
        "model_revisions": {},
        "extractor_revisions": {},
        "preprocessing_hashes": {},
        "seed_plan_sha256": contract["seed_plan_sha256"],
        "sample_identity_policy_sha256": contract["sample_identity_policy_sha256"],
        "expected_prefix_hashes": {},
        "expected_sample_count": 200,
        "expected_shard_count": 4,
        "expected_shard_coverage": {},
        "output_schema_version": "certgen.icml2027.generation_payload.v1",
        "claim_allowed": False,
    }
    assert validate_worker_spec(spec, expected_lane=spec["lane"], contract=contract)["passed"]
    for field in ("study_hash", "configuration_sha256", "seed_plan_sha256", "sample_identity_policy_sha256"):
        mutated = dict(spec)
        mutated[field] = "0" * 64
        assert not validate_worker_spec(mutated, expected_lane=spec["lane"], contract=contract)["passed"]


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.fromarray(np.zeros((4, 4, 3), dtype=np.uint8), mode="RGB").save(buffer, format="PNG")
    return buffer.getvalue()


def _generation_payload(tmp_path: Path) -> dict[str, object]:
    image = _png_bytes()
    record = {
        "sample_id": "sample-a",
        "model_id": "model-a",
        "checkpoint_id": "fixture/model-a",
        "checkpoint_revision": "rev-a",
        "generator_seed": 7,
        "image_path": "images/sample-a.png",
        "image_sha256": __import__("hashlib").sha256(image).hexdigest(),
        "shard_id": 0,
        "claim_allowed": False,
    }
    identity = {
        "input_package_sha256": "1" * 64,
        "study_id": STUDY_ID,
        "study_hash": STUDY_HASH,
        "configuration_sha256": CONFIG_SHA256,
        "worker_spec_sha256": "2" * 64,
        "source_tree_sha256": "3" * 64,
        "dependency_lock_sha256": "4" * 64,
        "model_revisions": {},
        "extractor_revisions": {},
        "preprocessing_hashes": {},
        "reference_plan_sha256": REFERENCE_PLAN_SHA256,
        "seed_manifest_sha256": "5" * 64,
        "claim_allowed": False,
    }
    return build_multipart_payload(
        lane="cifar_10k_generation",
        payload_type="generation",
        parts=[{"images/sample-a.png": image, "manifests/shard.jsonl": b"{}\n"}],
        records=[record],
        identity=identity,
        out_dir=tmp_path,
        basename="fixture",
    )


def test_multipart_integrity_missing_corrupt_and_identity(tmp_path: Path) -> None:
    payload = _generation_payload(tmp_path)
    index_path = Path(str(payload["index_path"]))
    assert validate_multipart_payload(index_path, expected_type="generation")["passed"]
    assert validate_multipart_payload(index_path, expected_identity={"study_hash": STUDY_HASH})["passed"]
    with pytest.raises(ValueError, match="identity"):
        validate_multipart_payload(index_path, expected_identity={"study_hash": "0" * 64})
    part = tmp_path / "fixture.part000.zip"
    original = part.read_bytes()
    part.write_bytes(original + b"corrupt")
    with pytest.raises(ValueError, match="corrupt"):
        validate_multipart_payload(index_path)
    part.write_bytes(original)
    part.rename(tmp_path / "missing.zip")
    with pytest.raises(FileNotFoundError, match="missing"):
        validate_multipart_payload(index_path)


def test_feature_payload_completeness_and_row_order(tmp_path: Path) -> None:
    ids = ["a", "b"]
    features: np.ndarray = np.arange(6, dtype=np.float32).reshape(2, 3)
    buffer = io.BytesIO()
    np.savez_compressed(buffer, features=features, sample_ids=np.asarray(ids))
    sidecar = {
        "sample_ids": ids,
        "extractor_id": "fixture",
        "extractor_revision": "v1",
        "preprocessing_sha256": "a" * 64,
        "dimension": 3,
        "dtype": "float32",
        "claim_allowed": False,
    }
    record = {
        "extractor_id": "fixture",
        "extractor_revision": "v1",
        "preprocessing_sha256": "a" * 64,
        "feature_path": "features/shard.npz",
        "sidecar_path": "sidecars/shard.json",
        "dimension": 3,
        "dtype": "float32",
        "row_count": 2,
        "source_sample_ids_sha256": stable_hash(ids),
        "claim_allowed": False,
    }
    payload = build_multipart_payload(
        lane="cifar_10k_features",
        payload_type="features",
        parts=[
            {
                "features/shard.npz": buffer.getvalue(),
                "sidecars/shard.json": json.dumps(sidecar, sort_keys=True).encode(),
            }
        ],
        records=[record],
        identity={
            "input_package_sha256": "1" * 64,
            "study_id": STUDY_ID,
            "study_hash": STUDY_HASH,
            "configuration_sha256": CONFIG_SHA256,
            "worker_spec_sha256": "2" * 64,
            "source_tree_sha256": "3" * 64,
            "dependency_lock_sha256": "4" * 64,
            "model_revisions": {},
            "extractor_revisions": {"fixture": "v1"},
            "preprocessing_hashes": {"fixture": "a" * 64},
            "reference_plan_sha256": REFERENCE_PLAN_SHA256,
            "seed_manifest_sha256": "5" * 64,
            "claim_allowed": False,
        },
        out_dir=tmp_path,
        basename="feature",
    )
    assert validate_multipart_payload(payload["index_path"], expected_type="features")["passed"]


def test_dino_robustness_only_payload_gate(tmp_path: Path) -> None:
    payload = _generation_payload(tmp_path)
    index = json.loads(Path(str(payload["index_path"])).read_text())
    index["lane"] = "dinov2_features"
    index["payload_index_sha256"] = stable_hash({key: value for key, value in index.items() if key != "payload_index_sha256"})
    Path(str(payload["index_path"])).write_text(json.dumps(index))
    with pytest.raises(ValueError, match="robustness-only"):
        validate_multipart_payload(str(payload["index_path"]))


def test_normalization_classification_and_independent_mmd() -> None:
    assert classify_scenario("scale_shift") == "INVARIANCE_CONTROL"
    assert classify_scenario("variance_inflation") == "INVARIANCE_CONTROL"
    rng = np.random.default_rng(2027)
    arrays = [rng.normal(size=(20, 7)).astype(np.float32) for _ in range(3)]
    order = rng.permutation(20)
    independent = independent_paired_mmd_difference(*arrays, indices=order)
    production = paired_mmd_difference_contributions(
        *arrays, {"name": "rbf", "gamma": 0.5, "normalize": "l2"}, indices=order
    )
    np.testing.assert_allclose(independent, production, rtol=0, atol=1e-12)


def test_probability_space_contract_and_no_external_restart_marker() -> None:
    probability = ROOT / "docs/icml2027/theory/GENERATOR_RANDOMIZATION_AND_PROBABILITY_SPACE.md"
    text = probability.read_text(encoding="utf-8")
    assert "Dirac measure" in text and "filtration" in text.lower() and "claim_allowed=false" in text
    notebook_factory = (ROOT / "certgen/icml2027/notebooks.py").read_text(encoding="utf-8")
    assert "ensure_dependency_lifecycle" in notebook_factory
    assert "dependency bootstrap/restart marker is required" not in notebook_factory
