"""Conservative adapter conformance reporting from local-safe checks."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable, Mapping


FIELDS = [
    "adapter",
    "model_or_extractor",
    "asset_resolution",
    "load",
    "smoke",
    "batching",
    "seed_mapping",
    "preprocessing",
    "output_dimension",
    "resume",
    "offline_loading",
    "status",
    "blocker",
]


def validate_conformance_rows(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    identities: set[tuple[str, str]] = set()
    for raw in rows:
        missing = sorted(set(FIELDS) - set(raw))
        if missing:
            raise ValueError("adapter conformance row missing fields: " + ", ".join(missing))
        row = {field: str(raw[field]) for field in FIELDS}
        identity = (row["adapter"], row["model_or_extractor"])
        if identity in identities:
            raise ValueError(f"duplicate adapter conformance identity: {identity}")
        identities.add(identity)
        if row["status"] not in {
            "FIXTURE_CONFORMANCE_PASS_REAL_PREFLIGHT_REQUIRED",
            "REGISTERED_NOT_SELECTED",
            "BLOCKED_UNVALIDATED_ADAPTER",
        }:
            raise ValueError(f"unsupported conformance status: {row['status']}")
        normalized.append(row)
    if not normalized:
        raise ValueError("adapter conformance matrix must not be empty")
    return normalized


def canonical_conformance_rows() -> list[dict[str, str]]:
    yes = "LOCAL_FIXTURE_VERIFIED"
    real = "REAL_PREFLIGHT_REQUIRED"
    return [
        {
            "adapter": "diffusers_unconditional_ddpm",
            "model_or_extractor": "google_ddpm_cifar10_candidate",
            "asset_resolution": yes,
            "load": yes,
            "smoke": yes,
            "batching": yes,
            "seed_mapping": yes,
            "preprocessing": "NOT_APPLICABLE_GENERATOR",
            "output_dimension": "NOT_APPLICABLE_GENERATOR",
            "resume": yes,
            "offline_loading": yes,
            "status": "FIXTURE_CONFORMANCE_PASS_REAL_PREFLIGHT_REQUIRED",
            "blocker": real,
        },
        {
            "adapter": "diffusers_unconditional_ddpm",
            "model_or_extractor": "frank_ddpm_ema_cifar10_candidate",
            "asset_resolution": yes,
            "load": yes,
            "smoke": yes,
            "batching": yes,
            "seed_mapping": yes,
            "preprocessing": "NOT_APPLICABLE_GENERATOR",
            "output_dimension": "NOT_APPLICABLE_GENERATOR",
            "resume": yes,
            "offline_loading": yes,
            "status": "FIXTURE_CONFORMANCE_PASS_REAL_PREFLIGHT_REQUIRED",
            "blocker": real,
        },
        {
            "adapter": "inception_torchvision_local_v1",
            "model_or_extractor": "inception",
            "asset_resolution": yes,
            "load": yes,
            "smoke": yes,
            "batching": yes,
            "seed_mapping": "NOT_APPLICABLE_EXTRACTOR",
            "preprocessing": yes,
            "output_dimension": yes,
            "resume": yes,
            "offline_loading": yes,
            "status": "FIXTURE_CONFORMANCE_PASS_REAL_PREFLIGHT_REQUIRED",
            "blocker": real,
        },
        {
            "adapter": "clip_projected_image_embedding_v1",
            "model_or_extractor": "clip",
            "asset_resolution": yes,
            "load": yes,
            "smoke": yes,
            "batching": yes,
            "seed_mapping": "NOT_APPLICABLE_EXTRACTOR",
            "preprocessing": yes,
            "output_dimension": yes,
            "resume": yes,
            "offline_loading": yes,
            "status": "FIXTURE_CONFORMANCE_PASS_REAL_PREFLIGHT_REQUIRED",
            "blocker": real,
        },
        {
            "adapter": "dinov2_optional_cls_v1",
            "model_or_extractor": "dinov2",
            "asset_resolution": "UNRESOLVED",
            "load": "NOT_VERIFIED",
            "smoke": "NOT_VERIFIED",
            "batching": "NOT_VERIFIED",
            "seed_mapping": "NOT_APPLICABLE_EXTRACTOR",
            "preprocessing": "UNRESOLVED",
            "output_dimension": "UNRESOLVED",
            "resume": "CONTRACT_IMPLEMENTED_NOT_SELECTED",
            "offline_loading": "NOT_VERIFIED",
            "status": "REGISTERED_NOT_SELECTED",
            "blocker": "exact DINO implementation, revision, preprocessing, dimension, license, and real preflight required",
        },
        {
            "adapter": "cfm_unvalidated",
            "model_or_extractor": "frank_cfm_cifar10_candidate",
            "asset_resolution": "UNRESOLVED",
            "load": "BLOCKED",
            "smoke": "BLOCKED",
            "batching": "BLOCKED",
            "seed_mapping": "BLOCKED",
            "preprocessing": "NOT_APPLICABLE_GENERATOR",
            "output_dimension": "NOT_APPLICABLE_GENERATOR",
            "resume": "BLOCKED",
            "offline_loading": "BLOCKED",
            "status": "BLOCKED_UNVALIDATED_ADAPTER",
            "blocker": "CFM loading, batching, sampler, and seed semantics are not validated",
        },
    ]


def write_adapter_conformance_matrix(path: str | Path) -> dict[str, Any]:
    rows = validate_conformance_rows(canonical_conformance_rows())
    target = Path(path)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite adapter conformance matrix: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return {
        "status": "ADAPTER_CONFORMANCE_MATRIX_WRITTEN",
        "path": str(target),
        "rows": len(rows),
        "claim_allowed": False,
    }
