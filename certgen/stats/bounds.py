"""Conservative time-uniform bounds for bounded streams."""

from __future__ import annotations

from math import log, pi, sqrt


def validate_alpha(alpha: float) -> None:
    if not (0.0 < float(alpha) < 1.0):
        raise ValueError("alpha must be in (0, 1)")


def validate_bounds(lower: float, upper: float) -> None:
    if not lower < upper:
        raise ValueError("lower bound must be smaller than upper bound")


def hoeffding_union_radius(n: int, alpha: float, lower: float, upper: float) -> float:
    validate_alpha(alpha)
    validate_bounds(lower, upper)
    if n <= 0:
        raise ValueError("n must be positive")
    width = upper - lower
    return width * sqrt(log((pi * pi * n * n) / (3.0 * alpha)) / (2.0 * n))


def empirical_bernstein_radius(n: int, alpha: float, lower: float, upper: float, sample_variance: float) -> float:
    """Conservative practical empirical-Bernstein-style radius.

    Assumptions: bounded observations in [lower, upper]. This is a practical
    V2 bound with an explicit union schedule, not a new theoretical result.
    """

    validate_alpha(alpha)
    validate_bounds(lower, upper)
    if n <= 1:
        return hoeffding_union_radius(max(1, n), alpha, lower, upper)
    width = upper - lower
    log_term = log((pi * pi * n * n) / (3.0 * alpha))
    return sqrt((2.0 * max(sample_variance, 0.0) * log_term) / n) + (3.0 * width * log_term) / max(1, n - 1)
