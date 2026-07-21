"""Canonical registry-derived preparation commands for the CVPR pipeline."""

from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

import yaml  # type: ignore[import-untyped]
from PIL import Image

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.contracts import atomic_write_json
from certgen.cvpr.extractor_adapters import adapter_for_extractor
from certgen.cvpr.controls import validate_controls
from certgen.cvpr.image_manifest import (
    ImageManifestRow,
    read_image_manifest,
    role_id_for_row,
    write_image_manifest,
)
from certgen.cvpr.model_adapters import UnsupportedModelAdapter, adapter_for_model
from certgen.cvpr.output_schemas import expected_output_schema
from certgen.cvpr.package import build_notebook_input_package
from certgen.cvpr.profiles import load_profile, load_profile_path, resolve_selection
from certgen.cvpr.study import require_frozen_study
from certgen.notebooks.model_assets import AssetPolicy
from certgen.notebooks.model_assets import portable_asset_manifest
from certgen.notebooks.model_assets import validate_asset_identity, validate_asset_manifest
from certgen.notebooks.network_policy import NetworkMode
from certgen.stats.reference_sampling import validate_reference_draw_plan


BLOCKED_LICENSES = {
    "",
    "unknown",
    "unverified",
    "unverified_requires_manual_review",
    "model_and_package_review_required",
    "package_and_weights_review_required",
    "manual_release_review_required",
}
PLACEHOLDER_TOKENS = ("TBD", "UNKNOWN", "UNVERIFIED", "<", ">")


