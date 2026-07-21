"""Deterministic input packages for canonical CVPR Kaggle notebooks."""

from __future__ import annotations

import hashlib
import io
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

import yaml  # type: ignore[import-untyped]
from PIL import Image

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.core.io import write_json
from certgen.cvpr.contracts import atomic_write_json
from certgen.cvpr.image_manifest import read_image_manifest
from certgen.notebooks.cvpr_factory import NOTEBOOK_SPECS
from certgen.notebooks.network_policy import network_policy_from_config


NOTEBOOK_BY_KIND = {
    "preflight": "notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb",
    "generation": "notebooks/kaggle/certgen_cvpr_generation_t4x2_generic.ipynb",
    "features": "notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_generic.ipynb",
}
SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9._-]+$")


def _load_locked_config(path: str | Path, kind: str) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError("notebook configuration must be a mapping")
    declared = payload.get("configuration_hash")
    without_hash = {key: value for key, value in payload.items() if key != "configuration_hash"}
    observed = stable_hash_json(without_hash)
    if declared != observed:
        raise ValueError(f"configuration hash mismatch: declared={declared}, observed={observed}")
    if payload.get("claim_allowed") is not False:
        raise ValueError("notebook input configuration must set claim_allowed=false")
    if payload.get("kind") != kind:
        raise ValueError(f"configuration kind must be {kind}")
    run_id = str(payload.get("run_id", ""))
    if not run_id or any(not SAFE_COMPONENT.fullmatch(component) for component in run_id.split("__")):
        raise ValueError("run_id contains unsafe or empty components")
    required = {
        "preflight": {"models", "extractors", "assets", "tiny_images_per_model", "network_mode", "dependency_network_allowed", "model_asset_network_allowed", "output_schema_version", "requested_gpu_count", "allow_single_gpu_fallback"},
        "generation": {"models", "seed_shards", "samples_per_model", "network_mode", "dependency_network_allowed", "model_asset_network_allowed", "output_schema_version", "preflight_configuration_hash", "benchmark_id", "scale", "requested_gpu_count", "allow_single_gpu_fallback"},
        "features": {"extractors", "image_shards", "source_manifest_hash", "reference_draw_plan", "reference_draw_plan_hash", "network_mode", "dependency_network_allowed", "model_asset_network_allowed", "output_schema_version", "benchmark_id", "scale", "requested_gpu_count", "allow_single_gpu_fallback", "expected_role_counts", "expected_model_ids"},
    }[kind]
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError("configuration missing fields: " + ", ".join(missing))
    if payload.get("requested_gpu_count") != 2 or not isinstance(payload.get("allow_single_gpu_fallback"), bool):
        raise ValueError("canonical T4x2 packages require requested_gpu_count=2 and an explicit fallback boolean")
    network_policy_from_config(payload)
    if kind in {"preflight", "generation"}:
        models = payload.get("models")
        if not isinstance(models, list) or not models:
            raise ValueError("models must be a non-empty list")
        for row in models:
            if not isinstance(row, dict) or not SAFE_COMPONENT.fullmatch(str(row.get("model_id", ""))):
                raise ValueError("every model requires a path-safe model_id")
            if not str(row.get("revision", "")) or str(row.get("revision", "")).startswith("TBD"):
                raise ValueError("every model requires a pinned revision")
    if kind == "preflight" and not 1 <= int(payload.get("tiny_images_per_model", 0)) <= 4:
        raise ValueError("checkpoint preflight must request 1-4 tiny images per model")
    if kind == "preflight":
        extractors = payload.get("extractors")
        assets = payload.get("assets")
        if not isinstance(extractors, list) or not extractors:
            raise ValueError("checkpoint preflight requires feature extractors")
        if not isinstance(assets, list) or not assets or {row.get("asset_kind") for row in assets} != {"model", "extractor"}:
            raise ValueError("checkpoint preflight assets must cover models and extractors")
    if kind == "generation":
        configured_model_ids = {row["model_id"] for row in payload["models"]}
        seed_shards = payload.get("seed_shards")
        if not isinstance(seed_shards, dict) or set(seed_shards) != configured_model_ids:
            raise ValueError("seed_shards must cover every and only configured model")
        expected = int(payload.get("samples_per_model", 0))
        if expected <= 0:
            raise ValueError("samples_per_model must be positive")
        for model_id, shards in seed_shards.items():
            if not isinstance(shards, list) or len(shards) < 2 or any(not isinstance(shard, list) or not shard for shard in shards):
                raise ValueError(f"{model_id}: at least two non-empty deterministic seed shards are required")
            seeds = [seed for shard in shards for seed in shard]
            if len(seeds) != expected or len(set(seeds)) != len(seeds) or any(not isinstance(seed, int) or seed < 0 for seed in seeds):
                raise ValueError(f"{model_id}: seed shards must be disjoint nonnegative integers totaling samples_per_model")
    if kind == "features":
        extractors = payload.get("extractors")
        extractor_ids = {
            row.get("feature_space_id") for row in extractors or [] if isinstance(row, dict)
        }
        if (
            not isinstance(extractors, list)
            or not extractor_ids
            or not extractor_ids.issubset({"inception", "clip", "dinov2"})
        ):
            raise ValueError("feature package requires a non-empty frozen subset of dedicated extractors")
        preprocessing_fields = {"extractor_id", "model_identifier", "revision", "processor_class", "input_resolution", "resize_size", "crop_size", "crop_mode", "interpolation", "antialias", "pixel_range", "channel_order", "mean", "std", "feature_normalization", "precision", "output_dimension", "package_versions"}
        if any(not isinstance(row.get("expected_preprocessing"), dict) or not preprocessing_fields.issubset(row["expected_preprocessing"]) for row in extractors):
            raise ValueError("every extractor requires a complete expected preprocessing contract")
        role_counts = payload.get("expected_role_counts")
        expected_model_ids = payload.get("expected_model_ids")
        if not isinstance(role_counts, dict) or not role_counts or any(not isinstance(value, int) or value <= 0 for value in role_counts.values()):
            raise ValueError("expected_role_counts must contain positive frozen counts")
        if not isinstance(expected_model_ids, list) or not expected_model_ids or len(set(expected_model_ids)) != len(expected_model_ids):
            raise ValueError("expected_model_ids must be a non-empty duplicate-free list")
        image_shards = payload.get("image_shards")
        if not isinstance(image_shards, list) or len(image_shards) < 2 or any(not isinstance(row, dict) or not isinstance(row.get("indices"), list) or not row["indices"] or not row.get("shard_id") or not row.get("role") for row in image_shards):
            raise ValueError("image_shards must contain at least two explicit role-labeled index shards")
        shard_ids = [row["shard_id"] for row in image_shards]
        if len(shard_ids) != len(set(shard_ids)) or any(not SAFE_COMPONENT.fullmatch(str(shard_id)) for shard_id in shard_ids):
            raise ValueError("image_shards require unique path-safe shard IDs")
        indices = [index for row in image_shards for index in row["indices"]]
        if any(not isinstance(index, int) or index < 0 for index in indices) or len(indices) != len(set(indices)):
            raise ValueError("image_shards indices must be disjoint nonnegative integers")
        expected_indices = set(range(sum(role_counts.values())))
        if set(indices) != expected_indices:
            raise ValueError("image_shards must cover every expected manifest row exactly once")
        if payload.get("reference_draw_plan_hash") != stable_hash_json(payload.get("reference_draw_plan")):
            raise ValueError("reference draw plan hash mismatch")
        if payload.get("image_manifest_schema_version") != "certgen.cvpr.image_manifest.v1":
            raise ValueError("feature package must declare the canonical image-manifest schema")
        if payload.get("feature_input_mode") not in {
            "EMBED_IMAGES_IN_PACKAGE",
            "MOUNT_EXTERNAL_IMAGE_DATASET",
        }:
            raise ValueError("feature package has no supported feature_input_mode")
    return payload


