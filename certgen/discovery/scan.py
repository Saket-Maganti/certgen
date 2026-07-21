"""Bounded recursive scanner that never follows directory symlinks."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Iterable

from certgen.discovery.models import DiscoveryLimits, ScanReport


EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__MACOSX",
}
PACKAGE_MARKERS = {
    "package_identity.json",
    "package_integrity_manifest.json",
    "integrity_manifest.json",
    "wheelhouse_manifest.json",
    "asset_manifest.json",
}


def _excluded(path: Path) -> bool:
    if path.name in EXCLUDED_DIRECTORY_NAMES:
        return True
    lowered = tuple(part.casefold() for part in path.parts)
    return len(lowered) >= 2 and lowered[-2:] == ("dist", "quarantine")


def scan_package_candidates(
    roots: Iterable[Path],
    *,
    limits: DiscoveryLimits,
) -> tuple[tuple[Path, ...], ScanReport]:
    limits.validate()
    started = time.monotonic()
    candidates: dict[str, Path] = {}
    seen_directories: set[tuple[int, int]] = set()
    files_visited = 0
    directories_visited = 0
    skipped_symlinks = 0
    depth_limit_hits = 0
    inaccessible_paths = 0
    errors: list[str] = []
    normalized_roots = tuple(Path(root).resolve(strict=False) for root in roots)

    def add_candidate(path: Path) -> None:
        key = os.path.normcase(str(path.resolve(strict=False)))
        candidates.setdefault(key, path.resolve(strict=False))
        if len(candidates) > limits.maximum_candidates:
            raise RuntimeError("discovery candidate-count limit exceeded")

    def visit(path: Path, depth: int) -> None:
        nonlocal files_visited, directories_visited, skipped_symlinks
        nonlocal depth_limit_hits, inaccessible_paths
        try:
            if path.is_symlink():
                skipped_symlinks += 1
                return
            if path.is_file():
                files_visited += 1
                if path.suffix.casefold() == ".zip":
                    add_candidate(path)
                elif path.name in PACKAGE_MARKERS:
                    if not (path.parent / ".certgen_runtime_location.json").is_file():
                        add_candidate(path.parent)
                return
            if not path.is_dir() or _excluded(path):
                return
            stat_result = path.stat(follow_symlinks=False)
            inode = (stat_result.st_dev, stat_result.st_ino)
            if inode in seen_directories:
                return
            seen_directories.add(inode)
            directories_visited += 1
            if depth > limits.maximum_depth:
                depth_limit_hits += 1
                return
            with os.scandir(path) as entries:
                ordered = sorted(entries, key=lambda entry: entry.name.casefold())
            for entry in ordered:
                child = Path(entry.path)
                if entry.is_symlink():
                    skipped_symlinks += 1
                    continue
                if entry.is_dir(follow_symlinks=False) and depth == limits.maximum_depth:
                    depth_limit_hits += 1
                    continue
                visit(child, depth + 1)
        except (OSError, PermissionError) as exc:
            inaccessible_paths += 1
            errors.append(f"inaccessible search path: {type(exc).__name__}")

    for root in normalized_roots:
        visit(root, 0)
    ordered_candidates = tuple(sorted(candidates.values(), key=lambda value: str(value).casefold()))
    report = ScanReport(
        roots=tuple(str(root) for root in normalized_roots),
        duration_seconds=time.monotonic() - started,
        files_visited=files_visited,
        directories_visited=directories_visited,
        candidates_found=len(ordered_candidates),
        skipped_symlinks=skipped_symlinks,
        depth_limit_hits=depth_limit_hits,
        inaccessible_paths=inaccessible_paths,
        errors=tuple(errors),
    )
    return ordered_candidates, report


def iter_bounded_files(
    roots: Iterable[Path],
    *,
    limits: DiscoveryLimits,
) -> tuple[Path, ...]:
    """Return bounded regular files for specialized reference/manifest discovery."""

    found: list[Path] = []
    seen: set[tuple[int, int]] = set()

    def visit(path: Path, depth: int) -> None:
        if path.is_symlink() or _excluded(path):
            return
        if path.is_file():
            found.append(path.resolve(strict=False))
            if len(found) > limits.maximum_candidates:
                raise RuntimeError("discovery candidate-count limit exceeded")
            return
        if not path.is_dir() or depth > limits.maximum_depth:
            return
        info = path.stat(follow_symlinks=False)
        inode = (info.st_dev, info.st_ino)
        if inode in seen:
            return
        seen.add(inode)
        try:
            entries = sorted(os.scandir(path), key=lambda entry: entry.name.casefold())
        except OSError:
            return
        for entry in entries:
            if not entry.is_symlink():
                visit(Path(entry.path), depth + 1)

    for root in roots:
        visit(Path(root).resolve(strict=False), 0)
    return tuple(found)
