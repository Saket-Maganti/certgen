from __future__ import annotations

from pathlib import Path

import yaml  # type: ignore[import-untyped]

from certgen.icml2027.kaggle import LANES, build_input
from certgen.icml2027.notebooks import check_notebook_determinism, generate_notebooks
from certgen.icml2027.numerical import run_numerical_audit
from certgen.icml2027.reviewer import run_reviewer_attacks
from certgen.icml2027.stress import run_adaptive_comparison, run_multi_model_scaling


def test_notebook_factory_and_blocked_input_plans(tmp_path: Path) -> None:
    notebook_root = tmp_path / "notebooks"
    generate_notebooks(notebook_root)
    assert check_notebook_determinism(notebook_root)["passed"]
    # Repository notebooks/configs exist, but real authenticated inputs do not.
    for lane in LANES:
        payload = build_input(lane, {}, root=Path.cwd(), out_root=tmp_path / "inputs")
        assert payload["input_zip_created"] is False
        assert payload["claim_allowed"] is False


def test_numerical_reviewer_scaling_and_adaptive_smokes(tmp_path: Path) -> None:
    numerical = run_numerical_audit(tmp_path / "numerical")
    assert numerical["passed"]
    reviewer_config = tmp_path / "reviewer.yaml"
    reviewer_config.write_text(yaml.safe_dump({"master_seed": 3, "replicates": 8, "alpha": 0.05, "attacks": ["optional_stopping", "near_ties", "high_dimension", "zero_variance"]}), encoding="utf-8")
    reviewer = run_reviewer_attacks(reviewer_config, tmp_path / "reviewer")
    assert reviewer["passed"]
    scaling_config = tmp_path / "scaling.yaml"
    scaling_config.write_text(yaml.safe_dump({"master_seed": 3, "model_counts": [2, 5], "replicates": 1, "sample_budget": 64, "alpha": 0.05}), encoding="utf-8")
    scaling = run_multi_model_scaling(scaling_config, tmp_path / "scaling")
    assert scaling["maximum_models"] == 5
    adaptive_config = tmp_path / "adaptive.yaml"
    adaptive_config.write_text(yaml.safe_dump({"master_seed": 3, "policies": ["uniform", "graph_frontier"], "replicates": 1, "model_count": 4, "chunk_size": 8, "maximum_samples": 1000, "alpha": 0.05}), encoding="utf-8")
    adaptive = run_adaptive_comparison(adaptive_config, tmp_path / "adaptive.csv")
    assert adaptive["invalid_confirmatory_promotions"] == 0
