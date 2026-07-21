# CertGen CVPR Run-Ready Execution Handbook

This is the authoritative real-execution closure handbook. Current status: `CVPR_RUN_READY_BLOCKED_BY_REFERENCE_INPUT`. A local `cifar-10-python.tar.gz` candidate exists but has not been validated. Every stage remains `claim_allowed=false` until separately approved paper evidence exists.

## 1. Supply or identify the official CIFAR-10 archive

- stage: 1; purpose: provide the user-authorized official reference source; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: official CIFAR-10 Python archive; current candidate: `cifar-10-python.tar.gz` (170,498,071 bytes, unvalidated); output package: the preserved source archive; prepare command: none while the candidate exists; notebook: N/A; copy-back: N/A; validation command: stage 2; import command: N/A.
- planning runtime: user-dependent only if replacement is required; measured runtime field: N/A; disk: archive plus 1 GiB margin; RAM: negligible; VRAM: 0; resume: preserve source bytes; failure recovery: if stage 2 rejects the candidate, replace it with the official archive and rerun the same command.
- evidence class: unvalidated_user_input_candidate; claim permission: false; completion status: candidate present, validation required; next action: stage 2.

## 2. Validate reference

- stage: 2; purpose: validate source layout without downloading; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: `cifar-10-python.tar.gz`; output package: `data/results/v9_cifar_reference_onramp.json`; prepare command: N/A; notebook: N/A; copy-back: N/A; validation command: `python3 -m certgen validate reference --source cifar-10-python.tar.gz --explain`; import command: N/A.
- planning runtime: seconds; measured runtime field: command ledger duration; disk: under 1 GiB temporary; RAM: under 1 GiB; VRAM: 0; resume: rerun is read-only/idempotent; failure recovery: replace only the invalid source.
- evidence class: input_validation; claim permission: false; completion status: `READY_FOR_LOCAL_CIFAR_REFERENCE_MATERIALIZATION`; next action: stage 3.

## 3. Materialize reference

- stage: 3; purpose: produce the immutable 10,000-row reference manifest/images; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: validated source from stage 2; output package: `registry/manifests/cvpr/cifar10_reference.jsonl`; prepare command: use the exact materialization command emitted by stage 2 (expected source `cifar-10-python.tar.gz`); notebook: N/A; copy-back: N/A; validation command: `python3 -m certgen status`; import command: N/A.
- planning runtime: seconds to minutes; measured runtime field: materialization status JSON; disk: about 1 GiB with margin; RAM: under 2 GiB; VRAM: 0; resume: refuse conflicting immutable output; failure recovery: quarantine partial output and rerun from original source.
- evidence class: reference_artifact_not_result; claim permission: false; completion status: exactly 10,000 unique hashed rows; next action: stage 4.

## 4. Prepare preflight package

- stage: 4; purpose: freeze models, extractors, capabilities, policies, worker configs, and identity; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: no access by builder.
- input package: materialized reference plus registries and human license approvals; output package: `artifacts/cvpr/preflight/certgen_cvpr_preflight_input.zip`; prepare command: `python3 -m certgen prepare preflight --license-approvals configs/cvpr/license_approvals.json`; notebook: preflight T4x2; copy-back: N/A; validation command: stage 5; import command: N/A.
- planning runtime: seconds; measured runtime field: input manifest; disk: package size plus 2 GiB; RAM: under 2 GiB; VRAM: 0; resume: use a new output directory if frozen bytes differ; failure recovery: resolve only reported license/revision/preprocessing blockers.
- evidence class: planning_only; claim permission: false; completion status: `PREFLIGHT_PACKAGE_READY`; next action: stage 5.

## 5. Validate preflight input

- stage: 5; purpose: emulate Kaggle input discovery/integrity; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: preflight input ZIP; output package: JSON validation on stdout; prepare command: N/A; notebook: N/A; copy-back: N/A; validation command: `python3 -m certgen validate kaggle-input artifacts/cvpr/preflight/certgen_cvpr_preflight_input.zip`; import command: N/A.
- planning runtime: seconds; measured runtime field: command ledger; disk: negligible; RAM: under 1 GiB; VRAM: 0; resume: freely repeat; failure recovery: rebuild package from the same frozen inputs.
- evidence class: package_validation; claim permission: false; completion status: `passed=true`; next action: stage 6.

## 6. Run real T4x2 preflight

