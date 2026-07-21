from __future__ import annotations

import json
from pathlib import Path

from certgen.core.hashing import file_sha256
from certgen.cvpr.readiness import readiness_report
from certgen.cvpr.analysis import write_cross_feature_analysis
from certgen.cvpr.builder_faithful import run_builder_faithful_synthetic
from certgen.cvpr.study import freeze_study
from certgen.max_ceiling.capsule import build_run_capsule, inspect_run_capsule, verify_run_capsule
from certgen.max_ceiling.contracts import (
    doctor_report,
    freeze_scale_plan,
    freeze_sensitivity,
    plan_resolution,
    rehearse_failures,
    replay_plan,
    scale_plan_next,
    scale_plan_status,
    summarize_accounting,
    validate_claims,
    validate_figure_table_contracts,
    validate_optional_lanes,
    validate_sensitivity,
    verify_replay_plan,
)
from certgen.max_ceiling.provenance import build_provenance_graph, verify_provenance_graph


REPO = Path(__file__).resolve().parents[1]


def _study(tmp_path: Path) -> Path:
    target = tmp_path / "study.yaml"
    freeze_study(
        "cifar_integrity_minimal",
        out_path=target,
        profile_root=REPO / "configs/cvpr/profiles",
        model_registry=REPO / "registry/cvpr/model_registry.yaml",
        feature_registry=REPO / "registry/cvpr/feature_space_registry.yaml",
        comparison_registry=REPO / "registry/cvpr/comparison_registry.csv",
    )
    return target


def _registry_row(path: Path, artifact_id: str, study_hash: str, parents: list[object]) -> dict[str, object]:
    return {
        "artifact_id": artifact_id,
        "artifact_type": "fixture_result",
        "schema_version": "certgen.maximum_ceiling.fixture.v1",
        "content_hash": file_sha256(path),
        "configuration_hash": study_hash,
        "study_hash": study_hash,
        "parent_artifact_ids": parents,
        "source_paths": [str(path)],
        "created_at": "fixture",
        "evidence_class": "synthetic_validation_only",
        "claim_allowed": False,
        "validation_status": "PASS",
        "stage": "controls",
        "path": str(path),
    }


def test_provenance_graph_is_deterministic_and_verifies(tmp_path: Path) -> None:
    study_path = _study(tmp_path)
    registry = tmp_path / "artifacts.jsonl"
    first = build_provenance_graph(study_path, registry_path=registry, root=tmp_path)
    second = build_provenance_graph(study_path, registry_path=registry, root=tmp_path)
    assert first["graph_hash"] == second["graph_hash"]
    assert Path(first["json_path"]).read_bytes() == Path(second["json_path"]).read_bytes()
    verdict = verify_provenance_graph(study_path, registry_path=registry, root=tmp_path)
    assert verdict["passed"]
    assert verdict["nodes"] == 1
    rogue = Path(first["json_path"]).parents[1] / "results/rogue.json"
    rogue.parent.mkdir()
    rogue.write_text("{}\n", encoding="utf-8")
    assert not verify_provenance_graph(study_path, registry_path=registry, root=tmp_path)["passed"]


def test_provenance_rejects_missing_changed_parent_and_cycle(tmp_path: Path) -> None:
    study_path = _study(tmp_path)
    study_hash = __import__("yaml").safe_load(study_path.read_text())["configuration_hash"]
    left = tmp_path / "left.json"
    right = tmp_path / "right.json"
    left.write_text("{}\n", encoding="utf-8")
    right.write_text("{\"right\": true}\n", encoding="utf-8")
    rows = [
        _registry_row(left, "left", study_hash, [{"artifact_id": "right", "content_hash": "0" * 64}]),
        _registry_row(right, "right", study_hash, ["left"]),
        _registry_row(right, "orphan", study_hash, ["missing"]),
    ]
    registry = tmp_path / "artifacts.jsonl"
    registry.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    verdict = verify_provenance_graph(study_path, registry_path=registry, root=tmp_path)
    assert not verdict["passed"]
    assert any("missing parent" in error for error in verdict["errors"])
    assert any("changed parent hash" in error for error in verdict["errors"])
    assert any("cycle" in error for error in verdict["errors"])


def test_provenance_prefers_current_study_bound_version_at_canonical_path(
    tmp_path: Path,
) -> None:
    study_path = _study(tmp_path)
    study_hash = __import__("yaml").safe_load(study_path.read_text())["configuration_hash"]
    artifact = tmp_path / "canonical.json"
    artifact.write_text('{"current": true}\n', encoding="utf-8")
    legacy = _registry_row(artifact, "legacy", study_hash, [])
    legacy.pop("study_hash")
    legacy["content_hash"] = "0" * 64
    current = _registry_row(artifact, "current", study_hash, [])
    registry = tmp_path / "artifacts.jsonl"
    registry.write_text(
        json.dumps(legacy) + "\n" + json.dumps(current) + "\n",
        encoding="utf-8",
    )

    verdict = verify_provenance_graph(
        study_path, registry_path=registry, root=tmp_path
    )

    assert verdict["passed"]
    assert verdict["nodes"] == 2


