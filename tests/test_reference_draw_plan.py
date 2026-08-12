import copy
import json

import numpy as np
import pytest

from certgen.certs.api import certify_clean_metric_comparison
from certgen.cli.build_reference_draw_plan import main as build_reference_draw_plan_main
from certgen.core.io import read_json
from certgen.stats.reference_sampling import (
    FINITE_POPULATION_WITHOUT_REPLACEMENT_STATUS,
    SAMPLING_SCHEME,
    build_reference_draw_plan,
    materialize_reference_draws,
    validate_reference_draw_plan,
    validate_reference_sampling_contract,
)


SOURCE_HASH = "a" * 64


def _plan(seed=7):
    return build_reference_draw_plan(
        ["r0", "r1", "r2", "r3"],
        num_draws=20,
        seed=seed,
        population_id="cifar10_test_empirical",
        source_manifest_sha256=SOURCE_HASH,
    )


def test_reference_draw_plan_is_deterministic_hash_bound_and_non_evidence():
    first = _plan()
    second = _plan()
    assert first == second
    assert first["sampling_scheme"] == SAMPLING_SCHEME
    assert first["claim_allowed"] is False
    assert first["plan_sha256"]
    validation = validate_reference_draw_plan(first, source_ids=["r0", "r1", "r2", "r3"], min_draws=20)
    assert validation["passed"] is True
    assert validation["num_unique_source_rows"] <= 4


def test_reference_draw_plan_changes_with_seed_and_rejects_without_replacement_label():
    assert _plan(7)["plan_sha256"] != _plan(8)["plan_sha256"]
    tampered = copy.deepcopy(_plan())
    tampered["sampling_scheme"] = "unique_without_replacement"
    validation = validate_reference_draw_plan(tampered, source_ids=["r0", "r1", "r2", "r3"])
    assert validation["passed"] is False
    assert any("with replacement" in error for error in validation["errors"])


def test_confirmatory_sampling_contract_fails_closed_on_reuse_and_plan_mutations():
    plan = _plan()
    valid = {
        "sampling_scheme": SAMPLING_SCHEME,
        "without_replacement": False,
        "adaptive_reference_reuse": False,
        "reference_reuse_declared": True,
        "precommitted_before_stream": True,
        "plan_sha256": plan["plan_sha256"],
    }
    assert validate_reference_sampling_contract(valid, expected_plan_sha256=plan["plan_sha256"])["passed"]
    for field, value in (
        ("without_replacement", True),
        ("adaptive_reference_reuse", True),
        ("reference_reuse_declared", False),
        ("precommitted_before_stream", False),
        ("plan_sha256", "0" * 64),
    ):
        mutated = {**valid, field: value}
        assert not validate_reference_sampling_contract(
            mutated, expected_plan_sha256=plan["plan_sha256"]
        )["passed"]
    assert FINITE_POPULATION_WITHOUT_REPLACEMENT_STATUS == "EXPERIMENTAL_NOT_SUPPORTED"


def test_reference_draw_plan_detects_draw_tampering_and_source_order_mismatch():
    plan = _plan()
    plan["draws"][0]["source_index"] = (plan["draws"][0]["source_index"] + 1) % 4
    assert validate_reference_draw_plan(plan, source_ids=["r0", "r1", "r2", "r3"])["passed"] is False
    assert validate_reference_draw_plan(_plan(), source_ids=["r1", "r0", "r2", "r3"])["passed"] is False


def test_materialize_reference_draws_matches_precommitted_source_ids():
    features = np.arange(12, dtype=float).reshape(4, 3)
    plan = _plan()
    drawn, draw_ids, validation = materialize_reference_draws(
        features,
        ["r0", "r1", "r2", "r3"],
        plan,
        min_draws=20,
    )
    expected = features[[row["source_index"] for row in plan["draws"]]]
    assert np.array_equal(drawn, expected)
    assert draw_ids == [row["draw_id"] for row in plan["draws"]]
    assert validation["passed"] is True


def test_real_like_certificate_hard_blocks_missing_reference_draw_plan(tmp_path):
    rng = np.random.default_rng(5)
    paths = []
    for name in ["a", "b", "r"]:
        path = tmp_path / f"{name}.npz"
        np.savez_compressed(
            path,
            features=rng.normal(size=(12, 3)),
            sample_ids=np.asarray([f"{name}{index}" for index in range(12)]),
        )
        paths.append(str(path))
    with pytest.raises(ValueError, match="IID-with-replacement reference_draw_plan"):
        certify_clean_metric_comparison(
            paths[0],
            paths[1],
            paths[2],
            "mmd_rbf",
            {},
            {"alpha": 0.05, "budget_units": 4, "method": "hoeffding"},
            "real_like",
            "pilot_only",
            str(tmp_path / "certificate.json"),
        )


def test_reference_draw_plan_cli_filters_reference_rows_and_writes_valid_plan(tmp_path):
    manifest = tmp_path / "manifest.jsonl"
    rows = [
        {"sample_id": "r0", "role": "reference"},
        {"sample_id": "generated", "role": "model_a"},
        {"sample_id": "r1", "role": "reference"},
    ]
    manifest.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    out = tmp_path / "draw_plan.json"
    assert (
        build_reference_draw_plan_main(
            [
                "--manifest",
                str(manifest),
                "--population-id",
                "cifar10_test_empirical",
                "--num-draws",
                "10",
                "--seed",
                "17",
                "--out",
                str(out),
            ]
        )
        == 0
    )
    plan = read_json(out)
    assert validate_reference_draw_plan(plan, source_ids=["r0", "r1"], min_draws=10)["passed"] is True
