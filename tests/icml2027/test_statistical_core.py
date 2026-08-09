from __future__ import annotations

import json
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from certgen.icml2027.equivalence import decide_equivalence
from certgen.icml2027.multiplicity import adjust_pvalues
from certgen.icml2027.sequential import anytime_radius, evaluate_stream
from certgen.icml2027.synthetic import run_synthetic_suite


def test_anytime_radius_and_stream_decisions_are_deterministic() -> None:
    assert anytime_radius(100, 0.05) > anytime_radius(1000, 0.05)
    positive = evaluate_stream([0.8] * 1000, alpha=0.05, rule="anytime")
    negative = evaluate_stream([-0.8] * 1000, alpha=0.05, rule="anytime")
    null = evaluate_stream([0.0] * 1000, alpha=0.05, rule="anytime")
    assert positive.decision == "B_BETTER"
    assert negative.decision == "A_BETTER"
    assert null.decision == "UNRESOLVED"
    assert evaluate_stream([0.0, float("nan")], alpha=0.05, rule="anytime").decision == "INVALID"


def test_equivalence_and_multiplicity_contracts() -> None:
    equivalent = decide_equivalence([0.0] * 5000, alpha=0.05, margin=0.2)
    assert equivalent["decision"] == "PRACTICALLY_EQUIVALENT"
    assert equivalent["exploratory_until_theory_verified"] is True
    bonferroni = adjust_pvalues([0.001, 0.04, 0.5], "bonferroni")
    holm = adjust_pvalues([0.001, 0.04, 0.5], "holm")
    fdr = adjust_pvalues([0.001, 0.04, 0.5], "benjamini_hochberg_exploratory")
    assert bonferroni["rejected"] == [True, False, False]
    assert holm["rejected"][0]
    assert fdr["validity_status"] == "EXPLORATORY_NOT_CONFIRMATORY"


def test_synthetic_scenario_determinism_and_schema(tmp_path: Path) -> None:
    config = {
        "tier": "quick",
        "master_seed": 7,
        "workers": 1,
        "replicates": 3,
        "report_root": str(tmp_path / "reports"),
        "defaults": {"sample_budget": 64, "alpha": 0.05, "look_step": 8},
        "scenarios": [
            {"scenario_id": "null", "family": "null_calibration", "stopping_rule": "anytime"},
            {"scenario_id": "power", "family": "mean_shift", "stopping_rule": "anytime", "effect_size": 0.2},
        ],
        "claim_allowed": False,
    }
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    first = run_synthetic_suite(config_path, tmp_path / "first")
    second = run_synthetic_suite(config_path, tmp_path / "second")
    rows_a = (tmp_path / "first/simulation_records.jsonl").read_text()
    rows_b = (tmp_path / "second/simulation_records.jsonl").read_text()
    # Runtime is measured and may differ; every scientific field is identical.
    def clean(text: str) -> list[dict[str, object]]:
        return [
            {key: value for key, value in json.loads(line).items() if key != "runtime_seconds"}
            for line in text.splitlines()
        ]
    assert clean(rows_a) == clean(rows_b)
    assert first["records"] == second["records"] == 6
    assert first["claim_allowed"] is False
