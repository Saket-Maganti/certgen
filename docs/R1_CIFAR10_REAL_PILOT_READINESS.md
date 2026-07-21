# CERTGEN_R1_CIFAR10_REAL_PILOT Readiness

`NO_REAL_EVIDENCE`

Status: `BLOCKED_MISSING_REFERENCE_SAMPLES`
Claim allowed: `False`

## Summary

- Selected benchmark: `cifar10`
- Selected candidate model pairs: `5`
- Source status: `not_verified`
- License status: `not_verified`
- Sample availability: `not_verified`
- Feature-cache status: `missing_or_unvalidated`
- Metric reproduction status: `missing_or_not_within_tolerance`
- Kaggle feature extraction needed: `True`
- Kaggle feature extraction ready: `False`
- Estimated Kaggle runtime if needed: planning estimate only: Inception 50k CIFAR images ~10-40 min; CLIP ~20-90 min; DINOv2 ~30-120 min on T4x2
- Updated R1B blocker taxonomy: `BLOCKED_MISSING_REFERENCE_SAMPLES`, `BLOCKED_GENERATION_NOT_RUN`, `BLOCKED_GENERATION_INCOMPLETE`, `BLOCKED_GENERATION_MANIFEST_INVALID`, `READY_FOR_KAGGLE_FEATURE_EXTRACTION`

## Blockers
- manifest: line 1: local sample path missing: data/sources/cifar10_r1/reference/cifar10_test_000000.png
- manifest: line 2: local sample path missing: data/sources/cifar10_r1/reference/cifar10_test_000001.png
- manifest: line 3: local sample path missing: data/sources/cifar10_r1/google_ddpm_cifar10_32/seed_000000.png
- manifest: line 4: local sample path missing: data/sources/cifar10_r1/google_ddpm_cifar10_32/seed_000001.png
- manifest: line 5: local sample path missing: data/sources/cifar10_r1/frank_cfm_cifar10_32/seed_000000.png
- manifest: line 6: local sample path missing: data/sources/cifar10_r1/frank_cfm_cifar10_32/seed_000001.png
- features: feature cache missing for reference_inception: reference_inception.npz and/or reference_inception.sidecar.json
- features: feature cache missing for model_a_inception: model_a_inception.npz and/or model_a_inception.sidecar.json
- features: feature cache missing for model_b_inception: model_b_inception.npz and/or model_b_inception.sidecar.json
- features: feature cache missing for reference_clip: reference_clip.npz and/or reference_clip.sidecar.json
- features: feature cache missing for model_a_clip: model_a_clip.npz and/or model_a_clip.sidecar.json
- features: feature cache missing for model_b_clip: model_b_clip.npz and/or model_b_clip.sidecar.json
- metric reproduction audit exists but within_tolerance is not true

## Selected Candidate Model Pairs

| pair_id | role | model_a | model_b | status |
|---|---|---|---|---|
| `cifar10_null_split_reference_vs_reference` | `null_calibration_pair` | `cifar10_test_split_a` | `cifar10_test_split_b` | `blocked_missing_local_reference_samples` |
| `cifar10_reference_vs_corruption_sanity` | `obvious_gap_sanity_pair` | `cifar10_reference_samples` | `deterministic_corruption_of_same_reference_samples` | `blocked_missing_local_reference_samples` |
| `google_ddpm_vs_frank_cfm` | `medium_gap_pair` | `google/ddpm-cifar10-32` | `FrankCCCCC/cfm-cifar10-32` | `blocked_missing_generated_samples` |
| `google_ddpm_vs_frank_ddpm_ema` | `close_gap_pair` | `google/ddpm-cifar10-32` | `FrankCCCCC/ddpm_ema_cifar10` | `blocked_missing_generated_samples` |
| `google_ddpm_preprocessing_sensitivity` | `preprocessing_sensitivity_pair` | `google/ddpm-cifar10-32_primary_preprocessing` | `google/ddpm-cifar10-32_alternate_locked_preprocessing` | `blocked_until_primary_samples_exist` |

