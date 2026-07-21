"""Betting e-values for the point null Delta = 0.

The clean-core comparison stream estimates Delta_AB = d(A, R) - d(B, R) with
per-unit values in a known bounded range. Testing whether a comparison is
The betting process evaluated at one fixed null mean is a genuine e-value when
the bounded stream satisfies ``E[Delta_t | F_{t-1}] = null_mean``.  Such a
point-null e-value can be supplied to e-BH at a fixed, predeclared analysis time.
It rejects equality only: it does not by itself certify a direction, a ranking,
or globally stopped FDR control across dependent streams.

The finite-grid interval in :mod:`certgen.stats.cs` is experimental and has a
separate unresolved continuum-inversion obligation.  No equivalence between
that interval and this point-null e-value is asserted.
"""

from __future__ import annotations

import numpy as np

from certgen.stats.bounds import validate_alpha, validate_bounds
from certgen.stats.cs import _betting_lambdas, _logmeanexp
from certgen.stats.design_contracts import CSConfig


def _scaled_null(values: list[float], config: CSConfig, null_mean: float) -> tuple[np.ndarray, float]:
    validate_bounds(config.lower_bound, config.upper_bound)
    width = config.upper_bound - config.lower_bound
    q0 = (null_mean - config.lower_bound) / width
    if not (0.0 < q0 < 1.0):
        raise ValueError("null mean must lie strictly inside the declared stream bounds")
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise ValueError("at least one stream value is required for an e-value")
    if not np.all(np.isfinite(arr)):
        raise ValueError("stream values must be finite")
    if np.any(arr < config.lower_bound) or np.any(arr > config.upper_bound):
        raise ValueError("stream value outside provided bounds")
    scaled = (arr - config.lower_bound) / width
    return scaled, q0


def betting_e_process(values: list[float], config: CSConfig, null_mean: float = 0.0) -> list[float]:
    """Running e-values e_1, ..., e_n for the point null E[Delta] = null_mean.

    Each e_t is the uniform mixture (over fixed betting fractions) of test
    martingales for H0, accumulated through time t. The process is an e-process,
    so any *fixed* or data-dependent stopped value e_tau satisfies E[e_tau] <= 1.
    """

    validate_alpha(config.alpha)
    scaled, q0 = _scaled_null(values[: config.budget_units], config, null_mean)
    lambdas = _betting_lambdas(np.asarray([q0]))  # shape (1, num_fractions)
    log_capitals = np.zeros_like(lambdas)
    trajectory: list[float] = []
    for y in scaled:
        factors = np.maximum(1.0 + lambdas * (float(y) - q0), 1e-300)
        log_capitals = log_capitals + np.log(factors)
        log_e = _logmeanexp(log_capitals, axis=1)
        trajectory.append(float(np.exp(log_e[0])))
    return trajectory


def betting_e_value(values: list[float], config: CSConfig, null_mean: float = 0.0) -> float:
    """Terminal e-value for H0: E[Delta] = null_mean (a valid e-value, E <= 1)."""

    return betting_e_process(values, config, null_mean)[-1]


def e_value_decided(e_value: float, alpha: float) -> bool:
    """Legacy name: whether the point null is rejected at level ``alpha``.

    ``True`` must not be relabelled as a directional certificate without a
    separately valid directional confidence sequence or one-sided test.
    """

    validate_alpha(alpha)
    return float(e_value) >= 1.0 / alpha
