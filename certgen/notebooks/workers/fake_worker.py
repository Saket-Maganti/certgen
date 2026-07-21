"""CPU-only worker used to verify the real subprocess orchestration path."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from certgen.core.hashing import file_sha256
from certgen.notebooks.worker_contract import completion_identity_fields


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--fail", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.0)
    args = parser.parse_args(argv)
    time.sleep(args.sleep)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    artifact = output.with_name(output.stem + "_artifact.json")
    artifact.write_text(json.dumps({"worker": output.stem}, sort_keys=True) + "\n", encoding="utf-8")
    payload = {
        **completion_identity_fields(
            "fixture",
            config_schema_version="certgen.fixture.config.v1",
            output_schema_version="certgen.fixture.output.v1",
        ),
        "status": "success",
        "physical_gpu_assignment": os.environ.get("CERTGEN_PHYSICAL_GPU"),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "shard_id": os.environ.get("CERTGEN_SHARD_ID"),
        "worker_pid": os.getpid(),
        "visible_gpu_count": "fixture_not_probed",
        "logical_device": "fixture_cpu",
        "gpu_name": "fixture_no_gpu",
        "cuda_version": "fixture_no_cuda",
        "pytorch_version": "fixture_not_imported",
        "configuration_hash": "fixture",
        "input_manifest_hash": "fixture",
        "asset_manifest_hash": "fixture",
        "outputs": {artifact.name: file_sha256(artifact)},
        "claim_allowed": False,
    }
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 7 if args.fail else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
