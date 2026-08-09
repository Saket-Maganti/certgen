"""Conservative sequential and fixed-budget mean-decision primitives."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np


DECISIONS = {"A_BETTER", "B_BETTER", "PRACTICALLY_EQUIVALENT", "UNRESOLVED", "INVALID"}


@dataclass(frozen=True)
class DecisionTrace:
    decision: str
    stopping_time: int
    mean: float
    lower: float
    upper: float
    confidence_width: float
    coverage: bool


def _radius(n: int, alpha: float, value_range: float = 2.0) -> float:
    if n <= 0 or not 0.0 < alpha < 1.0:
        raise ValueError("n must be positive and alpha must be in (0,1)")
    return value_range * math.sqrt(math.log(2.0 / alpha) / (2.0 * n))


def fixed_radius(n: int, alpha: float, value_range: float = 2.0) -> float:
    return _radius(n, alpha, value_range)


def anytime_radius(n: int, alpha: float, value_range: float = 2.0) -> float:
    # Union bound with delta_n = alpha / (n(n+1)); sum_n delta_n = alpha.
    return _radius(n, alpha / (n * (n + 1)), value_range)


def alpha_spending_radius(n: int, look_index: int, alpha: float, looks: int, value_range: float = 2.0) -> float:
    if not 1 <= look_index <= looks:
        raise ValueError("look_index must identify a scheduled look")
    weights = np.asarray([1.0 / (index * (index + 1)) for index in range(1, looks + 1)], dtype=float)
    allocation = alpha * float(weights[look_index - 1] / weights.sum())
    return _radius(n, allocation, value_range)


def _decision(lower: float, upper: float, margin: float | None) -> str:
    if upper < 0.0:
        return "A_BETTER"
    if lower > 0.0:
        return "B_BETTER"
    if margin is not None and lower >= -margin and upper <= margin:
        return "PRACTICALLY_EQUIVALENT"
    return "UNRESOLVED"


def evaluate_stream(
    values: Sequence[float] | np.ndarray,
    *,
    alpha: float,
    rule: str,
    looks: Iterable[int] | None = None,
    true_mean: float = 0.0,
    equivalence_margin: float | None = None,
) -> DecisionTrace:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or not len(array) or not np.all(np.isfinite(array)):
        return DecisionTrace("INVALID", 0, math.nan, math.nan, math.nan, math.nan, False)
    if np.any(array < -1.0) or np.any(array > 1.0):
        return DecisionTrace("INVALID", 0, math.nan, math.nan, math.nan, math.nan, False)
    selected_looks = looks if looks is not None else range(1, len(array) + 1)
    scheduled = sorted(set(int(value) for value in selected_looks if 1 <= int(value) <= len(array)))
    if not scheduled or scheduled[-1] != len(array):
        scheduled.append(len(array))
    cumulative = np.cumsum(array, dtype=float)
    covered_all = True
    latest = (float(array.mean()), -math.inf, math.inf)
    for look_index, n in enumerate(scheduled, start=1):
        mean = float(cumulative[n - 1] / n)
        if rule == "anytime":
            radius = anytime_radius(n, alpha)
        elif rule == "naive_repeated":
            radius = fixed_radius(n, alpha)
        elif rule == "alpha_spending":
            radius = alpha_spending_radius(n, look_index, alpha, len(scheduled))
        elif rule == "fixed_n":
            if n != scheduled[-1]:
                continue
            radius = fixed_radius(n, alpha)
        else:
            raise ValueError(f"unsupported stopping rule: {rule}")
        lower, upper = mean - radius, mean + radius
        covered_all = covered_all and lower <= true_mean <= upper
        latest = (mean, lower, upper)
        decision = _decision(lower, upper, equivalence_margin)
        if decision != "UNRESOLVED":
            return DecisionTrace(decision, n, mean, lower, upper, upper - lower, covered_all)
    mean, lower, upper = latest
    return DecisionTrace("UNRESOLVED", len(array), mean, lower, upper, upper - lower, covered_all)
