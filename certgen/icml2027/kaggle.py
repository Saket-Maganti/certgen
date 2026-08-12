"""Deterministic ICML 2027 Kaggle input and blocked-plan builder."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from certgen.icml2027.common import file_sha256, stable_hash, write_json
from certgen.icml2027.notebooks import NOTEBOOKS


LANES: dict[str, dict[str, Any]] = {
    "dinov2_preflight": {
        "notebook": "dinov2_preflight",
        "required_inputs": ["dinov2_asset_manifest", "dinov2_asset_root", "worker_spec"],
        "config": "registry/icml2027/model_registry.yaml",
    },
    "dinov2_features": {
        "notebook": "dinov2_features",
        "required_inputs": ["dinov2_preflight_output", "image_manifest", "dinov2_asset_manifest", "dinov2_asset_root", "worker_spec"],
        "config": "registry/icml2027/feature_space_registry.yaml",
    },
    "cifar_cross_family_preflight": {
        "notebook": "cifar_cross_family_preflight",
        "required_inputs": ["source_verification", "model_asset_manifest", "model_asset_root", "worker_spec"],
        "config": "configs/icml2027/cifar_cross_family/contract.yaml",
    },
    "cifar_10k_generation": {
        "notebook": "cifar_10k_generation",
        "required_inputs": ["legacy_preflight_output", "model_asset_manifest", "model_asset_root", "worker_spec"],
        "config": "configs/icml2027/cifar_confirmatory_10k_v2.yaml",
    },
    "cifar_10k_features": {
        "notebook": "cifar_10k_features",
        "required_inputs": ["generation_10k_output", "reference_manifest", "worker_spec"],
        "config": "configs/icml2027/cifar_confirmatory_10k_v2.yaml",
    },
    "released_sample_features": {
        "notebook": "released_sample_features",
        "required_inputs": ["released_sample_import", "released_sample_manifest", "worker_spec"],
        "config": "registry/icml2027/feature_space_registry.yaml",
    },
    "ffhq": {
        "notebook": "ffhq",
        "required_inputs": ["go_no_go_report", "reference_manifest", "model_or_released_samples"],
        "config": "configs/icml2027/benchmarks/ffhq/prospective_contract.yaml",
    },
    "imagenet": {
        "notebook": "imagenet",
        "required_inputs": ["go_no_go_report", "reference_manifest", "model_or_released_samples"],
        "config": "configs/icml2027/benchmarks/imagenet/prospective_contract.yaml",
    },
    "text_to_image": {
        "notebook": "text_to_image",
        "required_inputs": ["go_no_go_report", "prompt_manifest", "model_or_released_samples"],
        "config": "configs/icml2027/benchmarks/text_to_image/prospective_contract.yaml",
    },
}


def _members(path: Path, archive_name: str) -> list[tuple[str, bytes]]:
    if path.is_file():
        return [(archive_name, path.read_bytes())]
    if path.is_dir():
        return [
            (f"{archive_name}/{item.relative_to(path).as_posix()}", item.read_bytes())
            for item in sorted(path.rglob("*"))
            if item.is_file()
            and not item.is_symlink()
            and "__pycache__" not in item.parts
            and item.suffix != ".pyc"
            and not item.name.startswith(".")
        ]
    raise FileNotFoundError(path)


def _write_zip(path: Path, members: list[tuple[str, bytes]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(members):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(info, data)
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def compute_prerequisite_identity(lane: str, inputs: dict[str, str | Path]) -> str:
    """Hash authenticated prerequisite members, excluding the worker spec that binds this hash."""

    if lane not in LANES:
        raise ValueError(f"unknown ICML Kaggle lane: {lane}")
    required = [name for name in LANES[lane]["required_inputs"] if name != "worker_spec"]
    missing = [name for name in required if name not in inputs or not Path(inputs[name]).exists()]
    if missing:
        raise ValueError(f"missing prerequisites for identity calculation: {missing}")
    input_hashes: dict[str, Any] = {}
    for name in required:
        path = Path(inputs[name]).resolve()
        resolved = _members(path, f"inputs/{name}")
        input_hashes[name] = {
            "path_type": "directory" if path.is_dir() else "file",
            "members": [
                {"path": member, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                for member, data in resolved
            ],
        }
    return stable_hash(input_hashes)


def build_input(
    lane: str,
    inputs: dict[str, str | Path],
    *,
    root: str | Path = ".",
    out_root: str | Path = "artifacts/icml2027/kaggle_inputs",
) -> dict[str, Any]:
    if lane not in LANES:
        raise ValueError(f"unknown ICML Kaggle lane: {lane}")
    workspace = Path(root).resolve()
    output = Path(out_root) / lane
    spec = LANES[lane]
    missing = [name for name in spec["required_inputs"] if name not in inputs or not Path(inputs[name]).exists()]
    notebook_spec = NOTEBOOKS[spec["notebook"]]
    notebook = workspace / "notebooks/kaggle/icml2027" / notebook_spec["filename"]
    config = workspace / spec["config"]
    if not notebook.is_file():
        missing.append("source_controlled_notebook")
    if not config.is_file():
        missing.append("frozen_config")
    if missing:
        payload = {
            "schema_version": "certgen.icml2027.kaggle_blocked_plan.v1",
            "lane": lane,
            "status": "BLOCKED_MISSING_AUTHENTICATED_PREREQUISITES",
            "missing": sorted(set(missing)),
            "required_inputs": spec["required_inputs"],
            "notebook": notebook.relative_to(workspace).as_posix() if notebook.is_file() else str(notebook),
            "config": spec["config"],
            "input_zip_created": False,
            "human_action": "satisfy every named prerequisite with authenticated, hash-bound artifacts and rerun the exact builder",
            "planning_only": True,
            "claim_allowed": False,
        }
        write_json(output / "BLOCKED_PLAN.json", payload)
        return payload
    members: list[tuple[str, bytes]] = []
    members.extend(_members(notebook, f"notebook/{notebook.name}"))
    members.extend(_members(config, f"config/{config.name}"))
    dependency_profiles = workspace / "registry/icml2027/dependency_profiles.json"
    if lane in {
        "dinov2_preflight",
        "dinov2_features",
        "cifar_10k_generation",
        "cifar_10k_features",
        "released_sample_features",
    }:
        members.extend(_members(dependency_profiles, "contract/dependency_profiles.json"))
    if lane in {"cifar_10k_generation", "cifar_10k_features"}:
        execution_contract = workspace / "registry/icml2027/cifar_10k_v2_execution_contract_v1.json"
        seed_manifest = workspace / "registry/manifests/icml2027/cifar10k_generator_seed_manifest_v1.json"
        members.extend(_members(execution_contract, "contract/execution_contract.json"))
        members.extend(_members(seed_manifest, "contract/generator_seed_manifest.json"))
    code_paths = [workspace / "certgen"]
    for code in code_paths:
        members.extend(_members(code, f"source/{code.relative_to(workspace).as_posix()}"))
    input_hashes: dict[str, Any] = {}
    for name in spec["required_inputs"]:
        path = Path(inputs[name]).resolve()
        archive_name = f"inputs/{name}"
        resolved = _members(path, archive_name)
        members.extend(resolved)
        input_hashes[name] = {
            "path_type": "directory" if path.is_dir() else "file",
            "members": [{"path": member, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)} for member, data in resolved],
        }
    prerequisite_identity = stable_hash(
        {key: value for key, value in input_hashes.items() if key != "worker_spec"}
    )
    if "worker_spec" in inputs:
        from certgen.icml2027.execution_contract import (
            validate_feature_job_partition,
            validate_generation_job_partition,
            validate_worker_spec,
        )

        worker_payload = json.loads(Path(inputs["worker_spec"]).read_text(encoding="utf-8"))
        contract_payload = (
            json.loads(
                (workspace / "registry/icml2027/cifar_10k_v2_execution_contract_v1.json").read_text(
                    encoding="utf-8"
                )
            )
            if lane in {"cifar_10k_generation", "cifar_10k_features"}
            else None
        )
        worker_validation = validate_worker_spec(worker_payload, expected_lane=lane, contract=contract_payload)
        if worker_payload.get("input_package_sha256") != prerequisite_identity:
            worker_validation["passed"] = False
            worker_validation["errors"].append("input_package_sha256 does not bind the authenticated prerequisite set")
        if not worker_validation["passed"]:
            raise ValueError(f"worker scientific identity rejected: {worker_validation['errors']}")
        jobs = worker_payload.get("jobs", [])
        if lane == "cifar_10k_generation":
            seed_payload = json.loads(
                (workspace / "registry/manifests/icml2027/cifar10k_generator_seed_manifest_v1.json").read_text(
                    encoding="utf-8"
                )
            )
            partition = validate_generation_job_partition(jobs, seed_payload)
        elif lane == "cifar_10k_features":
            partition = validate_feature_job_partition(
                jobs,
                required_extractors=list(worker_payload["extractor_revisions"]),
                required_roles=list(worker_payload["expected_source_roles"]),
                expected_shards=int(worker_payload["expected_shard_count"]),
                source_sample_order_sha256=str(worker_payload["source_sample_order_sha256"]),
            )
        else:
            partition = {"passed": True, "errors": []}
        if not partition["passed"]:
            raise ValueError(f"aggregate worker partition rejected: {partition['errors']}")
    inventory = [{"path": name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)} for name, data in sorted(members)]
    source_inventory = [row for row in inventory if str(row["path"]).startswith("source/")]
    manifest = {
        "schema_version": "certgen.icml2027.kaggle_input.v1",
        "lane": lane,
        "package_type": "ICML2027_AUTHENTICATED_STAGE_INPUT",
        "configuration_sha256": file_sha256(config),
        "input_hashes": input_hashes,
        "authenticated_prerequisite_set_sha256": prerequisite_identity,
        "inventory": inventory,
        "inventory_hash": stable_hash(inventory),
        "source_tree_sha256": stable_hash(source_inventory),
        "dependency_profiles_sha256": file_sha256(dependency_profiles)
        if dependency_profiles.is_file()
        else None,
        "requested_gpu_count": 2,
        "one_gpu_fallback": False,
        "claim_allowed": False,
    }
    members.append(("package_manifest.json", json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"))
    zip_path = output / f"certgen_icml2027_{lane}_input.zip"
    _write_zip(zip_path, members)
    payload = {
        **manifest,
        "status": "READY",
        "input_zip": str(zip_path),
        "input_zip_sha256": file_sha256(zip_path),
        "input_zip_created": True,
    }
    write_json(zip_path.with_suffix(".zip.manifest.json"), payload)
    return payload
