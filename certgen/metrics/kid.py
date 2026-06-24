"""KID-style wrappers over polynomial MMD."""

from __future__ import annotations

import numpy as np

from certgen.metrics.mmd import block_mmd2_estimates, delta_stream_from_blocks, unbiased_mmd2


def kid_polynomial(x: np.ndarray, y: np.ndarray, *, degree: int = 3, gamma: float | None = None, coef0: float = 1.0) -> float:
    return unbiased_mmd2(x, y, kernel="poly", degree=degree, gamma=gamma, coef0=coef0)


def kid_block_estimates(x: np.ndarray, y: np.ndarray, *, block_size: int = 16) -> list[float]:
    return block_mmd2_estimates(x, y, block_size=block_size, kernel="poly")


def kid_delta_stream(model_a: np.ndarray, model_b: np.ndarray, reference: np.ndarray, *, block_size: int = 16) -> list[float]:
    return delta_stream_from_blocks(model_a, model_b, reference, block_size=block_size, kernel="poly")
