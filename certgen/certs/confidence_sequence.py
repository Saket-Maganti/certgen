"""Legacy confidence-sequence adapter used by V1-style certificates."""

from __future__ import annotations

from dataclasses import dataclass
from math import log, pi, sqrt
from typing import Iterable

from certgen.stats.cs import confidence_sequence
from certgen.stats.design_contracts import CSConfig


@dataclass
class CSState:
    n: int
    mean: float
    lower: float
    upper: float
    alpha: float
    method: str
    optional_stopping_valid: bool


def _radius(n: int, alpha: float, width: float) -> float:
    # Union-bound Hoeffding radius with sum_n 6/(pi^2 n^2) <= 1.
    return width * sqrt(log((pi * pi * n * n) / (3.0 * alpha)) / (2.0 * n))


def update_empirical_bernstein_cs(
    values: Iterable[float],
    alpha: float,
    value_range: tuple[float, float] | None = None,
) -> list[CSState]:
    """Return legacy CS states.

    The public name is retained for old callers. With declared fixed bounds it
    now routes to the bounded betting e-process CS used by the clean R0 path.
    Without declared bounds it keeps the old observed-range smoke fallback and
    explicitly marks the result as not optional-stopping-valid.
    """

    values = [float(value) for value in values]
    if value_range is not None:
        low, high = value_range
        result = confidence_sequence(
            values,
            CSConfig(alpha=alpha, budget_units=len(values), lower_bound=float(low), upper_bound=float(high), method="betting"),
        )
        return [
            CSState(
                n=int(state["n"]),
                mean=float(state["mean"]),
                lower=float(state["lower"]),
                upper=float(state["upper"]),
                alpha=float(alpha),
                method=result.method_label,
                optional_stopping_valid=True,
            )
            for state in result.states
        ]

    states: list[CSState] = []
    running_sum = 0.0
    observed_min = float("inf")
    observed_max = float("-inf")
    for index, value in enumerate(values, start=1):
        running_sum += value
        observed_min = min(observed_min, value)
        observed_max = max(observed_max, value)
        mean = running_sum / index
        width = max(1e-12, observed_max - observed_min)
        optional_stopping_valid = False
        method = "observed_range_hoeffding_smoke_not_time_uniform"
        radius = _radius(index, alpha, width)
        states.append(
            CSState(
                n=index,
                mean=float(mean),
                lower=float(mean - radius),
                upper=float(mean + radius),
                alpha=float(alpha),
                method=method,
                optional_stopping_valid=optional_stopping_valid,
            )
        )
    return states
