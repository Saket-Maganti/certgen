"""Tests for the R1 pre-pilot upgrades: e-values, e-BH, block-size sweep,
samples-to-decision, and real feature-extraction plumbing (stub-injected)."""

import json

import numpy as np
import pytest

from certgen.analysis.block_size_sensitivity import block_size_sensitivity
from certgen.analysis.samples_to_decision import samples_to_decision_from_states
from certgen.certs.multiple_comparisons import audit_comparisons_with_fdr, e_bh
from certgen.features.extractors import EXTRACTORS
from certgen.features.extractors.base import OptionalDependencyMissing
from certgen.stats.cs import confidence_sequence
from certgen.stats.design_contracts import CSConfig
from certgen.stats.e_values import betting_e_process, betting_e_value, e_value_decided


def test_e_bh_known_example():
    result = e_bh([100.0, 50.0, 1.0, 0.5], alpha=0.05)
    assert result["num_rejections"] == 2
    assert result["rejected_indices"] == [0, 1]
    assert result["fdr_controlled_under_arbitrary_dependence"] is True
    assert result["claim_allowed"] is False


def test_e_bh_rejects_none_when_no_evalue_large():
    result = e_bh([1.0, 1.0, 1.0], alpha=0.05)
    assert result["num_rejections"] == 0
    assert result["rejected_indices"] == []


def test_e_bh_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        e_bh([], 0.05)
    with pytest.raises(ValueError):
        e_bh([-1.0, 2.0], 0.05)


def test_point_null_evalue_rejects_obvious_gap_but_is_not_directional():
    obvious = [-0.8] * 80
    config = CSConfig(alpha=0.05, budget_units=80, lower_bound=-1, upper_bound=1, method="betting")
    cs = confidence_sequence(obvious, config)
    e = betting_e_value(obvious, config)
    decided_by_cs = cs.upper < 0 or cs.lower > 0
    assert decided_by_cs is True
    assert e_value_decided(e, 0.05) is True
    assert e >= 1.0 / 0.05
    assert cs.time_uniform is False


def test_betting_evalue_null_not_decided():
    null = [0.0] * 64
    config = CSConfig(alpha=0.05, budget_units=64, lower_bound=-1, upper_bound=1, method="betting")
    e = betting_e_value(null, config)
    assert e < 1.0 / 0.05
    assert e_value_decided(e, 0.05) is False


def test_betting_evalue_rejects_out_of_bounds_instead_of_clipping():
    config = CSConfig(alpha=0.05, budget_units=2, lower_bound=-1, upper_bound=1, method="betting")
    with pytest.raises(ValueError, match="outside"):
        betting_e_process([0.0, 1.1], config)


def test_audit_comparisons_with_fdr_undecided_fraction():
    comparisons = [
        {"comparison_id": "clear", "e_value": 1000.0},
        {"comparison_id": "noise_a", "e_value": 0.1},
        {"comparison_id": "noise_b", "e_value": 0.1},
    ]
    audit = audit_comparisons_with_fdr(comparisons, alpha=0.05)
    assert audit["num_decided"] == 1
    assert audit["undecided_fraction"] == pytest.approx(2.0 / 3.0)
    assert audit["comparisons"][0]["decided_under_fdr"] is True
    assert audit["comparisons"][0]["point_null_rejected_under_fdr"] is True
    assert audit["directional_claim_supported"] is False
    assert audit["global_optional_stopping_supported"] is False
    assert audit["claim_allowed"] is False


def test_samples_to_decision_from_states():
    decided = [{"n": 1.0, "lower": -0.5, "upper": 0.5}, {"n": 2.0, "lower": 0.1, "upper": 0.4}]
    undecided = [{"n": 1.0, "lower": -0.5, "upper": 0.5}, {"n": 2.0, "lower": -0.2, "upper": 0.3}]
    assert samples_to_decision_from_states(decided) == 2
    assert samples_to_decision_from_states(undecided) is None


def test_block_size_sensitivity_structure():
    r = np.tile(np.array([[1.0, 0.0]]), (64, 1))
    a = r + 0.01
    b = np.tile(np.array([[0.0, 1.0]]), (64, 1))
    sweep = block_size_sensitivity(a, b, r, alpha=0.05, block_sizes=[1, 4, 16], seed=3)
    assert [row["block_size"] for row in sweep["rows"]] == [1, 4, 16]
    assert all("final_width" in row for row in sweep["rows"])
    assert isinstance(sweep["decision_robust_across_block_sizes"], bool)
    assert sweep["claim_allowed"] is False


def test_real_extraction_plumbing_with_injected_backbone(tmp_path, monkeypatch):
    img_a = tmp_path / "a.png"
    img_b = tmp_path / "b.png"
    img_a.write_text("x", encoding="utf-8")
    img_b.write_text("y", encoding="utf-8")
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        json.dumps({"sample_id": "a", "path": str(img_a)}) + "\n" + json.dumps({"sample_id": "b", "path": str(img_b)}) + "\n",
        encoding="utf-8",
    )

    extractor = EXTRACTORS["inception_v3_pool3"]()
    monkeypatch.setattr(extractor, "is_available", lambda: True)
    monkeypatch.setattr(extractor, "_resolve_device", lambda device: "cpu")

    def load_stub(device, model_id, preprocessing):
        extractor.resolved_model_id = "stub-weights"
        extractor.resolved_model_revision = "fixture-revision"
        extractor.resolved_weights_id = "fixture-weights"
        extractor.resolved_weights_url = None
        extractor.resolved_license_status = "synthetic_fixture"
        return object(), None

    monkeypatch.setattr(extractor, "_load_backbone", load_stub)
    monkeypatch.setattr(extractor, "_embed_paths", lambda model, transform, paths, device, batch_size: np.ones((len(paths), 2048), dtype=np.float32))

    result = extractor.extract(
        str(manifest),
        str(tmp_path / "out"),
        batch_size=8,
        device="cpu",
        model_id="stub-weights",
        preprocessing={"image_size": 299, "interpolation": "bilinear", "normalization": "inception"},
    )
    assert result["num_items"] == 2
    assert result["feature_dim"] == 2048
    assert result["claim_allowed"] is False
    assert result["evidence_status"] == "real_features_unvalidated"

    sidecar = json.loads((tmp_path / "out" / "inception_v3_pool3_features.json").read_text())
    assert sidecar["sample_ids"] == ["a", "b"]
    assert sidecar["model_id"] == "stub-weights"
    assert sidecar["model_revision"] == "fixture-revision"
    assert sidecar["claim_allowed"] is False
    assert sidecar["hash"] == result["hash"]


def test_extract_still_blocks_when_dependencies_missing(tmp_path, monkeypatch):
    extractor = EXTRACTORS["clip_vit"]()
    monkeypatch.setattr(extractor, "is_available", lambda: False)
    with pytest.raises(OptionalDependencyMissing):
        extractor.extract(str(tmp_path / "missing.jsonl"), str(tmp_path), 1, "cpu")


def test_run_feature_extraction_cli_plans_without_execute(tmp_path):
    from certgen.cli.run_feature_extraction import run_feature_extraction

    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({"sample_id": "1", "path": str(tmp_path / "x.png")}) + "\n", encoding="utf-8")
    plan = run_feature_extraction(
        input_manifest=str(manifest),
        extractor="inception_v3_pool3",
        out_dir=str(tmp_path / "out"),
        execute=False,
    )
    assert plan["execute"] is False
    assert plan["claim_allowed"] is False
    with pytest.raises(ValueError):
        run_feature_extraction(input_manifest=str(manifest), extractor="bad", out_dir=str(tmp_path))
