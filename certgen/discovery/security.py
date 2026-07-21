"""Archive and path safety primitives used before metadata classification."""

from __future__ import annotations

import stat
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath

from certgen.discovery.models import DiscoveryLimits


NESTED_ARCHIVE_SUFFIXES = (".zip", ".tar", ".tgz", ".tar.gz", ".tar.bz2", ".tar.xz")


@dataclass(frozen=True)
class ArchiveInspection:
    passed: bool
    members: int
    uncompressed_bytes: int
    errors: tuple[str, ...]


def safe_archive_member(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(path.parts) and not path.is_absolute() and ".." not in path.parts and "\\" not in name


def inspect_zip_central_directory(
    archive: zipfile.ZipFile,
    *,
    limits: DiscoveryLimits,
) -> ArchiveInspection:
    errors: list[str] = []
    infos = archive.infolist()
    if len(infos) > limits.maximum_package_members:
        errors.append("archive member-count limit exceeded")
    total = 0
    seen: set[str] = set()
    for info in infos:
        name = info.filename
        key = PurePosixPath(name).as_posix().casefold()
        mode = (info.external_attr >> 16) & 0o170000
        total += max(0, info.file_size)
        if not safe_archive_member(name):
            errors.append(f"unsafe archive member path: {name}")
        if key in seen:
            errors.append(f"duplicate case-folded archive member: {name}")
        seen.add(key)
        if mode == stat.S_IFLNK:
            errors.append(f"symlink archive member refused: {name}")
        elif mode not in {0, stat.S_IFREG, stat.S_IFDIR}:
            errors.append(f"special/hard-link archive member refused: {name}")
        if not info.is_dir() and name.casefold().endswith(NESTED_ARCHIVE_SUFFIXES):
            errors.append(f"nested archive refused: {name}")
        if info.file_size > 0:
            ratio = info.file_size / max(1, info.compress_size)
            if ratio > limits.maximum_compression_ratio:
                errors.append(f"archive compression ratio limit exceeded: {name}")
    if total > limits.maximum_uncompressed_bytes:
        errors.append("archive expansion-byte limit exceeded")
    return ArchiveInspection(not errors, len(infos), total, tuple(errors))


def read_small_member(
    archive: zipfile.ZipFile,
    name: str,
    *,
    limits: DiscoveryLimits,
) -> bytes:
    try:
        info = archive.getinfo(name)
    except KeyError as exc:
        raise FileNotFoundError(f"archive metadata member is missing: {name}") from exc
    if info.file_size > limits.maximum_metadata_bytes:
        raise ValueError(f"archive metadata member exceeds limit: {name}")
    return archive.read(info)
