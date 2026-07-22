"""Deterministic clean source/reproducibility archive builder and verifier."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from certgen.cvpr.contracts import atomic_write_json


EXCLUDED_PARTS = {
    ".git",
    "__MACOSX",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "quarantine",
    "ade20k_root",
    "ade20kdataset",
    "model_cache",
    "snapshots",
    "weights",
}
EXCLUDED_NAMES = {".DS_Store"}
EXCLUDED_SUFFIXES = {
    ".aux",
    ".fdb_latexmk",
    ".fls",
    ".log",
    ".out",
    ".pdf",
    ".pyc",
    ".pyo",
    ".synctex.gz",
    ".toc",
    ".bin",
    ".ckpt",
    ".msgpack",
    ".onnx",
    ".pt",
    ".pth",
    ".safetensors",
}
ROOT_FILES = (
    "README.md",
    "LICENSE",
    "CITATION.cff",
    "pyproject.toml",
    ".gitignore",
    "Makefile",
    "CERTGEN_CVPR_FINAL_RUNTIME_HARDENING_REPORT.md",
    "CERTGEN_CVPR_FINAL_EXECUTION_HANDBOOK.md",
    "CERTGEN_CVPR_REAL_EXECUTION_CLOSURE_REPORT.md",
    "CERTGEN_CVPR_RUN_READY_EXECUTION_HANDBOOK.md",
    "CERTGEN_CVPR_FINAL_RUN_READY_CLOSURE_REPORT.md",
    "CERTGEN_CVPR_FINAL_RUN_READY_EXECUTION_HANDBOOK.md",
    "CERTGEN_CVPR_100_PERCENT_PRE_RUN_READINESS_REPORT.md",
    "CERTGEN_CVPR_100_PERCENT_PRE_RUN_EXECUTION_HANDBOOK.md",
    "CERTGEN_MAX_CEILING_PRE_RUN_READINESS_REPORT.md",
    "CERTGEN_MAX_CEILING_EXECUTION_HANDBOOK.md",
    "CERTGEN_MAX_CEILING_SINGLE_FILE_HANDOFF.md",
    "CERTGEN_CURRENT_NEXT_ACTION.md",
    "CERTGEN_KAGGLE_RUN_LAUNCHBOARD.md",
    "CERTGEN_KAGGLE_UNIVERSAL_ACCOUNT_HANDBOOK.md",
    "CERTGEN_KAGGLE_DEPENDENCY_AND_ASSET_GUIDE.md",
    "KAGGLE_ASSET_SETUP.md",
)
SOURCE_ROOTS = (
    "certgen", "tests", "configs", "docs", "paper", "release", "schemas", "requirements", "scripts"
)
REPORT_FILES = (
    "reports/CERTGEN_FINAL_RUN_READY_BASELINE.md",
    "reports/CERTGEN_FINAL_RUN_READY_COMMAND_LEDGER.csv",
    "reports/CERTGEN_FINAL_RUN_READY_CURRENT_STATE.json",
    "reports/CERTGEN_FINAL_RUN_READY_REPAIR_CHANGELOG.md",
    "reports/CERTGEN_FINAL_RUN_READY_TEST_MATRIX.md",
    "reports/CERTGEN_FINAL_RUN_READY_NOTEBOOK_READINESS.md",
    "reports/CERTGEN_FINAL_RUN_READY_HANDOFF_AUDIT.md",
    "reports/CERTGEN_ADAPTER_CONFORMANCE_MATRIX.csv",
    "reports/CERTGEN_FINAL_HARDENING_BASELINE.md",
    "reports/CERTGEN_FINAL_HARDENING_COMMAND_LEDGER.csv",
    "reports/CERTGEN_FINAL_HARDENING_CURRENT_STATE.json",
    "reports/CERTGEN_FINAL_HARDENING_REPAIR_CHANGELOG.md",
    "reports/CERTGEN_FINAL_HARDENING_TEST_MATRIX.md",
    "reports/CERTGEN_FINAL_HARDENING_NOTEBOOK_READINESS.md",
    "reports/CERTGEN_REAL_EXECUTION_CLOSURE_BASELINE.md",
    "reports/CERTGEN_REAL_EXECUTION_CLOSURE_COMMAND_LEDGER.csv",
    "reports/CERTGEN_REAL_EXECUTION_CLOSURE_CURRENT_STATE.json",
    "reports/CERTGEN_REAL_EXECUTION_CLOSURE_REPAIR_CHANGELOG.md",
    "reports/CERTGEN_REAL_EXECUTION_CLOSURE_TEST_MATRIX.md",
    "reports/CERTGEN_REAL_EXECUTION_CLOSURE_NOTEBOOK_READINESS.md",
    "reports/CERTGEN_REAL_EXECUTION_CLOSURE_ARCHIVE_AUDIT.md",
    "reports/CERTGEN_REAL_EXECUTION_CLOSURE_HANDOFF_AUDIT.md",
    "reports/CERTGEN_FINAL_100_PERCENT_BASELINE.md",
    "reports/CERTGEN_FINAL_100_PERCENT_COMMAND_LEDGER.csv",
    "reports/CERTGEN_FINAL_100_PERCENT_CURRENT_STATE.json",
    "reports/CERTGEN_FINAL_100_PERCENT_REPAIR_CHANGELOG.md",
    "reports/CERTGEN_FINAL_100_PERCENT_TEST_MATRIX.md",
    "reports/CERTGEN_FINAL_100_PERCENT_HANDOFF_AUDIT.md",
    "reports/CERTGEN_FINAL_100_PERCENT_NOTEBOOK_READINESS.md",
    "reports/CERTGEN_OPERATIONAL_HYPOTHESIS_COVERAGE.csv",
    "reports/CERTGEN_REPLACEMENT_AUDIT.md",
    "reports/CERTGEN_REPLACEMENT_AUDIT.json",
    "reports/CERTGEN_MAX_CEILING_BASELINE.md",
    "reports/CERTGEN_MAX_CEILING_COMMAND_LEDGER.csv",
    "reports/CERTGEN_MAX_CEILING_CURRENT_STATE.json",
    "reports/CERTGEN_MAX_CEILING_REPAIR_AND_UPGRADE_CHANGELOG.md",
    "reports/CERTGEN_MAX_CEILING_TEST_MATRIX.md",
    "reports/CERTGEN_MAX_CEILING_NOTEBOOK_READINESS.md",
    "reports/CERTGEN_FAILURE_INJECTION_MATRIX.csv",
    "reports/CERTGEN_SENSITIVITY_MATRIX.csv",
    "reports/CERTGEN_CLAIM_EVIDENCE_MATRIX.csv",
    "reports/CERTGEN_FINAL_EXECUTION_PATH_BASELINE.md",
    "reports/CERTGEN_FINAL_EXECUTION_PATH_CURRENT_STATE.json",
    "reports/CERTGEN_FINAL_EXECUTION_PATH_COMMAND_LEDGER.csv",
    "reports/CERTGEN_FINAL_EXECUTION_PATH_COMMAND_LEDGER.jsonl",
    "reports/CERTGEN_FINAL_EXECUTION_PATH_ARTIFACT_INVENTORY.csv",
    "reports/CERTGEN_PREIMPORT_AUTHENTICATION_AUDIT.md",
    "reports/CERTGEN_EXPECTED_IDENTITY_BINDING_AUDIT.md",
    "reports/CERTGEN_LOCAL_RESUME_IDENTITY_AUDIT.md",
    "reports/CERTGEN_ASSET_RESOLUTION_AUDIT.md",
    "reports/CERTGEN_WHEELHOUSE_COMPATIBILITY_AUDIT.md",
    "reports/CERTGEN_FINAL_DEPENDENCY_CLOSURE_MATRIX.csv",
    "reports/CERTGEN_FINAL_DEPENDENCY_CLOSURE_REPORT.md",
    "reports/CERTGEN_FOUR_ACCOUNT_EXECUTION_PATH_MATRIX.csv",
    "reports/CERTGEN_FOUR_ACCOUNT_EXECUTION_PATH_REPORT.md",
    "reports/CERTGEN_FINAL_PACKAGE_SECURITY_AUDIT.md",
    "reports/CERTGEN_FINAL_KAGGLE_EXECUTION_PATH_AUDIT.md",
)
CANONICAL_NOTEBOOKS = (
    "certgen_kaggle_environment_diagnostic_t4x2.ipynb",
    "certgen_cvpr_checkpoint_preflight_t4x2.ipynb",
    "certgen_cvpr_cifar10_generation_t4x2_1k.ipynb",
    "certgen_cvpr_generation_t4x2_generic.ipynb",
    "certgen_cvpr_feature_extraction_t4x2_1k.ipynb",
    "certgen_cvpr_feature_extraction_t4x2_generic.ipynb",
    "certgen_cvpr_generation_1k_t4x2.ipynb",
    "certgen_cvpr_feature_extraction_t4x2.ipynb",
)
BUNDLE_FILES = (
    "artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip",
    "artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip.manifest.json",
    "artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip.sha256",
    "artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip",
    "artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip.manifest.json",
    "artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip.sha256",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    return (
        path.is_file()
        and not path.is_symlink()
        and not any(part in EXCLUDED_PARTS for part in relative.parts)
        and path.name not in EXCLUDED_NAMES
        and path.suffix not in EXCLUDED_SUFFIXES
        and path.stat().st_size <= 50 * 1024 * 1024
    )


def archive_members(root: str | Path = ".") -> list[Path]:
    base = Path(root).resolve()
    candidates: list[Path] = []
    for name in ROOT_FILES:
        path = base / name
        if path.is_file():
            candidates.append(path)
    for name in REPORT_FILES:
        path = base / name
        if path.is_file():
            candidates.append(path)
    for name in SOURCE_ROOTS:
        source = base / name
        if source.is_dir():
            candidates.extend(path for path in source.rglob("*") if _safe(path, base))
    registry = base / "registry" / "cvpr"
    if registry.is_dir():
        candidates.extend(path for path in registry.rglob("*") if _safe(path, base))
    for name in CANONICAL_NOTEBOOKS:
        path = base / "notebooks" / "kaggle" / name
        if path.is_file():
            candidates.append(path)
    for name in BUNDLE_FILES:
        path = base / name
        if path.is_file():
            candidates.append(path)
    return sorted(set(candidates), key=lambda path: path.relative_to(base).as_posix())


def _write_member(archive: zipfile.ZipFile, name: str, data: bytes) -> None:
    posix = PurePosixPath(name)
    if posix.is_absolute() or ".." in posix.parts:
        raise ValueError(f"unsafe archive member: {name}")
    info = zipfile.ZipInfo(posix.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def _verify_names(names: Iterable[str]) -> list[str]:
    errors: list[str] = []
    names_set = set(names)
    for name in names_set:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or any(part in EXCLUDED_PARTS for part in path.parts):
            errors.append(f"forbidden member: {name}")
        if path.name in EXCLUDED_NAMES or path.suffix in EXCLUDED_SUFFIXES:
            errors.append(f"forbidden metadata: {name}")
    required = {
        "README.md",
        "LICENSE",
        "CITATION.cff",
        "pyproject.toml",
        "certgen/__init__.py",
        "tests/test_imports.py",
        "CERTGEN_CVPR_FINAL_RUN_READY_CLOSURE_REPORT.md",
        "CERTGEN_CVPR_FINAL_RUN_READY_EXECUTION_HANDBOOK.md",
        "CERTGEN_CVPR_100_PERCENT_PRE_RUN_READINESS_REPORT.md",
        "CERTGEN_CVPR_100_PERCENT_PRE_RUN_EXECUTION_HANDBOOK.md",
        "CERTGEN_MAX_CEILING_PRE_RUN_READINESS_REPORT.md",
        "CERTGEN_MAX_CEILING_EXECUTION_HANDBOOK.md",
        "CERTGEN_MAX_CEILING_SINGLE_FILE_HANDOFF.md",
        "schemas/cvpr/image_manifest.schema.json",
        "release/CERTGEN_PORTABLE_TEST_MANIFEST.json",
        *REPORT_FILES,
        *BUNDLE_FILES,
    }
    errors.extend(f"missing required member: {name}" for name in sorted(required - names_set))
    errors.extend(
        f"missing canonical notebook path: notebooks/kaggle/{name}"
        for name in CANONICAL_NOTEBOOKS
        if f"notebooks/kaggle/{name}" not in names_set
    )
    return errors


def _privacy_errors(extracted: Path, names: Iterable[str]) -> list[str]:
    """Reject private absolute paths in user-facing release text."""

    errors: list[str] = []
    for name in names:
        path = PurePosixPath(name)
        user_facing = name in ROOT_FILES or path.parts[:1] in {("docs",), ("reports",)}
        if not user_facing or path.suffix.lower() not in {".md", ".csv", ".json", ".yaml", ".yml", ".txt"}:
            continue
        try:
            text = (extracted / name).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "/Users/" in text or "C:\\Users\\" in text:
            errors.append(f"private absolute path in user-facing file: {name}")
    return errors


def build_archive(
    *,
    output: str | Path,
    root: str | Path = ".",
    run_tests: bool = True,
) -> dict[str, Any]:
    verification_started_at_utc = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    verification_started = time.monotonic()
    base = Path(root).resolve()
    target = Path(output).resolve()
    if target.exists():
        raise FileExistsError(f"refusing to overwrite archive: {target}")
    members = archive_members(base)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    with zipfile.ZipFile(target, "x") as archive:
        for path in members:
            name = path.relative_to(base).as_posix()
            data = path.read_bytes()
            _write_member(archive, name, data)
            rows.append({"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        manifest_bytes = (json.dumps({"files": rows, "claim_allowed": False}, indent=2, sort_keys=True) + "\n").encode()
        _write_member(archive, "release/archive_manifest.json", manifest_bytes)

    with tempfile.TemporaryDirectory(prefix="certgen_archive_verify_") as temporary:
        extracted = Path(temporary)
        with zipfile.ZipFile(target) as archive:
            names = archive.namelist()
            errors = _verify_names(names)
            archive.extractall(extracted)
        errors.extend(_privacy_errors(extracted, names))
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        import_check = subprocess.run(
            [sys.executable, "-c", "import certgen; print(certgen.__version__)"],
            cwd=extracted,
            env=environment,
            capture_output=True,
            text=True,
        )
        if import_check.returncode != 0:
            errors.append("portable package import failed: " + import_check.stderr.strip())
        test_result: dict[str, Any] = {"run": False, "returncode": None, "summary": "not requested"}
        notebook_result: dict[str, Any] = {"run": False, "returncode": None, "summary": "not requested"}
        synthetic_result: dict[str, Any] = {"run": False, "returncode": None, "summary": "not requested"}
        if run_tests and not errors:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "tests/test_archive_portable.py",
                    "tests/test_real_execution_closure.py",
                    "tests/test_final_execution_path_seal.py",
                    "tests/test_universal_kaggle_discovery.py",
                    "tests/test_phase1_closure.py",
                ],
                cwd=extracted,
                env=environment,
                capture_output=True,
                text=True,
                timeout=300,
            )
            summary = completed.stdout.strip().splitlines()[-1] if completed.stdout.strip() else completed.stderr.strip()
            test_result = {"run": True, "returncode": completed.returncode, "summary": summary}
            if completed.returncode != 0:
                errors.append("portable non-Git test lane failed: " + summary)
            notebook = subprocess.run(
                [sys.executable, "-m", "certgen", "audit", "notebooks"],
                cwd=extracted,
                env=environment,
                capture_output=True,
                text=True,
                timeout=120,
            )
            notebook_result = {"run": True, "returncode": notebook.returncode, "summary": notebook.stdout.strip()[-2000:]}
            if notebook.returncode != 0:
                errors.append("portable notebook static audit failed")
            synthetic = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from certgen.cvpr.builder_faithful import run_builder_faithful_synthetic; "
                        "import json; "
                        "print(json.dumps(run_builder_faithful_synthetic('.portable_builder_rehearsal'), sort_keys=True))"
                    ),
                ],
                cwd=extracted,
                env=environment,
                capture_output=True,
                text=True,
                timeout=300,
            )
            synthetic_result = {"run": True, "returncode": synthetic.returncode, "summary": synthetic.stdout.strip()[-2000:]}
            if synthetic.returncode != 0:
                errors.append("portable synthetic real-contract run failed")
    verification_completed_at_utc = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    payload = {
        "schema_version": "certgen.clean_archive.v1",
        "status": "ARCHIVE_VERIFIED" if not errors else "ARCHIVE_VERIFICATION_FAILED",
        "archive": str(target),
        "archive_sha256": _sha256(target),
        "member_count": len(rows) + 1,
        "manifest": rows,
        "errors": errors,
        "import_check": import_check.returncode,
        "portable_tests": test_result,
        "portable_notebook_audit": notebook_result,
        "portable_synthetic_runtime": synthetic_result,
        "required_files": sorted({
            "README.md", "LICENSE", "CITATION.cff", "pyproject.toml",
            "CERTGEN_MAX_CEILING_PRE_RUN_READINESS_REPORT.md",
            "CERTGEN_MAX_CEILING_EXECUTION_HANDBOOK.md",
            "CERTGEN_MAX_CEILING_SINGLE_FILE_HANDOFF.md",
        }),
        "forbidden_files": sorted(EXCLUDED_NAMES),
        "portable_test_lane": test_result,
        "notebook_static_result": notebook_result,
        "synthetic_rehearsal_result": synthetic_result,
        "verification_started_at_utc": verification_started_at_utc,
        "verification_completed_at_utc": verification_completed_at_utc,
        "verification_duration_seconds": round(time.monotonic() - verification_started, 3),
        "verification_working_directory": str(base),
        "verification_python": sys.version.split()[0],
        "evidence_class": "release_validation_only",
        "claim_allowed": False,
    }
    atomic_write_json(payload, target.with_suffix(target.suffix + ".manifest.json"))
    if errors:
        raise RuntimeError("archive verification failed: " + "; ".join(errors))
    return payload