def _yaml(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected a mapping: {path}")
    return payload


def _write_yaml(payload: Mapping[str, Any], path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite prepared configuration: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(yaml.safe_dump(dict(payload), sort_keys=False), encoding="utf-8")
    temporary.replace(path)


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _unresolved_paths(value: Any, prefix: str = "") -> list[str]:
    if isinstance(value, Mapping):
        return [
            item
            for key, child in value.items()
            if key != "configuration_hash"
            for item in _unresolved_paths(child, f"{prefix}.{key}" if prefix else str(key))
        ]
    if isinstance(value, list):
        return [item for index, child in enumerate(value) for item in _unresolved_paths(child, f"{prefix}[{index}]")]
    if isinstance(value, str) and any(token in value.upper() for token in PLACEHOLDER_TOKENS[:3]):
        return [prefix]
    return []


def _freeze(payload: dict[str, Any]) -> dict[str, Any]:
    unresolved = _unresolved_paths(payload)
    if unresolved:
        raise ValueError("canonical builder refuses unresolved placeholders: " + ", ".join(unresolved[:20]))
    payload.pop("configuration_hash", None)
    payload["configuration_hash"] = stable_hash_json(payload)
    return payload


def _write_json(payload: Mapping[str, Any], path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite prepared artifact: {path}")
    atomic_write_json(dict(payload), path)


def _dependency_profile() -> dict[str, Any]:
    return {
        "profile": "kaggle_t4x2_preflight",
        "network_mode": NetworkMode.ONLINE_DEPENDENCIES_ONLINE_ASSETS.value,
        "dependency_network_allowed": True,
        "model_asset_network_allowed": True,
        "wheelhouse_optional": True,
        "kernel_restart_revalidation_required": True,
        "claim_allowed": False,
    }


def _model_runtime(row: Mapping[str, Any], *, smoke: bool) -> dict[str, Any]:
    resolution = str(row.get("resolution", "32x32")).lower().split("x")
    width, height = (int(resolution[0]), int(resolution[1])) if len(resolution) == 2 else (32, 32)
    count = 2 if smoke else 0
    return {
        "batch_size": count or 64,
        "minimum_batch_size": 1,
        "seeds": list(range(1000, 1000 + count)),
        "num_inference_steps": 2 if smoke else 1000,
        "scheduler": "checkpoint_default_pinned",
        "guidance_scale": None,
        "width": width,
        "height": height,
        "prompts": [],
        "class_ids": [],
        "precision": "float16",
        "output_type": "pil",
    }


def prepare_preflight(
    *,
    out_dir: str | Path,
    policy: AssetPolicy | str,
    model_registry: str | Path = "registry/cvpr/model_registry.yaml",
    feature_registry: str | Path = "registry/cvpr/feature_space_registry.yaml",
    benchmark_registry: str | Path = "registry/cvpr/benchmark_registry.yaml",
    license_approvals: Mapping[str, str] | None = None,
    profile: str | None = None,
    profile_path: str | Path | None = None,
    model_ids: list[str] | None = None,
    extractor_ids: list[str] | None = None,
    profile_root: str | Path = "configs/cvpr/profiles",
) -> dict[str, Any]:
    selected_policy = AssetPolicy(policy)
    approvals = dict(license_approvals or {})
    model_rows = _yaml(model_registry).get("models", [])
    feature_rows = _yaml(feature_registry).get("feature_spaces", [])
    benchmark_rows = _yaml(benchmark_registry).get("benchmarks", [])
    benchmark = next((row for row in benchmark_rows if row.get("benchmark_id") == "cifar10"), None)
    if benchmark is None:
        raise ValueError("CIFAR-10 benchmark row is missing")
    if profile is not None and profile_path is not None:
        raise ValueError("profile and profile_path are mutually exclusive")
    profile_payload = load_profile(profile, profile_root) if profile is not None else (
        load_profile_path(profile_path) if profile_path is not None else None
    )
    selected_model_ids, selected_extractor_ids, profile_snapshot = resolve_selection(
        profile=profile_payload,
        models=model_ids,
        extractors=extractor_ids,
    )
    available_models = {
        str(row["model_id"]): row for row in model_rows if row.get("benchmark_id") == "cifar10"
    }
    available_extractors = {str(row["feature_space_id"]): row for row in feature_rows}
    if not selected_model_ids:
        selected_model_ids = list(available_models)
    if not selected_extractor_ids:
        selected_extractor_ids = list(available_extractors)
    missing_models = sorted(set(selected_model_ids) - set(available_models))
    missing_extractors = sorted(set(selected_extractor_ids) - set(available_extractors))
    if missing_models or missing_extractors:
        raise ValueError(
            f"selected registry rows are missing: models={missing_models}, extractors={missing_extractors}"
        )
    excluded_models = sorted(set(available_models) - set(selected_model_ids))
    excluded_extractors = sorted(set(available_extractors) - set(selected_extractor_ids))
    selection_snapshot = profile_snapshot or {
        "schema_version": "certgen.cvpr.explicit_selection.v1",
        "profile_id": "explicit_selection",
        "purpose": "prospective explicit CLI selection",
        "benchmark": "cifar10",
        "models": selected_model_ids,
        "extractors": selected_extractor_ids,
        "feature_spaces": selected_extractor_ids,
        "generation_count": 1000,
        "reference_count": 1000,
        "sample_budgets": [1000],
        "metrics": ["rbf_mmd"],
        "comparison_family": "explicit_selection_requires_study_freeze",
        "comparisons": ["checkpoint_variant"],
        "evidence_class": "pilot_only",
        "selection_policy": "prospective_membership_frozen_before_results",
        "claim_allowed": False,
    }
    models: list[dict[str, Any]] = []
    extractors: list[dict[str, Any]] = []
    assets: list[dict[str, Any]] = []
    capabilities: dict[str, Any] = {}
    blockers: list[str] = []
    for model_id in selected_model_ids:
        row = available_models[model_id]
        model_id = str(row["model_id"])
        revision = str(row.get("revision", ""))
        license_status = approvals.get(model_id, str(row.get("license", "")))
        if _unresolved_paths({"revision": revision}) or license_status.lower() in BLOCKED_LICENSES:
            blockers.append(f"{model_id}: pinned revision and manual license approval required")
            continue
        adapter = adapter_for_model(row)
        if isinstance(adapter, UnsupportedModelAdapter):
            blockers.append(f"{model_id}: {adapter.reason}")
            continue
        runtime = _model_runtime(row, smoke=True)
        model = {
            "model_id": model_id,
            "family": row.get("family"),
            "conditioning": row.get("conditioning"),
            "adapter": row.get("adapter"),
            "checkpoint_or_sample_source": row["checkpoint_or_sample_source"],
            "revision": revision,
            "license": license_status,
            "preflight_runtime_config": runtime,
        }
        models.append(model)
        capabilities[model_id] = {"adapter_name": adapter.adapter_name, **adapter.capabilities().as_dict()}
        assets.append(
            {
                "asset_kind": "model",
                "asset_id": f"{model_id}__asset",
                "model_or_extractor_id": model_id,
                "revision": revision,
                "source": row["checkpoint_or_sample_source"],
                "license": license_status,
                "authentication_required": row.get("authentication_required") is True,
                "policy": selected_policy.value,
                "expected_files": row.get("expected_files")
                or ["model_index.json", "scheduler/scheduler_config.json", "unet/config.json"],
            }
        )
    for extractor_id in selected_extractor_ids:
        row = available_extractors[extractor_id]
        extractor_id = str(row["feature_space_id"])
        revision = str(row.get("revision", ""))
        license_status = approvals.get(extractor_id, str(row.get("license", "")))
        unresolved = _unresolved_paths(
            {
                "model_identifier": row.get("model_identifier"),
                "revision": revision,
                "expected_dimension": row.get("expected_dimension"),
            }
        )
        if unresolved or license_status.lower() in BLOCKED_LICENSES:
            blockers.append(f"{extractor_id}: pinned implementation/revision/dimension and manual license approval required")
            continue
        expected = row.get("expected_preprocessing")
        if not isinstance(expected, Mapping) or _unresolved_paths(expected):
            blockers.append(f"{extractor_id}: exact expected preprocessing contract required")
            continue
        extractor = {
            "feature_space_id": extractor_id,
            "model_identifier": row["model_identifier"],
            "revision": revision,
            "expected_dimension": int(row["expected_dimension"]),
            "expected_preprocessing": dict(expected),
            "preflight_batch_sizes": row.get("preflight_batch_sizes", [1, 2, 4, 8, 16, 32, 64]),
            "model_class": row.get("model_class"),
            "processor_class": row.get("processor_class"),
            "feature_definition": row.get("feature_definition"),
            "pre_normalization_dimension": row.get("pre_normalization_dimension"),
            "post_normalization_dimension": row.get("post_normalization_dimension"),
            "projection_applied": row.get("projection_applied"),
            "l2_normalization_applied": row.get("l2_normalization_applied"),
            "license": license_status,
        }
        try:
            dedicated_adapter = adapter_for_extractor(extractor)
        except ValueError as exc:
            if not str(row.get("model_identifier", "")).startswith("fixture/"):
                blockers.append(f"{extractor_id}: {exc}")
                continue
            extractor["adapter_id"] = "fixture_contract_only"
            extractor["output_definition"] = {
                "extractor_id": extractor_id,
                "model_class": "FixtureExtractor",
                "processor_class": expected.get("processor_class"),
                "feature_definition": "fixture_validation_only",
                "pre_normalization_dimension": int(row["expected_dimension"]),
                "post_normalization_dimension": int(row["expected_dimension"]),
                "projection_applied": False,
                "l2_normalization_applied": expected.get("feature_normalization") == "l2",
                "expected_output_dimension": int(row["expected_dimension"]),
            }
        else:
            extractor["adapter_id"] = dedicated_adapter.adapter_id
            extractor["output_definition"] = dedicated_adapter.output_definition()
        extractors.append(extractor)
        source = str(row["model_identifier"])
        assets.append(
            {
                "asset_kind": "extractor",
                "asset_id": f"{extractor_id}__asset",
                "model_or_extractor_id": extractor_id,
                "revision": revision,
                "source": source,
                "license": license_status,
                "authentication_required": False,
                "policy": selected_policy.value,
                "expected_files": row.get("expected_files") or ["config.json"],
                "loader_type": (
                    "torchvision_local_state_dict" if extractor_id == "inception" else "from_pretrained_local_snapshot"
                ),
                "layout_type": (
                    "torchvision_local_weight_file" if extractor_id == "inception" else "direct_local_snapshot"
                ),
                "weight_enum": row.get("weight_enum"),
                "torchvision_package_version": row.get("torchvision_package_version"),
            }
        )
    if blockers or not models or not extractors:
        payload = {
            "status": "BLOCKED_PREFLIGHT_REGISTRY_OR_LICENSE",
            "blockers": blockers or ["no operational model/extractor candidates"],
            "selected_models": selected_model_ids,
            "selected_extractors": selected_extractor_ids,
            "registered_not_selected": {
                "models": excluded_models,
                "extractors": excluded_extractors,
                "status": "REGISTERED_NOT_SELECTED",
            },
            "policy": selected_policy.value,
            "evidence_class": "planning_only",
            "claim_allowed": False,
        }
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        atomic_write_json(payload, out / "prepare_preflight_blocked.json")
        return payload
    timestamp = _timestamp()
    identity_hash = stable_hash_json({"models": models, "extractors": extractors, "assets": assets})[:12]
    mode = (
        NetworkMode.ONLINE_DEPENDENCIES_ONLINE_ASSETS
        if selected_policy is AssetPolicy.ONLINE_PREFLIGHT_DOWNLOAD
        else NetworkMode.ONLINE_DEPENDENCIES_OFFLINE_ASSETS
    )
    config = _freeze(
        {
            "kind": "preflight",
            "run_id": f"cifar10__checkpoint-preflight__tiny__none__{identity_hash}__{timestamp}",
            "mode": "force_new_run",
            "asset_policy": selected_policy.value,
            "network_mode": mode.value,
            "dependency_network_allowed": True,
            "model_asset_network_allowed": selected_policy is AssetPolicy.ONLINE_PREFLIGHT_DOWNLOAD,
            "requested_gpu_count": 2,
            "allow_single_gpu_fallback": False,
            "environment_profile": "kaggle_t4x2_preflight",
            "input_manifest_hash": "preflight_none",
            "tiny_images_per_model": 2,
            "pilot_profile": selection_snapshot,
            "selected_models": selected_model_ids,
            "selected_extractors": selected_extractor_ids,
            "registered_not_selected": {
                "models": excluded_models,
                "extractors": excluded_extractors,
                "status": "REGISTERED_NOT_SELECTED",
            },
            "models": models,
            "extractors": extractors,
            "assets": assets,
            "output_schema_version": expected_output_schema("preflight")["schema_version"],
            "evidence_class": "non_evidence_preflight",
            "claim_allowed": False,
        }
    )
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    config_path = out / "preflight_config.yaml"
    _write_yaml(config, config_path)
    _write_yaml({"models": models, "claim_allowed": False}, out / "models.yaml")
    _write_yaml({"extractors": extractors, "claim_allowed": False}, out / "extractors.yaml")
    _write_yaml(selection_snapshot, out / "profile_snapshot.yaml")
    _write_yaml({"capabilities": capabilities, "claim_allowed": False}, out / "adapter_capabilities.yaml")
    _write_yaml(_dependency_profile(), out / "dependency_profile.yaml")
    _write_json(expected_output_schema("preflight"), out / "expected_output_schema.json")
    worker_dir = out / "worker_configs"
    worker_dir.mkdir()
    for asset in assets:
        _write_json({"asset": asset, "configuration_hash": config["configuration_hash"], "claim_allowed": False}, worker_dir / f"{asset['asset_id']}.json")
    identity = {
        "run_id": config["run_id"],
        "configuration_hash": config["configuration_hash"],
        "input_manifest_hash": config["input_manifest_hash"],
        "asset_manifest_hash": "generated_by_real_preflight",
        "claim_allowed": False,
    }
    _write_json(identity, out / "run_identity.json")
    instructions = out / "KAGGLE_INSTRUCTIONS.md"
    instructions.write_text(
        "# Kaggle preflight\n\nValidate this ZIP locally, upload it, run the canonical T4x2 preflight notebook, "
        "copy back the deterministic output ZIP, validate it, and import it. The output is non-evidence preflight; "
        "claim_allowed=false.\n",
        encoding="utf-8",
    )
    inputs = {
        name: out / name
        for name in (
            "models.yaml",
            "extractors.yaml",
            "profile_snapshot.yaml",
            "adapter_capabilities.yaml",
            "dependency_profile.yaml",
            "expected_output_schema.json",
            "worker_configs",
            "run_identity.json",
            "KAGGLE_INSTRUCTIONS.md",
        )
    }
    package = build_notebook_input_package(
        kind="preflight",
        config_path=config_path,
        inputs=inputs,
        out_zip=out / "certgen_cvpr_preflight_input.zip",
        manifest_out=out / "preflight_input_manifest.json",
    )
    return {"status": "PREFLIGHT_PACKAGE_READY", "config": str(config_path), "package": package, "claim_allowed": False}


def _imported_root(record: Mapping[str, Any], kind: str) -> Path:
    if record.get("passed") is not True or record.get("kind") not in {kind, "feature" if kind == "features" else kind}:
        raise ValueError(f"builder requires a successful canonical {kind} import")
    root = Path(str(record.get("out_dir", "")))
    if not root.is_dir():
        raise FileNotFoundError(f"imported {kind} output directory is unavailable: {root}")
    return root


def prepare_generation(
    *,
    out_dir: str | Path,
    preflight_config: str | Path,
    preflight_import: str | Path,
    reference_manifest: str | Path,
    scale: str,
    shard_count: int = 2,
    study_path: str | Path = "artifacts/cvpr/study/cifar_integrity_minimal.yaml",
) -> dict[str, Any]:
    if scale not in {"1k", "10k", "50k"}:
        raise ValueError("scale must be 1k, 10k, or 50k")
    imported = json.loads(Path(preflight_import).read_text(encoding="utf-8"))
    imported_root = _imported_root(imported, "preflight")
    reference = Path(reference_manifest)
    reference_rows = [json.loads(line) for line in reference.read_text(encoding="utf-8").splitlines() if line]
    preflight = _yaml(preflight_config)
    profile_snapshot = preflight.get("pilot_profile")
    if not isinstance(profile_snapshot, Mapping):
        profile_snapshot = {
            "profile_id": "legacy_nonclaim_builder",
            "generation_count": int(scale[:-1]) * 1000,
            "reference_count": 10000,
            "claim_allowed": False,
        }
    study = require_frozen_study(study_path, profile=profile_snapshot)
    required_reference_count = int(profile_snapshot.get("reference_count", 10000))
    if len(reference_rows) < required_reference_count:
        raise ValueError(
            f"generation builder requires at least {required_reference_count} materialized reference rows"
        )
    count = int(profile_snapshot.get("generation_count", int(scale[:-1]) * 1000))
    seed_shards: dict[str, list[list[int]]] = {}
    models: list[dict[str, Any]] = []
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    receipt = out / "preflight_receipt"
    receipt.mkdir()
    root_status = imported_root / "status.json"
    if not root_status.is_file():
        root_status = imported_root / "checkpoint_preflight_status.json"
    if not root_status.is_file():
        raise FileNotFoundError("imported preflight has no canonical root status")
    shutil.copy2(root_status, receipt / "status.json")
    input_mapping: dict[str, str | Path] = {"preflight": receipt, "study.yaml": study_path}
    calibration: dict[str, Any] = {}
    portable_assets_dir = out / "asset_manifests"
    portable_assets_dir.mkdir()
    for model_index, model in enumerate(preflight["models"]):
        model_id = str(model["model_id"])
        model_root = imported_root / "per_model" / model_id
        status_path = model_root / "status.json"
        smoke_path = model_root / "smoke_manifest.json"
        asset_path = model_root / "asset_manifest.json"
        model_load_path = model_root / "model_load.json"
        scheduler_path = model_root / "scheduler.json"
        throughput_path = model_root / "throughput.json"
        memory_path = model_root / "memory.json"
        required_reports = {
            "status": status_path,
            "model load": model_load_path,
            "scheduler": scheduler_path,
            "smoke": smoke_path,
            "asset": asset_path,
            "throughput": throughput_path,
            "memory": memory_path,
        }
        missing_reports = [name for name, path in required_reports.items() if not path.is_file()]
        if missing_reports:
            raise ValueError(f"{model_id}: imported preflight is missing {', '.join(missing_reports)} report(s)")
        completion = json.loads(status_path.read_text(encoding="utf-8")) if status_path.is_file() else {}
        if (
            completion.get("status_code") != "PREFLIGHT_PASS"
            or completion.get("configuration_hash") != preflight["configuration_hash"]
        ):
            raise ValueError(f"{model_id}: imported PREFLIGHT_PASS identity is invalid")
        model_load = json.loads(model_load_path.read_text(encoding="utf-8"))
        applied = model_load.get("applied_configuration") if isinstance(model_load, Mapping) else None
        if (
            model_load.get("status") != "MODEL_LOAD_PASS"
            or not isinstance(applied, Mapping)
            or applied.get("differences") != {}
        ):
            raise ValueError(f"{model_id}: model-load or frozen-configuration application did not pass")
        scheduler = json.loads(scheduler_path.read_text(encoding="utf-8"))
        if scheduler.get("status") != "SCHEDULER_VALIDATED" or not scheduler.get("applied"):
            raise ValueError(f"{model_id}: scheduler preflight is incomplete")
        smoke = json.loads(smoke_path.read_text(encoding="utf-8"))
        smoke_rows = smoke.get("images") if isinstance(smoke, Mapping) else None
        if (
            smoke.get("status") != "SMOKE_GENERATION_PASS"
            or smoke.get("configuration_hash") != preflight["configuration_hash"]
            or not isinstance(smoke_rows, list)
            or not 1 <= len(smoke_rows) <= 4
        ):
            raise ValueError(f"{model_id}: smoke-generation report did not pass")
        expected_runtime = model["preflight_runtime_config"]
        for row in smoke_rows:
            relative = PurePosixPath(str(row.get("path", ""))) if isinstance(row, Mapping) else PurePosixPath("")
            if relative.is_absolute() or not relative.parts or ".." in relative.parts:
                raise ValueError(f"{model_id}: unsafe smoke-image path")
            image_path = model_root.joinpath(*relative.parts)
            if not image_path.is_file() or file_sha256(image_path) != row.get("sha256"):
                raise ValueError(f"{model_id}: smoke-image hash mismatch")
            with Image.open(image_path) as image:
                image.load()
                if (
                    image.mode != "RGB"
                    or image.size
                    != (int(expected_runtime["width"]), int(expected_runtime["height"]))
                ):
                    raise ValueError(f"{model_id}: smoke-image decode contract mismatch")
        adapter = adapter_for_model(model)
        if isinstance(adapter, UnsupportedModelAdapter):
            raise ValueError(f"{model_id}: {adapter.reason}")
        seeds = list(range(model_index * 1_000_000, model_index * 1_000_000 + count))
        seed_shards[model_id] = [seeds[index::shard_count] for index in range(shard_count)]
        runtime = _model_runtime(model, smoke=False)
        runtime["seeds"] = []
        model_record = {**model, "runtime_config": runtime, "capabilities": adapter.capabilities().as_dict()}
        models.append(model_record)
        calibration[model_id] = json.loads(throughput_path.read_text(encoding="utf-8"))
        if (
            int(calibration[model_id].get("effective_batch_size", 0)) <= 0
            or float(calibration[model_id].get("seconds_per_image", 0)) <= 0
        ):
            raise ValueError(f"{model_id}: throughput calibration is invalid")
        memory = json.loads(memory_path.read_text(encoding="utf-8"))
        if int(memory.get("peak_vram_bytes", -1)) < 0:
            raise ValueError(f"{model_id}: peak VRAM measurement is invalid")
        cache_root = imported_root / "model_cache" / f"{model_id}__asset"
        if not cache_root.is_dir():
            cache_root = imported_root / "model_cache" / model_id
        if not cache_root.is_dir():
            raise FileNotFoundError(f"{model_id}: imported local model cache missing")
        asset_payload = json.loads(asset_path.read_text(encoding="utf-8"))
        validate_asset_manifest(asset_payload)
        validate_asset_identity(
            asset_payload,
            model_or_extractor_id=model_id,
            revision=str(model["revision"]),
        )
        portable_asset = portable_asset_manifest(
            asset_payload,
            snapshot_path=f"model_cache/{model_id}",
            preflight_manifest_sha256=file_sha256(asset_path),
        )
        validate_asset_manifest(portable_asset, cache_root=cache_root)
        portable_asset_path = portable_assets_dir / f"{model_id}.json"
        _write_json(portable_asset, portable_asset_path)
        input_mapping[f"asset_manifests/{model_id}.json"] = portable_asset_path
        input_mapping[f"model_cache/{model_id}"] = cache_root
    timestamp = _timestamp()
    identity_hash = stable_hash_json({"models": models, "seed_shards": seed_shards, "scale": scale})[:12]
    config = _freeze(
        {
            "kind": "generation",
            "run_id": f"cifar10__generation__{scale}__none__{identity_hash}__{timestamp}",
            "mode": "force_new_run",
            "benchmark_id": "cifar10",
            "scale": scale,
            "asset_policy": AssetPolicy.OFFLINE_PACKAGED_CACHE.value,
            "network_mode": NetworkMode.ONLINE_DEPENDENCIES_OFFLINE_ASSETS.value,
            "dependency_network_allowed": True,
            "model_asset_network_allowed": False,
            "requested_gpu_count": 2,
            "allow_single_gpu_fallback": False,
            "environment_profile": "kaggle_t4x2_generation",
            "preflight_configuration_hash": preflight["configuration_hash"],
            "asset_manifest_hash": stable_hash_json({key: file_sha256(path) for key, path in input_mapping.items() if str(key).startswith("asset_manifests/")}),
            "reference_manifest_hash": file_sha256(reference),
            "samples_per_model": count,
            "pilot_profile": dict(profile_snapshot),
            "study_hash": study["configuration_hash"],
            "models": models,
            "seed_shards": seed_shards,
            "output_schema_version": expected_output_schema("generation")["schema_version"],
            "evidence_class": "run_log_only",
            "claim_allowed": False,
        }
    )
    path = out / "generation_config.yaml"
    _write_yaml(config, path)
    _write_json({"seed_shards": seed_shards, "configuration_hash": config["configuration_hash"], "claim_allowed": False}, out / "seed_ledger.json")
    runtime_dir = out / "model_runtime_configs"
    runtime_dir.mkdir()
    for model in models:
        _write_json(model["runtime_config"], runtime_dir / f"{model['model_id']}.json")
    _write_json(calibration, out / "runtime_calibration.json")
    _write_json(expected_output_schema("generation"), out / "expected_output_schema.json")
    _write_json({"run_id": config["run_id"], "configuration_hash": config["configuration_hash"], "input_manifest_hash": config["reference_manifest_hash"], "asset_manifest_hash": config["asset_manifest_hash"], "claim_allowed": False}, out / "run_identity.json")
    (out / "KAGGLE_INSTRUCTIONS.md").write_text("# Kaggle generation\n\nValidate, upload, run the canonical T4x2 generation notebook, copy back, validate, and import. claim_allowed=false.\n", encoding="utf-8")
    input_mapping.update(
        {
            "seed_ledger.json": out / "seed_ledger.json",
            "model_runtime_configs": runtime_dir,
            "runtime_calibration.json": out / "runtime_calibration.json",
            "expected_output_schema.json": out / "expected_output_schema.json",
            "run_identity.json": out / "run_identity.json",
            "KAGGLE_INSTRUCTIONS.md": out / "KAGGLE_INSTRUCTIONS.md",
        }
    )
    package = build_notebook_input_package(kind="generation", config_path=path, inputs=input_mapping, out_zip=out / f"certgen_cvpr_generation_{scale}_input.zip", manifest_out=out / "generation_input_manifest.json")
    return {"status": "GENERATION_PACKAGE_READY", "config": str(path), "package": package, "claim_allowed": False}


def prepare_features(
    *,
    out_dir: str | Path,
    generation_import: str | Path,
    preflight_import: str | Path = "data/results/cvpr/preflight_import_status.json",
    reference_manifest: str | Path = "registry/manifests/cvpr/cifar10_reference.jsonl",
    reference_draw_plan: str | Path = "registry/manifests/cvpr/reference_draw_plan.json",
    feature_registry: str | Path = "registry/cvpr/feature_space_registry.yaml",
    shard_count: int = 2,
    input_mode: str = "EMBED_IMAGES_IN_PACKAGE",
    external_image_manifest: str | Path | None = None,
    external_image_root: str | Path | None = None,
    mount_id: str | None = None,
    expected_mount_path: str | None = None,
    mount_manifest_hash: str | None = None,
    controls_dir: str | Path | None = None,
) -> dict[str, Any]:
    if input_mode not in {"EMBED_IMAGES_IN_PACKAGE", "MOUNT_EXTERNAL_IMAGE_DATASET"}:
        raise ValueError("unsupported feature input mode")
    generation_record = json.loads(Path(generation_import).read_text(encoding="utf-8"))
    generation_root = _imported_root(generation_record, "generation")
    preflight_record = json.loads(Path(preflight_import).read_text(encoding="utf-8"))
    preflight_root = _imported_root(preflight_record, "preflight")
    reference_path = Path(reference_manifest)
    draw_path = Path(reference_draw_plan)
    if not reference_path.is_file() or not draw_path.is_file():
        raise FileNotFoundError("materialized reference manifest and frozen reference draw plan are required")
    generation_config_path = generation_root / "configuration.yaml"
    generation_config = _yaml(generation_config_path) if generation_config_path.is_file() else {}
    study_hash = str(generation_config.get("study_hash", ""))
    if len(study_hash) != 64 or any(character not in "0123456789abcdef" for character in study_hash):
        raise ValueError("feature preparation requires the frozen study hash from generation")
    profile_snapshot = generation_config.get("pilot_profile")
    if not isinstance(profile_snapshot, Mapping):
        profile_snapshot = {
            "profile_id": "imported_nonclaim_generation",
            "generation_count": None,
            "reference_count": None,
            "claim_allowed": False,
        }
    frozen_controls = set(map(str, profile_snapshot.get("controls", [])))
    control_root = Path(controls_dir) if controls_dir is not None else None
    if frozen_controls and control_root is None:
        raise FileNotFoundError(
            "selected profile freezes controls; pass --controls-dir from `certgen prepare controls`"
        )
    if control_root is not None:
        control_verdict = validate_controls(control_root, study_hash=study_hash)
        if not control_verdict["passed"]:
            raise ValueError("control artifacts failed validation: " + "; ".join(control_verdict["errors"]))
    extractors: list[dict[str, Any]] = []
    input_mapping: dict[str, str | Path] = {}
    for row in _yaml(feature_registry).get("feature_spaces", []):
        extractor_id = str(row["feature_space_id"])
        status_path = preflight_root / "per_extractor" / extractor_id / "status.json"
        if not status_path.is_file():
            # Registered-but-not-selected extractors are intentionally absent.
            continue
        contract_path = preflight_root / "per_extractor" / extractor_id / "preprocessing_contract.json"
        calibration_path = preflight_root / "per_extractor" / extractor_id / "runtime_calibration.json"
        asset_path = preflight_root / "per_extractor" / extractor_id / "asset_manifest.json"
        model_load_path = preflight_root / "per_extractor" / extractor_id / "model_load.json"
        feature_smoke_path = preflight_root / "per_extractor" / extractor_id / "feature_smoke.json"
        if not all(
            path.is_file()
            for path in (
                status_path,
                contract_path,
                calibration_path,
                asset_path,
                model_load_path,
                feature_smoke_path,
            )
        ):
            raise ValueError(f"{extractor_id}: successful imported extractor preflight is required")
        status = json.loads(status_path.read_text(encoding="utf-8"))
        if (
            status.get("status_code") != "EXTRACTOR_PREFLIGHT_PASS"
            or status.get("configuration_hash")
            != generation_config.get("preflight_configuration_hash")
        ):
            raise ValueError(f"{extractor_id}: extractor preflight did not pass")
        model_load = json.loads(model_load_path.read_text(encoding="utf-8"))
        if model_load.get("status") != "EXTRACTOR_LOAD_PASS":
            raise ValueError(f"{extractor_id}: extractor model load did not pass")
        feature_smoke = json.loads(feature_smoke_path.read_text(encoding="utf-8"))
        smoke_shape = feature_smoke.get("shape") if isinstance(feature_smoke, Mapping) else None
        if (
            feature_smoke.get("status") != "FEATURE_SMOKE_PASS"
            or feature_smoke.get("finite") is not True
            or not isinstance(smoke_shape, list)
            or len(smoke_shape) != 2
            or int(smoke_shape[1]) != int(row["expected_dimension"])
        ):
            raise ValueError(f"{extractor_id}: extractor feature smoke did not pass")
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        if contract.get("preflight_status") != "MATCH" or contract.get("difference_report") != {}:
            raise ValueError(f"{extractor_id}: observed preprocessing differs from the frozen contract")
        observed_contract = contract.get("observed_contract")
        observed = (
            observed_contract.get("preprocessing")
            if isinstance(observed_contract, Mapping)
            else contract.get("observed")
        )
        if not isinstance(observed, Mapping):
            raise ValueError(f"{extractor_id}: preflight preprocessing contract has no observed preprocessing")
        calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
        extractor = {
            "feature_space_id": extractor_id,
            "model_identifier": observed["model_identifier"],
            "revision": observed["revision"],
            "expected_dimension": int(observed["output_dimension"]),
            "expected_preprocessing": observed,
            "batch_size": int(calibration.get("selected_batch_size", calibration.get("safe_batch_size", 0))),
            "tested_batch_size": int(calibration.get("tested_batch_size", calibration.get("safe_batch_size", 0))),
            "fallback_batch_size": int(calibration.get("fallback_batch_size", calibration.get("safe_batch_size", 0))),
            "adapter_id": row.get("adapter_id") or contract.get("observed_contract", {}).get("adapter_id"),
            "output_definition": contract.get("observed_contract", {}).get("output_definition")
            or row.get("output_definition"),
        }
        if extractor["batch_size"] <= 0 or extractor["batch_size"] > extractor["tested_batch_size"]:
            raise ValueError(f"{extractor_id}: selected batch size was not truthfully tested")
        extractors.append(extractor)
        input_mapping[f"preprocessing_contracts/{extractor_id}.json"] = contract_path
        cache_root = preflight_root / "model_cache" / f"{extractor_id}__asset"
        if not cache_root.is_dir():
            cache_root = preflight_root / "model_cache" / extractor_id
        if not cache_root.is_dir():
            raise FileNotFoundError(f"{extractor_id}: imported local extractor cache missing")
        asset_payload = json.loads(asset_path.read_text(encoding="utf-8"))
        validate_asset_manifest(asset_payload)
        validate_asset_identity(
            asset_payload,
            model_or_extractor_id=extractor_id,
            revision=str(row["revision"]),
        )
        portable_asset = portable_asset_manifest(
            asset_payload,
            snapshot_path=f"model_cache/{extractor_id}",
            preflight_manifest_sha256=file_sha256(asset_path),
        )
        validate_asset_manifest(portable_asset, cache_root=cache_root)
        input_mapping[f"model_cache/{extractor_id}"] = cache_root
        portable_dir = Path(out_dir) / "asset_manifests"
        portable_dir.mkdir(parents=True, exist_ok=True)
        portable_path = portable_dir / f"{extractor_id}.json"
        _write_json(portable_asset, portable_path)
        input_mapping[f"asset_manifests/{extractor_id}.json"] = portable_path
    if not extractors:
        raise ValueError("feature builder found no selected successful extractor preflight rows")

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    image_rows: list[dict[str, Any]] = []
    if input_mode == "MOUNT_EXTERNAL_IMAGE_DATASET":
        if not all((external_image_manifest, external_image_root, mount_id, mount_manifest_hash)):
            raise ValueError("external mount mode requires manifest/root/dataset identity/hash")
        if len(str(mount_manifest_hash)) != 64:
            raise ValueError("mount_manifest_hash must be a SHA-256")
        if file_sha256(str(external_image_manifest)) != str(mount_manifest_hash):
            raise ValueError("external image manifest differs from mount_manifest_hash")
        image_rows = read_image_manifest(
            str(external_image_manifest), root=str(external_image_root), decode=True
        )
    else:
        embedded_root = out / "images"
        embedded_root.mkdir()
        reference_rows = [
            json.loads(raw)
            for raw in reference_path.read_text(encoding="utf-8").splitlines()
            if raw.strip()
        ]
        reference_by_id = {str(row["sample_id"]): row for row in reference_rows}
        if len(reference_by_id) != len(reference_rows):
            raise ValueError("reference manifest sample IDs must be unique")
        draw_plan = json.loads(draw_path.read_text(encoding="utf-8"))
        reference_count = int(profile_snapshot.get("reference_count") or draw_plan.get("num_draws", 0))
        draw_validation = validate_reference_draw_plan(
            draw_plan,
            source_ids=[str(row["sample_id"]) for row in reference_rows],
            min_draws=reference_count,
        )
        if not draw_validation["passed"] or int(draw_plan.get("num_draws", 0)) != reference_count:
            raise ValueError("reference draw plan does not exactly match the selected pilot reference count")
        reference_manifest_hash = file_sha256(reference_path)
        for draw in draw_plan["draws"]:
            source_row = reference_by_id[str(draw["source_id"])]
            raw_source = source_row.get("path") or source_row.get("image_path")
            if not raw_source:
                raise ValueError("reference row has no historical source path")
            source = Path(str(raw_source))
            if not source.is_absolute():
                source = reference_path.parent / source
            destination = embedded_root / "reference" / f"{draw['draw_id']}.png"
            destination.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(source) as image:
                converted = image.convert("RGB")
                converted.save(destination, format="PNG")
                width, height = converted.size
            image_rows.append(
                {
                    "sample_id": str(draw["draw_id"]),
                    "role": "reference",
                    "model_id": "reference",
                    "relative_image_path": destination.relative_to(out).as_posix(),
                    "image_hash": file_sha256(destination),
                    "seed": None,
                    "prompt_or_class_id": source_row.get("class_label"),
                    "width": width,
                    "height": height,
                    "mode": "RGB",
                    "source_run_id": "reference_materialization",
                    "source_manifest_hash": reference_manifest_hash,
                }
            )
        generated_counts: dict[str, int] = {}
        for manifest in sorted(generation_root.glob("per_model/*/per_shard/*/manifest.jsonl")):
            for source_row in read_image_manifest(manifest, root=manifest.parent, decode=True):
                model_id = str(source_row["model_id"])
                source = manifest.parent / source_row["relative_image_path"]
                destination = embedded_root / model_id / f"{source_row['sample_id']}.png"
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists():
                    raise ValueError(f"duplicate generated sample destination: {destination}")
                shutil.copy2(source, destination)
                row = dict(source_row)
                row["relative_image_path"] = destination.relative_to(out).as_posix()
                image_rows.append(row)
                generated_counts[model_id] = generated_counts.get(model_id, 0) + 1
        if not generated_counts:
            raise ValueError("generation import contains no canonical image manifests")
        expected_generated = profile_snapshot.get("generation_count")
        if expected_generated is not None and any(
            count != int(expected_generated) for count in generated_counts.values()
        ):
            raise ValueError(
                f"generated image counts differ from the selected profile: {generated_counts}"
            )
        if control_root is not None:
            control_manifest = control_root / "control_image_manifest.jsonl"
            for source_row in read_image_manifest(control_manifest, root=control_root, decode=True):
                source = control_root / source_row["relative_image_path"]
                destination = (
                    embedded_root
                    / "controls"
                    / str(source_row["model_id"])
                    / f"{source_row['sample_id']}.png"
                )
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists():
                    raise ValueError(f"duplicate control sample destination: {destination}")
                shutil.copy2(source, destination)
                row = dict(source_row)
                row["relative_image_path"] = destination.relative_to(out).as_posix()
                image_rows.append(row)
    image_rows.sort(key=lambda row: (row["role"], row["model_id"], row["sample_id"]))
    image_manifest = out / "image_manifest.jsonl"
    image_root = out if input_mode == "EMBED_IMAGES_IN_PACKAGE" else Path(str(external_image_root))
    write_image_manifest(image_rows, image_manifest, root=image_root, decode=True)
    by_role: dict[str, list[dict[str, Any]]] = {}
    for row in image_rows:
        role_id = role_id_for_row(row)
        by_role.setdefault(role_id, []).append(row)
    shards: list[dict[str, Any]] = []
    shard_dir = out / "image_shards"
    shard_dir.mkdir()
    offset = 0
    for role, role_rows in sorted(by_role.items()):
        for shard_index in range(shard_count):
            selected = role_rows[shard_index::shard_count]
            if not selected:
                continue
            shard_id = f"{role}__shard_{shard_index:04d}"
            path = shard_dir / f"{shard_id}.jsonl"
            path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in selected), encoding="utf-8")
            shards.append({"shard_id": shard_id, "role": role, "model_id": selected[0]["model_id"], "indices": list(range(offset, offset + len(selected))), "manifest": path.name, "manifest_sha256": file_sha256(path)})
            offset += len(selected)
    role_manifest = out / "role_manifest.csv"
    with role_manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=tuple(ImageManifestRow.__dataclass_fields__),
        )
        writer.writeheader()
        writer.writerows(image_rows)
    config = _freeze(
        {
            "kind": "features",
            "run_id": f"cifar10__features__imported__none__{stable_hash_json(image_rows)[:12]}__{_timestamp()}",
            "mode": "force_new_run",
            "benchmark_id": "cifar10",
            "scale": "imported",
            "pilot_profile": dict(profile_snapshot),
            "study_hash": study_hash,
            "feature_input_mode": input_mode,
            "image_root": "." if input_mode == "EMBED_IMAGES_IN_PACKAGE" else "runtime_resolved_from_dataset_manifest",
            "mount_id": mount_id,
            "dataset_identity": mount_id,
            "dataset_manifest_hash": mount_manifest_hash,
            "mount_manifest_hash": mount_manifest_hash,
            "asset_policy": AssetPolicy.OFFLINE_PACKAGED_CACHE.value,
            "network_mode": NetworkMode.ONLINE_DEPENDENCIES_OFFLINE_ASSETS.value,
            "dependency_network_allowed": True,
            "model_asset_network_allowed": False,
            "requested_gpu_count": 2,
            "allow_single_gpu_fallback": False,
            "environment_profile": "kaggle_t4x2_features",
            "source_manifest_hash": file_sha256(role_manifest),
            "reference_draw_plan": json.loads(draw_path.read_text(encoding="utf-8")),
            "reference_draw_plan_hash": file_sha256(draw_path),
            "control_artifacts_hash": (
                file_sha256(control_root / "integrity_manifest.json") if control_root is not None else None
            ),
            "extractors": extractors,
            "image_shards": shards,
            "expected_role_counts": {role: len(rows) for role, rows in by_role.items()},
            "expected_model_ids": sorted({row["model_id"] for row in image_rows}),
            "image_manifest_schema_version": "certgen.cvpr.image_manifest.v1",
            "output_schema_version": expected_output_schema("feature")["schema_version"],
            "evidence_class": "run_log_only",
            "claim_allowed": False,
        }
    )
    # The package validator uses the hash of the embedded object, not the source file hash.
    config["reference_draw_plan_hash"] = stable_hash_json(config["reference_draw_plan"])
    config = _freeze(config)
    config_path = out / "feature_config.yaml"
    _write_yaml(config, config_path)
    _write_yaml(dict(profile_snapshot), out / "profile_snapshot.yaml")
    shutil.copy2(draw_path, out / "reference_draw_plan.json")
    if control_root is not None:
        control_package = out / "control_manifests"
        control_package.mkdir()
        for name in (
            "null_control_manifest.json",
            "obvious_gap_manifest.json",
            "controls_summary.json",
            "integrity_manifest.json",
        ):
            shutil.copy2(control_root / name, control_package / name)
    extractor_dir = out / "extractor_configs"
    extractor_dir.mkdir()
    for extractor in extractors:
        _write_json(extractor, extractor_dir / f"{extractor['feature_space_id']}.json")
    _write_json(expected_output_schema("feature"), out / "expected_output_schema.json")
    _write_json({"run_id": config["run_id"], "configuration_hash": config["configuration_hash"], "input_manifest_hash": config["source_manifest_hash"], "asset_manifest_hash": stable_hash_json({key: file_sha256(value) for key, value in input_mapping.items() if key.startswith("asset_manifests/")}), "claim_allowed": False}, out / "run_identity.json")
    (out / "KAGGLE_INSTRUCTIONS.md").write_text("# Kaggle features\n\nValidate, upload, run the canonical T4x2 feature notebook, copy back, validate, import, then merge locally. claim_allowed=false.\n", encoding="utf-8")
    input_mapping.update(
        {
            "role_manifest.csv": role_manifest,
            "manifests/images.jsonl": image_manifest,
            "profile_snapshot.yaml": out / "profile_snapshot.yaml",
            "reference_draw_plan.json": out / "reference_draw_plan.json",
            "extractor_configs": extractor_dir,
            "image_shards": shard_dir,
            "expected_output_schema.json": out / "expected_output_schema.json",
            "run_identity.json": out / "run_identity.json",
            "KAGGLE_INSTRUCTIONS.md": out / "KAGGLE_INSTRUCTIONS.md",
        }
    )
    if control_root is not None:
        input_mapping["control_manifests"] = out / "control_manifests"
    if input_mode == "EMBED_IMAGES_IN_PACKAGE":
        input_mapping["images"] = out / "images"
    else:
        mount_payload = {
            "mount_id": mount_id,
            "dataset_identity": mount_id,
            "dataset_manifest_hash": mount_manifest_hash,
            "mount_manifest_hash": mount_manifest_hash,
            "image_manifest_sha256": file_sha256(image_manifest),
            "claim_allowed": False,
        }
        _write_json(mount_payload, out / "mount_manifest.json")
        input_mapping["mount_manifest.json"] = out / "mount_manifest.json"
    package = build_notebook_input_package(kind="features", config_path=config_path, inputs=input_mapping, out_zip=out / "certgen_cvpr_features_input.zip", manifest_out=out / "feature_input_manifest.json")
    return {"status": "FEATURE_PACKAGE_READY", "config": str(config_path), "package": package, "claim_allowed": False}


