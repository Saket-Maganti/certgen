"""Validate copied-back Kaggle generation output ZIPs."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any

from certgen.core.hashing import file_sha256
from certgen.core.io import write_json
from certgen.generation.validate_cifar10_generated_pilot import EXPECTED_MANIFESTS, validate_generated_pilot
from certgen.packaging.common import (
    archive_has_forbidden_outputs,
    inspect_zip_safety,
    safe_extract_zip,
    scan_text_for_private_paths_or_secrets,
    write_blocked_summary,
    write_jsonl,
    zip_file_manifest,
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _find_image(root: Path, row: dict[str, Any]) -> Path | None:
    value = str(row.get("image_path") or row.get("path") or "")
    candidates = []
    if value:
        candidates.extend(path for path in root.rglob(Path(value).name) if path.is_file())
    sample_id = str(row.get("sample_id") or "")
    if sample_id:
        candidates.extend(path for path in root.rglob(f"{sample_id}.*") if path.is_file())
    return sorted(set(candidates), key=lambda item: str(item))[0] if candidates else None


def _rewrite_manifests(extract_root: Path, manifest_dir: Path) -> list[str]:
    errors: list[str] = []
    manifest_dir.mkdir(parents=True, exist_ok=True)
    for name in EXPECTED_MANIFESTS:
        found = sorted(extract_root.rglob(name), key=lambda item: str(item))
        if not found:
            errors.append(f"missing per-gpu manifest: {name}")
            continue
        rows = []
        for row in _read_jsonl(found[0]):
            image = _find_image(extract_root, row)
            if image is None:
                errors.append(f"{row.get('sample_id', '<unknown>')}: generated image missing")
                rows.append(row)
                continue
            row = dict(row)
            row["path"] = str(image)
            row["image_path"] = str(image)
            row.setdefault("sha256", file_sha256(image))
            row.setdefault("image_hash", row["sha256"])
            row.setdefault("claim_allowed", False)
            rows.append(row)
        write_jsonl(rows, manifest_dir / name)
    return errors


def validate_generation_output_zip(
    *,
    input_zip: str | Path,
    extract_dir: str | Path = "data/sources/cifar10_r1/generated_1k",
    out_manifest: str | Path = "registry/manifests/cifar10_r1_generated_pilot_1000.jsonl",
    summary_out: str | Path = "data/results/v6_generation_output_validation_summary.json",
    expected_count_per_model: int = 1000,
) -> dict[str, Any]:
    input_zip = Path(input_zip)
    if not input_zip.exists():
        return write_blocked_summary(
            json_out=summary_out,
            status_code="BLOCKED_GENERATION_OUTPUT_ZIP_MISSING",
            errors=[f"generation output ZIP missing: {input_zip}"],
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
                        try:
                            text = zf.read(name).decode("utf-8", errors="ignore")
                        except Exception:
                            continue
                        text_issues.extend(scan_text_for_private_paths_or_secrets(text))
                        if '"claim_allowed": true' in text.lower():
                            claim_true = True
        except zipfile.BadZipFile:
            safety["errors"].append("bad ZIP file")
    if not safety["passed"] or forbidden or text_issues or claim_true:
        payload = {
            "passed": False,
            "status_code": "BLOCKED_GENERATION_MANIFEST_INVALID",
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
            status_code="BLOCKED_GENERATION_MANIFEST_INVALID",
            errors=[f"refusing to overwrite existing extraction directory: {extract_dir}"],
            zip_path=input_zip,
        )
    try:
        safe_extract_zip(input_zip, extract_dir)
    except (FileExistsError, ValueError, OSError) as exc:
        return write_blocked_summary(
            json_out=summary_out,
            status_code="BLOCKED_GENERATION_MANIFEST_INVALID",
            errors=[str(exc)],
            zip_path=input_zip,
        )
    manifest_dir = extract_dir / "kaggle_manifests"
    rewrite_errors = _rewrite_manifests(extract_dir, manifest_dir)
    summary = validate_generated_pilot(
        manifest_dir=manifest_dir,
        out_manifest=out_manifest,
        out_summary=summary_out,
        expected_count_per_model=expected_count_per_model,
        check_image_hashes=True,
    )
    errors = rewrite_errors + list(summary.get("errors", []))
    status_code = summary.get("status_code", "BLOCKED_GENERATION_MANIFEST_INVALID") if not errors else "BLOCKED_GENERATION_MANIFEST_INVALID"
    if summary.get("passed") and not errors:
        status_code = "VALIDATED_GENERATED_PILOT"
    payload = {
        **summary,
        "passed": summary.get("passed") and not errors,
        "status_code": status_code,
        "errors": errors,
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
    parser = argparse.ArgumentParser(description="Validate copied-back CertGen generation output ZIP.")
    parser.add_argument("--input-zip", required=True)
    parser.add_argument("--extract-dir", default="data/sources/cifar10_r1/generated_1k")
    parser.add_argument("--out-manifest", default="registry/manifests/cifar10_r1_generated_pilot_1000.jsonl")
    parser.add_argument("--summary-out", default="data/results/v6_generation_output_validation_summary.json")
    parser.add_argument("--expected-count-per-model", type=int, default=1000)
    args = parser.parse_args(argv)
    payload = validate_generation_output_zip(
        input_zip=args.input_zip,
        extract_dir=args.extract_dir,
        out_manifest=args.out_manifest,
        summary_out=args.summary_out,
        expected_count_per_model=args.expected_count_per_model,
    )
    print(f"Generation output validation: {payload['status_code']}")
    return 0 if payload["passed"] else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
