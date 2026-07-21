"""Deterministic, restricted-asset-free Phase 1 Kaggle input bundles."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.cvpr.output_schemas import expected_output_schema
from certgen.phase1.notebooks import PHASE1_NOTEBOOKS
from certgen.phase1.state import phase1_state


INPUT_ROOT = Path("artifacts/cvpr/kaggle_inputs")
BUNDLES = {
    "diagnostic": INPUT_ROOT / "diagnostic/certgen_kaggle_environment_diagnostic_input.zip",
    "preflight": INPUT_ROOT / "preflight/certgen_cvpr_preflight_input.zip",
}
RESTRICTED_SUFFIXES = {".pt", ".pth", ".bin", ".safetensors", ".ckpt", ".onnx"}


def _yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping: {path}")
    return payload


def _source_files(root: Path) -> list[Path]:
    excluded_tokens = {
        "builder_faithful.py",
        "synthetic_runtime.py",
        "fake_worker.py",
        "fake_generation_worker.py",
    }
    return sorted(
        path
        for path in (root / "certgen").rglob("*.py")
        if path.is_file() and path.name not in excluded_tokens and "__pycache__" not in path.parts
    )


def source_code_hash(root: str | Path = ".") -> str:
    base = Path(root).resolve()
    digest = hashlib.sha256()
    for path in _source_files(base):
        relative = path.relative_to(base).as_posix().encode()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        data = path.read_bytes()
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def _config(root: Path, stage: str) -> dict[str, Any]:
    code_hash = source_code_hash(root)
    if stage == "diagnostic":
        payload: dict[str, Any] = {
            "schema_version": "certgen.kaggle.diagnostic_config.v1",
            "kind": "diagnostic",
            "run_id": f"certgen__environment-diagnostic__t4x2__{code_hash[:12]}",
            "mode": "resume",
            "dependency_mode": "KAGGLE_INTERNET_ON_INSTALL",
            "network_mode": "ONLINE_DEPENDENCIES_OFFLINE_ASSETS",
            "dependency_network_allowed": True,
            "model_asset_network_allowed": False,
            "asset_policy": "OFFLINE_PACKAGED_CACHE",
            "requested_gpu_count": 2,
            "allow_single_gpu_fallback": False,
            "input_manifest_hash": code_hash,
            "source_code_hash": code_hash,
            "output_schema_version": "certgen.kaggle.diagnostic_output.v1",
            "claim_allowed": False,
        }
    elif stage == "preflight":
        profile = _yaml(root / "configs/cvpr/profiles/cifar_integrity_minimal.yaml")
        models_registry = _yaml(root / "registry/cvpr/model_registry.yaml")["models"]
        features_registry = _yaml(root / "registry/cvpr/feature_space_registry.yaml")["feature_spaces"]
        assets_registry = _yaml(root / "registry/cvpr/kaggle_asset_registry.yaml")["assets"]
        selected_models = [row for model_id in profile["models"] for row in models_registry if row.get("model_id") == model_id]
        selected_extractors = [row for extractor_id in profile["extractors"] for row in features_registry if row.get("feature_space_id") == extractor_id]
        model_rows = []
        for row in selected_models:
            model_rows.append(
                {
                    **row,
                    "preflight_runtime_config": {
                        "batch_size": 2,
                        "minimum_batch_size": 1,
                        "seeds": [1000, 1001],
                        "num_inference_steps": 2,
                        "scheduler": "checkpoint_default_pinned",
                        "guidance_scale": None,
                        "width": 32,
                        "height": 32,
                        "prompts": [],
                        "class_ids": [],
                        "precision": "float16",
                        "output_type": "pil",
                    },
                }
            )
        assets: list[dict[str, Any]] = []
        selected_ids = set(profile["models"]) | set(profile["extractors"])
        for row in assets_registry:
            identity = str(row["asset_id"]).removesuffix("__asset")
            if identity not in selected_ids:
                continue
            assets.append(
                {
                    "asset_kind": "model" if identity in profile["models"] else "extractor",
                    "asset_id": row["asset_id"],
                    "model_or_extractor_id": identity,
                    "revision": row["revision"],
                    "source": str(row["repository_or_mount"]).split(" or ")[0],
                    "license": row["license_status"],
                    "authentication_required": False,
                    "policy": "OFFLINE_PACKAGED_CACHE",
                    "expected_files": row["expected_files"],
                    "mount_subdir": identity if identity != "clip" else "clip-vit-large-patch14",
                    "redistribution_allowed": False,
                    "public_archive_included": False,
                    "private_mount_required": True,
                }
            )
        profile_hash = stable_hash_json(profile)
        payload = {
            "schema_version": "certgen.cvpr.preflight_config.v1",
            "kind": "preflight",
            "run_id": f"cifar10__checkpoint-preflight__tiny__{profile_hash[:12]}",
            "mode": "resume",
            "dependency_mode": "KAGGLE_INTERNET_ON_INSTALL",
            "network_mode": "ONLINE_DEPENDENCIES_OFFLINE_ASSETS",
            "dependency_network_allowed": True,
            "model_asset_network_allowed": False,
            "asset_policy": "OFFLINE_PACKAGED_CACHE",
            "private_asset_mount": "/kaggle/input/certgen-private-assets",
            "requested_gpu_count": 2,
            "allow_single_gpu_fallback": False,
            "input_manifest_hash": stable_hash_json({"profile": profile_hash, "assets": assets, "code": code_hash}),
            "source_code_hash": code_hash,
            "profile_hash": profile_hash,
            "tiny_images_per_model": 2,
            "pilot_profile": profile,
            "selected_models": list(profile["models"]),
            "selected_extractors": list(profile["extractors"]),
            "models": model_rows,
            "extractors": selected_extractors,
            "assets": assets,
            "output_schema_version": expected_output_schema("preflight")["schema_version"],
            "evidence_class": "non_evidence_preflight",
            "claim_allowed": False,
        }
    else:
        raise ValueError(f"static Phase 1 bundle is unsupported for stage: {stage}")
    payload["configuration_hash"] = stable_hash_json(payload)
    return payload


def _zip_bytes(files: Mapping[str, bytes]) -> bytes:
    import io

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return output.getvalue()


def _member_payloads(root: Path, stage: str, config: Mapping[str, Any]) -> dict[str, bytes]:
    lock = "kaggle-base.lock" if stage == "diagnostic" else "kaggle-preflight.lock"
    schema = {
        "schema_version": config["output_schema_version"],
        "stage": stage,
        "required_status_file": "diagnostic_status.json" if stage == "diagnostic" else "checkpoint_preflight_status.json",
        "required_gpu_count": 2,
        "claim_allowed": False,
    }
    instructions = f"""# CertGen {stage} Kaggle input

