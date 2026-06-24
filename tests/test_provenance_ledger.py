import csv

from certgen.registry.provenance import REQUIRED_LEDGER_FIELDS, validate_provenance_ledger


def _write_ledger(path, row):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_LEDGER_FIELDS)
        writer.writeheader()
        writer.writerow(row)


def _row(**updates):
    base = {field: "TBD" for field in REQUIRED_LEDGER_FIELDS}
    base.update(
        {
            "row_id": "row",
            "benchmark_id": "bench",
            "dataset_name": "dataset",
            "dataset_split": "test",
            "reference_source_type": "public_dataset",
            "reference_uri_or_path": "data/missing_reference",
            "model_id": "model",
            "model_family": "family",
            "sample_source_type": "released_samples",
            "sample_uri_or_path": "data/missing_samples",
            "sample_count_available": "100",
            "feature_cache_path": "data/missing_features",
            "feature_extractor": "inception_v3_pool3",
            "preprocessing_id": "explicit",
            "reported_metric_name": "kid",
            "reported_metric_value": "1.0",
            "reported_sample_count": "50",
            "reported_source_title": "source",
            "reported_source_url_or_doi": "https://example.invalid",
            "license_status": "verified_free",
            "download_required": "false",
            "requires_gpu_to_materialize": "false",
            "verified_by": "tester",
            "verified_date": "2026-06-23",
            "notes": "NO_REAL_EVIDENCE",
        }
    )
    base.update(updates)
    return base


def test_valid_planned_ledger_and_path_policy(tmp_path):
    path = tmp_path / "ledger.csv"
    _write_ledger(path, _row())
    assert validate_provenance_ledger(path, allow_missing_local=True)["passed"]
    assert not validate_provenance_ledger(path, allow_missing_local=False)["passed"]


def test_restricted_unavailable_and_unknown_license(tmp_path):
    path = tmp_path / "ledger.csv"
    _write_ledger(path, _row(license_status="restricted", sample_source_type="unavailable"))
    result = validate_provenance_ledger(path, allow_missing_local=True, require_real_pilot=True)
    assert not result["passed"]
    assert any("license" in error for error in result["errors"])
    path2 = tmp_path / "ledger_unknown.csv"
    _write_ledger(path2, _row(license_status="unknown"))
    result2 = validate_provenance_ledger(path2, allow_missing_local=True)
    assert result2["passed"]
    assert any("license unknown" in warning for warning in result2["warnings"])
