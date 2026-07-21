"""Append-only registry for imported or packaged CertGen artifacts."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from certgen.core.hashing import file_sha256


REQUIRED_FIELDS = {
    "artifact_id",
    "path",
    "artifact_type",
    "stage",
    "run_id",
    "source",
    "hash",
    "created_at",
    "schema_version",
    "validation_status",
    "evidence_class",
    "claim_allowed",
    "parent_artifacts",
    "notes",
}
NONRETAINED_VALIDATION_STATUSES = {
    "historical_package_manifest_passed_stale_after_source_repairs",
    "superseded_artifact_not_retained",
}


def build_artifact_entry(
    *,
    path: str | Path,
    artifact_type: str,
    stage: str,
    run_id: str,
    source: str,
    validation_status: str,
    evidence_class: str,
    parent_artifacts: list[str] | None = None,
    notes: str = "",
    created_at: str | None = None,
) -> dict[str, Any]:
    artifact = Path(path)
    if not artifact.is_file():
        raise FileNotFoundError(f"artifact is not a file: {artifact}")
    digest = file_sha256(artifact)
    try:
        portable_path = artifact.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        portable_path = str(artifact)
    source_path = Path(source)
    if source_path.exists():
        try:
            portable_source = source_path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            portable_source = source
    else:
        portable_source = source
    return {
        "artifact_id": f"{artifact_type}:{digest[:16]}",
        "path": portable_path,
        "artifact_type": artifact_type,
        "stage": stage,
        "run_id": run_id,
        "source": portable_source,
        "hash": {"algorithm": "sha256", "value": digest},
        "created_at": created_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "schema_version": "certgen.artifact_registry.v1",
        "validation_status": validation_status,
        "evidence_class": evidence_class,
        "claim_allowed": False,
        "parent_artifacts": list(parent_artifacts or []),
        "notes": notes,
    }


def validate_artifact_entry(entry: dict[str, Any]) -> list[str]:
    errors = [f"missing field: {field}" for field in sorted(REQUIRED_FIELDS - set(entry))]
    if entry.get("claim_allowed") is not False:
        errors.append("artifact registry entries must keep claim_allowed=false until a separate claim gate passes")
    digest = entry.get("hash")
    if not isinstance(digest, dict) or digest.get("algorithm") != "sha256" or len(str(digest.get("value", ""))) != 64:
        errors.append("hash must be a sha256 object")
    if entry.get("schema_version") != "certgen.artifact_registry.v1":
        errors.append("unsupported artifact registry schema_version")
    if not isinstance(entry.get("parent_artifacts"), list):
        errors.append("parent_artifacts must be a list")
    return errors


def append_artifact_entry(
    entry: dict[str, Any], registry_path: str | Path = "data/artifact_registry.jsonl"
) -> dict[str, Any]:
    """Append an entry atomically, or return the identical existing entry.

    Reusing an artifact id with different metadata is refused instead of
    silently rewriting provenance history.
    """

    errors = validate_artifact_entry(entry)
    if errors:
        raise ValueError("invalid artifact registry entry: " + "; ".join(errors))
    registry = Path(registry_path)
    registry.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    if registry.exists():
        for number, line in enumerate(registry.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid artifact registry JSON at line {number}") from exc
            rows.append(row)
            if row.get("artifact_id") == entry["artifact_id"]:
                if row == entry:
                    return row
                # created_at is allowed to differ on an idempotent rediscovery.
                comparable_old = {key: value for key, value in row.items() if key != "created_at"}
                comparable_new = {key: value for key, value in entry.items() if key != "created_at"}
                if comparable_old == comparable_new:
                    return row
                raise ValueError(f"artifact_id collision with different metadata: {entry['artifact_id']}")
    serialised = "\n".join(json.dumps(row, sort_keys=True) for row in [*rows, entry]) + "\n"
    temporary = registry.with_name(f".{registry.name}.tmp-{os.getpid()}")
    temporary.write_text(serialised, encoding="utf-8")
    os.replace(temporary, registry)
    return entry


def verify_artifact_registry(registry_path: str | Path = "data/artifact_registry.jsonl") -> dict[str, Any]:
    registry = Path(registry_path)
    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    if not registry.exists():
        errors.append(f"artifact registry missing: {registry}")
    else:
        parsed_lines: list[tuple[int, dict[str, Any]]] = []
        for number, line in enumerate(registry.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {number}: invalid JSON: {exc}")
                continue
            parsed_lines.append((number, row))
        latest_line_for_path = {
            str(row.get("path", "")): number
            for number, row in parsed_lines
            if str(row.get("path", ""))
        }
        for number, row in parsed_lines:
            rows.append(row)
            errors.extend(f"line {number}: {error}" for error in validate_artifact_entry(row))
            artifact_id = str(row.get("artifact_id", ""))
            if artifact_id in seen:
                errors.append(f"line {number}: duplicate artifact_id: {artifact_id}")
            seen.add(artifact_id)
            artifact = Path(str(row.get("path", "")))
            declared = (row.get("hash") or {}).get("value") if isinstance(row.get("hash"), dict) else None
            superseded_at_same_path = latest_line_for_path.get(str(row.get("path", ""))) != number
            if superseded_at_same_path:
                warnings.append(
                    f"line {number}: content-addressed artifact was superseded at its canonical path"
                )
                continue
            if not artifact.is_file():
                if row.get("validation_status") in NONRETAINED_VALIDATION_STATUSES:
                    warnings.append(
                        f"line {number}: historical/superseded artifact is intentionally not retained: {artifact}"
                    )
                else:
                    errors.append(f"line {number}: artifact path missing: {artifact}")
            elif declared != file_sha256(artifact):
                errors.append(f"line {number}: artifact hash mismatch: {artifact}")
    return {
        "passed": not errors,
        "registry_path": str(registry),
        "entries": len(rows),
        "errors": errors,
        "warnings": warnings,
        "claim_allowed": False,
    }
