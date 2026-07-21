import json
from pathlib import Path

from certgen.core.hashing import file_sha256
from certgen.cvpr.pilot_stop_go import evaluate_pilot_stop_go
from certgen.notebooks.worker_contract import (
    COMPLETION_SCHEMA_VERSION,
    LEGACY_COMPLETION_SCHEMA_VERSION,
    completion_identity_fields,
    validate_completion_identity,
)
from certgen.pipeline.v9_next_action import determine_next_action
from certgen.release.archive import EXCLUDED_SUFFIXES, archive_members


def test_worker_contract_exact_legacy_missing_stale_and_mixed() -> None:
    exact = completion_identity_fields(
        "feature", config_schema_version="config.v1", output_schema_version="output.v2"
    )
    assert exact["schema_version"] == COMPLETION_SCHEMA_VERSION
    assert validate_completion_identity(
        exact,
        worker_type="feature",
        config_schema_version="config.v1",
        output_schema_version="output.v2",
    )["passed"]
    assert validate_completion_identity(
        {"schema_version": LEGACY_COMPLETION_SCHEMA_VERSION, "worker_version": "certgen.worker.v3"},
        worker_type="feature",
    )["compatibility"] == "legacy_compatible"
    assert not validate_completion_identity({}, worker_type="feature")["passed"]
    assert not validate_completion_identity(
        {**exact, "worker_implementation_version": "stale"},
        worker_type="feature",
        config_schema_version="config.v1",
        output_schema_version="output.v2",
    )["passed"]
    assert not validate_completion_identity(
        {**exact, "worker_version": "certgen.worker.v3"},
        worker_type="feature",
        config_schema_version="config.v1",
        output_schema_version="output.v2",
    )["passed"]


def test_next_action_uses_actual_study_and_reference_paths(tmp_path: Path) -> None:
    study = tmp_path / "artifacts/cvpr/study/custom.yaml"
    study.parent.mkdir(parents=True)
    study.write_text("profile_id: custom_profile\n", encoding="utf-8")
    reference = tmp_path / "registry/manifests/cvpr/cifar10_reference.jsonl"
    reference.parent.mkdir(parents=True)
    reference.write_text("{}\n", encoding="utf-8")

    action = determine_next_action(root=tmp_path)

    assert action["action"] == "PREPARE_REFERENCE_DRAW"
    assert str(study.resolve()) in action["exact_command"]
    assert str(reference.resolve()) in action["exact_command"]
    assert action["cwd"] == str(tmp_path.resolve())
    assert action["input_paths"] == [str(study.resolve()), str(reference.resolve())]


def test_next_action_resolves_registered_draw_for_controls_only_after_generation(
    tmp_path: Path,
) -> None:
    study = tmp_path / "artifacts/cvpr/study/custom.yaml"
    study.parent.mkdir(parents=True)
    study.write_text("profile_id: custom_profile\n", encoding="utf-8")
    reference = tmp_path / "registry/manifests/cvpr/cifar10_reference.jsonl"
    reference.parent.mkdir(parents=True)
    reference.write_text("{}\n", encoding="utf-8")
    draw = tmp_path / "registered/actual_draw.json"
    draw.parent.mkdir(parents=True)
    draw.write_text("{}\n", encoding="utf-8")
    registry = tmp_path / "data/artifact_registry.jsonl"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        json.dumps(
            {
                "artifact_id": "cvpr_reference_draw_plan:fixture",
                "artifact_type": "cvpr_reference_draw_plan",
                "path": str(draw),
                "hash": {"algorithm": "sha256", "value": file_sha256(draw)},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert determine_next_action(root=tmp_path)["action"] != "PREPARE_CONTROLS"

    generation_status = tmp_path / "data/results/cvpr/generation_import_status.json"
    generation_status.parent.mkdir(parents=True, exist_ok=True)
    generation_status.write_text(json.dumps({"passed": True}) + "\n", encoding="utf-8")
    action = determine_next_action(root=tmp_path)

    assert action["action"] == "PREPARE_CONTROLS"
    assert str(draw.resolve()) in action["exact_command"]
    assert action["input_artifact_ids"] == ["cvpr_reference_draw_plan:fixture"]


def test_next_action_reports_phase1_diagnostic_before_preflight(tmp_path: Path) -> None:
    study = tmp_path / "artifacts/cvpr/study/custom.yaml"
    study.parent.mkdir(parents=True)
    study.write_text("profile_id: custom_profile\n", encoding="utf-8")
    reference = tmp_path / "registry/manifests/cvpr/cifar10_reference.jsonl"
    reference.parent.mkdir(parents=True)
    reference.write_text("{}\n" * 10_000, encoding="utf-8")
    draw = tmp_path / "registered/reference_draw_plan.json"
    draw.parent.mkdir(parents=True)
    draw.write_text("{}\n", encoding="utf-8")
    registry = tmp_path / "data/artifact_registry.jsonl"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        json.dumps(
            {
                "artifact_id": "cvpr_reference_draw_plan:fixture",
                "artifact_type": "cvpr_reference_draw_plan",
                "path": str(draw),
                "hash": {"algorithm": "sha256", "value": file_sha256(draw)},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    action = determine_next_action(root=tmp_path)

    assert action["status"] == "KAGGLE_DIAGNOSTIC_REQUIRED"
    assert action["action"] == "RUN_KAGGLE_ENVIRONMENT_DIAGNOSTIC"
    assert action["blocker"] == "WAITING_FOR_KAGGLE_DIAGNOSTIC"


def test_pilot_stop_go_rules_are_fixed_and_fail_closed() -> None:
    pending = evaluate_pilot_stop_go({})
    assert pending["status"] == "PENDING_REAL_PILOT"
    base = {
        "family_operational_status": "FAMILY_OPERATIONALLY_READY",
        "control_status": "PASS",
        "metric_reproduction_status": "PASS",
        "certificate_status": "COMPLETE",
        "all_primary_undecided": False,
        "dino_preflight_status": "PASS",
        "cfm_preflight_status": "BLOCKED",
        "second_benchmark_preregistered": False,
    }
    result = evaluate_pilot_stop_go(base)
    assert result["decision"] == "SCALE_TO_10K"
    assert result["eligible_expansions"] == ["ADD_DINO"]
    assert evaluate_pilot_stop_go({**base, "control_status": "FAIL"})["decision"] == "REPAIR"
    assert evaluate_pilot_stop_go({**base, "all_primary_undecided": True})["decision"] == "STOP"


def test_public_archive_member_policy_excludes_model_weight_bytes() -> None:
    weight_suffixes = {".bin", ".ckpt", ".msgpack", ".onnx", ".pt", ".pth", ".safetensors"}
    assert weight_suffixes.issubset(EXCLUDED_SUFFIXES)
    assert not any(path.suffix in weight_suffixes for path in archive_members())
