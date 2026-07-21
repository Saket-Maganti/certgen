from __future__ import annotations

import csv
from pathlib import Path

from certgen.registry.validate_multibench_candidates import validate


def test_multibench_candidate_validation(tmp_path: Path) -> None:
    path = tmp_path / "candidates.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "benchmark",
                "source_type",
                "sample_availability",
                "license",
                "expected_compute",
                "feature_extractors",
                "metric_reproduction_availability",
                "risk",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "benchmark": "CIFAR-10",
                "source_type": "image",
                "sample_availability": "user_provided",
                "license": "check_required",
                "expected_compute": "low",
                "feature_extractors": "inception;clip",
                "metric_reproduction_availability": "pilot_only",
                "risk": "reference_missing",
                "status": "blocked_until_reference",
            }
        )
    payload = validate(path)
    assert payload["ok"] is True
    assert payload["claim_allowed"] is False
