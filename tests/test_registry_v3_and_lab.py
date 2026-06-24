from certgen.registry.v3_schema import render_availability_table, validate_v3_registry
from certgen.stats.optional_stopping_lab import run_optional_stopping_lab_v3


def test_v3_registry_templates_and_availability(tmp_path):
    result = validate_v3_registry("registry/v3/benchmarks_template.csv", "registry/v3/model_pairs_template.csv", "registry/v3/feature_caches_template.csv")
    assert result["passed"]
    table = render_availability_table("registry/v3", tmp_path / "table.md", tmp_path / "table.json")
    assert table["claim_allowed"] is False
    assert table["entries"][0]["pilot_ready"] is False


def test_optional_stopping_lab_v3_deterministic(tmp_path):
    config = tmp_path / "lab.yaml"
    config.write_text("num_replicates: 4\nbudget: 20\nalpha: 0.05\nseed: 4\n", encoding="utf-8")
    first = run_optional_stopping_lab_v3(config, tmp_path / "lab.md", tmp_path / "lab.json")
    second = run_optional_stopping_lab_v3(config, tmp_path / "lab2.md", tmp_path / "lab2.json")
    assert first == second
    assert first["evidence_status"] == "synthetic_only"
    assert "null_equal_distance" in first["scenarios"]
    assert "certgen_hoeffding_cs" in first["scenarios"]["null_equal_distance"]
