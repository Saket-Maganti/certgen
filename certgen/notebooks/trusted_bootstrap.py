"""Stdlib-only authentication gate used before any package import in notebooks.

This module deliberately imports only the Python standard library.  Notebook
generation embeds this file's exact source and its SHA-256; the embedded code
discovers, authenticates, and atomically materializes a package before the
materialized directory is added to ``sys.path``.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


DEFAULT_LIMITS = {
    "maximum_depth": 12,
    "maximum_candidates": 10_000,
    "maximum_package_members": 200_000,
    "maximum_uncompressed_bytes": 20 * 1024**3,
    "maximum_metadata_bytes": 4 * 1024**2,
    "maximum_compression_ratio": 1_000.0,
}
RUNTIME_MARKERS = {".source_sha256", ".certgen_runtime_location.json"}
NESTED_ARCHIVE_SUFFIXES = (
    ".zip",
    ".tar",
    ".tgz",
    ".tar.gz",
    ".tbz",
    ".tbz2",
    ".7z",
    ".rar",
)
EXPECTED_IDENTITY_FIELDS = (
    "expected_package_sha256",
    "expected_scientific_identity_hash",
    "expected_configuration_hash",
    "expected_run_id",
    "expected_study_hash",
    "expected_profile_id",
    "expected_scale",
    "expected_source_code_hash",
    "expected_integrity_manifest",
    "expected_output_schema_version",
)


class AuthenticationError(RuntimeError):
    """The candidate did not satisfy the pre-import authentication contract."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _content_hash(members: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for name, data in sorted(members.items()):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


def _json_object(data: bytes, name: str, maximum_metadata_bytes: int) -> dict:
    if len(data) > maximum_metadata_bytes:
        raise AuthenticationError(f"oversized metadata rejected: {name}")
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuthenticationError(f"invalid JSON metadata: {name}") from exc
    if not isinstance(value, dict):
        raise AuthenticationError(f"metadata is not an object: {name}")
    return value


def _safe_member_name(raw: str) -> str:
    member = PurePosixPath(raw)
    if not raw or member.is_absolute() or ".." in member.parts or "\\" in raw:
        raise AuthenticationError(f"unsafe package member: {raw}")
    return member.as_posix()


def _inspect_zip(path: Path, limits: dict) -> tuple[dict[str, bytes], str]:
    package_sha256 = _sha256_file(path)
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise AuthenticationError(f"unreadable package ZIP: {exc}") from exc
    with archive:
        infos = archive.infolist()
        if len(infos) > limits["maximum_package_members"]:
            raise AuthenticationError("package member-count limit exceeded")
        seen: set[str] = set()
        total = 0
        for info in infos:
            name = _safe_member_name(info.filename)
            key = name.casefold()
            if key in seen:
                raise AuthenticationError(f"duplicate or case-colliding package member: {name}")
            seen.add(key)
            mode = (info.external_attr >> 16) & 0o177777
            file_type = stat.S_IFMT(mode)
            if file_type == stat.S_IFLNK:
                raise AuthenticationError(f"symlink archive entry rejected: {name}")
            if file_type not in {0, stat.S_IFREG, stat.S_IFDIR}:
                raise AuthenticationError(f"hard-link or special archive entry rejected: {name}")
            lowered = name.casefold()
            if not info.is_dir() and lowered.endswith(NESTED_ARCHIVE_SUFFIXES):
                raise AuthenticationError(f"nested archive rejected: {name}")
            total += info.file_size
            if total > limits["maximum_uncompressed_bytes"]:
                raise AuthenticationError("package uncompressed-byte limit exceeded")
            if info.file_size and info.compress_size == 0:
                raise AuthenticationError(f"invalid compressed size: {name}")
            ratio = info.file_size / max(info.compress_size, 1)
            if ratio > limits["maximum_compression_ratio"]:
                raise AuthenticationError(f"compression-ratio limit exceeded: {name}")
        if archive.testzip() is not None:
            raise AuthenticationError("package CRC validation failed")
        members = {
            info.filename: archive.read(info.filename)
            for info in infos
            if not info.is_dir()
        }
    return members, package_sha256


