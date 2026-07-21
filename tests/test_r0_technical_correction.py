import numpy as np
import pytest

from certgen.certs.api import certify_clean_metric_comparison
from certgen.cli.make_smoke_artifacts import create_smoke_artifacts
from certgen.core.io import read_json
from certgen.fixtures.make_v2_feature_fixtures import make_v2_feature_fixtures
from certgen.metrics.streams import mmd_difference_stream
from certgen.pipeline.cifar10_real_pilot import run_cifar10_r1_readiness
from certgen.stats.cs import confidence_sequence
from certgen.stats.design_contracts import CSConfig


def _first_decision_n(states):
    for state in states:
        if state["upper"] < 0 or state["lower"] > 0:
            return int(state["n"])
    return None


def test_bounded_kernel_streams_respect_declared_bounds_and_block_size():
    r = np.tile(np.array([[1.0, 0.0]]), (30, 1))
    a = r + 0.01
    b = np.tile(np.array([[0.0, 1.0]]), (30, 1))
    unblocked = mmd_difference_stream(a, b, r, {"name": "rbf", "normalize": "l2"}, seed=3, metric_label="mmd_rbf")
    blocked = mmd_difference_stream(a, b, r, {"name": "rbf", "normalize": "l2"}, seed=3, metric_label="mmd_rbf", block_size=5)
    assert unblocked.bounded is True
    assert unblocked.lower_bound == -3.0
    assert unblocked.upper_bound == 3.0
    assert all(unblocked.lower_bound <= value <= unblocked.upper_bound for value in unblocked.values)
    assert len(blocked.values) < len(unblocked.values)
    assert blocked.metadata["block_size"] == 5


def test_polynomial_kid_blocked_from_rigorous_certificate_mode_by_default(tmp_path):
    paths = make_v2_feature_fixtures(tmp_path / "features")
    with pytest.raises(ValueError, match="polynomial KID"):
        certify_clean_metric_comparison(
            paths["model_a_close"],
            paths["model_b_far"],
            paths["reference"],
            "kid_polynomial",
            {},
            {"alpha": 0.05, "budget_units": 8},
            "kid_blocked",
            "smoke_only",
            str(tmp_path / "kid.json"),
        )


def test_betting_cs_deterministic_and_null_not_decided():
    config = CSConfig(alpha=0.05, budget_units=64, lower_bound=-1, upper_bound=1, method="betting", seed=11)
    first = confidence_sequence([0.0] * 64, config)
    second = confidence_sequence([0.0] * 64, config)
    assert first.states == second.states
    assert first.lower <= 0.0 <= first.upper
    assert _first_decision_n(first.states) is None


def test_betting_grid_is_powerful_but_not_claim_capable():
    values = [-0.8] * 80
    betting = confidence_sequence(values, CSConfig(alpha=0.05, budget_units=80, lower_bound=-1, upper_bound=1, method="betting"))
    hoeffding = confidence_sequence(values, CSConfig(alpha=0.05, budget_units=80, lower_bound=-1, upper_bound=1, method="hoeffding"))
    betting_n = _first_decision_n(betting.states)
    hoeffding_n = _first_decision_n(hoeffding.states)
    assert betting_n is not None
    assert hoeffding_n is not None
    assert betting_n < hoeffding_n
    assert betting.time_uniform is False
    assert "continuum_coverage_unresolved" in betting.theory_status
    assert hoeffding.time_uniform is True


def test_claim_allowed_false_for_smoke_template_and_pilot_outputs(tmp_path):
    smoke = create_smoke_artifacts(config_path="configs/certgen_v1_smoke.yaml", out_dir=tmp_path / "smoke", compute_metrics=True, make_certificate=True)
    smoke_json = read_json(tmp_path / "smoke" / "smoke_artifact.json")
    smoke_cert = read_json(smoke["certificate_path"])
    assert smoke_json["evidence_status"] == "non_evidence_smoke"
    assert smoke_cert["evidence_status"] == "non_evidence_smoke"

    status = run_cifar10_r1_readiness(
        provenance_ledger=tmp_path / "missing_ledger.csv",
        sample_manifest=tmp_path / "missing_manifest.jsonl",
        preprocessing_lock="configs/preprocessing_locks/cifar10_inception_bilinear_299.json",
        feature_cache_dir=tmp_path / "missing_features",
        metric_reproduction_audit=tmp_path / "missing_repro.json",
        out_json=tmp_path / "r1_status.json",
        report=tmp_path / "r1.md",
    )
    assert status["claim_allowed"] is False
    assert status["ready_for_r1"] is False
    assert read_json(tmp_path / "r1_status.json")["claim_allowed"] is False
