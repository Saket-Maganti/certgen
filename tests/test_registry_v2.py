from certgen.registry.validate import read_csv, validate_claim_rows, validate_model_pair_rows


def test_v2_registry_templates_validate_as_incomplete_but_not_fabricated():
    rows = read_csv("registry/templates/candidate_model_pairs_template.csv")
    errors = validate_model_pair_rows(rows)
    assert rows[0]["audit_eligibility"] == "needs_user_verification"
    assert not any("eligible row has blockers" in error for error in errors)
    claims = read_csv("registry/templates/reported_metric_claims_template.csv")
    assert validate_claim_rows(claims) == []


def test_v2_registry_blocks_malformed_eligible_row():
    row = {
        "comparison_id": "cmp",
        "benchmark_id": "bench",
        "model_a_id": "a",
        "model_b_id": "b",
        "paper_or_source_id": "source",
        "reported_metric_name": "TBD",
        "reported_metric_a": "bad",
        "reported_metric_b": "1.0",
        "reported_sample_size": "",
        "reported_preprocessing_note": "unknown",
        "released_samples_a_status": "unknown",
        "released_samples_b_status": "available",
        "checkpoint_a_status": "unknown",
        "checkpoint_b_status": "unknown",
        "feature_cache_status": "missing",
        "license_status": "unknown",
        "audit_eligibility": "eligible",
        "blocker_reason": "",
    }
    errors = validate_model_pair_rows([row])
    assert any("eligible row has blockers" in error for error in errors)
    assert any("reported_metric_a malformed" in error for error in errors)


def test_v2_registry_comparison_id_unique():
    base = {
        "comparison_id": "dup",
        "benchmark_id": "bench",
        "model_a_id": "a",
        "model_b_id": "b",
        "paper_or_source_id": "source",
        "reported_metric_name": "kid",
        "reported_metric_a": "1",
        "reported_metric_b": "2",
        "reported_sample_size": "100",
        "reported_preprocessing_note": "resize explicit",
        "released_samples_a_status": "available",
        "released_samples_b_status": "available",
        "checkpoint_a_status": "unknown",
        "checkpoint_b_status": "unknown",
        "feature_cache_status": "available",
        "license_status": "verified",
        "audit_eligibility": "eligible",
        "blocker_reason": "",
    }
    errors = validate_model_pair_rows([base, dict(base)])
    assert any("comparison_id not unique" in error for error in errors)
