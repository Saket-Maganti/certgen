"""CMMD-style wrapper over CLIP-like feature arrays."""

from __future__ import annotations

import numpy as np

from certgen.metrics.mmd import block_mmd2_estimates, delta_stream_from_blocks, unbiased_mmd2


def cmmd_polynomial(x: np.ndarray, y: np.ndarray, *, degree: int = 3, gamma: float | None = None, coef0: float = 1.0) -> float:
    return unbiased_mmd2(x, y, kernel="poly", degree=degree, gamma=gamma, coef0=coef0)


def cmmd_rbf(x: np.ndarray, y: np.ndarray, *, gamma: float | None = None, normalize: str = "l2") -> float:
    return unbiased_mmd2(x, y, kernel="rbf", gamma=gamma, normalize=normalize)


def cmmd_block_estimates(x: np.ndarray, y: np.ndarray, *, block_size: int = 16) -> list[float]:
    return block_mmd2_estimates(x, y, block_size=block_size, kernel="rbf", normalize="l2")


def cmmd_delta_stream(model_a: np.ndarray, model_b: np.ndarray, reference: np.ndarray, *, block_size: int = 16) -> list[float]:
    return delta_stream_from_blocks(model_a, model_b, reference, block_size=block_size, kernel="rbf", normalize="l2")
