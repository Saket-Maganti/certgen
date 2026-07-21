"""Auditable scalar form of the bounded RBF comparison contribution."""

from __future__ import annotations

import math
from typing import Iterable


KERNEL_LOWER = 0.0
KERNEL_UPPER = 1.0
CONTRIBUTION_LOWER = -3.0
CONTRIBUTION_UPPER = 3.0


def direct_mmd_difference_contribution(
    k_aa: float,
    k_bb: float,
    k_ar_1: float,
    k_ar_2: float,
    k_br_1: float,
    k_br_2: float,
) -> float:
    """Return kAA-kBB-kAR1-kAR2+kBR1+kBR2 with fail-closed checks."""

    terms: Iterable[float] = (k_aa, k_bb, k_ar_1, k_ar_2, k_br_1, k_br_2)
    clean = [float(value) for value in terms]
    if any(not math.isfinite(value) for value in clean):
        raise ValueError("kernel terms must be finite")
    if any(value < KERNEL_LOWER or value > KERNEL_UPPER for value in clean):
        raise ValueError("bounded RBF kernel terms must lie in [0,1]")
    value = clean[0] - clean[1] - clean[2] - clean[3] + clean[4] + clean[5]
    if value < CONTRIBUTION_LOWER or value > CONTRIBUTION_UPPER:  # pragma: no cover - algebraic guard
        raise AssertionError("direct MMD difference contribution escaped [-3,3]")
    return value
