"""Canonical, no-download CIFAR-10 validation and materialization wrapper."""

from __future__ import annotations

import hashlib
import os
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from certgen.core.hashing import file_sha256
from certgen.cvpr.contracts import atomic_write_json
from certgen.data.build_cifar10_reference_manifest import build_reference_manifest
from certgen.data.cifar_reference_super_onramp import (
    MAX_TAR_MEMBERS,
    MAX_TAR_UNCOMPRESSED_BYTES,
    _detect_candidate,
    _inspect_official_tarball,
)


MAX_CONTAINER_MEMBERS = 96
MAX_CONTAINER_BYTES = 300 * 1024**2


def _safe_name(name: str) -> PurePosixPath:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name or not path.parts:
        raise ValueError(f"unsafe reference container member: {name}")
    return path


def validate_reference_source(source: str | Path) -> dict[str, Any]:
    path = Path(source)
    candidate = _detect_candidate(path)
    errors: list[str] = []
    layout = candidate.layout
    if candidate.accepted:
        return {"passed": True, "source": str(path), "layout": layout, "reason": candidate.reason, "source_sha256": file_sha256(path) if path.is_file() else None, "claim_allowed": False}
    if not path.is_file() or path.suffix.lower() not in {".zip", ".tar", ".tgz", ".gz"}:
        return {"passed": False, "source": str(path), "layout": layout, "errors": [candidate.reason], "claim_allowed": False}
    names: list[str] = []
    total = 0
    try:
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                if archive.testzip() is not None:
                    errors.append("reference ZIP CRC validation failed")
                infos = archive.infolist()
                if len(infos) > MAX_CONTAINER_MEMBERS:
                    errors.append("reference ZIP member count exceeds limit")
                for info in infos:
                    _safe_name(info.filename)
                    total += info.file_size
                    names.append(info.filename)
        elif tarfile.is_tarfile(path):
            with tarfile.open(path) as archive:
                members = archive.getmembers()
                if len(members) > MAX_CONTAINER_MEMBERS:
                    errors.append("reference TAR member count exceeds limit")
                for member in members:
                    _safe_name(member.name)
                    if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                        errors.append(f"unsafe reference TAR member type: {member.name}")
                    total += max(0, member.size)
                    names.append(member.name)
        else:
            errors.append("unsupported reference container")
    except (OSError, ValueError, zipfile.BadZipFile, tarfile.TarError) as exc:
        errors.append(str(exc))
    if total > MAX_CONTAINER_BYTES:
        errors.append("reference container expansion exceeds limit")
    basenames = {PurePosixPath(name).name for name in names}
    official_batches = {*(f"data_batch_{index}" for index in range(1, 6)), "test_batch"}
    has_official = official_batches.issubset(basenames) or "cifar-10-python.tar.gz" in basenames
    if not has_official:
        errors.append("container does not contain the official CIFAR Python batch structure")
    return {
        "passed": not errors,
        "source": str(path),
        "layout": "validated_official_structure_container" if not errors else "rejected_container",
        "errors": errors,
        "source_sha256": file_sha256(path),
        "members": len(names),
        "claim_allowed": False,
    }


def _extract_official_tarball(path: Path, destination: Path) -> Path:
    errors = _inspect_official_tarball(path)
    if errors:
        raise ValueError("official CIFAR archive failed validation: " + "; ".join(errors))
    target = destination / "cifar-10-batches-py"
    if target.exists():
        raise FileExistsError(f"refusing to overwrite reference extraction: {target}")
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".reference-tar-", dir=destination) as temporary_name:
        temporary = Path(temporary_name) / "cifar-10-batches-py"
        temporary.mkdir()
        with tarfile.open(path, "r:gz") as archive:
            members = archive.getmembers()
            if len(members) > MAX_TAR_MEMBERS or sum(max(0, member.size) for member in members) > MAX_TAR_UNCOMPRESSED_BYTES:
                raise ValueError("official CIFAR archive exceeds safety limits")
            for member in members:
                pure = _safe_name(member.name)
                if not member.isfile() or pure.parts[0] != "cifar-10-batches-py":
                    continue
                output = temporary.joinpath(*pure.parts[1:])
                output.parent.mkdir(parents=True, exist_ok=True)
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError(f"unable to read archive member: {member.name}")
                with stream, output.open("xb") as handle:
                    shutil.copyfileobj(stream, handle, 1024 * 1024)
        os.replace(temporary, target)
    return target


