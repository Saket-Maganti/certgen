"""V9 CIFAR-10 reference super-onramp.

This module searches local user-provided roots and reports whether CertGen can
materialize CIFAR-10 reference samples. It never downloads by default.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tarfile
import tempfile
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

from certgen.core.io import write_json


CLASS_NAMES = {
    "airplane",
    "automobile",
    "bird",
    "cat",
    "deer",
    "dog",
    "frog",
    "horse",
    "ship",
    "truck",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".ppm", ".bmp"}
OFFICIAL_URL = "https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz"
OFFICIAL_MD5 = "c58f30108f718f92721af3b95e74349a"
EXPECTED_BATCH_FILES = {*(f"data_batch_{idx}" for idx in range(1, 6)), "test_batch"}
MAX_TAR_MEMBERS = 64
MAX_TAR_UNCOMPRESSED_BYTES = 256 * 1024**2


@dataclass(frozen=True)
class Candidate:
    path: str
    layout: str
    accepted: bool
    reason: str
    counts: dict[str, int]


def _count_images(root: Path) -> int:
    return sum(1 for path in root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)


def _md5(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inspect_official_tarball(path: Path) -> list[str]:
    errors: list[str] = []
    if _md5(path) != OFFICIAL_MD5:
        return [f"official archive MD5 mismatch; expected {OFFICIAL_MD5}"]
    try:
        with tarfile.open(path, "r:gz") as archive:
            members = archive.getmembers()
            if len(members) > MAX_TAR_MEMBERS:
                errors.append(f"archive member count {len(members)} exceeds {MAX_TAR_MEMBERS}")
            total = 0
            names: set[str] = set()
            for member in members:
                pure = PurePosixPath(member.name)
                if pure.is_absolute() or ".." in pure.parts or "\\" in member.name:
                    errors.append(f"unsafe archive member path: {member.name}")
                    continue
                if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                    errors.append(f"unsafe archive member type: {member.name}")
                if not (member.isdir() or member.isfile()):
                    errors.append(f"unsupported archive member type: {member.name}")
                total += max(0, member.size)
                if pure.parts and pure.parts[0] == "cifar-10-batches-py":
                    names.add(pure.name)
            if total > MAX_TAR_UNCOMPRESSED_BYTES:
                errors.append(f"archive uncompressed size {total} exceeds {MAX_TAR_UNCOMPRESSED_BYTES}")
            missing = sorted(EXPECTED_BATCH_FILES - names)
            if missing:
                errors.append("official archive is missing batches: " + ", ".join(missing))
    except (OSError, tarfile.TarError) as exc:
        errors.append(f"invalid official archive: {exc}")
    return errors


def _validate_image_tree(path: Path) -> tuple[bool, str, dict[str, int]]:
    split_counts: dict[str, int] = {}
    for split, expected in [("test", 10_000), ("train", 50_000)]:
        split_root = path / split
        if not split_root.is_dir():
            continue
        class_names = {child.name.lower() for child in split_root.iterdir() if child.is_dir()}
        if class_names != CLASS_NAMES:
            missing = sorted(CLASS_NAMES - class_names)
            extra = sorted(class_names - CLASS_NAMES)
            return False, f"{split} class directories invalid; missing={missing}, extra={extra}", split_counts
        count = _count_images(split_root)
        split_counts[split] = count
        if count != expected:
            return False, f"{split} image count must be {expected}, found {count}", split_counts
    if split_counts:
        return True, "complete CIFAR split tree detected", split_counts
    class_dirs = {child.name.lower() for child in path.iterdir() if child.is_dir()}
    if class_dirs & CLASS_NAMES:
        if class_dirs != CLASS_NAMES:
            return False, "class-folder root must contain all ten CIFAR-10 classes", {"class_dirs": len(class_dirs & CLASS_NAMES)}
        count = _count_images(path)
        if count not in {10_000, 50_000, 60_000}:
            return False, f"class-folder image count must be 10000, 50000, or 60000; found {count}", {"image_files": count}
        return True, "complete CIFAR class-folder tree detected", {"class_dirs": 10, "image_files": count}
    return False, "no complete CIFAR image split/class tree detected", {}


def _detect_candidate(path: Path) -> Candidate:
    if not path.exists():
        return Candidate(str(path), "missing", False, "path does not exist", {})
    if path.is_file() and path.name == "cifar-10-python.tar.gz":
        errors = _inspect_official_tarball(path)
        return Candidate(
            str(path),
            "official_cifar_tarball",
            not errors,
            "official tarball hash and member contract passed" if not errors else "; ".join(errors),
            {"tarball": 1},
        )
    if path.is_file():
        return Candidate(str(path), "unsupported_file", False, "not a CIFAR directory/archive root", {})
    try:
        children = list(path.iterdir())
    except OSError as exc:
        return Candidate(
            str(path),
            "inaccessible_directory",
            False,
            f"directory could not be inspected: {type(exc).__name__}: {exc}",
            {},
        )
    names = {child.name for child in children}
    batch_files = [f"data_batch_{idx}" for idx in range(1, 6)]
    if set(batch_files).issubset(names) and "test_batch" in names:
        return Candidate(str(path), "official_cifar_10_batches_py", True, "official extracted Python batch archive", {"batch_files": 6})
    if (path / "cifar-10-batches-py").is_dir():
        return _detect_candidate(path / "cifar-10-batches-py")
    if (path / "cifar-10-python.tar.gz").is_file():
        return _detect_candidate(path / "cifar-10-python.tar.gz")
    tree_ok, tree_reason, tree_counts = _validate_image_tree(path)
    if tree_ok:
        layout = "image_folder_split_tree" if "test" in tree_counts or "train" in tree_counts else "image_folder_class_tree"
        return Candidate(str(path), layout, True, tree_reason, tree_counts)
    if any((path / split).exists() for split in ["train", "test"]) or any(
        child.is_dir() and child.name.lower() in CLASS_NAMES for child in children
    ):
        return Candidate(str(path), "incomplete_image_tree", False, tree_reason, tree_counts)
    manifests = [path / "registry/manifests/cifar10_r1_reference.jsonl", path / "cifar10_r1_reference.jsonl", path / "manifest.jsonl"]
    stale = [manifest for manifest in manifests if manifest.exists()]
    if stale:
        rows = sum(1 for line in stale[0].read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip())
        return Candidate(str(stale[0]), "stale_or_incomplete_manifest", False, f"manifest exists but is not a materialization root; rows={rows}", {"manifest_rows": rows})
    return Candidate(str(path), "unsupported_directory", False, "no official archive, torchvision root, or CIFAR image tree detected", {})


def _expand_roots(roots: list[str]) -> list[Path]:
    expanded: list[Path] = []
    for root in roots:
        path = Path(root).expanduser()
        expanded.append(path)
        if path.exists() and path.is_dir():
            try:
                expanded.extend(child for child in path.iterdir() if child.is_dir())
            except OSError:
                # The root itself remains in the result and will receive a
                # precise inaccessible-directory rejection from the detector.
                pass
    seen: set[str] = set()
    result: list[Path] = []
    for path in expanded:
        key = str(path)
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def explain_text() -> str:
    return """Accepted CIFAR-10 reference structures:

1. Official extracted archive:
   <root>/cifar-10-batches-py/data_batch_1 ... data_batch_5, test_batch
2. Archive directory itself:
   <root>/data_batch_1 ... data_batch_5, test_batch
3. Image folder:
   <root>/test/<class>/*.png or .ppm, optionally train/<class>/*
4. Class folder:
   <root>/<airplane|automobile|...>/*.png or .ppm
5. User-provided ZIP/TAR wrapper:
   a path-safe, resource-bounded container holding the official Python batches
   or the hash-verified official cifar-10-python.tar.gz

No download is performed unless --execute-download is explicitly passed.
"""


def _report_path(value: str) -> str:
    """Redact the local home prefix from release-facing Markdown reports."""

    home = str(Path.home())
    return value.replace(home, "$HOME")


def build_download_plan(download_dir: str | Path) -> dict[str, Any]:
    download_dir = Path(download_dir)
    return {
        "status_code": "DOWNLOAD_PLAN_ONLY",
        "url": OFFICIAL_URL,
        "expected_md5": OFFICIAL_MD5,
        "download_dir": str(download_dir),
        "archive_path": str(download_dir / "cifar-10-python.tar.gz"),
        "extract_dir": str(download_dir),
        "execute_download_required": True,
        "claim_allowed": False,
        "no_fake_results": True,
        "not_paper_evidence": True,
    }


def execute_download(plan: dict[str, Any]) -> None:
    target = Path(str(plan["archive_path"]))
    extract_dir = Path(str(plan["extract_dir"]))
    extracted_target = extract_dir / "cifar-10-batches-py"
    if target.exists():
        raise FileExistsError(f"refusing to overwrite existing CIFAR archive: {target}")
    if extracted_target.exists():
        raise FileExistsError(f"refusing to overwrite existing CIFAR directory: {extracted_target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.partial")
    urllib.request.urlretrieve(str(plan["url"]), temporary)  # pragma: no cover - explicit opt-in only.
    errors = _inspect_official_tarball(temporary)
    if errors:
        temporary.unlink(missing_ok=True)
        raise ValueError("downloaded CIFAR archive failed validation: " + "; ".join(errors))
    os.replace(temporary, target)
    extract_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cifar-extract-", dir=extract_dir) as temp:
        stage = Path(temp) / "cifar-10-batches-py"
        stage.mkdir()
        with tarfile.open(target, "r:gz") as archive:
            for member in archive.getmembers():
                pure = PurePosixPath(member.name)
                if not member.isfile() or not pure.parts or pure.parts[0] != "cifar-10-batches-py":
                    continue
                relative = Path(*pure.parts[1:])
                if not relative.parts:
                    continue
                destination = stage / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise ValueError(f"unable to read archive member: {member.name}")
                with source, destination.open("xb") as handle:
                    shutil.copyfileobj(source, handle, length=1024 * 1024)
        os.replace(stage, extracted_target)


def run_onramp(
    *,
    search_roots: list[str],
    out_json: str | Path = "data/results/v9_cifar_reference_onramp.json",
    out_report: str | Path = "docs/V9_CIFAR_REFERENCE_SUPER_ONRAMP.md",
    explain: bool = False,
    download_plan: bool = False,
    download_dir: str | Path = "data/sources",
    execute_download_flag: bool = False,
) -> dict[str, Any]:
    roots = search_roots or ["data/sources", "."]
    candidates = [_detect_candidate(path) for path in _expand_roots(roots)]
    accepted = [candidate for candidate in candidates if candidate.accepted]
    plan = build_download_plan(download_dir) if download_plan or execute_download_flag else None
    if execute_download_flag:
        if plan is None:
            plan = build_download_plan(download_dir)
        execute_download(plan)
    best = accepted[0] if accepted else None
    status_code = "READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION" if best else "BLOCKED_USER_MUST_PROVIDE_CIFAR_REFERENCE"
    exact_next_command = (
        f"CIFAR_ROOT={best.path} commands/v6_cpu_execution/01_materialize_reference_from_local_root.sh"
        if best and best.layout != "official_cifar_tarball"
        else (
            f"CIFAR_ARCHIVE_ROOT={Path(best.path).parent if best else '<path-to-cifar-10-batches-py-or-parent>'} "
            "commands/v6_cpu_execution/01b_materialize_reference_from_official_archive.sh"
            if best
            else "Provide CIFAR_ROOT or CIFAR_ARCHIVE_ROOT, then rerun commands/v9_cpu_execution/01_cifar_reference_super_onramp.sh"
        )
    )
    payload = {
        "status_code": status_code,
        "detected_paths": [asdict(candidate) for candidate in accepted],
        "rejected_paths": [asdict(candidate) for candidate in candidates if not candidate.accepted],
        "exact_next_command": exact_next_command,
        "license_status": "license_unknown_reference_only",
        "count_expectations": {"cifar10_test": 10000, "cifar10_train": 50000},
        "materialization_can_proceed": bool(best),
        "explain": explain_text() if explain else None,
        "download_plan": plan,
        "claim_allowed": False,
        "no_fake_results": True,
        "not_paper_evidence": True,
    }
    write_json(payload, out_json)
    lines = [
        "# V9 CIFAR Reference Super-Onramp",
        "",
        "`NO_FAKE_RESULTS`",
        "`NO_REAL_EVIDENCE`",
        "`not paper evidence`",
        "",
        f"Status: `{status_code}`",
        "Claim allowed: `false`",
        "",
        "## Exact Next Command",
        "",
        f"`{exact_next_command}`",
        "",
        "## Detected Paths",
    ]
    lines.extend(
        f"- `{_report_path(item.path)}` ({item.layout}): {_report_path(item.reason)}"
        for item in accepted or []
    )
    if not accepted:
        lines.append("- none")
    lines.extend(["", "## Rejected Paths"])
    lines.extend(
        f"- `{_report_path(item.path)}` ({item.layout}): {_report_path(item.reason)}"
        for item in candidates
        if not item.accepted
    )
    lines.extend(["", "## Accepted Structures", "", explain_text()])
    Path(out_report).parent.mkdir(parents=True, exist_ok=True)
    Path(out_report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V9 CIFAR reference super-onramp.")
    parser.add_argument("--search-root", action="append", default=[])
    parser.add_argument("--out-json", default="data/results/v9_cifar_reference_onramp.json")
    parser.add_argument("--out-report", default="docs/V9_CIFAR_REFERENCE_SUPER_ONRAMP.md")
    parser.add_argument("--explain", action="store_true")
    parser.add_argument("--download-plan", action="store_true")
    parser.add_argument("--download-dir", default="data/sources")
    parser.add_argument("--execute-download", action="store_true")
    args = parser.parse_args(argv)
    payload = run_onramp(
        search_roots=args.search_root,
        out_json=args.out_json,
        out_report=args.out_report,
        explain=args.explain,
        download_plan=args.download_plan,
        download_dir=args.download_dir,
        execute_download_flag=args.execute_download,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["materialization_can_proceed"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
