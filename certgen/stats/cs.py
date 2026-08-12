"""Confidence sequences for bounded comparison streams."""

from __future__ import annotations

from math import log

import numpy as np

from certgen.stats.bounds import (
    empirical_bernstein_radius,
    hoeffding_union_radius,
    validate_alpha,
    validate_bounds,
    validate_budget_units,
)
from certgen.stats.design_contracts import CSConfig, CSResult


def _validate_values(values: list[float], lower: float, upper: float) -> list[float]:
    validate_bounds(lower, upper)
    clean = [float(value) for value in values]
    if not clean:
        raise ValueError("at least one stream value is required")
    for value in clean:
        if not np.isfinite(value):
            raise ValueError("stream values must be finite")
        if value < lower or value > upper:
            raise ValueError("stream value outside provided bounds")
    return clean


def confidence_sequence(values: list[float], config: CSConfig) -> CSResult:
    validate_alpha(config.alpha)
    validate_budget_units(config.budget_units)
    values = _validate_values(values[: config.budget_units], config.lower_bound, config.upper_bound)
    if config.method in {"betting", "betting_mixture", "betting_cs"}:
        return betting_cs(values, config)
    if config.method in {"hoeffding", "time_uniform_hoeffding"}:
        return hoeffding_cs(values, config)
    if config.method in {"empirical_bernstein", "empirical_bernstein_conservative"}:
        return empirical_bernstein_cs(values, config)
    raise ValueError(f"unsupported CS method: {config.method}")


def hoeffding_cs(values: list[float], config: CSConfig) -> CSResult:
    states: list[dict[str, float]] = []
    running_sum = 0.0
    for n, value in enumerate(values, start=1):
        running_sum += value
        mean = running_sum / n
        radius = hoeffding_union_radius(n, config.alpha, config.lower_bound, config.upper_bound)
        states.append({"n": float(n), "mean": mean, "lower": mean - radius, "upper": mean + radius})
    final = states[-1]
    return CSResult(
        method_label="time_uniform_hoeffding_union_bound_v3",
        theory_status="valid_for_bounded_conditionally_mean_stationary_streams",
        time_uniform=True,
        sample_units_seen=len(values),
        budget_units=config.budget_units,
        mean_estimate=final["mean"],
        lower=final["lower"],
        upper=final["upper"],
        states=states,
    )


def empirical_bernstein_cs(values: list[float], config: CSConfig) -> CSResult:
    states: list[dict[str, float]] = []
    running: list[float] = []
    for n, value in enumerate(values, start=1):
        running.append(value)
        mean = float(np.mean(running))
        variance = float(np.var(running, ddof=1)) if n > 1 else 0.0
        radius = empirical_bernstein_radius(n, config.alpha, config.lower_bound, config.upper_bound, variance)
        states.append({"n": float(n), "mean": mean, "lower": mean - radius, "upper": mean + radius})
    final = states[-1]
    return CSResult(
        method_label="empirical_bernstein_diagnostic_v3",
        theory_status="diagnostic_only_proof_obligation_unresolved",
        time_uniform=False,
        sample_units_seen=len(values),
        budget_units=config.budget_units,
        mean_estimate=final["mean"],
        lower=final["lower"],
        upper=final["upper"],
        states=states,
    )


def _logmeanexp(log_values: np.ndarray, axis: int = 1) -> np.ndarray:
    max_value = np.max(log_values, axis=axis, keepdims=True)
    shifted = np.exp(log_values - max_value)
    return np.squeeze(max_value, axis=axis) + np.log(np.mean(shifted, axis=axis))


def _betting_lambdas(q_grid: np.ndarray) -> np.ndarray:
    fractions = np.asarray([-0.9, -0.75, -0.5, -0.25, -0.1, 0.1, 0.25, 0.5, 0.75, 0.9], dtype=float)
    q = np.clip(q_grid[:, None], 1e-6, 1.0 - 1e-6)
    frac = fractions[None, :]
    return np.where(frac > 0.0, frac / q, frac / (1.0 - q))


def betting_cs(values: list[float], config: CSConfig) -> CSResult:
    """Experimental finite-grid inversion of bounded-mean e-processes.

    For each candidate mean q on the [0, 1] scale, the process mixes fixed
    nonnegative bets of the form prod_t (1 + lambda (Y_t - q)). Each component
    is a test martingale under E[Y_t | past] = q when Y_t is in [0, 1], and the
    uniform mixture remains an e-process *at that candidate q*.  The current
    implementation evaluates only a finite grid and fills the hull of accepted
    grid points.  No continuum-coverage proof for that numerical inversion is
    implemented, so this result is deliberately not labelled time-uniform and
    must not issue a directional certificate.  The point-null e-value helper in
    :mod:`certgen.stats.e_values` has a narrower, separately documented scope.
    """

    validate_alpha(config.alpha)
    validate_bounds(config.lower_bound, config.upper_bound)
    validate_budget_units(config.budget_units)
    values = _validate_values(values[: config.budget_units], config.lower_bound, config.upper_bound)
    width = config.upper_bound - config.lower_bound
    scaled = (np.asarray(values, dtype=float) - config.lower_bound) / width
    grid_size = 2001
    q_grid = np.linspace(1e-6, 1.0 - 1e-6, grid_size)
    q_step = float(q_grid[1] - q_grid[0])
    lambdas = _betting_lambdas(q_grid)
    log_capitals = np.zeros_like(lambdas)
    threshold = log(1.0 / config.alpha)
    states: list[dict[str, float]] = []
    running_sum = 0.0
    zero_q = None
    if config.lower_bound <= 0.0 <= config.upper_bound:
        zero_q = (0.0 - config.lower_bound) / width
        zero_index = int(np.argmin(np.abs(q_grid - zero_q)))
    else:
        zero_index = None

    for n, y in enumerate(scaled, start=1):
        running_sum += float(values[n - 1])
        factors = 1.0 + lambdas * (float(y) - q_grid[:, None])
        if np.any(factors <= 0.0):
            factors = np.maximum(factors, 1e-300)
        log_capitals += np.log(factors)
        log_e_values = _logmeanexp(log_capitals, axis=1)
        accepted = log_e_values < threshold
        mean = running_sum / n
        if np.any(accepted):
            accepted_q = q_grid[accepted]
            lower_q = max(0.0, float(accepted_q[0] - q_step))
            upper_q = min(1.0, float(accepted_q[-1] + q_step))
        else:
            mean_q = (mean - config.lower_bound) / width
            lower_q = upper_q = min(1.0, max(0.0, mean_q))
        lower = config.lower_bound + width * lower_q
        upper = config.lower_bound + width * upper_q
        state = {
            "n": float(n),
            "mean": float(mean),
            "lower": float(lower),
            "upper": float(upper),
        }
        if zero_index is not None:
            state["log_e_value_at_zero"] = float(log_e_values[zero_index])
        states.append(state)

    final = states[-1]
    return CSResult(
        method_label="betting_mixture_finite_grid_diagnostic_v3",
        theory_status="experimental_grid_inversion_continuum_coverage_unresolved",
        time_uniform=False,
        sample_units_seen=len(values),
        budget_units=config.budget_units,
        mean_estimate=final["mean"],
        lower=final["lower"],
        upper=final["upper"],
        states=states,
    )