Select GPU T4 x2. Validate locally with:

`python3 -m certgen kaggle validate-input {BUNDLES[stage]}`

Upload this ZIP without unpacking. Run `{PHASE1_NOTEBOOKS[stage]}`. Download the final output ZIP and place it under `data/kaggle_returns/{stage}/`, then run:

`CUDA_VISIBLE_DEVICES=\"\" CERTGEN_CPU_ONLY=1 python3 scripts/run_all_available_cpu_stages.py --resume --explain`

This package contains no credentials or model weights. `claim_allowed=false`.
"""
    files: dict[str, bytes] = {
        "configuration.yaml": yaml.safe_dump(dict(config), sort_keys=False).encode(),
        f"{stage}_config.yaml": yaml.safe_dump(dict(config), sort_keys=False).encode(),
        "notebook.ipynb": (root / PHASE1_NOTEBOOKS[stage]).read_bytes(),
        "requirements/stage.lock": (root / "requirements" / lock).read_bytes(),
        "requirements/kaggle-constraints.txt": (root / "requirements/kaggle-constraints.txt").read_bytes(),
        "asset_registry.yaml": (root / "registry/cvpr/kaggle_asset_registry.yaml").read_bytes(),
        "KAGGLE_ASSET_SETUP.md": (root / "KAGGLE_ASSET_SETUP.md").read_bytes(),
        "expected_output_schema.json": (json.dumps(schema, indent=2, sort_keys=True) + "\n").encode(),
        "WORKER_CONTRACT.md": b"One active subprocess worker per physical GPU; multiprocessing spawn; hash-safe completion markers; atomic shards; claim_allowed=false.\n",
        "VALIDATION_AND_HANDOFF.md": instructions.encode(),
        "README.md": f"CertGen Phase 1 {stage} static input. not_empirical_evidence; claim_allowed=false.\n".encode(),
    }
    for path in _source_files(root):
        files[path.relative_to(root).as_posix()] = path.read_bytes()
    return files


def build_static_input(
    stage: str,
    *,
    root: str | Path = ".",
    dry_run: bool = False,
) -> dict[str, Any]:
    if stage not in BUNDLES:
        return write_blocked_plan(stage, root=root, dry_run=dry_run)
    base = Path(root).resolve()
    config = _config(base, stage)
    files = _member_payloads(base, stage, config)
    members = [
        {"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for name, data in sorted(files.items())
    ]
    bundle_manifest = {
        "schema_version": "certgen.phase1.kaggle_input_bundle.v1",
        "package_type": f"certgen_{stage}_input",
        "stage": stage,
        "source_code_hash": config["source_code_hash"],
        "configuration_hash": config["configuration_hash"],
        "profile_hash": config.get("profile_hash"),
        "dependency_lock": "requirements/stage.lock",
        "worker_contract": "WORKER_CONTRACT.md",
        "expected_output_schema": "expected_output_schema.json",
        "members": members,
        "contains_credentials": False,
        "contains_restricted_weights": False,
        "contains_fixture_payload": False,
        "not_empirical_evidence": True,
        "claim_allowed": False,
    }
    manifest_bytes = (json.dumps(bundle_manifest, indent=2, sort_keys=True) + "\n").encode()
    files["bundle_manifest.json"] = manifest_bytes
    integrity_members = [
        *members,
        {
            "path": "bundle_manifest.json",
            "size": len(manifest_bytes),
            "sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        },
    ]
    files["package_integrity_manifest.json"] = (
        json.dumps({"files": integrity_members, "configuration_hash": config["configuration_hash"], "claim_allowed": False}, indent=2, sort_keys=True) + "\n"
    ).encode()
    archive_bytes = _zip_bytes(files)
    relative = BUNDLES[stage]
    output = base / relative
    result = {
        "schema_version": "certgen.phase1.kaggle_build.v1",
        "status": "DRY_RUN_INPUT_READY" if dry_run else "INPUT_PACKAGE_READY",
        "stage": stage,
        "zip_path": str(relative),
        "zip_sha256": hashlib.sha256(archive_bytes).hexdigest(),
        "zip_size": len(archive_bytes),
        "configuration_hash": config["configuration_hash"],
        "source_code_hash": config["source_code_hash"],
        "notebook": PHASE1_NOTEBOOKS[stage],
        "claim_allowed": False,
    }
    if dry_run:
        return result
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_file():
        if output.read_bytes() != archive_bytes:
            raise FileExistsError(f"refusing to overwrite different immutable Kaggle input: {output}")
        result["status"] = "INPUT_PACKAGE_REUSED"
    else:
        temporary = output.with_name(f".{output.name}.partial")
        temporary.write_bytes(archive_bytes)
        os.replace(temporary, output)
    external = output.with_suffix(output.suffix + ".manifest.json")
    external_payload = {**bundle_manifest, "zip_path": str(relative), "zip_sha256": file_sha256(output), "zip_size": output.stat().st_size}
    serialized_external = json.dumps(external_payload, indent=2, sort_keys=True) + "\n"
    if external.exists() and external.read_text(encoding="utf-8") != serialized_external:
        raise FileExistsError(f"refusing to overwrite different external manifest: {external}")
    external.write_text(serialized_external, encoding="utf-8")
    sha_path = output.with_suffix(output.suffix + ".sha256")
    sha_text = f"{file_sha256(output)}  {output.name}\n"
    if sha_path.exists() and sha_path.read_text(encoding="utf-8") != sha_text:
        raise FileExistsError(f"refusing to overwrite different SHA-256 sidecar: {sha_path}")
    sha_path.write_text(sha_text, encoding="utf-8")
    return result


def write_blocked_plan(stage: str, *, root: str | Path = ".", dry_run: bool = False) -> dict[str, Any]:
    if stage not in {"generation", "features"}:
        raise ValueError(f"unsupported Kaggle input stage: {stage}")
    base = Path(root).resolve()
    state = phase1_state(base)
    directory = base / INPUT_ROOT / stage
    required = {
        "generation": [
            "validated and materialized CIFAR-10 reference",
            "frozen cifar_integrity_minimal study and 1k reference draw",
            "imported real Kaggle preflight PASS with validated private asset manifests",
        ],
        "features": [
            "validated and materialized CIFAR-10 reference and reference draw",
            "imported real 1k dual-GPU generation output",
            "validated Inception and private CLIP asset manifests",
        ],
    }[stage]
    plan = {
        "schema_version": "certgen.phase1.blocked_kaggle_build_plan.v1",
        "stage": stage,
        "scale": "1k",
        "status": "BLOCKED_REAL_STAGE_INPUTS_REQUIRED",
        "required_inputs": required,
        "current_boundary": state["boundary"],
        "builder": f"python3 -m certgen kaggle build-input --stage {stage} --scale 1k --study artifacts/cvpr/study/cifar_integrity_minimal.yaml",
        "fake_zip_created": False,
        "claim_allowed": False,
    }
    expected = {
        "stage": stage,
        "package_type": f"certgen_{stage}_1k_input",
        "required_members": ["configuration.yaml", "bundle_manifest.json", "package_integrity_manifest.json", "notebook.ipynb", "requirements/stage.lock", "expected_output_schema.json", "WORKER_CONTRACT.md", "VALIDATION_AND_HANDOFF.md"],
        "restricted_weights_allowed": False,
        "fixture_payload_allowed": False,
        "claim_allowed": False,
    }
    if not dry_run:
        directory.mkdir(parents=True, exist_ok=True)
        documents = {
            "BUILD_PLAN.json": json.dumps(plan, indent=2, sort_keys=True) + "\n",
            "EXPECTED_CONTENTS.json": json.dumps(expected, indent=2, sort_keys=True) + "\n",
            "README_BLOCKED.md": f"# {stage.title()} input blocked\n\nNo real ZIP is created until every entry in `BUILD_PLAN.json` is validated. Fixtures are forbidden here. `claim_allowed=false`.\n",
        }
        for name, text in documents.items():
            path = directory / name
            if path.exists() and path.read_text(encoding="utf-8") == text:
                continue
            temporary = path.with_name(f".{path.name}.partial")
            temporary.write_text(text, encoding="utf-8")
            os.replace(temporary, path)
    return plan


def validate_input(path: str | Path) -> dict[str, Any]:
    archive_path = Path(path)
    errors: list[str] = []
    manifest: dict[str, Any] = {}
    try:
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if archive.testzip() is not None:
                errors.append("ZIP CRC validation failed")
            if len(names) != len({name.casefold() for name in names}):
                errors.append("duplicate or case-colliding ZIP member")
            for info in infos:
                member = PurePosixPath(info.filename)
                mode = (info.external_attr >> 16) & 0o170000
                if member.is_absolute() or ".." in member.parts or "\\" in info.filename or mode == stat.S_IFLNK:
                    errors.append(f"unsafe ZIP member: {info.filename}")
                if member.suffix.lower() in RESTRICTED_SUFFIXES:
                    errors.append(f"restricted weight member: {info.filename}")
                if info.filename.casefold().endswith((".zip", ".tar", ".tgz", ".tar.gz")):
                    errors.append(f"nested archive member: {info.filename}")
            required = {"configuration.yaml", "bundle_manifest.json", "package_integrity_manifest.json", "notebook.ipynb", "requirements/stage.lock", "expected_output_schema.json", "WORKER_CONTRACT.md", "VALIDATION_AND_HANDOFF.md"}
            errors.extend(f"missing required member: {name}" for name in sorted(required - set(names)))
            if "bundle_manifest.json" in names:
                manifest = json.loads(archive.read("bundle_manifest.json"))
                declared = {row["path"]: row for row in manifest.get("members", [])}
                actual = set(names) - {"bundle_manifest.json", "package_integrity_manifest.json"}
                if set(declared) != actual:
                    errors.append("bundle manifest membership mismatch")
                for name, row in declared.items():
                    data = archive.read(name)
                    if len(data) != row.get("size") or hashlib.sha256(data).hexdigest() != row.get("sha256"):
                        errors.append(f"bundle member hash mismatch: {name}")
                if manifest.get("contains_credentials") is not False or manifest.get("contains_restricted_weights") is not False or manifest.get("contains_fixture_payload") is not False or manifest.get("claim_allowed") is not False:
                    errors.append("bundle safety labels are missing or unsafe")
            if "configuration.yaml" in names:
                config = yaml.safe_load(archive.read("configuration.yaml"))
                observed = stable_hash_json({key: value for key, value in config.items() if key != "configuration_hash"})
                if config.get("configuration_hash") != observed:
                    errors.append("configuration hash mismatch")
                if config.get("requested_gpu_count") != 2 or config.get("allow_single_gpu_fallback") is not False:
                    errors.append("bundle is not fail-closed for T4x2")
                if config.get("claim_allowed") is not False:
                    errors.append("configuration claim_allowed must be false")
    except (OSError, zipfile.BadZipFile, KeyError, TypeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        errors.append(f"input ZIP unreadable: {exc}")
    return {
        "schema_version": "certgen.phase1.kaggle_input_validation.v1",
        "path": str(archive_path),
        "passed": not errors,
        "errors": errors,
        "stage": manifest.get("stage"),
        "zip_sha256": file_sha256(archive_path) if archive_path.is_file() else None,
        "claim_allowed": False,
    }


def inspect_input(path: str | Path) -> dict[str, Any]:
    validation = validate_input(path)
    if not validation["passed"]:
        return validation
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("bundle_manifest.json"))
        config = yaml.safe_load(archive.read("configuration.yaml"))
    return {
        **validation,
        "package_type": manifest["package_type"],
        "configuration_hash": config["configuration_hash"],
        "profile_hash": config.get("profile_hash"),
        "source_code_hash": manifest["source_code_hash"],
        "members": len(manifest["members"]) + 2,
        "notebook": PHASE1_NOTEBOOKS[manifest["stage"]],
    }


def inventory(root: str | Path = ".") -> dict[str, Any]:
    base = Path(root).resolve()
    rows: list[dict[str, Any]] = []
    for stage, relative in BUNDLES.items():
        path = base / relative
        verdict = validate_input(path) if path.is_file() else {"passed": False, "errors": ["missing"]}
        rows.append({"stage": stage, "path": str(relative), "exists": path.is_file(), "sha256": file_sha256(path) if path.is_file() else None, "valid": verdict["passed"], "errors": verdict["errors"]})
    for stage in ("generation", "features"):
        directory = base / INPUT_ROOT / stage
        rows.append({"stage": stage, "path": str((INPUT_ROOT / stage).as_posix()), "exists": False, "blocked_plan": all((directory / name).is_file() for name in ("BUILD_PLAN.json", "EXPECTED_CONTENTS.json", "README_BLOCKED.md")), "valid": None})
    return {"schema_version": "certgen.phase1.kaggle_inventory.v1", "bundles": rows, "claim_allowed": False}


def validate_diagnostic_output(path: str | Path) -> dict[str, Any]:
    archive_path = Path(path)
    errors: list[str] = []
    status: dict[str, Any] = {}
    try:
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if archive.testzip() is not None:
                errors.append("diagnostic output ZIP CRC failure")
            if len(names) != len({name.casefold() for name in names}):
                errors.append("diagnostic output contains duplicate paths")
            for info in infos:
                member = PurePosixPath(info.filename)
                mode = (info.external_attr >> 16) & 0o170000
                if member.is_absolute() or ".." in member.parts or "\\" in info.filename or mode == stat.S_IFLNK:
                    errors.append(f"unsafe diagnostic output member: {info.filename}")
            status_names = [name for name in names if PurePosixPath(name).name == "diagnostic_status.json"]
            integrity_names = [name for name in names if PurePosixPath(name).name == "integrity_manifest.json"]
            if len(status_names) != 1:
                errors.append("diagnostic output must contain exactly one diagnostic_status.json")
            else:
                status = json.loads(archive.read(status_names[0]))
                if status.get("status_code") != "KAGGLE_DIAGNOSTIC_PASS" or status.get("gpu_count") != 2:
                    errors.append("diagnostic status does not prove the required two-GPU pass")
                if status.get("claim_allowed") is not False or status.get("not_empirical_evidence") is not True:
                    errors.append("diagnostic evidence labels are unsafe")
            if len(integrity_names) != 1:
                errors.append("diagnostic output must contain exactly one integrity_manifest.json")
            else:
                integrity = json.loads(archive.read(integrity_names[0]))
                prefix = str(PurePosixPath(integrity_names[0]).parent)
                prefix = "" if prefix == "." else prefix + "/"
                for row in integrity.get("files", []):
                    name = prefix + str(row.get("path", ""))
                    if name not in names:
                        errors.append(f"diagnostic integrity member missing: {name}")
                        continue
                    data = archive.read(name)
                    if len(data) != row.get("size") or hashlib.sha256(data).hexdigest() != row.get("sha256"):
                        errors.append(f"diagnostic integrity mismatch: {name}")
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError, KeyError, TypeError) as exc:
        errors.append(f"diagnostic output unreadable: {exc}")
    return {
        "schema_version": "certgen.phase1.diagnostic_output_validation.v1",
        "passed": not errors,
        "errors": errors,
        "path": str(archive_path),
        "zip_sha256": file_sha256(archive_path) if archive_path.is_file() else None,
        "configuration_hash": status.get("configuration_hash"),
        "claim_allowed": False,
    }


def import_diagnostic_output(
    path: str | Path,
    *,
    root: str | Path = ".",
) -> dict[str, Any]:
    base = Path(root).resolve()
    source = Path(path)
    verdict = validate_diagnostic_output(source)
    if not verdict["passed"]:
        return {**verdict, "status": "DIAGNOSTIC_IMPORT_REJECTED"}
    digest = str(verdict["zip_sha256"])
    destination = base / "data/imported/diagnostic" / digest
    if not destination.is_dir():
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.partial")
        with zipfile.ZipFile(source) as archive:
            archive.extractall(temporary)
        os.replace(temporary, destination)
    status = {
        "schema_version": "certgen.phase1.diagnostic_import.v1",
        "status": "DIAGNOSTIC_IMPORT_PASS",
        "status_code": "KAGGLE_DIAGNOSTIC_PASS",
        "passed": True,
        "source_zip": str(source),
        "source_zip_sha256": digest,
        "imported_root": str(destination.relative_to(base)),
        "configuration_hash": verdict["configuration_hash"],
        "not_empirical_evidence": True,
        "claim_allowed": False,
    }
    output = base / "data/results/cvpr/diagnostic_import_status.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(status, indent=2, sort_keys=True) + "\n"
    if output.exists() and output.read_text(encoding="utf-8") != serialized:
        raise FileExistsError(f"refusing to overwrite a different diagnostic import status: {output}")
    output.write_text(serialized, encoding="utf-8")
    return status
