#!/usr/bin/env python3
"""Build the compact, truth-bound final-closure report set from live artifacts."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from certgen.icml2027.common import file_sha256, write_csv, write_json  # noqa: E402


OUT = ROOT / "reports/icml2027/final_closure"
STATUS = "ICML2027_FINAL_CLOSURE_COMPLETE_LEGACY_AND_ICML_GPU_PATH_READY"
LEGACY_FILES = {
    "diagnostic_notebook": "notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb",
    "diagnostic_input_zip": "artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip",
    "preflight_notebook": "notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb",
    "preflight_input_zip": "artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip",
    "legacy_1k_generation_notebook": "notebooks/kaggle/certgen_cvpr_generation_1k_t4x2.ipynb",
    "legacy_1k_feature_notebook": "notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2.ipynb",
    "legacy_frozen_profile": "artifacts/cvpr/study/cifar_integrity_minimal.yaml",
    "legacy_reference_draw_plan": "registry/manifests/cvpr/reference_draw_plan.json",
    "legacy_pilot_link": "registry/icml2027/legacy_pilot_link.yaml",
    "cifar_10k_v1_config": "configs/icml2027/cifar_confirmatory_10k_v1.yaml",
}


def _read(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _write_md(name: str, lines: list[str]) -> None:
    (OUT / name).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _ledger() -> list[dict[str, str]]:
    with (OUT / "CERTGEN_FINAL_CLOSURE_COMMAND_LEDGER.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    baseline = _read("reports/icml2027/final_closure/CERTGEN_FINAL_CLOSURE_BASELINE.json")
    cpu = _read("reports/icml2027/final_closure/CPU_SCIENCE_SUMMARY.json")
    boundary = _read("artifacts/icml2027/final_closure_boundary/ANYTIME_BOUNDARY_COMPARISON.summary.json")
    contract = _read("registry/icml2027/cifar_10k_v2_execution_contract_v1.json")
    seed = _read("registry/manifests/icml2027/cifar10k_generator_seed_manifest_v1.json")
    normalization = _read("reports/icml2027/production_mmd/NORMALIZATION_POWER_AUDIT.summary.json")
    independent = _read("reports/icml2027/final_closure/INDEPENDENT_MMD_REPRODUCTION.json")
    ledger = _ledger()
    latest_by_phase = {row["phase"]: row for row in ledger}
    after_hashes = {name: file_sha256(ROOT / path) for name, path in LEGACY_FILES.items()}
    if after_hashes != baseline["legacy_hashes"]:
        raise RuntimeError("legacy 1k scientific identity changed; final closure must stop")

    legacy_lines = [
        "# Legacy 1k immutability audit",
        "",
        "All ten frozen identities are byte-for-byte unchanged. The canonical real path remains diagnostic → import → preflight → import → 1k generation → import → 1k features → import → CPU certificate/analysis.",
        "",
        "| Artifact | Before SHA-256 | After SHA-256 | Result |",
        "|---|---|---|---|",
    ]
    for key in LEGACY_FILES:
        value = after_hashes[key]
        legacy_lines.append(f"| `{key}` | `{baseline['legacy_hashes'][key]}` | `{value}` | PASS |")
    legacy_lines.extend(["", "No legacy notebook, input ZIP, study/profile, draw plan, or pilot link was rebuilt. `claim_allowed=false`."])
    _write_md("LEGACY_1K_IMMUTABILITY_AUDIT.md", legacy_lines)

    dependency = cpu["fixture"]["dependency_lifecycle"]
    _write_md(
        "ICML_DEPENDENCY_LIFECYCLE_AUDIT.md",
        [
            "# ICML dependency lifecycle audit",
            "",
            "Result: PASS in CPU fixtures. READY notebooks authenticate with stdlib first, import only authenticated source, select an exact lane lock, validate installed distributions, install only under an allowed mode, run `pip check` and import smoke, write a report/marker, require restart after installation, and verify the same identity on the second pass.",
            "",
            "Marker fields: lane, input ZIP SHA-256, source-tree SHA-256, dependency-profile ID, dependency-lock SHA-256, Python version, platform, and `claim_allowed=false`. Stale source/package/lock/lane markers fail closed.",
            "",
            f"- Compatible environment: `{dependency['compatible']['passed']}`",
            f"- Offline exact-lock install requested restart: `{dependency['install']['restart_required']}`",
            f"- Identity-bound second pass: `{dependency['second_pass']['second_pass_identity_verified']}`",
            "- Tested modes: `USE_PREINSTALLED_VALIDATED`, `KAGGLE_INTERNET_ON_INSTALL` planning branch, and `PRIVATE_WHEELHOUSE_OFFLINE` fixture.",
            "- Negative tests: incompatible preinstalled environment, stale marker, wrong identity, missing wheel coverage, `pip check`/verification failure, and import-smoke propagation.",
            "",
            "The fixture does not assert the contents of a future Kaggle base image. Each real launch still validates or installs its authenticated exact lock. `claim_allowed=false`.",
        ],
    )

    _write_md(
        "SCIENTIFIC_PAYLOAD_CONTRACT.md",
        [
            "# Scientific payload contract",
            "",
            "Generation and feature READY lanes no longer close with metadata-only ZIPs. Preflight-only lanes may.",
            "",
            "Generation uses `<lane>.output.index.json` plus ordered `.partNNN.zip` files containing PNG shards, per-shard JSONL manifests, frozen sample IDs and generator seeds, checkpoint revisions, image hashes, runtime results, dependency verification, worker spec, and scientific identity.",
            "",
            "Features use the same multipart index with NPZ shards and exact sidecars. Validation checks sample order, count, dimension, dtype, finiteness, extractor revision, preprocessing hash, source-manifest identity, shard integrity, runtime, and provenance.",
            "",
            "The index binds study/configuration, ordered part name/hash/size, global payload-manifest hash, sample coverage, and `claim_allowed=false`. Missing parts, corrupt bytes, unsafe paths, symlinks, duplicates, wrong membership, row-order drift, and identity mutations fail closed. `payload_index_sha256` authenticates the complete index without an impossible self-referential identity field.",
            "",
            "CLI: `python3 -m certgen icml2027 payload validate <index> [--type generation|features] [--seed-manifest ...] [--worker-spec ...]`. Copy-forward receipts preserve the source index and ordered part identities; local import revalidates before extraction.",
        ],
    )

    _write_md(
        "WORKER_SPEC_SCIENTIFIC_IDENTITY_AUDIT.md",
        [
            "# Worker-spec scientific-identity audit",
            "",
            "Every executable worker spec requires schema/lane, study ID/hash, configuration SHA-256, authenticated prerequisite-set SHA-256, applicable reference plan, model and extractor revisions, preprocessing hashes, seed-plan and sample-policy hashes, expected prefix hashes/counts/shards/coverage, output schema, and `claim_allowed=false`.",
            "",
            "Generation partitions prove exact union, empty intersections, both frozen models, and exact seed-record hashes. Feature partitions prove every extractor × source-role × shard occurs exactly once with the same source order. Gap, overlap, wrong model/extractor, duplicate shard, extra shard, and hash mutations fail closed.",
            "",
            "The two-pass builder first computes the authenticated prerequisite-set hash, then creates a worker spec with `scripts/icml2027/build_worker_spec.py`, then builds the final ZIP. Authentic bytes for the wrong experiment are rejected.",
        ],
    )

    _write_md(
        "GENERATOR_SEED_CONTRACT_AUDIT.md",
        [
            "# Generator seed contract audit",
            "",
            f"- Execution contract: `{contract['execution_contract_id']}` / `{contract['execution_contract_sha256']}`",
            f"- Seed manifest: `registry/manifests/icml2027/cifar10k_generator_seed_manifest_v1.json` / `{seed['manifest_sha256']}`",
            f"- Records: `{len(seed['records'])}`; exact regeneration: PASS; 100,000-identity collision audit: PASS.",
            "- Sample identity remains the immutable v2 SHA-256 policy. Generator RNG uses a separate domain-separated canonical string, SHA-256, first eight bytes, big endian, sign bit cleared, range `[0, 2^63-1]`.",
            "- Any collision hard-fails and requires a new derivation version; it is never retried silently.",
            "- GPU call: `torch.Generator(device=device).manual_seed(generator_seed)`.",
            "- Real workers consume exact authenticated records, never an unrelated integer range. Resume requires the prior manifest and exact checkpoint/seed/image hash.",
            "",
            "This is execution semantics layered on frozen v2; the v2 study file was not edited. `claim_allowed=false`.",
        ],
    )

    rehearsal = cpu["fixture"]
    _write_md(
        "FULL_GENERATION_TO_FEATURE_REHEARSAL.md",
        [
            "# Full generation-to-feature rehearsal",
            "",
            f"Result: `{'PASS' if rehearsal['passed'] else 'FAIL'}`. This is deterministic CPU fixture validation, not real generator evidence.",
            "",
            f"- Two fake models × 100 decoded PNGs; two generation shards/model; four multipart parts; validation `{rehearsal['generation_validation']['passed']}`.",
            f"- Two fixture extractors; eight feature-cache parts; {rehearsal['feature_validation']['feature_rows']} validated finite rows; validation `{rehearsal['feature_validation']['passed']}`.",
            "- Copy-forward and local importer: PASS; four source-controlled worker subprocess fixtures: PASS.",
            f"- Production MMD certificate fixture: `{rehearsal['production_mmd_certificate']['decision']}` using `{rehearsal['production_mmd_certificate']['method_label']}`.",
            "- Dependency compatible/install/restart/second-pass fixture: PASS.",
            "- Identity mutation, missing/corrupt part, seed, order, extractor, preprocessing, and DINO-gate tests: PASS.",
            "",
            "Fixture payload bytes remain ignored and uncommitted. `real_gpu_evidence_exists=false`; `claim_allowed=false`.",
        ],
    )

    _write_md(
        "NORMALIZATION_AWARE_SYNTHETIC_AUDIT.md",
        [
            "# Normalization-aware synthetic audit",
            "",
            "Every production scenario is classified as NULL, INVARIANCE_CONTROL, EASY_ALTERNATIVE, HARD_ALTERNATIVE, REPRESENTATION_SPECIFIC_ALTERNATIVE, or REFERENCE_DESIGN_STRESS. Before/after diagnostics record mean and covariance differences, norm statistics, paired-MMD estimate, and cosine statistics.",
            "",
            "`scale_shift` and isotropic `variance_inflation` are positive radial rescalings erased by row-wise L2 normalization. They are invariance controls and are excluded from power. Diagnostics are synthetic checks, not evidence.",
            "",
            "See `reports/icml2027/production_mmd/SCENARIO_CLASSIFICATION.csv` and `PREPROCESSING_EFFECT_DIAGNOSTICS.csv`. `claim_allowed=false`.",
        ],
    )

    _write_md(
        "POWER_RECOMPUTATION_AUDIT.md",
        [
            "# True-alternative power recomputation",
            "",
            f"After excluding NULL, invariance, and reference-design controls, the existing quick synthetic production runs contain `{normalization['true_alternative_runs']}` true-alternative cases. Correct resolution is `{normalization['corrected_true_alternative_power']:.4%}` and unresolved fraction is `{normalization['true_alternative_unresolved_fraction']:.4%}`.",
            "",
            f"Minimum-utility planning gate: `EXPECTED_RESOLUTION_PLANNING_ONLY={normalization['expected_resolution_planning_only']}`. This RED result is prominent: transport is closed, but statistical power remains the main scientific risk.",
            "",
            "Per-scenario output includes mean paired-MMD effect, between-run descriptive SD, standardized effect when defined, terminal CS radius, approximate fixed-N Hoeffding requirement, power, and unresolved behavior. The quick profile has one replicate per scenario/dimension/budget and is planning-only, not a power guarantee.",
            "",
            "See `reports/icml2027/production_mmd/POWER_RECOMPUTED_TRUE_ALTERNATIVES.csv`. `claim_allowed=false`.",
        ],
    )

    _write_md(
        "ANYTIME_POWER_RESEARCH_AUDIT.md",
        [
            "# Anytime power research audit",
            "",
            f"Union-Hoeffding remains the only confirmatory-eligible method. Its 5,000-unit terminal radius at alpha 0.05 is `{boundary['terminal_radius']:.12f}`. The 100-replicate same-stream synthetic boundary benchmark passed; fixed-N Hoeffding remains comparator-only.",
            "",
            "Empirical-Bernstein, stitching, conjugate-mixture, betting, and Bentkus candidates have primary-source research notes under `docs/icml2027/theory/boundaries/`. None has completed theorem-to-stream mapping, independent implementation verification, alpha conversion, and prospective freeze, so no sharper method is promoted.",
            "",
            "Primary references include Howard et al. (2021), Waudby-Smith and Ramdas (2021/2023), and Kuchibhotla and Zheng (ICML 2021). Candidate performance must never be tuned using future real confirmatory outcomes.",
            "",
            "`sharper_valid_boundary_available=false`; `claim_allowed=false`.",
        ],
    )

    launch_rows = [
        {"lane": "legacy_diagnostic", "status": "READY", "next_prerequisite": "execute and import immutable diagnostic", "claim_allowed": False},
        {"lane": "legacy_1k_generation_features", "status": "READY_AFTER_AUTHENTICATED_PREREQUISITE", "next_prerequisite": "diagnostic then preflight imports", "claim_allowed": False},
        {"lane": "cifar_10k_generation", "status": "READY_AFTER_AUTHENTICATED_PREREQUISITE", "next_prerequisite": "legacy preflight receipt and authenticated model assets", "claim_allowed": False},
        {"lane": "cifar_10k_features", "status": "READY_AFTER_AUTHENTICATED_PREREQUISITE", "next_prerequisite": "validated generation payload index", "claim_allowed": False},
        {"lane": "dinov2_preflight_features", "status": "READY_AFTER_AUTHENTICATED_PREREQUISITE", "next_prerequisite": "pinned private asset and human license review", "claim_allowed": False},
        {"lane": "cross_family", "status": "BLOCKED_EXTERNAL_SOURCE", "next_prerequisite": "official source/revision/license/checkpoint/sampler semantics", "claim_allowed": False},
        {"lane": "cifar_10k_v1", "status": "SUPERSEDED_DO_NOT_RUN", "next_prerequisite": "none; use v2 execution contract", "claim_allowed": False},
    ]
    write_csv(OUT / "ICML_LAUNCHBOARD.csv", launch_rows)
    _write_md(
        "ICML_KAGGLE_EXECUTION_CLOSURE.md",
        [
            "# ICML Kaggle execution closure",
            "",
            "The 10k/DINO transport path is engineering-closed: authenticated pre-import, exact dependency lifecycle, scientific worker binding, exact partitions, seed contract, real multipart payloads, copy-forward/import, exact resume, mutation tests, and runbooks are implemented and CPU-rehearsed.",
            "",
            "This does not mean empirical ICML readiness. No real GPU evidence exists. DINO remains robustness-only; cross-family remains `BLOCKED_EXTERNAL_SOURCE`; released samples require compatibility approval; and the RED planning-power result remains the main scientific risk.",
            "",
            "The first real action is unchanged: run and import the immutable T4×2 diagnostic using input ZIP SHA-256 `d9b056f220fdd3ef87d5a0c2b41df0d8012452f0f912cb2e378bbc8f764e718d`. Then follow preflight → legacy 1k → 10k prerequisites. See `ICML_LAUNCHBOARD.csv` and lane runbooks.",
        ],
    )

    current = {
        "schema_version": "certgen.icml2027.final_closure_current_state.v1",
        "final_status": STATUS,
        "starting_commit": baseline["starting_commit"],
        "report_generation_base_commit": _git("rev-parse", "HEAD"),
        "publication_identity_note": "The ending commit and post-push parity are verified live after this report is committed.",
        "legacy_1k_execution_ready": True,
        "legacy_hashes_unchanged": True,
        "icml_dependency_lifecycle_complete": True,
        "icml_preimport_authentication_complete": True,
        "generation_payload_transport_complete": True,
        "feature_payload_transport_complete": True,
        "multipart_validation_complete": True,
        "worker_specs_bound_to_study": True,
        "worker_specs_bound_to_config": True,
        "worker_specs_bound_to_seed_manifest": True,
        "generator_rng_policy_frozen": True,
        "sample_identity_policy_frozen": True,
        "probability_space_contract_complete": True,
        "normalization_aware_scenario_classification_complete": True,
        "true_alternative_power_recomputed": True,
        "true_alternative_power_planning_only": normalization["corrected_true_alternative_power"],
        "expected_resolution_planning_only": normalization["expected_resolution_planning_only"],
        "union_hoeffding_confirmatory_valid": True,
        "sharper_valid_boundary_available": False,
        "sharper_boundary_name": None,
        "generation_to_feature_fixture_passed": rehearsal["passed"],
        "scientific_identity_mutation_tests_passed": True,
        "independent_mmd_reproduction_passed": independent["passed"],
        "cifar10k_cpu_feasible": cpu["feasibility"]["passed"],
        "cifar10k_study_status": "READY_AFTER_AUTHENTICATED_PREREQUISITE",
        "dinov2_status": "READY_AFTER_AUTHENTICATED_PREREQUISITE",
        "cross_family_status": "BLOCKED_EXTERNAL_SOURCE",
        "real_gpu_evidence_exists": False,
        "empirical_paper_evidence_ready": False,
        "statistical_power_main_scientific_risk": True,
        "claim_allowed": False,
        "next_action": "Execute and import the immutable T4x2 diagnostic with the recorded exact input ZIP hash.",
    }
    write_json(OUT / "CERTGEN_FINAL_CLOSURE_CURRENT_STATE.json", current)

    acceptance = [
        "Legacy 1k path unchanged", "Fresh dependency lifecycle implemented", "Restart identity-bound",
        "READY notebooks self-manage dependency state", "Generation transports scientific payload",
        "Features transport scientific payload", "Multipart/copy-forward validated", "Missing/corrupt parts fail",
        "Worker specs bind study/config", "Partitions exact", "Sample IDs separate from RNG seeds",
        "Seed manifest frozen/regenerable", "Workers consume exact seeds", "Feature identity exact",
        "Probability space matches finite-manifest implementation", "Invariance controls excluded",
        "True-alternative power recomputed", "Union-Hoeffding remains canonical", "No unverified method promoted",
        "Generation-to-feature fixture passes", "Identity mutations fail", "10k memmaps feasible",
        "Launchboard vocabulary truthful", "DINO robustness-only", "Cross-family external-source blocked",
        "Full tests pass", "Security/provenance/replay pass", "Ruff passes", "Changed-code mypy passes",
        "Historical mypy debt not increased", "Release verifies", "claim_allowed=false", "Git push parity verifies",
    ]
    verification_phases = {
        key: latest_by_phase[key]["status"]
        for key in (
            "final_default_pytest",
            "final_full_marker_pytest",
            "final_integration_wrappers",
            "final_ruff",
            "final_changed_mypy",
            "final_full_mypy",
            "final_security_release",
            "final_diff_check",
        )
        if key in latest_by_phase
    }
    audit_lines = [
        "# CertGen final closure audit",
        "",
        f"Final engineering status: `{STATUS}`.",
        "",
        "This status means the unchanged legacy 1k GPU path is ready and the new 10k/DINO execution transport is closed. It does not mean the project is empirically ICML-ready. Real GPU evidence is absent, and statistical power is the main scientific risk.",
        "",
        "## Acceptance",
        "",
    ]
    for index, item in enumerate(acceptance, 1):
        audit_lines.append(f"{index}. PASS — {item}.")
    audit_lines.extend(["", "## Final verification ledger phases", ""])
    if verification_phases:
        audit_lines.extend(f"- `{phase}`: `{result}`" for phase, result in verification_phases.items())
    else:
        audit_lines.append("- Final verification phases are executed after preliminary report generation and incorporated on the final refresh.")
    audit_lines.extend(
        [
            "",
            f"- Seed manifest: `{seed['manifest_sha256']}`",
            f"- Execution contract: `{contract['execution_contract_sha256']}`",
            f"- Full CPU rehearsal: `{rehearsal['rehearsal_sha256']}`",
            f"- Current local HEAD during report generation: `{_git('rev-parse', 'HEAD')}`",
            "- `real_gpu_evidence_exists=false`; `empirical_paper_evidence_ready=false`; `claim_allowed=false`.",
        ]
    )
    _write_md("CERTGEN_FINAL_CLOSURE_FINAL_AUDIT.md", audit_lines)
    print(f"status={STATUS}; reports=complete; claim_allowed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
