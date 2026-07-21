"""Builder-faithful synthetic closure using canonical builders and importers."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import yaml  # type: ignore[import-untyped]
from PIL import Image

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.certificate_inputs import prepare_certificate_inputs
from certgen.cvpr.family_certificates import run_family_certificates
from certgen.cvpr.gates import run_metric_reproduction_gate, run_sanity_controls
from certgen.cvpr.post_cache import prepare_post_cache_gates
from certgen.cvpr.controls import prepare_controls
from certgen.cvpr.contracts import atomic_write_json
from certgen.cvpr.feature_merge import merge_feature_run
from certgen.cvpr.image_manifest import role_id_for_row
from certgen.cvpr.operational import validate_family_operational
from certgen.cvpr.output_schemas import expected_output_schema
from certgen.cvpr.package import inspect_notebook_input_package
from certgen.cvpr.prepare import prepare_family, prepare_features, prepare_generation, prepare_preflight
from certgen.cvpr.ranking import build_partial_ranking
from certgen.cvpr.reference_draw import prepare_reference_draw
from certgen.cvpr.study import freeze_study
from certgen.features.cache_v2 import validate_feature_cache_v2
from certgen.features.protocol_checks import compare_feature_runs
from certgen.notebooks.kaggle_io import deterministic_zip, validate_feature_input_images, write_integrity_manifest
from certgen.notebooks.model_assets import AssetPolicy, AssetRequirement, inventory_cache
from certgen.notebooks.subprocess_orchestrator import WorkerSpec, run_workers
from certgen.packaging.v9_import_repair import import_repair


def _dump_yaml(payload: dict[str, Any], path: Path) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _fixture_preprocessing() -> dict[str, Any]:
    return {
        "extractor_id": "inception",
        "model_identifier": "fixture/inception",
        "revision": "fixture-inception-v1",
        "processor_class": "FixtureProcessor",
        "input_resolution": 8,
        "resize_size": 8,
        "crop_size": 8,
        "crop_mode": "none",
        "interpolation": "nearest",
        "antialias": True,
        "pixel_range": "0..1",
        "channel_order": "RGB",
        "mean": [0.0, 0.0, 0.0],
        "std": [1.0, 1.0, 1.0],
        "feature_normalization": "none",
        "precision": "float32",
        "output_dimension": 7,
        "package_versions": {"fixture": "1"},
    }


def _fixture_registries(root: Path) -> dict[str, Path]:
    profile_root = root / "profiles"
    profile_root.mkdir(parents=True)
    model_ids = ["fixture_model_a", "fixture_model_b"]
    profile = {
        "schema_version": "certgen.cvpr.pilot_profile.v1",
        "profile_id": "fixture_builder_closure",
        "purpose": "Synthetic validation of canonical builder continuity.",
        "benchmark": "cifar10",
        "models": model_ids,
        "extractors": ["inception"],
        "generation_count": 8,
        "reference_count": 8,
        "sample_budgets": [8],
        "feature_spaces": ["inception"],
        "metrics": ["rbf_mmd"],
        "comparison_family": "fixture_family",
        "comparisons": ["fixture_a_vs_b", "fixture_b_vs_a"],
        "controls": ["null_reference_split", "obvious_gap_corruption"],
        "controls_in_confirmatory_family": False,
        "controls_claim_allowed": False,
        "selection_policy": "prospective_fixture_membership_before_synthetic_outputs",
        "scale_up_rules": ["stop_after_fixture"],
        "evidence_class": "pilot_only",
        "claim_allowed": False,
    }
    _dump_yaml(profile, profile_root / "fixture_builder_closure.yaml")
    models = {
        "models": [
            {
                "model_id": model_id,
                "family": "ddpm",
                "benchmark_id": "cifar10",
                "conditioning": "unconditional",
                "adapter": "diffusers_unconditional_ddpm",
                "checkpoint_or_sample_source": f"fixture/{model_id}",
                "revision": "fixture-revision-v1",
                "license": "synthetic_fixture_only",
                "authentication_required": False,
                "resolution": "8x8",
                "expected_files": ["model_index.json"],
            }
            for model_id in model_ids
        ]
    }
    model_registry = root / "models.yaml"
    _dump_yaml(models, model_registry)
    feature_registry = root / "features.yaml"
    _dump_yaml(
        {
            "feature_spaces": [
                {
                    "feature_space_id": "inception",
                    "model_identifier": "fixture/inception",
                    "revision": "fixture-inception-v1",
                    "license": "synthetic_fixture_only",
                    "expected_dimension": 7,
                    "expected_preprocessing": _fixture_preprocessing(),
                    "preflight_batch_sizes": [1, 2, 4],
                    "model_class": "FixtureInception",
                    "processor_class": "FixtureProcessor",
                    "feature_definition": "fixture_rgb_statistics_7d",
                    "pre_normalization_dimension": 7,
                    "post_normalization_dimension": 7,
                    "projection_applied": False,
                    "l2_normalization_applied": False,
                    "expected_files": ["fixture.bin"],
                    "weight_enum": "Inception_V3_Weights.IMAGENET1K_V1",
                }
            ]
        },
        feature_registry,
    )
    benchmark_registry = root / "benchmarks.yaml"
    _dump_yaml({"benchmarks": [{"benchmark_id": "cifar10"}]}, benchmark_registry)
    comparison_registry = root / "comparisons.csv"
    comparison_registry.write_text(
        "comparison_id,benchmark_id,model_a,model_b,comparison_type,source_of_pair,prospective_or_posthoc,primary_or_secondary,expected_gap_class,feature_spaces,metrics,sample_budgets,family_id,status,blocker\n"
        "null_reference_split,cifar10,reference_split_a,reference_split_b,null control,synthetic_fixture,prospective,primary,null,inception,rbf_mmd,8,fixture_family,registered,synthetic only\n"
        "obvious_gap_corruption,cifar10,reference_clean,reference_severe_corruption,obvious gap control,synthetic_fixture,prospective,primary,obvious,inception,rbf_mmd,8,fixture_family,registered,synthetic only\n"
        "fixture_a_vs_b,cifar10,fixture_model_a,fixture_model_b,fixture comparison,synthetic_fixture,prospective,primary,contestable,inception,rbf_mmd,8,fixture_family,registered,synthetic only\n"
        "fixture_b_vs_a,cifar10,fixture_model_b,fixture_model_a,fixture reverse comparison,synthetic_fixture,prospective,primary,contestable,inception,rbf_mmd,8,fixture_family,registered,synthetic only\n",
        encoding="utf-8",
    )
    return {
        "profile_root": profile_root,
        "model_registry": model_registry,
        "feature_registry": feature_registry,
        "benchmark_registry": benchmark_registry,
        "comparison_registry": comparison_registry,
    }


def _reference(root: Path) -> Path:
    images = root / "reference_images"
    images.mkdir()
    rows: list[dict[str, Any]] = []
    for index in range(32):
        path = images / f"reference_{index:04d}.png"
        Image.new("RGB", (8, 8), (index + 10, index + 20, index + 30)).save(path)
        rows.append(
            {
                "sample_id": f"reference-{index:04d}",
                "path": str(path.resolve()),
                "class_label": index % 2,
            }
        )
    manifest = root / "reference_manifest.jsonl"
    manifest.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    return manifest


def _asset(cache: Path, identity: str, expected: str) -> dict[str, Any]:
    cache.mkdir(parents=True)
    (cache / expected).write_bytes(f"synthetic fixture {identity}".encode())
    return inventory_cache(
        AssetRequirement(
            f"{identity}__asset",
            identity,
            "fixture-inception-v1" if identity == "inception" else "fixture-revision-v1",
            f"fixture/{identity}",
            "synthetic_fixture_only",
            False,
            (expected,),
        ),
        cache,
        AssetPolicy.OFFLINE_PACKAGED_CACHE,
    )


def _preflight_output(root: Path, config_path: Path, model_ids: list[str]) -> Path:
    output = root / "fake_preflight_output"
    output.mkdir()
    shutil.copy2(config_path, output / "configuration.yaml")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    atomic_write_json(
        {
            "run_id": config["run_id"],
            "configuration_hash": config["configuration_hash"],
            "input_manifest_hash": config["input_manifest_hash"],
            "asset_manifest_hash": "synthetic_preflight_generated",
            "claim_allowed": False,
        },
        output / "run_identity.json",
    )
    model_results = []
    for model_id in model_ids:
        model_root = output / "per_model" / model_id
        model_root.mkdir(parents=True)
        cache = output / "model_cache" / model_id
        manifest = _asset(cache, model_id, "model_index.json")
        atomic_write_json(manifest, model_root / "asset_manifest.json")
        smoke_image = model_root / "smoke_images" / "smoke_00.png"
        smoke_image.parent.mkdir()
        Image.new("RGB", (8, 8), (11, 22, 33)).save(smoke_image)
        applied = {
            "requested_config": {"fixture": True},
            "applied_config": {"fixture": True},
            "differences": {},
            "adapter_name": "fixture_ddpm",
            "pipeline_class": "FixturePipeline",
            "scheduler_class": "FixtureScheduler",
            "claim_allowed": False,
        }
        atomic_write_json(
            {
                "status_code": "PREFLIGHT_PASS",
                "configuration_hash": config["configuration_hash"],
                "adapter_capabilities": {"supports_batching": True},
                "claim_allowed": False,
            },
            model_root / "status.json",
        )
        atomic_write_json(
            {"status": "MODEL_LOAD_PASS", "applied_configuration": applied, "claim_allowed": False},
            model_root / "model_load.json",
        )
        atomic_write_json(
            {"status": "SCHEDULER_VALIDATED", "applied": "FixtureScheduler", "claim_allowed": False},
            model_root / "scheduler.json",
        )
        atomic_write_json(
            {
                "status": "SMOKE_GENERATION_PASS",
                "configuration_hash": config["configuration_hash"],
                "images": [
                    {
                        "path": "smoke_images/smoke_00.png",
                        "sha256": file_sha256(smoke_image),
                        "mode": "RGB",
                        "width": 8,
                        "height": 8,
                        "claim_allowed": False,
                    }
                ],
                "claim_allowed": False,
            },
            model_root / "smoke_manifest.json",
        )
        atomic_write_json(
            {"seconds_per_image": 1.0, "effective_batch_size": 1, "claim_allowed": False},
            model_root / "throughput.json",
        )
        atomic_write_json(
            {"peak_vram_bytes": 0, "claim_allowed": False}, model_root / "memory.json"
        )
        model_results.append({"model_id": model_id, "status_code": "PREFLIGHT_PASS"})
    extractor_root = output / "per_extractor" / "inception"
    extractor_root.mkdir(parents=True)
    extractor_cache = output / "model_cache" / "inception"
    extractor_asset = _asset(extractor_cache, "inception", "fixture.bin")
    atomic_write_json(extractor_asset, extractor_root / "asset_manifest.json")
    preprocessing = _fixture_preprocessing()
    atomic_write_json(
        {
            "requested_contract": {"preprocessing": preprocessing},
            "observed_contract": {
                "preprocessing": preprocessing,
                "output_definition": {"feature_definition": "fixture_rgb_statistics_7d", "expected_output_dimension": 7},
            },
            "difference_report": {},
            "preflight_status": "MATCH",
            "claim_allowed": False,
        },
        extractor_root / "preprocessing_contract.json",
    )
    atomic_write_json({"tested_batch_size": 4, "selected_batch_size": 4, "fallback_batch_size": 2, "peak_VRAM": 1.0, "elapsed_seconds": 0.01, "claim_allowed": False}, extractor_root / "runtime_calibration.json")
    atomic_write_json(
        {"status": "EXTRACTOR_LOAD_PASS", "snapshot_path": "fixture", "claim_allowed": False},
        extractor_root / "model_load.json",
    )
    atomic_write_json(
        {
            "status": "FEATURE_SMOKE_PASS",
            "shape": [4, 7],
            "finite": True,
            "claim_allowed": False,
        },
        extractor_root / "feature_smoke.json",
    )
    atomic_write_json(
        {
            "status_code": "EXTRACTOR_PREFLIGHT_PASS",
            "configuration_hash": config["configuration_hash"],
            "claim_allowed": False,
        },
        extractor_root / "status.json",
    )
    schema = expected_output_schema("preflight")
    workers = [*model_ids, "inception"]
    status = {
        "status_code": "PREFLIGHT_PASS",
        "output_schema_version": schema["schema_version"],
        "passed": True,
        "results": model_results,
        "extractor_results": [{"feature_space_id": "inception", "status_code": "EXTRACTOR_PREFLIGHT_PASS"}],
        "expected_workers": workers,
        "completed_workers": workers,
        "configuration_hash": config["configuration_hash"],
        "claim_allowed": False,
    }
    atomic_write_json(status, output / "checkpoint_preflight_status.json")
    atomic_write_json(status, output / "status.json")
    (output / "copyback_instructions.md").write_text("synthetic validation only; not paper evidence; claim_allowed=false\n", encoding="utf-8")
    write_integrity_manifest(output)
    archive = root / "fake_preflight_output.zip"
    deterministic_zip(output, archive)
    return archive


def _generation_output(root: Path, generation_config: Path, models: list[dict[str, Any]]) -> Path:
    output = root / "fake_generation_output"
    specs: list[WorkerSpec] = []
    for model_index, model in enumerate(models):
        model_id = str(model["model_id"])
        for shard_index, seeds in enumerate(model["seed_shards"]):
            shard_id = f"shard_{shard_index:04d}"
            worker_root = output / "per_model" / model_id / "per_shard" / shard_id
            worker_id = f"{model_id}__{shard_id}"
            specs.append(
                WorkerSpec(
                    worker_id,
                    "certgen.notebooks.workers.fake_generation_worker",
                    shard_index,
                    worker_id,
                    ("--out", str(worker_root), "--model-id", model_id, "--seeds", ",".join(map(str, seeds)), "--config-hash", "a" * 64, "--shard-id", shard_id, "--oom-above", "4"),
                    str(worker_root / "worker_status.json"),
                )
            )
    orchestration = run_workers(specs, output_dir=root / "generation_orchestration", timeout_seconds=30)
    if orchestration["status"] != "COMPLETE":
        raise RuntimeError("fixture generation workers failed")
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(generation_config, output / "configuration.yaml")
    config = yaml.safe_load(generation_config.read_text(encoding="utf-8"))
    atomic_write_json(
        {
            "run_id": config["run_id"],
            "configuration_hash": config["configuration_hash"],
            "input_manifest_hash": config["reference_manifest_hash"],
            "asset_manifest_hash": config["asset_manifest_hash"],
            "claim_allowed": False,
        },
        output / "run_identity.json",
    )
    workers = [spec.worker_id for spec in specs]
    status = {
        "status_code": "GENERATION_COMPLETE",
        "output_schema_version": expected_output_schema("generation")["schema_version"],
        "passed": True,
        "expected_workers": workers,
        "completed_workers": workers,
        "configuration_hash": config["configuration_hash"],
        "evidence_class": "synthetic_validation_only",
        "claim_allowed": False,
    }
    atomic_write_json(status, output / "generation_status.json")
    atomic_write_json(status, output / "status.json")
    (output / "copyback_instructions.md").write_text("synthetic validation only; not paper evidence; claim_allowed=false\n", encoding="utf-8")
    write_integrity_manifest(output)
    archive = root / "fake_generation_output.zip"
    deterministic_zip(output, archive)
    return archive


def _vector(path: Path) -> np.ndarray:
    pixels = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
    return np.concatenate([pixels.mean((0, 1)), pixels.std((0, 1)), np.asarray([0.01], dtype=np.float32)])


def _feature_output(root: Path, feature_package: Path) -> tuple[Path, Path]:
    extracted = root / "extracted_feature_input"
    shutil.unpack_archive(str(feature_package), str(extracted), "zip")
    config = yaml.safe_load((extracted / "configuration.yaml").read_text(encoding="utf-8"))
    validation = validate_feature_input_images(extracted, config)
    if validation["status"] != "ALL_FEATURE_IMAGE_PATHS_RESOLVED":
        raise RuntimeError("feature package image validation failed")
    rows = [json.loads(line) for line in (extracted / "manifests" / "images.jsonl").read_text(encoding="utf-8").splitlines() if line]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        role_id = role_id_for_row(row)
        grouped.setdefault(role_id, []).append(row)
    output = root / "fake_feature_output"
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(extracted / "configuration.yaml", output / "configuration.yaml")
    atomic_write_json(
        {
            "run_id": config["run_id"],
            "configuration_hash": config["configuration_hash"],
            "input_manifest_hash": config["source_manifest_hash"],
            "asset_manifest_hash": "synthetic_feature_assets",
            "claim_allowed": False,
        },
        output / "run_identity.json",
    )
    workers: list[str] = []
    preprocessing = _fixture_preprocessing()
    for role_id, role_rows in sorted(grouped.items()):
        shard_id = f"{role_id}__shard_0000"
        workers.append(f"inception__{shard_id}")
        shard = output / "shards" / "inception" / shard_id
        shard.mkdir(parents=True)
        raw_matrix = np.stack([_vector(extracted / row["relative_image_path"]) for row in role_rows]).astype(np.float32)
        # The fixture lane deliberately encodes the registered control ordering so
        # the post-cache gates exercise their real logic instead of depending on
        # incidental tiny-image statistics.
        if role_id in {"reference", "control__reference_split_a", "control__reference_split_b", "control__reference_clean"}:
            center = np.asarray([1.0, 0.05, 0.02, 0.01, 0.01, 0.01, 0.01], dtype=np.float32)
        elif role_id == "control__reference_mild_corruption":
            center = np.asarray([0.9, 0.15, 0.05, 0.02, 0.01, 0.01, 0.01], dtype=np.float32)
        elif role_id == "control__reference_moderate_corruption":
            center = np.asarray([0.55, 0.55, 0.25, 0.1, 0.05, 0.02, 0.01], dtype=np.float32)
        elif role_id == "control__reference_severe_corruption":
            center = np.asarray([0.02, 1.0, 0.8, 0.4, 0.2, 0.1, 0.05], dtype=np.float32)
        elif role_id == "model__fixture_model_a":
            center = np.asarray([0.75, 0.25, 0.1, 0.05, 0.02, 0.01, 0.01], dtype=np.float32)
        elif role_id == "model__fixture_model_b":
            center = np.asarray([0.25, 0.75, 0.1, 0.05, 0.02, 0.01, 0.01], dtype=np.float32)
        else:
            center = raw_matrix.mean(axis=0)
        offsets = np.linspace(-1e-4, 1e-4, len(role_rows), dtype=np.float32)[:, None]
        matrix = np.repeat(center[None, :], len(role_rows), axis=0) + offsets
        ids = [str(row["sample_id"]) for row in role_rows]
        batching_check = {
            "schema_version": "certgen.feature_repeated_batching.v1",
            "batch_sizes": [1, min(4, len(ids))],
            "synthetic_validation_only": True,
            **compare_feature_runs(ids, matrix, ids, matrix),
        }
        np.savez_compressed(shard / "features.npz", features=matrix, sample_ids=np.asarray(ids))
        model_id = str(role_rows[0]["model_id"])
        sidecar = {
            "schema_version": "certgen.feature_shard.v2",
            "extractor_id": "inception",
            "extractor_revision": "fixture-inception-v1",
            "configuration_hash": config["configuration_hash"],
            "preprocessing_hash": stable_hash_json(preprocessing),
            "array_sha256": file_sha256(shard / "features.npz"),
            "rows": len(ids),
            "dimension": 7,
            "sample_order_hash": stable_hash_json(ids),
            "role": role_id,
            "canonical_role": str(role_rows[0]["role"]),
            "model_id": model_id,
            "source_manifest_hash": config["source_manifest_hash"],
            "image_manifest_schema_version": "certgen.cvpr.image_manifest.v1",
            "expected_preprocessing": preprocessing,
            "output_definition": {"feature_definition": "fixture_rgb_statistics_7d", "expected_output_dimension": 7},
            "resolved_model_id": "fixture/inception",
            "resolved_revision": "fixture-inception-v1",
            "source_license": "synthetic_fixture_only",
            "runtime": {"device": "fixture_cpu", "precision": "float32", "batch_size": len(ids), "package_versions": {"fixture": "1"}},
            "protocol_checks": {"repeated_batching": batching_check},
            "claim_allowed": False,
        }
        atomic_write_json(sidecar, shard / "sidecar.json")
        atomic_write_json({"status_code": "FEATURE_SHARD_COMPLETE", "claim_allowed": False}, shard / "status.json")
    status = {
        "status_code": "FEATURE_EXTRACTION_SHARDS_COMPLETE",
        "output_schema_version": expected_output_schema("feature")["schema_version"],
        "passed": True,
        "expected_workers": workers,
        "completed_workers": workers,
        "configuration_hash": config["configuration_hash"],
        "evidence_class": "synthetic_validation_only",
        "claim_allowed": False,
    }
    atomic_write_json(status, output / "feature_extraction_status.json")
    atomic_write_json(status, output / "status.json")
    (output / "copyback_instructions.md").write_text("synthetic validation only; not paper evidence; claim_allowed=false\n", encoding="utf-8")
    write_integrity_manifest(output)
    archive = root / "fake_feature_output.zip"
    deterministic_zip(output, archive)
    return archive, extracted


def run_builder_faithful_synthetic(output_dir: str | Path) -> dict[str, Any]:
    root = Path(output_dir)
    if root.exists():
        raise FileExistsError(f"refusing to overwrite builder-faithful closure: {root}")
    root.mkdir(parents=True)
    registry = _fixture_registries(root / "registries")
    reference_manifest = _reference(root)
    study_result = freeze_study(
        "fixture_builder_closure",
        out_path=root / "study.yaml",
        profile_root=registry["profile_root"],
        model_registry=registry["model_registry"],
        feature_registry=registry["feature_registry"],
        comparison_registry=registry["comparison_registry"],
    )
    draw_result = prepare_reference_draw(
        profile_id="fixture_builder_closure",
        study_path=root / "study.yaml",
        reference_manifest=reference_manifest,
        out_path=root / "reference_draw_plan.json",
        seed=7,
        profile_root=registry["profile_root"],
        registry_path=root / "artifact_registry.jsonl",
    )
    draw_plan = Path(draw_result["draw_plan"])
    controls = prepare_controls(
        study_path=root / "study.yaml",
        reference_draw=draw_plan,
        out_root=root / "controls",
        registry_path=root / "artifact_registry.jsonl",
    )
    preflight = prepare_preflight(
        out_dir=root / "preflight_package",
        policy=AssetPolicy.OFFLINE_PACKAGED_CACHE,
        model_registry=registry["model_registry"],
        feature_registry=registry["feature_registry"],
        benchmark_registry=registry["benchmark_registry"],
        profile="fixture_builder_closure",
        profile_root=registry["profile_root"],
    )
    if preflight["status"] != "PREFLIGHT_PACKAGE_READY":
        raise RuntimeError(f"fixture preflight builder blocked: {preflight}")
    model_ids = ["fixture_model_a", "fixture_model_b"]
    preflight_zip = _preflight_output(root, Path(preflight["config"]), model_ids)
    preflight_import = import_repair(
        kind="preflight",
        zip_path=preflight_zip,
        out_dir=root / "imported_preflight",
        out_json=root / "preflight_import.json",
        out_report=root / "preflight_import.md",
        registry_path=root / "artifact_registry.jsonl",
    )
    if not preflight_import["passed"]:
        raise RuntimeError("fixture preflight import failed: " + "; ".join(preflight_import["errors"]))
    generation = prepare_generation(
        out_dir=root / "generation_package",
        preflight_config=preflight["config"],
        preflight_import=root / "preflight_import.json",
        reference_manifest=reference_manifest,
        scale="1k",
        study_path=root / "study.yaml",
    )
    generation_config = yaml.safe_load(Path(generation["config"]).read_text(encoding="utf-8"))
    generation_models = [
        {"model_id": row["model_id"], "seed_shards": generation_config["seed_shards"][row["model_id"]]}
        for row in generation_config["models"]
    ]
    generation_zip = _generation_output(root, Path(generation["config"]), generation_models)
    generation_import = import_repair(
        kind="generation",
        zip_path=generation_zip,
        out_dir=root / "imported_generation",
        out_json=root / "generation_import.json",
        out_report=root / "generation_import.md",
        registry_path=root / "artifact_registry.jsonl",
    )
    if not generation_import["passed"]:
        raise RuntimeError("fixture generation import failed: " + "; ".join(generation_import["errors"]))
    features = prepare_features(
        out_dir=root / "feature_package",
        generation_import=root / "generation_import.json",
        preflight_import=root / "preflight_import.json",
        reference_manifest=reference_manifest,
        reference_draw_plan=draw_plan,
        feature_registry=registry["feature_registry"],
        shard_count=1,
        controls_dir=controls["controls_dir"],
    )
    feature_package = Path(features["package"]["zip_path"])
    package_verdict = inspect_notebook_input_package(feature_package)
    if not package_verdict["passed"]:
        raise RuntimeError("fixture feature package inspection failed: " + "; ".join(package_verdict["errors"]))
    feature_zip, _ = _feature_output(root, feature_package)
    feature_import = import_repair(
        kind="feature",
        zip_path=feature_zip,
        out_dir=root / "imported_feature",
        out_json=root / "feature_import.json",
        out_report=root / "feature_import.md",
        registry_path=root / "artifact_registry.jsonl",
    )
    if not feature_import["passed"]:
        raise RuntimeError("fixture feature import failed: " + "; ".join(feature_import["errors"]))
    merged = merge_feature_run(
        root / "imported_feature",
        output_root=root / "cache_v2",
        registry_path=root / "artifact_registry.jsonl",
    )
    merge_root = Path(merged["output_dir"])
    for sidecar in merge_root.glob("inception/*/sidecar.json"):
        verdict = validate_feature_cache_v2(
            features_path=sidecar.with_name("features.npz"), sidecar_path=sidecar, artifact_root=merge_root
        )
        if not verdict["passed"]:
            raise RuntimeError("fixture cache-v2 validation failed")
    family = prepare_family(
        out_dir=root / "family",
        comparison_registry=registry["comparison_registry"],
        study_path=root / "study.yaml",
    )
    bundles = prepare_certificate_inputs(
        study_path=root / "study.yaml",
        family_path=root / "family" / "family.json",
        feature_run=merge_root,
        reference_draw_plan=draw_plan,
        out_root=root / "certificate_inputs",
        registry_path=root / "artifact_registry.jsonl",
    )
    operational = validate_family_operational(
        family_path=root / "family" / "family.json",
        study_path=root / "study.yaml",
        inputs_root=root / "certificate_inputs",
        coverage_path=root / "operational_hypothesis_coverage.csv",
    )
    if operational["status"] != "FAMILY_OPERATIONALLY_READY":
        raise RuntimeError("fixture family is not operational: " + "; ".join(operational["errors"]))
    gate_configs = prepare_post_cache_gates(
        study_path=root / "study.yaml",
        family_path=root / "family" / "family.json",
        feature_run=merge_root,
        metric_out=root / "frozen_metric_reproduction.yaml",
        sanity_out=root / "frozen_sanity.yaml",
        registry_path=root / "artifact_registry.jsonl",
    )
    metric_result = run_metric_reproduction_gate(
        gate_configs["metric_config"], root / "metric_reproduction.json"
    )
    sanity_result = run_sanity_controls(
        gate_configs["sanity_config"], root / "sanity_controls.json"
    )
    if metric_result["status"] != "PASS" or sanity_result["status"] != "PASS":
        raise RuntimeError("fixture post-cache gates did not pass")
    coverage = run_family_certificates(
        study_path=root / "study.yaml",
        family_path=root / "family" / "family.json",
        inputs_root=root / "certificate_inputs",
        reference_draw_plan=draw_plan,
        metric_result=root / "metric_reproduction.json",
        sanity_result=root / "sanity_controls.json",
        operational_status=operational["operational_artifact"],
        out_dir=root / "certificates",
        registry_path=root / "artifact_registry.jsonl",
    )
    certificate_paths = [Path(row["certificate"]) for row in coverage["certificates"]]
    certificates = [json.loads(path.read_text(encoding="utf-8")) for path in certificate_paths]
    ranking = build_partial_ranking(
        certificate_paths, out_dir=root / "ranking", family_path=root / "family" / "family.json"
    )
    stages = [
        "selected_profile", "study_freeze", "preflight_builder", "fake_preflight_zip", "preflight_import",
        "generation_builder", "fake_generation_zip", "generation_import", "feature_builder_embedded_images",
        "feature_image_decode", "fake_feature_zip", "feature_import", "feature_merge", "cache_v2",
        "canonical_reference_draw", "control_builder", "control_feature_roles", "family_freeze",
        "certificate_input_builder", "certificate_input_validation", "family_operational_gate",
        "post_cache_gate_configs", "metric_reproduction_gate", "sanity_controls_gate",
        "family_certificate_runner", "three_family_certificates", "partial_ranking",
    ]
    result = {
        "status": "BUILDER_FAITHFUL_SYNTHETIC_CLOSURE_PASS",
        "rehearsal_status": "COMPLETE_BUILDER_FAITHFUL_SYNTHETIC_REHEARSAL_PASS",
        "stages": stages,
        "study_hash": study_result["study_hash"],
        "profile": "fixture_builder_closure",
        "feature_package_sha256": file_sha256(feature_package),
        # Preserve the legacy model/reference closure count while reporting the
        # complete role count separately for the final rehearsal contract.
        "cache_groups": 3,
        "complete_cache_groups": merged["groups"],
        "family_hash": family["configuration_hash"],
        "certificate_hashes": [certificate["certificate_hash"] for certificate in certificates],
        "certificate_input_bundles": len(bundles["bundles"]),
        "family_operational_status": operational["status"],
        "metric_reproduction_status": metric_result["status"],
        "sanity_controls_status": sanity_result["status"],
        "family_certificate_coverage_status": coverage["status"],
        "ranking_hash": ranking["ranking_hash"],
        "evidence_class": "synthetic_validation_only",
        "not_model_evidence": True,
        "claim_allowed": False,
    }
    atomic_write_json(result, root / "builder_faithful_status.json")
    return result
