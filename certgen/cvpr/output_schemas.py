"""Single source of truth for canonical CVPR Kaggle output ZIP layouts."""

from __future__ import annotations

import hashlib
import json
import re
import stat
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable

import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import stable_hash_json


@dataclass(frozen=True)
class OutputSchema:
    kind: str
    schema_version: str
    status_file: str
    complete_statuses: frozenset[str]
    allowed_roots: frozenset[str]
    required_roots: frozenset[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "schema_version": self.schema_version,
            "status_file": self.status_file,
            "complete_statuses": sorted(self.complete_statuses),
            "allowed_roots": sorted(self.allowed_roots),
            "required_roots": sorted(self.required_roots),
            "claim_allowed": False,
        }


COMMON_ROOTS = frozenset(
    {
        "run_identity.json",
        "package_identity.json",
        "status.json",
        "status",
        "orchestration",
        "logs",
        "environment",
        "configuration.yaml",
        "merge_index.json",
        "integrity_manifest.json",
        "copyback_instructions.md",
        "final_zip_status.json",
    }
)

OUTPUT_SCHEMAS: dict[str, OutputSchema] = {
    "preflight": OutputSchema(
        "preflight",
        "certgen.cvpr.preflight_output.v2",
        "checkpoint_preflight_status.json",
        frozenset({"PREFLIGHT_PASS"}),
        COMMON_ROOTS
        | frozenset(
            {
                "checkpoint_preflight_status.json",
                "per_asset",
                "per_model",
                "per_extractor",
                "model_cache",
                "asset_manifests",
                "smoke_images",
                "runtime_calibration.json",
            }
        ),
        frozenset(
            {
                "checkpoint_preflight_status.json",
                "configuration.yaml",
                "run_identity.json",
                "per_model",
                "per_extractor",
            }
        ),
    ),
    "generation": OutputSchema(
        "generation",
        "certgen.cvpr.generation_output.v2",
        "generation_status.json",
        frozenset({"GENERATION_COMPLETE", "VALIDATED_GENERATED_PILOT"}),
        COMMON_ROOTS
        | frozenset(
            {
                "generation_status.json",
                "per_model",
                "per_shard",
                "samples",
                "images",
                "manifests",
                "asset_manifests",
                "model_cache",
            }
        ),
        frozenset(
            {"generation_status.json", "configuration.yaml", "run_identity.json", "per_model"}
        ),
    ),
    "feature": OutputSchema(
        "feature",
        "certgen.cvpr.feature_output.v2",
        "feature_extraction_status.json",
        frozenset({"FEATURE_EXTRACTION_SHARDS_COMPLETE"}),
        COMMON_ROOTS
        | frozenset(
            {
                "feature_extraction_status.json",
                "shards",
                "features",
                "sidecars",
                "manifests",
                "preprocessing_contracts",
                "asset_manifests",
                "model_cache",
                "merged",
            }
        ),
        frozenset(
            {"feature_extraction_status.json", "configuration.yaml", "run_identity.json", "shards"}
        ),
    ),
}


ALLOWED_SUFFIXES = {
    "",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".csv",
    ".md",
    ".txt",
    ".log",
    ".png",
    ".ppm",
    ".npy",
    ".npz",
    ".pt",
    ".pth",
    ".ckpt",
    ".model",
    ".safetensors",
    ".bin",
}
NESTED_ARCHIVE_SUFFIXES = (".zip", ".tar", ".tgz", ".tar.gz")
SAFE_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}")


def normalize_kind(kind: str) -> str:
    selected = "feature" if kind == "features" else kind
    if selected not in OUTPUT_SCHEMAS:
        raise ValueError(f"unknown CVPR output kind: {kind}")
    return selected


def schema_for(kind: str) -> OutputSchema:
    return OUTPUT_SCHEMAS[normalize_kind(kind)]


def expected_output_schema(kind: str) -> dict[str, Any]:
    return schema_for(kind).as_dict()


def member_allowed(kind: str, name: str) -> bool:
    schema = schema_for(kind)
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name or not path.parts:
        return False
    if name.casefold().endswith(NESTED_ARCHIVE_SUFFIXES):
        return False
    root = path.parts[0]
    return root in schema.allowed_roots and path.suffix.lower() in ALLOWED_SUFFIXES


