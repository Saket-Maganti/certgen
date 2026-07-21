"""Deterministic, content-addressed run capsules."""

from __future__ import annotations

import importlib.metadata
import io
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

import yaml  # type: ignore[import-untyped]

from certgen.cvpr.output_schemas import OUTPUT_SCHEMAS
from certgen.cvpr.profiles import load_profile, validate_profile
from certgen.max_ceiling.common import (
    canonical_json_bytes,
    load_study,
    sha256_bytes,
    sha256_file,
    study_hash,
)
from certgen.max_ceiling.provenance import build_provenance_graph


CAPSULE_STAGES = {
    "preflight",
    "generation",
    "feature",
    "controls",
    "certificate",
    "ranking",
}
REQUIRED_MEMBERS = {
    "run_identity.json",
    "study_snapshot.yaml",
    "profile_snapshot.yaml",
    "expected_output_schema.json",
    "provenance_parents.json",
    "KAGGLE_INSTRUCTIONS.md",
    "validation_commands.txt",
    "dependency_lock/pyproject.toml",
    "dependency_lock/dependencies.json",
}
WEIGHT_SUFFIXES = {".bin", ".ckpt", ".msgpack", ".onnx", ".pt", ".pth", ".safetensors"}


def _yaml(path: str | Path) -> dict[str, Any]:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping: {path}")
    return payload


def _selected_assets(study: Mapping[str, Any], root: Path) -> dict[str, dict[str, Any]]:
    model_registry = _yaml(root / "registry/cvpr/model_registry.yaml")
    feature_registry = _yaml(root / "registry/cvpr/feature_space_registry.yaml")
    models = {str(row.get("model_id")): row for row in model_registry.get("models", [])}
    features = {
        str(row.get("feature_space_id")): row for row in feature_registry.get("feature_spaces", [])
    }
    requested_models = list(map(str, study.get("models", [])))
    requested_features = list(map(str, study.get("feature_spaces", [])))
    missing = sorted((set(requested_models) - set(models)) | (set(requested_features) - set(features)))
    if missing:
        raise ValueError("run capsule rejects unresolved registry rows: " + ", ".join(missing))
    selected = {
        **{f"model__{key}": dict(models[key]) for key in requested_models},
        **{f"feature__{key}": dict(features[key]) for key in requested_features},
    }
    for identity, row in selected.items():
        if not row.get("status") or row.get("claim_allowed") is not False:
            raise ValueError(f"run capsule rejects unknown or unsafe asset: {identity}")
    return selected


def _dependencies() -> dict[str, str]:
    packages = ["certgen", "numpy", "scipy", "PyYAML", "packaging", "pytest"]
    versions: dict[str, str] = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not_installed_optional_or_editable"
    return dict(sorted(versions.items()))


def _output_schema(stage: str) -> dict[str, Any]:
    mapped = "feature" if stage == "feature" else stage
    if mapped in OUTPUT_SCHEMAS:
        return OUTPUT_SCHEMAS[mapped].as_dict()
    return {
        "schema_version": "certgen.maximum_ceiling.local_stage_output.v1",
        "stage": stage,
        "required_fields": [
            "status", "study_hash", "configuration_hash", "provenance_parents",
            "evidence_class", "claim_allowed",
        ],
        "claim_allowed": False,
    }


def _member(name: str, data: bytes) -> tuple[str, bytes]:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError(f"unsafe capsule member: {name}")
    return path.as_posix(), data


def _capsule_members(
    stage: str,
    study_path: str | Path,
    *,
    root: Path,
    public: bool,
) -> list[tuple[str, bytes]]:
    if stage not in CAPSULE_STAGES:
        raise ValueError(f"unsupported run-capsule stage: {stage}")
    study = load_study(study_path)
    profile_id = str(study.get("profile_id", ""))
    profile = load_profile(profile_id, root / "configs/cvpr/profiles")
    verdict = validate_profile(profile)
    if not verdict["passed"]:
        raise ValueError("run capsule rejects invalid profile: " + "; ".join(verdict["errors"]))
    assets = _selected_assets(study, root)
    graph = build_provenance_graph(study_path, root=root, write=False)
    classification = "PUBLIC_REPRODUCIBILITY_CAPSULE" if public else "PRIVATE_KAGGLE_INPUT_CAPSULE"
    identity_basis = {
        "schema_version": "certgen.maximum_ceiling.run_identity.v1",
        "stage": stage,
        "study_hash": study_hash(study),
        "profile_hash": profile["profile_hash"],
        "classification": classification,
        "asset_rows": {key: row.get("revision") for key, row in assets.items()},
        "provenance_graph_hash": graph["graph_hash"],
        "claim_allowed": False,
    }
    identity_basis["capsule_identity_hash"] = sha256_bytes(canonical_json_bytes(identity_basis))
    members: list[tuple[str, bytes]] = [
        _member("run_identity.json", canonical_json_bytes(identity_basis)),
        _member("study_snapshot.yaml", yaml.safe_dump(study, sort_keys=True).encode("utf-8")),
        _member("profile_snapshot.yaml", yaml.safe_dump(profile, sort_keys=True).encode("utf-8")),
        _member("expected_output_schema.json", canonical_json_bytes(_output_schema(stage))),
        _member(
            "provenance_parents.json",
            canonical_json_bytes(
                {
                    "graph_hash": graph["graph_hash"],
                    "parent_artifact_ids": [node["artifact_id"] for node in graph["nodes"]],
                    "claim_allowed": False,
                }
            ),
        ),
        _member("dependency_lock/pyproject.toml", (root / "pyproject.toml").read_bytes()),
        _member("dependency_lock/dependencies.json", canonical_json_bytes(_dependencies())),
        _member(
            "KAGGLE_INSTRUCTIONS.md",
            (
                "# Immutable CertGen run capsule\n\n"
                f"Stage: `{stage}`  \nClassification: `{classification}`\n\n"
                "Mount this capsule read-only, use one worker process per visible GPU, and validate "
                "the output ZIP locally before import. No result in this capsule is empirical evidence.\n"
            ).encode("utf-8"),
        ),
        _member(
            "validation_commands.txt",
            (
                "python3 -m certgen capsule verify <capsule.zip>\n"
                "python3 -m certgen doctor --stage " + stage + " --study <study.yaml> --json\n"
            ).encode("utf-8"),
        ),
    ]
    for path in sorted((root / "registry/cvpr").glob("*")):
        if path.is_file() and path.suffix in {".yaml", ".yml", ".csv", ".json"}:
            members.append(_member(f"registry_snapshot/{path.name}", path.read_bytes()))
    for path in sorted((root / "configs/cvpr").glob("*.yaml")):
        members.append(_member(f"configuration/{path.name}", path.read_bytes()))
    for identity, row in sorted(assets.items()):
        sanitized = dict(row)
        sanitized["asset_bytes_embedded"] = False
        sanitized["capsule_classification"] = classification
        sanitized["claim_allowed"] = False
        members.append(_member(f"asset_manifests/{identity}.json", canonical_json_bytes(sanitized)))
    if public and any(PurePosixPath(name).suffix.lower() in WEIGHT_SUFFIXES for name, _ in members):
        raise ValueError("public run capsule cannot embed restricted model weights")
    return sorted(members, key=lambda item: item[0])


