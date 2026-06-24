from certgen.audit.v5_state_intake import run_v5_state_intake


def test_v5_state_intake_passes_on_repo():
    payload = run_v5_state_intake(".")
    assert payload["passed"]
    assert payload["v4_detected"]
    assert payload["v4_audit_passed"]
    assert payload["claim_boundary_status"] == "clean"


def test_v5_state_intake_fails_missing_v4_files(tmp_path):
    payload = run_v5_state_intake(tmp_path)
    assert not payload["passed"]
    assert "claim_contract" in payload["missing_cvpr_ready_items"]
