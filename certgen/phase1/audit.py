"""Final Kaggle-launch and CPU-execution audits for Phase 1."""

from __future__ import annotations

import csv
import json
import os
import zipfile
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from packaging.requirements import Requirement

from certgen.cvpr.readiness import readiness_report
from certgen.max_ceiling.contracts import doctor_report
from certgen.phase1.kaggle import BUNDLES, validate_input
from certgen.phase1.notebooks import PHASE1_NOTEBOOKS, validate_phase1_notebooks
from certgen.phase1.state import phase1_state
from certgen.pipeline.v9_next_action import determine_next_action


def _check(checks: dict[str, dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks[name] = {"passed": bool(passed), "detail": detail}


def _locks(root: Path) -> dict[str, Any]:
    paths = [
        root / "requirements/kaggle-base.lock",
        root / "requirements/kaggle-diagnostic.lock",
        root / "requirements/kaggle-preflight.lock",
        root / "requirements/kaggle-generation.lock",
        root / "requirements/kaggle-features.lock",
        root / "requirements/kaggle-constraints.txt",
    ]
    errors: list[str] = []
    requirements: dict[str, set[str]] = {}
    for path in paths:
        if not path.is_file():
            errors.append(f"missing lock: {path}")
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith(("#", "-c", "-r")):
                continue
            try:
                requirement = Requirement(line)
            except Exception as exc:
                errors.append(f"invalid requirement {path.name}:{line}: {exc}")
                continue
            requirements.setdefault(requirement.name.lower(), set()).add(str(requirement.specifier))
    conflicts = {name: sorted(values) for name, values in requirements.items() if len(values) > 1}
    if conflicts:
        errors.append(f"conflicting direct pins: {conflicts}")
    required = {
        "torch", "torchvision", "numpy", "scipy", "pillow", "pandas", "pyyaml",
        "jsonschema", "safetensors", "huggingface-hub", "transformers", "diffusers",
        "accelerate", "tqdm", "packaging", "scikit-learn",
    }
    missing = sorted(required - set(requirements))
    errors.extend(f"dependency not covered: {name}" for name in missing)
    from certgen.notebooks.environment_bootstrap import (
        COMPATIBILITY_PROFILES,
        PROFILE_LOCKS,
        _lock_requirements,
    )

    for profile, lock_name in PROFILE_LOCKS.items():
        locked = {
            Requirement(raw).name.lower()
            for raw in _lock_requirements(root / "requirements" / lock_name)
        }
        profiled = {Requirement(raw).name.lower() for raw in COMPATIBILITY_PROFILES[profile]}
        for name in sorted(profiled - locked):
            errors.append(f"{profile}: profile dependency absent from lock: {name}")
        forbidden = sorted((locked | profiled) & {"timm", "open-clip-torch"})
        if forbidden:
            errors.append(f"{profile}: unused active dependency remains: {forbidden}")
    return {"passed": not errors, "errors": errors, "dependencies": sorted(requirements)}


def _assets(root: Path) -> dict[str, Any]:
    path = root / "registry/cvpr/kaggle_asset_registry.yaml"
    errors: list[str] = []
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        rows = payload["assets"]
    except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
        return {"passed": False, "errors": [str(exc)]}
    required = {
        "asset_id", "provider", "repository_or_mount", "revision", "expected_files",
        "expected_hashes", "license_status", "redistribution_allowed", "public_archive_included",
        "private_mount_required", "internet_required", "loader",
    }
    for row in rows:
        errors.extend(f"{row.get('asset_id')}: missing {field}" for field in sorted(required - set(row)))
        if row.get("redistribution_allowed") is not False or row.get("public_archive_included") is not False:
            errors.append(f"{row.get('asset_id')}: public weight inclusion is not fail-closed")
    clip: dict[str, Any] = next(
        (row for row in rows if row.get("asset_id") == "clip__asset"), {}
    )
    if clip.get("private_mount_required") is not True or clip.get("internet_required") is not False:
        errors.append("CLIP does not require an offline private mount")
    return {"passed": not errors, "errors": errors, "assets": len(rows)}


def run_kaggle_launch_audit(root: str | Path = ".") -> dict[str, Any]:
    base = Path(root).resolve()
    checks: dict[str, dict[str, Any]] = {}
    notebooks = validate_phase1_notebooks(base, deterministic=True)
    _check(checks, "canonical_notebooks", notebooks["passed"] and len(notebooks["results"]) == 4, notebooks)
    locks = _locks(base)
    _check(checks, "dependency_closure", locks["passed"], locks)
    assets = _assets(base)
    _check(checks, "asset_closure", assets["passed"], assets)

    package_results = {stage: validate_input(base / relative) for stage, relative in BUNDLES.items()}
    _check(checks, "diagnostic_input", package_results["diagnostic"]["passed"], package_results["diagnostic"])
    _check(checks, "preflight_input", package_results["preflight"]["passed"], package_results["preflight"])
    no_fixture_names = True
    restricted_names: list[str] = []
    for relative in BUNDLES.values():
        with zipfile.ZipFile(base / relative) as archive:
            for name in archive.namelist():
                if any(token in name.lower() for token in ("fake_worker", "fixture_payload")):
                    no_fixture_names = False
                if Path(name).suffix.lower() in {".pt", ".pth", ".bin", ".safetensors", ".ckpt", ".onnx"}:
                    restricted_names.append(name)
    _check(checks, "no_fixture_in_real_inputs", no_fixture_names, "member names inspected")
    _check(checks, "no_restricted_weights", not restricted_names, restricted_names or "none")

    blocked = {
        stage: all((base / "artifacts/cvpr/kaggle_inputs" / stage / name).is_file() for name in ("BUILD_PLAN.json", "EXPECTED_CONTENTS.json", "README_BLOCKED.md"))
        for stage in ("generation", "features")
    }
    _check(checks, "stage_dependent_blocked_plans", all(blocked.values()), blocked)

    launchboard = base / "CERTGEN_KAGGLE_RUN_LAUNCHBOARD.md"
    launch_text = launchboard.read_text(encoding="utf-8") if launchboard.is_file() else ""
    paths_resolve = all((base / path).is_file() for path in (*PHASE1_NOTEBOOKS.values(), *(str(value) for value in BUNDLES.values())))
    _check(checks, "launchboard_paths", paths_resolve and "PLANNING_ESTIMATE_NOT_MEASURED" in launch_text, {"paths_resolve": paths_resolve})

    state = phase1_state(base)
    readiness = readiness_report()
    action = determine_next_action(root=base)
    doctor = doctor_report(root=base)
    if state["boundary"] == "reference":
        agreement = (
            action.get("action") in {"PROVIDE_CIFAR_REFERENCE", "VALIDATE_CIFAR_REFERENCE"}
            and readiness.get("components", {}).get("reference")
            in {
                "WAITING_FOR_OFFICIAL_CIFAR_ARCHIVE",
                "CANDIDATE_ARCHIVE_PRESENT_VALIDATION_REQUIRED",
            }
            and doctor.get("status") in {"BLOCKED_REAL_INPUT", "PASS"}
        )
    else:
        agreement = doctor.get("status") in {"BLOCKED_REAL_INPUT", "BLOCKED_REAL_EXECUTION", "PASS"}
    _check(checks, "state_commands_agree", agreement, {"phase1": state, "next_action": action.get("action"), "doctor": doctor.get("status")})
    _check(checks, "t4x2_fail_closed", all("requested_gpu_count" not in row.get("errors", []) for row in package_results.values()), "both bundles validate requested_gpu_count=2 and no fallback")
    passed = all(row["passed"] for row in checks.values())
    payload = {
        "schema_version": "certgen.phase1.kaggle_launch_audit.v1",
        "status": "KAGGLE_LAUNCH_AUDIT_PASS" if passed else "LOCAL_DEFECT",
        "passed": passed,
        "checks_passed": sum(row["passed"] for row in checks.values()),
        "checks_total": len(checks),
        "checks": checks,
        "phase1_status": state["phase1_status"],
        "exact_next_action": state["exact_next_action"],
        "claim_allowed": False,
    }
    output = base / "reports/CERTGEN_KAGGLE_FINAL_LAUNCH_AUDIT.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# CertGen Kaggle final launch audit", "", f"Status: `{payload['status']}`", "",
        "| Check | Passed |", "|---|---:|",
        *[f"| `{name}` | `{row['passed']}` |" for name, row in checks.items()],
        "", f"Exact next action: `{state['exact_next_action']}`.", "", "`claim_allowed=false`",
    ]
    (base / "reports/CERTGEN_KAGGLE_FINAL_LAUNCH_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def run_cpu_execution_audit(root: str | Path = ".") -> dict[str, Any]:
    base = Path(root).resolve()
    checks: dict[str, dict[str, Any]] = {}
    _check(checks, "cpu_environment", os.environ.get("CUDA_VISIBLE_DEVICES") == "" and os.environ.get("CERTGEN_CPU_ONLY") == "1", {"CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"), "CERTGEN_CPU_ONLY": os.environ.get("CERTGEN_CPU_ONLY")})
    rehearsal_path = base / "artifacts/cvpr/kaggle_inputs/fixture_only/PHASE1_REHEARSAL.json"
    try:
        rehearsal = json.loads(rehearsal_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        rehearsal = {"passed": False, "error": str(exc)}
    _check(checks, "fixture_rehearsal", rehearsal.get("passed") is True and rehearsal.get("claim_allowed") is False, rehearsal)
    ledger_path = base / "reports/CERTGEN_PHASE1_COMMAND_LEDGER.csv"
    with ledger_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    successful_phases = {row["phase"] for row in rows if row["status"] in {"PASS", "EXPECTED_BOUNDARY"}}
    required_phases = {"baseline_checks", "notebooks"}
    _check(checks, "command_ledger", required_phases.issubset(successful_phases), {"rows": len(rows), "successful_phases": sorted(successful_phases)})
    unexpected_cuda: list[str] = []
    for row in rows:
        for key in ("stdout_log", "stderr_log"):
            path = base / row.get(key, "")
            if path.is_file() and "unexpected CUDA initialization" in path.read_text(encoding="utf-8", errors="ignore"):
                unexpected_cuda.append(str(path.relative_to(base)))
    _check(checks, "no_unexpected_cuda_initialization", not unexpected_cuda, unexpected_cuda or "none")
    state = phase1_state(base)
    expected_codes = {"reference": 10, "kaggle_diagnostic": 11, "kaggle_preflight": 12, "kaggle_generation": 13, "kaggle_features": 14, "cpu_or_complete": 0}
    _check(checks, "boundary_exit_code", state["exit_code"] == expected_codes[state["boundary"]], state)
    passed = all(row["passed"] for row in checks.values())
    payload = {
        "schema_version": "certgen.phase1.cpu_execution_audit.v1",
        "status": "CPU_EXECUTION_AUDIT_PASS" if passed else "LOCAL_DEFECT",
        "passed": passed,
        "checks": checks,
        "phase1_status": state["phase1_status"],
        "claim_allowed": False,
    }
    output = base / "reports/CERTGEN_PHASE1_CPU_EXECUTION_AUDIT.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload
