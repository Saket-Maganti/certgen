import json
from pathlib import Path

import pytest
import yaml

from certgen.audit.r0_cpu_gpu_audit import run_audit
from certgen.certs.api import certify_clean_metric_comparison
from certgen.certs.fid_policy import assert_no_rigorous_fid_claim
from certgen.fixtures.make_v2_feature_fixtures import make_v2_feature_fixtures


CPU_COMMANDS = [
    "00_validate_environment_cpu.sh",
    "01_validate_provenance.sh",
    "02_validate_feature_caches.sh",
    "03_reproduce_metric_from_features.sh",
    "04_run_clean_core_certificates_cpu.sh",
    "05_run_optional_stopping_lab_cpu.sh",
    "06_generate_pilot_report_cpu.sh",
    "07_run_r0_audit_cpu.sh",
]


def test_cpu_command_bundle_exists_and_disables_cuda():
    root = Path("commands/r0_cpu")
    for name in CPU_COMMANDS:
        path = root / name
        assert path.exists(), name
        text = path.read_text(encoding="utf-8")
        assert "set -euo pipefail" in text
        assert "PYTHONDONTWRITEBYTECODE=1" in text
        assert 'CUDA_VISIBLE_DEVICES=""' in text


def test_gpu_runbooks_exist_but_are_not_needed_for_cpu_tests():
    feature = Path("docs/KAGGLE_T4X2_FEATURE_EXTRACTION_RUNBOOK_R0.md")
    generation = Path("docs/KAGGLE_T4X2_PARALLEL_SEED_GENERATION_RUNBOOK_R0.md")
    assert feature.exists()
    assert generation.exists()
    feature_text = feature.read_text(encoding="utf-8")
    generation_text = generation.read_text(encoding="utf-8")
    assert "CUDA_VISIBLE_DEVICES=0" in feature_text
    assert "--shard-id 0" in feature_text
    assert "--num-shards 2" in feature_text
    assert "Prefer released samples" in generation_text
    assert "Sample generation is not implemented" in generation_text


def test_runtime_estimates_are_labeled_planning_not_results():
    text = Path("docs/R0_RUNTIME_ESTIMATES_CPU_AND_KAGGLE_T4X2.md").read_text(encoding="utf-8")
    assert "planning estimates, not empirical project results" in text
    assert "Inception features, 50k CIFAR-sized images" in text
    assert "CPU certificate/report runs from cached features" in text


def test_cpu_first_config_validates():
    config = yaml.safe_load(Path("configs/certgen_r0_cpu_first.yaml").read_text(encoding="utf-8"))
    assert config["execution_mode"] == "cpu_first"
    assert set(config["gpu_allowed_for"]) == {"feature_extraction", "optional_sample_generation"}
    assert config["certificate_device"] == "cpu"
    assert config["reports_device"] == "cpu"
    assert config["claim_allowed_default"] is False
    assert config["fid_certificate_allowed"] is False
    assert config["polynomial_kid_certificate_allowed"] is False
    assert config["bounded_rbf_mmd_certificate_allowed"] is True
    assert config["cmmd_bounded_certificate_allowed"] is True


def test_no_r0_claim_allowed_true_artifacts():
    for path in Path("data").glob("**/*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        stack = [payload]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                assert item.get("claim_allowed") is not True, str(path)
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)


def test_fid_and_polynomial_kid_certificates_remain_blocked(tmp_path):
    with pytest.raises(ValueError):
        assert_no_rigorous_fid_claim({"metric_label": "fid_inception", "rigorous_anytime_certificate": True})
    paths = make_v2_feature_fixtures(tmp_path / "features")
    with pytest.raises(ValueError, match="polynomial"):
        certify_clean_metric_comparison(
            paths["model_a_close"],
            paths["model_b_far"],
            paths["reference"],
            "kid_polynomial",
            {},
            {"alpha": 0.05, "budget_units": 4},
            "kid_blocked",
            "smoke_only",
            str(tmp_path / "kid.json"),
        )


def test_r0_cpu_gpu_audit_passes(tmp_path):
    payload = run_audit(out=tmp_path / "audit.md", json_out=tmp_path / "audit.json")
    assert payload["passed"], payload["checks"]
    assert payload["claim_allowed"] is False
    assert payload["r1_status_code"] in {
        "READY_FOR_R1_REAL_PILOT",
        "READY_FOR_KAGGLE_FEATURE_EXTRACTION",
        "READY_FOR_CPU_CERTIFICATE_PILOT",
        "BLOCKED_MISSING_REAL_SOURCES",
        "BLOCKED_MISSING_REFERENCE_SAMPLES",
        "BLOCKED_GENERATION_NOT_RUN",
        "BLOCKED_GENERATION_ADAPTER_UNSUPPORTED",
        "BLOCKED_FEATURE_EXTRACTION_NOT_RUN",
        "BLOCKED_MISSING_FEATURE_EXTRACTION",
        "BLOCKED_METRIC_REPRODUCTION",
        "BLOCKED_PROVENANCE_OR_LICENSE",
    }
