# R0 CPU/GPU Audit

`NO_REAL_EVIDENCE`

Audit status: `passed`
Checks passed: `15/15`
Claim allowed: `False`

| Check | Status | Detail |
|---|---:|---|
| `cpu_gpu_execution_policy_doc_exists` | `pass` | docs/R0_CPU_GPU_EXECUTION_POLICY.md |
| `cpu_command_bundle_exists` | `pass` | all required commands present |
| `cpu_commands_disable_cuda` | `pass` | all CPU commands disable CUDA |
| `kaggle_feature_extraction_runbook_exists` | `pass` | docs/KAGGLE_T4X2_FEATURE_EXTRACTION_RUNBOOK_R0.md |
| `feature_runbook_uses_t4x2_sharding` | `pass` | two-process sharding documented |
| `kaggle_parallel_seed_generation_runbook_exists` | `pass` | docs/KAGGLE_T4X2_PARALLEL_SEED_GENERATION_RUNBOOK_R0.md |
| `generation_runbook_prefers_released_samples` | `pass` | preference and placeholder documented |
| `runtime_estimates_doc_exists_and_labeled` | `pass` | docs/R0_RUNTIME_ESTIMATES_CPU_AND_KAGGLE_T4X2.md |
| `cpu_first_config_validates` | `pass` | cpu-first config valid |
| `no_real_evidence_claims_promoted` | `pass` | no claim_allowed=true JSON artifacts |
| `no_rigorous_fid_certificate_claim_exists` | `pass` | no rigorous FID certificate claims |
| `polynomial_kid_rigorous_certificate_disabled` | `pass` | polynomial KID/CMMD/MMD is descriptive-only and blocked from rigorous certificate mode by default |
| `bounded_rbf_cmmd_certificate_path_available` | `pass` | bounded RBF-MMD and CMMD streams available |
| `tests_are_external_verification_command_documented` | `pass` | pytest command documented externally |
| `r1_cifar10_ready_or_blocked_with_reason` | `pass` | {'status_code': 'BLOCKED_MISSING_REAL_SOURCES', 'blockers': ['provenance ledger missing: registry/provenance/cifar10_r1_ledger.csv', 'manifest: sample manifest missing: registry/manifests/cifar10_r1_samples.jsonl', 'features: feature cache missing for reference_inception: reference_inception.npz and/or reference_inception.sidecar.json', 'features: feature cache missing for model_a_inception: model_a_inception.npz and/or model_a_inception.sidecar.json', 'features: feature cache missing for model_b_inception: model_b_inception.npz and/or model_b_inception.sidecar.json', 'features: feature cache missing for reference_clip: reference_clip.npz and/or reference_clip.sidecar.json', 'features: feature cache missing for model_a_clip: model_a_clip.npz and/or model_a_clip.sidecar.json', 'features: feature cache missing for model_b_clip: model_b_clip.npz and/or model_b_clip.sidecar.json', 'metric reproduction audit missing: data/results/cifar10_r1_metric_reproduction.json']} |

## R1 CIFAR-10 Status

- Status code: `BLOCKED_MISSING_REAL_SOURCES`
- provenance ledger missing: registry/provenance/cifar10_r1_ledger.csv
- manifest: sample manifest missing: registry/manifests/cifar10_r1_samples.jsonl
- features: feature cache missing for reference_inception: reference_inception.npz and/or reference_inception.sidecar.json
- features: feature cache missing for model_a_inception: model_a_inception.npz and/or model_a_inception.sidecar.json
- features: feature cache missing for model_b_inception: model_b_inception.npz and/or model_b_inception.sidecar.json
- features: feature cache missing for reference_clip: reference_clip.npz and/or reference_clip.sidecar.json
- features: feature cache missing for model_a_clip: model_a_clip.npz and/or model_a_clip.sidecar.json
- features: feature cache missing for model_b_clip: model_b_clip.npz and/or model_b_clip.sidecar.json
- metric reproduction audit missing: data/results/cifar10_r1_metric_reproduction.json