def _inspect_directory(path: Path, limits: dict) -> tuple[dict[str, bytes], str]:
    members: dict[str, bytes] = {}
    total = 0
    for item in sorted(path.rglob("*")):
        relative = item.relative_to(path).as_posix()
        depth = len(PurePosixPath(relative).parts)
        if depth > limits["maximum_depth"]:
            raise AuthenticationError(f"extracted package depth limit exceeded: {relative}")
        if item.is_symlink():
            raise AuthenticationError(f"symlink in extracted package rejected: {relative}")
        try:
            item_stat = item.stat()
        except OSError as exc:
            raise AuthenticationError(f"extracted package entry is unreadable: {relative}") from exc
        if item.is_dir():
            continue
        if not item.is_file() or item_stat.st_nlink != 1:
            raise AuthenticationError(f"hard link or special extracted entry rejected: {relative}")
        if relative in RUNTIME_MARKERS:
            continue
        _safe_member_name(relative)
        if relative.casefold().endswith(NESTED_ARCHIVE_SUFFIXES):
            raise AuthenticationError(f"nested archive rejected: {relative}")
        if len(members) >= limits["maximum_package_members"]:
            raise AuthenticationError("package member-count limit exceeded")
        total += item_stat.st_size
        if total > limits["maximum_uncompressed_bytes"]:
            raise AuthenticationError("package uncompressed-byte limit exceeded")
        members[relative] = item.read_bytes()
    marker = path / ".source_sha256"
    source_sha256 = marker.read_text(encoding="utf-8").strip() if marker.is_file() else ""
    if source_sha256 and (len(source_sha256) != 64 or any(character not in "0123456789abcdef" for character in source_sha256)):
        raise AuthenticationError("invalid extracted-package source SHA-256 marker")
    return members, source_sha256 or _content_hash(members)


def _verify_integrity(members: dict[str, bytes], identity: dict, limits: dict) -> tuple[dict, str]:
    integrity_name = str(identity.get("integrity_manifest") or "")
    if not integrity_name or integrity_name not in members:
        raise AuthenticationError("declared integrity manifest is missing")
    integrity = _json_object(members[integrity_name], integrity_name, limits["maximum_metadata_bytes"])
    if integrity.get("claim_allowed") is not False:
        raise AuthenticationError("integrity manifest must set claim_allowed=false")
    rows = integrity.get("files")
    if not isinstance(rows, list) or not rows:
        raise AuthenticationError("integrity manifest requires non-empty files")
    declared: dict[str, dict] = {}
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise AuthenticationError(f"integrity row {index} is not an object")
        name = _safe_member_name(str(row.get("path") or ""))
        if name in declared:
            raise AuthenticationError(f"duplicate integrity path: {name}")
        declared[name] = row
        data = members.get(name)
        if data is None:
            raise AuthenticationError(f"integrity manifest references absent member: {name}")
        if row.get("size") != len(data) or row.get("sha256") != _sha256_bytes(data):
            raise AuthenticationError(f"integrity size/hash mismatch: {name}")
    actual = set(members) - {integrity_name}
    if set(declared) != actual:
        extra = sorted(actual - set(declared))
        absent = sorted(set(declared) - actual)
        raise AuthenticationError(
            "exact package membership mismatch; unexpected="
            + repr(extra[:20])
            + "; absent="
            + repr(absent[:20])
        )
    return integrity, integrity_name


def _verify_source_inventory(members: dict[str, bytes], limits: dict) -> tuple[str, list[dict]]:
    manifest_data = members.get("bundle_manifest.json")
    if manifest_data is None:
        raise AuthenticationError("bundle manifest is missing")
    manifest = _json_object(manifest_data, "bundle_manifest.json", limits["maximum_metadata_bytes"])
    inventory = manifest.get("source_inventory")
    if not isinstance(inventory, list) or not inventory:
        raise AuthenticationError("source-code inventory is missing")
    digest = hashlib.sha256()
    seen: set[str] = set()
    normalized: list[dict] = []
    for index, row in enumerate(inventory, start=1):
        if not isinstance(row, dict):
            raise AuthenticationError(f"source inventory row {index} is not an object")
        name = _safe_member_name(str(row.get("path") or ""))
        if not name.startswith("certgen/") or not name.endswith(".py") or name in seen:
            raise AuthenticationError(f"invalid or duplicate source inventory path: {name}")
        seen.add(name)
        data = members.get(name)
        if data is None:
            raise AuthenticationError(f"source code absent from package: {name}")
        observed = _sha256_bytes(data)
        if row.get("size") != len(data) or row.get("sha256") != observed:
            raise AuthenticationError(f"source code inventory mismatch: {name}")
        encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
        normalized.append({"path": name, "size": len(data), "sha256": observed})
    actual_sources = {name for name in members if name.startswith("certgen/") and name.endswith(".py")}
    if actual_sources != seen:
        raise AuthenticationError(
            "source-code inventory membership mismatch; unexpected="
            + repr(sorted(actual_sources - seen)[:20])
            + "; absent="
            + repr(sorted(seen - actual_sources)[:20])
        )
    observed_hash = digest.hexdigest()
    if manifest.get("source_code_hash") != observed_hash:
        raise AuthenticationError("source-code inventory aggregate hash mismatch")
    return observed_hash, normalized


