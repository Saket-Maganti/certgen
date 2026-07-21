"""Validate copied-back Kaggle feature output ZIPs."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path
from typing import Any

from certgen.core.io import write_json
from certgen.packaging.common import (
    archive_has_forbidden_outputs,
    inspect_zip_safety,
    safe_extract_zip,
    scan_text_for_private_paths_or_secrets,
    write_blocked_summary,
    zip_file_manifest,
)
from certgen.pipeline.v6_execution import _validate_split_feature_caches


def validate_feature_output_zip(
    *,
    input_zip: str | Path,
    extract_dir: str | Path = "data/features/cifar10_r1",
    summary_out: str | Path = "data/results/v6_feature_output_validation_summary.json",
) -> dict[str, Any]:
    input_zip = Path(input_zip)
    if not input_zip.exists():
        return write_blocked_summary(
            json_out=summary_out,
            status_code="BLOCKED_FEATURE_OUTPUT_ZIP_MISSING",
            errors=[f"feature output ZIP missing: {input_zip}"],
            zip_path=input_zip,
        )
    safety = inspect_zip_safety(input_zip)
    forbidden: list[str] = []
    text_issues: list[str] = []
    claim_true = False
    if safety["passed"]:
        try:
            with zipfile.ZipFile(input_zip, "r") as zf:
                names = zf.namelist()
                forbidden = archive_has_forbidden_outputs(names)
                text_issues = scan_text_for_private_paths_or_secrets("\n".join(names))
                for name in names:
                    if name.endswith((".json", ".jsonl", ".md", ".txt")):
                        text = zf.read(name).decode("utf-8", errors="ignore")
                        text_issues.extend(scan_text_for_private_paths_or_secrets(text))
                        if '"claim_allowed": true' in text.lower():
                            claim_true = True
        except zipfile.BadZipFile:
            safety["errors"].append("bad ZIP file")
    if not safety["passed"] or forbidden or text_issues or claim_true:
        payload = {
            "passed": False,
            "status_code": "BLOCKED_FEATURE_CACHE_INVALID",
            "errors": [*safety["errors"], *forbidden, *text_issues, *(["claim_allowed=true present"] if claim_true else [])],
            "claim_allowed": False,
            "no_fake_results": True,
            "not_paper_evidence": True,
        }
        write_json(payload, summary_out)
        return payload
    extract_dir = Path(extract_dir)
    if extract_dir.exists():
        return write_blocked_summary(
            json_out=summary_out,
            status_code="BLOCKED_FEATURE_CACHE_INVALID",
            errors=[f"refusing to overwrite existing extraction directory: {extract_dir}"],
            zip_path=input_zip,
        )
    try:
        safe_extract_zip(input_zip, extract_dir)
    except (FileExistsError, ValueError, OSError) as exc:
        return write_blocked_summary(
            json_out=summary_out,
            status_code="BLOCKED_FEATURE_CACHE_INVALID",
            errors=[str(exc)],
            zip_path=input_zip,
        )
    checks, blockers, role_counts = _validate_split_feature_caches(extract_dir)
    dims: dict[str, set[int]] = {"inception": set(), "clip": set()}
    for check in checks:
        shape = check.get("shape") or []
        if len(shape) == 2:
            if check["cache_id"].endswith("_inception"):
                dims["inception"].add(int(shape[1]))
            if check["cache_id"].endswith("_clip"):
                dims["clip"].add(int(shape[1]))
    if len(dims["inception"]) > 1:
        blockers.append("Inception dims are not stable")
    if len(dims["clip"]) > 1:
        blockers.append("CLIP dims are not stable")
    payload = {
        "passed": not blockers,
        "status_code": "FEATURE_OUTPUT_ZIP_VALIDATED" if not blockers else "BLOCKED_FEATURE_CACHE_INVALID",
        "feature_cache_checks": checks,
        "role_counts": role_counts,
        "errors": blockers,
        "input_zip": str(input_zip),
        "extract_dir": str(extract_dir),
        "zip_manifest": zip_file_manifest(input_zip),
        "claim_allowed": False,
        "no_fake_results": True,
        "not_paper_evidence": True,
    }
    write_json(payload, summary_out)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate copied-back CertGen feature output ZIP.")
    parser.add_argument("--input-zip", required=True)
    parser.add_argument("--extract-dir", default="data/features/cifar10_r1")
    parser.add_argument("--summary-out", default="data/results/v6_feature_output_validation_summary.json")
    args = parser.parse_args(argv)
    payload = validate_feature_output_zip(input_zip=args.input_zip, extract_dir=args.extract_dir, summary_out=args.summary_out)
    print(f"Feature output validation: {payload['status_code']}")
    return 0 if payload["passed"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
