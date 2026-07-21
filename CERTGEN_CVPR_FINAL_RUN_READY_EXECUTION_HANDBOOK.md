# CertGen CVPR Final Run-Ready Execution Handbook

> **Superseded by `CERTGEN_CVPR_RUN_READY_EXECUTION_HANDBOOK.md`.** Retained for historical compatibility.

`claim_allowed=false` throughout; real artifacts require separate evidence and paper approval.

## 1. Place CIFAR archive

Command: `mkdir -p data/sources && install -m 0444 /path/to/cifar-10-python.tar.gz data/sources/cifar-10-python.tar.gz`. Location: local repository. CPU_or_GPU: CPU. Network policy: none. Input: user-provided official archive. Output: read-only local archive. Runtime class: seconds. Resume: only when destination is absent. Failure recovery: correct the source path; never overwrite silently. Evidence class: prerequisite. Claim permission: false. Completion test: destination exists.

## 2. Validate reference

Command: `python3 -m certgen validate reference --source data/sources/cifar-10-python.tar.gz --explain`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: step-1 archive. Output: validation JSON/report. Runtime class: seconds. Resume: read-only rerun. Failure recovery: replace an invalid archive; never bypass validation. Evidence class: provenance validation. Claim permission: false. Completion test: `materialization_can_proceed=true`.

## 3. Materialize reference

Command: `python3 -m certgen materialize reference --source data/sources/cifar-10-python.tar.gz --out-manifest registry/manifests/cvpr/cifar10_reference.jsonl --out-summary data/results/cvpr_reference_materialization.json`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: validated archive. Output: images, manifest, summary. Runtime class: local minutes. Resume: hash-bound complete output only. Failure recovery: preserve diagnostics and remove only an identified partial target. Evidence class: reference provenance. Claim permission: false. Completion test: summary passes and every image decodes/hashes.

## 4. Select profile

Command: `python3 -m certgen profiles show cifar_integrity_minimal`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: canonical profile. Output: membership and profile hash. Runtime class: seconds. Resume: read-only. Failure recovery: membership changes require a new prospective version. Evidence class: design contract. Claim permission: false. Completion test: two DDPMs, Inception, CLIP, 1k counts, and hash are shown.

## 5. Freeze study

Command: `python3 -m certgen freeze study --profile cifar_integrity_minimal --out artifacts/cvpr/study/cifar_integrity_minimal.yaml`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: profile and registries. Output: frozen study/hash. Runtime class: seconds. Resume: immutable; do not overwrite. Failure recovery: repair prospective inputs before results and use a new version/path. Evidence class: preregistration. Claim permission: false. Completion test: `STUDY_FROZEN` and validator pass.

## 6. Prepare preflight package

Command: `python3 -m certgen prepare preflight --profile cifar_integrity_minimal --out-dir artifacts/cvpr/preflight`. Location: local. CPU_or_GPU: CPU. Network policy: none during build. Input: selected profile/registries. Output: frozen config and deterministic ZIP. Runtime class: seconds. Resume: new directory on conflict. Failure recovery: resolve blockers only on selected rows. Evidence class: preflight input. Claim permission: false. Completion test: `PREFLIGHT_PACKAGE_READY`.

## 7. Validate preflight input

Command: `python3 -m certgen validate kaggle-input artifacts/cvpr/preflight/certgen_cvpr_preflight_input.zip`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: preflight ZIP. Output: integrity verdict. Runtime class: seconds. Resume: read-only. Failure recovery: rebuild step 6. Evidence class: package validation. Claim permission: false. Completion test: `passed=true`.

## 8. Run Kaggle preflight

Command: upload step-7 ZIP and run `notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb`. Location: Kaggle T4x2. CPU_or_GPU: two GPUs, one subprocess worker per GPU. Network policy: dependencies and model assets allowed only here. Input: validated ZIP. Output: assets/hashes, smoke outputs, observed contracts, measured calibration, output ZIP. Runtime class: hardware-dependent preflight. Resume: identical hashes only. Failure recovery: use emitted worker rerun commands and preserve completed workers. Evidence class: non-evidence preflight. Claim permission: false. Completion test: root and every selected row pass.

## 9. Validate preflight output

Command: `python3 -m certgen validate kaggle-output <preflight-output.zip> --kind preflight`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: copied ZIP. Output: schema/integrity verdict. Runtime class: seconds. Resume: read-only. Failure recovery: rerun failed workers in step 8. Evidence class: output validation. Claim permission: false. Completion test: `passed=true`.

## 10. Import preflight

Command: `python3 -m certgen import preflight <preflight-output.zip> --out-dir data/imported/cvpr-preflight-1k --out-json data/results/cvpr/preflight_import_status.json --out-report reports/cvpr_preflight_import.md`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: validated ZIP. Output: immutable secure import and raw hash copy. Runtime class: seconds. Resume: new path on conflict. Failure recovery: repair upstream output; do not force replacement. Evidence class: run log. Claim permission: false. Completion test: import `passed=true`.

## 11. Ingest measured calibration

