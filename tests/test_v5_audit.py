import os

import pytest

from certgen.audit.v5_audit import FINAL_VERDICT, run_v5_final_audit


@pytest.mark.integration_audit
def test_v5_final_audit_runs(tmp_path):
    if os.environ.get("CERTGEN_SKIP_V5_AUDIT_TEST") == "1":
        pytest.skip("avoid recursive V5 audit")
    payload = run_v5_final_audit(out=tmp_path / "V5_FINAL_AUDIT.md", json_out=tmp_path / "v5_final_audit.json")
    assert payload["passed"]
    assert payload["checks_total"] >= 30
    assert payload["claim_allowed"] is False
    assert payload["final_verdict"] == FINAL_VERDICT
    assert "real execution" in payload["next_action"]
