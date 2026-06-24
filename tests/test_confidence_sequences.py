import pytest

from certgen.stats.cs import confidence_sequence
from certgen.stats.design_contracts import CSConfig


def test_interval_shrinks_with_more_identical_bounded_data():
    short = confidence_sequence([-0.4] * 8, CSConfig(alpha=0.05, budget_units=8, lower_bound=-1, upper_bound=1))
    long = confidence_sequence([-0.4] * 64, CSConfig(alpha=0.05, budget_units=64, lower_bound=-1, upper_bound=1))
    assert (long.upper - long.lower) < (short.upper - short.lower)


def test_alpha_and_bound_validation():
    with pytest.raises(ValueError):
        confidence_sequence([0.0], CSConfig(alpha=0, budget_units=1, lower_bound=-1, upper_bound=1))
    with pytest.raises(ValueError):
        confidence_sequence([0.0], CSConfig(alpha=0.05, budget_units=1, lower_bound=1, upper_bound=-1))


def test_unbounded_or_out_of_bounds_data_rejected():
    with pytest.raises(ValueError, match="outside"):
        confidence_sequence([2.0], CSConfig(alpha=0.05, budget_units=1, lower_bound=-1, upper_bound=1))


def test_empirical_bernstein_metadata_present():
    result = confidence_sequence(
        [-0.2, -0.1, -0.3, -0.2],
        CSConfig(alpha=0.05, budget_units=4, lower_bound=-1, upper_bound=1, method="empirical_bernstein"),
    )
    assert result.time_uniform is True
    assert result.method_label == "empirical_bernstein_conservative_v2"
    assert result.theory_status == "conservative_practical"
