from certgen.cvpr.synthetic_validation import run_extended_synthetic_validation


def test_extended_synthetic_lane_is_bounded_nonclaim_and_reports_uncertainty() -> None:
    result = run_extended_synthetic_validation(repetitions=12, budget_units=100, seed=9)
    assert result["synthetic_validation_only"] is True
    assert result["not_model_evidence"] is True
    assert result["claim_allowed"] is False
    assert len(result["null_rate_wilson_95"]) == 2
    assert result["positive_false_direction_count"] == 0
    assert result["negative_false_direction_count"] == 0
