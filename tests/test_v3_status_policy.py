from certgen.core.status import evaluate_claim_policy, validate_v3_evidence_status


def test_v3_statuses_known_and_claims_blocked():
    assert validate_v3_evidence_status("dry_run_only")
    assert not validate_v3_evidence_status("mystery_status")
    assert not evaluate_claim_policy("smoke_only", True).passed
    assert evaluate_claim_policy("real_pilot_claim_eligible", True).passed