def prepare_family(
    *,
    out_dir: str | Path,
    comparison_registry: str | Path = "registry/cvpr/comparison_registry.csv",
    alpha: float = 0.05,
    study_path: str | Path | None = None,
) -> dict[str, Any]:
    if not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0,1)")
    with Path(comparison_registry).open(encoding="utf-8", newline="") as handle:
        all_rows = list(csv.DictReader(handle))
    identifiers = [row.get("comparison_id", "") for row in all_rows]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("comparison registry contains duplicate comparison IDs")
    study: dict[str, Any] | None = None
    if study_path is not None:
        study = require_frozen_study(study_path)
        selected_comparisons = {
            str(row["comparison_id"])
            for row in study["model_pairs"]
            if isinstance(row, Mapping)
        }
        controls = set(map(str, study.get("controls", [])))
        overlap = selected_comparisons & controls
        if overlap:
            raise ValueError(
                "family builder refuses sanity controls in confirmatory comparisons: "
                + ", ".join(sorted(overlap))
            )
        if study.get("controls_in_confirmatory_family") is not False:
            raise ValueError("frozen study must set controls_in_confirmatory_family=false")
        if study.get("controls_claim_allowed") is not False:
            raise ValueError("frozen study must set controls_claim_allowed=false")
        selected_family = set(map(str, study["multiplicity_families"]))
        # A frozen study may promote an explicitly selected planning row into
        # this one immutable family.  Arbitrary/draft rows remain ineligible.
        study_allowed_statuses = {"registered", "frozen", "planning_only"}
        eligible = [
            row
            for row in all_rows
            if row.get("prospective_or_posthoc") == "prospective"
            and row.get("status") in study_allowed_statuses
            and row.get("comparison_id") in selected_comparisons
            and row.get("family_id") in selected_family
        ]
        missing = sorted(selected_comparisons - {str(row["comparison_id"]) for row in eligible})
        if missing:
            raise ValueError(f"frozen study comparisons are absent from the prospective registry: {missing}")
    else:
        eligible = [
            row for row in all_rows
            if row.get("prospective_or_posthoc") == "prospective" and row.get("status") in {"registered", "frozen"}
        ]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if not eligible:
        payload = {"status": "BLOCKED_NO_FROZEN_COMPARISONS", "claim_allowed": False}
        atomic_write_json(payload, out / "prepare_family_blocked.json")
        return payload
    benchmarks = {row.get("benchmark_id") or row.get("benchmark") for row in eligible}
    families = {row.get("family_id") for row in eligible}
    if len(benchmarks) != 1 or len(families) != 1:
        raise ValueError("family builder refuses mixed benchmarks or family IDs")
    hypotheses: list[dict[str, str]] = []
    for row in eligible:
        required = ("comparison_id", "model_a", "model_b", "feature_spaces", "metrics", "sample_budgets")
        if any(not row.get(key) for key in required):
            raise ValueError(f"comparison row {row.get('comparison_id')} is incomplete")
        feature_spaces = (
            list(map(str, study["feature_spaces"]))
            if study is not None
            else str(row["feature_spaces"]).split("|")
        )
        metrics = list(map(str, study["metrics"])) if study is not None else str(row["metrics"]).split("|")
        budgets = (
            list(map(str, study["sample_budgets"]))
            if study is not None
            else str(row["sample_budgets"]).split("|")
        )
        for feature_space in feature_spaces:
            for metric in metrics:
                for budget in budgets:
                    hypotheses.append(
                        {
                            "hypothesis_id": f"{row['comparison_id']}__{feature_space}__{metric}__n{budget}",
                            "comparison_id": row["comparison_id"],
                            "model_a": row["model_a"],
                            "model_b": row["model_b"],
                            "feature_space": feature_space,
                            "metric": metric,
                            "sample_budget": budget,
                        }
                    )
    payload = _freeze(
        {
            "schema_version": "certgen.cvpr.family.v2",
            "family_id": next(iter(families)),
            "benchmark_id": next(iter(benchmarks)),
            "benchmark": next(iter(benchmarks)),
            "analysis_scope": "prospective comparison x feature-space x metric x budget family",
            "feature_space": "multiple_registered_feature_spaces" if study is not None and len(study["feature_spaces"]) > 1 else (
                str(study["feature_spaces"][0]) if study is not None else "registry_cartesian"
            ),
            "feature_spaces": list(map(str, study["feature_spaces"])) if study is not None else sorted({item["feature_space"] for item in hypotheses}),
            "metric": str(study["metrics"][0]) if study is not None and len(study["metrics"]) == 1 else "registered_metrics",
            "kernel": "rbf",
            "bandwidth": "gamma_0.5_fixed",
            "status": "frozen",
            "comparisons": sorted(row["comparison_id"] for row in eligible),
            "comparison_registry_statuses": {
                row["comparison_id"]: row["status"] for row in sorted(
                    eligible, key=lambda item: item["comparison_id"]
                )
            },
            "eligibility_rule": (
                "prospective and registered/frozen, or planning_only explicitly selected by the frozen study"
                if study is not None
                else "prospective and registered/frozen"
            ),
            "model_pairs": sorted(row["comparison_id"] for row in eligible),
            "hypotheses": sorted(hypotheses, key=lambda row: row["hypothesis_id"]),
            "dimensions": {
                "feature_space": list(map(str, study["feature_spaces"])) if study is not None else sorted({item["feature_space"] for item in hypotheses}),
                "metric": list(map(str, study["metrics"])) if study is not None else sorted({item["metric"] for item in hypotheses}),
                "sample_budget": list(map(str, study["sample_budgets"])) if study is not None else sorted({item["sample_budget"] for item in hypotheses}),
            },
            "study_hash": study["configuration_hash"] if study is not None else None,
            "alpha_total": alpha,
            "number_of_hypotheses": len(hypotheses),
            "alpha_per_hypothesis": alpha / len(hypotheses),
            "multiplicity_method": "bonferroni",
            "controls_in_confirmatory_family": False,
            "controls_claim_allowed": False,
            "sanity_controls": list(map(str, study.get("controls", []))) if study is not None else [],
            "claim_allowed": False,
        }
    )
    atomic_write_json(payload, out / "family.json")
    return payload
