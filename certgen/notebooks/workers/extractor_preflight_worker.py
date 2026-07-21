"""One-GPU real extractor preflight with truthful batch calibration."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from certgen.core.hashing import file_sha256
from certgen.cvpr.contracts import atomic_write_json
from certgen.cvpr.extractor_adapters import adapter_for_extractor, package_versions_for
from certgen.notebooks.workers.common import hardware_record, load_configuration, require_gpu_pin
from certgen.notebooks.worker_contract import completion_identity_fields


def _fixture_images(count: int) -> list[Image.Image]:
    if count <= 0:
        raise ValueError("calibration fixture count must be positive")
    return [
        Image.new("RGB", (32, 32), (index * 17 % 255, index * 31 % 255, index * 47 % 255))
        for index in range(count)
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--extractor-id", required=True)
    parser.add_argument("--shard-id", required=True)
    parser.add_argument("--asset-manifest", required=True)
    parser.add_argument("--cache-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    require_gpu_pin()
    config = load_configuration(args.config)
    extractor = next(row for row in config["extractors"] if row["feature_space_id"] == args.extractor_id)
    asset = json.loads(Path(args.asset_manifest).read_text(encoding="utf-8"))
    if not isinstance(asset, dict):
        raise ValueError("extractor asset manifest must be an object")
    if asset.get("model_or_extractor_id") != args.extractor_id:
        raise ValueError("extractor asset identity mismatch")
    torch, hardware = hardware_record(str(config["configuration_hash"]), args.shard_id)
    packages = package_versions_for(args.extractor_id, str(torch.__version__))
    adapter = adapter_for_extractor(extractor)
    load_started = time.monotonic()
    adapter.load(asset, args.cache_root, "cuda:0")
    load_seconds = time.monotonic() - load_started
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    contract = adapter.contract_report(packages, difference_report=out / "preprocessing_difference.json")
    atomic_write_json(
        {
            "status": "EXTRACTOR_LOAD_PASS",
            "snapshot_path": str(adapter.snapshot_path),
            "adapter_id": adapter.adapter_id,
            "model_class": adapter.output_definition()["model_class"],
            "processor_class": adapter.output_definition()["processor_class"],
            "load_seconds": load_seconds,
            "claim_allowed": False,
        },
        out / "model_load.json",
    )
    atomic_write_json(contract, out / "preprocessing_contract.json")
    atomic_write_json(asset, out / "asset_manifest.json")

    selected_batch_size = 0
    tested_batch_size = 0
    calibration: list[dict[str, Any]] = []
    final_features: np.ndarray | None = None
    successful_sizes: list[int] = []
    for raw_candidate in extractor.get("preflight_batch_sizes", [1, 2, 4, 8]):
        candidate = int(raw_candidate)
        tested_batch_size = candidate
        fixtures = _fixture_images(candidate)
        torch.cuda.reset_peak_memory_stats(0)
        started = time.monotonic()
        try:
            with torch.inference_mode():
                result = adapter.extract_batch(fixtures)
            features = result.float().cpu().numpy()
            if features.ndim != 2 or features.shape != (candidate, int(extractor["expected_dimension"])):
                raise ValueError(
                    f"feature calibration output mismatch: requested={candidate}, observed={features.shape}"
                )
            if not np.isfinite(features).all():
                raise ValueError("feature calibration output contains nonfinite values")
            selected_batch_size = candidate
            successful_sizes.append(candidate)
            final_features = features
            calibration.append(
                {
                    "tested_batch_size": candidate,
                    "fixture_image_count": len(fixtures),
                    "output_count": int(features.shape[0]),
                    "status": "PASS",
                    "elapsed_seconds": time.monotonic() - started,
                    "peak_vram_bytes": int(torch.cuda.max_memory_allocated(0)),
                    "claim_allowed": False,
                }
            )
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            calibration.append(
                {
                    "tested_batch_size": candidate,
                    "fixture_image_count": len(fixtures),
                    "output_count": 0,
                    "status": "OOM",
                    "elapsed_seconds": time.monotonic() - started,
                    "claim_allowed": False,
                }
            )
            break
    if selected_batch_size == 0 or final_features is None:
        raise RuntimeError("no extractor calibration batch completed")
    fallback_batch_size = successful_sizes[-2] if len(successful_sizes) > 1 else successful_sizes[-1]
    atomic_write_json(
        {
            "status": "FEATURE_SMOKE_PASS",
            "shape": list(final_features.shape),
            "finite": True,
            "feature_definition": adapter.output_definition()["feature_definition"],
            "claim_allowed": False,
        },
        out / "feature_smoke.json",
    )
    atomic_write_json(
        {
            "tested_batch_size": tested_batch_size,
            "selected_batch_size": selected_batch_size,
            "fallback_batch_size": fallback_batch_size,
            "largest_actually_tested_successful_batch_size": selected_batch_size,
            "trials": calibration,
            "claim_allowed": False,
        },
        out / "runtime_calibration.json",
    )
    adapter.unload()
    outputs = {
        name: file_sha256(out / name)
        for name in (
            "asset_manifest.json",
            "model_load.json",
            "preprocessing_contract.json",
            "preprocessing_difference.json",
            "feature_smoke.json",
            "runtime_calibration.json",
        )
    }
    completion = {
        **completion_identity_fields(
            "extractor_preflight",
            config_schema_version=str(config.get("schema_version", "certgen.cvpr.preflight_config.v1")),
            output_schema_version=str(config["output_schema_version"]),
        ),
        "status": "success",
        "status_code": "EXTRACTOR_PREFLIGHT_PASS",
        "configuration_hash": config["configuration_hash"],
        "input_manifest_hash": str(config.get("input_manifest_hash", "preflight_none")),
        "asset_manifest_hash": file_sha256(args.asset_manifest),
        "outputs": outputs,
        "claim_allowed": False,
    }
    atomic_write_json(completion, out / "worker_completion.json")
    atomic_write_json(
        {
            **hardware,
            **completion,
            "extractor_id": args.extractor_id,
            "tested_batch_size": tested_batch_size,
            "selected_batch_size": selected_batch_size,
            "fallback_batch_size": fallback_batch_size,
        },
        out / "status.json",
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