def _identity_mismatches(identity: dict, expected: dict, package_sha256: str, source_code_hash: str) -> list[str]:
    mapping = {
        "expected_package_sha256": package_sha256,
        "expected_scientific_identity_hash": identity.get("scientific_identity_hash"),
        "expected_configuration_hash": identity.get("configuration_hash"),
        "expected_run_id": identity.get("run_id"),
        "expected_study_hash": identity.get("study_hash"),
        "expected_profile_id": identity.get("profile_id"),
        "expected_scale": identity.get("scale"),
        "expected_source_code_hash": source_code_hash,
        "expected_integrity_manifest": identity.get("integrity_manifest"),
        "expected_output_schema_version": identity.get("output_schema_version"),
        "expected_package_type": identity.get("package_type"),
        "expected_stage": identity.get("stage"),
    }
    mismatches = []
    for key, observed in mapping.items():
        required = expected.get(key)
        if required is not None and required != observed:
            mismatches.append(f"{key} mismatch: expected={required!r}, observed={observed!r}")
    return mismatches


def authenticate_candidate(path_value: str | os.PathLike, expected: dict, limits: dict | None = None) -> dict:
    """Authenticate all bytes and the exact identity of one ZIP/directory."""

    selected_limits = dict(DEFAULT_LIMITS)
    selected_limits.update(limits or {})
    path = Path(path_value).resolve(strict=False)
    if path.is_symlink():
        raise AuthenticationError("candidate symlink rejected")
    if path.is_file():
        members, package_sha256 = _inspect_zip(path, selected_limits)
        form = "ZIP"
    elif path.is_dir():
        members, package_sha256 = _inspect_directory(path, selected_limits)
        form = "EXTRACTED_DIRECTORY"
    else:
        raise AuthenticationError("candidate is not a package ZIP or extracted directory")
    identity_data = members.get("package_identity.json")
    if identity_data is None:
        raise AuthenticationError("package identity is missing")
    identity = _json_object(
        identity_data,
        "package_identity.json",
        int(selected_limits["maximum_metadata_bytes"]),
    )
    if identity.get("claim_allowed") is not False:
        raise AuthenticationError("package identity must set claim_allowed=false")
    integrity, integrity_name = _verify_integrity(members, identity, selected_limits)
    source_code_hash, source_inventory = _verify_source_inventory(members, selected_limits)
    mismatches = _identity_mismatches(identity, expected, package_sha256, source_code_hash)
    if mismatches:
        raise AuthenticationError("exact expected identity rejected: " + "; ".join(mismatches))
    return {
        "path": str(path),
        "form": form,
        "package_sha256": package_sha256,
        "identity": identity,
        "integrity_manifest": integrity_name,
        "integrity_manifest_sha256": _sha256_bytes(members[integrity_name]),
        "source_code_hash": source_code_hash,
        "source_inventory": source_inventory,
        "member_count": len(members),
        "uncompressed_bytes": sum(len(data) for data in members.values()),
        "claim_allowed": False,
    }


def _candidate_paths(search_roots: list[str | os.PathLike], limits: dict) -> list[Path]:
    candidates: list[Path] = []
    skipped = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
    for root_value in search_roots:
        root = Path(root_value).resolve(strict=False)
        if not root.exists() or root.is_symlink():
            continue
        for current, directories, filenames in os.walk(root, topdown=True, followlinks=False):
            current_path = Path(current)
            depth = len(current_path.relative_to(root).parts)
            directories[:] = sorted(
                name
                for name in directories
                if depth < limits["maximum_depth"]
                and name not in skipped
                and not (current_path / name).is_symlink()
            )
            if "package_identity.json" in filenames and ".certgen_runtime_location.json" not in filenames:
                candidates.append(current_path)
            candidates.extend(
                current_path / name
                for name in sorted(filenames)
                if name.casefold().endswith(".zip") and not (current_path / name).is_symlink()
            )
            if len(candidates) > limits["maximum_candidates"]:
                raise AuthenticationError("bootstrap discovery candidate-count limit exceeded")
    return sorted(set(candidates), key=lambda value: str(value).casefold())