Command: `python3 -m certgen runtime-plan ingest-preflight <preflight-runtime-report.json> --config configs/cvpr/runtime_plan_template.yaml --out artifacts/cvpr/runtime/runtime_plan.json`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: measured preflight report. Output: labeled runtime plan. Runtime class: seconds. Resume: immutable. Failure recovery: correct malformed/nonfinite fields; do not relabel estimates. Evidence class: execution metadata. Claim permission: false. Completion test: `PLANNING_ESTIMATE`, `MEASURED_PREFLIGHT`, and `DERIVED_FROM_MEASURED_PREFLIGHT` are distinguished.

## 12. Prepare generation package

Command: `python3 -m certgen prepare generation --scale 1k --study artifacts/cvpr/study/cifar_integrity_minimal.yaml --preflight-config artifacts/cvpr/preflight/preflight_config.yaml --preflight-import data/results/cvpr/preflight_import_status.json --reference-manifest registry/manifests/cvpr/cifar10_reference.jsonl --out-dir artifacts/cvpr/generation`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: study, reference, preflight import. Output: offline caches, seeds/config, ZIP. Runtime class: packaging seconds/minutes. Resume: immutable. Failure recovery: resolve receipt/hash mismatch; no checkpoint downloads. Evidence class: run input. Claim permission: false. Completion test: ready status and study hash.

## 13. Validate generation input

Command: `python3 -m certgen validate kaggle-input artifacts/cvpr/generation/certgen_cvpr_generation_1k_input.zip`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: generation ZIP. Output: integrity verdict. Runtime class: seconds. Resume: read-only. Failure recovery: rebuild step 12. Evidence class: package validation. Claim permission: false. Completion test: `passed=true`, no nested archive/private path.

## 14. Run 1k generation

Command: upload step-13 ZIP and run `notebooks/kaggle/certgen_cvpr_cifar10_generation_t4x2_1k.ipynb`. Location: Kaggle T4x2. CPU_or_GPU: two GPUs. Network policy: dependency policy only; model-asset network forbidden. Input: exact snapshots/seeds/study hash. Output: 1k images/model and canonical manifests. Runtime class: measured-plan dependent. Resume: identical identities, incomplete shards only. Failure recovery: adaptive OOM fallback and emitted rerun commands. Evidence class: pilot artifact. Claim permission: false. Completion test: complete status, exact counts, all images decode/hash.

## 15. Validate and import generation

Command: `python3 -m certgen validate kaggle-output <generation-output.zip> --kind generation && python3 -m certgen import generation <generation-output.zip> --out-dir data/imported/cvpr-generation-1k --out-json data/results/cvpr/generation_import_status.json --out-report reports/cvpr_generation_import.md`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: copied output. Output: secure import. Runtime class: seconds/minutes. Resume: new path on conflict. Failure recovery: rerun only failed shards. Evidence class: pilot artifact. Claim permission: false. Completion test: import passes and manifests/counts match.

## 16. Prepare embedded-image feature package

Command: `python3 -m certgen prepare features --input-mode EMBED_IMAGES_IN_PACKAGE --generation-import data/results/cvpr/generation_import_status.json --preflight-import data/results/cvpr/preflight_import_status.json --reference-manifest registry/manifests/cvpr/cifar10_reference.jsonl --reference-draw-plan registry/manifests/cvpr/reference_draw_plan.json --out-dir artifacts/cvpr/features`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: reference draw, generation import, extractor assets/contracts, study hash. Output: embedded images/manifests/shards/config/ZIP. Runtime class: local minutes. Resume: immutable. Failure recovery: repair missing/hash-invalid source only. Evidence class: feature input. Claim permission: false. Completion test: ready status and every embedded image opens/hashes.

## 17. Validate feature input

Command: `python3 -m certgen validate kaggle-input artifacts/cvpr/features/certgen_cvpr_features_input.zip`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: feature ZIP. Output: package/image verdict. Runtime class: seconds/minutes. Resume: read-only. Failure recovery: rebuild step 16, never patch paths. Evidence class: package validation. Claim permission: false. Completion test: every manifest path resolves inside ZIP.

## 18. Run feature extraction

Command: upload step-17 ZIP and run `notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_1k.ipynb`. Location: Kaggle T4x2. CPU_or_GPU: two GPUs. Network policy: dependencies only; asset network forbidden. Input: embedded images and exact local extractor assets. Output: feature shards/sidecars. Runtime class: measured-plan dependent. Resume: identical hashes, incomplete shards only. Failure recovery: calibrated fallback and worker reruns. Evidence class: pilot artifact. Claim permission: false. Completion test: all images validate before GPU allocation and root completes.

## 19. Validate and import features

Command: `python3 -m certgen validate kaggle-output <feature-output.zip> --kind feature && python3 -m certgen import feature <feature-output.zip> --out-dir data/imported/cvpr-feature-1k --out-json data/results/cvpr/feature_import_status.json --out-report reports/cvpr_feature_import.md`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: feature output ZIP. Output: secure import. Runtime class: seconds/minutes. Resume: new path on conflict. Failure recovery: rerun missing/failed shards. Evidence class: pilot artifact. Claim permission: false. Completion test: schema, integrity, workers, arrays, sidecars pass.

