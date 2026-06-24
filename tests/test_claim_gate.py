from certgen.gates.claim_gate import scan_text_for_forbidden_claims


def test_claim_gate_blocks_forbidden_phrases():
    text = "We find that model A beats model B and report a certified result."
    decision = scan_text_for_forbidden_claims(text, evidence_status="non_evidence_smoke")
    assert not decision.passed
    assert "we find that" in decision.violations
    assert "certified result" in decision.violations


def test_claim_gate_allows_cautious_non_evidence_wording():
    text = "This smoke artifact is a non-evidence toy placeholder for contract validation."
    decision = scan_text_for_forbidden_claims(text, evidence_status="non_evidence_smoke")
    assert decision.passed


def test_claim_gate_blocks_forbidden_fid_phrases():
    text = "This is a rigorous FID certificate."
    decision = scan_text_for_forbidden_claims(text, evidence_status="non_evidence_smoke")
    assert not decision.passed
    assert "rigorous fid certificate" in decision.violations