- stage: 6; purpose: load real models/extractors, smoke them, and calibrate; location: Kaggle; CPU_or_GPU: GPU; GPU_count: 2 T4, one active worker each; network policy: frozen split policy, normally online dependencies and assets for first preflight.
- input package: validated preflight ZIP; output package: `/kaggle/working/certgen_cvpr_preflight_<run_id>.zip`; prepare command: stage 4; notebook: `notebooks/kaggle/certgen_cvpr_checkpoint_preflight_t4x2.ipynb`; copy-back: copy ZIP unchanged and preserve SHA-256; validation command: stage 7; import command: stage 8.
- planning runtime: 5–30 minutes, model dependent; measured runtime field: per-model/extractor throughput and memory JSON; disk: package + caches + 8 GiB margin; RAM: Kaggle allocation; VRAM: measured per worker; resume: strict completion markers only; failure recovery: rerun emitted failed subset, never completed workers.
- evidence class: non_evidence_preflight/run_log_only; claim permission: false; completion status: model and extractor results all pass; next action: stage 7.

## 7. Validate preflight output

- stage: 7; purpose: reject bad output before import; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: copied preflight ZIP; output package: validation JSON; prepare command: N/A; notebook: N/A; copy-back: already complete; validation command: `python3 -m certgen validate kaggle-output <preflight-zip> --kind preflight`; import command: stage 8.
- planning runtime: seconds to minutes; measured runtime field: command ledger; disk: ZIP only; RAM: under 2 GiB; VRAM: 0; resume: repeat read-only; failure recovery: use exact Kaggle rerun subset if schema/integrity indicates incomplete workers.
- evidence class: output_validation; claim permission: false; completion status: schema, workers, CRC, integrity and safety pass; next action: stage 8.

## 8. Import preflight

- stage: 8; purpose: preserve raw ZIP and safely extract validated run logs/caches; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: validated preflight ZIP; output package: `data/imported/<preflight-run>` plus status JSON; prepare command: N/A; notebook: N/A; copy-back: source ZIP retained read-only; validation command: artifact registry audit; import command: `python3 -m certgen import preflight <preflight-zip> --out-json data/results/cvpr/preflight_import_status.json`.
- planning runtime: seconds to minutes; measured runtime field: import timestamp; disk: ZIP + extracted cache; RAM: under 2 GiB; VRAM: 0; resume: immutable hash-addressed raw store; failure recovery: never overwrite, choose a new run-specific directory.
- evidence class: run_log_only; claim permission: false; completion status: `passed=true`; next action: stage 9.

## 9. Ingest runtime calibration

- stage: 9; purpose: convert real throughput/memory into a session plan; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: imported preflight reports; output package: `artifacts/cvpr/generation/runtime_plan.json`; prepare command: `python3 -m certgen plan-runtime --config artifacts/cvpr/preflight/preflight_config.yaml --ingest-preflight <preflight-report> --out artifacts/cvpr/generation/runtime_plan.json`; notebook: N/A; copy-back: N/A; validation command: inspect runtime plan; import command: N/A.
- planning runtime: seconds; measured runtime field: ingested report fields; disk: negligible; RAM: under 1 GiB; VRAM: 0; resume: regenerate from immutable reports; failure recovery: block if measurement identity differs.
- evidence class: resource_plan; claim permission: false; completion status: every selected runtime has calibration; next action: stage 10.

## 10. Prepare generation package

- stage: 10; purpose: freeze adapters, caches, seed shards, and 1k run identity; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: no access by builder.
- input package: real preflight import, complete reference, scale 1k; output package: `artifacts/cvpr/generation/certgen_cvpr_generation_1k_input.zip`; prepare command: `python3 -m certgen prepare generation --scale 1k`; notebook: generation T4x2 1k; copy-back: N/A; validation command: stage 11; import command: N/A.
- planning runtime: seconds to minutes; measured runtime field: package manifest; disk: model caches + package + margin; RAM: under 4 GiB; VRAM: 0; resume: immutable new package path; failure recovery: repair only missing imported preflight/cache identity.
- evidence class: planning_only; claim permission: false; completion status: `GENERATION_PACKAGE_READY`; next action: stage 11.

## 11. Validate generation input