def validate_member_names(kind: str, infos: Iterable[zipfile.ZipInfo]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    roots: set[str] = set()
    for info in infos:
        name = info.filename
        key = name.casefold()
        mode = (info.external_attr >> 16) & 0o170000
        if key in seen:
            errors.append(f"duplicate ZIP path: {name}")
        seen.add(key)
        if mode == stat.S_IFLNK:
            errors.append(f"symlink ZIP member refused: {name}")
        if mode == stat.S_IFREG and info.external_attr >> 16 & 0o111:
            errors.append(f"executable ZIP member refused: {name}")
        if not member_allowed(kind, name):
            errors.append(f"unsupported output member: {name}")
        path = PurePosixPath(name)
        if path.parts:
            roots.add(path.parts[0])
    missing = sorted(schema_for(kind).required_roots - roots)
    errors.extend(f"missing required output root: {name}" for name in missing)
    return errors


def validate_status_payload(kind: str, payload: Any) -> list[str]:
    schema = schema_for(kind)
    if not isinstance(payload, dict):
        return ["canonical status must be a JSON object"]
    errors: list[str] = []
    if payload.get("claim_allowed") is not False:
        errors.append("canonical status must set claim_allowed=false")
    if payload.get("status_code") not in schema.complete_statuses:
        errors.append(
            f"canonical status_code must be one of {sorted(schema.complete_statuses)}"
        )
    if payload.get("output_schema_version") != schema.schema_version:
        errors.append("canonical output schema version mismatch")
    expected = payload.get("expected_workers")
    completed = payload.get("completed_workers")
    if not isinstance(expected, list) or not expected or len(expected) != len(set(expected)):
        errors.append("canonical status requires unique non-empty expected_workers")
    if not isinstance(completed, list) or sorted(completed) != sorted(expected or []):
        errors.append("completed_workers must exactly equal expected_workers")
    return errors


def validate_output_zip(kind: str, path: str, *, maximum_bytes: int = 50 * 1024**3) -> dict[str, Any]:
    schema = schema_for(kind)
    errors: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if archive.testzip() is not None:
                errors.append("output ZIP CRC validation failed")
            if sum(info.file_size for info in infos) > maximum_bytes:
                errors.append("output ZIP expansion limit exceeded")
            errors.extend(validate_member_names(kind, infos))
            identity: dict[str, Any] = {}
            config: dict[str, Any] = {}
            identity_candidates = [info for info in infos if info.filename == "run_identity.json"]
            config_candidates = [info for info in infos if info.filename == "configuration.yaml"]
            if len(identity_candidates) != 1:
                errors.append("expected exactly one root run_identity.json")
            else:
                try:
                    loaded_identity = json.loads(archive.read(identity_candidates[0]).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    errors.append(f"invalid run identity JSON: {exc}")
                else:
                    if not isinstance(loaded_identity, dict):
                        errors.append("run identity must be a JSON object")
                    else:
                        identity = loaded_identity
                        if identity.get("claim_allowed") is not False:
                            errors.append("run identity must set claim_allowed=false")
                        if not isinstance(identity.get("run_id"), str) or not SAFE_RUN_ID.fullmatch(
                            identity["run_id"]
                        ):
                            errors.append("run identity has an unsafe or missing run_id")
            if len(config_candidates) != 1:
                errors.append("expected exactly one root configuration.yaml")
            else:
                try:
                    loaded_config = yaml.safe_load(archive.read(config_candidates[0]))
                except yaml.YAMLError as exc:
                    errors.append(f"invalid frozen configuration YAML: {exc}")
                else:
                    if not isinstance(loaded_config, dict):
                        errors.append("frozen configuration must be a mapping")
                    else:
                        config = loaded_config
                        observed_hash = stable_hash_json(
                            {key: value for key, value in config.items() if key != "configuration_hash"}
                        )
                        if config.get("configuration_hash") != observed_hash:
                            errors.append("frozen configuration hash mismatch")
                        if config.get("claim_allowed") is not False:
                            errors.append("frozen configuration must set claim_allowed=false")
            if identity and config:
                if identity.get("run_id") != config.get("run_id"):
                    errors.append("run identity and frozen configuration disagree on run_id")
                if identity.get("configuration_hash") != config.get("configuration_hash"):
                    errors.append("run identity and frozen configuration disagree on configuration_hash")
            integrity_candidates = [info for info in infos if info.filename == "integrity_manifest.json"]
            if len(integrity_candidates) != 1:
                errors.append("expected exactly one root integrity_manifest.json")
            else:
                try:
                    integrity = json.loads(archive.read(integrity_candidates[0]).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    errors.append(f"invalid integrity manifest JSON: {exc}")
                else:
                    rows = integrity.get("files") if isinstance(integrity, dict) else None
                    if not isinstance(rows, list) or not rows:
                        errors.append("integrity manifest requires a non-empty files list")
                    else:
                        info_by_name = {info.filename: info for info in infos if not info.is_dir()}
                        declared: set[str] = set()
                        for index, row in enumerate(rows, start=1):
                            if not isinstance(row, dict):
                                errors.append(f"integrity row {index} is not an object")
                                continue
                            name = row.get("path")
                            if not isinstance(name, str) or not name or name in declared:
                                errors.append(f"integrity row {index} has a missing or duplicate path")
                                continue
                            declared.add(name)
                            info = info_by_name.get(name)
                            if info is None or name == "integrity_manifest.json":
                                errors.append(f"integrity row {index} references an invalid member: {name}")
                                continue
                            if row.get("size") != info.file_size:
                                errors.append(f"integrity size mismatch: {name}")
                            digest = hashlib.sha256(archive.read(name)).hexdigest()
                            if row.get("sha256") != digest:
                                errors.append(f"integrity hash mismatch: {name}")
                        actual = set(info_by_name) - {"integrity_manifest.json"}
                        missing = sorted(actual - declared)
                        extra = sorted(declared - actual)
                        if missing:
                            errors.append("ZIP members missing from integrity manifest: " + ", ".join(missing[:20]))
                        if extra:
                            errors.append("integrity manifest declares absent members: " + ", ".join(extra[:20]))
            candidates = [info.filename for info in infos if info.filename == schema.status_file]
            if len(candidates) != 1:
                errors.append(f"expected exactly one {schema.status_file}")
            else:
                try:
                    payload = json.loads(archive.read(candidates[0]).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    errors.append(f"invalid canonical status JSON: {exc}")
                else:
                    errors.extend(validate_status_payload(kind, payload))
                    if config and payload.get("configuration_hash") != config.get("configuration_hash"):
                        errors.append("canonical status and frozen configuration disagree on configuration_hash")
    except (OSError, zipfile.BadZipFile) as exc:
        errors.append(f"invalid output ZIP: {exc}")
    return {
        "kind": normalize_kind(kind),
        "schema_version": schema.schema_version,
        "passed": not errors,
        "errors": errors,
        "claim_allowed": False,
    }