def _safe_archive_root(value: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or not path.parts or any(not SAFE_COMPONENT.fullmatch(part) for part in path.parts):
        raise ValueError(f"unsafe package input name: {value}")
    return path.as_posix()


def _files_for_input(name: str, source: Path) -> list[tuple[Path, str]]:
    archive_root = _safe_archive_root(name)
    if not source.exists():
        raise FileNotFoundError(f"package input missing: {source}")
    if source.is_symlink():
        raise ValueError(f"package input symlink refused: {source}")
    if source.is_file():
        return [(source, archive_root)]
    files: list[tuple[Path, str]] = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"package input symlink refused: {path}")
        if not path.is_file():
            continue
        mode = path.stat().st_mode
        if mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
            raise ValueError(f"executable package input refused: {path}")
        relative = path.relative_to(source).as_posix()
        files.append((path, f"{archive_root}/{relative}"))
    if not files:
        raise ValueError(f"package input directory is empty: {source}")
    return files


def _zip_write_bytes(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def build_notebook_input_package(
    *, kind: str, config_path: str | Path, inputs: Mapping[str, str | Path], out_zip: str | Path,
    manifest_out: str | Path,
) -> dict[str, Any]:
    if kind not in NOTEBOOK_BY_KIND:
        raise ValueError(f"unsupported package kind: {kind}")
    config = _load_locked_config(config_path, kind)
    output = Path(out_zip)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite input package: {output}")
    notebook = Path(NOTEBOOK_BY_KIND[kind])
    runtime = Path("certgen/notebooks/cvpr_runtime.py")
    package_sources = sorted(Path("certgen").rglob("*.py"))
    if not notebook.is_file() or not runtime.is_file() or not package_sources:
        raise FileNotFoundError("canonical notebook/runtime assets are missing")
    input_files: list[tuple[Path, str]] = []
    for name, source in sorted(inputs.items()):
        input_files.extend(_files_for_input(name, Path(source)))
    if kind == "generation" and not any(name == "preflight/status.json" for _, name in input_files):
        raise ValueError("generation package requires input mapping preflight=<directory containing status.json>")
    if kind == "features" and not any(name == "manifests/images.jsonl" for _, name in input_files):
        raise ValueError("feature package requires manifests/images.jsonl")
    if kind == "features":
        source_by_name = {name: path for path, name in input_files}
        manifest_source = source_by_name["manifests/images.jsonl"]
        image_rows = read_image_manifest(manifest_source, decode=False)
        if config["feature_input_mode"] == "EMBED_IMAGES_IN_PACKAGE":
            for row in image_rows:
                name = row["relative_image_path"]
                image_source = source_by_name.get(name)
                if image_source is None:
                    raise ValueError(f"feature package omits declared embedded image: {name}")
                if file_sha256(image_source) != row["image_hash"]:
                    raise ValueError(f"embedded feature image hash mismatch: {name}")
                with Image.open(image_source) as image:
                    image.load()
                    if image.size != (row["width"], row["height"]) or image.mode != row["mode"]:
                        raise ValueError(f"embedded feature image decode mismatch: {name}")
        elif "mount_manifest.json" not in source_by_name:
            raise ValueError("external feature input mode requires mount_manifest.json")
    member_rows: list[dict[str, Any]] = []
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x") as archive:
        config_bytes = yaml.safe_dump(config, sort_keys=False).encode("utf-8")
        builtins = [
            ("configuration.yaml", config_bytes),
            (f"{kind[:-1] if kind == 'features' else kind}_config.yaml", config_bytes),
            ("certgen_kaggle_runtime.py", runtime.read_bytes()),
            ("notebook.ipynb", notebook.read_bytes()),
            ("README.md", f"CertGen CVPR {kind} input package. Planning/run infrastructure only; not paper evidence; claim_allowed=false.\n".encode()),
        ]
        builtins.extend((path.as_posix(), path.read_bytes()) for path in package_sources)
        for name, data in builtins:
            _zip_write_bytes(archive, name, data)
            member_rows.append({"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        for path, name in input_files:
            data = path.read_bytes()
            _zip_write_bytes(archive, name, data)
            member_rows.append({"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        integrity = {"files": sorted(member_rows, key=lambda row: row["path"]), "configuration_hash": config["configuration_hash"], "claim_allowed": False}
        integrity_bytes = (json.dumps(integrity, indent=2, sort_keys=True) + "\n").encode()
        _zip_write_bytes(archive, "package_integrity_manifest.json", integrity_bytes)
    payload = {
        "schema_version": "certgen.cvpr.kaggle_input_package.v1",
        "kind": kind,
        "run_id": config["run_id"],
        "configuration_hash": config["configuration_hash"],
        "zip_path": str(output),
        "zip_sha256": file_sha256(output),
        "members": len(member_rows) + 1,
        "notebook": NOTEBOOK_BY_KIND[kind],
        "status": "INPUT_PACKAGE_READY",
        "evidence_class": "planning_only",
        "not_empirical_evidence": True,
        "claim_allowed": False,
    }
    write_json(payload, manifest_out)
    return payload


def freeze_notebook_configuration(input_path: str | Path, out_path: str | Path) -> dict[str, Any]:
    """Freeze a fully specified notebook config to a new hash-bound file."""

    with Path(input_path).open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError("configuration must be a mapping")
    if payload.get("claim_allowed") is not False:
        raise ValueError("configuration must set claim_allowed=false")

    def find_tbd(value: Any, prefix: str = "") -> list[str]:
        if isinstance(value, dict):
            return [item for key, child in value.items() if key != "configuration_hash" for item in find_tbd(child, f"{prefix}.{key}" if prefix else str(key))]
        if isinstance(value, list):
            return [item for index, child in enumerate(value) for item in find_tbd(child, f"{prefix}[{index}]")]
        return [prefix] if isinstance(value, str) and ("TBD" in value or "<" in value or ">" in value) else []

    blockers = find_tbd(payload)
    if blockers:
        raise ValueError("configuration contains unresolved placeholders: " + ", ".join(blockers[:20]))
    payload.pop("configuration_hash", None)
    payload["configuration_hash"] = stable_hash_json(payload)
    _load_locked_config_from_payload = {key: value for key, value in payload.items() if key != "configuration_hash"}
    if payload["configuration_hash"] != stable_hash_json(_load_locked_config_from_payload):  # pragma: no cover
        raise AssertionError("configuration hash construction failed")
    if str(out_path).endswith(".json"):
        atomic_write_json(payload, out_path)
    else:
        _atomic_yaml(payload, out_path)
    return payload


def _atomic_yaml(payload: Mapping[str, Any], out_path: str | Path) -> None:
    output = Path(out_path)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite frozen configuration: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    temporary.write_text(yaml.safe_dump(dict(payload), sort_keys=False), encoding="utf-8")
    temporary.replace(output)


def available_notebook_specs() -> list[str]:
    return sorted(NOTEBOOK_SPECS)


def inspect_notebook_input_package(path: str | Path) -> dict[str, Any]:
    """Validate and summarize a package without extracting or executing it."""

    archive_path = Path(path)
    errors: list[str] = []
    try:
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if archive.testzip() is not None:
                errors.append("input package CRC validation failed")
            if len(names) != len({name.casefold() for name in names}):
                errors.append("input package contains duplicate paths")
            for info in infos:
                member = PurePosixPath(info.filename)
                mode = (info.external_attr >> 16) & 0o170000
                if member.is_absolute() or ".." in member.parts or "\\" in info.filename or mode == stat.S_IFLNK:
                    errors.append(f"unsafe input package member: {info.filename}")
                if info.filename.casefold().endswith((".zip", ".tar", ".tgz", ".tar.gz")):
                    errors.append(f"nested archive refused: {info.filename}")
            required = {"configuration.yaml", "package_integrity_manifest.json", "notebook.ipynb", "README.md"}
            errors.extend(f"missing input package member: {name}" for name in sorted(required - set(names)))
            config: dict[str, Any] = {}
            if "configuration.yaml" in names:
                loaded = yaml.safe_load(archive.read("configuration.yaml"))
                if not isinstance(loaded, dict):
                    errors.append("configuration.yaml is not a mapping")
                else:
                    config = loaded
                    kind = str(config.get("kind", ""))
                    if kind not in NOTEBOOK_BY_KIND:
                        errors.append("configuration kind is unsupported")
                    else:
                        observed = stable_hash_json({key: value for key, value in config.items() if key != "configuration_hash"})
                        if config.get("configuration_hash") != observed:
                            errors.append("configuration hash mismatch")
                        try:
                            network_policy_from_config(config)
                        except (ValueError, FileNotFoundError) as exc:
                            errors.append(str(exc))
            if "package_integrity_manifest.json" in names:
                try:
                    manifest = json.loads(archive.read("package_integrity_manifest.json"))
                    rows = manifest["files"]
                    declared = {row["path"]: row for row in rows}
                    actual = set(names) - {"package_integrity_manifest.json"}
                    if set(declared) != actual:
                        errors.append("input package integrity membership mismatch")
                    for name, row in declared.items():
                        data = archive.read(name)
                        if row.get("size") != len(data) or row.get("sha256") != hashlib.sha256(data).hexdigest():
                            errors.append(f"input package integrity mismatch: {name}")
                except (KeyError, TypeError, json.JSONDecodeError) as exc:
                    errors.append(f"invalid package integrity manifest: {exc}")
            if config.get("kind") == "features" and "manifests/images.jsonl" in names:
                try:
                    rows = [
                        json.loads(line)
                        for line in archive.read("manifests/images.jsonl").decode("utf-8").splitlines()
                        if line.strip()
                    ]
                    feature_mode = config.get("feature_input_mode")
                    if feature_mode == "EMBED_IMAGES_IN_PACKAGE":
                        for row in rows:
                            name = str(row["relative_image_path"])
                            if name not in names:
                                errors.append(f"embedded image is not resolvable in package: {name}")
                                continue
                            data = archive.read(name)
                            if hashlib.sha256(data).hexdigest() != row.get("image_hash"):
                                errors.append(f"embedded image hash mismatch: {name}")
                                continue
                            with Image.open(io.BytesIO(data)) as image:
                                image.load()
                                if image.size != (row.get("width"), row.get("height")) or image.mode != row.get("mode"):
                                    errors.append(f"embedded image decode mismatch: {name}")
                    elif feature_mode == "MOUNT_EXTERNAL_IMAGE_DATASET" and "mount_manifest.json" not in names:
                        errors.append("external feature package omits mount_manifest.json")
                except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError, OSError) as exc:
                    errors.append(f"invalid canonical feature image manifest: {exc}")
    except (OSError, zipfile.BadZipFile) as exc:
        errors.append(f"invalid input package: {exc}")
        config = {}
    kind = str(config.get("kind", "unknown"))
    return {
        "package_type": kind,
        "run_id": config.get("run_id"),
        "configuration_hash": config.get("configuration_hash"),
        "required_assets": [row.get("asset_id") for row in config.get("assets", [])]
        or [row.get("model_id") for row in config.get("models", [])],
        "expected_output": config.get("output_schema_version"),
        "notebook": NOTEBOOK_BY_KIND.get(kind),
        "network_policy": {
            "mode": config.get("network_mode"),
            "dependency_network_allowed": config.get("dependency_network_allowed"),
            "model_asset_network_allowed": config.get("model_asset_network_allowed"),
        },
        "disk_estimate_bytes": config.get("required_disk_bytes", "measure_from_package_and_scale"),
        "passed": not errors,
        "errors": errors,
        "claim_allowed": False,
    }
