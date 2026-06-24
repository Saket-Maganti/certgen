"""Validate reported metric claim rows."""

from __future__ import annotations

import csv
from pathlib import Path

from certgen.literature.claim_schema import CLAIM_FIELDS


def read_claims(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_claims(path: str | Path, *, strict: bool = False) -> dict:
    rows = read_claims(path)
    errors: list[str] = []
    warnings: list[str] = []
    for idx, row in enumerate(rows, start=2):
        for field in CLAIM_FIELDS:
            if field not in row:
                errors.append(f"row {idx}: missing field {field}")
        if not row.get("paper_title") or not row.get("citation_key"):
            errors.append(f"row {idx}: clear source required")
        if row.get("metric_name") in {"", "TBD", "unknown"} or row.get("benchmark") in {"", "TBD", "unknown"}:
            errors.append(f"row {idx}: metric and benchmark required")
        if row.get("reported_sample_size") in {"", "TBD", "unknown"}:
            (errors if strict else warnings).append(f"row {idx}: reported sample size unknown")
        if row.get("claim_allowed", "false").lower() == "true":
            errors.append(f"row {idx}: claim_allowed must remain false until gates pass")
    return {"passed": not errors, "errors": errors, "warnings": warnings, "rows": len(rows), "claim_allowed": False, "evidence_status": "planned_only"}
