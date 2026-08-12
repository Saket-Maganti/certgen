"""Argparse surface for the prospective ICML 2027 research layer."""

from __future__ import annotations

import argparse
import json
from typing import Any


def add_commands(subparsers: Any) -> None:
    icml = subparsers.add_parser("icml2027", help="Prospective ICML 2027 research and validation tools")
    icml_sub = icml.add_subparsers(dest="icml_command", required=True)

    synthetic = icml_sub.add_parser("synthetic")
    synthetic_sub = synthetic.add_subparsers(dest="icml_action", required=True)
    synthetic_run = synthetic_sub.add_parser("run")
    synthetic_run.add_argument("--config", required=True)
    synthetic_run.add_argument("--out-dir", required=True)

    production_mmd = icml_sub.add_parser("production-mmd")
    production_mmd_sub = production_mmd.add_subparsers(dest="icml_action", required=True)
    production_mmd_validate = production_mmd_sub.add_parser("validate")
    production_mmd_validate.add_argument("--config", required=True)
    production_mmd_validate.add_argument("--out-dir", required=True)

    baseline = icml_sub.add_parser("baseline")
    baseline_sub = baseline.add_subparsers(dest="icml_action", required=True)
    baseline_run = baseline_sub.add_parser("run")
    baseline_run.add_argument("--baseline", required=True)
    baseline_run.add_argument("--feature-bundle", required=True)
    baseline_run.add_argument("--study", required=True)
    baseline_run.add_argument("--out", required=True)

    analyze = icml_sub.add_parser("analyze")
    analyze_sub = analyze.add_subparsers(dest="icml_action", required=True)
    sample = analyze_sub.add_parser("samples-to-decision")
    sample.add_argument("--input", required=True)
    sample.add_argument("--out", required=True)
    sample.add_argument("--prefixes", default="100,250,500,1000,2000,5000,10000")
    cost = analyze_sub.add_parser("cost-to-decision")
    cost.add_argument("--input", required=True)
    cost.add_argument("--out", required=True)
    agreement = analyze_sub.add_parser("representation-agreement")
    agreement.add_argument("--input", required=True)
    agreement.add_argument("--out-dir", required=True)
    duplicates = analyze_sub.add_parser("duplicates")
    duplicates.add_argument("--root", action="append", required=True)
    duplicates.add_argument("--out", required=True)
    duplicates.add_argument("--near-threshold", type=int, default=4)

    audit = icml_sub.add_parser("audit")
    audit_sub = audit.add_subparsers(dest="icml_action", required=True)
    numerical = audit_sub.add_parser("numerical")
    numerical.add_argument("--out-dir", required=True)
    numerical.add_argument("--seed", type=int, default=2027)
    production_numerical = audit_sub.add_parser("production-numerical")
    production_numerical.add_argument("--out-dir", required=True)
    production_numerical.add_argument("--seed", type=int, default=20270812)
    boundary = audit_sub.add_parser("boundary")
    boundary.add_argument("--config", required=True)
    boundary.add_argument("--out-dir", required=True)
    paired_performance = audit_sub.add_parser("paired-performance")
    paired_performance.add_argument("--out", required=True)
    paired_performance.add_argument("--seed", type=int, default=20270812)
    c2st = audit_sub.add_parser("c2st")
    c2st.add_argument("--out-dir", required=True)
    c2st.add_argument("--seed", type=int, default=20270812)
    go_no_go = audit_sub.add_parser("go-no-go")
    go_no_go.add_argument("--registry", required=True)
    go_no_go.add_argument("--out", required=True)

    evidence = icml_sub.add_parser("evidence")
    evidence_sub = evidence.add_subparsers(dest="icml_action", required=True)
    evidence_audit = evidence_sub.add_parser("audit")
    evidence_audit.add_argument("--registry", default="registry/icml2027/claim_registry.yaml")
    evidence_audit.add_argument("--out", default="reports/icml2027/CLAIM_EVIDENCE_MATRIX.csv")

    plan = icml_sub.add_parser("plan")
    plan_sub = plan.add_subparsers(dest="icml_action", required=True)
    compute = plan_sub.add_parser("compute")
    compute.add_argument("--config", required=True)
    compute.add_argument("--out", required=True)
    selection = plan_sub.add_parser("study-selection")
    selection.add_argument("--config", required=True)
    selection.add_argument("--out", required=True)
    power = plan_sub.add_parser("power")
    power.add_argument("--config", required=True)
    power.add_argument("--out-dir", required=True)

    reviewer = icml_sub.add_parser("reviewer-attack")
    reviewer_sub = reviewer.add_subparsers(dest="icml_action", required=True)
    reviewer_run = reviewer_sub.add_parser("run")
    reviewer_run.add_argument("--config", required=True)
    reviewer_run.add_argument("--out-dir", default="artifacts/icml2027/reviewer_attacks")

    scaling = icml_sub.add_parser("multi-model")
    scaling_sub = scaling.add_subparsers(dest="icml_action", required=True)
    scaling_run = scaling_sub.add_parser("run")
    scaling_run.add_argument("--config", required=True)
    scaling_run.add_argument("--out-dir", default="reports/icml2027")

    adaptive = icml_sub.add_parser("adaptive")
    adaptive_sub = adaptive.add_subparsers(dest="icml_action", required=True)
    adaptive_run = adaptive_sub.add_parser("run")
    adaptive_run.add_argument("--config", required=True)
    adaptive_run.add_argument("--out", default="reports/icml2027/ADAPTIVE_ALLOCATION_COMPARISON.csv")

    replay = icml_sub.add_parser("replay")
    replay_sub = replay.add_subparsers(dest="icml_action", required=True)
    replay_study = replay_sub.add_parser("study")
    replay_study.add_argument("--study-id", required=True)
    replay_study.add_argument("--registry", default="registry/icml2027/study_registry.yaml")
    replay_study.add_argument("--out-dir", default="artifacts/icml2027/replay")

    notebooks = icml_sub.add_parser("notebooks")
    notebooks_sub = notebooks.add_subparsers(dest="icml_action", required=True)
    for action in ("generate", "check-determinism"):
        command = notebooks_sub.add_parser(action)
        command.add_argument("--root", default="notebooks/kaggle/icml2027")
    rehearse = notebooks_sub.add_parser("rehearse")
    rehearse.add_argument("--out-dir", default="reports/icml2027/notebook_rehearsals")

    payload = icml_sub.add_parser("payload")
    payload_sub = payload.add_subparsers(dest="icml_action", required=True)
    payload_validate = payload_sub.add_parser("validate")
    payload_validate.add_argument("index")
    payload_validate.add_argument("--type", choices=["generation", "features"])
    payload_validate.add_argument("--seed-manifest")
    payload_validate.add_argument("--worker-spec")
    payload_import = payload_sub.add_parser("import")
    payload_import.add_argument("index")
    payload_import.add_argument("--out-dir", required=True)

    released = subparsers.add_parser("released-samples", help="Validate and import released sample archives")
    released_sub = released.add_subparsers(dest="released_action", required=True)
    validate = released_sub.add_parser("validate")
    validate.add_argument("archive")
    validate.add_argument("--manifest")
    validate.add_argument("--expected-count", type=int)
    validate.add_argument("--out")
    importer = released_sub.add_parser("import")
    importer.add_argument("archive")
    importer.add_argument("--manifest", required=True)
    importer.add_argument("--out-dir", required=True)
    build = released_sub.add_parser("build-manifest")
    build.add_argument("archive")
    build.add_argument("--metadata", required=True)
    build.add_argument("--out", required=True)


