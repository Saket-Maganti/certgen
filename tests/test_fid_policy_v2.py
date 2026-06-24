import numpy as np
import pytest

from certgen.certs.fid_policy import assert_no_rigorous_fid_claim, fid_policy_summary
from certgen.gates.claim_gate import scan_text_for_forbidden_claims
from certgen.metrics.fid import frechet_distance


def test_fid_point_estimate_computes_on_synthetic_features():
    x = np.zeros((8, 3))
    y = np.ones((8, 3))
    assert frechet_distance(x, y) >= 0


def test_fid_certificate_claims_are_blocked():
    with pytest.raises(ValueError):
        assert_no_rigorous_fid_claim({"metric_label": "fid_inception", "rigorous_anytime_certificate": True})
    with pytest.raises(ValueError):
        assert_no_rigorous_fid_claim({"metric_label": "fd_dinov2", "decision": "A_certified_better"})


def test_fid_policy_summary_and_claim_gate():
    summary = fid_policy_summary("fid_inception")
    assert summary["fid_rigor_status"] == "descriptive_only"
    assert summary["rigorous_anytime_certificate_allowed"] is False
    decision = scan_text_for_forbidden_claims("FID-certified winner", evidence_status="smoke_only")
    assert not decision.passed