def _zip_bytes(members: list[tuple[str, bytes]]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, data in members:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return output.getvalue()


def build_run_capsule(
    stage: str,
    study_path: str | Path,
    *,
    root: str | Path = ".",
    output: str | Path | None = None,
    public: bool = False,
) -> dict[str, Any]:
    base = Path(root).resolve()
    members = _capsule_members(stage, study_path, root=base, public=public)
    data = _zip_bytes(members)
    digest = sha256_bytes(data)
    target = (
        Path(output)
        if output
        else base / "dist/capsules" / f"{stage}-{digest}.zip"
    )
    if target.exists():
        if target.read_bytes() != data:
            raise FileExistsError(f"refusing to overwrite non-identical run capsule: {target}")
        reused = True
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        reused = False
    return {
        "schema_version": "certgen.maximum_ceiling.run_capsule.v1",
        "status": "CAPSULE_REUSED" if reused else "CAPSULE_BUILT",
        "stage": stage,
        "capsule": str(target),
        "capsule_sha256": digest,
        "member_count": len(members),
        "classification": "PUBLIC_REPRODUCIBILITY_CAPSULE" if public else "PRIVATE_KAGGLE_INPUT_CAPSULE",
        "deterministic": True,
        "claim_allowed": False,
    }


def inspect_run_capsule(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    errors: list[str] = []
    names: list[str] = []
    identity: dict[str, Any] = {}
    if not zipfile.is_zipfile(source):
        errors.append("not a readable ZIP")
    else:
        with zipfile.ZipFile(source) as archive:
            for info in archive.infolist():
                name = info.filename
                names.append(name)
                member = PurePosixPath(name)
                if member.is_absolute() or ".." in member.parts or "\\" in name:
                    errors.append(f"unsafe member: {name}")
                if stat.S_ISLNK(info.external_attr >> 16):
                    errors.append(f"symlink member: {name}")
            missing = sorted(REQUIRED_MEMBERS - set(names))
            errors.extend(f"missing member: {name}" for name in missing)
            if "run_identity.json" in names:
                try:
                    identity = json.loads(archive.read("run_identity.json"))
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    errors.append(f"invalid run_identity.json: {exc}")
    return {
        "schema_version": "certgen.maximum_ceiling.run_capsule_inspection.v1",
        "status": "PASS" if not errors else "LOCAL_DEFECT",
        "passed": not errors,
        "capsule": str(source),
        "capsule_sha256": sha256_file(source) if source.is_file() else None,
        "member_count": len(names),
        "identity": identity,
        "errors": errors,
        "claim_allowed": False,
    }


def verify_run_capsule(path: str | Path) -> dict[str, Any]:
    result = inspect_run_capsule(path)
    errors = list(result["errors"])
    source = Path(path)
    identity = result.get("identity") or {}
    if identity.get("claim_allowed") is not False:
        errors.append("run identity must keep claim_allowed=false")
    classification = identity.get("classification")
    if classification not in {"PRIVATE_KAGGLE_INPUT_CAPSULE", "PUBLIC_REPRODUCIBILITY_CAPSULE"}:
        errors.append("unknown capsule classification")
    if source.is_file() and source.stem.rsplit("-", 1)[-1] not in {result["capsule_sha256"], source.stem}:
        errors.append("content-addressed filename does not match archive SHA-256")
    if classification == "PUBLIC_REPRODUCIBILITY_CAPSULE" and zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as archive:
            restricted = [name for name in archive.namelist() if PurePosixPath(name).suffix.lower() in WEIGHT_SUFFIXES]
        errors.extend(f"restricted weight in public capsule: {name}" for name in restricted)
    return {
        **result,
        "status": "PASS" if not errors else "LOCAL_DEFECT",
        "passed": not errors,
        "errors": errors,
    }
