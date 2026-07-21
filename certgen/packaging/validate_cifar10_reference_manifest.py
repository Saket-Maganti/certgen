"""Validate a local CIFAR-10 reference manifest."""

from __future__ import annotations

import argparse
from pathlib import Path

from certgen.core.hashing import file_sha256
from certgen.core.io import write_json
from certgen.data.build_cifar10_reference_manifest import CLASS_NAMES, _image_info
from certgen.packaging.common import has_claim_allowed_true, read_jsonl


def validate_reference_manifest(*, manifest: str | Path, summary_out: str | Path, expected_count: int = 10000) -> dict:
    path = Path(manifest)
    errors: list[str] = []
    if not path.exists():
        errors.append(f"reference manifest missing: {path}")
        rows = []
    else:
        try:
            rows = read_jsonl(path)
        except Exception as exc:
            errors.append(f"reference manifest is not valid JSONL: {exc}")
            rows = []
    sample_ids: set[str] = set()
    resolved_paths: set[str] = set()
    content_hashes: set[str] = set()
    class_counts = {name: 0 for name in CLASS_NAMES}
    for idx, row in enumerate(rows, start=1):
        if has_claim_allowed_true(row):
            errors.append(f"line {idx}: claim_allowed=true")
        sample_path = Path(str(row.get("path") or row.get("image_path") or ""))
        sample_id = str(row.get("sample_id") or "")
        if not sample_id:
            errors.append(f"line {idx}: sample_id missing")
        elif sample_id in sample_ids:
            errors.append(f"line {idx}: duplicate sample_id: {sample_id}")
        sample_ids.add(sample_id)
        path_key = str(sample_path.resolve()) if sample_path.exists() else str(sample_path)
        if path_key in resolved_paths:
            errors.append(f"line {idx}: duplicate sample path: {sample_path}")
        resolved_paths.add(path_key)
        if not sample_path.exists():
            errors.append(f"line {idx}: sample path missing: {sample_path}")
        if int(row.get("width", 0)) != 32 or int(row.get("height", 0)) != 32 or int(row.get("channels", 0)) != 3:
            errors.append(f"line {idx}: expected 32x32 RGB")
        declared_hash = row.get("sha256") or row.get("hash")
        if not declared_hash:
            errors.append(f"line {idx}: missing hash")
        elif sample_path.is_file():
            actual_hash = file_sha256(sample_path)
            if declared_hash != actual_hash:
                errors.append(f"line {idx}: image hash mismatch: {sample_path}")
            if actual_hash in content_hashes:
                errors.append(f"line {idx}: duplicate image content: {sample_path}")
            content_hashes.add(actual_hash)
            try:
                actual_shape = _image_info(sample_path)
            except Exception as exc:
                errors.append(f"line {idx}: image decode/header validation failed: {exc}")
            else:
                if actual_shape != (32, 32, 3):
                    errors.append(f"line {idx}: decoded image is not 32x32 RGB: {actual_shape}")
        if row.get("role") != "reference":
            errors.append(f"line {idx}: role must be reference")
        if row.get("evidence_status") not in {"r1a_sample_package_non_evidence", "sample_package_only"}:
            errors.append(f"line {idx}: unsafe or missing evidence_status")
        if not row.get("source_url") or not row.get("license_status"):
            errors.append(f"line {idx}: source_url/license_status missing")
        class_label = str(row.get("class_label") or "")
        if class_label in class_counts:
            class_counts[class_label] += 1
        if "absolute_path" in row:
            errors.append(f"line {idx}: deprecated privacy-sensitive absolute_path field present")
    if len(rows) != expected_count:
        errors.append(f"expected {expected_count} reference rows, found {len(rows)}")
    if expected_count == 10_000 and sum(class_counts.values()) == 10_000:
        unbalanced = {label: count for label, count in class_counts.items() if count != 1_000}
        if unbalanced:
            errors.append(f"CIFAR-10 test class counts must each equal 1000: {unbalanced}")
    payload = {
        "passed": not errors,
        "status_code": "REFERENCE_MANIFEST_VALID" if not errors else "BLOCKED_MISSING_REFERENCE_SAMPLES",
        "rows": len(rows),
        "expected_count": expected_count,
        "class_counts": class_counts,
        "errors": errors,
        "claim_allowed": False,
        "no_fake_results": True,
        "not_paper_evidence": True,
    }
    write_json(payload, summary_out)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate CIFAR-10 reference manifest.")
    parser.add_argument("--manifest", default="registry/manifests/cifar10_r1_reference.jsonl")
    parser.add_argument("--summary-out", default="data/results/v6_reference_manifest_validation_summary.json")
    parser.add_argument("--expected-count", type=int, default=10000)
    args = parser.parse_args(argv)
    payload = validate_reference_manifest(manifest=args.manifest, summary_out=args.summary_out, expected_count=args.expected_count)
    print(f"Reference manifest validation: {payload['status_code']}")
    return 0 if payload["passed"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
