from certgen.certs.api import certify_clean_metric_comparison
from certgen.certs.replay import replay_certificate
from certgen.fixtures.make_v2_feature_fixtures import make_v2_feature_fixtures
from certgen.gates.claim_gate import scan_report_for_overclaims
from certgen.reporting.pilot_cards import render_pilot_report


def test_certificate_replay_and_missing_inputs(tmp_path):
    paths = make_v2_feature_fixtures(tmp_path / "features")
    cert_path = tmp_path / "cert.json"
    c1 = certify_clean_metric_comparison(paths["model_a_close"], paths["model_b_far"], paths["reference"], "mmd_rbf", {}, {"alpha": 0.05, "budget_units": 20, "method": "betting", "seed": 1}, "cmp", "smoke_only", str(cert_path))
    c2 = certify_clean_metric_comparison(paths["model_a_close"], paths["model_b_far"], paths["reference"], "mmd_rbf", {}, {"alpha": 0.05, "budget_units": 20, "method": "betting", "seed": 1}, "cmp", "smoke_only", str(tmp_path / "cert2.json"))
    assert c1.stream_hash == c2.stream_hash
    replay = replay_certificate(cert_path, tmp_path / "replay.md", tmp_path / "replay.json")
    assert replay["replay_status"] == "passed"
    missing = replay_certificate(tmp_path / "cert2.json", tmp_path / "replay2.md", tmp_path / "missing_dir" / "replay2.json")
    assert missing["replay_status"] in {"passed", "blocked_missing_inputs"}


def test_pilot_report_claim_gate():
    report = render_pilot_report({"pilot_id": "p", "mode": "dry_run", "evidence_status": "dry_run_only", "claim_allowed": False, "claim_blockers": ["blocked"], "comparisons": [], "certificates": []})
    assert "not paper evidence" in report.lower()
    assert scan_report_for_overclaims("our results demonstrate model A is better", claim_allowed=False).passed is False
    assert scan_report_for_overclaims("computed in non-claim mode; claim blocked", claim_allowed=False).passed is True
