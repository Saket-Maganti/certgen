"""One-GPU real model preflight worker.

Downloads are confined to this worker.  A pass requires cache validation, real
adapter load, configuration application, decoded smoke images, and clean unload.
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import Any

from PIL import Image

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.contracts import atomic_write_json
from certgen.cvpr.extractor_adapters import adapter_for_extractor, resolve_extractor_asset_from_environment
from certgen.cvpr.model_adapters import DiffusersAdapter, UnsupportedModelAdapter, adapter_for_model
from certgen.notebooks.model_assets import (
    AssetPolicy,
    AssetRequirement,
    inventory_cache,
    resolve_local_snapshot,
    validate_policy_preconditions,
    write_asset_manifest,
)
from certgen.notebooks.network_policy import network_policy_from_config
from certgen.notebooks.workers.common import hardware_record, load_configuration, require_gpu_pin
from certgen.notebooks.worker_contract import completion_identity_fields


def _validate_smoke(images: list[Image.Image], expected_size: tuple[int, int], output: Path) -> list[dict[str, Any]]:
    if not 1 <= len(images) <= 4:
        raise ValueError("model smoke output must contain 1-4 images")
    output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for index, image in enumerate(images):
        if not isinstance(image, Image.Image):
            raise TypeError("model smoke output did not decode to PIL.Image")
        converted = image.convert("RGB")
        if converted.size != expected_size:
            raise ValueError(f"smoke image size mismatch: {converted.size} != {expected_size}")
        # PIL RGB conversion fixes the decoded representation to uint8 [0, 255].
        path = output / f"smoke_{index:02d}.png"
        converted.save(path, format="PNG")
        with Image.open(path) as reopened:
            reopened.load()
            if reopened.mode != "RGB" or reopened.size != expected_size:
                raise ValueError("saved smoke image failed decode validation")
        rows.append(
            {
                "sample_index": index,
                "path": f"smoke_images/{path.name}",
                "sha256": file_sha256(path),
                "mode": "RGB",
                "width": expected_size[0],
                "height": expected_size[1],
                "claim_allowed": False,
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--asset-id", required=True)
    parser.add_argument("--shard-id", required=True)
    parser.add_argument("--cache-root", required=True)
    parser.add_argument("--asset-resolution-report")
    parser.add_argument("--out", required=True)
    parser.add_argument("--asset-only", action="store_true")
    args = parser.parse_args(argv)

    require_gpu_pin()
    config = load_configuration(args.config)
    network = network_policy_from_config(config)
    asset = next((row for row in config["assets"] if row["asset_id"] == args.asset_id), None)
    if asset is None:
        raise ValueError(f"asset absent from configuration: {args.asset_id}")
    if asset.get("asset_kind") != "model" and not args.asset_only:
        raise ValueError(f"non-model asset requires --asset-only: {args.asset_id}")
    policy = AssetPolicy(str(asset["policy"]))
    requirement = AssetRequirement(
        asset_id=asset["asset_id"],
        model_or_extractor_id=asset["model_or_extractor_id"],
        revision=asset["revision"],
        source=asset["source"],
        license=asset["license"],
        authentication_required=asset["authentication_required"],
        expected_files=tuple(asset["expected_files"]),
    )
    validate_policy_preconditions(
        requirement,
        policy=policy,
        internet_enabled=network.model_asset_network_allowed,
        token_present=bool(os.environ.get("HF_TOKEN")),
        cache_root=args.cache_root,
    )
    if policy is AssetPolicy.OFFLINE_PACKAGED_CACHE:
        if not args.asset_resolution_report:
            raise ValueError("offline worker requires an authenticated asset-resolution report")
        from certgen.discovery import validate_resolved_asset

        resolved = validate_resolved_asset(
            args.asset_resolution_report,
            asset_id=str(asset["asset_id"]),
            expected_revision=str(asset["revision"]),
        )
        if Path(str(resolved["snapshot_root"])).resolve() != Path(args.cache_root).resolve():
            raise ValueError("worker cache root differs from the resolved private asset snapshot")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cache_root = Path(args.cache_root)
    if policy is AssetPolicy.ONLINE_PREFLIGHT_DOWNLOAD:
        cache_root.mkdir(parents=True, exist_ok=True)
    if asset.get("asset_kind") == "extractor":
        if not args.asset_only:
            raise ValueError("extractor asset acquisition requires --asset-only")
        extractor = next(
            row for row in config["extractors"] if row["feature_space_id"] == asset["model_or_extractor_id"]
        )
        extractor_adapter = adapter_for_extractor(extractor)
        manifest = resolve_extractor_asset_from_environment(
            extractor_adapter,
            asset,
            cache_root,
            policy=policy,
            internet_enabled=network.model_asset_network_allowed,
        )
        manifest_path = out / "asset_manifest.json"
        write_asset_manifest(manifest, manifest_path)
        atomic_write_json(
            {
                "status": "ASSET_CACHE_VALID",
                "asset_manifest_sha256": file_sha256(manifest_path),
                "extractor_adapter": extractor_adapter.adapter_id,
                "claim_allowed": False,
            },
            out / "asset_status.json",
        )
        completion = {
            **completion_identity_fields(
                "preflight",
                config_schema_version=str(config.get("schema_version", "certgen.cvpr.preflight_config.v1")),
                output_schema_version=str(config["output_schema_version"]),
            ),
            "status": "success",
            "status_code": "ASSET_CACHE_VALID",
            "configuration_hash": config["configuration_hash"],
            "input_manifest_hash": str(config.get("input_manifest_hash", "preflight_none")),
            "asset_manifest_hash": file_sha256(manifest_path),
            "outputs": {
                "asset_manifest.json": file_sha256(manifest_path),
                "asset_status.json": file_sha256(out / "asset_status.json"),
            },
            "evidence_class": "non_evidence_preflight",
            "claim_allowed": False,
        }
        atomic_write_json(completion, out / "worker_completion.json")
        atomic_write_json(completion, out / "status.json")
        return 0
    download_seconds = 0.0
    if policy is AssetPolicy.ONLINE_PREFLIGHT_DOWNLOAD:
        from huggingface_hub import snapshot_download

        start = time.monotonic()
        snapshot_download(
            repo_id=requirement.source,
            revision=requirement.revision,
            local_dir=cache_root,
            local_files_only=False,
            token=os.environ.get("HF_TOKEN"),
        )
        download_seconds = time.monotonic() - start
    manifest = inventory_cache(requirement, cache_root, policy)
    if manifest["validation_status"] != "VALIDATED":
        raise FileNotFoundError("preflight cache is incomplete after acquisition")
    manifest_path = out / "asset_manifest.json"
    write_asset_manifest(manifest, manifest_path)
    atomic_write_json(
        {"status": "ASSET_CACHE_VALID", "asset_manifest_sha256": file_sha256(manifest_path), "claim_allowed": False},
        out / "asset_status.json",
    )

    if args.asset_only:
        completion = {
            **completion_identity_fields(
                "preflight",
                config_schema_version=str(config.get("schema_version", "certgen.cvpr.preflight_config.v1")),
                output_schema_version=str(config["output_schema_version"]),
            ),
            "status": "success",
            "status_code": "ASSET_CACHE_VALID",
            "configuration_hash": config["configuration_hash"],
            "input_manifest_hash": str(config.get("input_manifest_hash", "preflight_none")),
            "asset_manifest_hash": file_sha256(manifest_path),
            "outputs": {
                "asset_manifest.json": file_sha256(manifest_path),
                "asset_status.json": file_sha256(out / "asset_status.json"),
            },
            "evidence_class": "non_evidence_preflight",
            "claim_allowed": False,
        }
        atomic_write_json(completion, out / "worker_completion.json")
        atomic_write_json(completion, out / "status.json")
        return 0

    model = next(row for row in config["models"] if row["model_id"] == asset["model_or_extractor_id"])

    adapter = adapter_for_model(model)
    if isinstance(adapter, UnsupportedModelAdapter):
        raise NotImplementedError(adapter.reason)
    if not isinstance(adapter, DiffusersAdapter):  # pragma: no cover - current validated families
        raise TypeError("model preflight requires a validated diffusers adapter")
    runtime = dict(model["preflight_runtime_config"])
    torch, hardware = hardware_record(str(config["configuration_hash"]), args.shard_id)
    torch.cuda.reset_peak_memory_stats(0)
    load_start = time.monotonic()
    adapter.load(resolve_local_snapshot(manifest), runtime, "cuda:0")
    load_seconds = time.monotonic() - load_start
    atomic_write_json(
        {
            "status": "MODEL_LOAD_PASS",
            "model_id": model["model_id"],
            "revision": model["revision"],
            "load_seconds": load_seconds,
            "adapter": adapter.adapter_name,
            "applied_configuration": adapter.applied_record,
            "claim_allowed": False,
        },
        out / "model_load.json",
    )
    atomic_write_json(
        {
            "requested": runtime["scheduler"],
            "applied": (adapter.applied_record or {}).get("scheduler_class"),
            "status": "SCHEDULER_VALIDATED",
            "claim_allowed": False,
        },
        out / "scheduler.json",
    )
    smoke_start = time.monotonic()
    images = list(adapter.generate_smoke(runtime))
    smoke_seconds = time.monotonic() - smoke_start
    smoke_rows = _validate_smoke(images, (int(runtime["width"]), int(runtime["height"])), out / "smoke_images")
    atomic_write_json(
        {
            "status": "SMOKE_GENERATION_PASS",
            "images": smoke_rows,
            "configuration_hash": config["configuration_hash"],
            "claim_allowed": False,
        },
        out / "smoke_manifest.json",
    )
    peak_vram = int(torch.cuda.max_memory_allocated(0))
    adapter.unload()
    throughput = {
        "smoke_seconds": smoke_seconds,
        "seconds_per_image": smoke_seconds / len(images),
        "images_per_minute": len(images) * 60.0 / max(smoke_seconds, 1e-9),
        "effective_batch_size": len(images),
        "download_cache_seconds": download_seconds,
        "claim_allowed": False,
    }
    atomic_write_json(throughput, out / "throughput.json")
    atomic_write_json({"peak_vram_bytes": peak_vram, "claim_allowed": False}, out / "memory.json")
    outputs = {
        name: file_sha256(out / name)
        for name in ("asset_manifest.json", "model_load.json", "scheduler.json", "smoke_manifest.json", "throughput.json", "memory.json")
    }
    completion = {
        **completion_identity_fields(
            "preflight",
            config_schema_version=str(config.get("schema_version", "certgen.cvpr.preflight_config.v1")),
            output_schema_version=str(config["output_schema_version"]),
        ),
        "status": "success",
        "status_code": "PREFLIGHT_PASS",
        "configuration_hash": config["configuration_hash"],
        "input_manifest_hash": str(config.get("input_manifest_hash", "preflight_none")),
        "asset_manifest_hash": file_sha256(manifest_path),
        "outputs": outputs,
        "evidence_class": "non_evidence_preflight",
        "claim_allowed": False,
    }
    atomic_write_json(completion, out / "worker_completion.json")
    atomic_write_json(
        {
            **hardware,
            **completion,
            "model_id": model["model_id"],
            "adapter_capabilities": adapter.capabilities().as_dict(),
            "report_hash": stable_hash_json({"outputs": outputs, "runtime": runtime}),
        },
        out / "status.json",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
