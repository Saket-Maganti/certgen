"""Canonical CVPR-native stage dispatcher with legacy-compatible action labels."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from certgen.core.hashing import file_sha256
from certgen.core.io import read_json, write_json


STAGES = [
    "REFERENCE_SOURCE_REQUIRED",
    "REFERENCE_VALIDATION_REQUIRED",
    "REFERENCE_MATERIALIZATION_REQUIRED",
    "KAGGLE_DIAGNOSTIC_REQUIRED",
    "PREFLIGHT_CONFIG_REQUIRED",
    "KAGGLE_PREFLIGHT_REQUIRED",
    "PREFLIGHT_IMPORT_REQUIRED",
    "GENERATION_CONFIG_REQUIRED",
    "KAGGLE_GENERATION_REQUIRED",
    "GENERATION_IMPORT_REQUIRED",
    "FEATURE_CONFIG_REQUIRED",
    "KAGGLE_FEATURE_EXTRACTION_REQUIRED",
    "FEATURE_IMPORT_REQUIRED",
    "FEATURE_MERGE_REQUIRED",
    "CACHE_VALIDATION_REQUIRED",
    "GATE_CONFIGS_REQUIRED",
    "METRIC_REPRODUCTION_REQUIRED",
    "SANITY_GATES_REQUIRED",
    "FAMILY_FREEZE_REQUIRED",
    "REFERENCE_DRAW_REQUIRED",
    "CONTROLS_REQUIRED",
    "CERTIFICATE_INPUTS_REQUIRED",
    "CERTIFICATE_INPUTS_VALIDATION_REQUIRED",
    "FAMILY_OPERATIONAL_VALIDATION_REQUIRED",
    "FAMILY_CERTIFICATES_REQUIRED",
    "FIRST_PILOT_REQUIRED",
    "PARTIAL_RANKING_REQUIRED",
    "CROSS_FEATURE_ANALYSIS_REQUIRED",
    "STOP_AND_INTERPRET",
]

# Historical public labels remain accepted by compatibility audits, but no
# current command routes through V6/V9 wrappers or notebooks.
ACTIONS = [
    "PROVIDE_CIFAR_REFERENCE",
    "VALIDATE_CIFAR_REFERENCE",
    "MATERIALIZE_CIFAR_REFERENCE",
    "RUN_KAGGLE_ENVIRONMENT_DIAGNOSTIC",
    "PREPARE_PREFLIGHT_CONFIG",
    "RUN_KAGGLE_CHECKPOINT_PREFLIGHT",
    "IMPORT_CHECKPOINT_PREFLIGHT_ZIP",
    "PREPARE_GENERATION_CONFIG",
    "RUN_KAGGLE_GENERATION_1K",
    "IMPORT_GENERATION_ZIP",
    "PREPARE_FEATURE_CONFIG",
    "RUN_KAGGLE_FEATURE_EXTRACTION_1K",
    "IMPORT_FEATURE_ZIP",
    "MERGE_FEATURE_CACHES",
    "VALIDATE_FEATURE_CACHES",
    "PREPARE_GATE_CONFIGS",
    "RUN_METRIC_REPRODUCTION",
    "RUN_METRIC_SANITY_GATES",
    "FREEZE_FAMILY",
    "PREPARE_REFERENCE_DRAW",
    "PREPARE_CONTROLS",
    "PREPARE_CERTIFICATE_INPUTS",
    "VALIDATE_CERTIFICATE_INPUTS",
    "VALIDATE_FAMILY_OPERATIONAL",
    "RUN_FAMILY_CERTIFICATES",
    "RUN_FIRST_CERTIFICATE_PILOT",
    "BUILD_PARTIAL_RANKING",
    "RUN_CROSS_FEATURE_ANALYSIS",
    "STOP_FIRST_PILOT_COMPLETE",
]


def _json(path: str | Path) -> dict[str, Any]:
    try:
        return read_json(path)
    except Exception:
        return {}


def _reference_manifest_materialized(
    root: Path, path: str | Path = "registry/manifests/cvpr/cifar10_reference.jsonl"
) -> bool:
    manifest = root / Path(path)
    if not manifest.is_file():
        # Legacy materialization is accepted as input state, never as guidance.
        manifest = root / "registry/manifests/cifar10_r1_reference.jsonl"
    if not manifest.is_file():
        return False
    return sum(1 for line in manifest.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()) >= 10000


def _make(
    *,
    status: str,
    action: str,
    reason: str,
    command: str,
    notebook: str | None,
    location: str,
    expected_input: str,
    expected_output: str,
    validator: str,
    runtime: str,
    network_policy: str,
    recovery: str,
    blocker: str | None = None,
    cwd: str | None = None,
    input_artifact_ids: list[str] | None = None,
    input_paths: list[str] | None = None,
    expected_output_artifact: str | None = None,
) -> dict[str, Any]:
    if status not in STAGES or action not in ACTIONS:
        raise ValueError("unknown canonical next-action state")
    gpu = location == "Kaggle T4x2"
    return {
        "status": status,
        "action": action,
        "reason": reason,
        "exact_command": command,
        "cwd": cwd or str(Path.cwd().resolve()),
        "input_artifact_ids": list(input_artifact_ids or []),
        "input_paths": list(input_paths or ([expected_input] if expected_input else [])),
        "expected_output_artifact": expected_output_artifact or expected_output,
        "notebook_path": notebook,
        "execution_location": location,
        "input": expected_input,
        "expected_input": expected_input,
        "expected_output": expected_output,
        "success_validator": validator,
        "planning_runtime": runtime,
        "estimated_runtime": runtime,
        "CPU_or_GPU": "GPU" if gpu else "CPU",
        "cpu_or_gpu": "GPU" if gpu else "CPU",
        "network_policy": network_policy,
        "network_requirement": network_policy,
        "failure_recovery": recovery,
        "location": "Kaggle" if gpu else "CPU",
        "kaggle_or_local": location,
        "evidence_class": "run_log_only" if gpu else "planning_only",
        "claim_permission": False,
        "claim_allowed": False,
        "evidence_allowed": False,
        "blocker": blocker,
        "no_fake_results": True,
        "not_paper_evidence": True,
        "canonical_handbook": "CERTGEN_CVPR_100_PERCENT_PRE_RUN_EXECUTION_HANDBOOK.md",
        "legacy_compatibility": "LEGACY_COMPATIBILITY_ONLY_NOT_CANONICAL_GUIDANCE",
    }


def _registry_rows(root: Path, registry_path: str | Path) -> list[dict[str, Any]]:
    path = Path(registry_path)
    path = path if path.is_absolute() else root / path
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        artifact = Path(str(row.get("path", "")))
        artifact = artifact if artifact.is_absolute() else root / artifact
        digest = row.get("hash", {}).get("value") if isinstance(row.get("hash"), dict) else None
        if artifact.is_file() and digest == file_sha256(artifact):
            rows.append({**row, "_resolved_path": str(artifact.resolve())})
    return rows


def _latest(rows: list[dict[str, Any]], *artifact_types: str) -> dict[str, Any]:
    matches = [row for row in rows if row.get("artifact_type") in set(artifact_types)]
    return matches[-1] if matches else {}


def _discover(root: Path, pattern: str) -> Path | None:
    matches = sorted(path for path in root.glob(pattern) if path.is_file())
    return matches[-1].resolve() if matches else None


def determine_next_action(
    *, root: str | Path = ".", registry_path: str | Path = "data/artifact_registry.jsonl"
) -> dict[str, Any]:
    base = Path(root).resolve()
    rows = _registry_rows(base, registry_path)
    onramp = _json(base / "data/results/v9_cifar_reference_onramp.json")
    diagnostic_import = _json(base / "data/results/cvpr/diagnostic_import_status.json")
    preflight_import = _json(base / "data/results/cvpr/preflight_import_status.json")
    generation_import = _json(base / "data/results/cvpr/generation_import_status.json")
    feature_import = _json(base / "data/results/cvpr/feature_import_status.json")
    merged_statuses = [_json(path) for path in sorted((base / "data/features/cvpr").glob("*/status.json"))]
    merged = next((row for row in reversed(merged_statuses) if row.get("passed") is True), {})
    cache_validation = _json(base / "data/results/cvpr/cache_validation_status.json")
    metric_result_path = base / "data/results/cvpr/metric_reproduction.json"
    sanity_result_path = base / "data/results/cvpr/sanity_controls.json"
    metric = _json(metric_result_path)
    sanity = _json(sanity_result_path)
    metric_config_path = base / "configs/cvpr/frozen_metric_reproduction.yaml"
    sanity_config_path = base / "configs/cvpr/frozen_sanity.yaml"
    family_path = _discover(base, "artifacts/cvpr/family/**/family.json")
    family = _json(family_path) if family_path else {}
    certificate_coverage_path = base / "data/results/cvpr/certificates/family_certificate_coverage.json"
    certificate_coverage = _json(certificate_coverage_path)
    ranking = _json(base / "data/results/cvpr/partial_ranking/status.json")
    study_path = _discover(base, "artifacts/cvpr/study/*.yaml")
    study = {}
    if study_path is not None:
        loaded_study = yaml.safe_load(study_path.read_text(encoding="utf-8"))
        study = loaded_study if isinstance(loaded_study, dict) else {}
    reference_path = _discover(base, "registry/manifests/cvpr/cifar10_reference.jsonl")
    draw_artifact = _latest(rows, "cvpr_reference_draw_plan")
    control_artifact = _latest(rows, "cvpr_control_artifacts")
    feature_artifact = _latest(rows, "cvpr_feature_cache_v2")
    bundle_artifacts = [row for row in rows if row.get("artifact_type") == "cvpr_certificate_input_bundle"]
    certificate_artifacts = [row for row in rows if row.get("artifact_type") == "cvpr_certificate"]
    draw_path = Path(draw_artifact["_resolved_path"]) if draw_artifact else None
    controls_path = Path(control_artifact["_resolved_path"]).parent if control_artifact else None
    feature_root = Path(feature_artifact["_resolved_path"]).parents[2] if feature_artifact else None
    input_family_root = None
    if bundle_artifacts and family.get("family_id"):
        candidate = Path(bundle_artifacts[0]["_resolved_path"]).parent
        while candidate != candidate.parent and candidate.name != str(family["family_id"]):
            candidate = candidate.parent
        if candidate.name == str(family["family_id"]):
            input_family_root = candidate
    certificate_validation = _json(input_family_root / "certificate_inputs_validation.json") if input_family_root else {}
    operational = _json(input_family_root / "family_operational_status.json") if input_family_root else {}
    ranking_graph_path = _discover(base, "data/results/cvpr/partial_ranking/ranking_graph.json")
    if ranking_graph_path is not None:
        ranking = {**_json(ranking_graph_path), "status": "COMPLETE"}
    cross_feature_path = _discover(base, "data/results/cvpr/cross_feature*.json")
    def artifact_ids(*items: dict[str, Any]) -> list[str]:
        return [str(item["artifact_id"]) for item in items if item]

    cwd = str(base)

    common_recovery = "Preserve immutable inputs and logs; correct only the failing gate, then rerun the same canonical command."
    def quote(path: str | Path) -> str:
        return shlex.quote(str(path))

    if study_path is not None and reference_path is not None and draw_path is None:
        output = base / "registry/manifests/cvpr/reference_draw_plan.json"
        profile_id = str(study.get("profile_id", ""))
        if not profile_id:
            raise ValueError("frozen study omits profile_id required by reference-draw builder")
        return _make(
            status="REFERENCE_DRAW_REQUIRED", action="PREPARE_REFERENCE_DRAW",
            reason="The study and materialized reference population exist, but no validated draw plan is registered.",
            command=(
                f"python3 -m certgen prepare reference-draw --profile {shlex.quote(profile_id)} "
                f"--study {quote(study_path)} --reference-manifest {quote(reference_path)} --out {quote(output)}"
            ),
            notebook=None, location="local", expected_input="frozen study and materialized reference manifest",
            expected_output=str(output), validator=(
                f"python3 -m certgen prepare reference-draw --profile {shlex.quote(profile_id)} "
                f"--study {quote(study_path)} --reference-manifest {quote(reference_path)} --out {quote(output)} --dry-run"
            ), runtime="seconds", network_policy="none", recovery=common_recovery, cwd=cwd,
            input_paths=[str(study_path), str(reference_path)], expected_output_artifact=str(output),
        )
    phase1_resume = (
        'CUDA_VISIBLE_DEVICES="" CERTGEN_CPU_ONLY=1 '
        "python3 scripts/run_all_available_cpu_stages.py --resume --explain"
    )
    if (
        study_path is not None
        and draw_path is not None
        and _reference_manifest_materialized(base)
        and diagnostic_import.get("passed") is not True
    ):
        diagnostic_input = (
            base
            / "artifacts/cvpr/kaggle_inputs/diagnostic/"
            "certgen_kaggle_environment_diagnostic_input.zip"
        )
        returned = base / "data/kaggle_returns/diagnostic/"
        return _make(
            status="KAGGLE_DIAGNOSTIC_REQUIRED",
            action="RUN_KAGGLE_ENVIRONMENT_DIAGNOSTIC",
            reason=(
                "The reference, frozen study, and registered draw are ready; the two-GPU "
                "environment diagnostic is the first unresolved external boundary."
            ),
            command=(
                "Upload artifacts/cvpr/kaggle_inputs/diagnostic/"
                "certgen_kaggle_environment_diagnostic_input.zip and run "
                "notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb "
                "on GPU T4 x2"
            ),
            notebook="notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb",
            location="Kaggle T4x2",
            expected_input=str(diagnostic_input),
            expected_output="certgen_kaggle_environment_diagnostic_output.zip",
            validator=phase1_resume,
            runtime="5-20 minutes planning estimate",
            network_policy="KAGGLE_INTERNET_ON_INSTALL; no model-asset network access",
            recovery=common_recovery,
            cwd=cwd,
            input_paths=[str(diagnostic_input)],
            expected_output_artifact=str(returned),
            blocker="WAITING_FOR_KAGGLE_DIAGNOSTIC",
        )
    if (
        study_path is not None
        and draw_path is not None
        and _reference_manifest_materialized(base)
        and diagnostic_import.get("passed") is True
        and preflight_import.get("passed") is not True
    ):
        preflight_input = (
            base
            / "artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip"
        )
        returned = base / "data/kaggle_returns/preflight/"
        return _make(
            status="KAGGLE_PREFLIGHT_REQUIRED",
            action="RUN_KAGGLE_CHECKPOINT_PREFLIGHT",
            reason=(
                "The environment diagnostic passed; the immutable checkpoint and extractor "
                "preflight is the next unresolved external boundary."
            ),
            command=(
                "Upload artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip "
                "with the private asset dataset and run "
                "notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb on GPU T4 x2"
            ),
            notebook="notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb",
            location="Kaggle T4x2",
            expected_input=str(preflight_input),
            expected_output="certgen_cvpr_preflight_<run_id>.zip",
            validator=phase1_resume,
            runtime="20-60 minutes planning estimate",
            network_policy="KAGGLE_INTERNET_ON_INSTALL; model loading from private offline mount",
            recovery=common_recovery,
            cwd=cwd,
            input_paths=[str(preflight_input)],
            expected_output_artifact=str(returned),
            blocker="WAITING_FOR_KAGGLE_PREFLIGHT",
        )
    if (
        study_path is not None
        and draw_path is not None
        and controls_path is None
        and generation_import.get("passed") is True
    ):
        output = base / "artifacts/cvpr/controls"
        return _make(
            status="CONTROLS_REQUIRED", action="PREPARE_CONTROLS",
            reason="The registered draw plan exists; frozen null and obvious-gap inputs are the next missing artifacts.",
            command=f"python3 -m certgen prepare controls --study {quote(study_path)} --reference-draw-plan {quote(draw_path)} --out-root {quote(output)}",
            notebook=None, location="local", expected_input="registered reference draw plan", expected_output=str(output),
            validator=f"python3 -m certgen prepare controls --study {quote(study_path)} --reference-draw-plan {quote(draw_path)} --out-root {quote(output)} --dry-run",
            runtime="seconds-minutes", network_policy="none", recovery=common_recovery, cwd=cwd,
            input_artifact_ids=artifact_ids(draw_artifact), input_paths=[str(study_path), str(draw_path)],
            expected_output_artifact=str(output),
        )
    if cache_validation.get("passed") is True and study_path and draw_path and controls_path and feature_root and family.get("status") != "frozen":
        return _make(
            status="FAMILY_FREEZE_REQUIRED", action="FREEZE_FAMILY",
            reason="Validated caches, draw plan, and controls exist; freeze the prospective Bonferroni family before gate configuration.",
            command=f"python3 -m certgen prepare family --study {quote(study_path)}",
            notebook=None, location="local", expected_input="frozen study, comparison registry, and validated caches",
            expected_output="artifacts/cvpr/family/family.json", validator="python3 -m certgen audit registries",
            runtime="seconds", network_policy="none", recovery=common_recovery, cwd=cwd,
            input_paths=[str(study_path), str(draw_path), str(controls_path), str(feature_root)],
        )
    if cache_validation.get("passed") is True and family.get("status") == "frozen" and study_path and draw_path and controls_path and feature_root:
        assert family_path is not None
        if not metric_config_path.is_file() or not sanity_config_path.is_file():
            return _make(
                status="GATE_CONFIGS_REQUIRED", action="PREPARE_GATE_CONFIGS",
                reason="Cache-v2 and the frozen family exist, but immutable metric/sanity gate configurations are missing.",
                command=(f"python3 -m certgen prepare gate-configs --study {quote(study_path)} "
                         f"--family {quote(family_path)} --feature-run {quote(feature_root)} "
                         f"--metric-out {quote(metric_config_path)} --sanity-out {quote(sanity_config_path)}"),
                notebook=None, location="local", expected_input="validated cache-v2 roles and frozen family",
                expected_output=f"{metric_config_path} and {sanity_config_path}",
                validator=(f"python3 -m certgen prepare gate-configs --study {quote(study_path)} "
                           f"--family {quote(family_path)} --feature-run {quote(feature_root)} --dry-run"),
                runtime="seconds-minutes", network_policy="none", recovery=common_recovery, cwd=cwd,
                input_paths=[str(study_path), str(family_path), str(feature_root)],
                expected_output_artifact=str(metric_config_path),
            )
        if metric.get("status") != "PASS":
            return _make(
                status="METRIC_REPRODUCTION_REQUIRED", action="RUN_METRIC_REPRODUCTION",
                reason="Frozen metric-reproduction configs exist; all registered feature-space checks must pass before certificates.",
                command=f"python3 -m certgen sanity metric-reproduction --config {quote(metric_config_path)} --out {quote(metric_result_path)}",
                notebook=None, location="local", expected_input=str(metric_config_path), expected_output=str(metric_result_path),
                validator="python3 -m certgen audit cvpr", runtime="seconds-minutes", network_policy="none",
                recovery=common_recovery, cwd=cwd, input_paths=[str(metric_config_path), str(feature_root)],
                expected_output_artifact=str(metric_result_path),
            )
        if sanity.get("status") != "PASS":
            return _make(
                status="SANITY_GATES_REQUIRED", action="RUN_METRIC_SANITY_GATES",
                reason="Metric reproduction passed; all frozen null, obvious-gap, direction, and protocol controls must pass before certificates.",
                command=f"python3 -m certgen sanity controls --config {quote(sanity_config_path)} --out {quote(sanity_result_path)}",
                notebook=None, location="local", expected_input=str(sanity_config_path), expected_output=str(sanity_result_path),
                validator="python3 -m certgen audit cvpr", runtime="seconds-minutes", network_policy="none",
                recovery=common_recovery, cwd=cwd, input_paths=[str(sanity_config_path), str(feature_root), str(controls_path)],
                expected_output_artifact=str(sanity_result_path),
            )
    if family.get("status") == "frozen" and metric.get("status") == "PASS" and sanity.get("status") == "PASS" and study_path and draw_path and controls_path and feature_root:
        assert family_path is not None
        study_ready = study_path
        draw_ready = draw_path
        controls_ready = controls_path
        features_ready = feature_root
        expected = int(family.get("number_of_hypotheses", 0))
        inputs_root = base / "artifacts/cvpr/certificate_inputs"
        if len(bundle_artifacts) != expected:
            return _make(
                status="CERTIFICATE_INPUTS_REQUIRED", action="PREPARE_CERTIFICATE_INPUTS",
                reason=f"The frozen family requires {expected} immutable bundles; {len(bundle_artifacts)} are registered.",
                command=(
                    f"python3 -m certgen prepare certificate-inputs --study {quote(study_ready)} "
                    f"--family {quote(family_path)} --feature-run {quote(feature_root)} "
                    f"--reference-draw-plan {quote(draw_ready)} --out-root {quote(inputs_root)}"
                ), notebook=None, location="local", expected_input="frozen family and registered cache-v2 roles",
                expected_output=str(inputs_root), validator=(
                    f"python3 -m certgen validate certificate-inputs --study {quote(study_ready)} "
                    f"--family {quote(family_path)} --inputs-root {quote(inputs_root)}"
                ), runtime="seconds-minutes", network_policy="none", recovery=common_recovery, cwd=cwd,
                input_artifact_ids=artifact_ids(draw_artifact, control_artifact, feature_artifact),
                input_paths=[str(study_ready), str(family_path), str(draw_ready), str(controls_ready), str(features_ready)],
                expected_output_artifact=str(inputs_root),
            )
        assert input_family_root is not None
        if certificate_validation.get("passed") is not True:
            return _make(
                status="CERTIFICATE_INPUTS_VALIDATION_REQUIRED", action="VALIDATE_CERTIFICATE_INPUTS",
                reason="Every registered family bundle must pass the canonical immutable-input validator.",
                command=(f"python3 -m certgen validate certificate-inputs --study {quote(study_ready)} "
                         f"--family {quote(family_path)} --inputs-root {quote(inputs_root)}"),
                notebook=None, location="local", expected_input="registered certificate-input bundles",
                expected_output=str(input_family_root / "certificate_inputs_validation.json"),
                validator=(f"python3 -m certgen validate certificate-inputs --study {quote(study_ready)} "
                           f"--family {quote(family_path)} --inputs-root {quote(inputs_root)} --dry-run"),
                runtime="seconds", network_policy="none", recovery=common_recovery, cwd=cwd,
                input_artifact_ids=[str(row["artifact_id"]) for row in bundle_artifacts],
                input_paths=[str(row["_resolved_path"]) for row in bundle_artifacts],
                expected_output_artifact=str(input_family_root / "certificate_inputs_validation.json"),
            )
        if operational.get("status") != "FAMILY_OPERATIONALLY_READY":
            return _make(
                status="FAMILY_OPERATIONAL_VALIDATION_REQUIRED", action="VALIDATE_FAMILY_OPERATIONAL",
                reason="The inputs validate individually; family-wide coverage and alpha completeness remain to be gated.",
                command=(f"python3 -m certgen validate family-operational --study {quote(study_ready)} "
                         f"--family {quote(family_path)} --inputs-root {quote(inputs_root)}"),
                notebook=None, location="local", expected_input="validated family-complete certificate inputs",
                expected_output=str(input_family_root / "family_operational_status.json"),
                validator=(f"python3 -m certgen validate family-operational --study {quote(study_ready)} "
                           f"--family {quote(family_path)} --inputs-root {quote(inputs_root)} --dry-run"),
                runtime="seconds", network_policy="none", recovery=common_recovery, cwd=cwd,
                input_artifact_ids=[str(row["artifact_id"]) for row in bundle_artifacts],
                input_paths=[str(input_family_root / "certificate_inputs_validation.json"), *[str(row["_resolved_path"]) for row in bundle_artifacts]],
                expected_output_artifact=str(input_family_root / "family_operational_status.json"),
            )
        if certificate_coverage.get("status") != "FAMILY_CERTIFICATES_COMPLETE" or int(certificate_coverage.get("completed_hypotheses", -1)) != expected:
            output_dir = base / "data/results/cvpr/certificates"
            return _make(
                status="FAMILY_CERTIFICATES_REQUIRED", action="RUN_FAMILY_CERTIFICATES",
                reason=f"The family is operational and both gates passed; execute all {expected} frozen certificates with coverage tracking.",
                command=(f"python3 -m certgen run family-certificates --study {quote(study_ready)} "
                         f"--family {quote(family_path)} --inputs-root {quote(inputs_root)} "
                         f"--reference-draw-plan {quote(draw_ready)} --metric-result {quote(metric_result_path)} "
                         f"--sanity-result {quote(sanity_result_path)} --operational-status {quote(input_family_root / 'family_operational_status.json')} "
                         f"--out-dir {quote(output_dir)}"),
                notebook=None, location="local", expected_input="gated family-complete certificate inputs",
                expected_output=str(output_dir / "family_certificate_coverage.json"),
                validator="python3 -m certgen audit cvpr", runtime="seconds-minutes", network_policy="none",
                recovery=common_recovery, cwd=cwd,
                input_artifact_ids=[str(row["artifact_id"]) for row in bundle_artifacts],
                input_paths=[str(metric_result_path), str(sanity_result_path), str(input_family_root / "family_operational_status.json")],
                expected_output_artifact=str(output_dir / "family_certificate_coverage.json"),
            )
    if ranking.get("status") == "COMPLETE" and len(set(map(str, family.get("feature_spaces", [])))) > 1 and cross_feature_path is None and certificate_artifacts:
        certificate_dir = Path(certificate_artifacts[0]["_resolved_path"]).parent
        output = base / "data/results/cvpr/cross_feature_analysis.json"
        return _make(
            status="CROSS_FEATURE_ANALYSIS_REQUIRED", action="RUN_CROSS_FEATURE_ANALYSIS",
            reason="The ranking is complete and the frozen family has multiple feature spaces; apply the prospective consensus policy.",
            command=f"python3 -m certgen analyze cross-feature --certificate-dir {quote(certificate_dir)} --out {quote(output)}",
            notebook=None, location="local", expected_input="registered family-bound certificates",
            expected_output=str(output), validator="python3 -m certgen audit cvpr", runtime="seconds",
            network_policy="none", recovery=common_recovery, cwd=cwd,
            input_artifact_ids=[str(row["artifact_id"]) for row in certificate_artifacts],
            input_paths=[str(row["_resolved_path"]) for row in certificate_artifacts],
            expected_output_artifact=str(output),
        )
    if ranking.get("status") == "COMPLETE":
        inputs = [str(ranking_graph_path)] if ranking_graph_path else []
        if cross_feature_path:
            inputs.append(str(cross_feature_path))
        output = base / "reports/CERTGEN_CVPR_FINAL_AUDIT.json"
        return _make(
            status="STOP_AND_INTERPRET", action="STOP_FIRST_PILOT_COMPLETE",
            reason="The nonclaim first-pilot ranking and required cross-feature interpretation are complete.",
            command="python3 -m certgen audit cvpr", notebook=None, location="local",
            expected_input="completed registered ranking artifacts", expected_output=str(output),
            validator="python3 -m certgen audit cvpr", runtime="seconds", network_policy="none",
            recovery=common_recovery, cwd=cwd, input_paths=inputs, expected_output_artifact=str(output),
        )
    if certificate_coverage.get("status") == "FAMILY_CERTIFICATES_COMPLETE":
        if not certificate_artifacts or family_path is None:
            return _make(
                status="PARTIAL_RANKING_REQUIRED", action="BUILD_PARTIAL_RANKING",
                reason="Family certificate coverage is complete, but certificate artifacts are absent from the registry.",
                command="python3 -m certgen audit artifact-registry", notebook=None, location="local",
                expected_input="registered certificate artifacts", expected_output="verified artifact registry",
                validator="python3 -m certgen audit artifact-registry", runtime="seconds", network_policy="none",
                recovery=common_recovery, blocker="BLOCKED_CERTIFICATES_NOT_REGISTERED", cwd=cwd,
            )
        certificate_dir = Path(certificate_artifacts[0]["_resolved_path"]).parent
        output = base / "data/results/cvpr/partial_ranking"
        return _make(
            status="PARTIAL_RANKING_REQUIRED", action="BUILD_PARTIAL_RANKING",
            reason="Registered family-bound certificates exist; build only the prospectively defined partial ranking.",
            command=f"python3 -m certgen rank --family {quote(family_path)} --certificate-dir {quote(certificate_dir)} --out-dir {quote(output)}",
            notebook=None, location="local", expected_input="registered family-bound certificates",
            expected_output=str(output / "ranking_graph.json"), validator="python3 -m certgen audit cvpr",
            runtime="seconds", network_policy="none", recovery=common_recovery, cwd=cwd,
            input_artifact_ids=[str(row["artifact_id"]) for row in certificate_artifacts],
            input_paths=[str(row["_resolved_path"]) for row in certificate_artifacts],
            expected_output_artifact=str(output / "ranking_graph.json"),
        )
    if family.get("status") == "frozen":
        return _make(
            status="FIRST_PILOT_REQUIRED", action="RUN_FIRST_CERTIFICATE_PILOT",
            reason="The family is frozen, but one or more prerequisite artifacts are absent from the verified registry.",
            command="python3 -m certgen audit artifact-registry", notebook=None, location="local",
            expected_input="registered draw, controls, cache-v2, and certificate-input artifacts",
            expected_output="verified artifact registry", validator="python3 -m certgen audit artifact-registry",
            runtime="seconds", network_policy="none", recovery=common_recovery,
            blocker="BLOCKED_LATE_STAGE_ARTIFACT_NOT_REGISTERED", cwd=cwd,
            input_paths=[str(family_path)] if family_path else [],
        )
    if merged.get("passed") is True:
        if feature_artifact:
            features_path = Path(feature_artifact["_resolved_path"])
            sidecar_path = features_path.with_name("sidecar.json")
            assert feature_root is not None
            output = base / "data/results/cvpr/cache_validation_status.json"
            return _make(
                status="CACHE_VALIDATION_REQUIRED", action="VALIDATE_FEATURE_CACHES",
                reason="Feature output was securely imported; validate the exact registered cache-v2 artifact.",
                command=f"python3 -m certgen validate caches --features {quote(features_path)} --sidecar {quote(sidecar_path)} --artifact-root {quote(feature_root)}",
                notebook=None, location="local", expected_input="registered canonical feature cache",
                expected_output=str(output), validator="python3 -m certgen audit artifact-registry",
                runtime="seconds-minutes", network_policy="none", recovery=common_recovery, cwd=cwd,
                input_artifact_ids=artifact_ids(feature_artifact),
                input_paths=[str(features_path), str(sidecar_path)], expected_output_artifact=str(output),
            )
        return _make(
            status="CACHE_VALIDATION_REQUIRED", action="VALIDATE_FEATURE_CACHES",
            reason="A merge is declared complete, but no cache-v2 artifact is present in the verified registry.",
            command="python3 -m certgen audit artifact-registry", notebook=None, location="local",
            expected_input="registered canonical feature cache", expected_output="verified artifact registry",
            validator="python3 -m certgen audit artifact-registry", runtime="seconds", network_policy="none",
            recovery=common_recovery, blocker="BLOCKED_FEATURE_CACHE_NOT_REGISTERED", cwd=cwd,
        )
    if feature_import.get("passed") is True:
        run_id = str(feature_import.get("run_id", "<run_id>"))
        return _make(status="FEATURE_MERGE_REQUIRED", action="MERGE_FEATURE_CACHES", reason="Feature output was securely imported; deterministic cache-v2 merge is required.", command=f"python3 -m certgen merge features --run {run_id}", notebook=None, location="local", expected_input="canonical imported feature shards", expected_output=f"data/features/cvpr/{run_id}/status.json", validator="python3 -m certgen validate caches --features <features.npz> --sidecar <sidecar.json> --artifact-root data/features/cvpr/<run_id>", runtime="seconds-minutes", network_policy="none", recovery=common_recovery)
    if (base / "data/kaggle_outputs/certgen_cvpr_features_output.zip").is_file():
        return _make(status="FEATURE_IMPORT_REQUIRED", action="IMPORT_FEATURE_ZIP", reason="A canonical feature output ZIP is waiting for secure import.", command="python3 -m certgen import features data/kaggle_outputs/certgen_cvpr_features_output.zip --out-json data/results/cvpr/feature_import_status.json", notebook=None, location="local", expected_input="data/kaggle_outputs/certgen_cvpr_features_output.zip", expected_output="data/results/cvpr/feature_import_status.json", validator="python3 -m certgen audit artifact-registry", runtime="seconds-minutes", network_policy="none", recovery=common_recovery)
    if (base / "artifacts/cvpr/features/feature_config.yaml").is_file():
        return _make(status="KAGGLE_FEATURE_EXTRACTION_REQUIRED", action="RUN_KAGGLE_FEATURE_EXTRACTION_1K", reason="The canonical feature package is frozen.", command="Run the canonical notebook on Kaggle", notebook="notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_1k.ipynb", location="Kaggle T4x2", expected_input="artifacts/cvpr/features/certgen_cvpr_features_input.zip", expected_output="/kaggle/working/certgen_cvpr_features_<run_id>.zip", validator="python3 -m certgen import features <copied-back-zip>", runtime="planning estimate in runtime plan", network_policy="OFFLINE_PACKAGED_CACHE", recovery=common_recovery)
    if generation_import.get("passed") is True:
        return _make(status="FEATURE_CONFIG_REQUIRED", action="PREPARE_FEATURE_CONFIG", reason="Generation output is imported and validated.", command="python3 -m certgen prepare features", notebook=None, location="local", expected_input="canonical generation import and materialized reference", expected_output="artifacts/cvpr/features/feature_config.yaml", validator="python3 -m certgen audit registries", runtime="seconds-minutes", network_policy="none", recovery=common_recovery)
    if (base / "data/kaggle_outputs/certgen_cvpr_generation_output.zip").is_file():
        return _make(status="GENERATION_IMPORT_REQUIRED", action="IMPORT_GENERATION_ZIP", reason="A canonical generation output ZIP is waiting for secure import.", command="python3 -m certgen import generation data/kaggle_outputs/certgen_cvpr_generation_output.zip --out-json data/results/cvpr/generation_import_status.json", notebook=None, location="local", expected_input="data/kaggle_outputs/certgen_cvpr_generation_output.zip", expected_output="data/results/cvpr/generation_import_status.json", validator="python3 -m certgen audit artifact-registry", runtime="seconds-minutes", network_policy="none", recovery=common_recovery)
    if (base / "artifacts/cvpr/generation/generation_config.yaml").is_file():
        return _make(status="KAGGLE_GENERATION_REQUIRED", action="RUN_KAGGLE_GENERATION_1K", reason="The hash-bound generation package is ready.", command="Run the canonical notebook on Kaggle", notebook="notebooks/kaggle/certgen_cvpr_cifar10_generation_t4x2_1k.ipynb", location="Kaggle T4x2", expected_input="artifacts/cvpr/generation/certgen_cvpr_generation_input.zip", expected_output="/kaggle/working/certgen_cvpr_generation_<run_id>.zip", validator="python3 -m certgen import generation <copied-back-zip>", runtime="derived from measured checkpoint preflight", network_policy="OFFLINE_PACKAGED_CACHE", recovery=common_recovery)
    if preflight_import.get("passed") is True:
        return _make(status="GENERATION_CONFIG_REQUIRED", action="PREPARE_GENERATION_CONFIG", reason="Canonical checkpoint preflight output is imported and validated.", command="python3 -m certgen prepare generation --scale 1k", notebook=None, location="local", expected_input="validated reference plus canonical preflight import", expected_output="artifacts/cvpr/generation/generation_config.yaml", validator="python3 -m certgen audit registries", runtime="seconds-minutes", network_policy="none", recovery=common_recovery)
    if (base / "data/kaggle_outputs/certgen_cvpr_preflight_output.zip").is_file():
        return _make(status="PREFLIGHT_IMPORT_REQUIRED", action="IMPORT_CHECKPOINT_PREFLIGHT_ZIP", reason="Canonical preflight output is waiting for secure import.", command="python3 -m certgen import preflight data/kaggle_outputs/certgen_cvpr_preflight_output.zip --out-json data/results/cvpr/preflight_import_status.json", notebook=None, location="local", expected_input="data/kaggle_outputs/certgen_cvpr_preflight_output.zip", expected_output="data/results/cvpr/preflight_import_status.json", validator="python3 -m certgen audit artifact-registry", runtime="seconds", network_policy="none", recovery=common_recovery)
    if (base / "artifacts/cvpr/preflight/preflight_config.yaml").is_file():
        return _make(status="KAGGLE_PREFLIGHT_REQUIRED", action="RUN_KAGGLE_CHECKPOINT_PREFLIGHT", reason="The canonical preflight configuration and package are frozen.", command="Run the canonical notebook on Kaggle", notebook="notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb", location="Kaggle T4x2", expected_input="artifacts/cvpr/preflight/certgen_cvpr_preflight_input.zip", expected_output="/kaggle/working/certgen_cvpr_preflight_<run_id>.zip", validator="python3 -m certgen import preflight <copied-back-zip>", runtime="5-20 minutes planning estimate", network_policy="ONLINE_PREFLIGHT_DOWNLOAD or OFFLINE_PACKAGED_CACHE as frozen", recovery=common_recovery)
    if _reference_manifest_materialized(base):
        return _make(status="PREFLIGHT_CONFIG_REQUIRED", action="PREPARE_PREFLIGHT_CONFIG", reason="The canonical CIFAR reference manifest is materialized.", command="python3 -m certgen prepare preflight", notebook=None, location="local", expected_input="model/feature registries plus explicit asset policy and license approvals", expected_output="artifacts/cvpr/preflight/preflight_config.yaml", validator="python3 -m certgen audit registries", runtime="seconds-minutes", network_policy="explicit choice required", recovery=common_recovery)
    if onramp.get("materialization_can_proceed") is True:
        detected = onramp.get("detected_paths", [{}])[0]
        detected_path = detected.get("path") or detected.get("source") or "<validated-source>"
        return _make(status="REFERENCE_MATERIALIZATION_REQUIRED", action="MATERIALIZE_CIFAR_REFERENCE", reason="A supported local CIFAR source passed validation.", command=f"python3 -m certgen materialize reference --source {detected_path}", notebook=None, location="local", expected_input=str(detected_path), expected_output="registry/manifests/cvpr/cifar10_reference.jsonl", validator="python3 -m certgen status", runtime="seconds-minutes", network_policy="none", recovery=common_recovery)
    reference_candidates = (
        base / "data/sources/cifar-10-python.tar.gz",
        base / "cifar-10-python.tar.gz",
    )
    reference_candidate = next(
        (path for path in reference_candidates if path.is_file()), None
    )
    if reference_candidate is not None:
        relative_candidate = reference_candidate.relative_to(base).as_posix()
        command = (
            "python3 -m certgen validate reference "
            f"--source {quote(relative_candidate)} --explain"
        )
        return _make(
            status="REFERENCE_VALIDATION_REQUIRED",
            action="VALIDATE_CIFAR_REFERENCE",
            reason="A local CIFAR-10 archive candidate exists but has not passed hash/layout validation.",
            command=command,
            notebook=None,
            location="local",
            expected_input=relative_candidate,
            expected_output="data/results/v9_cifar_reference_onramp.json",
            validator=command,
            runtime="seconds-minutes",
            network_policy="none",
            recovery="If validation fails, replace the candidate with the official archive and rerun the same command.",
            blocker="BLOCKED_REFERENCE_VALIDATION_REQUIRED",
            cwd=cwd,
            input_paths=[relative_candidate],
        )
    return _make(
        status="REFERENCE_SOURCE_REQUIRED",
        action="PROVIDE_CIFAR_REFERENCE",
        reason="No valid local CIFAR-10 reference root/archive has been detected.",
        command="python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain",
        notebook=None,
        location="local",
        expected_input="data/sources/cifar-10-python.tar.gz (official archive) or another accepted local CIFAR-10 source",
        expected_output="data/results/v9_cifar_reference_onramp.json",
        validator="python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain",
        runtime="user-dependent",
        network_policy="none",
        recovery="Place a supported local archive/root at the declared path; this command never downloads it.",
        blocker="BLOCKED_USER_MUST_PROVIDE_CIFAR_REFERENCE",
    )


def write_next_action(
    out_json: str | Path = "data/results/v9_exact_next_action.json",
    out_report: str | Path = "docs/V9_EXACT_NEXT_ACTION.md",
    *,
    root: str | Path = ".",
    registry_path: str | Path = "data/artifact_registry.jsonl",
) -> dict[str, Any]:
    payload = determine_next_action(root=root, registry_path=registry_path)
    write_json(payload, out_json)
    lines = [
        "# Legacy Compatibility Next-Action Mirror",
        "",
        "`LEGACY_COMPATIBILITY_ONLY` · `NOT_CANONICAL_GUIDANCE`",
        "",
        "Canonical source: `CERTGEN_CVPR_FINAL_100_PERCENT_PRE_RUN_HANDBOOK.md`.",
        "",
        f"Status: `{payload['status']}`",
        f"Action: `{payload['action']}`",
        f"Reason: {payload['reason']}",
        f"Exact command: `{payload['exact_command']}`",
        f"Notebook: `{payload['notebook_path']}`",
        f"Expected output: `{payload['expected_output']}`",
        f"Success validator: `{payload['success_validator']}`",
        "Claim allowed: `false`",
    ]
    Path(out_report).parent.mkdir(parents=True, exist_ok=True)
    Path(out_report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print the canonical CVPR next action.")
    parser.add_argument("--out-json", default="data/results/v9_exact_next_action.json")
    parser.add_argument("--out-report", default="docs/V9_EXACT_NEXT_ACTION.md")
    args = parser.parse_args(argv)
    print(json.dumps(write_next_action(args.out_json, args.out_report), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
