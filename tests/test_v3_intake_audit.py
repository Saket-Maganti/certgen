import importlib.util
import os

import pytest

from certgen.audit.v3_intake import run_v3_intake_audit


def test_v3_intake_audit_schema(tmp_path):
    if os.environ.get("CERTGEN_SKIP_V3_INTAKE_TEST") == "1":
        pytest.skip("avoid recursive intake audit")
    payload = run_v3_intake_audit(out=tmp_path / "intake.md", json_out=tmp_path / "intake.json", run_pytest=False)
    assert payload["audit_name"] == "v3_intake_audit"
    assert payload["claim_allowed"] is False
    assert payload["evidence_status"] == "dry_run_only"


def test_missing_core_module_detection_monkeypatch(tmp_path, monkeypatch):
    original = importlib.util.find_spec

    def fake_find_spec(name, *args, **kwargs):
        if name == "certgen.metrics.streams":
            return None
        return original(name, *args, **kwargs)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)
    payload = run_v3_intake_audit(out=tmp_path / "intake.md", json_out=tmp_path / "intake.json", run_pytest=False)
    assert not payload["passed"]
    assert any("certgen.metrics.streams" in item for item in payload["blockers"])
