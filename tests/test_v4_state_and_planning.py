import csv
from pathlib import Path

from certgen.audit.v4_state_intake import run_v4_state_intake
from certgen.notebooks.generate_feature_notebook import generate_feature_notebook
from certgen.preprocess.locks import make_preprocessing_lock, validate_preprocessing_lock
from certgen.provenance.ledger import V4_LEDGER_FIELDS
from certgen.provenance.real_run_plan import build_real_run_plan


def _write_ledger(path: Path, **overrides):
    row = {
        "comparison_id": "pair_1",
        "benchmark_id": "bench",
        "dataset_name": "dataset",
        "dataset_split": "test",
        "reference_set_source": "manifest.jsonl",
        "model_a_name": "a",
        "model_b_name": "b",
        "model_a_sample_source": "a.jsonl",
        "model_b_sample_source": "b.jsonl",
        "sample_source_type": "released_samples",
        "sample_license_status": "verified_free",
        "sample_count_available_a": "100",
        "sample_count_available_b": "100",
        "reported_metric_name": "kid_polynomial",
        "reported_metric_value_a": "",
        "reported_metric_value_b": "",
        "reported_sample_size": "32",
        "reported_preprocessing": "v4_lock",
        "paper_or_source_citation": "template",
        "download_required": "no",
        "external_data_required": "no",
        "provenance_status": "verified",
        "claim_allowed": "false",
    }
    row.update(overrides)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=V4_LEDGER_FIELDS)
        writer.writeheader()
        writer.writerow(row)


def test_v4_state_intake_passes_on_repo():
    payload = run_v4_state_intake(".")
    assert payload["passed"]
    assert payload["claim_allowed"] is False


def test_real_run_plan_blocks_unverified_rows_and_keeps_nonclaim(tmp_path):
    ledger = tmp_path / "ledger.csv"
    _write_ledger(ledger, provenance_status="planned", sample_license_status="unknown")
    plan = build_real_run_plan(ledger, "pair_1", tmp_path / "plan.json", tmp_path / "plan.md")
    assert plan["evidence_status"] == "planned_only"
    assert plan["claim_allowed"] is False
    assert plan["blockers"]


def test_real_run_plan_notebook_and_preprocessing_lock(tmp_path):
    ledger = tmp_path / "ledger.csv"
    _write_ledger(ledger)
    plan_path = tmp_path / "plan.json"
    plan = build_real_run_plan(ledger, "pair_1", plan_path, tmp_path / "plan.md")
    assert plan["evidence_status"] == "real_verified_nonclaim"
    assert plan["claim_allowed"] is False

    script = generate_feature_notebook(plan_path, "local", "inception_v3_pool3", tmp_path / "notebook.py")
    assert "CERTGEN_SAMPLE_MANIFEST" in script
    assert "CLAIM_ALLOWED = False" in script

    lock_path = tmp_path / "lock.json"
    lock = make_preprocessing_lock("v4_lock", lock_path)
    assert lock["hash"]
    assert validate_preprocessing_lock(lock_path) == []
