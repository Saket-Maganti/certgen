import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from certgen.certs.api import certify_clean_metric_comparison
from certgen.core.io import read_json
from certgen.fixtures.make_v2_feature_fixtures import make_v2_feature_fixtures


def test_certify_clean_metric_cli_smoke_success(tmp_path):
    paths = make_v2_feature_fixtures(tmp_path / "features", seed=0)
    out = tmp_path / "cert.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "certgen.cli.certify_clean_metric",
            "--features-a",
            paths["model_a_close"],
            "--features-b",
            paths["model_b_far"],
            "--features-r",
            paths["reference"],
            "--metric",
            "mmd_rbf",
            "--comparison-id",
            "smoke_pair",
            "--alpha",
            "0.05",
            "--budget-units",
            "40",
            "--method",
            "betting",
            "--out",
            str(out),
            "--evidence-status",
            "smoke_only",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    cert = read_json(out)
    assert cert["comparison_id"] == "smoke_pair"
    assert cert["claim_allowed"] is False
    assert cert["decision"] in {"A_certified_better", "not_decided_at_budget"}
    assert cert["stream_hash"]


def test_api_failures_for_missing_shape_nan_and_real_evidence(tmp_path):
    paths = make_v2_feature_fixtures(tmp_path / "features", seed=0)
    with pytest.raises(FileNotFoundError):
        certify_clean_metric_comparison("missing.npz", paths["model_b_far"], paths["reference"], "mmd_rbf", {}, {"alpha": 0.05, "budget_units": 4}, "x", "smoke_only", str(tmp_path / "x.json"))
    bad = tmp_path / "bad.npz"
    np.savez_compressed(bad, features=np.zeros((8, 3)))
    with pytest.raises(ValueError, match="dimensionality mismatch"):
        certify_clean_metric_comparison(paths["model_a_close"], bad, paths["reference"], "mmd_rbf", {}, {"alpha": 0.05, "budget_units": 4}, "x", "smoke_only", str(tmp_path / "x.json"))
    nan = tmp_path / "nan.npz"
    arr = np.zeros((80, 6))
    arr[0, 0] = float("nan")
    np.savez_compressed(nan, features=arr)
    with pytest.raises(ValueError, match="NaN|Inf"):
        certify_clean_metric_comparison(nan, paths["model_b_far"], paths["reference"], "mmd_rbf", {}, {"alpha": 0.05, "budget_units": 4}, "x", "smoke_only", str(tmp_path / "x.json"))
    with pytest.raises(ValueError, match="real evidence"):
        certify_clean_metric_comparison(paths["model_a_close"], paths["model_b_far"], paths["reference"], "mmd_rbf", {}, {"alpha": 0.05, "budget_units": 4}, "x", "real_evidence", str(tmp_path / "x.json"))


def test_polynomial_kid_blocked_from_rigorous_certificate_mode(tmp_path):
    paths = make_v2_feature_fixtures(tmp_path / "features", seed=0)
    with pytest.raises(ValueError, match="polynomial KID"):
        certify_clean_metric_comparison(
            paths["model_a_close"],
            paths["model_b_far"],
            paths["reference"],
            "kid_polynomial",
            {},
            {"alpha": 0.05, "budget_units": 4},
            "x",
            "smoke_only",
            str(tmp_path / "x.json"),
        )


def test_certificate_hash_output_deterministic(tmp_path):
    paths = make_v2_feature_fixtures(tmp_path / "features", seed=3)
    kwargs = dict(
        features_a_path=paths["model_a_close"],
        features_b_path=paths["model_b_far"],
        features_r_path=paths["reference"],
        metric_label="mmd_rbf",
        kernel_config={},
        cs_config={"alpha": 0.05, "budget_units": 16, "method": "betting", "seed": 99},
        comparison_id="deterministic",
        evidence_status="smoke_only",
    )
    c1 = certify_clean_metric_comparison(**kwargs, out_path=str(tmp_path / "c1.json"))
    c2 = certify_clean_metric_comparison(**kwargs, out_path=str(tmp_path / "c2.json"))
    assert c1.stream_hash == c2.stream_hash
    assert c1.feature_hashes == c2.feature_hashes
