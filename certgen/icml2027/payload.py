"""Deterministic multipart scientific-payload transport and fail-closed validation."""

from __future__ import annotations

import hashlib
import io
import json
import os
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

import numpy as np
from PIL import Image

from certgen.icml2027.common import file_sha256, stable_hash, write_json


PAYLOAD_TYPES = {"generation", "features"}
REQUIRED_OUTPUT_IDENTITY_FIELDS = {
    "input_package_sha256",
    "study_id",
    "study_hash",
    "configuration_sha256",
    "worker_spec_sha256",
    "source_tree_sha256",
    "dependency_lock_sha256",
    "model_revisions",
    "extractor_revisions",
    "preprocessing_hashes",
    "reference_plan_sha256",
    "seed_manifest_sha256",
    "claim_allowed",
}


def _safe_name(value: str) -> str:
    pure = PurePosixPath(value)
    if not value or pure.is_absolute() or ".." in pure.parts or "\\" in value:
        raise ValueError(f"unsafe payload member: {value}")
    return pure.as_posix()


def _deterministic_zip(path: Path, members: Mapping[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(members.items()):
                safe = _safe_name(name)
                info = zipfile.ZipInfo(safe, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(info, data)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build_multipart_payload(
    *,
    lane: str,
    payload_type: str,
    parts: Sequence[Mapping[str, bytes]],
    records: Sequence[Mapping[str, Any]],
    identity: Mapping[str, Any],
    out_dir: str | Path,
    basename: str,
) -> dict[str, Any]:
    """Write ordered deterministic ZIP parts and a compact authenticated index."""

    if payload_type not in PAYLOAD_TYPES:
        raise ValueError(f"unsupported payload type: {payload_type}")
    if not parts or any(not part for part in parts):
        raise ValueError("multipart payload requires non-empty parts")
    if identity.get("claim_allowed") is not False:
        raise ValueError("scientific identity must carry claim_allowed=false")
    missing_identity = REQUIRED_OUTPUT_IDENTITY_FIELDS - set(identity)
    if missing_identity:
        raise ValueError(f"scientific output identity is incomplete: {sorted(missing_identity)}")
    for field in (
        "input_package_sha256",
        "study_hash",
        "configuration_sha256",
        "worker_spec_sha256",
        "source_tree_sha256",
        "dependency_lock_sha256",
    ):
        value = identity[field]
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"output identity {field} must be an exact SHA-256")
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    inventory: list[dict[str, Any]] = []
    part_rows: list[dict[str, Any]] = []
    names: set[str] = set()
    for part_index, part in enumerate(parts):
        normalized = {_safe_name(name): bytes(data) for name, data in part.items()}
        overlap = names & set(normalized)
        if overlap:
            raise ValueError(f"duplicate payload member across parts: {sorted(overlap)}")
        names.update(normalized)
        part_name = f"{basename}.part{part_index:03d}.zip"
        part_path = target / part_name
        _deterministic_zip(part_path, normalized)
        member_rows = [
            {
                "path": name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "part_index": part_index,
            }
            for name, data in sorted(normalized.items())
        ]
        inventory.extend(member_rows)
        part_rows.append(
            {
                "part_index": part_index,
                "name": part_name,
                "sha256": file_sha256(part_path),
                "bytes": part_path.stat().st_size,
                "member_count": len(member_rows),
                "inventory_sha256": stable_hash(member_rows),
            }
        )
    normalized_records = [dict(row) for row in records]
    manifest = {"inventory": inventory, "records": normalized_records}
    sample_ids = [str(row["sample_id"]) for row in normalized_records if "sample_id" in row]
    if payload_type == "features":
        total_sample_count = sum(int(row.get("row_count", 0)) for row in normalized_records)
        coverage_identity: Any = [row.get("source_sample_ids_sha256") for row in normalized_records]
    else:
        total_sample_count = len(sample_ids)
        coverage_identity = sample_ids
    index: dict[str, Any] = {
        "schema_version": "certgen.icml2027.multipart_payload_index.v1",
        "lane": lane,
        "payload_type": payload_type,
        "identity": dict(identity),
        "part_count": len(part_rows),
        "parts": part_rows,
        "inventory": inventory,
        "records": normalized_records,
        "global_payload_manifest_sha256": stable_hash(manifest),
        "total_sample_count": total_sample_count,
        "sample_id_coverage_sha256": stable_hash(coverage_identity),
        "claim_allowed": False,
    }
    index["payload_index_sha256"] = stable_hash(index)
    index_path = target / f"{basename}.output.index.json"
    write_json(index_path, index)
    return {**index, "index_path": str(index_path)}


def _load_index(index_path: str | Path) -> tuple[Path, dict[str, Any]]:
    path = Path(index_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("payload index must be a mapping")
    return path, payload


def _read_parts(index_path: Path, index: Mapping[str, Any]) -> dict[str, bytes]:
    if index.get("schema_version") != "certgen.icml2027.multipart_payload_index.v1":
        raise ValueError("wrong multipart index schema")
    if index.get("claim_allowed") is not False or index.get("identity", {}).get("claim_allowed") is not False:
        raise ValueError("payload evidence gate is not closed")
    parts = index.get("parts")
    if not isinstance(parts, list) or int(index.get("part_count", -1)) != len(parts) or not parts:
        raise ValueError("multipart part count mismatch")
    expected_inventory = index.get("inventory")
    if not isinstance(expected_inventory, list):
        raise ValueError("multipart inventory missing")
    by_part: dict[int, list[dict[str, Any]]] = {}
    for row in expected_inventory:
        by_part.setdefault(int(row["part_index"]), []).append(dict(row))
    result: dict[str, bytes] = {}
    for expected_index, row in enumerate(parts):
        if int(row.get("part_index", -1)) != expected_index:
            raise ValueError("multipart parts are not in canonical order")
        name = _safe_name(str(row.get("name", "")))
        part_path = index_path.parent / name
        if not part_path.is_file():
            raise FileNotFoundError(f"payload part missing: {name}")
        if part_path.stat().st_size != int(row.get("bytes", -1)) or file_sha256(part_path) != row.get("sha256"):
            raise ValueError(f"payload part corrupt: {name}")
        declared = sorted(by_part.get(expected_index, []), key=lambda item: str(item["path"]))
        if stable_hash(declared) != row.get("inventory_sha256"):
            raise ValueError(f"part inventory identity mismatch: {name}")
        with zipfile.ZipFile(part_path) as archive:
            if len(archive.infolist()) > 200_000 or sum(item.file_size for item in archive.infolist()) > 20 * 1024**3:
                raise ValueError(f"payload part resource limit exceeded: {name}")
            for info in archive.infolist():
                mode = (info.external_attr >> 16) & 0o177777
                if stat.S_IFMT(mode) == stat.S_IFLNK:
                    raise ValueError(f"payload symlink rejected: {info.filename}")
            archive_names = sorted(archive.namelist())
            if len(archive_names) != len(set(item.casefold() for item in archive_names)):
                raise ValueError(f"payload duplicate or case collision: {name}")
            if archive_names != [item["path"] for item in declared]:
                raise ValueError(f"part membership mismatch: {name}")
            for item in declared:
                member = _safe_name(str(item["path"]))
                data = archive.read(member)
                if len(data) != int(item["bytes"]) or hashlib.sha256(data).hexdigest() != item["sha256"]:
                    raise ValueError(f"payload member corrupt: {member}")
                if member in result:
                    raise ValueError(f"duplicate payload member: {member}")
                result[member] = data
    return result


def _validate_generation(index: Mapping[str, Any], members: Mapping[str, bytes]) -> dict[str, Any]:
    records = index.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("generation payload requires sample records")
    seen: set[str] = set()
    models: set[str] = set()
    for row in records:
        required = {
            "sample_id",
            "model_id",
            "checkpoint_id",
            "checkpoint_revision",
            "generator_seed",
            "image_path",
            "image_sha256",
            "shard_id",
            "claim_allowed",
        }
        if not isinstance(row, dict) or not required <= set(row):
            raise ValueError("generation record is incomplete")
        sample_id = str(row["sample_id"])
        if sample_id in seen:
            raise ValueError(f"duplicate generation sample ID: {sample_id}")
        seen.add(sample_id)
        models.add(str(row["model_id"]))
        if row.get("claim_allowed") is not False:
            raise ValueError("generation record evidence gate is open")
        data = members.get(_safe_name(str(row["image_path"])))
        if data is None or hashlib.sha256(data).hexdigest() != row["image_sha256"]:
            raise ValueError(f"generation image missing or corrupt: {sample_id}")
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
        if not 0 <= int(row["generator_seed"]) < 2**63:
            raise ValueError(f"invalid generator seed: {sample_id}")
    return {"samples": len(records), "models": sorted(models)}


def _validate_features(index: Mapping[str, Any], members: Mapping[str, bytes]) -> dict[str, Any]:
    records = index.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("feature payload requires shard records")
    extractors: set[str] = set()
    total_rows = 0
    for row in records:
        required = {
            "extractor_id",
            "extractor_revision",
            "preprocessing_sha256",
            "feature_path",
            "sidecar_path",
            "dimension",
            "dtype",
            "row_count",
            "source_sample_ids_sha256",
            "claim_allowed",
        }
        if not isinstance(row, dict) or not required <= set(row):
            raise ValueError("feature shard record is incomplete")
        if row.get("claim_allowed") is not False:
            raise ValueError("feature record evidence gate is open")
        feature_path = _safe_name(str(row["feature_path"]))
        sidecar_path = _safe_name(str(row["sidecar_path"]))
        if feature_path not in members or sidecar_path not in members:
            raise ValueError("feature array or sidecar is missing")
        sidecar = json.loads(members[sidecar_path])
        with np.load(io.BytesIO(members[feature_path]), allow_pickle=False) as loaded:
            features = np.asarray(loaded["features"])
            sample_ids = [str(value) for value in np.asarray(loaded["sample_ids"]).tolist()]
        expected_shape = (int(row["row_count"]), int(row["dimension"]))
        if features.shape != expected_shape or str(features.dtype) != str(row["dtype"]):
            raise ValueError(f"feature shape/dtype mismatch: {feature_path}")
        if not np.isfinite(features).all():
            raise ValueError(f"non-finite feature values: {feature_path}")
        if len(sample_ids) != len(set(sample_ids)) or stable_hash(sample_ids) != row["source_sample_ids_sha256"]:
            raise ValueError(f"feature row-order mismatch: {feature_path}")
        bound = {
            "sample_ids": sample_ids,
            "extractor_id": row["extractor_id"],
            "extractor_revision": row["extractor_revision"],
            "preprocessing_sha256": row["preprocessing_sha256"],
            "dimension": row["dimension"],
            "dtype": row["dtype"],
            "claim_allowed": False,
        }
        if sidecar != bound:
            raise ValueError(f"feature sidecar mismatch: {sidecar_path}")
        extractors.add(str(row["extractor_id"]))
        total_rows += len(sample_ids)
    return {"feature_rows": total_rows, "extractors": sorted(extractors)}


def validate_multipart_payload(
    index_path: str | Path,
    *,
    expected_type: str | None = None,
    expected_identity: Mapping[str, Any] | None = None,
    seed_manifest_path: str | Path | None = None,
    worker_spec_path: str | Path | None = None,
) -> dict[str, Any]:
    path, index = _load_index(index_path)
    expected_self = stable_hash({key: value for key, value in index.items() if key != "payload_index_sha256"})
    if index.get("payload_index_sha256") != expected_self:
        raise ValueError("payload index self-hash mismatch")
    payload_type = str(index.get("payload_type", ""))
    if expected_type is not None and payload_type != expected_type:
        raise ValueError("wrong payload type")
    if expected_identity is not None:
        for field, value in expected_identity.items():
            if index.get("identity", {}).get(field) != value:
                raise ValueError(f"payload scientific identity mismatch: {field}")
    if index.get("lane") == "dinov2_features":
        identity = index.get("identity", {})
        if identity.get("robustness_feature_space") is not True or identity.get("confirmatory_family") is not False:
            raise ValueError("DINO payload escaped the robustness-only gate")
    members = _read_parts(path, index)
    manifest = {"inventory": index["inventory"], "records": index["records"]}
    if index.get("global_payload_manifest_sha256") != stable_hash(manifest):
        raise ValueError("global payload manifest hash mismatch")
    details = _validate_generation(index, members) if payload_type == "generation" else _validate_features(index, members)
    if seed_manifest_path is not None:
        if payload_type != "generation":
            raise ValueError("a generator seed manifest may validate only a generation payload")
        seed_manifest = json.loads(Path(seed_manifest_path).read_text(encoding="utf-8"))
        expected_rows = {
            (str(row["model_id"]), str(row["sample_id"])): row for row in seed_manifest["records"]
        }
        actual_rows = {
            (str(row["model_id"]), str(row["sample_id"])): row for row in index["records"]
        }
        if set(actual_rows) != set(expected_rows):
            raise ValueError("generation sample set differs from the frozen seed manifest")
        for key, expected_row in expected_rows.items():
            actual_row = actual_rows[key]
            for expected_field, actual_field in (
                ("generator_seed", "generator_seed"),
                ("checkpoint_id", "checkpoint_id"),
                ("checkpoint_revision", "checkpoint_revision"),
            ):
                if actual_row[actual_field] != expected_row[expected_field]:
                    raise ValueError(f"generation frozen identity mismatch: {key}/{actual_field}")
    if worker_spec_path is not None:
        spec = json.loads(Path(worker_spec_path).read_text(encoding="utf-8"))
        if spec.get("lane") != index.get("lane") or spec.get("claim_allowed") is not False:
            raise ValueError("worker spec lane/evidence identity mismatch")
        if stable_hash(spec) != index.get("identity", {}).get("worker_spec_sha256"):
            raise ValueError("worker spec hash mismatch")
        if payload_type == "features":
            rows = index["records"]
            if {str(row["extractor_id"]) for row in rows} != set(spec["extractor_revisions"]):
                raise ValueError("feature extractor set differs from worker spec")
            for row in rows:
                extractor = str(row["extractor_id"])
                if row["extractor_revision"] != spec["extractor_revisions"][extractor]:
                    raise ValueError("feature extractor revision differs from worker spec")
                if row["preprocessing_sha256"] != spec["preprocessing_hashes"][extractor]:
                    raise ValueError("feature preprocessing differs from worker spec")
    return {
        "passed": True,
        "payload_type": payload_type,
        "lane": index["lane"],
        "payload_index_sha256": index["payload_index_sha256"],
        "parts": index["part_count"],
        **details,
        "claim_allowed": False,
    }


def build_copy_forward(index_path: str | Path, out_path: str | Path) -> dict[str, Any]:
    validation = validate_multipart_payload(index_path)
    source = Path(index_path)
    index = json.loads(source.read_text(encoding="utf-8"))
    payload = {
        "schema_version": "certgen.icml2027.copy_forward.v1",
        "source_index": source.name,
        "source_index_file_sha256": file_sha256(source),
        "payload_index_sha256": index["payload_index_sha256"],
        "ordered_parts": [dict(row) for row in index["parts"]],
        "validation": validation,
        "claim_allowed": False,
    }
    payload["copy_forward_sha256"] = stable_hash(payload)
    write_json(out_path, payload)
    return payload


def import_multipart_payload(index_path: str | Path, out_dir: str | Path) -> dict[str, Any]:
    validation = validate_multipart_payload(index_path)
    path, index = _load_index(index_path)
    members = _read_parts(path, index)
    target = Path(out_dir)
    for name, data in members.items():
        output = (target / _safe_name(name)).resolve()
        output.relative_to(target.resolve())
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
    receipt = {
        "schema_version": "certgen.icml2027.payload_import.v1",
        "validation": validation,
        # The receipt lives inside the import root, so a receipt-relative path
        # is both sufficient for replay and portable across execution hosts.
        "import_root": ".",
        "member_count": len(members),
        "claim_allowed": False,
    }
    write_json(target / "IMPORT_RECEIPT.json", receipt)
    return receipt