def _extract_validated_container(path: Path, destination: Path) -> Path:
    """Extract only official batch members (or the official tarball) by basename."""

    if destination.exists():
        raise FileExistsError(f"refusing to overwrite reference extraction: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    expected = {*(f"data_batch_{index}" for index in range(1, 6)), "test_batch", "batches.meta", "readme.html"}
    with tempfile.TemporaryDirectory(prefix=".reference-container-", dir=destination.parent) as temporary_name:
        temporary = Path(temporary_name)
        batch_root = temporary / "cifar-10-batches-py"
        batch_root.mkdir()
        inner_tar: Path | None = None
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as archive:
                for info in archive.infolist():
                    pure = _safe_name(info.filename)
                    name = pure.name
                    if name == "cifar-10-python.tar.gz":
                        inner_tar = temporary / name
                        with archive.open(info) as zip_source, inner_tar.open("xb") as output:
                            shutil.copyfileobj(zip_source, output, 1024 * 1024)
                    elif name in expected and not info.is_dir():
                        with archive.open(info) as zip_source, (batch_root / name).open("xb") as output:
                            shutil.copyfileobj(zip_source, output, 1024 * 1024)
        else:
            with tarfile.open(path) as archive:
                for member in archive.getmembers():
                    pure = _safe_name(member.name)
                    if not member.isfile():
                        continue
                    tar_source = archive.extractfile(member)
                    if tar_source is None:
                        raise ValueError(f"unable to read reference container member: {member.name}")
                    name = pure.name
                    if name == "cifar-10-python.tar.gz":
                        inner_tar = temporary / name
                        with tar_source, inner_tar.open("xb") as output:
                            shutil.copyfileobj(tar_source, output, 1024 * 1024)
                    elif name in expected:
                        with tar_source, (batch_root / name).open("xb") as output:
                            shutil.copyfileobj(tar_source, output, 1024 * 1024)
        if inner_tar is not None:
            shutil.rmtree(batch_root)
            extracted = _extract_official_tarball(inner_tar, temporary / "official")
            os.replace(extracted.parent, destination)
            return destination / "cifar-10-batches-py"
        required = {*(f"data_batch_{index}" for index in range(1, 6)), "test_batch"}
        if not required.issubset({item.name for item in batch_root.iterdir()}):
            raise ValueError("validated container extraction did not produce all official CIFAR batches")
        os.replace(batch_root, destination)
    return destination


def materialize_reference_source(
    source: str | Path, *, out_manifest: str | Path = "registry/manifests/cvpr/cifar10_reference.jsonl",
    out_summary: str | Path = "data/results/cvpr_reference_materialization.json",
    extraction_root: str | Path = "data/reference_materialized",
) -> dict[str, Any]:
    verdict = validate_reference_source(source)
    if not verdict["passed"]:
        raise ValueError("reference source invalid: " + "; ".join(verdict.get("errors", [])))
    path = Path(source)
    final_manifest = Path(out_manifest)
    final_summary = Path(out_summary)
    for output in (final_manifest, final_summary):
        if output.exists():
            raise FileExistsError(f"refusing to overwrite existing reference artifact: {output}")
    root = path
    if verdict["layout"] == "official_cifar_tarball":
        root = _extract_official_tarball(path, Path(extraction_root) / file_sha256(path)[:16])
    elif verdict["layout"] == "validated_official_structure_container":
        root = _extract_validated_container(path, Path(extraction_root) / file_sha256(path)[:16] / "cifar-10-batches-py")
    elif verdict["layout"] == "official_cifar_10_batches_py":
        source_batches = path / "cifar-10-batches-py" if (path / "cifar-10-batches-py").is_dir() else path
        destination = Path(extraction_root) / stable_directory_hash(source_batches) / "cifar-10-batches-py"
        if destination.exists():
            raise FileExistsError(f"refusing to overwrite preserved extracted-batch copy: {destination}")
        destination.mkdir(parents=True)
        for name in [*(f"data_batch_{index}" for index in range(1, 6)), "test_batch", "batches.meta", "readme.html"]:
            candidate = source_batches / name
            if candidate.is_file():
                shutil.copy2(candidate, destination / name)
        root = destination
    final_manifest.parent.mkdir(parents=True, exist_ok=True)
    builder_manifest = final_manifest.with_name(f".{final_manifest.name}.builder")
    builder_summary = final_summary.with_name(f".{final_summary.name}.builder")
    for builder in (builder_manifest, builder_summary):
        if builder.exists():
            raise FileExistsError(f"stale builder artifact requires review: {builder}")
    summary = build_reference_manifest(
        cifar_root=root, split="test", out_manifest=builder_manifest, out_summary=builder_summary,
        license_status="cifar10_source_license_requires_release_review",
        source_url="https://www.cs.toronto.edu/~kriz/cifar.html", claim_allowed=False,
    )
    if summary.get("rows") != 10_000 or summary.get("counts_by_split", {}).get("test") != 10_000:
        raise ValueError("materialized CIFAR test manifest must contain exactly 10000 rows")
    summary.update({"source_sha256": file_sha256(path) if path.is_file() else None, "source_validation": verdict, "status_code": "REFERENCE_MATERIALIZED", "claim_allowed": False})
    os.replace(builder_manifest, final_manifest)
    summary["out_manifest"] = str(final_manifest)
    builder_summary.unlink(missing_ok=True)
    atomic_write_json(summary, final_summary, overwrite_identical=True)
    return summary


def stable_directory_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.iterdir(), key=lambda candidate: candidate.name):
        if item.is_file():
            digest.update(item.name.encode("utf-8"))
            digest.update(str(item.stat().st_size).encode("ascii"))
            digest.update(file_sha256(item).encode("ascii"))
    return digest.hexdigest()[:16]
