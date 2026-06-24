"""V4 released-sample ledger helpers."""

from __future__ import annotations

import csv
from pathlib import Path


V4_LEDGER_FIELDS = [
    "comparison_id",
    "benchmark_id",
    "dataset_name",
    "dataset_split",
    "reference_set_source",
    "model_a_name",
    "model_b_name",
    "model_a_sample_source",
    "model_b_sample_source",
    "sample_source_type",
    "sample_license_status",
    "sample_count_available_a",
    "sample_count_available_b",
    "reported_metric_name",
    "reported_metric_value_a",
    "reported_metric_value_b",
    "reported_sample_size",
    "reported_preprocessing",
    "paper_or_source_citation",
    "download_required",
    "external_data_required",
    "provenance_status",
    "claim_allowed",
]


def read_v4_ledger(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
