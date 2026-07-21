"""Synthetic-only generation worker exercising the production batch/resume engine."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from certgen.core.hashing import file_sha256
from certgen.cvpr.contracts import atomic_write_json
from certgen.cvpr.image_manifest import write_image_manifest
from certgen.notebooks.generation_runtime import (
    FixtureBatchAdapter,
    GenerationSample,
    GenerationSettings,
    generate_batches,
)
from certgen.notebooks.worker_contract import completion_identity_fields
from certgen.notebooks.workers.common import require_gpu_pin


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--model-id", default="fixture_model")
    parser.add_argument("--seeds", required=True)
    parser.add_argument("--config-hash", required=True)
    parser.add_argument("--shard-id", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--oom-above", type=int)
    args = parser.parse_args(argv)
    physical, visible = require_gpu_pin()
    seeds = [int(value) for value in args.seeds.split(",") if value]
    samples = [GenerationSample(f"{args.model_id}__seed_{seed:04d}", seed) for seed in seeds]
    output = Path(args.out)
    result = generate_batches(
        adapter=FixtureBatchAdapter(size=(8, 8), oom_above=args.oom_above),
        samples=samples,
        settings=GenerationSettings(
            model_id=args.model_id,
            scheduler="fixture",
            inference_steps=1,
            guidance_scale=None,
            precision="float32",
            device="fixture_cpu",
            configured_batch_size=4,
            image_size=(8, 8),
        ),
        output_root=output,
        configuration_hash=args.config_hash,
        resume=args.resume,
    )
    rows = []
    for image in sorted((output / "images").glob("*.png")):
        rows.append(
            {
                "sample_id": image.stem,
                "role": "model",
                "model_id": args.model_id,
                "relative_image_path": f"images/{image.name}",
                "image_hash": file_sha256(image),
                "seed": int(image.stem.rsplit("_", 1)[-1]),
                "prompt_or_class_id": None,
                "width": 8,
                "height": 8,
                "mode": "RGB",
                "source_run_id": f"{args.model_id}:generation",
                "source_manifest_hash": args.config_hash,
            }
        )
    write_image_manifest(rows, output / "manifest.jsonl", root=output, decode=True)
    atomic_write_json({"status_code": "SHARD_COMPLETE", "model_id": args.model_id, "shard_id": args.shard_id, "passed": True, "claim_allowed": False}, output / "status.json")
    atomic_write_json({**completion_identity_fields("fixture", config_schema_version="certgen.fixture.generation_config.v1", output_schema_version="certgen.fixture.generation_output.v1"), "status": "success", "physical_gpu_assignment": physical, "cuda_visible_devices": visible, "visible_gpu_count": "fixture_not_probed", "logical_device": "fixture_cpu", "gpu_name": "fixture_no_gpu", "CUDA_version": "fixture_no_cuda", "PyTorch_version": "fixture_not_imported", "worker_PID": os.getpid(), "configuration_hash": args.config_hash, "input_manifest_hash": "synthetic_fixture", "asset_manifest_hash": "synthetic_fixture", "shard_ID": args.shard_id, "generation": result, "outputs": {"status.json": file_sha256(output / "status.json"), "manifest.jsonl": file_sha256(output / "manifest.jsonl")}, "claim_allowed": False}, output / "worker_status.json")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