def _print(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def dispatch(args: argparse.Namespace) -> int | None:
    if args.command == "released-samples":
        from certgen.icml2027.released_samples import build_manifest, import_archive, validate_archive
        from certgen.icml2027.common import write_json

        if args.released_action == "validate":
            payload = validate_archive(args.archive, manifest_path=args.manifest, expected_count=args.expected_count)
            if args.out:
                write_json(args.out, payload)
            _print(payload)
            return 0 if payload["passed"] else 2
        if args.released_action == "import":
            payload = import_archive(args.archive, args.manifest, args.out_dir)
        else:
            payload = build_manifest(args.metadata, args.archive, args.out)
        _print(payload)
        return 0
    if args.command != "icml2027":
        return None
    command, action = args.icml_command, args.icml_action
    if command == "synthetic" and action == "run":
        from certgen.icml2027.synthetic import run_synthetic_suite

        payload = run_synthetic_suite(args.config, args.out_dir)
    elif command == "production-mmd" and action == "validate":
        from certgen.icml2027.production_mmd import run_production_mmd_validation

        payload = run_production_mmd_validation(args.config, args.out_dir)
    elif command == "baseline" and action == "run":
        from certgen.icml2027.baselines import run_baseline

        payload = run_baseline(args.baseline, args.feature_bundle, args.study, args.out)
    elif command == "analyze" and action == "samples-to-decision":
        from certgen.icml2027.analysis import samples_to_decision

        prefixes = tuple(int(value) for value in args.prefixes.split(",") if value.strip())
        payload = samples_to_decision(args.input, args.out, prefixes=prefixes)
    elif command == "analyze" and action == "cost-to-decision":
        from certgen.icml2027.analysis import cost_to_decision

        payload = cost_to_decision(args.input, args.out)
    elif command == "analyze" and action == "representation-agreement":
        from certgen.icml2027.representations import analyze_representation_agreement

        payload = analyze_representation_agreement(args.input, args.out_dir)
    elif command == "analyze" and action == "duplicates":
        from certgen.icml2027.analysis import analyze_duplicates

        payload = analyze_duplicates(args.root, args.out, near_threshold=args.near_threshold)
    elif command == "audit" and action == "numerical":
        from certgen.icml2027.numerical import run_numerical_audit

        payload = run_numerical_audit(args.out_dir, seed=args.seed)
    elif command == "audit" and action == "production-numerical":
        from certgen.icml2027.numerical_reviewer import run_production_numerical_attacks

        payload = run_production_numerical_attacks(args.out_dir, seed=args.seed)
    elif command == "audit" and action == "boundary":
        from certgen.icml2027.boundary_benchmark import run_boundary_benchmark

        payload = run_boundary_benchmark(args.config, args.out_dir)
    elif command == "audit" and action == "paired-performance":
        from certgen.icml2027.paired_performance import run_paired_performance_audit

        payload = run_paired_performance_audit(args.out, seed=args.seed)
    elif command == "audit" and action == "c2st":
        from certgen.icml2027.c2st_benchmark import run_c2st_benchmark

        payload = run_c2st_benchmark(args.out_dir, seed=args.seed)
    elif command == "audit" and action == "go-no-go":
        from certgen.icml2027.gates import audit_go_no_go

        payload = audit_go_no_go(args.registry, args.out)
    elif command == "evidence" and action == "audit":
        from certgen.icml2027.evidence import audit_evidence

        payload = audit_evidence(args.registry, args.out)
    elif command == "plan" and action == "compute":
        from certgen.icml2027.planning import plan_compute

        payload = plan_compute(args.config, args.out)
    elif command == "plan" and action == "study-selection":
        from certgen.icml2027.planning import plan_study_selection

        payload = plan_study_selection(args.config, args.out)
    elif command == "plan" and action == "power":
        from certgen.icml2027.power_planning import run_power_planning

        payload = run_power_planning(args.config, args.out_dir)
    elif command == "reviewer-attack" and action == "run":
        from certgen.icml2027.reviewer import run_reviewer_attacks

        payload = run_reviewer_attacks(args.config, args.out_dir)
    elif command == "multi-model" and action == "run":
        from certgen.icml2027.stress import run_multi_model_scaling

        payload = run_multi_model_scaling(args.config, args.out_dir)
    elif command == "adaptive" and action == "run":
        from certgen.icml2027.stress import run_adaptive_comparison

        payload = run_adaptive_comparison(args.config, args.out)
    elif command == "replay" and action == "study":
        from certgen.icml2027.replay import replay_study

        payload = replay_study(args.study_id, registry_path=args.registry, out_dir=args.out_dir)
    elif command == "notebooks" and action == "generate":
        from certgen.icml2027.notebooks import generate_notebooks

        payload = generate_notebooks(args.root)
    elif command == "notebooks" and action == "check-determinism":
        from certgen.icml2027.notebooks import check_notebook_determinism

        payload = check_notebook_determinism(args.root)
    elif command == "notebooks" and action == "rehearse":
        from certgen.icml2027.notebook_runtime import run_closure_rehearsals

        payload = run_closure_rehearsals(args.out_dir)
    elif command == "payload" and action == "validate":
        from certgen.icml2027.payload import validate_multipart_payload

        payload = validate_multipart_payload(
            args.index,
            expected_type=args.type,
            seed_manifest_path=args.seed_manifest,
            worker_spec_path=args.worker_spec,
        )
    elif command == "payload" and action == "import":
        from certgen.icml2027.payload import import_multipart_payload

        payload = import_multipart_payload(args.index, args.out_dir)
    else:  # pragma: no cover - argparse prevents this
        raise AssertionError(f"unhandled ICML command: {command}/{action}")
    _print(payload)
    return 0 if payload.get("passed", True) else 2
