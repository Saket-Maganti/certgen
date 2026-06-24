from pathlib import Path
import os

import pytest

from certgen.audit.v2_audit import run_v2_audit


def test_v2_audit_runs_and_writes_outputs(tmp_path):
    if os.environ.get("CERTGEN_SKIP_V2_AUDIT_TEST") == "1":
        pytest.skip("skip recursive audit test inside V2 audit subprocess")
    payload = run_v2_audit(out=tmp_path / "V2_FINAL_AUDIT.md", json_out=tmp_path / "v2_final_audit.json")
    assert payload["audit_status"] == "passed"
    assert len(payload["checks"]) >= 15
    assert all(check["passed"] for check in payload["checks"])
    assert Path(tmp_path / "V2_FINAL_AUDIT.md").exists()
    assert Path(tmp_path / "v2_final_audit.json").exists()
