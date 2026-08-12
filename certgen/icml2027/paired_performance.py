"""Deterministic time/memory audit for paired RBF evaluation."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import numpy as np

from certgen.icml2027.common import write_csv
from certgen.metrics.kernels import rbf_kernel, rbf_kernel_paired


def run_paired_performance_audit(out_path: str | Path, *, seed: int = 20270812) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    cases = {(n, d) for n in (2, 10, 100, 1000) for d in (2, 16, 64, 768, 2048)}
    cases.update((n, d) for n in (1000, 2000, 4000, 8000, 10000) for d in (64, 768, 2048))
    for n, dimension in sorted(cases):
        rng = np.random.default_rng(seed + n + dimension)
        x = rng.normal(size=(n, dimension)).astype(np.float32)
        y = rng.normal(size=(n, dimension)).astype(np.float32)
        chunk_size = min(512, n)
        started = time.perf_counter()
        result = rbf_kernel_paired(x, y, gamma=0.5, chunk_size=chunk_size)
        paired_seconds = time.perf_counter() - started
        parity_max_abs = None
        matrix_seconds = None
        if n <= 100:
            matrix_started = time.perf_counter()
            expected = np.diag(rbf_kernel(x, y, gamma=0.5))
            matrix_seconds = time.perf_counter() - matrix_started
            parity_max_abs = float(np.max(np.abs(result - expected)))
        item_size = np.dtype(np.float64).itemsize
        paired_extra_bound = (2 * chunk_size * dimension + n) * item_size
        matrix_extra = n * n * item_size
        rows.append(
            {
                "n": n,
                "dimension": dimension,
                "dtype": "float32_inputs_float64_accumulation",
                "chunk_size": chunk_size,
                "paired_seconds": paired_seconds,
                "matrix_seconds_small_fixture_only": matrix_seconds,
                "parity_max_abs_small_fixture_only": parity_max_abs,
                "paired_extra_memory_upper_bound_bytes": paired_extra_bound,
                "full_gram_extra_memory_bytes": matrix_extra,
                "full_gram_to_paired_extra_memory_ratio": matrix_extra / max(1, paired_extra_bound),
                "finite": bool(np.all(np.isfinite(result))),
                "pairwise_matrix_materialized": False,
                "complexity": "O(ND)_time_O(chunk*D+N)_extra_memory",
                "claim_allowed": False,
            }
        )
    write_csv(out_path, rows)
    return {
        "passed": all(bool(row["finite"]) for row in rows)
        and all(
            row["parity_max_abs_small_fixture_only"] is None
            or float(row["parity_max_abs_small_fixture_only"]) < 2e-6
            for row in rows
        ),
        "cases": len(rows),
        "maximum_n": max(int(row["n"]) for row in rows),
        "maximum_dimension": max(int(row["dimension"]) for row in rows),
        "claim_allowed": False,
    }