- stage: 11; purpose: pre-upload integrity/network/cache check; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: generation input ZIP; output package: validation JSON; prepare command: N/A; notebook: N/A; copy-back: N/A; validation command: `python3 -m certgen validate kaggle-input artifacts/cvpr/generation/certgen_cvpr_generation_1k_input.zip`; import command: N/A.
- planning runtime: seconds to minutes; measured runtime field: command ledger; disk: ZIP only; RAM: under 2 GiB; VRAM: 0; resume: repeat read-only; failure recovery: rebuild from same imported preflight.
- evidence class: package_validation; claim permission: false; completion status: `passed=true`; next action: stage 12.

## 12. Run 1k generation

- stage: 12; purpose: generate deterministic batched pilot images; location: Kaggle; CPU_or_GPU: GPU; GPU_count: 2 T4, one active worker each; network policy: online dependencies, offline model assets.
- input package: validated generation ZIP; output package: `/kaggle/working/certgen_cvpr_generation_<run_id>.zip`; prepare command: stage 10; notebook: `notebooks/kaggle/certgen_cvpr_cifar10_generation_t4x2_1k.ipynb`; copy-back: copy unchanged with SHA-256; validation command: stage 13; import command: stage 14.
- planning runtime: derived from stage 9; measured runtime field: worker batch/throughput/memory status; disk: images + cache + 8 GiB margin; RAM: Kaggle allocation; VRAM: calibrated safe batch; resume: strict shard markers and idempotent ZIP; failure recovery: OOM microbatch fallback or emitted rerun subset.
- evidence class: pilot_artifact/run_log_only; claim permission: false; completion status: every expected shard complete; next action: stage 13.

## 13. Validate generation output

- stage: 13; purpose: enforce shared output schema and completeness; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: copied generation ZIP; output package: validation JSON; prepare command: N/A; notebook: N/A; copy-back: already complete; validation command: `python3 -m certgen validate kaggle-output <generation-zip> --kind generation`; import command: stage 14.
- planning runtime: seconds to minutes; measured runtime field: command ledger; disk: ZIP only; RAM: under 2 GiB; VRAM: 0; resume: repeat read-only; failure recovery: rerun only missing/failed shard or rebuild ZIP from valid shards.
- evidence class: output_validation; claim permission: false; completion status: schema/integrity/worker completeness pass; next action: stage 14.

## 14. Import generation

- stage: 14; purpose: preserve and extract real generated artifacts safely; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: validated generation ZIP; output package: `data/imported/<generation-run>`; prepare command: N/A; notebook: N/A; copy-back: raw ZIP retained read-only; validation command: artifact registry audit; import command: `python3 -m certgen import generation <generation-zip> --out-json data/results/cvpr/generation_import_status.json`.
- planning runtime: seconds to minutes; measured runtime field: import record; disk: ZIP + extracted images; RAM: under 2 GiB; VRAM: 0; resume: hash-addressed immutable store; failure recovery: never force overwrite.
- evidence class: pilot_artifact; claim permission: false; completion status: `passed=true`; next action: stage 15.

## 15. Prepare feature package

- stage: 15; purpose: freeze roles, shards, extractors, preprocessing, assets, and draw plan; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: no access by builder.
- input package: generation/preflight imports and materialized reference; output package: `artifacts/cvpr/features/certgen_cvpr_features_input.zip`; prepare command: `python3 -m certgen prepare features`; notebook: feature T4x2 1k; copy-back: N/A; validation command: stage 16; import command: N/A.
- planning runtime: seconds to minutes; measured runtime field: feature input manifest; disk: images + extractor caches + margin; RAM: under 4 GiB; VRAM: 0; resume: new immutable package path; failure recovery: repair only missing import/preflight/draw-plan input.
- evidence class: planning_only; claim permission: false; completion status: `FEATURE_PACKAGE_READY`; next action: stage 16.

## 16. Validate feature input

- stage: 16; purpose: verify role coverage, shard uniqueness, cache and schema; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: feature input ZIP; output package: validation JSON; prepare command: N/A; notebook: N/A; copy-back: N/A; validation command: `python3 -m certgen validate kaggle-input artifacts/cvpr/features/certgen_cvpr_features_input.zip`; import command: N/A.
- planning runtime: seconds to minutes; measured runtime field: command ledger; disk: ZIP only; RAM: under 2 GiB; VRAM: 0; resume: repeat read-only; failure recovery: rebuild from frozen role manifest.
- evidence class: package_validation; claim permission: false; completion status: `passed=true`; next action: stage 17.

## 17. Run feature extraction

