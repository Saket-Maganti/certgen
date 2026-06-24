"""V2 registry validation."""

from __future__ import annotations

import csv
from pathlib import Path

from certgen.registry.schemas import CandidateModelPairV2, ReportedMetricClaimV2


UNKNOWN = {"", "unknown", "TBD", "tbd", "needs_user_verification"}


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_model_pair_rows(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    required = set(CandidateModelPairV2.__dataclass_fields__)
    seen: set[str] = set()
    for index, row in enumerate(rows, start=2):
        missing = required - set(row)
        errors.extend(f"row {index}: missing column {col}" for col in sorted(missing))
        comparison_id = row.get("comparison_id", "")
        if comparison_id in seen:
            errors.append(f"row {index}: comparison_id not unique")
        seen.add(comparison_id)
        blockers = []
        for field in [
            "reported_metric_name",
            "reported_sample_size",
            "reported_preprocessing_note",
            "license_status",
        ]:
            if row.get(field, "") in UNKNOWN:
                blockers.append(field)
        if row.get("released_samples_a_status", "") in UNKNOWN and row.get("checkpoint_a_status", "") in UNKNOWN:
            blockers.append("model_a_samples_or_checkpoint")
        if row.get("released_samples_b_status", "") in UNKNOWN and row.get("checkpoint_b_status", "") in UNKNOWN:
            blockers.append("model_b_samples_or_checkpoint")
        for field in ["reported_metric_a", "reported_metric_b"]:
            value = row.get(field, "")
            if value in UNKNOWN:
                blockers.append(field)
            else:
                try:
                    float(value)
                except ValueError:
                    errors.append(f"row {index}: {field} malformed")
        if blockers and row.get("audit_eligibility") == "eligible":
            errors.append(f"row {index}: eligible row has blockers: {', '.join(blockers)}")
        if row.get("audit_eligibility") not in {"eligible", "blocked", "needs_user_verification"}:
            errors.append(f"row {index}: invalid audit_eligibility")
    return errors


def validate_claim_rows(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    required = set(ReportedMetricClaimV2.__dataclass_fields__)
    for index, row in enumerate(rows, start=2):
        missing = required - set(row)
        errors.extend(f"claim row {index}: missing column {col}" for col in sorted(missing))
        if row.get("claim_evidence_status") not in {"planned", "dry_run_only", "smoke_only"}:
            errors.append(f"claim row {index}: claim_evidence_status must be planned/dry_run/smoke")
    return errors
