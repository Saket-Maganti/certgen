"""Canonical, claim-safe command surface for CertGen execution."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any

from certgen.data.cifar_reference_super_onramp import run_onramp
from certgen.notebooks.cvpr_static_analyzer import analyze_all
from certgen.packaging.artifact_registry import verify_artifact_registry
from certgen.packaging.v9_import_repair import import_repair
from certgen.paper.v9_paper_firewall import run_firewall
from certgen.pipeline.v9_next_action import determine_next_action, write_next_action


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _split_csv_ids(value: str | None) -> list[str] | None:
    return [item.strip() for item in value.split(",") if item.strip()] if value else None


def _status() -> dict[str, Any]:
    action = determine_next_action()
    top_level_by_status = {
        "REFERENCE_SOURCE_REQUIRED": "CVPR_RUN_READY_BLOCKED_ONLY_BY_REFERENCE_INPUT",
        "REFERENCE_VALIDATION_REQUIRED": "CVPR_RUN_READY_BLOCKED_ONLY_BY_REFERENCE_INPUT",
        "REFERENCE_MATERIALIZATION_REQUIRED": "CVPR_REFERENCE_READY_PREFLIGHT_REQUIRED",
        "PREFLIGHT_CONFIG_REQUIRED": "CVPR_REFERENCE_READY_PREFLIGHT_REQUIRED",
        "KAGGLE_PREFLIGHT_REQUIRED": "CVPR_REAL_PREFLIGHT_REQUIRED",
        "PREFLIGHT_IMPORT_REQUIRED": "CVPR_REAL_PREFLIGHT_REQUIRED",
        "GENERATION_CONFIG_REQUIRED": "CVPR_1K_GENERATION_READY",
        "KAGGLE_GENERATION_REQUIRED": "CVPR_1K_GENERATION_READY",
        "GENERATION_IMPORT_REQUIRED": "CVPR_1K_GENERATION_READY",
    }
    return {
        "top_level_status": top_level_by_status.get(action["status"], "CVPR_REAL_PREFLIGHT_REQUIRED"),
        "status_code": action.get("blocker") or action["action"],
        "next_action": action,
        "real_evidence_status": "none",
        "validated_real_evidence_status": "none",
        "claim_allowed": False,
        "evidence_boundary": "Status and package checks are not empirical evidence.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="certgen", description="Canonical CertGen execution interface")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="Print the current blocked-honest execution status")

    next_action = subparsers.add_parser("next-action", help="Print the one exact next action")
    next_action.add_argument("--write", action="store_true", help="Refresh the JSON and Markdown next-action artifacts")
    next_action.add_argument("--explain", action="store_true")
    next_action.add_argument("--json", action="store_true")
    next_action.add_argument("--dry-run", action="store_true")
    next_action.add_argument("--root", default=".")
    next_action.add_argument("--registry", default="data/artifact_registry.jsonl")

    discover = subparsers.add_parser("discover", help="Discover packages and runtime assets by verified internal identity")
    discover_sub = discover.add_subparsers(dest="discover_kind", required=True)

    def add_discovery_limits(command: argparse.ArgumentParser) -> None:
        command.add_argument("--search-root", action="append", required=True)
        command.add_argument("--max-depth", type=int, default=12)
        command.add_argument("--max-candidates", type=int, default=10_000)
        command.add_argument("--maximum-members", type=int, default=200_000)
        command.add_argument("--maximum-bytes", type=int, default=20 * 1024**3)
        command.add_argument("--explain", action="store_true")
        command.add_argument("--dry-run", action="store_true")
        command.add_argument("--json", action="store_true")

    discover_packages = discover_sub.add_parser("packages", help="Classify and select CertGen ZIP/extracted packages")
    add_discovery_limits(discover_packages)
    discover_packages.add_argument("--expected-stage", choices=["diagnostic", "preflight", "generation", "features"])
    discover_packages.add_argument("--expected-package-type", choices=[
        "DIAGNOSTIC_INPUT", "DIAGNOSTIC_OUTPUT", "PREFLIGHT_INPUT", "PREFLIGHT_OUTPUT",
        "GENERATION_INPUT", "GENERATION_OUTPUT", "FEATURE_INPUT", "FEATURE_OUTPUT", "MULTIPART_OUTPUT",
    ])
    discover_packages.add_argument("--expected-package-sha256")
    discover_packages.add_argument("--expected-scientific-identity-hash")
    discover_packages.add_argument("--study-hash", "--expected-study-hash", dest="study_hash")
    discover_packages.add_argument("--profile-id", "--expected-profile-id", dest="profile_id")
    discover_packages.add_argument("--configuration-hash", "--expected-configuration-hash", dest="configuration_hash")
    discover_packages.add_argument("--expected-source-code-hash")
    discover_packages.add_argument("--expected-integrity-manifest")
    discover_packages.add_argument("--expected-output-schema-version")
    discover_packages.add_argument("--run-id", "--expected-run-id", dest="run_id")
    discover_packages.add_argument("--scale", "--expected-scale", dest="scale")
    discover_packages.add_argument("--completion-status")

    discover_reference = discover_sub.add_parser("reference", help="Discover a validated reference archive by structure/hash")
    add_discovery_limits(discover_reference)
    discover_reference.add_argument("--expected-kind", required=True, choices=["cifar10_python"])

    discover_assets = discover_sub.add_parser("assets", help="Discover a private asset mount by manifest identity")
    add_discovery_limits(discover_assets)
    discover_assets.add_argument("--asset-id", required=True)
    discover_assets.add_argument("--revision")

    discover_wheels = discover_sub.add_parser("wheelhouse", help="Discover a complete private wheelhouse by manifest")
    add_discovery_limits(discover_wheels)
    discover_wheels.add_argument("--profile", required=True)
    discover_wheels.add_argument("--target-python", default="cp311")
    discover_wheels.add_argument("--target-platform", default="manylinux_x86_64")

    discover_expected = discover_sub.add_parser("expected-output", help="Select output for the exact active input identity")
    add_discovery_limits(discover_expected)
    discover_expected.add_argument("--root", default=".")
    discover_expected.add_argument("--stage", required=True, choices=["diagnostic", "preflight", "generation", "features"])

    discover_multipart = discover_sub.add_parser("multipart", help="Validate and atomically reassemble manifest-declared output parts")
    discover_multipart.add_argument("--manifest", required=True)
    discover_multipart.add_argument("--out")
    discover_multipart.add_argument("--json", action="store_true")
    discover_multipart.add_argument("--explain", action="store_true")

    validate = subparsers.add_parser("validate", help="Validate an execution prerequisite")
    validate_sub = validate.add_subparsers(dest="validate_kind", required=True)
    reference = validate_sub.add_parser("reference", help="Search for a supported CIFAR-10 reference source")
    reference.add_argument("--source", action="append", default=[])
    reference.add_argument("--explain", action="store_true")
    reference.add_argument("--out-json", default="data/results/v9_cifar_reference_onramp.json")
    reference.add_argument("--out-report", default="docs/V9_CIFAR_REFERENCE_SUPER_ONRAMP.md")
    caches = validate_sub.add_parser("caches", help="Validate one cache-v2 feature artifact")
    caches.add_argument("--features", required=True)
    caches.add_argument("--sidecar", required=True)
    caches.add_argument("--artifact-root")
    certificate_inputs_validation = validate_sub.add_parser(
        "certificate-inputs", help="Validate complete immutable inputs for a frozen family"
    )
    certificate_inputs_validation.add_argument("--study", required=True)
    certificate_inputs_validation.add_argument("--family", required=True)
    certificate_inputs_validation.add_argument("--inputs-root", default="artifacts/cvpr/certificate_inputs")
    certificate_inputs_validation.add_argument("--explain", action="store_true")
    certificate_inputs_validation.add_argument("--json", action="store_true")
    certificate_inputs_validation.add_argument("--dry-run", action="store_true")
    family_operational = validate_sub.add_parser(
        "family-operational", help="Require one valid executable bundle per family hypothesis"
    )
    family_operational.add_argument("--study", required=True)
    family_operational.add_argument("--family", required=True)
    family_operational.add_argument("--inputs-root", default="artifacts/cvpr/certificate_inputs")
    family_operational.add_argument("--coverage-out", default="reports/CERTGEN_OPERATIONAL_HYPOTHESIS_COVERAGE.csv")
    family_operational.add_argument("--explain", action="store_true")
    family_operational.add_argument("--json", action="store_true")
    family_operational.add_argument("--dry-run", action="store_true")
    claims_validation = validate_sub.add_parser("claims", help="Validate the reviewer claim-evidence matrix")
    claims_validation.add_argument("--study")
    claims_validation.add_argument("--matrix", default="reports/CERTGEN_CLAIM_EVIDENCE_MATRIX.csv")

    materialize = subparsers.add_parser("materialize", help="Materialize a validated execution prerequisite")
    materialize_sub = materialize.add_subparsers(dest="materialize_kind", required=True)
    materialize_reference = materialize_sub.add_parser("reference", help="Materialize a local CIFAR-10 reference source")
    materialize_reference.add_argument("--source", required=True)
    materialize_reference.add_argument("--out-manifest", default="registry/manifests/cvpr/cifar10_reference.jsonl")
    materialize_reference.add_argument("--out-summary", default="data/results/cvpr_reference_materialization.json")

    importer = subparsers.add_parser("import", help="Safely import a copied-back execution ZIP")
    importer.add_argument("kind", choices=["preflight", "generation", "feature", "features"])
    importer.add_argument("zip")
    importer.add_argument("--out-dir")
    importer.add_argument("--registry", default="data/artifact_registry.jsonl")
    importer.add_argument("--out-json", default="data/results/v9_import_repair_status.json")
    importer.add_argument("--out-report", default="docs/V9_IMPORT_REPAIR_REPORT.md")

    audit = subparsers.add_parser("audit", help="Run a local-safe static audit")
    audit.add_argument("lane", choices=["notebooks", "paper", "artifact-registry", "cvpr", "registries", "final-pre-run", "maximum-ceiling", "kaggle-launch", "cpu-execution", "universal-kaggle"])
    audit.add_argument("--out-root", default="reports/final_pre_run_audit")
    audit.add_argument("--explain", action="store_true")
    audit.add_argument("--json", action="store_true")
    audit.add_argument("--dry-run", action="store_true")

    validate_caches = subparsers.add_parser("validate-caches", help="Validate one cache-v2 feature artifact")
    validate_caches.add_argument("--features", required=True)
    validate_caches.add_argument("--sidecar", required=True)
    validate_caches.add_argument("--artifact-root")

    kaggle_input = validate_sub.add_parser("kaggle-input", help="Emulate notebook input discovery before upload")
    kaggle_input.add_argument("zip")
    kaggle_output = validate_sub.add_parser("kaggle-output", help="Validate a copied-back ZIP before import")
    kaggle_output.add_argument("zip")
    kaggle_output.add_argument("--kind", choices=["preflight", "generation", "feature", "features"])

    inspect = subparsers.add_parser("inspect", help="Inspect a run package without execution")
    inspect_sub = inspect.add_subparsers(dest="inspect_kind", required=True)
    inspect_package = inspect_sub.add_parser("package")
    inspect_package.add_argument("zip")

    readiness = subparsers.add_parser("readiness", help="Report live CVPR run readiness and one exact next action")
    readiness.add_argument("--explain", action="store_true")
    readiness.add_argument("--json", action="store_true")
    readiness.add_argument("--dry-run", action="store_true")

    profiles = subparsers.add_parser("profiles", help="List or inspect immutable prospective pilot profiles")
    profiles_sub = profiles.add_subparsers(dest="profiles_kind", required=True)
    profiles_sub.add_parser("list")
    profiles_show = profiles_sub.add_parser("show")
    profiles_show.add_argument("profile")

    merge = subparsers.add_parser("merge", help="Merge imported execution artifacts")
    merge_sub = merge.add_subparsers(dest="merge_kind", required=True)
    merge_features = merge_sub.add_parser("features")
    merge_features.add_argument("--run", required=True)
    merge_features.add_argument("--imported-root", default="data/imported")
    merge_features.add_argument("--output-root", default="data/features/cvpr")
    merge_features.add_argument("--registry", default="data/artifact_registry.jsonl")

    certify = subparsers.add_parser("certify", help="Run a frozen-family bounded-RBF certificate")
    certify.add_argument("--study", required=True)
    certify.add_argument("--family", required=True)
    certify.add_argument("--features", required=True)
    certify.add_argument("--reference-draw-plan", required=True)
    certify.add_argument("--comparison", required=True)
    certify.add_argument("--feature-space", required=True)
    certify.add_argument("--out", required=True)
    certify.add_argument("--fingerprint", help="Complete reproducibility-fingerprint JSON")
    certify.add_argument("--registry", default="data/artifact_registry.jsonl")

    rank = subparsers.add_parser("rank", help="Build a certified partial ranking")
    rank.add_argument("--family", required=True)
    rank.add_argument("--certificate-dir", required=True)
    rank.add_argument("--out-dir", required=True)
    rank.add_argument("--aggregation-rule", choices=["unanimous_direction_or_unresolved"])

    figures = subparsers.add_parser("figures", help="Write or validate an evidence-gated figure contract")
    figures.add_argument("--request", required=True)
    figures.add_argument("--out", required=True)

    package = subparsers.add_parser("package", help="Build a deterministic Kaggle input package")
    package.add_argument("kind", choices=["preflight", "generation", "features"])
    package.add_argument("--config", required=True)
    package.add_argument("--input", action="append", default=[], metavar="NAME=PATH")
    package.add_argument("--out-zip", required=True)
    package.add_argument("--manifest-out", required=True)

    freeze_config = subparsers.add_parser("freeze-config", help="Freeze a fully specified notebook configuration")
    freeze_config.add_argument("--input", required=True)
    freeze_config.add_argument("--out", required=True)

    freeze = subparsers.add_parser("freeze", help="Freeze a prospective scientific protocol")
    freeze_sub = freeze.add_subparsers(dest="freeze_kind", required=True)
    freeze_study = freeze_sub.add_parser("study", help="Freeze a named pilot profile into a study")
    freeze_study.add_argument("--profile", required=True)
    freeze_study.add_argument("--out")
    freeze_study.add_argument("--alpha", type=float, default=0.05)

    analyze = subparsers.add_parser("analyze", help="Build a nonclaim certificate analysis")
    analyze.add_argument("kind", choices=["samples-to-decision", "cross-feature", "ranking-stability", "point-vs-certified", "pilot-stop-go"])
    analyze.add_argument("--certificate-dir")
    analyze.add_argument("--point-estimates")
    analyze.add_argument("--ranking")
    analyze.add_argument("--pilot-summary")
    analyze.add_argument("--out", required=True)

    runtime = subparsers.add_parser("plan-runtime", help="Build a nonempirical resource and session plan")
    runtime.add_argument("--config", required=True)
    runtime.add_argument("--out", required=True)
    runtime.add_argument("--ingest-preflight")

    runtime_alias = subparsers.add_parser("runtime-plan", help="Alias for plan-runtime with optional measured preflight")
    runtime_alias.add_argument("runtime_action", nargs="?", choices=["ingest-preflight"])
    runtime_alias.add_argument("runtime_report", nargs="?")
    runtime_alias.add_argument("--config", default="configs/cvpr/runtime_plan_template.yaml")
    runtime_alias.add_argument("--out", default="artifacts/cvpr/runtime/runtime_plan.json")
    runtime_alias.add_argument("--ingest-preflight")

    run = subparsers.add_parser("run", help="Execute a gated local CVPR stage")
    run_sub = run.add_subparsers(dest="run_kind", required=True)
    run_family = run_sub.add_parser("family-certificates", help="Run every missing certificate in a frozen family")
    run_family.add_argument("--study", required=True)
    run_family.add_argument("--family", required=True)
    run_family.add_argument("--inputs-root", default="artifacts/cvpr/certificate_inputs")
    run_family.add_argument("--reference-draw-plan", required=True)
    run_family.add_argument("--metric-result", default="data/results/cvpr/metric_reproduction.json")
    run_family.add_argument("--sanity-result", default="data/results/cvpr/sanity_controls.json")
    run_family.add_argument("--operational-status", required=True)
    run_family.add_argument("--out-dir", default="data/results/cvpr/certificates")
    run_family.add_argument("--registry", default="data/artifact_registry.jsonl")

    prepare = subparsers.add_parser("prepare", help="Build a canonical registry-derived execution configuration")
    prepare_sub = prepare.add_subparsers(dest="prepare_kind", required=True)
    prepare_preflight = prepare_sub.add_parser("preflight")
    prepare_preflight.add_argument("--out-dir", default="artifacts/cvpr/preflight")
    prepare_preflight.add_argument("--asset-policy", choices=["ONLINE_PREFLIGHT_DOWNLOAD", "OFFLINE_PACKAGED_CACHE"], default="ONLINE_PREFLIGHT_DOWNLOAD")
    prepare_preflight.add_argument("--license-approvals", help="JSON object mapping model IDs to manually approved license labels")
    prepare_preflight.add_argument("--profile", help="Named prospective pilot profile")
    prepare_preflight.add_argument("--profile-path", help="Explicit fixture/profile YAML path")
    prepare_preflight.add_argument("--models", help="Comma-separated prospective model IDs")
    prepare_preflight.add_argument("--extractors", help="Comma-separated prospective extractor IDs")
    prepare_generation = prepare_sub.add_parser("generation")
    prepare_generation.add_argument("--scale", choices=["1k", "10k", "50k"], default="1k")
    prepare_generation.add_argument("--out-dir", default="artifacts/cvpr/generation")
    prepare_generation.add_argument("--preflight-config", default="artifacts/cvpr/preflight/preflight_config.yaml")
    prepare_generation.add_argument("--preflight-import", default="data/results/cvpr/preflight_import_status.json")
    prepare_generation.add_argument("--reference-manifest", default="registry/manifests/cvpr/cifar10_reference.jsonl")
    prepare_generation.add_argument("--study", default="artifacts/cvpr/study/cifar_integrity_minimal.yaml")
    prepare_features = prepare_sub.add_parser("features")
    prepare_features.add_argument("--out-dir", default="artifacts/cvpr/features")
    prepare_features.add_argument("--generation-import", default="data/results/cvpr/generation_import_status.json")
    prepare_features.add_argument("--preflight-import", default="data/results/cvpr/preflight_import_status.json")
    prepare_features.add_argument("--reference-manifest", default="registry/manifests/cvpr/cifar10_reference.jsonl")
    prepare_features.add_argument("--reference-draw-plan", default="registry/manifests/cvpr/reference_draw_plan.json")
    prepare_features.add_argument(
        "--input-mode",
        choices=["EMBED_IMAGES_IN_PACKAGE", "MOUNT_EXTERNAL_IMAGE_DATASET"],
        default="EMBED_IMAGES_IN_PACKAGE",
    )
    prepare_features.add_argument("--external-image-manifest")
    prepare_features.add_argument("--external-image-root")
    prepare_features.add_argument("--mount-id")
    prepare_features.add_argument("--expected-mount-path")
    prepare_features.add_argument("--mount-manifest-hash")
    prepare_features.add_argument("--controls-dir")
    prepare_family = prepare_sub.add_parser("family")
    prepare_family.add_argument("--out-dir", default="artifacts/cvpr/family")
    prepare_family.add_argument("--alpha", type=float, default=0.05)
    prepare_family.add_argument("--study", default="artifacts/cvpr/study/cifar_integrity_minimal.yaml")
    prepare_runtime = prepare_sub.add_parser("runtime-plan")
    prepare_runtime.add_argument("--config", default="artifacts/cvpr/generation/generation_config.yaml")
    prepare_runtime.add_argument("--out", default="artifacts/cvpr/generation/runtime_plan.json")
    prepare_runtime.add_argument("--ingest-preflight")
    prepare_reference_draw = prepare_sub.add_parser("reference-draw")
    prepare_reference_draw.add_argument("--profile", required=True)
    prepare_reference_draw.add_argument("--study", required=True)
    prepare_reference_draw.add_argument("--reference-manifest", required=True)
    prepare_reference_draw.add_argument("--out", default="registry/manifests/cvpr/reference_draw_plan.json")
    prepare_reference_draw.add_argument("--seed", type=int, default=0)
    prepare_reference_draw.add_argument("--registry", default="data/artifact_registry.jsonl")
    prepare_reference_draw.add_argument("--explain", action="store_true")
    prepare_reference_draw.add_argument("--json", action="store_true")
    prepare_reference_draw.add_argument("--dry-run", action="store_true")
    prepare_controls_parser = prepare_sub.add_parser("controls")
    prepare_controls_parser.add_argument("--study", required=True)
    prepare_controls_parser.add_argument("--reference-draw-plan", required=True)
    prepare_controls_parser.add_argument("--out-root", default="artifacts/cvpr/controls")
    prepare_controls_parser.add_argument("--registry", default="data/artifact_registry.jsonl")
    prepare_controls_parser.add_argument("--explain", action="store_true")
    prepare_controls_parser.add_argument("--json", action="store_true")
    prepare_controls_parser.add_argument("--dry-run", action="store_true")
    prepare_certificate_inputs_parser = prepare_sub.add_parser("certificate-inputs")
    prepare_certificate_inputs_parser.add_argument("--study", required=True)
    prepare_certificate_inputs_parser.add_argument("--family", required=True)
    prepare_certificate_inputs_parser.add_argument("--feature-run", required=True)
    prepare_certificate_inputs_parser.add_argument("--reference-draw-plan", required=True)
    prepare_certificate_inputs_parser.add_argument("--out-root", default="artifacts/cvpr/certificate_inputs")
    prepare_certificate_inputs_parser.add_argument("--registry", default="data/artifact_registry.jsonl")
    prepare_certificate_inputs_parser.add_argument("--explain", action="store_true")
    prepare_certificate_inputs_parser.add_argument("--json", action="store_true")
    prepare_certificate_inputs_parser.add_argument("--dry-run", action="store_true")
    prepare_gates = prepare_sub.add_parser("gate-configs", help="Freeze post-cache metric and sanity gate configs")
    prepare_gates.add_argument("--study", required=True)
    prepare_gates.add_argument("--family", required=True)
    prepare_gates.add_argument("--feature-run", required=True)
    prepare_gates.add_argument("--metric-out", default="configs/cvpr/frozen_metric_reproduction.yaml")
    prepare_gates.add_argument("--sanity-out", default="configs/cvpr/frozen_sanity.yaml")
    prepare_gates.add_argument("--registry", default="data/artifact_registry.jsonl")
    prepare_gates.add_argument("--dry-run", action="store_true")

    provenance = subparsers.add_parser("provenance", help="Build or verify the content-addressed execution DAG")
    provenance_sub = provenance.add_subparsers(dest="provenance_kind", required=True)
    for name in ("graph", "verify"):
        provenance_command = provenance_sub.add_parser(name)
        provenance_command.add_argument("--study", required=True)
        provenance_command.add_argument("--registry", default="data/artifact_registry.jsonl")
        provenance_command.add_argument("--root", default=".")
        provenance_command.add_argument("--out-json")
        provenance_command.add_argument("--out-dot")

    doctor = subparsers.add_parser("doctor", help="Diagnose one execution contract without collapsing real blockers")
    doctor.add_argument("--stage")
    doctor.add_argument("--study")
    doctor.add_argument("--root", default=".")
    doctor.add_argument("--json", action="store_true")

    capsule = subparsers.add_parser("capsule", help="Build, inspect, or verify an immutable run capsule")
    capsule_sub = capsule.add_subparsers(dest="capsule_kind", required=True)
    capsule_build = capsule_sub.add_parser("build")
    capsule_build.add_argument("--stage", required=True)
    capsule_build.add_argument("--study", required=True)
    capsule_build.add_argument("--root", default=".")
    capsule_build.add_argument("--out")
    capsule_build.add_argument("--public", action="store_true")
    for name in ("inspect", "verify"):
        capsule_command = capsule_sub.add_parser(name)
        capsule_command.add_argument("zip")

    scale_plan = subparsers.add_parser("scale-plan", help="Freeze and query the prospective 1k/10k/50k ladder")
    scale_sub = scale_plan.add_subparsers(dest="scale_kind", required=True)
    for name in ("freeze", "status", "next"):
        scale_command = scale_sub.add_parser(name)
        scale_command.add_argument("--study", required=True)
        scale_command.add_argument("--root", default=".")

    sensitivity = subparsers.add_parser("sensitivity", help="Freeze or validate prospective sensitivity lanes")
    sensitivity_sub = sensitivity.add_subparsers(dest="sensitivity_kind", required=True)
    for name in ("freeze", "validate"):
        sensitivity_command = sensitivity_sub.add_parser(name)
        sensitivity_command.add_argument("--study", required=True)
        sensitivity_command.add_argument("--root", default=".")

    plan = subparsers.add_parser("plan", help="Run a non-evidentiary planning contract")
    plan_sub = plan.add_subparsers(dest="plan_kind", required=True)
    resolution = plan_sub.add_parser("resolution")
    resolution.add_argument("--study", required=True)
    resolution.add_argument("--root", default=".")
    resolution.add_argument("--trials", type=int, default=128)

    rehearse = subparsers.add_parser("rehearse", help="Run local fixture-only failure rehearsals")
    rehearse_sub = rehearse.add_subparsers(dest="rehearse_kind", required=True)
    failures = rehearse_sub.add_parser("failures")
    failures.add_argument("--all", action="store_true")
    failures.add_argument("--root", default=".")

    replay = subparsers.add_parser("replay", help="Plan or verify minimal deterministic recomputation")
    replay_sub = replay.add_subparsers(dest="replay_kind", required=True)
    for name in ("plan", "verify"):
        replay_command = replay_sub.add_parser(name)
        replay_command.add_argument("--study", required=True)
        replay_command.add_argument("--root", default=".")
        if name == "plan":
            replay_command.add_argument("--changed", action="append", default=[])

    accounting = subparsers.add_parser("accounting", help="Summarize typed compute and efficiency records")
    accounting_sub = accounting.add_subparsers(dest="accounting_kind", required=True)
    accounting_summary = accounting_sub.add_parser("summarize")
    accounting_summary.add_argument("--study", required=True)
    accounting_summary.add_argument("--root", default=".")

    release = subparsers.add_parser("release", help="Build or verify a clean reproducibility export")
    release_sub = release.add_subparsers(dest="release_kind", required=True)
    archive = release_sub.add_parser("build-archive")
    archive.add_argument("--out", default="dist/certgen_cvpr_reproducibility.zip")
    archive.add_argument("--no-tests", action="store_true")

    synthetic_runtime = subparsers.add_parser("synthetic-runtime", help="Run the end-to-end synthetic-only runtime contract")
    synthetic_runtime.add_argument("--out-dir", required=True)

    sanity = subparsers.add_parser("sanity", help="Run or report a fail-closed metric/sanity gate")
    sanity.add_argument("kind", choices=["metric-reproduction", "controls"])
    sanity.add_argument("--config", help="Frozen gate configuration; omission reports the prerequisite blocker")
    sanity.add_argument("--out", help="Immutable JSON result path")

    kaggle = subparsers.add_parser("kaggle", help="Build, validate, and route canonical Kaggle inputs")
    kaggle_sub = kaggle.add_subparsers(dest="kaggle_kind", required=True)
    kaggle_inventory = kaggle_sub.add_parser("inventory")
    kaggle_inventory.add_argument("--json", action="store_true")
    kaggle_inventory.add_argument("--explain", action="store_true")
    kaggle_inventory.add_argument("--dry-run", action="store_true")
    kaggle_build = kaggle_sub.add_parser("build-input")
    kaggle_build.add_argument("--stage", required=True, choices=["diagnostic", "preflight", "generation", "features"])
    kaggle_build.add_argument("--profile")
    kaggle_build.add_argument("--scale", choices=["1k", "10k", "50k"])
    kaggle_build.add_argument("--study")
    kaggle_build.add_argument("--json", action="store_true")
    kaggle_build.add_argument("--explain", action="store_true")
    kaggle_build.add_argument("--dry-run", action="store_true")
    for name in ("validate-input", "inspect-input"):
        kaggle_validate = kaggle_sub.add_parser(name)
        kaggle_validate.add_argument("zip")
        kaggle_validate.add_argument("--json", action="store_true")
        kaggle_validate.add_argument("--explain", action="store_true")
    kaggle_next = kaggle_sub.add_parser("next")
    kaggle_next.add_argument("--json", action="store_true")
    kaggle_next.add_argument("--explain", action="store_true")
    kaggle_next.add_argument("--dry-run", action="store_true")
    kaggle_import = kaggle_sub.add_parser("import-output")
    kaggle_import.add_argument("--stage", required=True, choices=["diagnostic"])
    kaggle_import.add_argument("zip")
    kaggle_import.add_argument("--json", action="store_true")
    kaggle_import.add_argument("--explain", action="store_true")

    notebooks = subparsers.add_parser("notebooks", help="Generate and validate canonical Phase 1 notebooks")
    notebooks_sub = notebooks.add_subparsers(dest="notebooks_kind", required=True)
    for name in ("generate", "validate", "check-determinism"):
        notebooks_command = notebooks_sub.add_parser(name)
        notebooks_command.add_argument("--json", action="store_true")
        notebooks_command.add_argument("--explain", action="store_true")
        notebooks_command.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "status":
        _print(_status())
        return 0
    if args.command == "next-action":
        payload = (
            write_next_action(root=args.root, registry_path=args.registry)
            if args.write
            else determine_next_action(root=args.root, registry_path=args.registry)
        )
        _print(payload)
        return 0
    if args.command == "discover":
        from certgen.discovery import (
            DiscoveryLimits,
            PackageRequirement,
            PackageType,
            discover_asset_mount,
            discover_packages,
            discover_reference,
            discover_wheelhouse,
        )

        if args.discover_kind == "multipart":
            from certgen.notebooks.final_zip import reassemble_multipart_fallback

            payload = reassemble_multipart_fallback(args.manifest, output_path=args.out)
            exit_code = 0 if payload["passed"] else 6
            payload["exit_code"] = exit_code
            _print(payload)
            return exit_code
        limits = DiscoveryLimits(
            maximum_depth=args.max_depth,
            maximum_candidates=args.max_candidates,
            maximum_package_members=args.maximum_members,
            maximum_uncompressed_bytes=args.maximum_bytes,
        )
        if args.discover_kind == "packages":
            requirement = PackageRequirement(
                expected_package_type=PackageType(args.expected_package_type) if args.expected_package_type else None,
                expected_package_sha256=args.expected_package_sha256,
                expected_scientific_identity_hash=args.expected_scientific_identity_hash,
                expected_stage=args.expected_stage,
                expected_study_hash=args.study_hash,
                expected_profile_id=args.profile_id,
                expected_configuration_hash=args.configuration_hash,
                expected_source_code_hash=args.expected_source_code_hash,
                expected_integrity_manifest=args.expected_integrity_manifest,
                expected_output_schema_version=args.expected_output_schema_version,
                expected_run_id=args.run_id,
                expected_scale=args.scale,
                required_completion_status=args.completion_status,
            )
            result = discover_packages(args.search_root, requirement=requirement, limits=limits)
            payload = result.to_dict()
            exit_code = 0 if payload["status"] in {"SELECTED_UNIQUE_VALID_PACKAGE", "DUPLICATE_IDENTICAL_COPY_DEDUPED"} else (
                4 if payload["status"] in {"AMBIGUOUS_MATCHING_PACKAGES", "AMBIGUOUS_DIFFERENT_CONTENT"} else 3
            )
        elif args.discover_kind == "expected-output":
            from certgen.discovery.expected_output import discover_expected_output

            payload = discover_expected_output(args.root, args.stage, args.search_root)
            exit_code = 0 if payload["status"] in {"SELECTED_UNIQUE_VALID_PACKAGE", "DUPLICATE_IDENTICAL_COPY_DEDUPED"} else (
                4 if payload["status"] == "AMBIGUOUS_DIFFERENT_CONTENT" else 3
            )
        elif args.discover_kind == "reference":
            payload = discover_reference(args.search_root, expected_kind=args.expected_kind, limits=limits)
            exit_code = 0 if payload["status"] == "SELECTED_UNIQUE_VALID_REFERENCE" else (
                4 if payload["status"].startswith("AMBIGUOUS") else 3
            )
        elif args.discover_kind == "assets":
            payload = discover_asset_mount(
                args.search_root,
                required_assets={args.asset_id: args.revision},
                limits=limits,
            )
            exit_code = 0 if payload["status"] in {"SELECTED_UNIQUE_VALID_ASSET_MOUNT", "DUPLICATE_IDENTICAL_COPY_DEDUPED"} else (
                4 if payload["status"].startswith("AMBIGUOUS") else 3
            )
        else:
            payload = discover_wheelhouse(
                args.search_root,
                profile=args.profile,
                limits=limits,
                target_python=args.target_python,
                target_platform=args.target_platform,
            )
            exit_code = 0 if payload["status"] in {"SELECTED_UNIQUE_VALID_WHEELHOUSE", "DUPLICATE_IDENTICAL_COPY_DEDUPED"} else (
                4 if payload["status"].startswith("AMBIGUOUS") else 3
            )
        payload["exit_code"] = exit_code
        if args.explain:
            payload["explanation"] = "Runtime paths are reported separately; selection uses only validated internal identity and hashes."
        _print(payload)
        return exit_code
    if args.command == "kaggle":
        from certgen.phase1.kaggle import (
            build_static_input,
            import_diagnostic_output,
            inspect_input,
            inventory,
            validate_input,
        )
        from certgen.phase1.state import phase1_state

        if args.kaggle_kind == "inventory":
            payload = inventory()
        elif args.kaggle_kind == "build-input":
            if args.stage == "preflight" and args.profile not in {None, "cifar_integrity_minimal"}:
                raise ValueError("Phase 1 preflight supports only --profile cifar_integrity_minimal")
            if args.stage in {"generation", "features"} and args.scale not in {None, "1k"}:
                raise ValueError("Phase 1 permits only the 1k pilot before real 1k interpretation")
            payload = build_static_input(args.stage, dry_run=args.dry_run)
        elif args.kaggle_kind == "validate-input":
            payload = validate_input(args.zip)
        elif args.kaggle_kind == "inspect-input":
            payload = inspect_input(args.zip)
        elif args.kaggle_kind == "import-output":
            payload = import_diagnostic_output(args.zip)
        else:
            payload = phase1_state()
        _print(payload)
        return 0 if payload.get("passed", True) is not False else 2
    if args.command == "notebooks":
        from certgen.phase1.notebooks import validate_phase1_notebooks, write_phase1_notebooks

        if args.notebooks_kind == "generate":
            payload = (
                {"status": "DRY_RUN", "validation": validate_phase1_notebooks(deterministic=False), "claim_allowed": False}
                if args.dry_run
                else write_phase1_notebooks()
            )
        else:
            payload = validate_phase1_notebooks(deterministic=args.notebooks_kind == "check-determinism")
        _print(payload)
        return 0 if payload.get("passed", True) is not False else 2
    if args.command == "inspect" and args.inspect_kind == "package":
        from certgen.cvpr.package import inspect_notebook_input_package

        payload = inspect_notebook_input_package(args.zip)
        _print(payload)
        return 0 if payload["passed"] else 2
    if args.command == "readiness":
        from certgen.cvpr.readiness import readiness_report

        _print(readiness_report())
        return 0
    if args.command == "provenance":
        from certgen.max_ceiling.provenance import build_provenance_graph, verify_provenance_graph

        if args.provenance_kind == "graph":
            payload = build_provenance_graph(
                args.study,
                registry_path=args.registry,
                root=args.root,
                out_json=args.out_json,
                out_dot=args.out_dot,
            )
        else:
            payload = verify_provenance_graph(args.study, registry_path=args.registry, root=args.root)
        _print(payload)
        return 0 if payload.get("passed", True) else 2
    if args.command == "doctor":
        from certgen.max_ceiling.contracts import doctor_report

        payload = doctor_report(stage=args.stage, study_path=args.study, root=args.root)
        _print(payload)
        return 2 if payload["status"] in {"LOCAL_DEFECT", "STALE_ARTIFACT"} else 0
    if args.command == "capsule":
        from certgen.max_ceiling.capsule import build_run_capsule, inspect_run_capsule, verify_run_capsule

        if args.capsule_kind == "build":
            payload = build_run_capsule(
                args.stage, args.study, root=args.root, output=args.out, public=args.public
            )
        elif args.capsule_kind == "inspect":
            payload = inspect_run_capsule(args.zip)
        else:
            payload = verify_run_capsule(args.zip)
        _print(payload)
        return 0 if payload.get("passed", True) else 2
    if args.command == "scale-plan":
        from certgen.max_ceiling.contracts import freeze_scale_plan, scale_plan_next, scale_plan_status

        if args.scale_kind == "freeze":
            payload = freeze_scale_plan(args.study, root=args.root)
        elif args.scale_kind == "status":
            payload = scale_plan_status(args.study, root=args.root)
        else:
            payload = scale_plan_next(args.study, root=args.root)
        _print(payload)
        return 0 if payload.get("passed", True) else 2
    if args.command == "sensitivity":
        from certgen.max_ceiling.contracts import freeze_sensitivity, validate_sensitivity

        payload = (
            freeze_sensitivity(args.study, root=args.root)
            if args.sensitivity_kind == "freeze"
            else validate_sensitivity(args.study, root=args.root)
        )
        _print(payload)
        return 0 if payload.get("passed", True) else 2
    if args.command == "plan" and args.plan_kind == "resolution":
        from certgen.max_ceiling.contracts import plan_resolution

        payload = plan_resolution(args.study, root=args.root, trials=args.trials)
        _print(payload)
        return 0
    if args.command == "rehearse" and args.rehearse_kind == "failures":
        from certgen.max_ceiling.contracts import rehearse_failures

        if not args.all:
            raise ValueError("failure rehearsal currently requires --all")
        payload = rehearse_failures(root=args.root)
        _print(payload)
        return 0 if payload["passed"] else 2
    if args.command == "replay":
        from certgen.max_ceiling.contracts import replay_plan, verify_replay_plan

        payload = (
            replay_plan(args.study, root=args.root, changed_paths=args.changed)
            if args.replay_kind == "plan"
            else verify_replay_plan(args.study, root=args.root)
        )
        _print(payload)
        return 0 if payload.get("passed", True) else 2
    if args.command == "accounting" and args.accounting_kind == "summarize":
        from certgen.max_ceiling.contracts import summarize_accounting

        payload = summarize_accounting(args.study, root=args.root)
        _print(payload)
        return 2 if payload["status"] == "LOCAL_DEFECT" else 0
    if args.command == "profiles":
        from certgen.cvpr.profiles import list_profiles, load_profile

        payload = (
            {"profiles": list_profiles(), "claim_allowed": False}
            if args.profiles_kind == "list"
            else load_profile(args.profile)
        )
        _print(payload)
        return 0
    if args.command == "merge" and args.merge_kind == "features":
        from certgen.cvpr.feature_merge import merge_feature_run

        payload = merge_feature_run(args.run, imported_root=args.imported_root, output_root=args.output_root, registry_path=args.registry)
        _print(payload)
        return 0
    if args.command == "validate" and args.validate_kind == "reference":
        payload = run_onramp(
            search_roots=args.source,
            out_json=args.out_json,
            out_report=args.out_report,
            explain=args.explain,
        )
        if not payload["materialization_can_proceed"] and args.source:
            from certgen.core.io import write_json
            from certgen.cvpr.reference import validate_reference_source

            canonical = [validate_reference_source(source) for source in args.source]
            accepted = [row for row in canonical if row["passed"]]
            if accepted:
                selected = accepted[0]
                payload.update(
                    {
                        "status_code": "READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION",
                        "detected_paths": [selected],
                        "materialization_can_proceed": True,
                        "exact_next_command": f"python3 -m certgen materialize reference --source {shlex.quote(str(selected['source']))}",
                    }
                )
                write_json(payload, args.out_json)
                Path(args.out_report).write_text(
                    "# CIFAR-10 Reference Validation\n\n"
                    "Status: `READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION`\n\n"
                    f"Accepted layout: `{selected['layout']}`\n\n"
                    "The source path is recorded only in the machine-local JSON. No download was performed.\n\n"
                    f"Next command: `python3 -m certgen materialize reference --source <validated-source>`\n",
                    encoding="utf-8",
                )
        _print(payload)
        return 0 if payload["materialization_can_proceed"] else 2
    if args.command == "validate" and args.validate_kind == "claims":
        from certgen.max_ceiling.contracts import validate_claims

        payload = validate_claims(args.study, matrix_path=args.matrix)
        _print(payload)
        return 0 if payload["passed"] else 2
    if args.command == "materialize" and args.materialize_kind == "reference":
        from certgen.cvpr.reference import materialize_reference_source

        payload = materialize_reference_source(
            args.source, out_manifest=args.out_manifest, out_summary=args.out_summary
        )
        _print(payload)
        return 0
    if args.command == "validate" and args.validate_kind == "caches":
        from certgen.features.cache_v2 import validate_feature_cache_v2

        payload = validate_feature_cache_v2(features_path=args.features, sidecar_path=args.sidecar, artifact_root=args.artifact_root)
        _print(payload)
        return 0 if payload["passed"] else 2
    if args.command == "validate" and args.validate_kind == "certificate-inputs":
        from certgen.cvpr.certificate_inputs import validate_certificate_inputs

        payload = validate_certificate_inputs(
            study_path=args.study,
            family_path=args.family,
            inputs_root=args.inputs_root,
            write_result=not args.dry_run,
        )
        _print(payload)
        return 0 if payload["passed"] else 2
    if args.command == "validate" and args.validate_kind == "family-operational":
        from certgen.cvpr.operational import validate_family_operational

        payload = validate_family_operational(
            family_path=args.family,
            study_path=args.study,
            inputs_root=args.inputs_root,
            coverage_path=None if args.dry_run else args.coverage_out,
            write_result=not args.dry_run,
        )
        _print(payload)
        return 0 if payload["passed"] else 2
    if args.command == "validate" and args.validate_kind == "kaggle-input":
        from certgen.cvpr.package import inspect_notebook_input_package

        payload = inspect_notebook_input_package(args.zip)
        _print(payload)
        return 0 if payload["passed"] else 2
    if args.command == "validate" and args.validate_kind == "kaggle-output":
        import zipfile

        from certgen.cvpr.output_schemas import OUTPUT_SCHEMAS, validate_output_zip

        kind = args.kind
        if kind is None:
            with zipfile.ZipFile(args.zip) as archive:
                names = set(archive.namelist())
            matches = [candidate for candidate, schema in OUTPUT_SCHEMAS.items() if schema.status_file in names]
            if len(matches) != 1:
                raise ValueError(f"could not infer one output kind; matches={matches}")
            kind = matches[0]
        payload = validate_output_zip(kind, args.zip)
        _print(payload)
        return 0 if payload["passed"] else 2
    if args.command == "import":
        payload = import_repair(
            kind="feature" if args.kind == "features" else args.kind,
            zip_path=args.zip,
            out_dir=args.out_dir,
            out_json=args.out_json,
            out_report=args.out_report,
            registry_path=args.registry,
        )
        _print(payload)
        return 0 if payload["passed"] else 2
    if args.command == "audit":
        if args.lane == "kaggle-launch":
            from certgen.phase1.audit import run_kaggle_launch_audit

            payload = run_kaggle_launch_audit()
        elif args.lane == "cpu-execution":
            from certgen.phase1.audit import run_cpu_execution_audit

            payload = run_cpu_execution_audit()
        elif args.lane == "universal-kaggle":
            from certgen.discovery.audit import run_universal_kaggle_audit

            payload = run_universal_kaggle_audit()
        elif args.lane == "notebooks":
            payload = analyze_all()
        elif args.lane == "paper":
            payload = run_firewall()
        elif args.lane == "artifact-registry":
            payload = verify_artifact_registry()
        elif args.lane == "registries":
            from certgen.cvpr.registries import validate_all_cvpr_registries

            payload = validate_all_cvpr_registries()
        elif args.lane == "cvpr":
            from certgen.audit.cvpr_final_audit import run_cvpr_audit

            payload = run_cvpr_audit()
        elif args.lane == "maximum-ceiling":
            from certgen.max_ceiling.audit import run_maximum_ceiling_audit

            payload = run_maximum_ceiling_audit()
        else:
            from certgen.audit.final_pre_run_audit import run_final_pre_run_audit

            payload = run_final_pre_run_audit(args.out_root, dry_run=args.dry_run)
        _print(payload)
        return 0 if payload["passed"] else 2
    if args.command == "validate-caches":
        from certgen.features.cache_v2 import validate_feature_cache_v2

        payload = validate_feature_cache_v2(features_path=args.features, sidecar_path=args.sidecar, artifact_root=args.artifact_root)
        _print(payload)
        return 0 if payload["passed"] else 2
    if args.command == "certify":
        from certgen.cvpr.certificate import certify_feature_bundle

        family = Path(args.family)
        if not family.is_file():
            family = Path("registry/cvpr/families") / f"{args.family}.json"
        payload = certify_feature_bundle(
            study_path=args.study, family_path=family, feature_bundle_path=args.features,
            reference_draw_plan_path=args.reference_draw_plan, comparison_id=args.comparison,
            feature_space=args.feature_space, out_path=args.out, fingerprint_path=args.fingerprint,
            registry_path=args.registry,
        )
        _print(payload)
        return 0
    if args.command == "rank":
        from certgen.cvpr.ranking import build_partial_ranking

        paths = [
            path for path in sorted(Path(args.certificate_dir).glob("*.json"))
            if json.loads(path.read_text(encoding="utf-8")).get("schema_version") == "certgen.cvpr.certificate.v1"
        ]
        family = Path(args.family)
        if not family.is_file():
            family = Path("registry/cvpr/families") / f"{args.family}.json"
        payload = build_partial_ranking(paths, out_dir=args.out_dir, aggregation_rule=args.aggregation_rule, family_path=family)
        _print(payload)
        return 0
    if args.command == "figures":
        from certgen.visualization.factory import write_planning_contract

        request = json.loads(Path(args.request).read_text(encoding="utf-8"))
        payload = write_planning_contract(request, args.out)
        _print(payload)
        return 0
    if args.command == "package":
        from certgen.cvpr.package import build_notebook_input_package

        inputs: dict[str, str] = {}
        for item in args.input:
            if "=" not in item:
                raise ValueError("--input values must use NAME=PATH")
            name, value = item.split("=", 1)
            if name in inputs:
                raise ValueError(f"duplicate package input name: {name}")
            inputs[name] = value
        payload = build_notebook_input_package(kind=args.kind, config_path=args.config, inputs=inputs, out_zip=args.out_zip, manifest_out=args.manifest_out)
        _print(payload)
        return 0
    if args.command == "freeze-config":
        from certgen.cvpr.package import freeze_notebook_configuration

        payload = freeze_notebook_configuration(args.input, args.out)
        _print(payload)
        return 0
    if args.command == "freeze" and args.freeze_kind == "study":
        from certgen.cvpr.study import freeze_study

        out = args.out or f"artifacts/cvpr/study/{args.profile}.yaml"
        payload = freeze_study(args.profile, out_path=out, alpha=args.alpha)
        _print(payload)
        return 0
    if args.command == "analyze":
        from certgen.cvpr.analysis import (
            point_vs_certified_contract,
            summarize_samples_to_decision,
            write_cross_feature_analysis,
            write_ranking_stability,
        )
        from certgen.cvpr.contracts import atomic_write_json

        if args.kind == "pilot-stop-go":
            if not args.pilot_summary:
                raise ValueError("pilot-stop-go requires --pilot-summary")
            from certgen.cvpr.pilot_stop_go import write_pilot_stop_go

            payload = write_pilot_stop_go(args.pilot_summary, args.out)
        elif args.kind == "point-vs-certified":
            if not args.point_estimates or not args.ranking:
                raise ValueError("point-vs-certified requires --point-estimates and --ranking")
            points = json.loads(Path(args.point_estimates).read_text(encoding="utf-8"))
            ranking = json.loads(Path(args.ranking).read_text(encoding="utf-8"))
            payload = point_vs_certified_contract(point_estimates=points, ranking=ranking)
            atomic_write_json(payload, args.out)
        else:
            if not args.certificate_dir:
                raise ValueError(f"{args.kind} requires --certificate-dir")
            rows = [
                payload
                for path in sorted(Path(args.certificate_dir).glob("*.json"))
                for payload in [json.loads(path.read_text(encoding="utf-8"))]
                if payload.get("schema_version") == "certgen.cvpr.certificate.v1"
            ]
            if args.kind == "samples-to-decision":
                payload = summarize_samples_to_decision(rows)
                atomic_write_json(payload, args.out)
            elif args.kind == "cross-feature":
                payload = write_cross_feature_analysis(rows, args.out)
            else:
                payload = write_ranking_stability(rows, args.out)
        _print(payload)
        return 0
    if args.command in {"plan-runtime", "runtime-plan"}:
        from certgen.cvpr.runtime_planner import build_runtime_plan

        report = args.ingest_preflight
        if args.command == "runtime-plan" and args.runtime_action == "ingest-preflight":
            if not args.runtime_report:
                raise ValueError("runtime-plan ingest-preflight requires a report path")
            if report is not None:
                raise ValueError("provide the preflight report either positionally or with --ingest-preflight")
            report = args.runtime_report
        payload = build_runtime_plan(args.config, args.out, preflight_report=report)
        _print(payload)
        return 0
    if args.command == "run" and args.run_kind == "family-certificates":
        from certgen.cvpr.family_certificates import run_family_certificates

        payload = run_family_certificates(
            study_path=args.study,
            family_path=args.family,
            inputs_root=args.inputs_root,
            reference_draw_plan=args.reference_draw_plan,
            metric_result=args.metric_result,
            sanity_result=args.sanity_result,
            operational_status=args.operational_status,
            out_dir=args.out_dir,
            registry_path=args.registry,
        )
        _print(payload)
        return 0
    if args.command == "prepare":
        from certgen.cvpr.prepare import prepare_family, prepare_features, prepare_generation, prepare_preflight
        from certgen.cvpr.runtime_planner import build_runtime_plan

        if args.prepare_kind == "preflight":
            approvals = json.loads(Path(args.license_approvals).read_text(encoding="utf-8")) if args.license_approvals else None
            payload = prepare_preflight(
                out_dir=args.out_dir,
                policy=args.asset_policy,
                license_approvals=approvals,
                profile=args.profile,
                profile_path=args.profile_path,
                model_ids=_split_csv_ids(args.models),
                extractor_ids=_split_csv_ids(args.extractors),
            )
        elif args.prepare_kind == "generation":
            payload = prepare_generation(
                out_dir=args.out_dir,
                preflight_config=args.preflight_config,
                preflight_import=args.preflight_import,
                reference_manifest=args.reference_manifest,
                scale=args.scale,
                study_path=args.study,
            )
        elif args.prepare_kind == "features":
            payload = prepare_features(
                out_dir=args.out_dir,
                generation_import=args.generation_import,
                preflight_import=args.preflight_import,
                reference_manifest=args.reference_manifest,
                reference_draw_plan=args.reference_draw_plan,
                input_mode=args.input_mode,
                external_image_manifest=args.external_image_manifest,
                external_image_root=args.external_image_root,
                mount_id=args.mount_id,
                expected_mount_path=args.expected_mount_path,
                mount_manifest_hash=args.mount_manifest_hash,
                controls_dir=args.controls_dir,
            )
        elif args.prepare_kind == "family":
            payload = prepare_family(out_dir=args.out_dir, alpha=args.alpha, study_path=args.study)
        elif args.prepare_kind == "reference-draw":
            from certgen.cvpr.reference_draw import prepare_reference_draw

            payload = prepare_reference_draw(
                profile_id=args.profile,
                study_path=args.study,
                reference_manifest=args.reference_manifest,
                out_path=args.out,
                seed=args.seed,
                registry_path=args.registry,
                dry_run=args.dry_run,
            )
        elif args.prepare_kind == "controls":
            from certgen.cvpr.controls import prepare_controls

            payload = prepare_controls(
                study_path=args.study,
                reference_draw=args.reference_draw_plan,
                out_root=args.out_root,
                registry_path=args.registry,
                dry_run=args.dry_run,
            )
        elif args.prepare_kind == "certificate-inputs":
            from certgen.cvpr.certificate_inputs import prepare_certificate_inputs

            payload = prepare_certificate_inputs(
                study_path=args.study,
                family_path=args.family,
                feature_run=args.feature_run,
                reference_draw_plan=args.reference_draw_plan,
                out_root=args.out_root,
                registry_path=args.registry,
                dry_run=args.dry_run,
            )
        elif args.prepare_kind == "gate-configs":
            from certgen.cvpr.post_cache import prepare_post_cache_gates

            payload = prepare_post_cache_gates(
                study_path=args.study,
                family_path=args.family,
                feature_run=args.feature_run,
                metric_out=args.metric_out,
                sanity_out=args.sanity_out,
                registry_path=args.registry,
                dry_run=args.dry_run,
            )
        else:
            payload = build_runtime_plan(args.config, args.out, preflight_report=args.ingest_preflight)
        _print(payload)
        return 0 if not str(payload.get("status", "")).startswith("BLOCKED") else 2
    if args.command == "release" and args.release_kind == "build-archive":
        from certgen.release.archive import build_archive

        payload = build_archive(output=args.out, run_tests=not args.no_tests)
        _print(payload)
        return 0
    if args.command == "synthetic-runtime":
        from certgen.cvpr.synthetic_runtime import run_synthetic_runtime

        payload = run_synthetic_runtime(args.out_dir)
        _print(payload)
        return 0
    if args.command == "sanity":
        if args.config or args.out:
            if not args.config or not args.out:
                raise ValueError("--config and --out must be provided together")
            from certgen.cvpr.gates import run_metric_reproduction_gate, run_sanity_controls

            payload = (
                run_metric_reproduction_gate(args.config, args.out)
                if args.kind == "metric-reproduction"
                else run_sanity_controls(args.config, args.out)
            )
            _print(payload)
            return 0 if payload["status"] == "PASS" else 2
        payload = {
            "status": "BLOCKED_REAL_VALIDATED_FEATURE_CACHES_REQUIRED",
            "requested_gate": args.kind,
            "exact_next_action": determine_next_action(),
            "evidence_class": "planning_only",
            "claim_allowed": False,
        }
        _print(payload)
        return 2
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":  # pragma: no cover
    try:
        raise SystemExit(main())
    except (FileNotFoundError, PermissionError, ValueError) as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(2) from None