- stage: 17; purpose: produce deterministic extractor/role shards; location: Kaggle; CPU_or_GPU: GPU; GPU_count: 2 T4, one active worker each; network policy: online dependencies, offline extractor assets.
- input package: validated feature ZIP; output package: `/kaggle/working/certgen_cvpr_features_<run_id>.zip`; prepare command: stage 15; notebook: `notebooks/kaggle/certgen_cvpr_feature_extraction_t4x2_1k.ipynb`; copy-back: copy unchanged with SHA-256; validation command: stage 18; import command: stage 19.
- planning runtime: derived from extractor preflight; measured runtime field: shard worker/memory status; disk: feature shards + 8 GiB margin; RAM: Kaggle allocation; VRAM: calibrated safe batch; resume: strict marker validation; failure recovery: rerun exact extractor/role shard subset.
- evidence class: pilot_artifact/run_log_only; claim permission: false; completion status: every expected feature shard complete; next action: stage 18.

## 18. Validate feature output

- stage: 18; purpose: enforce feature output schema before import; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: copied feature ZIP; output package: validation JSON; prepare command: N/A; notebook: N/A; copy-back: already complete; validation command: `python3 -m certgen validate kaggle-output <feature-zip> --kind feature`; import command: stage 19.
- planning runtime: seconds to minutes; measured runtime field: command ledger; disk: ZIP only; RAM: under 2 GiB; VRAM: 0; resume: repeat read-only; failure recovery: rerun only missing/failed shard or rebuild ZIP.
- evidence class: output_validation; claim permission: false; completion status: schema/integrity/worker completeness pass; next action: stage 19.

## 19. Import features

- stage: 19; purpose: preserve and safely extract feature shards; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: validated feature ZIP; output package: `data/imported/<feature-run>`; prepare command: N/A; notebook: N/A; copy-back: raw ZIP retained read-only; validation command: artifact registry audit; import command: `python3 -m certgen import features <feature-zip> --out-json data/results/cvpr/feature_import_status.json`.
- planning runtime: seconds to minutes; measured runtime field: import record; disk: ZIP + extracted shards; RAM: under 2 GiB; VRAM: 0; resume: hash-addressed immutable store; failure recovery: never force overwrite.
- evidence class: pilot_artifact; claim permission: false; completion status: `passed=true`; next action: stage 20.

## 20. Merge features

- stage: 20; purpose: merge imported shards into role-preserving cache-v2; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: imported feature run; output package: `data/features/cvpr/<run_id>/`; prepare command: `python3 -m certgen merge features --run <run_id>`; notebook: N/A; copy-back: N/A; validation command: stage 21; import command: N/A.
- planning runtime: seconds to minutes; measured runtime field: merge manifest/status; disk: merged arrays plus temporary copy; RAM: feature matrix dependent; VRAM: 0; resume: completed destination is immutable; failure recovery: failed partial destination is quarantined, then rerun.
- evidence class: pilot_artifact; claim permission: false; completion status: `FEATURE_CACHE_V2_MERGE_COMPLETE`; next action: stage 21.

## 21. Validate cache-v2

- stage: 21; purpose: validate every merged array and sidecar identity; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: each merged `features.npz` and `sidecar.json`; output package: cache validation status; prepare command: N/A; notebook: N/A; copy-back: N/A; validation command: `python3 -m certgen validate caches --features <features.npz> --sidecar <sidecar.json> --artifact-root data/features/cvpr/<run_id>`; import command: N/A.
- planning runtime: seconds to minutes; measured runtime field: validation JSON; disk: no additional material; RAM: one cache matrix; VRAM: 0; resume: repeat read-only; failure recovery: identify and rerun only the bad source shard, then merge to a new run.
- evidence class: artifact_validation; claim permission: false; completion status: all cache-v2 validations pass; next action: stage 22.

## 22. Metric reproduction

- stage: 22; purpose: validate exact bounded-RBF implementation identity; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: immutable validated caches and frozen metric config; output package: `data/results/cvpr/metric_reproduction.json`; prepare command: freeze real cache paths/hashes in config; notebook: N/A; copy-back: N/A; validation command: `python3 -m certgen sanity metric-reproduction --config configs/cvpr/frozen_metric_reproduction.yaml --out data/results/cvpr/metric_reproduction.json`; import command: N/A.
- planning runtime: seconds to minutes; measured runtime field: gate output; disk: negligible; RAM: cache dependent; VRAM: 0; resume: immutable result path; failure recovery: repair only the mismatched implementation/config identity.
- evidence class: sanity_artifact; claim permission: false; completion status: `PASS`; next action: stage 23.

