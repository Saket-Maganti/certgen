"""Explicit familywise and exploratory multiplicity allocations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def adjust_pvalues(pvalues: Sequence[float], method: str, *, alpha: float = 0.05) -> dict[str, Any]:
    values = [float(value) for value in pvalues]
    if not values or any(not 0.0 <= value <= 1.0 for value in values):
        raise ValueError("p-values must form a non-empty sequence in [0,1]")
    m = len(values)
    rejected = [False] * m
    adjusted = [1.0] * m
    validity = "VALIDITY_PROVEN"
    if method in {"bonferroni", "fixed_alpha_split"}:
        for index, value in enumerate(values):
            adjusted[index] = min(1.0, value * m)
            rejected[index] = value <= alpha / m
    elif method == "holm":
        order = sorted(range(m), key=values.__getitem__)
        running = 0.0
        still_rejecting = True
        for rank, index in enumerate(order):
            candidate = min(1.0, (m - rank) * values[index])
            running = max(running, candidate)
            adjusted[index] = running
            rejected[index] = still_rejecting and values[index] <= alpha / (m - rank)
            still_rejecting = still_rejecting and rejected[index]
    elif method == "benjamini_hochberg_exploratory":
        validity = "EXPLORATORY_NOT_CONFIRMATORY"
        order = sorted(range(m), key=values.__getitem__)
        threshold_rank = 0
        for rank, index in enumerate(order, start=1):
            if values[index] <= alpha * rank / m:
                threshold_rank = rank
        for rank, index in enumerate(order, start=1):
            rejected[index] = rank <= threshold_rank
        running = 1.0
        for rank, index in reversed(list(enumerate(order, start=1))):
            running = min(running, values[index] * m / rank)
            adjusted[index] = min(1.0, running)
    else:
        raise ValueError(f"unsupported multiplicity method: {method}")
    return {
        "method": method,
        "alpha": alpha,
        "raw_pvalues": values,
        "adjusted_pvalues": adjusted,
        "rejected": rejected,
        "validity_status": validity,
        "claim_allowed": False,
    }


def edge_alpha_allocation(edge_count: int, method: str, *, alpha: float = 0.05) -> list[float]:
    if edge_count <= 0:
        raise ValueError("edge_count must be positive")
    if method not in {"bonferroni", "fixed_alpha_split"}:
        raise ValueError("only fixed conservative edge allocations are supported")
    return [alpha / edge_count] * edge_count