def test_capsule_is_deterministic_content_addressed_and_safe(tmp_path: Path) -> None:
    study_path = _study(tmp_path)
    output = tmp_path / "preflight.zip"
    first = build_run_capsule("preflight", study_path, root=REPO, output=output)
    second = build_run_capsule("preflight", study_path, root=REPO, output=output)
    assert first["capsule_sha256"] == second["capsule_sha256"]
    assert second["status"] == "CAPSULE_REUSED"
    assert inspect_run_capsule(output)["passed"]
    assert verify_run_capsule(output)["passed"]
    public = build_run_capsule("preflight", study_path, root=REPO, output=tmp_path / "public.zip", public=True)
    assert public["classification"] == "PUBLIC_REPRODUCIBILITY_CAPSULE"
    assert verify_run_capsule(tmp_path / "public.zip")["passed"]


def test_scale_sensitivity_resolution_and_replay_contracts(tmp_path: Path) -> None:
    study_path = _study(tmp_path)
    assert freeze_scale_plan(study_path, root=tmp_path)["status"] == "SCALE_PLAN_FROZEN"
    assert scale_plan_status(study_path, root=tmp_path)["passed"]
    assert scale_plan_next(study_path, root=tmp_path)["decision"] == "COMPLETE_AT_1K"
    freeze_sensitivity(study_path, root=tmp_path)
    assert validate_sensitivity(study_path, root=tmp_path)["passed"]
    resolution = plan_resolution(study_path, root=tmp_path, trials=16)
    assert resolution["planning_simulation_only"]
    assert resolution["not_empirical_power"]
    replay_plan(study_path, root=tmp_path, changed_paths=["feature_preprocessing.yaml"])
    assert verify_replay_plan(study_path, root=tmp_path)["passed"]


def test_failure_rehearsal_and_accounting_boundary(tmp_path: Path) -> None:
    failures = rehearse_failures(root=tmp_path)
    assert failures["passed"]
    assert failures["cases"] == 16
    study_path = _study(tmp_path)
    accounting = summarize_accounting(study_path, root=tmp_path)
    assert accounting["status"] == "BLOCKED_REAL_EXECUTION"
    assert accounting["planning_estimates_are_never_measured"]


def test_certificate_ranking_and_cross_feature_products(tmp_path: Path) -> None:
    root = tmp_path / "rehearsal"
    run_builder_faithful_synthetic(root)
    certificates = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((root / "certificates").glob("*.json"))
        if json.loads(path.read_text(encoding="utf-8")).get("schema_version")
        == "certgen.cvpr.certificate.v1"
    ]
    assert certificates
    required_lineage = {
        "study_hash", "profile", "family_id", "hypothesis_id", "comparison_type",
        "feature_definition", "reference_draw_hash", "control_protocol", "feature_cache_hashes",
        "alpha_accounting", "sample_budget", "decision", "first_decision_n", "censored",
        "support_bound", "limitations", "evidence_eligibility",
    }
    assert required_lineage.issubset(certificates[0])
    ranking = root / "ranking"
    for name in (
        "ranking_graph.json", "ranking_edges.csv", "ranking_unresolved.csv",
        "ranking_invalid.csv", "ranking_provenance.json",
    ):
        assert (ranking / name).is_file()

    cross_rows = [
        {
            "comparison_id": "pair",
            "feature_space": "inception",
            "sample_budget": 1000,
            "decision": "A_BETTER",
            "model_a": "a",
            "model_b": "b",
            "claim_allowed": False,
        },
        {
            "comparison_id": "pair",
            "feature_space": "clip",
            "sample_budget": 1000,
            "decision": "UNDECIDED_AT_BUDGET",
            "model_a": "a",
            "model_b": "b",
            "claim_allowed": False,
        },
    ]
    cross = tmp_path / "cross"
    write_cross_feature_analysis(cross_rows, cross)
    for name in (
        "agreement_matrix.csv", "direction_disagreements.csv", "decided_vs_unresolved.csv",
        "invalid_feature_lanes.csv", "consensus_edges.json", "representation_specific_edges.json",
    ):
        assert (cross / name).is_file()


def test_claim_figure_optional_and_doctor_contracts() -> None:
    claims = validate_claims(matrix_path=REPO / "reports/CERTGEN_CLAIM_EVIDENCE_MATRIX.csv")
    assert claims["passed"]
    assert claims["rows"] >= 5
    assert validate_figure_table_contracts(root=REPO)["passed"]
    assert validate_optional_lanes(REPO / "registry/cvpr/optional_extension_lanes.yaml")["passed"]
    doctor = doctor_report(root=REPO)
    assert doctor["status"] in {"PASS", "BLOCKED_REAL_INPUT", "BLOCKED_REAL_EXECUTION"}
    assert doctor["exact_next_action"] == readiness_report()["exact_next_command"]


def test_readiness_reports_complete_maximum_ceiling_stage_surface() -> None:
    report = readiness_report()
    required = {
        "replacement_status", "reference", "profile", "study_freeze", "reference_draw",
        "preflight", "generation", "controls", "features", "cache_v2", "metric_gates",
        "sanity_gates", "family", "certificate_inputs", "family_certificates", "ranking",
        "cross_feature_analysis", "pilot_decision", "provenance_integrity", "public_release_safety",
        "exact_next_action",
    }
    assert required.issubset(report["maximum_ceiling_components"])
    assert report["claim_allowed"] is False
