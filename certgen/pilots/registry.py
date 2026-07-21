"""Pilot registry dataclasses and CSV helpers."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from certgen.core.enums import EvidenceStatus


@dataclass
class CandidateBenchmark:
    benchmark_id: str
    name: str
    data_source_note: str
    reference_set_available: str
    license_note: str
    preprocessing_requirements: str
    status: str
    evidence_status: str = EvidenceStatus.NON_EVIDENCE_PLANNED.value


@dataclass
class CandidateModelPair:
    pair_id: str
    benchmark_id: str
    model_a_name: str
    model_b_name: str
    reported_metric: str
    reported_a_score: str
    reported_b_score: str
    reported_sample_size: str
    paper_or_source: str
    samples_available: str
    checkpoint_available: str
    feature_stats_available: str
    license_note: str
    contestable_reason: str
    status: str
    evidence_status: str = EvidenceStatus.NON_EVIDENCE_PLANNED.value


@dataclass
class AuditClaimRecord:
    claim_id: str
    pair_id: str
    claim_text: str
    metric_name: str
    reported_direction: str
    recomputed_direction: str
    certificate_status: str
    decided_at_n: str
    evidence_status: str
    limitations: str


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_benchmark_rows(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    required = set(CandidateBenchmark.__dataclass_fields__)
    for index, row in enumerate(rows, start=2):
        missing = required - set(row)
        if missing:
            errors.append(f"benchmarks row {index}: missing columns {sorted(missing)}")
        if row.get("evidence_status") != EvidenceStatus.NON_EVIDENCE_PLANNED.value:
            errors.append(f"benchmarks row {index}: evidence_status must be non_evidence_planned")
        if row.get("status") not in {"planned", "ready_for_feature_extraction", "blocked"}:
            errors.append(f"benchmarks row {index}: invalid status {row.get('status')}")
    return errors


def validate_pair_rows(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    required = set(CandidateModelPair.__dataclass_fields__)
    for index, row in enumerate(rows, start=2):
        missing = required - set(row)
        if missing:
            errors.append(f"pairs row {index}: missing columns {sorted(missing)}")
        if row.get("evidence_status") != EvidenceStatus.NON_EVIDENCE_PLANNED.value:
            errors.append(f"pairs row {index}: evidence_status must be non_evidence_planned")
        if row.get("status") not in {"planned", "ready_for_feature_extraction", "blocked"}:
            errors.append(f"pairs row {index}: invalid status {row.get('status')}")
        for score_field in ("reported_a_score", "reported_b_score", "reported_sample_size"):
            value = row.get(score_field, "")
            if value and value.upper() != "TBD":
                try:
                    float(value)
                except ValueError:
                    errors.append(f"pairs row {index}: {score_field} must be numeric, blank, or TBD")
    return errors


def enough_metadata_for_pilot(row: dict[str, str]) -> bool:
    required = [
        "benchmark_id",
        "model_a_name",
        "model_b_name",
        "reported_metric",
        "reported_a_score",
        "reported_b_score",
        "reported_sample_size",
        "paper_or_source",
        "license_note",
    ]
    return all(row.get(field) and row.get(field) != "TBD" for field in required)


def plan_first_pilot_markdown(pair_rows: list[dict[str, str]]) -> str:
    ready = [row for row in pair_rows if enough_metadata_for_pilot(row)]
    lines = [
        "# First Pilot Plan",
        "",
        "No pilot run has been executed.",
        "No decidedness fraction is available.",
        "",
    ]
    if ready:
        lines.extend(["## Candidate Rows With Complete Metadata", ""])
        for row in ready:
            lines.append(f"- `{row['pair_id']}` on `{row['benchmark_id']}` using `{row['reported_metric']}`")
    else:
        lines.extend(
            [
                "## TODO Checklist",
                "",
                "- Select one benchmark.",
                "- Verify reference-set availability and license.",
                "- Verify released samples, checkpoints, or feature stats for both models.",
                "- Record the reported metric, scores, sample size, and source.",
                "- Document preprocessing and interpolation.",
                "- Choose one clean-core metric for the first certificate run.",
                "- Keep FID descriptive if it is included.",
                "- Run only after all metadata cells are verified.",
            ]
        )
    lines.append("")
    return "\n".join(lines)
