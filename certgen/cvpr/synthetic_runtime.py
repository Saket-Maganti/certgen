"""End-to-end local synthetic validation of the canonical runtime contracts."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import yaml  # type: ignore[import-untyped]
from PIL import Image

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.core.io import write_json
from certgen.cvpr.certificate import certify_feature_bundle
from certgen.cvpr.contracts import atomic_write_json, configuration_hash
from certgen.cvpr.gates import run_metric_reproduction_gate, run_sanity_controls
from certgen.cvpr.image_manifest import write_image_manifest
from certgen.cvpr.fingerprint import REQUIRED_INPUTS, build_reproducibility_fingerprint
from certgen.cvpr.feature_merge import merge_feature_run
from certgen.cvpr.output_schemas import expected_output_schema
from certgen.cvpr.package import build_notebook_input_package, inspect_notebook_input_package
from certgen.cvpr.ranking import build_partial_ranking
from certgen.cvpr.registries import build_family_record, write_frozen_family
from certgen.features.cache_v2 import SCHEMA_VERSION, validate_feature_cache_v2
from certgen.features.protocol_checks import compare_feature_runs
from certgen.notebooks.kaggle_io import deterministic_zip, write_integrity_manifest
from certgen.notebooks.model_assets import AssetPolicy, AssetRequirement, inventory_cache, validate_asset_manifest
from certgen.notebooks.subprocess_orchestrator import WorkerSpec, run_workers
from certgen.packaging.v9_import_repair import import_repair
from certgen.stats.reference_sampling import build_reference_draw_plan
from certgen.visualization.factory import validate_figure_request


def _write_cache(root: Path, role: str, values: np.ndarray) -> tuple[Path, Path, dict[str, Any]]:
    root.mkdir(parents=True)
    ids = [f"{role}-{index:04d}" for index in range(len(values))]
    features = root / "features.npz"
    np.savez_compressed(features, features=values.astype(np.float32), sample_ids=np.asarray(ids))
    manifest = root / "manifest.jsonl"
    manifest.write_text("".join(json.dumps({"sample_id": sample_id, "role": role}) + "\n" for sample_id in ids), encoding="utf-8")
    extractor = {"name": "fixture", "resolved_model_id": "fixture/extractor", "resolved_revision": "fixture-v1", "checkpoint_sha256": None, "package_versions": {"numpy": np.__version__}, "output_layer": "rgb_mean_std", "feature_dim": int(values.shape[1])}
    preprocessing = {"resize": "8x8", "interpolation": "none", "crop": "none", "color_mode": "rgb", "pixel_range": "0..1", "normalization": "none", "feature_normalization": "l2_in_metric"}
    sidecar = {
        "schema_version": SCHEMA_VERSION,
        "cache_id": f"synthetic-{role}",
        "role": role,
        "benchmark": {"dataset_id": "synthetic_fixture", "split": "fixture", "source_manifest_path": "manifest.jsonl", "source_manifest_sha256": file_sha256(manifest)},
        "producer": {"model_or_generator_id": "synthetic-reference" if role == "reference" else "fixture_model", "checkpoint_or_revision": "fixture-v1", "checkpoint_sha256": None},
        "extractor": extractor,
        "preprocessing": preprocessing,
        "array": {"path": "features.npz", "sha256": file_sha256(features), "dtype": "float32", "shape": list(values.shape), "features_key": "features", "sample_ids_key": "sample_ids", "ordered_sample_ids_sha256": stable_hash_json(ids)},
        "shard": {"shard_id": 0, "num_shards": 1, "selection_policy": "fixture_manifest_order", "input_shard_manifest_sha256": file_sha256(manifest)},
        "runtime": {"device": "cpu", "precision": "float32", "batch_size": len(values), "determinism_policy": "fixture", "created_by": "certgen.cvpr.synthetic_runtime", "created_at": "deterministic_fixture", "certgen_version": "0.5.0"},
        "source": {"license_status": "verified_synthetic_fixture", "provenance_ledger_sha256": "f" * 64},
        "evidence": {"status": "synthetic_validation_only", "claim_allowed": False},
    }
    sidecar_path = root / "features.v2.json"
    write_json(sidecar, sidecar_path)
    return features, sidecar_path, sidecar


def _feature_vector(path: Path) -> np.ndarray:
    pixels = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
    return np.concatenate([pixels.mean(axis=(0, 1)), pixels.std(axis=(0, 1)), np.asarray([0.01], dtype=np.float32)])


def _metric_config(reference: tuple[Path, Path, dict[str, Any]], generated: tuple[Path, Path, dict[str, Any]]) -> dict[str, Any]:
    from certgen.metrics.mmd import unbiased_mmd2

    ref_features = np.load(reference[0], allow_pickle=False)["features"]
    gen_features = np.load(generated[0], allow_pickle=False)["features"]
    target = unbiased_mmd2(ref_features, gen_features, kernel="rbf", normalize="l2", gamma=0.5)
    def artifact_root(cache: tuple[Path, Path, dict[str, Any]]) -> Path:
        relative = Path(str(cache[2]["array"]["path"]))
        for parent in cache[0].parents:
            if (parent / relative).resolve() == cache[0].resolve():
                return parent
        raise ValueError("synthetic cache has no portable artifact root")

    payload = {
        "schema_version": "certgen.cvpr.metric_reproduction_config.v1", "gate_id": "synthetic-runtime-metric", "run_id": "synthetic-runtime",
        "reference_cache": {"features": str(reference[0]), "sidecar": str(reference[1]), "artifact_root": str(artifact_root(reference)), "array_sha256": file_sha256(reference[0]), "ordered_sample_ids_sha256": reference[2]["array"]["ordered_sample_ids_sha256"], "sample_count": len(ref_features), "role": "reference"},
        "generated_cache": {"features": str(generated[0]), "sidecar": str(generated[1]), "artifact_root": str(artifact_root(generated)), "array_sha256": file_sha256(generated[0]), "ordered_sample_ids_sha256": generated[2]["array"]["ordered_sample_ids_sha256"], "sample_count": len(gen_features), "role": generated[2]["role"]},
        "metric": {"name": "unbiased_mmd2", "convention": "unbiased_u_statistic_full_pairwise", "feature_extractor_hash": stable_hash_json(reference[2]["extractor"]), "preprocessing_hash": stable_hash_json(reference[2]["preprocessing"]), "kernel": {"name": "rbf", "normalize": "l2", "gamma": 0.5}},
        "target": {"class": "cross_implementation_consistency", "implementation_id": "synthetic-runtime-direct", "provenance": "deterministic synthetic fixture", "value": target, "tolerance_abs": 1e-7, "tolerance_rel": 1e-7},
        "evidence_class": "synthetic_validation_only", "claim_allowed": False,
    }
    payload["configuration_hash"] = configuration_hash(payload)
    return payload


def _sanity_config() -> dict[str, Any]:
    ordinary_nulls = ["reference_split_vs_reference_split", "same_model_independent_samples"]
    protocol_nulls = ["repeated_batching", "repeated_shard_merge"]
    fields = ["preprocessing_hash", "feature_space", "bandwidth", "reference_population_hash"]
    payload = {
        "schema_version": "certgen.cvpr.sanity_gate_config.v1", "run_id": "synthetic-runtime",
        "gates": [
            *[{"gate_id": name, "family": "null", "control_type": name, "inputs": {"fixture": True}, "measured_values": {"value": 0.001}, "tolerances": {"max_absolute": 0.01}} for name in ordinary_nulls],
            *[{"gate_id": name, "family": "null", "control_type": name, "inputs": {"synthetic_validation_only": True}, "measured_values": {"maximum_feature_difference": 0.0, "metric_difference": 0.0}, "tolerances": {"maximum_feature_difference": 0.0, "metric_difference": 0.0}} for name in protocol_nulls],
            {"gate_id": "reference_vs_severe_corruption", "family": "obvious_gap", "control_type": "reference_vs_severe_corruption", "inputs": {"fixture": True}, "measured_values": {"gap": 0.8}, "tolerances": {"minimum_gap": 0.5, "expected_sign": 1}},
            {"gate_id": "gaussian_blur_severity_ladder", "family": "direction", "control_type": "gaussian_blur_severity_ladder", "inputs": {"severities": [0.0, 0.5, 1.0, 2.0]}, "measured_values": {"ordered_values": [0.0, 0.1, 0.3, 0.9]}, "tolerances": {"expected_direction": "increasing", "minimum_aggregate_step": 0.5}},
            {"gate_id": "protocol", "family": "protocol", "control_type": "identity_mismatch_rejection", "inputs": {"cases": [{"mismatch_field": field, "baseline": {field: "a"}, "candidate": {field: "b"}} for field in fields]}, "measured_values": {}, "tolerances": {"all_mismatches_must_be_rejected": True}},
        ],
        "evidence_class": "synthetic_validation_only", "claim_allowed": False,
    }
    payload["configuration_hash"] = configuration_hash(payload)
    return payload


def run_synthetic_runtime(output_dir: str | Path) -> dict[str, Any]:
    root = Path(output_dir)
    if root.exists():
        raise FileExistsError(f"refusing to overwrite synthetic runtime: {root}")
    root.mkdir(parents=True)
    stages: dict[str, Any] = {}

    reference_images = root / "reference_images"
    reference_images.mkdir()
    for index in range(8):
        Image.new("RGB", (8, 8), (20 + index, 40 + index, 60 + index)).save(reference_images / f"reference_{index:04d}.png")
    reference_manifest = root / "synthetic_reference_manifest.jsonl"
    reference_manifest.write_text(
        "".join(json.dumps({"sample_id": f"reference-{index:04d}", "path": f"reference_images/reference_{index:04d}.png"}) + "\n" for index in range(8)),
        encoding="utf-8",
    )
    stages["01_synthetic_reference"] = {"status": "PASS", "count": 8}

    cache = root / "fake_asset_cache"
    (cache / "weights").mkdir(parents=True)
    (cache / "weights" / "fixture.bin").write_bytes(b"synthetic fixture only")
    requirement = AssetRequirement("fixture_asset", "fixture_model", "fixture-v1", "local/synthetic", "verified_synthetic_fixture", False, ("weights/fixture.bin",))
    asset_manifest = inventory_cache(requirement, cache, AssetPolicy.OFFLINE_PACKAGED_CACHE)
    validate_asset_manifest(asset_manifest, cache_root=cache)
    atomic_write_json(asset_manifest, root / "model_asset_manifest.json")
    smoke_dir = root / "fake_model_preflight" / "smoke_images"
    smoke_dir.mkdir(parents=True)
    Image.new("RGB", (8, 8), (1, 2, 3)).save(smoke_dir / "smoke_00.png")
    atomic_write_json({"status_code": "PREFLIGHT_PASS", "smoke_sha256": file_sha256(smoke_dir / "smoke_00.png"), "claim_allowed": False}, root / "fake_model_preflight" / "status.json")
    stages["02_fake_model_preflight_with_smoke_images"] = {"status": "PASS", "policy": asset_manifest["policy"]}
    atomic_write_json({"status_code": "EXTRACTOR_PREFLIGHT_PASS", "output_dimension": 7, "safe_batch_size": 4, "finite": True, "claim_allowed": False}, root / "fake_extractor_preflight.json")
    stages["03_fake_extractor_preflight"] = {"status": "PASS", "dimension": 7}

    preflight_fixture = root / "preflight_fixture"
    preflight_fixture.mkdir()
    atomic_write_json({"status_code": "PREFLIGHT_PASS", "claim_allowed": False}, preflight_fixture / "status.json")
    generation_config_payload = {
        "kind": "generation", "run_id": "synthetic__generation__1k__none__fixture__run",
        "mode": "force_new_run", "benchmark_id": "cifar10", "scale": "1k",
        "asset_policy": "OFFLINE_PACKAGED_CACHE", "network_mode": "ONLINE_DEPENDENCIES_OFFLINE_ASSETS",
        "dependency_network_allowed": True, "model_asset_network_allowed": False,
        "requested_gpu_count": 2, "allow_single_gpu_fallback": False,
        "preflight_configuration_hash": "p" * 64, "output_schema_version": expected_output_schema("generation")["schema_version"],
        "reference_manifest_hash": file_sha256(reference_manifest), "asset_manifest_hash": "a" * 64,
        "samples_per_model": 8,
        "models": [{"model_id": "fixture_model", "revision": "fixture-v1"}],
        "seed_shards": {"fixture_model": [[0, 2, 4, 6], [1, 3, 5, 7]]},
        "claim_allowed": False,
    }
    generation_config_payload["configuration_hash"] = stable_hash_json(generation_config_payload)
    generation_package_config = root / "generation_package_config.yaml"
    generation_package_config.write_text(yaml.safe_dump(generation_config_payload, sort_keys=False), encoding="utf-8")
    generation_package = build_notebook_input_package(kind="generation", config_path=generation_package_config, inputs={"preflight": preflight_fixture}, out_zip=root / "synthetic_generation_input.zip", manifest_out=root / "synthetic_generation_input.json")
    if not inspect_notebook_input_package(generation_package["zip_path"])["passed"]:
        raise RuntimeError("synthetic generation input package failed inspection")
    stages["04_generation_config_package"] = {"status": "PASS", "sha256": generation_package["zip_sha256"]}

    generation = root / "generation_export"
    orchestrator = root / "orchestration"
    specs = []
    for index, seeds in enumerate(([0, 2, 4, 6], [1, 3, 5, 7])):
        shard = f"shard_{index:04d}"
        out = generation / "per_model" / "fixture_model" / "per_shard" / shard
        specs.append(WorkerSpec(f"fixture_model__{shard}", "certgen.notebooks.workers.fake_generation_worker", index, f"fixture_model__{shard}", ("--out", str(out), "--seeds", ",".join(map(str, seeds)), "--config-hash", "a" * 64, "--shard-id", shard, "--oom-above", "2"), str(out / "worker_status.json")))
    first = run_workers(specs, output_dir=orchestrator, timeout_seconds=30)
    resumed = run_workers(specs, output_dir=root / "orchestration_resume", timeout_seconds=30, resume=True)
    if first["status"] != "COMPLETE" or any(row["status"] != "REUSED_VALID_COMPLETION" for row in resumed["workers"]):
        raise RuntimeError("synthetic two-worker generation/resume failed")
    stages["05_two_gpu_queue_simulation"] = {"status": "PASS", "queues": 2, "one_active_per_gpu": True}
    stages["06_batched_fake_generation"] = {"status": "PASS", "workers": 2, "resume": "PASS"}
    shutil.copy2(generation_package_config, generation / "configuration.yaml")
    atomic_write_json(
        {
            "run_id": generation_config_payload["run_id"],
            "configuration_hash": generation_config_payload["configuration_hash"],
            "input_manifest_hash": generation_config_payload["reference_manifest_hash"],
            "asset_manifest_hash": generation_config_payload["asset_manifest_hash"],
            "claim_allowed": False,
        },
        generation / "run_identity.json",
    )
    root_generation_status = {"status_code": "GENERATION_COMPLETE", "output_schema_version": expected_output_schema("generation")["schema_version"], "configuration_hash": generation_config_payload["configuration_hash"], "passed": True, "expected_workers": [spec.worker_id for spec in specs], "completed_workers": [spec.worker_id for spec in specs], "evidence_class": "synthetic_validation_only", "claim_allowed": False}
    atomic_write_json(root_generation_status, generation / "generation_status.json")
    atomic_write_json(root_generation_status, generation / "status.json")
    (generation / "copyback_instructions.md").write_text("not paper evidence; claim_allowed=false\n", encoding="utf-8")
    write_integrity_manifest(generation)
    zip_path = root / "synthetic_generation.zip"
    deterministic_zip(generation, zip_path)
    stages["07_generation_output_zip"] = {"status": "PASS", "sha256": file_sha256(zip_path)}
    imported = import_repair(kind="generation", zip_path=zip_path, out_dir=root / "imported_generation", out_json=root / "generation_import.json", out_report=root / "generation_import.md", registry_path=root / "artifact_registry.jsonl")
    if not imported["passed"]:
        raise RuntimeError("synthetic secure import failed: " + "; ".join(imported["errors"]))
    stages["08_canonical_generation_import"] = {"status": "PASS", "import": "PASS"}

    preprocessing_contract = {
        "extractor_id": "fixture", "model_identifier": "fixture/extractor", "revision": "fixture-v1",
        "processor_class": "FixtureProcessor", "input_resolution": 8, "resize_size": 8, "crop_size": 8,
        "crop_mode": "none", "interpolation": "nearest", "antialias": True, "pixel_range": "0..1",
        "channel_order": "RGB", "mean": [0.0, 0.0, 0.0], "std": [1.0, 1.0, 1.0],
        "feature_normalization": "none", "precision": "float32", "output_dimension": 7,
        "package_versions": {"numpy": np.__version__},
    }
    feature_extractors = [
        {"feature_space_id": name, "revision": f"{name}-fixture-v1", "expected_preprocessing": preprocessing_contract}
        for name in ("inception", "clip", "dinov2")
    ]
    feature_config_payload = {
        "kind": "features", "run_id": "synthetic__features__1k__none__fixture__run", "mode": "force_new_run",
        "benchmark_id": "cifar10", "scale": "1k", "asset_policy": "OFFLINE_PACKAGED_CACHE",
        "network_mode": "ONLINE_DEPENDENCIES_OFFLINE_ASSETS", "dependency_network_allowed": True,
        "model_asset_network_allowed": False, "requested_gpu_count": 2, "allow_single_gpu_fallback": False,
        "output_schema_version": expected_output_schema("feature")["schema_version"],
        "extractors": feature_extractors,
        "image_shards": [{"shard_id": "reference_shard", "role": "reference", "indices": list(range(8))}, {"shard_id": "generated_shard", "role": "generated", "indices": list(range(8, 16))}],
        "source_manifest_hash": file_sha256(reference_manifest), "reference_draw_plan": {"fixture": True},
        "reference_draw_plan_hash": stable_hash_json({"fixture": True}),
        "expected_role_counts": {"reference": 8, "generated": 8}, "expected_model_ids": ["reference", "fixture_model"],
        "feature_input_mode": "EMBED_IMAGES_IN_PACKAGE", "image_root": ".",
        "image_manifest_schema_version": "certgen.cvpr.image_manifest.v1",
        "study_hash": "b" * 64,
        "claim_allowed": False,
    }
    feature_config_payload["configuration_hash"] = stable_hash_json(feature_config_payload)
    feature_package_config = root / "feature_package_config.yaml"
    feature_package_config.write_text(yaml.safe_dump(feature_config_payload, sort_keys=False), encoding="utf-8")
    feature_manifest_input = root / "feature_images.jsonl"
    packaged_images = root / "feature_package_images"
    rows: list[dict[str, Any]] = []
    source_hash = file_sha256(reference_manifest)
    generated_images = sorted(generation.glob("per_model/*/per_shard/*/images/*.png"))
    for role, model_id, images in (
        ("reference", "reference", sorted(reference_images.glob("*.png"))),
        ("model", "fixture_model", generated_images),
    ):
        for index, source in enumerate(images):
            destination = packaged_images / ("reference" if role == "reference" else model_id) / source.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            rows.append(
                {
                    "sample_id": f"{role}-{index:04d}",
                    "role": role,
                    "model_id": model_id,
                    "relative_image_path": f"images/{destination.relative_to(packaged_images).as_posix()}",
                    "image_hash": file_sha256(destination),
                    "seed": index if role == "model" else None,
                    "prompt_or_class_id": None,
                    "width": 8,
                    "height": 8,
                    "mode": "RGB",
                    "source_run_id": "synthetic-runtime",
                    "source_manifest_hash": source_hash,
                }
            )
    write_image_manifest(rows, feature_manifest_input, decode=False)
    feature_package = build_notebook_input_package(kind="features", config_path=feature_package_config, inputs={"manifests/images.jsonl": feature_manifest_input, "images": packaged_images}, out_zip=root / "synthetic_feature_input.zip", manifest_out=root / "synthetic_feature_input.json")
    if not inspect_notebook_input_package(feature_package["zip_path"])["passed"]:
        raise RuntimeError("synthetic feature input package failed inspection")
    stages["09_feature_config_package"] = {"status": "PASS", "sha256": feature_package["zip_sha256"]}

    reference_values = np.stack([_feature_vector(path) for path in sorted(reference_images.glob("*.png"))])
    generated_values = np.stack([_feature_vector(path) for path in generated_images])
    feature_export = root / "feature_export"
    feature_workers: list[str] = []
    for role, model_id, values in (("reference", "reference", reference_values), ("generated", "fixture_model", generated_values)):
        worker_id = f"fixture__{role}_shard"
        feature_workers.append(worker_id)
        feature_shard_path = feature_export / "shards" / "fixture" / f"{role}_shard"
        feature_shard_path.mkdir(parents=True)
        ids = [f"{role}-{index:04d}" for index in range(len(values))]
        np.savez_compressed(feature_shard_path / "features.npz", features=values.astype(np.float32), sample_ids=np.asarray(ids))
        sidecar = {
            "schema_version": "certgen.feature_shard.v2", "extractor_id": "fixture", "extractor_revision": "fixture-v1",
            "configuration_hash": feature_config_payload["configuration_hash"], "preprocessing_hash": stable_hash_json(preprocessing_contract),
            "array_sha256": file_sha256(feature_shard_path / "features.npz"), "rows": len(ids), "dimension": 7,
            "sample_order_hash": stable_hash_json(ids), "role": role, "model_id": model_id,
            "source_manifest_hash": file_sha256(reference_manifest), "expected_preprocessing": preprocessing_contract,
            "resolved_model_id": "fixture/extractor", "resolved_revision": "fixture-v1", "source_license": "verified_synthetic_fixture",
            "runtime": {"device": "fixture_cpu", "precision": "float32", "batch_size": 4, "determinism_policy": "fixture", "package_versions": {"numpy": np.__version__}},
            "protocol_checks": {
                "repeated_batching": {
                    "schema_version": "certgen.feature_repeated_batching.v1",
                    "batch_sizes": [1, 4],
                    "ordered_sample_ids": ids,
                    **compare_feature_runs(
                        ids,
                        values.astype(np.float32),
                        ids,
                        values.astype(np.float32).copy(),
                        maximum_feature_difference=0.0,
                        maximum_metric_difference=0.0,
                    ),
                }
            },
            "claim_allowed": False,
        }
        atomic_write_json(sidecar, feature_shard_path / "sidecar.json")
        atomic_write_json({"status_code": "FEATURE_SHARD_COMPLETE", "claim_allowed": False}, feature_shard_path / "status.json")
    stages["10_fake_feature_extraction"] = {"status": "PASS", "workers": len(feature_workers)}
    shutil.copy2(feature_package_config, feature_export / "configuration.yaml")
    atomic_write_json(
        {
            "run_id": feature_config_payload["run_id"],
            "configuration_hash": feature_config_payload["configuration_hash"],
            "input_manifest_hash": feature_config_payload["source_manifest_hash"],
            "asset_manifest_hash": "f" * 64,
            "claim_allowed": False,
        },
        feature_export / "run_identity.json",
    )
    root_feature_status = {"status_code": "FEATURE_EXTRACTION_SHARDS_COMPLETE", "output_schema_version": expected_output_schema("feature")["schema_version"], "configuration_hash": feature_config_payload["configuration_hash"], "passed": True, "expected_workers": feature_workers, "completed_workers": feature_workers, "claim_allowed": False}
    atomic_write_json(root_feature_status, feature_export / "feature_extraction_status.json")
    atomic_write_json(root_feature_status, feature_export / "status.json")
    (feature_export / "copyback_instructions.md").write_text("not paper evidence; claim_allowed=false\n", encoding="utf-8")
    write_integrity_manifest(feature_export)
    feature_zip = root / "synthetic_features.zip"
    deterministic_zip(feature_export, feature_zip)
    stages["11_feature_output_zip"] = {"status": "PASS", "sha256": file_sha256(feature_zip)}
    feature_import = import_repair(kind="feature", zip_path=feature_zip, out_dir=root / "imported_features", out_json=root / "feature_import.json", out_report=root / "feature_import.md", registry_path=root / "artifact_registry.jsonl")
    if not feature_import["passed"]:
        raise RuntimeError("synthetic feature import failed: " + "; ".join(feature_import["errors"]))
    stages["12_canonical_feature_import"] = {"status": "PASS"}
    merged = merge_feature_run(root / "imported_features", output_root=root / "merged_features", registry_path=root / "artifact_registry.jsonl")
    stages["13_feature_merge"] = {"status": "PASS", "groups": merged["groups"]}
    merged_root = Path(merged["output_dir"])
    reference_features = merged_root / "fixture" / "reference" / "features.npz"
    reference_sidecar = merged_root / "fixture" / "reference" / "sidecar.json"
    generated_features = merged_root / "fixture" / "generated" / "features.npz"
    generated_sidecar = merged_root / "fixture" / "generated" / "sidecar.json"
    reference_cache = (reference_features, reference_sidecar, json.loads(reference_sidecar.read_text(encoding="utf-8")))
    generated_cache = (generated_features, generated_sidecar, json.loads(generated_sidecar.read_text(encoding="utf-8")))
    cache_checks = [validate_feature_cache_v2(features_path=item[0], sidecar_path=item[1], artifact_root=merged_root) for item in (reference_cache, generated_cache)]
    if not all(row["passed"] for row in cache_checks):
        raise RuntimeError("synthetic merged cache-v2 validation failed")
    stages["14_cache_v2_validation"] = {"status": "PASS", "caches": 2}

    metric_payload = _metric_config(reference_cache, generated_cache)
    metric_config = root / "metric.yaml"
    metric_config.write_text(yaml.safe_dump(metric_payload, sort_keys=False), encoding="utf-8")
    metric = run_metric_reproduction_gate(metric_config, root / "metric.json")
    sanity_payload = _sanity_config()
    sanity_config = root / "sanity.yaml"
    sanity_config.write_text(yaml.safe_dump(sanity_payload, sort_keys=False), encoding="utf-8")
    sanity = run_sanity_controls(sanity_config, root / "sanity.json")
    if metric["status"] != "PASS" or sanity["status"] != "PASS":
        raise RuntimeError("synthetic metric/sanity gates failed")
    stages["15_metric_reproduction_gate"] = {"status": "PASS", "claim_allowed": False}
    stages["16_sanity_gates"] = {"status": "PASS", "claim_allowed": False}

    family = build_family_record(family_id="synthetic_family", analysis_scope="synthetic", benchmark="synthetic_fixture", feature_space="fixture", metric="rbf_mmd", kernel="rbf", bandwidth="gamma_0.5", model_pairs=["a_vs_b"], alpha_total=0.05)
    family_path = root / "family.json"
    family = write_frozen_family(family, family_path)
    stages["17_family_freeze"] = {"status": "PASS", "hypotheses": family["number_of_hypotheses"]}
    rng = np.random.default_rng(7)
    bundle_path = root / "bundle.npz"
    np.savez_compressed(bundle_path, features_a=rng.normal(0, 0.2, (16, 6)), features_b=rng.normal(1.5, 0.2, (16, 6)), features_r=rng.normal(0, 0.2, (16, 6)), sample_ids_a=np.asarray([f"a{i}" for i in range(16)]), sample_ids_b=np.asarray([f"b{i}" for i in range(16)]), source_ids_r=np.asarray([f"r{i}" for i in range(16)]))
    draw = build_reference_draw_plan([f"r{i}" for i in range(16)], num_draws=16, seed=3, population_id="synthetic_reference", source_manifest_sha256="a" * 64)
    draw_path = root / "draw_plan.json"
    atomic_write_json(draw, draw_path)
    study = {"study_id": "synthetic_study", "version": 1, "primary_question": "synthetic validation", "primary_outcomes": ["decision"], "secondary_outcomes": ["samples"], "benchmarks": ["synthetic_fixture"], "models": ["a", "b"], "model_pairs": [{"comparison_id": "a_vs_b", "model_a": "a", "model_b": "b"}], "feature_spaces": ["fixture"], "metrics": ["rbf_mmd"], "kernel": {"name": "rbf", "normalize": "l2", "gamma": 0.5}, "bandwidth_protocol": "fixed gamma", "alpha": 0.05, "multiplicity_families": ["synthetic_family"], "sample_budgets": [16], "stopping_rule": "first_boundary_crossing_union_hoeffding", "reference_draw_protocol": "fixed", "exclusion_rules": ["invalid"], "failure_rules": ["fail closed"], "resume_rules": ["same stream"], "missing_data_rules": ["block"], "censoring_rules": ["right censor"], "claim_thresholds": ["separate"], "scale_up_rules": ["stop"], "pivot_rules": ["new family"], "preprocessing_hash": "b" * 64, "frozen": True, "evidence_class": "synthetic_validation_only", "claim_allowed": False}
    study["configuration_hash"] = configuration_hash(study)
    study_path = root / "study.yaml"
    study_path.write_text(yaml.safe_dump(study, sort_keys=False), encoding="utf-8")
    generation_config = root / "synthetic_generation_config.json"
    feature_config = root / "synthetic_feature_config.json"
    atomic_write_json({"model": "fixture_model", "seeds": list(range(8)), "configuration_hash": "s" * 64, "claim_allowed": False}, generation_config)
    atomic_write_json({"extractor": "fixture", "preprocessing": reference_cache[2]["preprocessing"], "claim_allowed": False}, feature_config)
    fingerprint_inputs = {
        "benchmark_registry": Path("registry/cvpr/benchmark_registry.yaml"),
        "model_registry": Path("registry/cvpr/model_registry.yaml"),
        "feature_registry": Path("registry/cvpr/feature_space_registry.yaml"),
        "preregistration": study_path,
        "reference_manifest": reference_manifest,
        "asset_manifest": root / "model_asset_manifest.json",
        "generation_config": generation_config,
        "feature_config": feature_config,
        "family_config": family_path,
    }
    if set(fingerprint_inputs) != set(REQUIRED_INPUTS):
        raise RuntimeError("synthetic fingerprint input set is incomplete")
    fingerprint_path = root / "reproducibility_fingerprint.json"
    fingerprint = build_reproducibility_fingerprint(
        fingerprint_inputs,
        environment={"python": "local-fixture", "numpy": np.__version__, "torch": "not_loaded"},
        out=fingerprint_path,
    )
    certificate_path = root / "certificates" / "a_vs_b.json"
    certificate = certify_feature_bundle(study_path=study_path, family_path=family_path, feature_bundle_path=bundle_path, reference_draw_plan_path=draw_path, comparison_id="a_vs_b", feature_space="fixture", out_path=certificate_path, evidence_class="synthetic_validation_only", fingerprint_path=fingerprint_path)
    stages["18_certificate"] = {"status": "PASS", "decision": certificate["decision"]}
    ranking = build_partial_ranking([certificate_path], out_dir=root / "ranking", aggregation_rule="unanimous_direction_or_unresolved", family_path=family_path)
    stages["19_partial_ranking"] = {"status": "PASS", "forced_total_order": ranking["forced_total_order"], "reproducibility_fingerprint": fingerprint["fingerprint"]}

    figure_request = {"figure_id": "synthetic", "figure_type": "headline_partial_ranking", "approved_input_artifacts": ["synthetic-certificate"], "schema": "v1", "configuration_hash": study["configuration_hash"], "claim_gate_status": "BLOCKED_NO_PAPER_EVIDENCE", "output_path": str(root / "forbidden.pdf"), "caption_metadata": {}, "limitations": ["synthetic"]}
    figure_artifact = {"artifact_id": "synthetic-certificate", "validation_status": "synthetic_only", "claim_allowed": False, "configuration_hash": study["configuration_hash"]}
    figure = validate_figure_request(figure_request, [figure_artifact])
    if figure["render_allowed"]:
        raise RuntimeError("synthetic figure was incorrectly approved")

    firewall_root = root / "firewall_fixture"
    (firewall_root / "paper").mkdir(parents=True)
    (firewall_root / "paper" / "main.tex").write_text("Our results show a real improvement.\n", encoding="utf-8")
    from certgen.paper.v9_paper_firewall import run_firewall
    previous = Path.cwd()
    try:
        os.chdir(firewall_root)
        firewall = run_firewall("firewall.json", "firewall.md")
    finally:
        os.chdir(previous)
    if firewall["passed"]:
        raise RuntimeError("paper firewall failed to deny synthetic result promotion")
    stages["20_paper_firewall_denial"] = {"status": "PASS", "promotion_allowed": False, "figure_render_allowed": False}

    if len(stages) != 20 or not all(row.get("status") == "PASS" for row in stages.values()):
        raise RuntimeError(f"synthetic real-contract stage ledger incomplete: {len(stages)}/20 prerequisite stages")
    stages["21_final_synthetic_audit"] = {"status": "PASS", "prerequisite_stages": 20, "claim_allowed": False}
    payload = {"schema_version": "certgen.synthetic_runtime.v2", "status": "synthetic_real_contract_passed", "stages": stages, "stage_count": len(stages), "not_model_evidence": True, "not_empirical_evidence": True, "claim_allowed": False}
    atomic_write_json(payload, root / "final_non_evidence_audit.json")
    return payload
