"""Fail-closed imports for official or author-released sample archives."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import stat
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from certgen.icml2027.common import file_sha256, stable_hash, write_json, write_jsonl


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
MAX_MEMBERS = 1_000_000
MAX_UNCOMPRESSED_BYTES = 2 * 1024**4


@dataclass(frozen=True)
class Member:
    name: str
    size: int
    mode: int


def _safe_name(name: str) -> str:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or normalized.startswith("/")
        or path.is_absolute()
        or ".." in path.parts
        or any(part in {"", "."} for part in path.parts)
        or ":" in path.parts[0]
    ):
        raise ValueError(f"unsafe archive member: {name!r}")
    return path.as_posix()


def _valid_image(data: bytes, suffix: str) -> bool:
    suffix = suffix.lower()
    magic_ok = (
        (suffix == ".png" and data.startswith(b"\x89PNG\r\n\x1a\n"))
        or (suffix in {".jpg", ".jpeg"} and data.startswith(b"\xff\xd8") and data.rstrip().endswith(b"\xff\xd9"))
        or (suffix == ".webp" and data.startswith(b"RIFF") and data[8:12] == b"WEBP")
        or (suffix == ".bmp" and data.startswith(b"BM"))
    )
    if not magic_ok:
        return False
    try:
        from PIL import Image

        with Image.open(io.BytesIO(data)) as image:
            image.verify()
        return True
    except ImportError:
        return magic_ok
    except Exception:
        return False


class _Reader:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.zip: zipfile.ZipFile | None = None
        self.tar: tarfile.TarFile | None = None

    def __enter__(self) -> "_Reader":
        if zipfile.is_zipfile(self.path):
            self.zip = zipfile.ZipFile(self.path)
        elif tarfile.is_tarfile(self.path):
            self.tar = tarfile.open(self.path, mode="r:*")
        else:
            raise ValueError("released-sample archive must be ZIP or TAR")
        return self

    def __exit__(self, *_: object) -> None:
        if self.zip:
            self.zip.close()
        if self.tar:
            self.tar.close()

    def members(self) -> list[Member]:
        rows: list[Member] = []
        if self.zip:
            for zip_info in self.zip.infolist():
                mode = zip_info.external_attr >> 16
                if zip_info.is_dir():
                    continue
                rows.append(Member(zip_info.filename, zip_info.file_size, mode))
        elif self.tar:
            for tar_info in self.tar.getmembers():
                if tar_info.isdir():
                    continue
                rows.append(Member(tar_info.name, tar_info.size, tar_info.mode if tar_info.isfile() else stat.S_IFLNK))
        return rows

    def read(self, name: str) -> bytes:
        if self.zip:
            return self.zip.read(name)
        if self.tar:
            handle = self.tar.extractfile(name)
            if handle is None:
                raise ValueError(f"cannot read archive member {name}")
            return handle.read()
        raise RuntimeError("archive is not open")


def _inventory(archive_path: str | Path, expected_members: list[str] | None = None) -> tuple[list[dict[str, Any]], list[str]]:
    source = Path(archive_path)
    errors: list[str] = []
    inventory: list[dict[str, Any]] = []
    seen_names: set[str] = set()
    seen_casefold: set[str] = set()
    total = 0
    with _Reader(source) as reader:
        members = reader.members()
        if len(members) > MAX_MEMBERS:
            errors.append("archive member count exceeds safety limit")
            return [], errors
        for member in members:
            try:
                name = _safe_name(member.name)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            folded = name.casefold()
            if name in seen_names or folded in seen_casefold:
                errors.append(f"duplicate or case-colliding member: {name}")
                continue
            seen_names.add(name)
            seen_casefold.add(folded)
            if member.mode and not stat.S_ISREG(member.mode) and member.mode & stat.S_IFMT(member.mode):
                errors.append(f"non-regular archive member: {name}")
                continue
            total += member.size
            if total > MAX_UNCOMPRESSED_BYTES:
                errors.append("archive uncompressed size exceeds safety limit")
                break
            suffix = Path(name).suffix.lower()
            if suffix not in IMAGE_SUFFIXES:
                errors.append(f"non-image member is not allowed: {name}")
                continue
            data = reader.read(member.name)
            if len(data) != member.size:
                errors.append(f"member size mismatch: {name}")
                continue
            if not _valid_image(data, suffix):
                errors.append(f"image decode validation failed: {name}")
                continue
            inventory.append(
                {
                    "archive_member": name,
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "suffix": suffix,
                }
            )
    if expected_members is not None and sorted(seen_names) != sorted(_safe_name(name) for name in expected_members):
        errors.append("exact archive membership does not match expected_members")
    return inventory, sorted(set(errors))


def validate_archive(
    archive_path: str | Path,
    *,
    manifest_path: str | Path | None = None,
    expected_count: int | None = None,
) -> dict[str, Any]:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8")) if manifest_path else {}
    expected_members = manifest.get("expected_members")
    inventory, errors = _inventory(archive_path, expected_members if isinstance(expected_members, list) else None)
    resolved_count = expected_count if expected_count is not None else manifest.get("sample_count")
    if resolved_count is not None and len(inventory) != int(resolved_count):
        errors.append(f"sample count mismatch: expected {resolved_count}, found {len(inventory)}")
    archive_hash = file_sha256(archive_path)
    declared_hash = manifest.get("archive_sha256")
    if declared_hash and declared_hash != archive_hash:
        errors.append("archive SHA-256 mismatch")
    hashes = [str(row["sha256"]) for row in inventory]
    duplicate_hashes = sorted(hash_value for hash_value in set(hashes) if hashes.count(hash_value) > 1)
    if duplicate_hashes:
        errors.append(f"duplicate image content detected: {len(duplicate_hashes)} hashes")
    return {
        "schema_version": "certgen.icml2027.released_sample_validation.v1",
        "archive": str(archive_path),
        "archive_sha256": archive_hash,
        "sample_count": len(inventory),
        "inventory_hash": stable_hash(inventory),
        "inventory": inventory,
        "duplicate_hashes": duplicate_hashes,
        "errors": sorted(set(errors)),
        "passed": not errors,
        "source_protocol_verified": bool(manifest.get("sampling_protocol_verified", False)),
        "claim_allowed": False,
    }


def build_manifest(metadata_path: str | Path, archive_path: str | Path, out_path: str | Path) -> dict[str, Any]:
    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8"))
    required = {
        "source_name", "source_type", "source_url_or_repository", "revision", "sampling_protocol",
        "model_id", "benchmark_id", "resolution", "conditioning", "class_balance", "license_status",
        "redistribution_allowed", "provenance_notes",
    }
    missing = sorted(required - set(metadata))
    if missing:
        raise ValueError(f"released-sample metadata missing fields: {missing}")
    validation = validate_archive(archive_path)
    if not validation["passed"]:
        raise ValueError(f"archive validation failed: {validation['errors']}")
    payload = {
        "schema_version": "certgen.icml2027.released_sample_manifest.v1",
        **metadata,
        "archive_sha256": validation["archive_sha256"],
        "sample_count": validation["sample_count"],
        "expected_members": [row["archive_member"] for row in validation["inventory"]],
        "file_inventory_hash": validation["inventory_hash"],
        "prompt_manifest_hash": metadata.get("prompt_manifest_hash"),
        "sampling_protocol_verified": bool(metadata.get("sampling_protocol_verified", False)),
        "claim_allowed": False,
    }
    write_json(out_path, payload)
    return payload


def import_archive(
    archive_path: str | Path,
    manifest_path: str | Path,
    out_dir: str | Path,
) -> dict[str, Any]:
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    validation = validate_archive(archive_path, manifest_path=manifest_path)
    if not validation["passed"]:
        raise ValueError(f"archive validation failed: {validation['errors']}")
    target = Path(out_dir)
    if target.exists():
        raise FileExistsError(f"refusing to overwrite released-sample import: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{target.name}.", dir=target.parent))
    rows: list[dict[str, Any]] = []
    try:
        with _Reader(Path(archive_path)) as reader:
            by_name = {member.name.replace("\\", "/"): member.name for member in reader.members()}
            for index, row in enumerate(validation["inventory"]):
                original_name = str(row["archive_member"])
                data = reader.read(by_name[original_name])
                sample_id = "released_" + stable_hash(
                    {
                        "source": manifest["source_name"],
                        "revision": manifest["revision"],
                        "archive_sha256": validation["archive_sha256"],
                        "image_sha256": row["sha256"],
                        "ordinal": index,
                    }
                )[:24]
                relative = Path("images") / f"{sample_id}{row['suffix']}"
                destination = temporary / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
                rows.append(
                    {
                        "sample_id": sample_id,
                        "path": relative.as_posix(),
                        "image_sha256": row["sha256"],
                        "source_archive_member_hash": hashlib.sha256(original_name.encode()).hexdigest(),
                        "source_name": manifest["source_name"],
                        "model_id": manifest["model_id"],
                        "benchmark_id": manifest["benchmark_id"],
                        "sampling_protocol_verified": bool(manifest.get("sampling_protocol_verified", False)),
                        "claim_allowed": False,
                    }
                )
        write_jsonl(temporary / "sample_manifest.jsonl", rows)
        write_json(
            temporary / "import_summary.json",
            {
                "schema_version": "certgen.icml2027.released_sample_import.v1",
                "archive_sha256": validation["archive_sha256"],
                "manifest_sha256": file_sha256(manifest_path),
                "sample_count": len(rows),
                "sample_manifest_hash": stable_hash(rows),
                "source_protocol_verified": bool(manifest.get("sampling_protocol_verified", False)),
                "claim_allowed": False,
            },
        )
        os.replace(temporary, target)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return json.loads((target / "import_summary.json").read_text(encoding="utf-8"))


def assess_protocol_compatibility(
    generated_manifest: dict[str, Any], released_manifest: dict[str, Any]
) -> dict[str, Any]:
    required_equal = ("model_id", "benchmark_id", "resolution", "conditioning", "class_balance")
    mismatches = [
        field for field in required_equal
        if generated_manifest.get(field) != released_manifest.get(field)
    ]
    verified = (
        generated_manifest.get("sampling_protocol_verified") is True
        and released_manifest.get("sampling_protocol_verified") is True
    )
    compatible = verified and not mismatches and (
        generated_manifest.get("sampling_protocol") == released_manifest.get("sampling_protocol")
    )
    return {
        "schema_version": "certgen.icml2027.sample_protocol_compatibility.v1",
        "compatible_for_shared_confirmatory_family": compatible,
        "sampling_protocols_verified": verified,
        "mismatched_fields": mismatches,
        "protocol_text_equal": generated_manifest.get("sampling_protocol") == released_manifest.get("sampling_protocol"),
        "decision": "COMPATIBLE" if compatible else "KEEP_IN_SEPARATE_FAMILIES",
        "claim_allowed": False,
    }
