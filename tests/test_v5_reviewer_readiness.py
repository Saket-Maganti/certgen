from certgen.audit.cvpr_readiness import audit_cvpr_readiness
from certgen.audit.reviewer_harness_audit import audit_reviewer_harness
from certgen.review.reviewer_simulator import reviewer_attack_bank, simulate_v5_scorecard


def test_v5_reviewer_harness_and_scorecard():
    review = audit_reviewer_harness()
    assert review["passed"]
    assert review["attacks"] >= 15
    assert any("descriptive-only" in card["response"] for card in reviewer_attack_bank() if "FID" in card["attack"])
    assert simulate_v5_scorecard(False)["empirical_strength"] == "blocked_until_real_runs"


def test_v5_cvpr_readiness_blocks_no_results_high_score():
    readiness = audit_cvpr_readiness(False)
    assert readiness["passed"]
    assert readiness["scores"]["empirical_evidence_actual_status"] <= 2
    assert "claim gates allow fake evidence" in readiness["kill_list"]
