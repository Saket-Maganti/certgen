import os

import pytest

from certgen.audit.v4_audit import NEXT_V5_ACTION, run_v4_final_audit


@pytest.mark.integration_audit
def test_v4_final_audit_runs(tmp_path):
    if os.environ.get("CERTGEN_SKIP_V4_AUDIT_TEST") == "1":
        pytest.skip("avoid recursive V4 audit")
    payload = run_v4_final_audit(out=tmp_path / "V4_FINAL_AUDIT.md", json_out=tmp_path / "v4_final_audit.json")
    assert payload["passed"]
    assert payload["checks_total"] >= 25
    assert payload["claim_allowed"] is False
    assert payload["next_action"] == NEXT_V5_ACTION
