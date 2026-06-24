from certgen.certs.api import certify_clean_metric_comparison
from certgen.fixtures.make_v2_feature_fixtures import make_v2_feature_fixtures
from certgen.gates.evidence_gate import validate_evidence_status


def _cert(paths, a, b, metric, out, method="betting"):
    return certify_clean_metric_comparison(
        paths[a],
        paths[b],
        paths["reference"],
        metric,
        {},
        {"alpha": 0.05, "budget_units": 40, "method": method, "seed": 0},
        f"{a}_vs_{b}_{metric}",
        "smoke_only",
        str(out),
    )


def test_v2_integration_cases(tmp_path):
    paths = make_v2_feature_fixtures(tmp_path / "features", seed=0)
    a_cert = _cert(paths, "model_a_close", "model_b_far", "mmd_rbf", tmp_path / "a.json")
    b_cert = _cert(paths, "model_a_far", "model_b_close", "mmd_rbf", tmp_path / "b.json")
    equal = _cert(paths, "model_equal_1", "model_equal_2", "mmd_rbf", tmp_path / "eq.json")
    cmmd = _cert(paths, "model_a_close", "model_b_far", "cmmd_clip_mmd", tmp_path / "cmmd.json")
    rbf = _cert(paths, "model_a_close", "model_b_far", "mmd_rbf", tmp_path / "rbf.json")
    assert a_cert.metric_label == "mmd_rbf"
    assert b_cert.metric_label == "mmd_rbf"
    assert a_cert.claim_allowed is False
    assert b_cert.claim_allowed is False
    assert equal.decision == "not_decided_at_budget"
    assert cmmd.metric_label == "cmmd_clip_mmd"
    assert rbf.metric_label == "mmd_rbf"
    assert not validate_evidence_status("real_evidence_candidate", mode="smoke").passed


def test_fixture_generation_metadata_visible(tmp_path):
    paths = make_v2_feature_fixtures(tmp_path / "features", seed=1)
    for path in paths.values():
        meta_path = path.replace(".npz", ".metadata.json")
        text = open(meta_path, encoding="utf-8").read()
        assert "smoke_only" in text
        assert "NO_REAL_EVIDENCE" in text
