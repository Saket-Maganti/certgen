"""Independent local-only audit for the 100% pre-run readiness seal."""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from certgen.core.io import write_json
from certgen.core.hashing import file_sha256
from certgen.cvpr.builder_faithful import run_builder_faithful_synthetic
from certgen.cvpr.controls import validate_controls
from certgen.cvpr.operational import validate_family_operational
from certgen.cvpr.output_schemas import OUTPUT_SCHEMAS
from certgen.cvpr.profiles import load_profile, validate_profile
from certgen.cvpr.study import require_frozen_study
from certgen.notebooks.cvpr_static_analyzer import analyze_all
from certgen.notebooks.worker_contract import (
    COMPLETION_SCHEMA_VERSION,
    IMPLEMENTATION_VERSIONS,
    completion_identity_fields,
    validate_completion_identity,
)
from certgen.paper.v9_paper_firewall import run_firewall
from certgen.pipeline.v9_next_action import determine_next_action
from certgen.release.archive import EXCLUDED_SUFFIXES, archive_members


REQUIRED_LOCAL_ARTIFACTS = (
    "reports/CERTGEN_FINAL_100_PERCENT_BASELINE.md",
    "reports/CERTGEN_FINAL_100_PERCENT_COMMAND_LEDGER.csv",
    "reports/CERTGEN_FINAL_100_PERCENT_CURRENT_STATE.json",
    "reports/CERTGEN_FINAL_100_PERCENT_REPAIR_CHANGELOG.md",
    "reports/CERTGEN_FINAL_100_PERCENT_TEST_MATRIX.md",
    "reports/CERTGEN_FINAL_100_PERCENT_NOTEBOOK_READINESS.md",
    "reports/CERTGEN_OPERATIONAL_HYPOTHESIS_COVERAGE.csv",
    "reports/CERTGEN_ADAPTER_CONFORMANCE_MATRIX.csv",
    "docs/execution/CERTGEN_REFERENCE_DRAW_PLAN_PROTOCOL.md",
    "docs/execution/CERTGEN_CONTROL_ARTIFACT_PROTOCOL.md",
    "docs/execution/CERTGEN_CERTIFICATE_INPUT_BUNDLE_CONTRACT.md",
    "docs/execution/CERTGEN_OPERATIONAL_FAMILY_GATE.md",
    "docs/execution/CERTGEN_ARTIFACT_DRIVEN_NEXT_ACTION.md",
    "docs/execution/CERTGEN_WORKER_VERSION_CONTRACT.md",
    "docs/legal/CERTGEN_CLIP_ASSET_AND_REDISTRIBUTION_POLICY.md",
    "docs/analysis/CERTGEN_PILOT_STOP_GO_PROTOCOL.md",
    "docs/analysis/CERTGEN_CERTIFICATE_LINEAGE_CARD.md",
    "docs/analysis/CERTGEN_PARTIAL_RANKING_PROVENANCE.md",
    "release/CERTGEN_PORTABLE_TEST_MANIFEST.json",
    "CERTGEN_CVPR_100_PERCENT_PRE_RUN_EXECUTION_HANDBOOK.md",
)
WEIGHT_SUFFIXES = {".bin", ".ckpt", ".msgpack", ".onnx", ".pt", ".pth", ".safetensors"}


