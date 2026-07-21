"""Helpers deliberately free of top-level PyTorch imports."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import stable_hash_json


def require_gpu_pin() -> tuple[str, str]:
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    physical = os.environ.get("CERTGEN_PHYSICAL_GPU")
    if visible is None or physical is None or visible != physical:
        raise RuntimeError("worker GPU pin is absent or inconsistent before PyTorch import")
    if "," in visible:
        raise RuntimeError("each worker must see exactly one physical GPU")
    return physical, visible


def load_configuration(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("worker configuration must be a mapping")
    declared = payload.get("configuration_hash")
    observed = stable_hash_json({key: value for key, value in payload.items() if key != "configuration_hash"})
    if declared != observed:
        raise ValueError("worker configuration hash mismatch")
    if payload.get("claim_allowed") is not False:
        raise ValueError("worker configuration must set claim_allowed=false")
    return payload


def hardware_record(configuration_hash: str, shard_id: str) -> tuple[Any, dict[str, Any]]:
    physical, visible = require_gpu_pin()
    import torch

    if torch.cuda.device_count() != 1:
        raise RuntimeError("isolated worker must observe exactly one logical CUDA device")
    record = {
        "physical_gpu_assignment": int(physical),
        "cuda_visible_devices": visible,
        "visible_gpu_count": torch.cuda.device_count(),
        "logical_device": "cuda:0",
        "gpu_name": torch.cuda.get_device_name(0),
        "cuda_version": torch.version.cuda,
        "pytorch_version": torch.__version__,
        "worker_pid": os.getpid(),
        "configuration_hash": configuration_hash,
        "shard_id": shard_id,
        "evidence_class": "run_log_only",
        "claim_allowed": False,
    }
    return torch, record
