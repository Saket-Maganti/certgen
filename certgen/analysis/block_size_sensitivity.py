"""Block-size sensitivity for clean-core decision certificates.

The linear-time MMD difference stream averages per-pair kernel contributions
into blocks. Larger blocks reduce the number of (still independent) stream units
but lower their variance; smaller blocks give more units with higher variance.
The decision time and final interval therefore depend on block size, and the
"compute savings" story is only credible if it is shown to be robust to this
choice rather than tuned. This module sweeps block sizes on *already-loaded*
feature arrays -- it never fetches, generates, or extracts anything.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from certgen.analysis.samples_to_decision import samples_to_decision_from_states
from certgen.metrics.streams import mmd_difference_stream
from certgen.stats.cs import confidence_sequence
from certgen.stats.design_contracts import CSConfig


def block_size_sensitivity(
    features_a: np.ndarray,
    features_b: np.ndarray,
    features_r: np.ndarray,
    *,
    kernel_config: dict | None = None,
    alpha: float = 0.05,
    block_sizes: list[int] | None = None,
    method: str = "hoeffding",
    seed: int = 0,
    comparison_id: str = "comparison",
) -> dict[str, Any]:
    kernel_config = kernel_config or {"name": "rbf", "normalize": "l2"}
    block_sizes = block_sizes or [1, 4, 16, 64]
    rows: list[dict[str, Any]] = []
    for block_size in block_sizes:
        bsize = None if int(block_size) <= 1 else int(block_size)
        stream = mmd_difference_stream(
            features_a,
            features_b,
            features_r,
            kernel_config,
            seed=seed,
            metric_label="mmd_rbf",
            comparison_id=comparison_id,
            block_size=bsize,
            require_bounded_kernel=True,
        )
        if stream.lower_bound is None or stream.upper_bound is None:
            raise ValueError("block-size sweep requires a bounded-kernel stream")
        config = CSConfig(
            alpha=alpha,
            budget_units=len(stream.values),
            lower_bound=stream.lower_bound,
            upper_bound=stream.upper_bound,
            method=method,
            seed=seed,
        )
        result = confidence_sequence(stream.values, config)
        decision_unit = samples_to_decision_from_states(result.states)
        contributions_at_decision = None
        if decision_unit is not None:
            contributions_at_decision = min(
                int(stream.metadata["num_contributions_consumed"]),
                int(decision_unit) * int(stream.metadata["block_size"]),
            )
        rows.append(
            {
                "block_size": int(block_size),
                "num_units": len(stream.values),
                "decided": decision_unit is not None,
                "samples_to_decision_units": decision_unit,
                # One linear-time contribution consumes two samples from each
                # of A, B, and R.  Preserve the legacy field with an explicit
                # per-distribution meaning and expose the total separately.
                "samples_to_decision_raw": None if contributions_at_decision is None else 2 * contributions_at_decision,
                "samples_to_decision_per_distribution": None if contributions_at_decision is None else 2 * contributions_at_decision,
                "total_feature_rows_to_decision": None if contributions_at_decision is None else 6 * contributions_at_decision,
                "final_lower": result.lower,
                "final_upper": result.upper,
                "final_width": result.upper - result.lower,
                "mean_estimate": result.mean_estimate,
            }
        )
    decided_flags = {row["decided"] for row in rows}
    return {
        "comparison_id": comparison_id,
        "alpha": float(alpha),
        "method": method,
        "kernel_config": kernel_config,
        "rows": rows,
        "decision_robust_across_block_sizes": len(decided_flags) == 1,
        "claim_allowed": False,
        "labels": ["sensitivity_diagnostic", "not_paper_claim"],
    }
