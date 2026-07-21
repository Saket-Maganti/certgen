from __future__ import annotations

import json
import hashlib
import subprocess
import zipfile
from pathlib import Path

import pytest

from certgen.audit.cvpr_final_audit import REQUIRED_PATHS
from certgen.cvpr.contracts import CVPRStage, STAGE_TRANSITIONS, build_run_id, configuration_hash
from certgen.cvpr.ranking import build_partial_ranking
from certgen.cvpr.package import build_notebook_input_package
from certgen.cvpr.registries import build_family_record, validate_all_cvpr_registries, validate_family_record, validate_preregistration
from certgen.notebooks.cvpr_static_analyzer import analyze_all
from certgen.visualization.factory import render_approved_figure, validate_figure_request
from certgen.core.hashing import file_sha256, stable_hash_json
from certgen.packaging.v9_import_repair import import_repair


def test_stage_machine_is_complete_nonclaim_and_run_ids_stable() -> None:
    assert {row.stage for row in STAGE_TRANSITIONS} == set(CVPRStage)
    assert all(row.claim_permission is False for row in STAGE_TRANSITIONS)
    config = {"alpha": 0.05, "models": ["a", "b"]}
    assert configuration_hash(config) == configuration_hash({"models": ["a", "b"], "alpha": 0.05})
    assert build_run_id(benchmark="CIFAR-10", stage="feature extraction", scale="1k", feature_space="CLIP", config=config, timestamp="20260713T000000Z") == build_run_id(benchmark="CIFAR-10", stage="feature extraction", scale="1k", feature_space="CLIP", config=config, timestamp="20260713T000000Z")


def test_family_registry_counts_cartesian_scope_and_requires_freeze() -> None:
    record = build_family_record(family_id="fixture", analysis_scope="test", benchmark="cifar10", feature_space="clip", metric="rbf_mmd", kernel="rbf", bandwidth="gamma_0.5", model_pairs=["a_vs_b", "a_vs_c"], alpha_total=0.05, dimensions={"preprocessing": ["p1", "p2"], "kernel": ["k1"]})
    assert record["number_of_hypotheses"] == 4
    assert record["alpha_per_hypothesis"] == 0.0125
    assert not validate_family_record(record)["passed"]
    record["status"] = "frozen"
    from certgen.core.hashing import stable_hash_json
    record["configuration_hash"] = stable_hash_json({key: value for key, value in record.items() if key != "configuration_hash"})
    assert validate_family_record(record)["passed"]


def test_frozen_preregistration_rejects_unresolved_placeholders(tmp_path: Path) -> None:
    import yaml

    payload = yaml.safe_load(Path("configs/cvpr/certgen_cvpr_preregistration_template.yaml").read_text(encoding="utf-8"))
    payload["frozen"] = True
    payload["configuration_hash"] = configuration_hash(payload)
    path = tmp_path / "study.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    verdict = validate_preregistration(path, require_frozen=True)
    assert not verdict["passed"]
    assert any("unresolved placeholders" in error for error in verdict["errors"])


def _certificate(comparison_id: str, feature_space: str, decision: str, direction: str | None) -> dict:
    return {"comparison_id": comparison_id, "model_a": "a", "model_b": "b", "feature_space": feature_space, "metric": "rbf_mmd", "decision": decision, "direction": direction, "family_id": "family", "family_configuration_hash": "f" * 64, "alpha_total": 0.05, "benchmark": "cifar10", "configuration_hash": "c" * 64, "preprocessing_hash": "p" * 64, "reference_population_hash": "r" * 64, "claim_allowed": False}


def test_partial_ranking_never_forces_total_order_and_detects_feature_disagreement(tmp_path: Path) -> None:
    paths = []
    for index, row in enumerate([_certificate("a_vs_b", "clip", "A_BETTER", "A"), _certificate("a_vs_b", "inception", "B_BETTER", "B")]):
        path = tmp_path / f"c{index}.json"
        path.write_text(json.dumps(row))
        paths.append(path)
    graph = build_partial_ranking(paths, out_dir=tmp_path / "ranking", aggregation_rule="unanimous_direction_or_unresolved")
    assert graph["forced_total_order"] is False
    assert graph["directed_certified_edges"] == []
    assert len(graph["feature_disagreements"]) == 1
    assert graph["contradiction_components"] == [["a", "b"]]
    assert graph["incomparable_pairs"] == [{"model_a": "a", "model_b": "b"}]
    assert set(graph["feature_space_graphs"]) == {"clip", "inception"}
    assert (tmp_path / "ranking/unresolved_pairs.csv").is_file()


