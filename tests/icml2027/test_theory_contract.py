from __future__ import annotations

import math
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from certgen.icml2027.sequential import anytime_radius, fixed_radius


def test_anytime_boundary_matches_registered_union_hoeffding_formula() -> None:
    alpha = 0.05
    for n in (1, 2, 10, 100, 10_000):
        allocated_alpha = alpha / (n * (n + 1))
        expected = 2.0 * math.sqrt(math.log(2.0 / allocated_alpha) / (2.0 * n))
        assert anytime_radius(n, alpha) == expected
        assert anytime_radius(n, alpha) >= fixed_radius(n, alpha)


def test_union_schedule_spends_no_more_than_alpha() -> None:
    alpha = 0.05
    spent = sum(alpha / (n * (n + 1)) for n in range(1, 1_000_000))
    assert spent < alpha
    assert alpha - spent < 1e-6


def test_production_theory_contract_maps_every_required_object() -> None:
    root = Path(__file__).resolve().parents[2]
    contract = yaml.safe_load((root / "registry/icml2027/production_theory_contract.yaml").read_text())
    for field in (
        "random_variables",
        "filtration",
        "target_estimand",
        "paired_contribution_definition",
        "support_bound",
        "conditional_mean_assumption",
        "reference_sampling_assumption",
        "candidate_sampling_assumption",
        "independence_dependence_assumptions",
        "stopping_time_guarantee",
        "multiplicity_allocation",
        "validity_statement",
    ):
        assert contract[field]
    assert set(contract["unproven_extensions"].values()) == {"NOT_PROVEN"}
    assert contract["claim_allowed"] is False
