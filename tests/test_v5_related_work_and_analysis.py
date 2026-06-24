import csv

from certgen.audit.analysis_plan_audit import analysis_plan_hash, audit_analysis_plan_lock, default_analysis_plan, write_analysis_plan_lock
from certgen.audit.related_work_audit import RELATED_WORK_FIELDS, audit_related_work_board
from certgen.core.io import read_json, write_json


def test_v5_related_work_board_passes_on_repo():
    result = audit_related_work_board()
    assert result["passed"]
    assert result["rows"] >= 6


def test_v5_related_work_rejects_verified_without_source(tmp_path):
    path = tmp_path / "related.csv"
    row = {field: "x" for field in RELATED_WORK_FIELDS}
    row.update({"work_id": "w", "bucket": "generative_image_metrics", "verified": "true", "url_or_doi": "", "verification_source": "", "citation_status": "verified"})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RELATED_WORK_FIELDS)
        writer.writeheader()
        writer.writerow(row)
    result = audit_related_work_board(path, paper_root=tmp_path)
    assert not result["passed"]


def test_v5_analysis_plan_hash_and_mismatch(tmp_path):
    plan_path = tmp_path / "plan.json"
    hash_path = tmp_path / "hash.txt"
    plan = write_analysis_plan_lock(plan_path, hash_path)
    assert audit_analysis_plan_lock(plan_path, hash_path)["passed"]
    loaded = read_json(plan_path)
    loaded["primary_question"] = "changed"
    write_json(loaded, plan_path)
    assert not audit_analysis_plan_lock(plan_path, hash_path)["passed"]
    assert analysis_plan_hash(default_analysis_plan()) == plan["lock_hash"]
