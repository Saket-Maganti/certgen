"""Validation helpers for the corrected prospective CIFAR 10k v2 study."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from certgen.core.io import read_json
from certgen.icml2027.common import file_sha256, load_mapping, stable_hash
from certgen.stats.reference_sampling import (
    validate_reference_draw_plan,
    validate_reference_sampling_contract,
)


def prospective_sample_ids(study_id: str, model_id: str, master_seed: int, count: int) -> list[str]:
    return [
        hashlib.sha256(f"{study_id}|{model_id}|{index:08d}|{master_seed}".encode()).hexdigest()
        for index in range(count)
    ]


def validate_cifar_10k_v2(
    config_path: str | Path = "configs/icml2027/cifar_confirmatory_10k_v2.yaml",
    *,
    root: str | Path = ".",
) -> dict[str, Any]:
    workspace = Path(root)
    config = load_mapping(workspace / config_path)
    errors: list[str] = []
    if config.get("study_id") != "icml2027_cifar_confirmatory_10k_v2":
        errors.append("unexpected v2 study ID")
    if config.get("immutable") is not True or config.get("claim_allowed") is not False:
        errors.append("v2 must be immutable and claim-blocked")
    prefixes = [int(value) for value in config.get("prefixes", [])]
    if prefixes != [100, 250, 500, 1000, 2000, 5000, 10000]:
        errors.append("v2 prefix grid is not frozen as required")
    master_seed = int(config.get("seed_plan", {}).get("master_seed", -1))
    for model_id in config.get("models", []):
        ids = prospective_sample_ids(str(config["study_id"]), str(model_id), master_seed, 10_000)
        declared = config.get("prefix_sample_id_hashes", {}).get(model_id, {})
        for prefix in prefixes:
            if declared.get(prefix) != stable_hash(ids[:prefix]):
                errors.append(f"prefix sample-ID hash mismatch: {model_id}/{prefix}")
    reference = config.get("reference_draw", {})
    contract = validate_reference_sampling_contract(
        reference,
        expected_plan_sha256=str(reference.get("plan_sha256")),
    )
    errors.extend(contract["errors"])
    plan_path = workspace / str(reference.get("plan_path", ""))
    plan_validation: dict[str, Any]
    if not plan_path.is_file():
        errors.append("v2 reference draw plan is missing")
        plan_validation = {"passed": False}
    else:
        plan = read_json(plan_path)
        plan_validation = validate_reference_draw_plan(plan, min_draws=10_000)
        if not plan_validation["passed"]:
            errors.extend(plan_validation["errors"])
        if plan.get("plan_sha256") != reference.get("plan_sha256"):
            errors.append("v2 reference plan identity mismatch")
    return {
        "passed": not errors,
        "errors": errors,
        "study_id": config.get("study_id"),
        "config_sha256": file_sha256(workspace / config_path),
        "reference_plan_sha256": reference.get("plan_sha256"),
        "reference_plan_validation": plan_validation,
        "claim_allowed": False,
    }
