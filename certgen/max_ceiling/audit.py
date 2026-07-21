"""Independent maximum-ceiling pre-run audit."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from certgen.cvpr.builder_faithful import run_builder_faithful_synthetic
from certgen.cvpr.study import freeze_study
from certgen.max_ceiling.capsule import build_run_capsule, verify_run_capsule
from certgen.max_ceiling.contracts import (
    bootstrap_contract_artifacts,
    doctor_report,
    freeze_scale_plan,
    freeze_sensitivity,
    plan_resolution,
    rehearse_failures,
    replay_plan,
    scale_plan_status,
    summarize_accounting,
    validate_claims,
    validate_figure_table_contracts,
    validate_optional_lanes,
    validate_sensitivity,
    verify_replay_plan,
)
from certgen.max_ceiling.provenance import verify_provenance_graph
from certgen.notebooks.cvpr_static_analyzer import analyze_all


REQUIRED_ARTIFACTS = (
    "CERTGEN_MAX_CEILING_PRE_RUN_READINESS_REPORT.md",
    "CERTGEN_MAX_CEILING_EXECUTION_HANDBOOK.md",
    "CERTGEN_MAX_CEILING_SINGLE_FILE_HANDOFF.md",
    "reports/CERTGEN_REPLACEMENT_AUDIT.md",
    "reports/CERTGEN_MAX_CEILING_BASELINE.md",
    "reports/CERTGEN_MAX_CEILING_COMMAND_LEDGER.csv",
    "reports/CERTGEN_MAX_CEILING_CURRENT_STATE.json",
    "reports/CERTGEN_MAX_CEILING_REPAIR_AND_UPGRADE_CHANGELOG.md",
    "reports/CERTGEN_MAX_CEILING_TEST_MATRIX.md",
    "reports/CERTGEN_MAX_CEILING_NOTEBOOK_READINESS.md",
    "reports/CERTGEN_FAILURE_INJECTION_MATRIX.csv",
    "reports/CERTGEN_SENSITIVITY_MATRIX.csv",
    "reports/CERTGEN_OPERATIONAL_HYPOTHESIS_COVERAGE.csv",
    "reports/CERTGEN_CLAIM_EVIDENCE_MATRIX.csv",
    "reports/CERTGEN_ADAPTER_CONFORMANCE_MATRIX.csv",
    "docs/execution/CERTGEN_PROVENANCE_DAG_CONTRACT.md",
    "docs/execution/CERTGEN_RUN_CAPSULE_PROTOCOL.md",
    "docs/execution/CERTGEN_SCALE_LADDER_PROTOCOL.md",
    "docs/execution/CERTGEN_DETERMINISTIC_REPLAY_PROTOCOL.md",
    "docs/execution/CERTGEN_FAILURE_REHEARSAL_PROTOCOL.md",
    "docs/analysis/CERTGEN_RESOLUTION_PLANNING_PROTOCOL.md",
    "docs/analysis/CERTGEN_CROSS_FEATURE_CONSENSUS_POLICY.md",
    "docs/analysis/CERTGEN_COMPUTE_ACCOUNTING_PROTOCOL.md",
    "docs/analysis/CERTGEN_CLAIM_EVIDENCE_PROTOCOL.md",
    "docs/analysis/CERTGEN_FIGURE_TABLE_DATA_CONTRACTS.md",
)


def _has_claim_true(value: Any) -> bool:
    if isinstance(value, dict):
        return any((key == "claim_allowed" and item is True) or _has_claim_true(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_has_claim_true(item) for item in value)
    return False


def _claim_hits(root: Path) -> list[str]:
    hits: list[str] = []
    for directory in ("data", "reports", "release", "artifacts"):
        base = root / directory
        if not base.is_dir():
            continue
        for path in base.rglob("*.json*"):
            try:
                values = (
                    [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
                    if path.suffix == ".jsonl"
                    else [json.loads(path.read_text(encoding="utf-8"))]
                )
            except (OSError, json.JSONDecodeError):
                continue
            if any(_has_claim_true(value) for value in values):
                hits.append(str(path.relative_to(root)))
    return sorted(hits)


def run_maximum_ceiling_audit(
    *,
    root: str | Path = ".",
    require_archive: bool = True,
) -> dict[str, Any]:
    base = Path(root).resolve()
    checks: dict[str, dict[str, Any]] = {}

    def add(name: str, passed: bool, detail: Any) -> None:
        checks[name] = {"passed": bool(passed), "detail": detail}

    replacement_json = base / "reports/CERTGEN_REPLACEMENT_AUDIT.json"
    try:
        replacement = json.loads(replacement_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        replacement = {}
        add("replacement_audit", False, str(exc))
    else:
        add(
            "replacement_audit",
            replacement.get("expected_sha256") == "d1a144dfa317f766b4c86e108a605de9a346e5e0cbb071b2f29d70e17bf530af"
            and replacement.get("observed_sha256") == replacement.get("expected_sha256")
            and replacement.get("replacement_verified") is True
            and replacement.get("git_metadata_preserved") is True
            and replacement.get("stale_source_carried_forward") is False,
            replacement,
        )
    missing = [path for path in REQUIRED_ARTIFACTS if not (base / path).is_file()]
    add("required_artifacts", not missing, missing or "all present")
    bootstrap_contract_artifacts(root=base)
    with tempfile.TemporaryDirectory(prefix="certgen_maximum_ceiling_audit_") as temporary_name:
        temporary = Path(temporary_name)
        study_path = temporary / "study.yaml"
        frozen = freeze_study(
            "cifar_integrity_minimal",
            out_path=study_path,
            profile_root=base / "configs/cvpr/profiles",
            model_registry=base / "registry/cvpr/model_registry.yaml",
            feature_registry=base / "registry/cvpr/feature_space_registry.yaml",
            comparison_registry=base / "registry/cvpr/comparison_registry.csv",
        )
        add("fixture_study_frozen", frozen["status"] == "STUDY_FROZEN", frozen)
        provenance = verify_provenance_graph(study_path, registry_path=temporary / "empty.jsonl", root=temporary)
        add("provenance_dag_valid", provenance["passed"], provenance)
        capsule_path = temporary / "capsule.zip"
        first_capsule = build_run_capsule("preflight", study_path, root=base, output=capsule_path)
        first_hash = first_capsule["capsule_sha256"]
        second_capsule = build_run_capsule("preflight", study_path, root=base, output=capsule_path)
        capsule_verdict = verify_run_capsule(capsule_path)
        add(
            "run_capsule_deterministic",
            first_hash == second_capsule["capsule_sha256"] and capsule_verdict["passed"],
            capsule_verdict,
        )
        scale = freeze_scale_plan(study_path, root=temporary)
        scale_status = scale_plan_status(study_path, root=temporary)
        add("scale_ladder_frozen", scale_status["passed"], scale)
        sensitivity = freeze_sensitivity(study_path, root=temporary)
        sensitivity_status = validate_sensitivity(study_path, root=temporary)
        add("sensitivity_registry_valid", sensitivity_status["passed"], sensitivity)
        resolution = plan_resolution(study_path, root=temporary, trials=32)
        add(
            "planning_simulation_labeled",
            resolution["planning_simulation_only"]
            and resolution["not_model_evidence"]
            and resolution["not_empirical_power"]
            and resolution["claim_allowed"] is False,
            resolution,
        )
        failures = rehearse_failures(root=temporary)
        add("failure_rehearsal", failures["passed"] and failures["cases"] == 16, failures)
        replay_plan(study_path, root=temporary, changed_paths=["preprocessing.yaml"])
        replay = verify_replay_plan(study_path, root=temporary)
        add("deterministic_replay", replay["passed"], replay)
        accounting = summarize_accounting(study_path, root=temporary)
        add("accounting_contract", accounting["status"] == "BLOCKED_REAL_EXECUTION" and not accounting["errors"], accounting)
        rehearsal = run_builder_faithful_synthetic(temporary / "builder_rehearsal")
        add(
            "builder_faithful_rehearsal",
            rehearsal.get("rehearsal_status") == "COMPLETE_BUILDER_FAITHFUL_SYNTHETIC_REHEARSAL_PASS"
            and rehearsal.get("metric_reproduction_status") == "PASS"
            and rehearsal.get("sanity_controls_status") == "PASS"
            and rehearsal.get("family_certificate_coverage_status") == "FAMILY_CERTIFICATES_COMPLETE",
            rehearsal,
        )
    doctor = doctor_report(root=base)
    add("doctor_classification", doctor["status"] in {"PASS", "BLOCKED_REAL_INPUT", "BLOCKED_REAL_EXECUTION"}, doctor)
    claims = validate_claims(matrix_path=base / "reports/CERTGEN_CLAIM_EVIDENCE_MATRIX.csv")
    add("claim_evidence_matrix_fail_closed", claims["passed"], claims)
    figures = validate_figure_table_contracts(root=base)
    add("figure_table_contracts", figures["passed"], figures)
    optional = validate_optional_lanes(base / "registry/cvpr/optional_extension_lanes.yaml")
    add("optional_lanes_nonblocking", optional["passed"], optional)
    notebooks = analyze_all(base / path for path in (
        "notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb",
        "notebooks/kaggle/certgen_cvpr_cifar10_generation_t4x2_1k.ipynb",
        "notebooks/kaggle/certgen_cvpr_generation_t4x2_generic.ipynb",
        "notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_1k.ipynb",
        "notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_generic.ipynb",
    ))
    add("notebooks_local_contract", notebooks["passed"] and len(notebooks["results"]) == 5, notebooks)
    claim_hits = _claim_hits(base)
    add("no_claim_allowed_true", not claim_hits, claim_hits or "none")
    archive = base / "dist/certgen_max_ceiling_pre_run.zip"
    manifest_path = archive.with_suffix(archive.suffix + ".manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        archive_passed = not require_archive
        archive_detail: Any = str(exc)
    else:
        archive_passed = (
            archive.is_file()
            and manifest.get("status") == "ARCHIVE_VERIFIED"
            and manifest.get("archive_sha256")
            and manifest.get("errors") == []
            and manifest.get("portable_tests", {}).get("returncode") == 0
            and manifest.get("portable_notebook_audit", {}).get("returncode") == 0
            and manifest.get("portable_synthetic_runtime", {}).get("returncode") == 0
        )
        archive_detail = {
            "status": manifest.get("status"),
            "sha256": manifest.get("archive_sha256"),
            "members": manifest.get("member_count"),
        }
    add("portable_archive_verified", archive_passed, archive_detail)
    passed = all(row["passed"] for row in checks.values())
    if not replacement.get("replacement_verified"):
        status = "INPLACE_REPLACEMENT_FAILED"
    elif passed:
        status = "CERTGEN_MAX_CEILING_PRE_RUN_READY"
    elif any(not row["passed"] for name, row in checks.items() if name not in {"portable_archive_verified"}):
        status = "LOCAL_PRE_RUN_DEFECT_REMAINS"
    else:
        status = "REPLACEMENT_VERIFIED_SUPERCHARGE_PARTIAL"
    return {
        "schema_version": "certgen.maximum_ceiling.audit.v1",
        "status": status,
        "sub_status": "BLOCKED_ONLY_BY_REAL_INPUTS_AND_REAL_EXECUTION" if passed else "LOCAL_REPAIR_REQUIRED",
        "passed": passed,
        "checks_passed": sum(row["passed"] for row in checks.values()),
        "checks_total": len(checks),
        "checks": checks,
        "exact_next_command": "python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain",
        "further_speculative_pre_run_build_justified": False if passed else None,
        "evidence_class": "local_and_synthetic_validation_only",
        "claim_allowed": False,
    }
