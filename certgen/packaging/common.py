"""Shared helpers for V6 Kaggle input/output packages."""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

from certgen.core.hashing import file_sha256
from certgen.core.io import write_json


FORBIDDEN_ARCHIVE_PARTS = {
    "data/results",
    "data/features",
    "data/smoke",
    "paper",
}
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
]

NESTED_ARCHIVE_SUFFIXES = (
    ".zip",
    ".tar",
    ".tar.gz",
    ".tgz",
    ".tar.bz2",
    ".tbz2",
    ".tar.xz",
    ".txz",
    ".7z",
    ".rar",
)


@dataclass(frozen=True)
class ZipSafetyLimits:
    """Fail-closed resource limits for copied-back execution archives.

    The defaults accommodate the planned 1k execution lane while preventing an
    importer from accepting an unbounded member count or decompression bomb.
    Larger, explicitly approved runs can pass a reviewed limits instance.
    """

    max_members: int = 200_000
    max_member_uncompressed_bytes: int = 4 * 1024**3
    max_total_uncompressed_bytes: int = 20 * 1024**3
    max_compression_ratio: float = 1_000.0


DEFAULT_ZIP_LIMITS = ZipSafetyLimits()


def _normalise_zip_name(name: str) -> str:
    if not name or "\x00" in name or "\\" in name:
        raise ValueError(f"unsafe ZIP member name: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe ZIP member path: {name}")
    # Reject drive-like roots even on POSIX so the same archive is safe on Windows.
    if path.parts and re.fullmatch(r"[A-Za-z]:", path.parts[0]):
        raise ValueError(f"unsafe ZIP drive path: {name}")
    return path.as_posix().rstrip("/")


def _zip_member_mode(info: zipfile.ZipInfo) -> int:
    return (info.external_attr >> 16) & 0xFFFF


def inspect_zip_safety(
    zip_path: str | Path,
    *,
    limits: ZipSafetyLimits = DEFAULT_ZIP_LIMITS,
    reject_nested_archives: bool = True,
    reject_executables: bool = True,
) -> dict[str, Any]:
    """Inspect a ZIP without extracting it and return a machine-readable verdict."""

    path = Path(zip_path)
    errors: list[str] = []
    members: list[dict[str, Any]] = []
    total_uncompressed = 0
    seen: set[str] = set()
    if not path.is_file():
        return {
            "passed": False,
            "errors": [f"ZIP missing: {path}"],
            "members": [],
            "limits": asdict(limits),
            "claim_allowed": False,
        }
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = archive.infolist()
            if len(infos) > limits.max_members:
                errors.append(f"member count {len(infos)} exceeds limit {limits.max_members}")
            for info in infos:
                try:
                    normalised = _normalise_zip_name(info.filename)
                except ValueError as exc:
                    errors.append(str(exc))
                    continue
                collision_key = normalised.casefold()
                if collision_key in seen:
                    errors.append(f"duplicate or case-colliding ZIP member: {info.filename}")
                seen.add(collision_key)
                mode = _zip_member_mode(info)
                file_type = stat.S_IFMT(mode)
                if file_type == stat.S_IFLNK:
                    errors.append(f"symlink ZIP member refused: {info.filename}")
                elif file_type and file_type not in {stat.S_IFREG, stat.S_IFDIR}:
                    errors.append(f"special-file ZIP member refused: {info.filename}")
                if reject_executables and not info.is_dir() and mode and mode & 0o111:
                    errors.append(f"executable ZIP member refused: {info.filename}")
                if info.flag_bits & 0x1:
                    errors.append(f"encrypted ZIP member refused: {info.filename}")
                lowered = normalised.lower()
                if reject_nested_archives and not info.is_dir() and lowered.endswith(NESTED_ARCHIVE_SUFFIXES):
                    errors.append(f"nested archive refused: {info.filename}")
                if info.file_size > limits.max_member_uncompressed_bytes:
                    errors.append(
                        f"member {info.filename} uncompressed size {info.file_size} exceeds "
                        f"limit {limits.max_member_uncompressed_bytes}"
                    )
                total_uncompressed += info.file_size
                ratio = info.file_size / max(info.compress_size, 1)
                if info.file_size and ratio > limits.max_compression_ratio:
                    errors.append(
                        f"member {info.filename} compression ratio {ratio:.1f} exceeds "
                        f"limit {limits.max_compression_ratio:.1f}"
                    )
                members.append(
                    {
                        "path": normalised,
                        "compressed_size": info.compress_size,
                        "uncompressed_size": info.file_size,
                        "crc32": f"{info.CRC:08x}",
                        "is_dir": info.is_dir(),
                    }
                )
            if total_uncompressed > limits.max_total_uncompressed_bytes:
                errors.append(
                    f"total uncompressed size {total_uncompressed} exceeds "
                    f"limit {limits.max_total_uncompressed_bytes}"
                )
            bad_member = archive.testzip()
            if bad_member is not None:
                errors.append(f"CRC check failed for ZIP member: {bad_member}")
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        errors.append(f"invalid ZIP: {exc}")
    return {
        "passed": not errors,
        "errors": sorted(set(errors)),
        "members": members,
        "member_count": len(members),
        "total_uncompressed_bytes": total_uncompressed,
        "limits": asdict(limits),
        "claim_allowed": False,
    }


