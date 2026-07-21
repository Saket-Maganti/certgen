import json
from pathlib import Path

from certgen.core.io import read_json
from certgen.pipeline.cifar10_real_pilot import run_cifar10_r1_readiness, validate_sample_manifest
from certgen.registry.provenance import validate_provenance_ledger


def _has_claim_allowed_true(value):
    if isinstance(value, dict):
        return any((key == "claim_allowed" and item is True) or _has_claim_allowed_true(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_has_claim_allowed_true(item) for item in value)
    return False


def test_r1_source_selection_artifacts_exist_and_are_claim_safe():
    required = [
        Path("docs/R1_SOURCE_SELECTION_AND_PROVENANCE_REPORT.md"),
        Path("registry/provenance/cifar10_r1_ledger.csv"),
        Path("registry/manifests/cifar10_r1_samples.jsonl"),
        Path("data/results/r1_source_selection_status.json"),
    ]
    for path in required:
        assert path.exists(), path
    status = read_json("data/results/r1_source_selection_status.json")
    assert status["status_code"] in {"BLOCKED_MISSING_REAL_SOURCES", "BLOCKED_MISSING_REFERENCE_SAMPLES"}
    assert status["claim_allowed"] is False
    assert status["verified_sources_count"] == 3
    assert status["blocked_sources_count"] >= 1
    assert status["kaggle_feature_extraction_can_run"] is False
    assert status["kaggle_feature_extraction_command"] is None
    assert not _has_claim_allowed_true(status)


def test_r1_provenance_ledger_validates_but_keeps_unresolved_warnings():
    result = validate_provenance_ledger("registry/provenance/cifar10_r1_ledger.csv", require_real_pilot=True)
    assert result["passed"], result["errors"]
    assert result["claim_allowed"] is False
    warnings = "\n".join(result["warnings"]).lower()
    assert "license unknown" in warnings
    assert "checkpoint generation needed later" in warnings


def test_r1_sample_manifest_is_structured_but_not_local_ready():
    manifest = Path("registry/manifests/cifar10_r1_samples.jsonl")
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert {row["role"] for row in rows} == {"reference", "model_a", "model_b"}
    assert all(row.get("claim_allowed") is False for row in rows)
    assert validate_sample_manifest(manifest, require_local_files=False)["passed"]
    local_result = validate_sample_manifest(manifest, require_local_files=True)
    assert not local_result["passed"]
    assert any("local sample path missing" in error for error in local_result["errors"])


def test_r1_readiness_blocks_before_kaggle_feature_extraction(tmp_path):
    payload = run_cifar10_r1_readiness(
        provenance_ledger="registry/provenance/cifar10_r1_ledger.csv",
        sample_manifest="registry/manifests/cifar10_r1_samples.jsonl",
        preprocessing_lock="configs/preprocessing_locks/cifar10_inception_bilinear_299.json",
        feature_cache_dir="data/features/cifar10_r1",
        metric_reproduction_audit="data/results/cifar10_r1_metric_reproduction.json",
        out_json=tmp_path / "r1_status.json",
        report=tmp_path / "r1_report.md",
    )
    assert payload["status_code"] == "BLOCKED_MISSING_REFERENCE_SAMPLES"
    assert payload["ready_for_r1"] is False
    assert payload["claim_allowed"] is False
    assert payload["kaggle_feature_extraction_ready"] is False
    assert payload["kaggle_feature_extraction_command"] is None
    assert len(payload["selected_candidate_model_pairs"]) == 5
    report = (tmp_path / "r1_report.md").read_text(encoding="utf-8")
    assert "not_ready: source package is not feature-extraction-ready" in report
