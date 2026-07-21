from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from certgen.cvpr.analysis import summarize_samples_to_decision, validate_gate_result
from certgen.cvpr.certificate import certify_feature_bundle
from certgen.cvpr.contracts import configuration_hash
from certgen.cvpr.registries import build_family_record, write_frozen_family
from certgen.cvpr.statistical_contract import direct_mmd_difference_contribution
from certgen.core.hashing import stable_hash_json
from certgen.metrics.streams import clip_stream_values, mmd_difference_stream
from certgen.stats.cs import confidence_sequence
from certgen.stats.design_contracts import CSConfig
from certgen.stats.reference_sampling import build_reference_draw_plan


def test_direct_contribution_exact_conservative_extremes_and_invalid_values() -> None:
    assert direct_mmd_difference_contribution(1, 0, 0, 0, 1, 1) == 3.0
    assert direct_mmd_difference_contribution(0, 1, 1, 1, 0, 0) == -3.0
    assert direct_mmd_difference_contribution(1, 1, 1, 1, 1, 1) == 0.0
    for bad in (-0.01, 1.01, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            direct_mmd_difference_contribution(bad, 0, 0, 0, 0, 0)


def test_random_normalized_rbf_stream_property_sweep_is_finite_and_bounded() -> None:
    for seed in range(20):
        rng = np.random.default_rng(seed)
        arrays = [rng.normal(size=(42, 17)) for _ in range(3)]
        stream = mmd_difference_stream(*arrays, {"name": "rbf", "normalize": "l2", "gamma": 0.5}, seed=seed)
        assert stream.lower_bound == -3.0
        assert stream.upper_bound == 3.0
        assert np.isfinite(stream.values).all()
        assert min(stream.values) >= -3.0
        assert max(stream.values) <= 3.0


def test_identical_features_zero_stream_and_clipping_contract() -> None:
    features: np.ndarray = np.eye(8, dtype=float)
    stream = mmd_difference_stream(features, features, features, {"name": "rbf", "normalize": "l2", "gamma": 0.5})
    assert stream.values == [0.0] * 4
    clipped = clip_stream_values([-4, -3, 0, 3, 4], -3, 3)
    assert clipped.values == [-3.0, -3.0, 0.0, 3.0, 3.0]
    assert clipped.metadata["num_clipped_low"] == 1
    assert clipped.metadata["num_clipped_high"] == 1
    with pytest.raises(ValueError):
        clip_stream_values([0, float("nan")], -3, 3)


def test_union_hoeffding_null_directions_resume_and_budget_censoring() -> None:
    config = CSConfig(alpha=0.05, budget_units=200, lower_bound=-3, upper_bound=3, method="hoeffding")
    zero = confidence_sequence([0.0] * 200, config)
    positive = confidence_sequence([2.0] * 200, config)
    negative = confidence_sequence([-2.0] * 200, config)
    assert all(state["lower"] <= 0 <= state["upper"] for state in zero.states)
    assert any(state["lower"] > 0 for state in positive.states)
    assert any(state["upper"] < 0 for state in negative.states)
    prefix = confidence_sequence([2.0] * 73, CSConfig(alpha=0.05, budget_units=73, lower_bound=-3, upper_bound=3, method="hoeffding"))
    assert prefix.states == positive.states[:73]
    assert positive.states[72] == prefix.states[-1]


def test_samples_to_decision_keeps_censoring_visible() -> None:
    result = summarize_samples_to_decision([
        {"decision": "A_BETTER", "first_decision_n": 120, "sample_budget": 1000},
        {"decision": "UNDECIDED_AT_BUDGET", "first_decision_n": None, "sample_budget": 1000},
        {"decision": "BLOCKED_ASSUMPTION", "first_decision_n": None, "sample_budget": 1000},
    ])
    assert result["decided"] == 1
    assert result["censored_undecided"] == 1
    assert result["decided_only_summary_prohibited"] is True
    assert result["kaplan_meier_estimate"] is None


def test_gate_schema_fails_closed() -> None:
    payload = {"gate_id": "null", "run_id": "fixture", "inputs": [], "configuration_hash": "abc", "status": "NOT_RUN", "measured_values": {}, "tolerances": {}, "failure_reason": "not run", "evidence_class": "synthetic_validation_only", "claim_allowed": False}
    assert validate_gate_result(payload) == []
    assert validate_gate_result({**payload, "claim_allowed": True})


def test_canonical_certificate_is_deterministic_and_binds_resume_identity(tmp_path: Path) -> None:
    rng = np.random.default_rng(17)
    bundle_path = tmp_path / "bundle.npz"
    np.savez_compressed(
        bundle_path,
        features_a=rng.normal(size=(16, 5)),
        features_b=rng.normal(size=(16, 5)),
        features_r=rng.normal(size=(16, 5)),
        sample_ids_a=np.asarray([f"a{index}" for index in range(16)]),
        sample_ids_b=np.asarray([f"b{index}" for index in range(16)]),
        source_ids_r=np.asarray([f"r{index}" for index in range(16)]),
    )
    plan = build_reference_draw_plan(
        [f"r{index}" for index in range(16)],
        num_draws=16,
        seed=3,
        population_id="fixture_reference",
        source_manifest_sha256="a" * 64,
    )
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True), encoding="utf-8")
    family = build_family_record(
        family_id="fixture_family",
        analysis_scope="fixture",
        benchmark="cifar10",
        feature_space="clip",
        metric="rbf_mmd",
        kernel="rbf",
        bandwidth="gamma_0.5",
        model_pairs=["a_vs_b"],
        alpha_total=0.05,
    )
    family_path = tmp_path / "family.json"
    family = write_frozen_family(family, family_path)
    study = {
        "study_id": "fixture_study", "version": 1, "primary_question": "fixture question",
        "primary_outcomes": ["decision"], "secondary_outcomes": ["samples to decision"],
        "benchmarks": ["cifar10"], "models": ["a", "b"],
        "model_pairs": [{"comparison_id": "a_vs_b", "model_a": "a", "model_b": "b"}],
        "feature_spaces": ["clip"], "metrics": ["rbf_mmd"],
        "kernel": {"name": "rbf", "normalize": "l2", "gamma": 0.5},
        "bandwidth_protocol": "fixed gamma", "alpha": 0.05,
        "multiplicity_families": ["fixture_family"], "sample_budgets": [16],
        "stopping_rule": "first_boundary_crossing_union_hoeffding",
        "reference_draw_protocol": "fixed with replacement", "exclusion_rules": ["invalid input"],
        "failure_rules": ["fail closed"], "resume_rules": ["same stream only"],
        "missing_data_rules": ["block"], "censoring_rules": ["right censor"],
        "claim_thresholds": ["separate gate"], "scale_up_rules": ["stop"],
        "pivot_rules": ["new version"], "preprocessing_hash": "b" * 64,
        "frozen": True, "evidence_class": "pilot_only", "claim_allowed": False,
    }
    study["configuration_hash"] = configuration_hash(study)
    study_path = tmp_path / "study.yaml"
    study_path.write_text(yaml.safe_dump(study, sort_keys=False), encoding="utf-8")
    first = certify_feature_bundle(
        study_path=study_path, family_path=family_path, feature_bundle_path=bundle_path,
        reference_draw_plan_path=plan_path, comparison_id="a_vs_b", feature_space="clip",
        out_path=tmp_path / "certificate-1.json",
    )
    second = certify_feature_bundle(
        study_path=study_path, family_path=family_path, feature_bundle_path=bundle_path,
        reference_draw_plan_path=plan_path, comparison_id="a_vs_b", feature_space="clip",
        out_path=tmp_path / "certificate-2.json",
    )
    assert first == second
    assert first["certificate_hash"] == stable_hash_json({key: value for key, value in first.items() if key != "certificate_hash"})
    assert first["independent_reuse_prohibited"] is True
    assert first["stream_identity_hash"]
    assert first["stream_order_hash"]
    assert first["claim_allowed"] is False
