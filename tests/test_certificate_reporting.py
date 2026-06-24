import pytest

from certgen.certs.api import certify_clean_metric_comparison
from certgen.core.io import read_json
from certgen.fixtures.make_v2_feature_fixtures import make_v2_feature_fixtures
from certgen.reporting.certificate_card import render_certificate_card


def test_certificate_card_contains_not_evidence_warning(tmp_path):
    paths = make_v2_feature_fixtures(tmp_path / "features")
    out = tmp_path / "cert.json"
    certify_clean_metric_comparison(
        paths["model_a_close"],
        paths["model_b_far"],
        paths["reference"],
        "mmd_rbf",
        {},
        {"alpha": 0.05, "budget_units": 16, "method": "betting"},
        "card",
        "smoke_only",
        str(out),
    )
    card = render_certificate_card(read_json(out))
    assert "NOT PAPER EVIDENCE" in card
    assert "Claim allowed: `False`" in card
    assert "published wins are undecided" not in card.lower()


def test_certificate_card_fid_warning_and_malformed_rejection():
    cert = {
        "comparison_id": "fid",
        "metric_label": "fid_inception",
        "feature_hashes": {},
        "evidence_status": "descriptive_only",
        "method_label": "descriptive",
        "theory_status": "descriptive_only",
        "alpha": 0.05,
        "budget_units": 0,
        "sample_units_seen": 0,
        "mean_estimate": 0.0,
        "lower": None,
        "upper": None,
        "decision": "descriptive_only",
        "claim_allowed": False,
        "limitations": ["NO_REAL_EVIDENCE"],
    }
    card = render_certificate_card(cert)
    assert "FID-like metrics are descriptive-only" in card
    with pytest.raises(ValueError, match="malformed"):
        render_certificate_card({"comparison_id": "bad"})
