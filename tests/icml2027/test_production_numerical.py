from __future__ import annotations

from certgen.icml2027.numerical_reviewer import run_production_numerical_attacks


def test_production_numerical_reviewer_attacks(tmp_path) -> None:
    result = run_production_numerical_attacks(tmp_path)
    assert result["passed"]
    assert result["attacks_total"] >= 20
    assert result["claim_allowed"] is False
