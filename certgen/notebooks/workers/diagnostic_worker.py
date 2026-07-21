"""Per-GPU non-evidentiary Kaggle diagnostic worker.

PyTorch is imported only in this subprocess after the parent has pinned one
physical GPU through ``CUDA_VISIBLE_DEVICES``.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from certgen.core.hashing import file_sha256
from certgen.notebooks.worker_contract import completion_identity_fields


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--configuration-hash", required=True)
    parser.add_argument("--input-manifest-hash", required=True)
    parser.add_argument("--warmup", type=int, default=4)
    parser.add_argument("--iterations", type=int, default=16)
    args = parser.parse_args(argv)

    import torch

    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("diagnostic worker must see exactly one pinned CUDA device")
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    before = torch.cuda.mem_get_info(device)
    started_load = time.perf_counter()
    left = torch.randn((512, 512), device=device)
    right = torch.randn((512, 512), device=device)
    model_load_seconds = time.perf_counter() - started_load
    started_warmup = time.perf_counter()
    for _ in range(args.warmup):
        torch.mm(left, right)
    torch.cuda.synchronize(device)
    warmup_seconds = time.perf_counter() - started_warmup
    started = time.perf_counter()
    for _ in range(args.iterations):
        torch.mm(left, right)
    torch.cuda.synchronize(device)
    elapsed = time.perf_counter() - started
    peak = int(torch.cuda.max_memory_allocated(device))
    after = torch.cuda.mem_get_info(device)

    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    report = output / "diagnostic_report.json"
    report_payload = {
        "schema_version": "certgen.kaggle.gpu_diagnostic.v1",
        "physical_gpu_assignment": int(os.environ["CERTGEN_PHYSICAL_GPU"]),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "logical_device": "cuda:0",
        "gpu_name": torch.cuda.get_device_name(device),
        "torch_version": torch.__version__,
        "cuda_runtime": torch.version.cuda,
        "model_load_seconds": model_load_seconds,
        "warmup_seconds": warmup_seconds,
        "iterations": args.iterations,
        "throughput_iterations_per_second": args.iterations / elapsed,
        "vram_free_before_bytes": int(before[0]),
        "vram_total_bytes": int(before[1]),
        "vram_free_after_bytes": int(after[0]),
        "peak_allocated_bytes": peak,
        "safe_batch_size": 1,
        "synthetic_validation_only": True,
        "not_real_kaggle_input": False,
        "not_empirical_evidence": True,
        "claim_allowed": False,
    }
    report.write_text(json.dumps(report_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    completion = {
        **completion_identity_fields(
            "diagnostic",
            config_schema_version="certgen.kaggle.diagnostic_config.v1",
            output_schema_version="certgen.kaggle.diagnostic_output.v1",
        ),
        "status": "success",
        "configuration_hash": args.configuration_hash,
        "input_manifest_hash": args.input_manifest_hash,
        "asset_manifest_hash": "no_assets_required",
        "outputs": {report.name: file_sha256(report)},
        "claim_allowed": False,
    }
    (output / "worker_completion.json").write_text(
        json.dumps(completion, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
