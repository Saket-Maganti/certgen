"""Classify packages by verified internal identity rather than path names."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any, Mapping

import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.discovery.models import (
    CandidateForm,
    DiscoveryLimits,
    PackageCandidate,
    PackageIdentity,
    PackageType,
)
from certgen.discovery.security import inspect_zip_central_directory, read_small_member


SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")
RUNTIME_MARKERS = {".source_sha256", ".certgen_runtime_location.json"}
STATUS_FILES = {
    "diagnostic": "diagnostic_status.json",
    "preflight": "checkpoint_preflight_status.json",
    "generation": "generation_status.json",
    "features": "feature_extraction_status.json",
}
COMPLETE_STATUSES = {
    "diagnostic": {"KAGGLE_DIAGNOSTIC_PASS"},
    "preflight": {"PREFLIGHT_PASS"},
    "generation": {"GENERATION_COMPLETE", "VALIDATED_GENERATED_PILOT"},
    "features": {"FEATURE_EXTRACTION_SHARDS_COMPLETE"},
}


def _unknown_identity(*, invalid: bool = False) -> PackageIdentity:
    package_type = PackageType.INVALID if invalid else PackageType.UNKNOWN
    return PackageIdentity(
        schema_version="certgen.discovery.unknown.v1",
        package_type=package_type,
        stage=None,
        run_id=None,
        study_hash=None,
        configuration_hash=None,
        profile_id=None,
        scale=None,
        created_at_utc=None,
        claim_allowed=False,
        integrity_manifest=None,
        completion_status=None,
        scientific_identity_hash=hashlib.sha256(package_type.value.encode()).hexdigest(),
    )


def _normalize_stage(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    lowered = value.strip().casefold().replace("_", "-")
    aliases = {
        "diagnostic": "diagnostic",
        "environment-diagnostic": "diagnostic",
        "preflight": "preflight",
        "checkpoint-preflight": "preflight",
        "generation": "generation",
        "feature": "features",
        "features": "features",
        "feature-extraction": "features",
    }
    return aliases.get(lowered)


def _package_type(stage: str | None, direction: str) -> PackageType:
    mapping = {
        ("diagnostic", "input"): PackageType.DIAGNOSTIC_INPUT,
        ("diagnostic", "output"): PackageType.DIAGNOSTIC_OUTPUT,
        ("preflight", "input"): PackageType.PREFLIGHT_INPUT,
        ("preflight", "output"): PackageType.PREFLIGHT_OUTPUT,
        ("generation", "input"): PackageType.GENERATION_INPUT,
        ("generation", "output"): PackageType.GENERATION_OUTPUT,
        ("features", "input"): PackageType.FEATURE_INPUT,
        ("features", "output"): PackageType.FEATURE_OUTPUT,
    }
    if stage is None:
        return PackageType.UNKNOWN
    return mapping.get((stage, direction), PackageType.UNKNOWN)


def _json(data: bytes, name: str) -> dict[str, Any]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON metadata: {name}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"metadata must be an object: {name}")
    return payload


def _yaml(data: bytes, name: str) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(data)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid safe YAML metadata: {name}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"metadata must be a mapping: {name}")
    return payload


def _verify_config(config: Mapping[str, Any], errors: list[str]) -> None:
    if config.get("claim_allowed") is not False:
        errors.append("frozen configuration must set claim_allowed=false")
    declared = config.get("configuration_hash")
    observed = stable_hash_json({key: value for key, value in config.items() if key != "configuration_hash"})
    if declared != observed:
        errors.append("frozen configuration hash mismatch")
    run_id = config.get("run_id")
    if not isinstance(run_id, str) or not SAFE_ID.fullmatch(run_id):
        errors.append("frozen configuration has unsafe or missing run_id")


def _verify_integrity_bytes(
    members: Mapping[str, bytes],
    integrity: Mapping[str, Any],
    integrity_name: str,
    errors: list[str],
) -> None:
    if integrity.get("claim_allowed") is not False:
        errors.append("integrity manifest must set claim_allowed=false")
    rows = integrity.get("files")
    if not isinstance(rows, list) or not rows:
        errors.append("integrity manifest requires a non-empty files list")
        return
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
        data = members.get(name)
        if data is None:
            errors.append(f"integrity manifest references absent member: {name}")
            continue
        if row.get("size") != len(data) or row.get("sha256") != hashlib.sha256(data).hexdigest():
            errors.append(f"integrity size/hash mismatch: {name}")
    actual = set(members) - {integrity_name}
    if actual != declared:
        missing = sorted(actual - declared)
        extra = sorted(declared - actual)
        if missing:
            errors.append("members missing from integrity manifest: " + ", ".join(missing[:20]))
        if extra:
            errors.append("integrity manifest declares absent members: " + ", ".join(extra[:20]))


def _directory_members(root: Path, errors: list[str]) -> dict[str, bytes]:
    members: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            errors.append(f"symlink in extracted package refused: {path.relative_to(root).as_posix()}")
            continue
        if not path.is_file():
            continue
        name = path.relative_to(root).as_posix()
        if name in RUNTIME_MARKERS:
            continue
        members[name] = path.read_bytes()
    return members


def _metadata_from_members(
    members: Mapping[str, bytes],
    *,
    errors: list[str],
) -> tuple[PackageIdentity, list[str]]:
    warnings: list[str] = []
    identity_payload = _json(members["package_identity.json"], "package_identity.json") if "package_identity.json" in members else {}
    config = _yaml(members["configuration.yaml"], "configuration.yaml") if "configuration.yaml" in members else {}
    bundle = _json(members["bundle_manifest.json"], "bundle_manifest.json") if "bundle_manifest.json" in members else {}
    integrity_name = "package_integrity_manifest.json" if "package_integrity_manifest.json" in members else (
        "integrity_manifest.json" if "integrity_manifest.json" in members else ""
    )
    if not identity_payload and not config and not integrity_name:
        return _unknown_identity(), warnings
    if not integrity_name:
        errors.append("package integrity manifest is missing")
        return _unknown_identity(invalid=True), warnings
    integrity = _json(members[integrity_name], integrity_name)
    _verify_integrity_bytes(members, integrity, integrity_name, errors)
    if config:
        _verify_config(config, errors)

    stage = _normalize_stage(identity_payload.get("stage") or bundle.get("stage") or config.get("kind") or config.get("stage"))
    if stage is None:
        errors.append("package stage identity is missing or unsupported")
    status_payload: dict[str, Any] = {}
    status_name = STATUS_FILES.get(stage or "", "")
    if status_name and status_name in members:
        status_payload = _json(members[status_name], status_name)
    elif "status.json" in members:
        status_payload = _json(members["status.json"], "status.json")
    direction = "output" if status_payload or integrity_name == "integrity_manifest.json" else "input"
    inferred_type = _package_type(stage, direction)
    raw_type = identity_payload.get("package_type")
    if isinstance(raw_type, str):
        try:
            package_type = PackageType(raw_type.upper())
        except ValueError:
            errors.append("package_identity.json has an unsupported package_type")
            package_type = inferred_type
        if inferred_type is not PackageType.UNKNOWN and package_type is not inferred_type:
            errors.append("package type conflicts with stage/direction metadata")
    else:
        package_type = inferred_type
        warnings.append("package identity was derived from legacy internal metadata")
    if package_type is PackageType.UNKNOWN:
        errors.append("package type could not be classified")

    run_identity = _json(members["run_identity.json"], "run_identity.json") if "run_identity.json" in members else {}
    run_id = identity_payload.get("run_id") or run_identity.get("run_id") or config.get("run_id")
    configuration_hash = identity_payload.get("configuration_hash") or config.get("configuration_hash")
    pilot_profile: dict[str, Any] = (
        config["pilot_profile"] if isinstance(config.get("pilot_profile"), dict) else {}
    )
    profile_id = identity_payload.get("profile_id") or config.get("profile_id") or pilot_profile.get("profile_id")
    study_hash = identity_payload.get("study_hash") or config.get("study_hash")
    scale = identity_payload.get("scale") or config.get("scale")
    completion = identity_payload.get("completion_status") or status_payload.get("status_code") or (
        "INPUT_PACKAGE_READY" if direction == "input" else None
    )
    created_at = identity_payload.get("created_at_utc") or status_payload.get("created_at_utc") or status_payload.get("completed_at_utc")
    claim_allowed = identity_payload.get("claim_allowed", config.get("claim_allowed", integrity.get("claim_allowed")))
    if claim_allowed is not False:
        errors.append("package identity must set claim_allowed=false")
    if direction == "output" and stage and completion not in COMPLETE_STATUSES[stage]:
        errors.append(f"output completion status is not valid for {stage}: {completion}")
    if identity_payload:
        for field in ("schema_version", "package_type", "stage", "run_id", "configuration_hash", "created_at_utc", "integrity_manifest", "completion_status"):
            if identity_payload.get(field) in {None, ""}:
                errors.append(f"package identity is missing required field: {field}")
        if identity_payload.get("integrity_manifest") != integrity_name:
            errors.append("package identity names the wrong integrity manifest")

    scientific_fields = {
        "package_type": package_type.value,
        "stage": stage,
        "run_id": run_id,
        "study_hash": study_hash,
        "configuration_hash": configuration_hash,
        "profile_id": profile_id,
        "scale": scale,
    }
    scientific_hash = hashlib.sha256(
        json.dumps(scientific_fields, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    declared_scientific_hash = identity_payload.get("scientific_identity_hash")
    if declared_scientific_hash not in {None, scientific_hash}:
        errors.append("declared scientific identity hash mismatch")
    schema_version = str(identity_payload.get("schema_version") or bundle.get("schema_version") or config.get("schema_version") or "certgen.discovery.derived.v1")
    identity = PackageIdentity(
        schema_version=schema_version,
        package_type=PackageType.INVALID if errors else package_type,
        stage=stage,
        run_id=str(run_id) if run_id is not None else None,
        study_hash=str(study_hash) if study_hash is not None else None,
        configuration_hash=str(configuration_hash) if configuration_hash is not None else None,
        profile_id=str(profile_id) if profile_id is not None else None,
        scale=str(scale) if scale is not None else None,
        created_at_utc=str(created_at) if created_at is not None else None,
        claim_allowed=False,
        integrity_manifest=integrity_name,
        completion_status=str(completion) if completion is not None else None,
        scientific_identity_hash=scientific_hash,
    )
    return identity, warnings


def classify_package(path: str | Path, *, limits: DiscoveryLimits | None = None) -> PackageCandidate:
    candidate_path = Path(path).resolve(strict=False)
    selected_limits = limits or DiscoveryLimits()
    errors: list[str] = []
    warnings: list[str] = []
    if candidate_path.is_file():
        form = CandidateForm.ZIP
        digest = file_sha256(candidate_path)
        try:
            with zipfile.ZipFile(candidate_path) as archive:
                inspection = inspect_zip_central_directory(archive, limits=selected_limits)
                errors.extend(inspection.errors)
                if errors:
                    identity = _unknown_identity(invalid=True)
                else:
                    approved_names = {
                        "package_identity.json",
                        "configuration.yaml",
                        "bundle_manifest.json",
                        "package_integrity_manifest.json",
                        "integrity_manifest.json",
                        "run_identity.json",
                        "status.json",
                        *STATUS_FILES.values(),
                    }
                    names = {info.filename for info in archive.infolist() if not info.is_dir()}
                    metadata: dict[str, bytes] = {}
                    # Integrity verification intentionally reads all members only after
                    # the central directory has passed every safety/size limit.
                    if names & {"package_integrity_manifest.json", "integrity_manifest.json"}:
                        metadata = {name: archive.read(name) for name in names}
                    else:
                        metadata = {
                            name: read_small_member(archive, name, limits=selected_limits)
                            for name in sorted(names & approved_names)
                        }
                    identity, derived_warnings = _metadata_from_members(metadata, errors=errors)
                    warnings.extend(derived_warnings)
        except (OSError, zipfile.BadZipFile, RuntimeError, ValueError, KeyError) as exc:
            errors.append(f"package ZIP classification failed: {exc}")
            identity = _unknown_identity(invalid=True)
    elif candidate_path.is_dir():
        form = CandidateForm.EXTRACTED_DIRECTORY
        digest = None
        try:
            members = _directory_members(candidate_path, errors)
            identity, derived_warnings = _metadata_from_members(members, errors=errors)
            warnings.extend(derived_warnings)
            digest = hashlib.sha256(
                b"".join(
                    name.encode() + b"\0" + hashlib.sha256(data).digest()
                    for name, data in sorted(members.items())
                )
            ).hexdigest()
        except (OSError, RuntimeError, ValueError, KeyError) as exc:
            errors.append(f"extracted package classification failed: {exc}")
            identity = _unknown_identity(invalid=True)
    else:
        form = CandidateForm.ZIP
        digest = None
        errors.append("candidate path is not a regular ZIP or extracted directory")
        identity = _unknown_identity(invalid=True)
    valid = not errors and identity.package_type not in {PackageType.INVALID, PackageType.UNKNOWN}
    if errors and identity.package_type is not PackageType.INVALID:
        identity = PackageIdentity(**{**identity.__dict__, "package_type": PackageType.INVALID})
    return PackageCandidate(
        path=candidate_path,
        form=form,
        package_sha256=digest,
        identity=identity,
        valid=valid,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def package_identity_payload(
    config: Mapping[str, Any],
    *,
    package_type: PackageType,
    integrity_manifest: str,
    completion_status: str,
    created_at_utc: str,
) -> dict[str, Any]:
    stage = _normalize_stage(config.get("kind") or config.get("stage"))
    pilot_profile: dict[str, Any] = (
        config["pilot_profile"] if isinstance(config.get("pilot_profile"), dict) else {}
    )
    scientific = {
        "package_type": package_type.value,
        "stage": stage,
        "run_id": config.get("run_id"),
        "study_hash": config.get("study_hash"),
        "configuration_hash": config.get("configuration_hash"),
        "profile_id": config.get("profile_id") or pilot_profile.get("profile_id"),
        "scale": config.get("scale"),
    }
    return {
        "schema_version": "certgen.package_identity.v1",
        **scientific,
        "created_at_utc": created_at_utc,
        "claim_allowed": False,
        "integrity_manifest": integrity_manifest,
        "completion_status": completion_status,
        "scientific_identity_hash": hashlib.sha256(
            json.dumps(scientific, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }
