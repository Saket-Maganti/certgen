from __future__ import annotations

import numpy as np

from certgen.icml2027.production_mmd import _scenario_arrays, evaluate_production_contributions
from certgen.metrics.streams import mmd_difference_stream
from certgen.stats.cs import confidence_sequence
from certgen.stats.design_contracts import CSConfig


def test_highdim_generator_to_production_stream_to_cs_exact_parity() -> None:
    rng = np.random.default_rng(2027)
    a, b, r, expected = _scenario_arrays("covariance_perturbation", 250, 64, rng)
    stream = mmd_difference_stream(
        a,
        b,
        r,
        {"name": "rbf", "gamma": 0.5, "normalize": "l2"},
        seed=99,
        kernel_chunk_size=17,
    )
    simulator = evaluate_production_contributions(stream.values, alpha=0.05)
    production = confidence_sequence(
        stream.values,
        CSConfig(
            alpha=0.05,
            budget_units=len(stream.values),
            lower_bound=-3.0,
            upper_bound=3.0,
            method="hoeffding",
            seed=0,
        ),
    )
    assert expected == "A_BETTER"
    assert simulator["states"] == production.states
    assert simulator["method_label"] == production.method_label
