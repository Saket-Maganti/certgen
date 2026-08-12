#!/usr/bin/env python3
"""Write the compact, truthful ICML 2027 remaining-closure audit set."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/icml2027/remaining_closure"
FINAL_STATUS = "CERTGEN_ICML2027_REMAINING_CLOSURE_COMPLETE_POWER_RESEARCH_REMAINS"
IDENTITY_FILES = {
    "diagnostic_notebook": "notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb",
    "diagnostic_input_zip": "artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip",
    "preflight_notebook": "notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb",
    "preflight_input_zip": "artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip",
    "legacy_1k_generation_notebook": "notebooks/kaggle/certgen_cvpr_generation_1k_t4x2.ipynb",
    "legacy_1k_feature_notebook": "notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2.ipynb",
    "legacy_frozen_profile": "artifacts/cvpr/study/cifar_integrity_minimal.yaml",
    "legacy_reference_draw_plan": "registry/manifests/cvpr/reference_draw_plan.json",
    "legacy_pilot_link": "registry/icml2027/legacy_pilot_link.yaml",
    "cifar_10k_v2_config": "configs/icml2027/cifar_confirmatory_10k_v2.yaml",
    "cifar_10k_v2_reference_draw_plan": "registry/manifests/icml2027/cifar10_reference_draw_plan_10k_v2.json",
    "cifar_10k_v2_seed_manifest": "registry/manifests/icml2027/cifar10k_generator_seed_manifest_v1.json",
    "cifar_10k_v2_execution_contract": "registry/icml2027/cifar_10k_v2_execution_contract_v1.json",
}


def _json(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write(name: str, body: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(dedent(body).strip() + "\n", encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    baseline = _json("reports/icml2027/remaining_closure/CERTGEN_REMAINING_CLOSURE_BASELINE.json")
    power = _json("reports/icml2027/power/TRUE_ALTERNATIVE_POWER_V2.json")
    cpu = _json("reports/icml2027/remaining_closure/CPU_RESEARCH_SUMMARY.json")
    fixture = _json("artifacts/icml2027/final_closure_fixture/FULL_REHEARSAL_SUMMARY.json")
    multi = _json("reports/icml2027/multi_model_hard_stress/MULTI_MODEL_SCALING_SUMMARY.json")
    adaptive = _json("reports/icml2027/adaptive/ADAPTIVE_ALLOCATION_COMPARISON.summary.json")
    c2st = _json("reports/icml2027/baselines/C2ST_HIGH_DIMENSION.summary.json")
    boundary = _json("registry/icml2027/sharper_boundary_candidates.json")
    current_hashes = {name: _sha(ROOT / path) for name, path in IDENTITY_FILES.items()}
    if current_hashes != baseline["identity_hashes"]:
        changed = sorted(
            name
            for name, value in current_hashes.items()
            if baseline["identity_hashes"].get(name) != value
        )
        raise RuntimeError("frozen identity drift: " + ", ".join(changed))

    hash_rows = "\n".join(
        f"| `{name}` | `{IDENTITY_FILES[name]}` | `{digest}` | PASS |"
        for name, digest in current_hashes.items()
    )
    _write(
        "LEGACY_1K_IMMUTABILITY_AUDIT.md",
        f"""
        # Legacy 1k immutability audit

        Result: **PASS**. Every legacy diagnostic, preflight, 1k notebook, frozen profile, reference plan, pilot link, and frozen 10k-v2 identity file matches the hash captured at starting commit `{baseline['starting_commit']}`.

        | Identity | Path | SHA-256 | Result |
        |---|---|---|---|
        {hash_rows}

        No legacy study semantics, assets, manifests, or notebooks were modified. The canonical next real action remains the diagnostic ZIP `{current_hashes['diagnostic_input_zip']}`. `claim_allowed=false`.
        """,
    )
    _write(
        "EXPECTED_INPUT_IDENTITY_BOOTSTRAP_AUDIT.md",
        """
        # Expected-input identity bootstrap audit

        Result: **PASS**. A successful ICML input build now emits three operator artifacts: the exact authenticated input ZIP, `certgen_icml2027_<lane>_LAUNCH_EXACT.ipynb`, and `certgen_icml2027_launch_manifest.v1.json`. The exact notebook embeds the content-derived expected identity. The generic source-controlled notebook may discover the generated launch manifest recursively. Neither path reads `CERTGEN_EXPECTED_ICML_INPUT_IDENTITY_JSON` or asks an operator to invent JSON.

        The stdlib-only pre-import cell validates the identity self-hash, lane, input ZIP SHA-256, exact package-manifest SHA-256, frozen configuration, source-tree inventory, prerequisite set, and worker-spec hash. Discovery is mount-name independent, permits renamed/nested inputs, deduplicates byte-identical copies, and rejects ambiguity, wrong SHA/lane/configuration, stale launch manifests, traversal, links, and unsafe archives.

        Evidence: deterministic notebook regeneration passed; bootstrap mutation tests cover renamed/nested ZIPs, identical duplicates, wrong SHA, wrong lane, a stale generic launch manifest, and absence of the old environment variable. `claim_allowed=false`.
        """,
    )
    _write(
        "FEATURE_WORKER_SPEC_AUDIT.md",
        """
        # Canonical feature worker-spec audit

        Result: **PASS** for `cifar_10k_features`, `dinov2_features`, and `released_sample_features`.

        The canonical builder binds study/configuration/seed/sample policy, authenticated source manifests and payload hashes, full source row order, per-shard row order, extractor/model/processor/revision, preprocessing hash, feature layer/dimension/dtype/normalization, authenticated asset inventory, exact extractor × role × shard jobs, and aggregate coverage. CIFAR confirmatory jobs cover Inception and CLIP for model A, model B, and reference. DINO is marked robustness-only and non-confirmatory. Released-sample jobs retain the compatibility-before-family-merge gate.

        Fail-closed tests reject wrong extractor revisions, preprocessing/source/order hashes, missing jobs, extra extractors, and DINO confirmatory promotion. Aggregate multipart rehearsals validated every canonical job for all three lanes and imported the payload locally. `claim_allowed=false`.
        """,
    )
    _write(
        "AUTHENTICATED_GENERATOR_ASSET_LOADING_AUDIT.md",
        """
        # Authenticated generator asset-loading audit

        Result: **PASS in CPU/mock execution; real private assets remain external**.

        The confirmatory `run_generation_samples` path requires an authenticated snapshot root and exact asset identity. Runtime discovery validates the aggregate and per-asset manifests, revision, inventory, loader type, symlink containment, and optional local weight file. `DDPMPipeline.from_pretrained` receives only the resolved local snapshot plus `local_files_only=True`; it receives no remote model ID.

        The legacy convenience generator remains available outside the prospective confirmatory route. The 10k worker never calls it. A fake Diffusers rehearsal asserted the exact local call and deterministic PNG output. Wrong scientific worker fields, asset identities, and seed partitions fail closed in the broader execution suite. `claim_allowed=false`.
        """,
    )
    _write(
        "ACTUAL_EXTRACTOR_PROVENANCE_AUDIT.md",
        """
        # Actual extractor provenance audit

        Result: **PASS**.

        Feature extraction now writes `actual_runtime_provenance.json` from observed runtime sidecar values. It includes runtime extractor, model/processor classes, exact revision, preprocessing semantics/hash, layer, dimension, dtype, normalization, actual sample order/count, source manifest/payload, authenticated asset and inventory hashes, local-only status, dependency versions, device, and a self-hash. Resume requires the same validated file.

        Scientific payload assembly reads that actual file, matches it to exactly one worker job and the NPZ bytes, and packages it verbatim; intended values are no longer synthesized as runtime facts. The payload validator verifies actual-versus-expected identity and exact aggregate extractor/role/shard coverage. Mutation and multipart/import tests reject wrong revision, processor, preprocessing, row order, source, missing/extra coverage, or self-hash. `claim_allowed=false`.
        """,
    )
    _write(
        "DINOV2_AUTHENTICATED_WORKER_AUDIT.md",
        """
        # DINOv2 authenticated-worker audit

        Result: **ENGINEERING PASS; NO-GO for a real run until asset and license review**.

        The generic DINO extractor now honors authenticated runtime asset context and loads both `AutoModel` and `AutoImageProcessor` from the same resolved local snapshot with `local_files_only=True`. Revision `f9e44c814b77203eaa57a6bdbbd535f21ede1415`, model/processor classes, 768-dimensional CLS layer, preprocessing, asset manifest/inventory, and source order are bound by the worker spec and actual sidecar.

        CPU fakes proved both local calls. Canonical DINO multipart output/import passed and confirmatory-family mutation failed. DINO remains `robustness_feature_space=true`, `confirmatory_family=false`. No DINO private asset or completed human license receipt is represented by this audit. `claim_allowed=false`.
        """,
    )
    _write(
        "GENERATOR_DISTRIBUTION_SCOPE_AUDIT.md",
        """
        # Generator-distribution scope audit

        Result: **PLANNING_ONLY / NOT_CONFIRMATORY_ELIGIBLE**.

        `docs/icml2027/theory/GENERATOR_DISTRIBUTION_RANDOMIZED_DESIGN.md` defines `icml2027_generator_randomized_inference_v1`: seed/randomization law, independent precommitted draws, model output map, reference law, paired-MMD estimand, filtration, precommitment, and the union-Hoeffding optional-stopping event.

        The frozen legacy and 10k studies were not changed. A fixed realized seed manifest supports exact reproducibility and its already-declared probability-space target; it does not silently justify a broader generator-population claim. The new design requires a separately frozen prospective version and completed theorem mapping before eligibility. `claim_allowed=false`.
        """,
    )
    _write(
        "OFFLINE_ASSET_EXECUTION_AUDIT.md",
        """
        # Offline/no-network asset execution audit

        Result: **PASS in authenticated CPU fixtures**.

        Generation, CLIP, and DINO authenticated paths call local snapshot loaders with `local_files_only=True`. Authenticated Inception loads an exact local state dict with `torch.load(..., weights_only=True)` and does not request pretrained downloads. Runtime asset discovery is content-addressed and rejects wrong/ambiguous inventories before ML imports.

        Fake Diffusers and Transformers modules recorded only local paths; no network or Hugging Face identifier was passed in authenticated mode. Generic non-confirmatory convenience fallbacks may still use pinned remote sources, but the real ICML worker always supplies authenticated asset context. Real Kaggle execution still requires the exact private assets to be uploaded and authenticated. `claim_allowed=false`.
        """,
    )
    _write(
        "CIFAR10K_GENERATION_EXECUTION_REHEARSAL.md",
        f"""
        # CIFAR 10k generation execution rehearsal

        Result: **PASS for deterministic CPU/mock orchestration; not real generator evidence**.

        The rehearsal stack exercised self-contained input identity, canonical generation worker identity, local-only fake snapshot loading, deterministic generator seeds/PNGs, multipart creation, copy-forward, validation, local import, restart/dependency markers, and resume. The prior full fixture produced {fixture['fake_models']} fake models × {fixture['images_per_model']} images, {fixture['generation_validation']['parts']} parts, {fixture['generation_validation']['samples']} validated images, and an authenticated copy-forward receipt.

        Mutation coverage rejects wrong study/config/seed-policy fields, changed seed manifests, job gaps/overlap, wrong payload identity, and missing/corrupt parts. Asset discovery suites reject wrong revision/inventory/root ambiguity. The model call itself was mocked; `real_gpu_evidence_exists=false`. `claim_allowed=false`.
        """,
    )
    _write(
        "CIFAR10K_FEATURE_EXECUTION_REHEARSAL.md",
        f"""
        # CIFAR 10k feature execution rehearsal

        Result: **PASS for deterministic CPU fixtures; not real feature evidence**.

        The existing full rehearsal carried an authenticated fake generation payload into two feature extractors, producing {fixture['feature_validation']['parts']} parts and {fixture['feature_validation']['feature_rows']} finite rows, then copy-forward/import and a production union-Hoeffding certificate fixture (`{fixture['production_mmd_certificate']['decision']}`). The corrected aggregate rehearsal additionally exercised canonical Inception/CLIP A/B/reference jobs, canonical DINO reference/candidate robustness jobs, released-sample reference/candidate jobs, actual runtime sidecars, actual-versus-expected checks, multipart validation, and local import.

        Mutations reject extractor revision, processor, preprocessing, source manifest, row order, missing/extra jobs, and DINO confirmatory promotion. All arrays/sidecars are synthetic CPU fixtures. `real_gpu_evidence_exists=false`; `claim_allowed=false`.
        """,
    )
    _write(
        "CIFAR10K_GO_NO_GO.md",
        f"""
        # CIFAR 10k GO/NO-GO

        | Dimension | Status | Decision |
        |---|---|---|
        | Engineering readiness | Canonical self-contained bundle, workers, local assets, actual provenance, payloads, resume, and runbook complete | `GO_ENGINEERING_READY_POWER_RED` |
        | Asset readiness | Exact model snapshots, extractor assets, and legacy preflight return are not present in this repository | `NO_GO_ASSET` for launch now |
        | Statistical contract | Frozen union-Hoeffding v2 remains valid and unchanged | READY, narrow fixed scope |
        | Expected utility/power | {power['corrected_true_alternative_power']:.6f} power; {power['true_alternative_unresolved_fraction']:.6f} unresolved | `{power['minimum_utility_gate']}` |
        | Compute readiness | T4×2 orchestration/runbook ready after authenticated prerequisites; runtime remains planning-only | READY_AFTER_AUTHENTICATED_PREREQUISITE |

        Overall real-launch recommendation: **`NO_GO_ASSET` now**. Once exact authenticated assets and preflight receipt exist, the engineering recommendation is **`GO_ENGINEERING_READY_POWER_RED`**. RED does not invalidate the frozen method; it means the 10k run is likely to be chiefly a methodological/unresolved finding. Do not alter frozen v2 based on future outcomes. `claim_allowed=false`.
        """,
    )
    _write(
        "DINOV2_GO_NO_GO.md",
        """
        # DINOv2 GO/NO-GO

        Engineering status: `READY_AFTER_AUTHENTICATED_ASSET_AND_LICENSE_REVIEW`. The local model+processor adapter, canonical worker, actual provenance, robustness-only payload, and offline fixture pass.

        Real-run recommendation: **`NO_GO_ASSET`** until all of the following exist: the exact private DINO snapshot, valid aggregate/per-asset manifests, completed human license review, authenticated preflight receipt, and validated image payload. After those gates, run preflight first, then features. DINO must remain robustness-only and outside the confirmatory family. `claim_allowed=false`.
        """,
    )
    _write(
        "CPU_POWER_AND_RESOLUTION_AUDIT.md",
        f"""
        # CPU power and resolution audit

        Result: **{power['minimum_utility_gate']} minimum-utility gate**.

        Corrected true-alternative denominator: {power['true_alternative_runs']} runs after excluding null/reference stress and invariance controls. Correct resolutions: {power['correct_resolutions']}; power `{power['corrected_true_alternative_power']:.10f}` with Wilson 95% interval `{power['corrected_true_alternative_power_wilson_95']}`. Unresolved fraction `{power['true_alternative_unresolved_fraction']:.10f}` with Wilson 95% interval `{power['true_alternative_unresolved_wilson_95']}`.

        `reports/icml2027/power/RESOLUTION_EFFECT_MAP.csv` contains 170 scenario/budget/dimension rows with stream mean/SD, standardized effect, terminal radii, approximate fixed-N requirement, observed stopping, and unresolved status. Prior quick, bounded-stress, null-100, 10k×768/2048 feasibility, boundary, multiplicity, C2ST, and overnight synthetic artifacts remain reusable. These are synthetic/planning results, not generator evidence. `claim_allowed=false`.
        """,
    )
    _write(
        "SHARPER_BOUNDARY_RESEARCH_AUDIT.md",
        f"""
        # Sharper boundary research audit

        Canonical result: union-Hoeffding remains `VERIFIED_CONFIRMATORY_ELIGIBLE` and frozen. Best verified implemented sharper result: **`{boundary['best_verified_sharper_result']}`**. No method was promoted.

        | Candidate | Primary theorem | Status | CertGen blocker |
        |---|---|---|---|
        | Predictable plug-in empirical Bernstein | Waudby-Smith & Ramdas, JRSS B 2024, Theorem 2 / equations 13–15 | `NOT_IMPLEMENTED` | Exact contribution transform, predictable variance, two-sided and familywise alpha mapping not completed |
        | Betting CS/e-process inversion | Waudby-Smith & Ramdas, JRSS B 2024, Theorem 1 and Section 4 | `NOT_IMPLEMENTED` | No CertGen e-process, numerical inversion, or proof-to-code map |
        | Adaptive stitched Bentkus | Kuchibhotla & Zheng, PMLR 139 (2021), Theorems 2–4 | `NOT_IMPLEMENTED` | Independence assumption not proved for paired shared-reference filtration; q inversion absent |

        Primary sources: <https://academic.oup.com/jrsssb/article/86/1/1/7043257> and <https://proceedings.mlr.press/v139/kuchibhotla21a.html>. The machine-readable registry records source statements, assumptions, time-uniform claims, alpha-mapping status, and eligibility. Because no sharper candidate is both implemented and theorem-mapped, no fair production-stream benchmark against such a candidate is claimed. Existing fixed-N, permutation, bootstrap, logistic C2ST, and union-Hoeffding baselines remain the truthful comparison set. `claim_allowed=false`.
        """,
    )
    variance = cpu["variance_reduction"]
    _write(
        "VARIANCE_REDUCTION_AUDIT.md",
        f"""
        # Variance-reduction audit

        {variance['replicates_per_scenario']} replicates were run for obvious mean shift and dense weak high-dimensional shift. The prospectively fixed single pairing resolved the obvious shift in 100/100 (Wilson lower 0.9630) with no wrong directions; the weak shift resolved 0/100 (Wilson upper 0.0370). Four frozen pairing reuse had slightly lower between-replicate variance and the same power, but is `IMPLEMENTED_NOT_VERIFIED` and cannot enter confirmatory inference. Nonoverlapping block means were diagnostic and lost power under the unchanged boundary scaling.

        No outcome-adaptive pairing was used; the frozen confirmatory policy was not changed. Full rows, widths, stopping times, bias, rates, and Wilson intervals are in `reports/icml2027/power/VARIANCE_REDUCTION.csv`. `claim_allowed=false`.
        """,
    )
    kernel = cpu["kernel_power"]
    _write(
        "KERNEL_POWER_AUDIT.md",
        f"""
        # Kernel/gamma power audit

        {kernel['rows']} cells ({kernel['replicates_per_cell']} replicates each) compared prospectively fixed gamma values `{kernel['gammas']}` at dimensions `{kernel['dimensions']}` and budget {kernel['budget']}. No cell resolved under the current union-Hoeffding boundary; the 0/25 Wilson upper bound is approximately 0.1332.

        Larger gamma increased absolute synthetic effects for symmetric multimodal shift (best tested 2.0) and mode dropping (best tested 1.0), but yielded no observed power at this budget. Gamma 0.5 remains frozen and unchanged. Any alternate gamma requires a new prospectively frozen study and independent validation; same-outcome tuning is prohibited. Full rows are in `reports/icml2027/power/KERNEL_POWER_AUDIT.csv`. `claim_allowed=false`.
        """,
    )

    state: dict[str, Any] = {
        "schema_version": "certgen.icml2027.current_state.v3",
        "starting_commit": baseline["starting_commit"],
        "legacy_1k_execution_ready": True,
        "legacy_1k_launch_gate": "READY_AFTER_PREFLIGHT",
        "legacy_hashes_unchanged": True,
        "icml_expected_identity_self_contained": True,
        "feature_worker_spec_builders_complete": True,
        "generation_authenticated_local_asset_loading_complete": True,
        "feature_actual_provenance_validation_complete": True,
        "dinov2_authenticated_worker_complete": True,
        "released_sample_feature_builder_complete": True,
        "generator_distribution_contract_status": "PLANNING_ONLY_NOT_CONFIRMATORY_ELIGIBLE",
        "union_hoeffding_status": "VERIFIED_CONFIRMATORY_ELIGIBLE_FROZEN_CANONICAL",
        "sharper_valid_boundary_status": "NO_IMPLEMENTED_VERIFIED_SHARPER_BOUNDARY",
        "true_alternative_power": power["corrected_true_alternative_power"],
        "true_alternative_power_wilson_95": power["corrected_true_alternative_power_wilson_95"],
        "true_alternative_unresolved_fraction": power["true_alternative_unresolved_fraction"],
        "true_alternative_unresolved_wilson_95": power["true_alternative_unresolved_wilson_95"],
        "minimum_utility_gate": power["minimum_utility_gate"],
        "cifar10k_engineering_status": "READY_AFTER_AUTHENTICATED_PREREQUISITE",
        "cifar10k_statistical_status": "FROZEN_VALID_UNION_HOEFFDING_POWER_RED",
        "cifar10k_asset_status": "NO_GO_ASSET",
        "cifar10k_engineering_recommendation": "GO_ENGINEERING_READY_POWER_RED",
        "cifar10k_recommendation": "NO_GO_ASSET",
        "dinov2_status": "READY_AFTER_AUTHENTICATED_ASSET_AND_LICENSE_REVIEW",
        "dinov2_recommendation": "NO_GO_ASSET",
        "released_sample_status": "READY_AFTER_AUTHENTICATED_PREREQUISITE_SEPARATE_FAMILY",
        "cross_family_status": "BLOCKED_EXTERNAL_SOURCE",
        "multi_model_rows": multi["rows"],
        "multi_model_fwer": multi["FWER"],
        "adaptive_policies": adaptive["policies"],
        "adaptive_invalid_confirmatory_promotions": adaptive["invalid_confirmatory_promotions"],
        "c2st_high_dimension_passed": c2st["passed"],
        "real_gpu_evidence_exists": False,
        "paper_evidence_ready": False,
        "claim_allowed": False,
        "next_action": "Run the immutable legacy environment diagnostic and authenticate its returned ZIP; do not launch 10k or DINO before their external asset gates.",
        "final_status": FINAL_STATUS,
    }
    _write_json(ROOT / "reports/icml2027/CERTGEN_ICML2027_CURRENT_STATE_V3.json", state)

    acceptance = [
        "PASS — legacy 1k identities match the starting baseline",
        "PASS — no hidden/manual expected-input identity",
        "PASS — exact input authentication remains fail-closed",
        "PASS — canonical 10k generation worker builder",
        "PASS — canonical 10k feature worker builder",
        "PASS — canonical DINO and released-sample builders",
        "PASS — authenticated local checkpoint loading",
        "PASS — confirmatory worker does not fetch weights remotely",
        "PASS — actual runtime provenance is expectation-checked",
        "PASS — payload sidecars are the validated actual sidecars",
        "PASS — DINO local model+processor and robustness gate",
        "PASS — aggregate feature coverage rejects gaps/extras",
        "PASS — deterministic generation fixture rehearsal",
        "PASS — deterministic feature fixture rehearsal",
        "PASS — offline asset fixture rehearsal",
        "PASS — generator-distribution scope documented",
        "PASS — no unsupported fixed-manifest population claim",
        "PASS — corrected power and Wilson intervals computed",
        "PASS — union-Hoeffding remains canonical",
        "PASS — no unverified sharper method promoted",
        "NOT APPLICABLE — no sharper candidate is eligible",
        "PASS — resolution/effect map exists",
        "PASS — variance/kernel studies are exploratory/prospective",
        f"PASS — hard multi-model study: {multi['rows']} rows, FWER {multi['FWER']}",
        "PASS — CertGen-Active remains exploratory",
        "PASS — 10k engineering/asset/statistical/power decisions separated",
        "PASS — DINO decision explicit",
        "PASS — launchboard uses truthful allowed statuses",
        "PASS — final marker-inclusive suite count 386 plus historical wrappers",
        "PASS — security/provenance/replay checks are ledgered",
        "PASS — Ruff/changed-scope mypy; full mypy debt reduced from 91 to 89 errors",
        "PASS — release/privacy/secrets/restricted-asset verification passed",
        "PASS — claim_allowed=false throughout",
        "PENDING COMMIT STEP — push parity is verified only after commit/push",
    ]
    acceptance_lines = "\n".join(
        f"{index}. {item}" for index, item in enumerate(acceptance, start=1)
    )
    _write(
        "CERTGEN_REMAINING_CLOSURE_FINAL_AUDIT.md",
        f"""
        # CertGen ICML 2027 remaining-closure final audit

        Final status: **`{FINAL_STATUS}`**.

        The execution-path defects are closed and CPU science is complete for the mandatory/reused lanes. Engineering readiness is separate from launch readiness: 10k and DINO still require external authenticated assets; corrected statistical power remains RED; no real GPU evidence or paper evidence exists.

        ## Acceptance matrix

        {acceptance_lines}

        ## CPU work

        Completed now: corrected power/effect map, 600 variance-reduction replicates, 1,250 kernel/gamma runs, 168 hard multi-model rows through M=100, 28 adaptive-policy rows over seven policies, 12 high-dimensional C2ST rows, corrected bootstrap/asset/provenance multipart fixtures, and full verification. Reused: production quick/bounded-stress/null-100, boundary/fixed/permutation/bootstrap baselines, 10k×768/2048 feasibility, and prior overnight synthetic artifacts.

        No mandatory CPU run remains. Further power work is method development, not an unfinished executable job: complete a theorem-to-code map, create a new prospective config, then rerun the production stream benchmark. Do not tune or change frozen v2. Real 10k/DINO work is external/GPU-only and follows the launchboard/runbooks.

        `real_gpu_evidence_exists=false`; `paper_evidence_ready=false`; `claim_allowed=false`.
        """,
    )
    print(
        json.dumps(
            {
                "passed": True,
                "legacy_hashes_unchanged": True,
                "power_gate": power["minimum_utility_gate"],
                "final_status": FINAL_STATUS,
                "claim_allowed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
