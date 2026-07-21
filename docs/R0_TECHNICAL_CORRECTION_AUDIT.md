# CERTGEN_R0 Technical Correction Report

`NO_REAL_EVIDENCE`

Audit status: `passed`
Checks passed: `9/9`
Claim allowed: `False`
Promote to paper evidence: `False`

| Check | Status | Detail |
|---|---:|---|
| `no_claim_allowed_true_artifacts` | `pass` | none |
| `no_rigorous_fid_certificate_claim` | `pass` | none |
| `polynomial_kid_not_certified_by_default` | `pass` | polynomial KID/CMMD/MMD is descriptive-only and blocked from rigorous certificate mode by default |
| `bounded_rbf_mmd_certificate_path_exists` | `pass` | {'kernel_name': 'rbf', 'feature_normalization': 'l2', 'kernel_lower': 0.0, 'kernel_upper': 1.0, 'mmd_contribution_lower': -2.0, 'mmd_contribution_upper': 2.0, 'delta_lower': -4.0, 'delta_upper': 4.0, 'bounded_by_construction': True} |
| `bounded_cmmd_clip_mmd_path_exists` | `pass` | {'kernel_name': 'rbf', 'feature_normalization': 'l2', 'kernel_lower': 0.0, 'kernel_upper': 1.0, 'mmd_contribution_lower': -2.0, 'mmd_contribution_upper': 2.0, 'delta_lower': -4.0, 'delta_upper': 4.0, 'bounded_by_construction': True} |
| `betting_cs_path_exists` | `pass` | betting_mixture_bounded_mean_r0 |
| `lightweight_e_bh_design_scaffold_exists` | `pass` | {'policy': 'e_bh_design_scaffold', 'alpha': 0.05, 'num_hypotheses': 4, 'inputs_required': ['valid e-values from bounded-stream e-processes'], 'implemented_for_claims': False, 'claim_allowed': False} |
| `first_real_pilot_ready_or_blocked_with_exact_reason` | `pass` | ['manifest: line 1: local sample path missing: data/sources/cifar10_r1/reference/cifar10_test_000000.png', 'manifest: line 2: local sample path missing: data/sources/cifar10_r1/reference/cifar10_test_000001.png', 'manifest: line 3: local sample path missing: data/sources/cifar10_r1/google_ddpm_cifar10_32/seed_000000.png', 'manifest: line 4: local sample path missing: data/sources/cifar10_r1/google_ddpm_cifar10_32/seed_000001.png', 'manifest: line 5: local sample path missing: data/sources/cifar10_r1/frank_cfm_cifar10_32/seed_000000.png', 'manifest: line 6: local sample path missing: data/sources/cifar10_r1/frank_cfm_cifar10_32/seed_000001.png', 'features: feature cache missing for reference_inception: reference_inception.npz and/or reference_inception.sidecar.json', 'features: feature cache missing for model_a_inception: model_a_inception.npz and/or model_a_inception.sidecar.json', 'features: feature cache missing for model_b_inception: model_b_inception.npz and/or model_b_inception.sidecar.json', 'features: feature cache missing for reference_clip: reference_clip.npz and/or reference_clip.sidecar.json', 'features: feature cache missing for model_a_clip: model_a_clip.npz and/or model_a_clip.sidecar.json', 'features: feature cache missing for model_b_clip: model_b_clip.npz and/or model_b_clip.sidecar.json', 'metric reproduction audit missing: data/results/cifar10_r1_metric_reproduction.json'] |
| `updated_r0_command_index_written` | `pass` | docs/R0_COMMAND_INDEX.md |

## R1 CIFAR-10 Status

Status: `blocked`
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
- metric reproduction audit missing: data/results/cifar10_r1_metric_reproduction.json

## Exact Next Command

`python3 -m certgen.cli.run_cifar10_real_pilot --provenance-ledger registry/provenance/cifar10_r1_ledger.csv --sample-manifest registry/manifests/cifar10_r1_samples.jsonl --preprocessing-lock configs/preprocessing_locks/cifar10_inception_bilinear_299.json --feature-cache-dir data/features/cifar10_r1 --metric-reproduction-audit data/results/cifar10_r1_metric_reproduction.json --out-json data/results/r1_cifar10_status.json --report docs/R1_CIFAR10_REAL_PILOT_READINESS.md`