def test_ranking_rejects_mixed_family_and_unregistered_feature_aggregation(tmp_path: Path) -> None:
    first = _certificate("a_vs_b", "clip", "A_BETTER", "A")
    second = _certificate("a_vs_c", "inception", "A_BETTER", "A")
    second["family_id"] = "other"
    paths = []
    for index, row in enumerate([first, second]):
        path = tmp_path / f"x{index}.json"
        path.write_text(json.dumps(row))
        paths.append(path)
    with pytest.raises(ValueError):
        build_partial_ranking(paths, out_dir=tmp_path / "bad")


def test_figure_gate_requires_paper_approved_lineage(tmp_path: Path) -> None:
    output = tmp_path / "headline.pdf"
    request = {"figure_id": "headline", "figure_type": "headline_partial_ranking", "approved_input_artifacts": ["a1"], "schema": "v1", "configuration_hash": "cfg", "claim_gate_status": "BLOCKED_NO_PAPER_EVIDENCE", "output_path": str(output), "caption_metadata": {}, "limitations": []}
    artifact = {"artifact_id": "a1", "validation_status": "pilot_valid", "claim_allowed": False, "configuration_hash": "cfg"}
    verdict = validate_figure_request(request, [artifact])
    assert not verdict["passed"]
    assert not verdict["render_allowed"]
    with pytest.raises(PermissionError):
        render_approved_figure(request, [artifact])
    assert not output.exists()


def test_cvpr_registries_notebooks_and_deliverables_exist() -> None:
    assert validate_all_cvpr_registries()["passed"]
    notebook = analyze_all()
    assert notebook["passed"], notebook
    assert notebook["real_run_required"] is True
    assert [path for path in REQUIRED_PATHS if not Path(path).is_file()] == []


def test_canonical_cli_status_and_cvpr_help_surface_are_claim_safe() -> None:
    status = subprocess.run(["python3", "-m", "certgen", "status"], capture_output=True, text=True, check=True)
    payload = json.loads(status.stdout)
    assert payload["top_level_status"] in {
        "CVPR_RUN_READY_BLOCKED_ONLY_BY_REFERENCE_INPUT",
        "CVPR_REFERENCE_READY_PREFLIGHT_REQUIRED",
        "CVPR_REAL_PREFLIGHT_REQUIRED",
        "CVPR_1K_GENERATION_READY",
    }
    assert payload["claim_allowed"] is False
    for command in ["materialize", "freeze-config", "package", "plan-runtime", "runtime-plan", "prepare", "release", "synthetic-runtime", "sanity", "certify", "rank", "analyze", "figures", "audit"]:
        completed = subprocess.run(["python3", "-m", "certgen", command, "--help"], capture_output=True, text=True)
        assert completed.returncode == 0, completed.stderr


def test_preflight_package_is_deterministic_and_claim_safe(tmp_path: Path) -> None:
    config = {
        "kind": "preflight",
        "run_id": "cifar10__preflight__tiny__none__fixture__20260713t000000z",
        "network_mode": "OFFLINE_DEPENDENCIES_OFFLINE_ASSETS",
        "dependency_network_allowed": False,
        "model_asset_network_allowed": False,
        "output_schema_version": "certgen.cvpr.preflight_output.v2",
        "requested_gpu_count": 2,
        "allow_single_gpu_fallback": False,
        "tiny_images_per_model": 2,
        "models": [{"model_id": "fixture_model", "checkpoint_or_sample_source": "fixture/source", "revision": "a" * 40, "preflight_seed": 1, "preflight_steps": 2}],
        "extractors": [{"feature_space_id": "fixture", "revision": "b" * 40}],
        "assets": [
            {"asset_kind": "model", "asset_id": "fixture_model__asset"},
            {"asset_kind": "extractor", "asset_id": "fixture__asset"},
        ],
        "claim_allowed": False,
    }
    config["configuration_hash"] = stable_hash_json(config)
    config_path = tmp_path / "config.yaml"
    import yaml

    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    outputs = []
    for index in range(2):
        output = tmp_path / f"package-{index}.zip"
        payload = build_notebook_input_package(kind="preflight", config_path=config_path, inputs={}, out_zip=output, manifest_out=tmp_path / f"manifest-{index}.json")
        assert payload["claim_allowed"] is False
        outputs.append(output)
    assert file_sha256(outputs[0]) == file_sha256(outputs[1])
    with zipfile.ZipFile(outputs[0]) as archive:
        assert {"configuration.yaml", "certgen_kaggle_runtime.py", "notebook.ipynb", "package_integrity_manifest.json"}.issubset(archive.namelist())


