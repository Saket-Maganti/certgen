"""Validate copied-back CIFAR-10 generated pilot manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from certgen.core.hashing import file_sha256
from certgen.core.io import write_json
from certgen.generation.merge_sample_manifests import merge_sample_manifests


EXPECTED_MANIFESTS = {
    "google_ddpm_gpu0.jsonl": "google/ddpm-cifar10-32",
    "google_ddpm_gpu1.jsonl": "google/ddpm-cifar10-32",
    "frank_ddpm_ema_gpu0.jsonl": "FrankCCCCC/ddpm_ema_cifar10",
    "frank_ddpm_ema_gpu1.jsonl": "FrankCCCCC/ddpm_ema_cifar10",
    "frank_cfm_gpu0.jsonl": "FrankCCCCC/cfm-cifar10-32",
    "frank_cfm_gpu1.jsonl": "FrankCCCCC/cfm-cifar10-32",
}

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


def _status_from_errors(errors: list[str], counts: dict[str, int], expected_count_per_model: int) -> str:
    if any("missing per-gpu manifest" in error for error in errors):
        return "BLOCKED_GENERATION_NOT_RUN"
    if any("duplicate" in error or "claim_allowed=true" in error or "hash mismatch" in error or "missing generated image path" in error for error in errors):
        return "BLOCKED_GENERATION_MANIFEST_INVALID"
    if any(counts.get(model, 0) != expected_count_per_model for model in MODEL_ROLES):
        return "BLOCKED_GENERATION_INCOMPLETE"
    return "VALIDATED_GENERATED_PILOT"


def validate_generated_pilot(
    *,
    manifest_dir: str | Path,
    out_manifest: str | Path,
    out_summary: str | Path,
    expected_count_per_model: int = 1000,
    check_image_hashes: bool = True,
) -> dict[str, Any]:
    manifest_dir = Path(manifest_dir)
    errors: list[str] = []
    warnings: list[str] = []
    manifests: list[Path] = []
    for name in EXPECTED_MANIFESTS:
        path = manifest_dir / name
        if path.exists():
            manifests.append(path)
        else:
            errors.append(f"missing per-gpu manifest: {path}")

    if errors:
        summary = {
            "passed": False,
            "status_code": "BLOCKED_GENERATION_NOT_RUN",
            "errors": errors,
            "warnings": warnings,
            "manifest_dir": str(manifest_dir),
            "out_manifest": str(out_manifest),
            "counts_by_model": {},
            "expected_count_per_model": expected_count_per_model,
            "evidence_status": "sample_package_only",
            "claim_allowed": False,
        }
        write_json(summary, out_summary)
        return summary

    merge_summary = merge_sample_manifests(
        manifests=manifests,
        out_manifest=out_manifest,
        out_summary=out_summary,
        check_image_hashes=check_image_hashes,
    )
    errors.extend(merge_summary["errors"])
    rows = _read_jsonl(out_manifest) if Path(out_manifest).exists() and not errors else []
    counts_by_model = {model: 0 for model in MODEL_ROLES}
    for idx, row in enumerate(rows, start=1):
        checkpoint_id = str(row.get("checkpoint_id") or "")
        if checkpoint_id not in MODEL_ROLES:
            errors.append(f"line {idx}: unknown checkpoint_id: {checkpoint_id}")
            continue
        counts_by_model[checkpoint_id] += 1
        image_path = Path(str(row.get("image_path") or row.get("path") or ""))
        if not image_path.exists():
            errors.append(f"line {idx}: missing generated image path: {image_path}")
        if int(row.get("width", 0)) != 32 or int(row.get("height", 0)) != 32 or int(row.get("channels", 0)) != 3:
            errors.append(f"line {idx}: invalid CIFAR image shape")
        if row.get("claim_allowed") is True:
            errors.append(f"line {idx}: claim_allowed=true is forbidden")
        image_hash = row.get("image_hash") or row.get("sha256")
        if not image_hash:
            errors.append(f"line {idx}: image hash missing")
        elif check_image_hashes and image_path.exists() and image_hash != file_sha256(image_path):
            errors.append(f"line {idx}: image hash mismatch: {image_path}")
    for model, count in counts_by_model.items():
        if count != expected_count_per_model:
            errors.append(f"{model}: expected {expected_count_per_model} rows, found {count}")

    status_code = _status_from_errors(errors, counts_by_model, expected_count_per_model)
    summary = {
        "passed": not errors,
        "status_code": status_code,
        "errors": errors,
        "warnings": warnings,
        "manifest_dir": str(manifest_dir),
        "out_manifest": str(out_manifest),
        "counts_by_model": counts_by_model,
        "expected_count_per_model": expected_count_per_model,
        "rows": len(rows),
        "check_image_hashes": check_image_hashes,
        "evidence_status": "sample_package_only",
        "claim_allowed": False,
    }
    write_json(summary, out_summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate copied-back CIFAR-10 generated pilot manifests.")
    parser.add_argument("--manifest-dir", required=True)
    parser.add_argument("--out-manifest", required=True)
    parser.add_argument("--out-summary", required=True)
    parser.add_argument("--expected-count-per-model", type=int, default=1000)
    parser.add_argument("--check-image-hashes", action="store_true")
    args = parser.parse_args(argv)
    try:
        summary = validate_generated_pilot(
            manifest_dir=args.manifest_dir,
            out_manifest=args.out_manifest,
            out_summary=args.out_summary,
            expected_count_per_model=args.expected_count_per_model,
            check_image_hashes=args.check_image_hashes,
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2
    print(f"CIFAR-10 generated pilot validation: {summary['status_code']}")
    return 0 if summary["passed"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
