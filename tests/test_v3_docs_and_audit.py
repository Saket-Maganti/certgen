import os

import pytest

from certgen.audit.v3_final import run_v3_final_audit


def test_v3_docs_exist_and_command_index_mentions_clis():
    required = [
        "docs/COMMAND_INDEX_V3.md",
        "docs/V3_RUNBOOK.md",
        "docs/REPRODUCIBILITY_CAPSULE_V3.md",
        "docs/CLAIM_POLICY_V3.md",
        "docs/FID_POLICY_V3.md",
        "docs/FIRST_REAL_PILOT_CHECKLIST.md",
        "docs/TROUBLESHOOTING_V3.md",
    ]
    for path in required:
        assert os.path.exists(path)
    index = open("docs/COMMAND_INDEX_V3.md", encoding="utf-8").read()
    for command in [
        "v3_intake_audit",
        "validate_provenance_ledger",
        "validate_feature_cache",
        "plan_feature_extraction",
        "audit_metric_reproduction",
        "run_first_pilot",
        "replay_certificate",
        "render_pilot_report",
        "validate_v3_registry",
        "render_availability_table",
        "run_optional_stopping_lab",
        "v3_audit",
    ]:
        assert command in index
    assert "model A is better" in open("docs/CLAIM_POLICY_V3.md", encoding="utf-8").read()
    assert "descriptive-only" in open("docs/FID_POLICY_V3.md", encoding="utf-8").read()


def test_v3_final_audit_runs(tmp_path):
    if os.environ.get("CERTGEN_SKIP_V3_AUDIT_TEST") == "1":
        pytest.skip("avoid recursive V3 audit")
    payload = run_v3_final_audit(out=tmp_path / "audit.md", json_out=tmp_path / "audit.json")
    assert payload["passed"]
    assert payload["checks_total"] >= 24
    assert payload["claim_allowed"] is False