## 23. Sanity gates

- stage: 23; purpose: run preregistered null, gap, direction, and identity controls; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: validated caches and frozen sanity config; output package: `data/results/cvpr/sanity_controls.json`; prepare command: freeze real inputs; notebook: N/A; copy-back: N/A; validation command: `python3 -m certgen sanity controls --config configs/cvpr/frozen_sanity.yaml --out data/results/cvpr/sanity_controls.json`; import command: N/A.
- planning runtime: seconds to minutes; measured runtime field: gate output; disk: negligible; RAM: cache dependent; VRAM: 0; resume: immutable result path; failure recovery: stop and diagnose failed control, never waive it.
- evidence class: sanity_artifact; claim permission: false; completion status: `PASS`; next action: stage 24.

## 24. Freeze family

- stage: 24; purpose: freeze the prospective full hypothesis family and Bonferroni allocation; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: registered prospective comparisons and validated feature availability; output package: `artifacts/cvpr/family/family.json`; prepare command: `python3 -m certgen prepare family`; notebook: N/A; copy-back: N/A; validation command: `python3 -m certgen audit registries`; import command: N/A.
- planning runtime: seconds; measured runtime field: family configuration hash; disk: negligible; RAM: under 1 GiB; VRAM: 0; resume: frozen output is immutable; failure recovery: fix registry status or missing cache, never admit post hoc rows.
- evidence class: preregistration_artifact; claim permission: false; completion status: nonempty full cartesian family frozen; next action: stage 25.

## 25. Run first certificate

- stage: 25; purpose: execute the first family-bound bounded-RBF certificate; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: study, family, validated bundle, draw plan, fingerprint; output package: first certificate JSON; prepare command: N/A; notebook: N/A; copy-back: N/A; validation command: certificate contract audit; import command: N/A; command: `python3 -m certgen certify --study configs/cvpr/frozen_study.yaml --family artifacts/cvpr/family/family.json --features <bundle.npz> --reference-draw-plan <draw-plan.json> --comparison <comparison_id> --feature-space <feature_space> --out data/results/cvpr/certificates/first.json`.
- planning runtime: seconds to minutes; measured runtime field: certificate; disk: negligible; RAM: feature dependent; VRAM: 0; resume: immutable output; failure recovery: stop on fingerprint/family mismatch.
- evidence class: pilot_certificate_not_paper_evidence; claim permission: false; completion status: valid decided or undecided certificate; next action: stage 26.

## 26. Build partial ranking

- stage: 26; purpose: aggregate only valid family-bound certificates without forcing a total order; location: local; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: frozen family and certificate directory; output package: `data/results/cvpr/partial_ranking/`; prepare command: N/A; notebook: N/A; copy-back: N/A; validation command: `python3 -m certgen audit cvpr`; import command: N/A; command: `python3 -m certgen rank --family artifacts/cvpr/family/family.json --certificate-dir data/results/cvpr/certificates --out-dir data/results/cvpr/partial_ranking`.
- planning runtime: seconds; measured runtime field: ranking status; disk: negligible; RAM: under 1 GiB; VRAM: 0; resume: deterministic rebuild to new output; failure recovery: remove invalid certificates, never force edges.
- evidence class: pilot_ranking_not_paper_evidence; claim permission: false; completion status: partial ranking contract passes; next action: stage 27.

## 27. Stop and interpret

- stage: 27; purpose: inspect the pilot honestly before any new work; location: local/human review; CPU_or_GPU: CPU; GPU_count: 0; network policy: none.
- input package: validated certificates, partial ranking, limitations; output package: interpretation decision, not an automated paper claim; prepare command: N/A; notebook: N/A; copy-back: N/A; validation command: `python3 -m certgen audit cvpr`; import command: N/A.
- planning runtime: human-dependent; measured runtime field: review record; disk: negligible; RAM: negligible; VRAM: 0; resume: retain all immutable artifacts; failure recovery: patch only a real observed execution/gate defect.
- evidence class: human_interpretation_required; claim permission: false by default; completion status: stop-building rule observed; next action: none until interpretation authorizes a scientifically bounded continuation.

## Stop-building rule

Do not add more pre-run architecture. Only patch a failure observed during real model/extractor loading, Kaggle environment setup, adapter application, OOM fallback, asset loading, output import, feature merge, metric reproduction, or evidence gating.