def test_importer_accepts_canonical_generation_layout(tmp_path: Path) -> None:
    zip_path = tmp_path / "generation.zip"
    config = {
        "kind": "generation",
        "run_id": "fixture-generation-import",
        "claim_allowed": False,
    }
    config["configuration_hash"] = stable_hash_json(config)
    import yaml

    root_status = {
        "status_code": "GENERATION_COMPLETE",
        "output_schema_version": "certgen.cvpr.generation_output.v2",
        "configuration_hash": config["configuration_hash"],
        "passed": True,
        "expected_workers": ["model_a__shard_0000"],
        "completed_workers": ["model_a__shard_0000"],
        "claim_allowed": False,
    }
    files: dict[str, str | bytes] = {
        "configuration.yaml": yaml.safe_dump(config, sort_keys=False),
        "run_identity.json": json.dumps(
            {
                "run_id": config["run_id"],
                "configuration_hash": config["configuration_hash"],
                "input_manifest_hash": "i" * 64,
                "asset_manifest_hash": "a" * 64,
                "claim_allowed": False,
            }
        ),
        "generation_status.json": json.dumps(root_status),
        "status.json": json.dumps(root_status),
        "per_model/model_a/per_shard/shard_0000/status.json": json.dumps({"status_code": "SHARD_COMPLETE", "model_id": "model_a", "shard_id": "shard_0000", "claim_allowed": False}),
        "per_model/model_a/per_shard/shard_0000/manifest.jsonl": json.dumps({"sample_id": "model_a__00000000", "seed": 0, "claim_allowed": False}) + "\n",
        "per_model/model_a/per_shard/shard_0000/images/model_a__00000000.png": b"fixture_png_bytes",
        "copyback_instructions.md": "not paper evidence; claim_allowed=false\n",
    }
    integrity = {"files": [{"path": name, "size": len(data.encode() if isinstance(data, str) else data), "sha256": hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()} for name, data in files.items()], "claim_allowed": False}
    with zipfile.ZipFile(zip_path, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
        archive.writestr("integrity_manifest.json", json.dumps(integrity))
    payload = import_repair(kind="generation", zip_path=zip_path, out_dir=tmp_path / "imported", out_json=tmp_path / "import.json", out_report=tmp_path / "import.md", registry_path=tmp_path / "registry.jsonl")
    assert payload["passed"], payload["errors"]


def test_failed_import_preserves_raw_zip_and_structured_repair_record(tmp_path: Path) -> None:
    zip_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("../escape.json", "{}")
    payload = import_repair(
        kind="generation",
        zip_path=zip_path,
        out_dir=tmp_path / "rejected",
        out_json=tmp_path / "rejected.json",
        out_report=tmp_path / "rejected.md",
        registry_path=tmp_path / "registry.jsonl",
    )
    assert payload["passed"] is False
    assert payload["kaggle_rerun_needed"] is True
    assert payload["local_repair_safe"] is False
    raw_path = Path(payload["raw_preserved_path"])
    assert raw_path.is_file()
    assert file_sha256(raw_path) == file_sha256(zip_path)
    records = list(raw_path.parent.glob("validation_*.json"))
    assert len(records) == 1
    record = json.loads(records[0].read_text(encoding="utf-8"))
    assert record["validation_result"] == "IMPORT_REPAIR_BLOCKED"
    assert record["source_zip_hash"] == file_sha256(zip_path)