def _claim_true(value: Any) -> bool:
    if isinstance(value, dict):
        return any((key == "claim_allowed" and item is True) or _claim_true(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_claim_true(item) for item in value)
    return False


def _structured_claim_hits(root: Path) -> list[str]:
    hits: list[str] = []
    for name in ("data", "reports", "release"):
        base = root / name
        if not base.is_dir():
            continue
        for path in base.rglob("*.json*"):
            try:
                values = (
                    [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
                    if path.suffix == ".jsonl"
                    else [json.loads(path.read_text(encoding="utf-8"))]
                )
            except (OSError, json.JSONDecodeError):
                continue
            if any(_claim_true(value) for value in values):
                hits.append(str(path.relative_to(root)))
    return sorted(hits)


def run_final_pre_run_audit(
    out_root: str | Path = "reports/final_pre_run_audit",
    *,
    root: str | Path = ".",
    dry_run: bool = False,
) -> dict[str, Any]:
    base = Path(root).resolve()
    output = Path(out_root)
    output = output if output.is_absolute() else base / output
    if dry_run:
        return {
            "status": "FINAL_PRE_RUN_AUDIT_DRY_RUN",
            "planned_checks": 24,
            "writes": [str(output / "audit.json"), str(base / "reports/CERTGEN_FINAL_100_PERCENT_HANDOFF_AUDIT.md")],
            "claim_allowed": False,
        }
    checks: dict[str, dict[str, Any]] = {}

    def add(name: str, passed: bool, detail: Any) -> None:
        checks[name] = {"passed": bool(passed), "detail": detail}

    missing = [path for path in REQUIRED_LOCAL_ARTIFACTS if not (base / path).is_file()]
    add("required_local_artifacts", not missing, missing or "all present")
    profile = load_profile("cifar_integrity_minimal", base / "configs/cvpr/profiles")
    profile_verdict = validate_profile(profile)
    add("selected_pilot_profile_valid", profile_verdict["passed"], profile_verdict)

    with tempfile.TemporaryDirectory(prefix="certgen_final_pre_run_audit_") as temporary:
        temporary_root = Path(temporary)
        rehearsal = run_builder_faithful_synthetic(temporary_root / "rehearsal")
        rehearsal_root = temporary_root / "rehearsal"
        fixture_study = require_frozen_study(rehearsal_root / "study.yaml")
        add("frozen_study_valid", bool(fixture_study.get("frozen")), fixture_study["configuration_hash"])
        add(
            "complete_builder_faithful_synthetic_rehearsal",
            rehearsal.get("rehearsal_status") == "COMPLETE_BUILDER_FAITHFUL_SYNTHETIC_REHEARSAL_PASS",
            rehearsal,
        )
        add("reference_draw_builder_fixture", "canonical_reference_draw" in rehearsal["stages"], rehearsal["stages"])
        controls_root = next((rehearsal_root / "controls").iterdir())
        controls = validate_controls(controls_root, study_hash=fixture_study["configuration_hash"])
        add("control_builder_fixture", controls["passed"], controls)
        add("preflight_package_builder", "preflight_builder" in rehearsal["stages"], rehearsal["stages"])
        add("generation_package_builder", "generation_builder" in rehearsal["stages"], rehearsal["stages"])
        add("feature_package_builder", "feature_builder_embedded_images" in rehearsal["stages"], rehearsal["stages"])
        add("cache_v2_merge", rehearsal.get("complete_cache_groups") == 9, rehearsal.get("complete_cache_groups"))
        add("family_builder", "family_freeze" in rehearsal["stages"], rehearsal.get("family_hash"))
        add("certificate_input_builder", rehearsal.get("certificate_input_bundles") == 2, rehearsal.get("certificate_input_bundles"))
        operational = validate_family_operational(
            family_path=rehearsal_root / "family/family.json",
            study_path=rehearsal_root / "study.yaml",
            inputs_root=rehearsal_root / "certificate_inputs",
            write_result=False,
        )
        add("family_operational_gate", operational["passed"], operational)

        firewall = run_firewall(temporary_root / "firewall.json", temporary_root / "firewall.md")
        add("paper_firewall_closed", firewall["passed"] and firewall["claim_allowed"] is False, firewall)

    exact = completion_identity_fields(
        "feature", config_schema_version="fixture.config.v1", output_schema_version="fixture.output.v1"
    )
    current_worker = validate_completion_identity(
        exact,
        worker_type="feature",
        config_schema_version="fixture.config.v1",
        output_schema_version="fixture.output.v1",
    )
    stale_worker = validate_completion_identity(
        {**exact, "worker_implementation_version": "stale"},
        worker_type="feature",
        config_schema_version="fixture.config.v1",
        output_schema_version="fixture.output.v1",
    )
    add(
        "worker_contract_consistent",
        current_worker["passed"] and not stale_worker["passed"] and COMPLETION_SCHEMA_VERSION.endswith("v3"),
        {"implementations": IMPLEMENTATION_VERSIONS, "current": current_worker, "stale": stale_worker},
    )
    add(
        "output_schemas_consistent",
        set(OUTPUT_SCHEMAS) == {"preflight", "generation", "feature"},
        {key: value.schema_version for key, value in OUTPUT_SCHEMAS.items()},
    )
    action = determine_next_action(root=base)
    required_action_fields = {
        "status", "reason", "exact_command", "cwd", "input_artifact_ids", "input_paths",
        "expected_output_artifact", "success_validator", "CPU_or_GPU", "network_policy",
        "planning_runtime", "evidence_class", "claim_permission", "failure_recovery",
    }
    forbidden_paths = {
        "data/features/cvpr/features.npz", "data/features/cvpr/sidecar.json",
        "configs/cvpr/frozen_study.yaml", "artifacts/cvpr/reference_draw_plan.json",
    }
    source = (base / "certgen/pipeline/v9_next_action.py").read_text(encoding="utf-8")
    add("artifact_driven_next_action", required_action_fields.issubset(action) and not any(value in source for value in forbidden_paths), action)
    add("no_hardcoded_nonexistent_late_paths", not any(value in source for value in forbidden_paths), sorted(forbidden_paths))

    registry_payload = yaml.safe_load((base / "registry/cvpr/feature_space_registry.yaml").read_text(encoding="utf-8"))
    clip = next(row for row in registry_payload["feature_spaces"] if row["feature_space_id"] == "clip")
    member_names = [path.relative_to(base).as_posix() for path in archive_members(base)]
    clip_policy = (
        clip.get("redistribution_allowed") is False
        and clip.get("public_archive_included") is False
        and clip.get("user_provided") is True
        and clip.get("private_mount_required") is True
        and WEIGHT_SUFFIXES.issubset(EXCLUDED_SUFFIXES)
        and not any(Path(name).suffix in WEIGHT_SUFFIXES for name in member_names)
    )
    add("clip_weights_excluded", clip_policy, {"registry": clip, "weight_members": [name for name in member_names if Path(name).suffix in WEIGHT_SUFFIXES]})

    archive_path = base / "dist/certgen_cvpr_100_percent_pre_run.zip"
    archive_status_path = archive_path.with_suffix(archive_path.suffix + ".manifest.json")
    archive_status = json.loads(archive_status_path.read_text(encoding="utf-8")) if archive_status_path.is_file() else {}
    archive_names: list[str] = []
    if archive_path.is_file():
        with zipfile.ZipFile(archive_path) as archive:
            archive_names = archive.namelist()
    portable_passed = (
        archive_status.get("status") == "ARCHIVE_VERIFIED"
        and archive_status.get("errors") == []
        and archive_status.get("archive_sha256")
        and archive_status.get("archive_sha256") == file_sha256(archive_path)
        and not any(Path(name).suffix in WEIGHT_SUFFIXES for name in archive_names)
        and archive_status.get("portable_tests", {}).get("returncode") == 0
        and archive_status.get("portable_notebook_audit", {}).get("returncode") == 0
        and archive_status.get("portable_synthetic_runtime", {}).get("returncode") == 0
    )
    add(
        "portable_archive_verified",
        bool(portable_passed),
        {
            "status": archive_status.get("status"),
            "member_count": archive_status.get("member_count"),
            "archive_sha256": archive_status.get("archive_sha256"),
            "weight_members": [name for name in archive_names if Path(name).suffix in WEIGHT_SUFFIXES],
        },
    )

    state = json.loads((base / "reports/CERTGEN_FINAL_100_PERCENT_CURRENT_STATE.json").read_text(encoding="utf-8"))
    separate = isinstance(state.get("LIVE_CHECKOUT_VERIFICATION"), dict) and isinstance(state.get("PORTABLE_ARCHIVE_VERIFICATION"), dict)
    add("live_portable_reporting_separate", separate, {key: state.get(key) for key in ("LIVE_CHECKOUT_VERIFICATION", "PORTABLE_ARCHIVE_VERIFICATION")})
    notebooks = analyze_all()
    add("notebooks_static", notebooks["passed"] and len(notebooks["results"]) == 5, notebooks)
    claim_hits = _structured_claim_hits(base)
    add("no_claim_allowed_true", not claim_hits, claim_hits or "none")
    add("no_local_defect_remains", all(row["passed"] for row in checks.values()), "derived from all preceding checks")

    passed = all(row["passed"] for row in checks.values())
    status = "CVPR_100_PERCENT_PRE_RUN_READY" if passed else "FINAL_PRE_RUN_LOCAL_DEFECT_REMAINS"
    result = {
        "schema_version": "certgen.final_pre_run_audit.v1",
        "status": status,
        "sub_status": "BLOCKED_ONLY_BY_REAL_INPUTS_AND_REAL_EXECUTION" if passed else "LOCAL_REPAIR_REQUIRED",
        "passed": passed,
        "checks_passed": sum(row["passed"] for row in checks.values()),
        "checks_total": len(checks),
        "checks": checks,
        "exact_next_command": action["exact_command"],
        "real_evidence_status": "none",
        "evidence_class": "local_and_synthetic_validation_only",
        "claim_allowed": False,
    }
    output.mkdir(parents=True, exist_ok=True)
    write_json(result, output / "audit.json")
    lines = [
        "# CertGen Final 100% Pre-Run Handoff Audit", "",
        f"Status: `{status}`", f"Sub-status: `{result['sub_status']}`",
        f"Checks: `{result['checks_passed']}/{result['checks_total']}`", "Claim allowed: `false`", "",
        "| Check | Passed |", "|---|---:|",
        *[f"| `{name}` | `{row['passed']}` |" for name, row in checks.items()],
    ]
    (base / "reports/CERTGEN_FINAL_100_PERCENT_HANDOFF_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result