## Candidate Role Table

| candidate_id | role | status | purpose |
|---|---|---|---|
| `cifar10_null_split_reference_vs_reference` | `null_calibration_pair` | `selected_blocked_missing_local_reference_samples` | same-source CIFAR-10 split-vs-split calibration |
| `cifar10_reference_vs_corruption_sanity` | `obvious_gap_sanity_pair` | `selected_blocked_missing_local_reference_samples` | reference samples versus clearly corrupted/noise replacement samples for software sanity only |
| `google_ddpm_vs_frank_cfm` | `medium_gap_pair` | `selected_blocked_missing_generated_samples` | Apache-2.0 DDPM checkpoint versus Apache-2.0 CIFAR flow-matching checkpoint after generated samples exist |
| `google_ddpm_vs_frank_ddpm_ema` | `close_gap_pair` | `selected_blocked_missing_generated_samples` | two Apache-2.0 DDPM-style CIFAR-10 checkpoints after generated samples exist |
| `google_ddpm_preprocessing_sensitivity` | `preprocessing_sensitivity_pair` | `selected_blocked_until_primary_samples_exist` | same generated samples under the primary preprocessing lock and a later explicitly locked variant |

## Replacement-Candidate Table

| candidate_id | status | reason |
|---|---|---|
| `minimal_diffusion_cifar10_released_50k` | `blocked_until_asset_license_and_google_drive_artifact_are_verified` | README advertises released CIFAR-10 synthetic images but the downloadable artifact was not locally verified in R1. |
| `openai_improved_diffusion_cifar10` | `blocked_until_checkpoint_or_released_samples_are_verified` | MIT code is public but R1 did not verify a concrete CIFAR-10 generated-sample artifact. |
| `nvlabs_edm_cifar10` | `blocked_license_noncommercial` | Repository license is CC BY-NC-SA 4.0 and is not selected for the public/free R1 source lock. |

## R1B Sample Materialization

| item | value |
|---|---|
| `reference_rows` | `2` |
| `generated_rows` | `4` |
| `missing_reference_paths` | `2` |
| `missing_generated_paths` | `4` |
| `generation_blockers` | `4` |

## Generation Adapter Status

| checkpoint_id | adapter_status | pipeline_class |
|---|---|---|
| `google/ddpm-cifar10-32` | `ready_guarded_diffusers_ddpm_pipeline` | `DDPMPipeline` |
| `FrankCCCCC/ddpm_ema_cifar10` | `ready_guarded_diffusers_ddpm_pipeline` | `DDPMPipeline` |
| `FrankCCCCC/cfm-cifar10-32` | `ready_guarded_diffusers_ddpm_pipeline_per_model_card` | `DDPMPipeline` |

## Kaggle Feature Extraction Command

`not_ready: source package is not feature-extraction-ready`

## CPU Commands After Feature Caches Are Available
- `commands/r0_cpu/01_validate_provenance.sh`
- `commands/r0_cpu/02_validate_feature_caches.sh`
- `commands/r0_cpu/03_reproduce_metric_from_features.sh`
- `commands/r0_cpu/04_run_clean_core_certificates_cpu.sh`
- `commands/r0_cpu/06_generate_pilot_report_cpu.sh`

## Exact Next Command

`python3 -m certgen.cli.run_cifar10_real_pilot --provenance-ledger registry/provenance/cifar10_r1_ledger.csv --sample-manifest registry/manifests/cifar10_r1_samples.jsonl --preprocessing-lock configs/preprocessing_locks/cifar10_inception_bilinear_299.json --feature-cache-dir data/features/cifar10_r1 --metric-reproduction-audit data/results/cifar10_r1_metric_reproduction.json --out-json data/results/r1_cifar10_status.json --report docs/R1_CIFAR10_REAL_PILOT_READINESS.md`
