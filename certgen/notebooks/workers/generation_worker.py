"""One-GPU generation worker using a validated family-specific adapter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from PIL import Image

from certgen.core.hashing import file_sha256
from certgen.cvpr.contracts import atomic_write_json
from certgen.cvpr.image_manifest import write_image_manifest
from certgen.cvpr.model_adapters import DiffusersAdapter, UnsupportedModelAdapter, adapter_for_model
from certgen.notebooks.generation_runtime import GenerationSample, GenerationSettings, generate_batches
from certgen.notebooks.model_assets import resolve_local_snapshot, validate_asset_identity, validate_asset_manifest
from certgen.notebooks.network_policy import network_policy_from_config
from certgen.notebooks.worker_contract import completion_identity_fields
from certgen.notebooks.workers.common import hardware_record, load_configuration, require_gpu_pin


class FrozenModelBatchAdapter:
    """Bridge the generic batch/resume engine to one frozen model adapter."""

    def __init__(self, adapter: DiffusersAdapter, runtime_config: Mapping[str, Any]) -> None:
        self.adapter = adapter
        self.runtime_config = dict(runtime_config)
        self.supports_generator_list = adapter.capabilities().supports_generator_list

    def generate(self, *, seeds: Sequence[int], prompts: Sequence[str | None]) -> Sequence[Image.Image]:
        applied = dict(self.runtime_config)
        applied["seeds"] = [int(seed) for seed in seeds]
        if self.adapter.capabilities().supports_prompt_conditioning:
            applied["prompts"] = [prompt or "" for prompt in prompts]
        else:
            applied["prompts"] = []
        if applied.get("class_ids"):
            applied["class_ids"] = list(applied["class_ids"][: len(seeds)])
        return self.adapter.generate_batch(applied)

    def clear_cache(self) -> None:
        torch = self.adapter._torch
        if torch is not None:
            torch.cuda.empty_cache()


def _load_asset_manifest(path: Path, cache_root: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("asset manifest must be an object")
    validate_asset_manifest(payload, cache_root=cache_root)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--shard-id", required=True)
    parser.add_argument("--asset-manifest", required=True)
    parser.add_argument("--cache-root", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)

    require_gpu_pin()
    config = load_configuration(args.config)
    network = network_policy_from_config(config)
    if network.model_asset_network_allowed:
        raise RuntimeError("generation requires preflighted offline model assets")
    model = next((row for row in config["models"] if row["model_id"] == args.model_id), None)
    if model is None:
        raise ValueError(f"model absent from configuration: {args.model_id}")
    shards = config["seed_shards"][args.model_id]
    try:
        shard_index = int(args.shard_id.rsplit("_", 1)[-1])
        seeds = [int(seed) for seed in shards[shard_index]]
    except (ValueError, IndexError) as error:
        raise ValueError(f"invalid shard ID: {args.shard_id}") from error
    asset = _load_asset_manifest(Path(args.asset_manifest), Path(args.cache_root))
    validate_asset_identity(asset, model_or_extractor_id=args.model_id, revision=str(model["revision"]))
    snapshot = resolve_local_snapshot(asset, runtime_cache_root=args.cache_root)
    torch, hardware = hardware_record(str(config["configuration_hash"]), args.shard_id)
    adapter = adapter_for_model(model, torch_module=torch)
    if isinstance(adapter, UnsupportedModelAdapter):
        raise NotImplementedError(adapter.reason)
    runtime = dict(model["runtime_config"])
    runtime["seeds"] = seeds
    runtime.setdefault("prompts", [])
    runtime.setdefault("class_ids", [])
    adapter.load(snapshot, runtime, "cuda:0")
    if not isinstance(adapter, DiffusersAdapter):  # pragma: no cover - current validated adapters
        raise TypeError("generation worker requires a diffusers adapter")
    bridge = FrozenModelBatchAdapter(adapter, runtime)
    samples = [
        GenerationSample(sample_id=f"{args.model_id}__seed_{seed:010d}", seed=seed)
        for seed in seeds
    ]
    settings = GenerationSettings(
        model_id=args.model_id,
        scheduler=str(runtime["scheduler"]),
        inference_steps=int(runtime["num_inference_steps"]),
        guidance_scale=runtime.get("guidance_scale"),
        precision=str(runtime["precision"]),
        device="cuda:0",
        configured_batch_size=int(runtime["batch_size"]),
        minimum_batch_size=int(runtime.get("minimum_batch_size", 1)),
        image_size=(int(runtime["width"]), int(runtime["height"])),
    )
    out = Path(args.out)
    result = generate_batches(
        adapter=bridge,
        samples=samples,
        settings=settings,
        output_root=out,
        configuration_hash=str(config["configuration_hash"]),
        resume=args.resume,
    )
    rows = []
    for manifest_path in sorted(out.glob("batches/*/batch_manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        rows.extend(manifest["images"])
    rows.sort(key=lambda row: row["sample_id"])
    for row in rows:
        row["source_run_id"] = str(config["run_id"])
        row["source_manifest_hash"] = str(config["configuration_hash"])
    write_image_manifest(rows, out / "manifest.jsonl", root=out, decode=True)
    atomic_write_json(adapter.applied_record or {}, out / "applied_configuration.json")
    atomic_write_json(
        {
            "status_code": "SHARD_COMPLETE",
            "passed": True,
            "model_id": args.model_id,
            "shard_id": args.shard_id,
            "configuration_hash": config["configuration_hash"],
            "manifest_sha256": file_sha256(out / "manifest.jsonl"),
            "effective_batch_size": result["effective_batch_size"],
            "claim_allowed": False,
        },
        out / "status.json",
    )
    outputs = {
        "status.json": file_sha256(out / "status.json"),
        "manifest.jsonl": file_sha256(out / "manifest.jsonl"),
        "applied_configuration.json": file_sha256(out / "applied_configuration.json"),
    }
    completion = {
        **completion_identity_fields(
            "generation",
            config_schema_version=str(config.get("schema_version", "certgen.cvpr.generation_config.v1")),
            output_schema_version=str(config["output_schema_version"]),
        ),
        "status": "success",
        "configuration_hash": config["configuration_hash"],
        "input_manifest_hash": str(config["reference_manifest_hash"]),
        "asset_manifest_hash": file_sha256(args.asset_manifest),
        "outputs": outputs,
        "claim_allowed": False,
    }
    atomic_write_json(completion, out / "worker_completion.json")
    atomic_write_json({**hardware, **completion, "generation": result}, out / "worker_status.json")
    adapter.unload()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
