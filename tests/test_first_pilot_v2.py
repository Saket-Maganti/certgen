import csv
from pathlib import Path

from certgen.pilot.first_pilot_v2 import plan_first_pilot_v2


HEADER = [
    "comparison_id",
    "benchmark_id",
    "model_a_id",
    "model_b_id",
    "paper_or_source_id",
    "reported_metric_name",
    "reported_metric_a",
    "reported_metric_b",
    "reported_sample_size",
    "reported_preprocessing_note",
    "released_samples_a_status",
    "released_samples_b_status",
    "checkpoint_a_status",
    "checkpoint_b_status",
    "feature_cache_status",
    "license_status",
    "audit_eligibility",
    "blocker_reason",
]


def _write_registry(root: Path, row: dict):
    template_dir = root / "templates"
    template_dir.mkdir(parents=True)
    with (template_dir / "candidate_model_pairs_template.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER)
        writer.writeheader()
        writer.writerow(row)


def _complete_row(**updates):
    row = {
        "comparison_id": "cmp",
        "benchmark_id": "bench",
        "model_a_id": "a",
        "model_b_id": "b",
        "paper_or_source_id": "paper",
        "reported_metric_name": "kid",
        "reported_metric_a": "1.0",
        "reported_metric_b": "1.1",
        "reported_sample_size": "50000",
        "reported_preprocessing_note": "resize=32 interpolation=nearest",
        "released_samples_a_status": "available",
        "released_samples_b_status": "available",
        "checkpoint_a_status": "unknown",
        "checkpoint_b_status": "unknown",
        "feature_cache_status": "available",
        "license_status": "verified",
        "audit_eligibility": "eligible",
        "blocker_reason": "",
    }
    row.update(updates)
    return row


def test_complete_smoke_registry_selects_pilot(tmp_path):
    _write_registry(tmp_path / "registry", _complete_row())
    plan = plan_first_pilot_v2(tmp_path / "registry", tmp_path / "plan.json", tmp_path / "plan.md", dry_run=True)
    assert plan["selected_benchmark"] == "bench"
    assert plan["selected_model_pairs"] == ["cmp"]
    assert plan["evidence_status"] == "dry_run_only"
    assert plan["claim_status"] == "NO_REAL_CLAIMS_ALLOWED"


def test_missing_availability_license_or_preprocessing_blocks(tmp_path):
    _write_registry(
        tmp_path / "registry",
        _complete_row(
            released_samples_a_status="unknown",
            checkpoint_a_status="unknown",
            license_status="unknown",
            reported_preprocessing_note="TBD",
            audit_eligibility="needs_user_verification",
        ),
    )
    plan = plan_first_pilot_v2(tmp_path / "registry", tmp_path / "plan.json", tmp_path / "plan.md", dry_run=True)
    assert plan["selected_benchmark"] == "none_selected"
    assert "verified registry row" in plan["missing_artifacts"]
