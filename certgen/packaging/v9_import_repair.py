"""V9 local import repair for copied-back Kaggle ZIPs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from certgen.core.hashing import file_sha256
from certgen.core.io import write_json
from certgen.cvpr.contracts import atomic_write_json
from certgen.cvpr.output_schemas import (
    member_allowed,
    schema_for,
    validate_output_zip,
    validate_status_payload,
)
from certgen.packaging.artifact_registry import append_artifact_entry, build_artifact_entry
from certgen.packaging.common import inspect_zip_safety, safe_extract_zip, scan_text_for_private_paths_or_secrets


ALLOWLISTS = {
    "preflight": ["checkpoint_preflight_status.json", "preflight", "logs", "certgen_checkpoint_preflight_outputs"],
    "generation": ["samples", "manifests", "logs", "generation", "status", "integrity", "certgen_cifar10_generation"],
    "feature": ["features", "split", "logs", "feature", "status", "integrity", "certgen_cifar10_feature"],
}
REQUIRED_STATUS = {
    "preflight": ("checkpoint_preflight_status.json", "status.json"),
    "generation": ("generation_status.json", "status.json"),
    "feature": ("feature_extraction_status.json", "status.json"),
}
CLAIM_KEY = "claim_allowed"
CLAIM_EQUALS_TRUE = f"{CLAIM_KEY}=true"
CLAIM_JSON_TRUE = f'"{CLAIM_KEY}": true'
MAX_TEXT_MEMBER_BYTES = 16 * 1024**2
SAFE_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}")


def _run_id_from_archive(zip_path: Path, kind: str, zip_digest: str | None) -> str:
    fallback = (
        f"cifar10-{kind}-1k-{zip_digest[:12]}"
        if zip_digest
        else f"cifar10-{kind}-1k-missing"
    )
    if not zip_path.is_file():
        return fallback
    try:
        with zipfile.ZipFile(zip_path) as archive:
            candidates = [
                info
                for info in archive.infolist()
                if info.filename == "run_identity.json" and not info.is_dir()
            ]
            if len(candidates) != 1 or candidates[0].file_size > 64 * 1024:
                return fallback
            payload = json.loads(archive.read(candidates[0]).decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile):
        return fallback
    run_id = payload.get("run_id") if isinstance(payload, dict) else None
    if (
        not isinstance(run_id, str)
        or not SAFE_RUN_ID.fullmatch(run_id)
        or payload.get("claim_allowed") is not False
    ):
        return fallback
    return run_id


def _safe_member(name: str, kind: str) -> bool:
    return member_allowed(kind, name)


def _status_jsons(root: Path) -> list[Path]:
    return [path for path in root.rglob("*.json") if "status" in path.name.lower()]


def _status_errors(kind: str, status: dict[str, Any]) -> list[str]:
    errors = validate_status_payload(kind, status)
    code = str(status.get("status_code", ""))
    if not code:
        errors.append("required status JSON has no status_code")
    if "BLOCKED" in code or "FAILED" in code:
        errors.append(f"required status JSON is not complete: {code}")
    if kind == "preflight":
        results = status.get("results")
        extractor_results = status.get("extractor_results")
        if code != "PREFLIGHT_PASS":
            errors.append(f"checkpoint preflight status must be PREFLIGHT_PASS, found {code or '<missing>'}")
        if not isinstance(results, list) or not results:
            errors.append("checkpoint preflight status must contain per-model results")
        elif any(item.get("status_code") != "PREFLIGHT_PASS" for item in results if isinstance(item, dict)):
            errors.append("one or more checkpoint preflight model results did not pass")
        if not isinstance(extractor_results, list) or not extractor_results:
            errors.append("checkpoint preflight status must contain per-extractor results")
        elif any(item.get("status_code") != "EXTRACTOR_PREFLIGHT_PASS" for item in extractor_results if isinstance(item, dict)):
            errors.append("one or more extractor preflight results did not pass")
    elif kind == "generation":
        if status.get("passed") is not True or code not in {"VALIDATED_GENERATED_PILOT", "GENERATION_COMPLETE"}:
            errors.append("generation status must be passed=true and use a supported complete status")
    elif kind == "feature" and code != "FEATURE_EXTRACTION_SHARDS_COMPLETE":
        errors.append("feature status must be FEATURE_EXTRACTION_SHARDS_COMPLETE")
    return errors


def _integrity_errors(archive: zipfile.ZipFile, names: list[str]) -> list[str]:
    errors: list[str] = []
    candidates = [name for name in names if name.endswith("output_zip_integrity_manifest.json") or name == "integrity_manifest.json"]
    if len(candidates) != 1:
        return ["output ZIP integrity manifest must appear exactly once"]
    try:
        payload = json.loads(archive.read(candidates[0]).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [f"output ZIP integrity manifest is invalid: {exc}"]
    rows = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows:
        return ["output ZIP integrity manifest must contain a non-empty files list"]
    declared: set[str] = set()
    info_by_name = {info.filename: info for info in archive.infolist() if not info.is_dir()}
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"integrity row {index} is not an object")
            continue
        name = str(row.get("path") or "")
        if not name or name in declared:
            errors.append(f"integrity row {index} has a missing/duplicate path: {name!r}")
            continue
        declared.add(name)
        info = info_by_name.get(name)
        if info is None:
            errors.append(f"integrity row {index} references missing ZIP member: {name}")
            continue
        if row.get("size") != info.file_size:
            errors.append(f"integrity size mismatch: {name}")
        digest = hashlib.sha256()
        with archive.open(info, "r") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        if row.get("sha256") != digest.hexdigest():
            errors.append(f"integrity hash mismatch: {name}")
    actual = set(info_by_name) - set(candidates)
    undeclared = sorted(actual - declared)
    if undeclared:
        errors.append("ZIP members missing from integrity manifest: " + ", ".join(undeclared[:20]))
    return errors


def _worker_completeness_errors(kind: str, status: dict[str, Any], status_names: list[str]) -> list[str]:
    """Require the canonical root status to enumerate every worker identity."""

    expected = status.get("expected_workers")
    if not isinstance(expected, list) or not expected or any(not isinstance(item, str) or not item for item in expected):
        return [f"canonical {kind} status must declare non-empty expected_workers"]
    if len(expected) != len(set(expected)):
        return [f"canonical {kind} status contains duplicate expected_workers"]
    observed: list[str] = []
    for name in status_names:
        parts = Path(name).parts
        if kind == "generation" and len(parts) >= 5:
            observed.append(f"{parts[1]}__{parts[3]}")
        elif kind == "feature" and len(parts) >= 4:
            observed.append(f"{parts[1]}__{parts[2]}")
    missing = sorted(set(expected) - set(observed))
    unexpected = sorted(set(observed) - set(expected))
    errors: list[str] = []
    if missing:
        errors.append("canonical output is missing expected workers: " + ", ".join(missing))
    if unexpected:
        errors.append("canonical output contains unexpected workers: " + ", ".join(unexpected))
    return errors


def import_repair(
    *,
    kind: str,
    zip_path: str | Path,
    out_dir: str | Path | None = None,
    out_json: str | Path = "data/results/v9_import_repair_status.json",
    out_report: str | Path = "docs/V9_IMPORT_REPAIR_REPORT.md",
    registry_path: str | Path = "data/artifact_registry.jsonl",
    force: bool = False,
) -> dict[str, Any]:
    if kind not in ALLOWLISTS:
        raise ValueError(f"unknown import kind: {kind}")
    zip_path = Path(zip_path)
    zip_digest = file_sha256(zip_path) if zip_path.is_file() else None
    run_id = _run_id_from_archive(zip_path, kind, zip_digest)
    out_dir = Path(out_dir or f"data/imported/{run_id}")
    errors: list[str] = []
    warnings: list[str] = []
    failed_shards: list[str] = []
    missing_shards: list[str] = []
    import_time = datetime.now(timezone.utc).isoformat()
    preserved_raw_copy: Path | None = None
    raw_record_root: Path | None = None
    if zip_digest:
        raw_record_root = out_dir.parent / "_raw_zip_store" / zip_digest
        preserved_raw_copy = raw_record_root / "source.zip"
        try:
            if raw_record_root.exists():
                if not preserved_raw_copy.is_file() or file_sha256(preserved_raw_copy) != zip_digest:
                    errors.append(f"hash-addressed raw ZIP store is inconsistent: {raw_record_root}")
            else:
                temporary_raw_root = raw_record_root.with_name(f".{zip_digest}.partial.{os.getpid()}")
                temporary_raw_root.mkdir(parents=True, exist_ok=False)
                temporary_copy = temporary_raw_root / "source.zip"
                shutil.copy2(zip_path, temporary_copy)
                os.chmod(temporary_copy, 0o444)
                raw_record_root.parent.mkdir(parents=True, exist_ok=True)
                os.replace(temporary_raw_root, raw_record_root)
        except OSError as exc:
            errors.append(f"raw ZIP preservation failed: {exc}")
    if not zip_path.exists():
        errors.append(f"ZIP missing: {zip_path}")
    else:
        try:
            with zipfile.ZipFile(zip_path) as archive:
                safety = inspect_zip_safety(zip_path)
                errors.extend(safety["errors"])
                schema_verdict = validate_output_zip(kind, str(zip_path))
                errors.extend(
                    f"canonical output schema: {error}"
                    for error in schema_verdict["errors"]
                )
                names = archive.namelist()
                unknown = [name for name in names if not _safe_member(name, kind)]
                if unknown:
                    errors.extend(f"unknown file refused: {name}" for name in unknown[:20])
                text_blob = "\n".join(names)
                for name in names:
                    if name.endswith((".json", ".jsonl", ".md", ".txt", ".log")):
                        info = archive.getinfo(name)
                        if info.file_size > MAX_TEXT_MEMBER_BYTES:
                            errors.append(f"text/log member exceeds scan limit: {name}")
                            continue
                        text_blob += "\n" + archive.read(name).decode("utf-8", errors="ignore")
                if CLAIM_JSON_TRUE in text_blob.lower() or CLAIM_EQUALS_TRUE in text_blob.lower():
                    errors.append("claim_allowed true flag found in ZIP")
                lower = text_blob.lower()
                if "paper evidence" in lower and "not paper evidence" not in lower:
                    errors.append("paper-evidence language found without negation")
                errors.extend(scan_text_for_private_paths_or_secrets(text_blob))
                errors.extend(_integrity_errors(archive, names))
                required_payload: dict[str, Any] = {}
                schema = schema_for(kind)
                required_options = REQUIRED_STATUS[kind]
                preferred = schema.status_file
                preferred_names = [name for name in names if name == preferred or name.endswith("/" + preferred)]
                canonical_names = [name for name in names if name == "status.json"]
                status_names = preferred_names[:1] or canonical_names[:1]
                if not status_names:
                    errors.append(f"required status JSON missing; accepted names: {', '.join(required_options)}")
                else:
                    try:
                        required_payload = json.loads(archive.read(status_names[0]).decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        errors.append(f"required status JSON is invalid: {exc}")
                    else:
                        if not isinstance(required_payload, dict):
                            errors.append("required status JSON must contain an object")
                        else:
                            errors.extend(_status_errors(kind, required_payload))
                lowered_names = "\n".join(names).lower()
                if kind == "generation":
                    canonical_statuses = [name for name in names if name.startswith("per_model/") and name.endswith("/status.json")]
                    if canonical_statuses:
                        errors.extend(_worker_completeness_errors("generation", required_payload, canonical_statuses))
                        for status_name in canonical_statuses:
                            try:
                                shard_status = json.loads(archive.read(status_name).decode("utf-8"))
                            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                                errors.append(f"invalid generation shard status {status_name}: {exc}")
                                continue
                            if shard_status.get("status_code") != "SHARD_COMPLETE":
                                errors.append(f"generation shard is not complete: {status_name}")
                        canonical_manifests = [name for name in names if name.startswith("per_model/") and name.endswith("/manifest.jsonl")]
                        if len(canonical_manifests) != len(canonical_statuses):
                            errors.append("canonical generation ZIP must contain one manifest per shard status")
                    else:
                        expected = [
                            "google_ddpm_gpu0",
                            "google_ddpm_gpu1",
                            "frank_ddpm_ema_gpu0",
                            "frank_ddpm_ema_gpu1",
                            "frank_cfm_gpu0",
                            "frank_cfm_gpu1",
                        ]
                        missing_shards = [shard for shard in expected if shard not in lowered_names]
                        if missing_shards:
                            errors.append("generation ZIP is missing required shard artifacts: " + ", ".join(missing_shards))
                elif kind == "feature":
                    canonical_statuses = [name for name in names if name.startswith("shards/") and name.endswith("/status.json")]
                    if canonical_statuses:
                        errors.extend(_worker_completeness_errors("feature", required_payload, canonical_statuses))
                        for status_name in canonical_statuses:
                            try:
                                shard_status = json.loads(archive.read(status_name).decode("utf-8"))
                            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                                errors.append(f"invalid feature shard status {status_name}: {exc}")
                                continue
                            if shard_status.get("status_code") != "FEATURE_SHARD_COMPLETE":
                                errors.append(f"feature shard is not complete: {status_name}")
                        for status_name in canonical_statuses:
                            prefix = status_name.removesuffix("status.json")
                            for required_name in (prefix + "features.npz", prefix + "sidecar.json"):
                                if required_name not in names:
                                    errors.append(f"canonical feature shard is missing: {required_name}")
                    else:
                        expected = [
                            f"{role}_{extractor}.{suffix}"
                            for role in ["reference", "google_ddpm", "frank_ddpm_ema", "frank_cfm"]
                            for extractor in ["inception", "clip"]
                            for suffix in ["npz", "sidecar.json"]
                        ]
                        missing_shards = [item for item in expected if item not in lowered_names]
                        if missing_shards:
                            errors.append("feature ZIP is missing required cache artifacts: " + ", ".join(missing_shards))
                if force:
                    errors.append("destructive --force replacement is disabled; choose a new run-specific --out-dir")
                if out_dir.exists():
                    errors.append(f"output directory already exists; existing artifacts were preserved: {out_dir}")
                if not errors:
                    safe_extract_zip(zip_path, out_dir)
                    raw_dir = out_dir / "_raw_zip"
                    raw_dir.mkdir(parents=True, exist_ok=False)
                    raw_copy = raw_dir / zip_path.name
                    shutil.copy2(zip_path, raw_copy)
                    os.chmod(raw_copy, 0o444)
                    entry = build_artifact_entry(
                        path=raw_copy,
                        artifact_type=f"kaggle_{kind}_output_zip",
                        stage=kind,
                        run_id=run_id,
                        source=f"copied_back:{zip_path}",
                        validation_status="import_contract_passed",
                        evidence_class="RUN_LOG_ONLY" if kind == "preflight" else "PILOT_ARTIFACT",
                        notes="Imported package remains non-evidence until downstream provenance and scientific gates pass.",
                    )
                    append_artifact_entry(entry, registry_path)
        except zipfile.BadZipFile:
            errors.append("bad ZIP file")
    if out_dir.exists():
        for status_path in _status_jsons(out_dir):
            try:
                payload = json.loads(status_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            status_text = json.dumps(payload).lower()
            if "failed" in status_text or "blocked" in status_text:
                failed_shards.append(str(status_path))
        if kind == "generation":
            if any(out_dir.glob("per_model/*/per_shard/*/status.json")):
                missing_shards = []
            else:
                expected = ["google_ddpm_gpu0", "google_ddpm_gpu1", "frank_ddpm_ema_gpu0", "frank_ddpm_ema_gpu1", "frank_cfm_gpu0", "frank_cfm_gpu1"]
                all_names = "\n".join(str(path) for path in out_dir.rglob("*"))
                missing_shards = [shard for shard in expected if shard not in all_names]
        if kind == "feature":
            if any(out_dir.glob("shards/*/status.json")):
                missing_shards = []
            else:
                expected = ["inception", "clip"]
                all_names = "\n".join(str(path) for path in out_dir.rglob("*"))
                missing_shards = [shard for shard in expected if shard not in all_names]
    repair_commands = []
    if kind == "preflight":
        repair_commands.append("Run notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb and copy back the deterministic output ZIP")
    elif kind == "generation":
        repair_commands.append("Run notebooks/kaggle/certgen_cvpr_cifar10_generation_t4x2_1k.ipynb and copy back the deterministic output ZIP")
    else:
        repair_commands.append("Run notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_1k.ipynb and copy back the deterministic output ZIP")
    payload = {
        "schema_version": "certgen.cvpr.import_record.v1",
        "kind": kind,
        "import_time": import_time,
        "passed": not errors,
        "status_code": "IMPORT_REPAIR_READY" if not errors else "IMPORT_REPAIR_BLOCKED",
        "zip_path": str(zip_path),
        "out_dir": str(out_dir),
        "zip_sha256": file_sha256(zip_path) if zip_path.exists() else None,
        "run_id": run_id,
        "registry_path": str(registry_path),
        "errors": errors,
        "warnings": warnings,
        "missing_files": [error for error in errors if "missing" in error.lower()],
        "hash_mismatches": [error for error in errors if "hash" in error.lower() or "integrity" in error.lower()],
        "schema_mismatches": [error for error in errors if "schema" in error.lower() or "status json" in error.lower()],
        "missing_shards": missing_shards,
        "failed_shards": failed_shards,
        "repair_commands": repair_commands,
        "kaggle_rerun_needed": bool(errors),
        "local_repair_safe": False if errors else None,
        "raw_preserved_path": str(preserved_raw_copy) if preserved_raw_copy and preserved_raw_copy.is_file() else None,
        "claim_allowed": False,
        "no_fake_results": True,
        "not_paper_evidence": True,
    }
    write_json(payload, out_json)
    if raw_record_root is not None and preserved_raw_copy is not None and preserved_raw_copy.is_file():
        record_stamp = import_time.replace(":", "").replace("+00:00", "Z").replace(".", "-")
        atomic_write_json(
            {
                "schema_version": "certgen.cvpr.raw_import_validation.v1",
                "source_zip_hash": zip_digest,
                "raw_path": str(preserved_raw_copy),
                "import_time": import_time,
                "run_id": run_id,
                "kind": kind,
                "validation_result": payload["status_code"],
                "repair_actions": repair_commands,
                "errors": errors,
                "claim_allowed": False,
            },
            raw_record_root / f"validation_{record_stamp}.json",
        )
    lines = [
        "# V9 Import Repair Report",
        "",
        "`NO_FAKE_RESULTS`",
        "`NO_REAL_EVIDENCE`",
        "`not paper evidence`",
        "",
        f"Kind: `{kind}`",
        f"Status: `{payload['status_code']}`",
        f"Passed: `{payload['passed']}`",
        "Claim allowed: `false`",
        "",
        "## Errors",
    ]
    lines.extend(f"- {item}" for item in errors or ["none"])
    lines.extend(["", "## Repair Commands"])
    lines.extend(f"- `{item}`" for item in repair_commands)
    Path(out_report).parent.mkdir(parents=True, exist_ok=True)
    Path(out_report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V9 import repair for Kaggle ZIPs.")
    parser.add_argument("--kind", required=True, choices=sorted(ALLOWLISTS))
    parser.add_argument("--zip", required=True)
    parser.add_argument("--out-dir")
    parser.add_argument("--out-json", default="data/results/v9_import_repair_status.json")
    parser.add_argument("--out-report", default="docs/V9_IMPORT_REPAIR_REPORT.md")
    parser.add_argument("--registry", default="data/artifact_registry.jsonl")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    payload = import_repair(
        kind=args.kind,
        zip_path=args.zip,
        out_dir=args.out_dir,
        out_json=args.out_json,
        out_report=args.out_report,
        registry_path=args.registry,
        force=args.force,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["passed"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