def default_checkpoints() -> list[dict[str, Any]]:
    return [
        {
            "checkpoint_id": "google/ddpm-cifar10-32",
            "short_id": "google_ddpm",
            "revision": "267b167dc01f0e4e61923ea244e8b988f84deb80",
        },
        {
            "checkpoint_id": "FrankCCCCC/ddpm_ema_cifar10",
            "short_id": "frank_ddpm_ema",
            "revision": "6aa387f240fbb00d0e003f93a3b994f56dd98dc2",
        },
        {
            "checkpoint_id": "FrankCCCCC/cfm-cifar10-32",
            "short_id": "frank_cfm",
            "revision": "b3f30358497e11ce5011c00614c9b0521262f51c",
        },
    ]


def seed_shard_plan(sample_count_per_model: int) -> list[dict[str, Any]]:
    midpoint = int(sample_count_per_model) // 2
    return [
        {"gpu": 0, "seed_start": 0, "seed_end": midpoint, "num_samples": midpoint},
        {"gpu": 1, "seed_start": midpoint, "seed_end": int(sample_count_per_model), "num_samples": int(sample_count_per_model) - midpoint},
    ]


def has_claim_allowed_true(value: Any) -> bool:
    if isinstance(value, dict):
        return any((key == "claim_allowed" and item is True) or has_claim_allowed_true(item) for key, item in value.items())
    if isinstance(value, list):
        return any(has_claim_allowed_true(item) for item in value)
    return False


def archive_has_forbidden_outputs(names: list[str]) -> list[str]:
    offenders: list[str] = []
    lowered = [name.lower() for name in names]
    for name in lowered:
        if "certificate" in name or "undecided_fraction" in name or "metric_reproduction" in name:
            offenders.append(name)
        if name.endswith(".json") and ("result" in name or "evidence" in name) and "package_manifest" not in name:
            offenders.append(name)
    return sorted(set(offenders))


def scan_text_for_private_paths_or_secrets(text: str) -> list[str]:
    issues: list[str] = []
    if "/Users/" in text and "user_provided_local_path_redacted" not in text:
        issues.append("private /Users path leaked")
    if "C:\\Users\\" in text and "user_provided_local_path_redacted" not in text:
        issues.append("private Windows user path leaked")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            issues.append(f"secret-like pattern found: {pattern.pattern}")
    return issues


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(rows: list[dict[str, Any]], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + ("\n" if rows else ""), encoding="utf-8")


def write_zip_json(zf: zipfile.ZipFile, name: str, payload: Any) -> None:
    zf.writestr(name, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def add_text_file(zf: zipfile.ZipFile, name: str, text: str) -> None:
    zf.writestr(name, text)


def add_repo_file(zf: zipfile.ZipFile, src: str | Path, arcname: str) -> None:
    src = Path(src)
    if not src.exists():
        return
    text = src.read_text(encoding="utf-8", errors="ignore")
    issues = scan_text_for_private_paths_or_secrets(text)
    if issues:
        raise ValueError(f"unsafe file for zip {src}: {issues}")
    zf.write(src, arcname)


def safe_extract_zip(
    zip_path: str | Path,
    out_dir: str | Path,
    *,
    limits: ZipSafetyLimits = DEFAULT_ZIP_LIMITS,
) -> list[Path]:
    """Atomically extract a validated ZIP into a new directory.

    Existing output directories are never removed or overwritten. Extraction
    happens in a sibling temporary directory and is renamed only after every
    member has been copied successfully.
    """

    zip_path = Path(zip_path)
    out_dir = Path(out_dir)
    verdict = inspect_zip_safety(zip_path, limits=limits)
    if not verdict["passed"]:
        raise ValueError("unsafe ZIP: " + "; ".join(verdict["errors"]))
    if out_dir.exists():
        raise FileExistsError(f"refusing to overwrite existing extraction directory: {out_dir}")
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    relative_files: list[Path] = []
    with tempfile.TemporaryDirectory(prefix=f".{out_dir.name}.partial-", dir=out_dir.parent) as temp:
        stage = Path(temp) / "payload"
        stage.mkdir(mode=0o700)
        stage_resolved = stage.resolve()
        with zipfile.ZipFile(zip_path, "r") as archive:
            for info in archive.infolist():
                relative = Path(_normalise_zip_name(info.filename))
                target = stage / relative
                try:
                    target.resolve().relative_to(stage_resolved)
                except ValueError as exc:  # pragma: no cover - guarded by inspection too.
                    raise ValueError(f"unsafe ZIP path after resolution: {info.filename}") from exc
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info, "r") as source, target.open("xb") as destination:
                    shutil.copyfileobj(source, destination, length=1024 * 1024)
                os.chmod(target, 0o600)
                relative_files.append(relative)
        os.replace(stage, out_dir)
    return [out_dir / relative for relative in relative_files]


def zip_file_manifest(zip_path: str | Path) -> list[dict[str, Any]]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        rows = []
        for info in zf.infolist():
            if info.is_dir():
                continue
            rows.append(
                {
                    "path": info.filename,
                    "size": info.file_size,
                    "compressed_size": info.compress_size,
                    "crc32": f"{info.CRC:08x}",
                }
            )
        return rows


def write_blocked_summary(*, json_out: str | Path, status_code: str, errors: list[str], zip_path: str | Path | None = None) -> dict[str, Any]:
    payload = {
        "passed": False,
        "status_code": status_code,
        "errors": errors,
        "zip_path": str(zip_path) if zip_path else None,
        "claim_allowed": False,
        "no_fake_results": True,
        "not_paper_evidence": True,
    }
    write_json(payload, json_out)
    return payload


def file_info(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    return {"path": str(path), "size": path.stat().st_size, "sha256": file_sha256(path)}
