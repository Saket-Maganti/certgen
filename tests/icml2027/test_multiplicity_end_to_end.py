from __future__ import annotations

from certgen.icml2027.multiplicity import adjust_pvalues, edge_alpha_allocation


def test_hand_computable_bonferroni_and_fixed_split() -> None:
    values = [0.01, 0.02, 0.20]
    for method in ("bonferroni", "fixed_alpha_split"):
        result = adjust_pvalues(values, method, alpha=0.06)
        assert result["adjusted_pvalues"] == [0.03, 0.06, 0.6000000000000001]
        assert result["rejected"] == [True, True, False]
    assert edge_alpha_allocation(3, "bonferroni", alpha=0.06) == [0.02, 0.02, 0.02]


def test_hand_computable_holm_step_down() -> None:
    result = adjust_pvalues([0.01, 0.03, 0.20], "holm", alpha=0.05)
    assert result["adjusted_pvalues"] == [0.03, 0.06, 0.2]
    assert result["rejected"] == [True, False, False]


def test_bh_is_explicitly_exploratory() -> None:
    result = adjust_pvalues([0.01, 0.03, 0.20], "benjamini_hochberg_exploratory", alpha=0.05)
    assert result["validity_status"] == "EXPLORATORY_NOT_CONFIRMATORY"
    assert result["claim_allowed"] is False
