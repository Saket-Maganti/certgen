"""Prospective cross-family CIFAR adapter and source-verification contract."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from certgen.icml2027.common import stable_hash


class CrossFamilyGenerator(Protocol):
    def load(self, asset_root: Path, device: str) -> Any: ...

    def sample(self, model: Any, seeds: list[int], sampler: dict[str, Any]) -> np.ndarray: ...


@dataclass(frozen=True)
class CrossFamilyContract:
    adapter_api: str = "certgen.icml2027.cross_family.CrossFamilyGenerator"
    expected_resolution: int = 32
    expected_channels: int = 3
    output_dtype: str = "uint8"
    seed_control: str = "one_explicit_seed_per_sample"
    scheduler_sampler_contract: str = "must_be_verified_from_exact_source_revision"
    source_verification: str = "BLOCKED_REQUIRES_REAL_SOURCE_VERIFICATION"
    license_gate: str = "BLOCKED_REQUIRES_REAL_SOURCE_VERIFICATION"
    ddpm_pipeline_compatibility_assumed: bool = False
    claim_allowed: bool = False

    @property
    def contract_hash(self) -> str:
        return stable_hash(self.__dict__)


def validate_generated_batch(images: np.ndarray, seeds: list[int]) -> dict[str, Any]:
    contract = CrossFamilyContract()
    errors: list[str] = []
    if images.shape != (len(seeds), contract.expected_resolution, contract.expected_resolution, contract.expected_channels):
        errors.append(f"unexpected image batch shape: {images.shape}")
    if str(images.dtype) != contract.output_dtype:
        errors.append(f"unexpected image dtype: {images.dtype}")
    if len(seeds) != len(set(seeds)):
        errors.append("seed collision detected")
    return {
        "schema_version": "certgen.icml2027.cross_family_validation.v1",
        "passed": not errors,
        "errors": errors,
        "contract_hash": contract.contract_hash,
        "source_verification": contract.source_verification,
        "claim_allowed": False,
    }

def conformance_smoke(adapter_factory: Callable[[], CrossFamilyGenerator] | None = None) -> dict[str, Any]:
    if adapter_factory is None:
        return {
            "passed": False,
            "status": "BLOCKED_REQUIRES_REAL_SOURCE_VERIFICATION",
            "human_action": "Provide the exact official repository, immutable revision, license text, checkpoint manifest, and documented sampler API; then implement the adapter protocol and run this smoke test on Kaggle.",
            "claim_allowed": False,
        }
    return {
        "passed": False,
        "status": "REAL_ASSET_PREFLIGHT_REQUIRED",
        "human_action": "Run adapter load and two-seed deterministic sampling against the authenticated real asset.",
        "claim_allowed": False,
    }
