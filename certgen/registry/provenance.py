"""Released-sample provenance ledger validation."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from certgen.core.io import write_json


REQUIRED_LEDGER_FIELDS = [
    "row_id",
    "benchmark_id",
    "dataset_name",
    "dataset_split",
    "reference_source_type",
    "reference_uri_or_path",
    "model_id",
    "model_family",
    "sample_source_type",
    "sample_uri_or_path",
    "sample_count_available",
    "feature_cache_path",
    "feature_extractor",
    "preprocessing_id",
    "reported_metric_name",
    "reported_metric_value",
    "reported_sample_count",
    "reported_source_title",
    "reported_source_url_or_doi",
    "license_status",
    "download_required",
    "requires_gpu_to_materialize",
    "verified_by",
    "verified_date",
    "notes",
]


def read_ledger(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_provenance_ledger(path: str | Path, *, allow_missing_local: bool = False, require_real_pilot: bool = False) -> dict[str, Any]:
    rows = read_ledger(path)
    errors: list[str] = []
    warnings: list[str] = []
    for idx, row in enumerate(rows, start=2):
        for field in REQUIRED_LEDGER_FIELDS:
            if field not in row:
                errors.append(f"row {idx}: missing field {field}")
        if row.get("license_status") in {"restricted", "not_allowed"}:
            errors.append(f"row {idx}: license_status blocks use")
        if require_real_pilot and row.get("sample_source_type") == "unavailable":
            errors.append(f"row {idx}: unavailable samples cannot enter real pilot")
        for field in ["reported_metric_value", "reported_sample_count", "sample_count_available"]:
            value = row.get(field, "")
            if value in {"", "unknown", "TBD"}:
                warnings.append(f"row {idx}: {field} unknown")
            else:
                try:
                    float(value)
                except ValueError:
                    errors.append(f"row {idx}: {field} must be numeric")
        try:
            if row.get("sample_count_available") not in {"", "unknown", "TBD"} and row.get("reported_sample_count") not in {"", "unknown", "TBD"}:
                if int(float(row["sample_count_available"])) < int(float(row["reported_sample_count"])):
                    errors.append(f"row {idx}: sample_count_available < reported_sample_count")
        except ValueError:
            pass
        if row.get("license_status") == "unknown":
            warnings.append(f"row {idx}: license unknown")
        if not row.get("reported_source_url_or_doi"):
            warnings.append(f"row {idx}: source URL/DOI absent")
        if row.get("sample_source_type") == "checkpoint_generated_later":
            warnings.append(f"row {idx}: checkpoint generation needed later")
        if row.get("preprocessing_id") in {"", "unknown", "TBD"}:
            warnings.append(f"row {idx}: preprocessing unknown")
        if row.get("reported_metric_name", "").lower().startswith("fid") and row.get("feature_extractor") not in {"inception", "inception_v3_pool3", "custom", "TBD", "unknown"}:
            errors.append(f"row {idx}: feature_extractor conflicts with FID")
        for local_field in ["reference_uri_or_path", "sample_uri_or_path", "feature_cache_path"]:
            value = row.get(local_field, "")
            if value.startswith("/") or value.startswith(".") or value.startswith("data/"):
                if value and not Path(value).exists() and not allow_missing_local:
                    errors.append(f"row {idx}: local path missing for {local_field}: {value}")
    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "rows": len(rows),
        "evidence_status": "planned_only",
        "claim_allowed": False,
    }


def write_provenance_validation_report(result: dict[str, Any], out: str | Path, json_out: str | Path) -> None:
    lines = ["# Provenance Ledger Validation", "", "`NO_REAL_EVIDENCE`", "", f"Passed: `{result['passed']}`", f"Rows: `{result['rows']}`", "", "## Errors"]
    lines.extend(f"- {e}" for e in result["errors"] or ["none"])
    lines.append("")
    lines.append("## Warnings")
    lines.extend(f"- {w}" for w in result["warnings"] or ["none"])
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(result, json_out)
