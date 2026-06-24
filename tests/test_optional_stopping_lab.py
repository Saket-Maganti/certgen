import pytest

from certgen.experiments.optional_stopping_lab import run_optional_stopping_lab


def test_optional_stopping_lab_deterministic_and_schema(tmp_path):
    first = run_optional_stopping_lab(out_dir=tmp_path / "lab1", num_replicates=5, budget=12, seed=0, evidence_status="smoke_only")
    second = run_optional_stopping_lab(out_dir=tmp_path / "lab2", num_replicates=5, budget=12, seed=0, evidence_status="smoke_only")
    assert first == second
    assert first["label"] == "SMOKE_SIMULATION_ONLY_NOT_REAL_EVIDENCE"
    assert "null" in first["scenarios"]
    assert "naive_fixed_width_ci" in first["scenarios"]["null"]
    assert "v2_hoeffding_cs" in first["scenarios"]["null"]


def test_optional_stopping_lab_refuses_non_smoke_status(tmp_path):
    with pytest.raises(ValueError):
        run_optional_stopping_lab(out_dir=tmp_path / "lab", num_replicates=2, budget=5, evidence_status="real_evidence")