def discover_authenticated_package(
    search_roots: list[str | os.PathLike], expected: dict, limits: dict | None = None
) -> dict:
    """Select an exact authenticated package, deduplicating byte-identical copies."""

    selected_limits = dict(DEFAULT_LIMITS)
    selected_limits.update(limits or {})
    candidates = _candidate_paths(search_roots, selected_limits)
    accepted: list[dict] = []
    rejected: list[dict] = []
    for path in candidates:
        try:
            accepted.append(authenticate_candidate(path, expected, selected_limits))
        except (AuthenticationError, OSError) as exc:
            rejected.append({"path": str(path), "error": str(exc)})
    if not accepted:
        raise AuthenticationError(
            "NO_MATCHING_PACKAGE; expected=" + json.dumps(expected, sort_keys=True) + "; rejected=" + json.dumps(rejected, sort_keys=True)
        )
    by_hash: dict[str, list[dict]] = {}
    for row in accepted:
        by_hash.setdefault(str(row["package_sha256"]), []).append(row)
    if len(by_hash) != 1:
        raise AuthenticationError(
            "AMBIGUOUS_DIFFERENT_CONTENT; matches="
            + json.dumps([{"path": row["path"], "sha256": row["package_sha256"]} for row in accepted], sort_keys=True)
        )
    selected = sorted(accepted, key=lambda row: str(row["path"]).casefold())[0]
    selected["selection_status"] = (
        "DUPLICATE_IDENTICAL_COPY_DEDUPED" if len(accepted) > 1 else "SELECTED_UNIQUE_VALID_PACKAGE"
    )
    selected["duplicate_paths"] = [row["path"] for row in sorted(accepted, key=lambda row: str(row["path"]).casefold())]
    selected["candidate_count"] = len(candidates)
    selected["rejected_candidates"] = rejected
    return selected


def materialize_authenticated_package(authentication: dict, destination_value: str | os.PathLike) -> Path:
    """Atomically materialize a previously authenticated package and reauthenticate it."""

    source = Path(str(authentication["path"]))
    destination = Path(destination_value)
    expected = {
        "expected_package_sha256": authentication["package_sha256"],
        "expected_scientific_identity_hash": authentication["identity"].get("scientific_identity_hash"),
        "expected_configuration_hash": authentication["identity"].get("configuration_hash"),
        "expected_run_id": authentication["identity"].get("run_id"),
        "expected_study_hash": authentication["identity"].get("study_hash"),
        "expected_profile_id": authentication["identity"].get("profile_id"),
        "expected_scale": authentication["identity"].get("scale"),
        "expected_source_code_hash": authentication["source_code_hash"],
        "expected_integrity_manifest": authentication["integrity_manifest"],
        "expected_output_schema_version": authentication["identity"].get("output_schema_version"),
        "expected_package_type": authentication["identity"].get("package_type"),
        "expected_stage": authentication["identity"].get("stage"),
    }
    if authentication["form"] == "EXTRACTED_DIRECTORY":
        authenticate_candidate(source, expected)
        return source
    if destination.exists():
        marker = destination / ".source_sha256"
        if destination.is_dir() and marker.is_file() and marker.read_text(encoding="utf-8").strip() == authentication["package_sha256"]:
            directory_expected = {**expected, "expected_package_sha256": None}
            authenticated_directory = authenticate_candidate(destination, directory_expected)
            if authenticated_directory["identity"].get("scientific_identity_hash") == expected["expected_scientific_identity_hash"]:
                return destination
        raise FileExistsError("materialization destination contains a different or unauthenticated package")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = Path(tempfile.mkdtemp(prefix=f".{destination.name}.partial-", dir=destination.parent))
    try:
        with zipfile.ZipFile(source) as archive:
            for info in archive.infolist():
                target = partial.joinpath(*PurePosixPath(info.filename).parts)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source_handle, target.open("xb") as target_handle:
                    shutil.copyfileobj(source_handle, target_handle, 1024 * 1024)
        (partial / ".source_sha256").write_text(str(authentication["package_sha256"]) + "\n", encoding="utf-8")
        directory_expected = {**expected, "expected_package_sha256": None}
        authenticate_candidate(partial, directory_expected)
        os.replace(partial, destination)
    except Exception:
        shutil.rmtree(partial, ignore_errors=True)
        raise
    runtime = {
        "schema_version": "certgen.runtime_location.v2",
        "source_form": authentication["form"],
        "source_sha256": authentication["package_sha256"],
        "scientific_identity_hash": authentication["identity"].get("scientific_identity_hash"),
        "source_code_hash": authentication["source_code_hash"],
        "claim_allowed": False,
    }
    (destination / ".certgen_runtime_location.json").write_text(
        json.dumps(runtime, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return destination


def authenticate_discover_materialize(
    search_roots: list[str | os.PathLike], expected: dict, destination: str | os.PathLike
) -> tuple[Path, dict]:
    authentication = discover_authenticated_package(search_roots, expected)
    root = materialize_authenticated_package(authentication, destination)
    return root, authentication
