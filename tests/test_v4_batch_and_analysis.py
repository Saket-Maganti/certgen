from certgen.analysis.decidedness import build_decidedness_audit
from certgen.analysis.ranking_stability import build_ranking_stability
from certgen.certs.batch_certificate import run_batch_certificates
from certgen.certs.multiple_comparisons import allocate_alpha
from certgen.fixtures.make_v2_feature_fixtures import make_v2_feature_fixtures
from certgen.stats.dependence_diagnostics import dependence_warnings


def test_v4_batch_certificates_and_analysis_outputs(tmp_path):
    features = make_v2_feature_fixtures(tmp_path / "features", seed=7)
    config = {
        "alpha": 0.05,
        "alpha_policy": "bonferroni",
        "budget_units": 16,
        "method": "betting",
        "evidence_status": "synthetic_only",
        "metrics": ["mmd_rbf"],
        "comparisons": [
            {
                "comparison_id": "c1",
                "features_a": features["model_a_close"],
                "features_b": features["model_b_far"],
                "features_r": features["reference"],
                "shared_reference_id": "ref",
            },
            {
                "comparison_id": "c2",
                "features_a": features["model_equal_1"],
                "features_b": features["model_equal_2"],
                "features_r": features["reference"],
                "shared_reference_id": "ref",
            },
        ],
    }
    batch = run_batch_certificates(config, tmp_path / "batch.json", tmp_path / "batch.md")
    assert len(batch["rows"]) == 2
    assert batch["claim_allowed"] is False
    assert batch["multiple_comparison_policy"]["adjusted_for_multiplicity"]

    decided = build_decidedness_audit(tmp_path / "batch.json", tmp_path / "decided.csv", tmp_path / "decided.json", tmp_path / "decided.md")
    assert decided["claim_allowed"] is False
    assert sum(decided["counts"].values()) == 2

    ranking = build_ranking_stability(tmp_path / "batch.json", tmp_path / "ranking.md", tmp_path / "ranking.json")
    assert ranking["claim_allowed"] is False
    assert "certified_partial_order" in ranking


def test_v4_multiplicity_and_dependence_helpers():
    policy = allocate_alpha(0.05, 10, "bonferroni")
    assert policy["alpha_used"] == 0.005
    assert policy["claim_allowed"] is False

    warnings = dependence_warnings(
        [
            {"comparison_id": "a", "shared_reference_id": "ref"},
            {"comparison_id": "b", "shared_reference_id": "ref"},
        ]
    )
    assert warnings["a"]
    assert warnings["b"]