## 20. Merge features

Command: `python3 -m certgen merge features --run data/imported/cvpr-feature-1k --output-root data/features/cvpr`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: imported shards. Output: cache-v2 groups/manifest. Runtime class: local minutes. Resume: immutable destination. Failure recovery: partial merge is quarantined; repair import and use a new run. Evidence class: pilot cache. Claim permission: false. Completion test: `FEATURE_CACHE_V2_MERGE_COMPLETE`.

## 21. Validate cache-v2

Command: `python3 -m certgen validate caches --features <group>/features.npz --sidecar <group>/sidecar.json --artifact-root <merged-root>` for every group. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: merged groups. Output: validation verdicts. Runtime class: seconds/minutes. Resume: read-only. Failure recovery: return to merge/origin shard. Evidence class: validated pilot cache. Claim permission: false. Completion test: every group passes exact output/image lineage.

## 22. Metric reproduction

Command: `python3 -m certgen sanity metric-reproduction --config <frozen-metric-config.yaml> --out data/results/cvpr/metric_reproduction.json`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: validated caches and frozen convention. Output: reproduction gate. Runtime class: local minutes. Resume: immutable. Failure recovery: stop and audit preprocessing, identities, kernel, implementation. Evidence class: scientific gate. Claim permission: false. Completion test: `PASS`.

## 23. Sanity gates

Command: `python3 -m certgen sanity controls --config <frozen-sanity-config.yaml> --out data/results/cvpr/sanity_controls.json`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: registered controls. Output: control gate. Runtime class: local minutes. Resume: immutable. Failure recovery: stop and interpret; no substitution. Evidence class: scientific gate. Claim permission: false. Completion test: all required controls pass.

## 24. Freeze family

Command: `python3 -m certgen prepare family --study artifacts/cvpr/study/cifar_integrity_minimal.yaml --out-dir artifacts/cvpr/family`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: study and prospective comparison registry after gates. Output: Bonferroni family ledger. Runtime class: seconds. Resume: immutable. Failure recovery: repair prospective linkage only; outcome-dependent changes require a new study. Evidence class: multiplicity contract. Claim permission: false. Completion test: family is hash-valid and study-bound.

## 25. Issue certificates

Command: `python3 -m certgen certify --study artifacts/cvpr/study/cifar_integrity_minimal.yaml --family artifacts/cvpr/family/family.json --features <feature-bundle.npz> --reference-draw-plan registry/manifests/cvpr/reference_draw_plan.json --comparison <comparison-id> --feature-space <feature-space> --out <certificate.json>`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: frozen study/family/draw and validated features. Output: bounded RBF-MMD certificate. Runtime class: local minutes. Resume: deterministic identical-stream replay only. Failure recovery: stop on lineage/assumption mismatch. Evidence class: pilot certificate. Claim permission: false. Completion test: hash, alpha ledger, and decision validate.

## 26. Build partial ranking

Command: `python3 -m certgen rank --family artifacts/cvpr/family/family.json --certificate-dir <certificate-dir> --out-dir artifacts/cvpr/ranking --aggregation-rule unanimous_direction_or_unresolved`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: compatible certificates. Output: direct/transitive/unresolved/invalid/disagreement graph. Runtime class: seconds. Resume: immutable. Failure recovery: correct missing/incompatible inputs; never force a total order. Evidence class: pilot analysis. Claim permission: false. Completion test: ranking hash passes and all edges are registered.

## 27. Cross-feature analysis

Command: `python3 -m certgen analyze cross-feature --certificate-dir <certificate-dir> --out artifacts/cvpr/cross_feature`. Location: local. CPU_or_GPU: CPU. Network policy: none. Input: completed selected-feature certificates. Output: five prospective agreement/disagreement artifacts. Runtime class: seconds. Resume: immutable. Failure recovery: fix duplicate/incompatible identities; disagreements remain feature-specific. Evidence class: pilot analysis. Claim permission: false. Completion test: matrix, disagreements, one-unresolved, consensus, and feature-specific files exist.

## 28. Stop and interpret

Command: `python3 -m certgen readiness`, then review gates, certificates, ranking, cross-feature, limitations, and compute accounting. Location: local/research review. CPU_or_GPU: CPU. Network policy: none. Input: all immutable prior artifacts. Output: stop/scale/new-study decision. Runtime class: human review. Resume: continue without artifact mutation. Failure recovery: stop on any blocked gate; patch only observed real-execution defects. Evidence class: interpretation decision. Claim permission: false until separate approval. Completion test: decision/limitations recorded without post hoc membership changes.

## Stop-building rule

Further patches are justified only by an observed real model/extractor load failure, Kaggle dependency failure, OOM, snapshot incompatibility, output import failure, feature-path failure, cache-v2 failure, metric-reproduction failure, or evidence-gate defect.
