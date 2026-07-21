"""Build the CIFAR-10 R1 feature-extraction sample package."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from certgen.core.hashing import file_sha256
from certgen.core.io import read_json, write_json


MODEL_ROLES = {
    "google/ddpm-cifar10-32": "google_ddpm",
    "FrankCCCCC/ddpm_ema_cifar10": "frank_ddpm_ema",
    "FrankCCCCC/cfm-cifar10-32": "frank_cfm",
}


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _read_ledger_model_ids(path: str | Path) -> set[str]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return {row.get("model_id", "") for row in csv.DictReader(handle)}


def _path_value(row: dict[str, Any]) -> str:
    return str(row.get("path") or row.get("image_path") or row.get("absolute_path") or "")


def build_sample_package(
    *,
    reference_manifest: str | Path,
    generated_manifest: str | Path,
    provenance_ledger: str | Path,
    preprocessing_lock: str | Path,
    out_manifest: str | Path,
    out_summary: str | Path,
    expected_reference_count: int = 10000,
    expected_generated_count_per_model: int = 1000,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not Path(reference_manifest).exists():
        errors.append(f"reference manifest missing: {reference_manifest}")
        reference_rows: list[dict[str, Any]] = []
    else:
        reference_rows = _read_jsonl(reference_manifest)
    if not Path(generated_manifest).exists():
        errors.append(f"generated manifest missing: {generated_manifest}")
        generated_rows: list[dict[str, Any]] = []
    else:
        generated_rows = _read_jsonl(generated_manifest)
    if not Path(provenance_ledger).exists():
        errors.append(f"provenance ledger missing: {provenance_ledger}")
        ledger_ids: set[str] = set()
    else:
        ledger_ids = _read_ledger_model_ids(provenance_ledger)
    if not Path(preprocessing_lock).exists():
        errors.append(f"preprocessing lock missing: {preprocessing_lock}")
        preprocessing_hash = None
    else:
        preprocessing_hash = file_sha256(preprocessing_lock)
        read_json(preprocessing_lock)

    if reference_rows and len(reference_rows) != expected_reference_count:
        errors.append(f"reference expected {expected_reference_count} rows, found {len(reference_rows)}")
    counts_by_role = {role: 0 for role in MODEL_ROLES.values()}
    output_rows: list[dict[str, Any]] = []
    seen_sample_ids: set[str] = set()

    def add_row(row: dict[str, Any], *, role: str, source_id: str) -> None:
        sample_id = str(row.get("sample_id") or "")
        if not sample_id:
            errors.append(f"{role}: missing sample_id")
            return
        if sample_id in seen_sample_ids:
            errors.append(f"duplicate sample_id: {sample_id}")
        seen_sample_ids.add(sample_id)
        path = _path_value(row)
        if not path or not Path(path).exists():
            errors.append(f"{sample_id}: path missing: {path}")
        if row.get("claim_allowed") is True:
            errors.append(f"{sample_id}: claim_allowed=true is forbidden")
        packaged = {key: value for key, value in row.items() if key not in {"role", "evidence_status", "claim_allowed"}}
        packaged.update(
            {
                "role": role,
                "path": path,
                "source_id": source_id,
                "preprocessing_lock_hash": preprocessing_hash,
                "evidence_status": "sample_package_only",
                "claim_allowed": False,
            }
        )
        output_rows.append(packaged)

    for row in reference_rows:
        source_id = str(row.get("source_id") or "cifar10_reference")
        if source_id not in ledger_ids and "cifar10_reference" not in ledger_ids:
            warnings.append(f"reference source_id not directly present in ledger: {source_id}")
        add_row(row, role="reference", source_id=source_id)

    for row in generated_rows:
        checkpoint_id = str(row.get("checkpoint_id") or row.get("model_id") or "")
        role = MODEL_ROLES.get(checkpoint_id)
        if not role:
            errors.append(f"unknown checkpoint_id: {checkpoint_id}")
            continue
        counts_by_role[role] += 1
        if checkpoint_id not in ledger_ids:
            errors.append(f"checkpoint_id missing from provenance ledger: {checkpoint_id}")
        add_row(row, role=role, source_id=checkpoint_id)

    for role, count in counts_by_role.items():
        if count != expected_generated_count_per_model:
            errors.append(f"{role}: expected {expected_generated_count_per_model} generated rows, found {count}")

    passed = not errors
    out_manifest = Path(out_manifest)
    out_manifest.parent.mkdir(parents=True, exist_ok=True)
    if passed:
        output_rows.sort(key=lambda row: (str(row.get("role", "")), str(row.get("sample_id", ""))))
        with out_manifest.open("w", encoding="utf-8") as handle:
            for row in output_rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
    status_code = "READY_FOR_KAGGLE_FEATURE_EXTRACTION" if passed else "BLOCKED_GENERATION_MANIFEST_INVALID"
    if any("reference manifest missing" in error or "reference expected" in error for error in errors):
        status_code = "BLOCKED_MISSING_REFERENCE_SAMPLES"
    elif any("generated manifest missing" in error for error in errors):
        status_code = "BLOCKED_GENERATION_NOT_RUN"
    elif any("expected" in error and "generated rows" in error for error in errors):
        status_code = "BLOCKED_GENERATION_INCOMPLETE"

    summary = {
        "passed": passed,
        "status_code": status_code,
        "errors": errors,
        "warnings": warnings,
        "reference_count": len(reference_rows),
        "generated_counts_by_role": counts_by_role,
        "out_manifest": str(out_manifest),
        "preprocessing_lock_hash": preprocessing_hash,
        "evidence_status": "sample_package_only",
        "claim_allowed": False,
        "feature_extraction_ready": passed,
    }
    write_json(summary, out_summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the CIFAR-10 R1 feature-extraction sample package.")
    parser.add_argument("--reference-manifest", required=True)
    parser.add_argument("--generated-manifest", required=True)
    parser.add_argument("--provenance-ledger", required=True)
    parser.add_argument("--preprocessing-lock", required=True)
    parser.add_argument("--out-manifest", required=True)
    parser.add_argument("--out-summary", required=True)
    parser.add_argument("--expected-reference-count", type=int, default=10000)
    parser.add_argument("--expected-generated-count-per-model", type=int, default=1000)
    args = parser.parse_args(argv)
    try:
        summary = build_sample_package(
            reference_manifest=args.reference_manifest,
            generated_manifest=args.generated_manifest,
            provenance_ledger=args.provenance_ledger,
            preprocessing_lock=args.preprocessing_lock,
            out_manifest=args.out_manifest,
            out_summary=args.out_summary,
            expected_reference_count=args.expected_reference_count,
            expected_generated_count_per_model=args.expected_generated_count_per_model,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2
    print(f"CIFAR-10 R1 sample package: {summary['status_code']}")
    return 0 if summary["passed"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
