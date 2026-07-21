# R1A Sample Materialization Audit

`NO_REAL_EVIDENCE`

Audit status: `passed`
Checks passed: `12/12`
Claim allowed: `False`

| Check | Status | Detail |
|---|---:|---|
| `r1a_policy_doc_exists` | `pass` | docs/R1A_CIFAR10_SAMPLE_MATERIALIZATION_POLICY.md |
| `cifar10_reference_materialization_doc_exists` | `pass` | docs/CIFAR10_REFERENCE_MATERIALIZATION_R1A.md |
| `reference_manifest_builder_exists` | `pass` | python -m certgen.data.build_cifar10_reference_manifest |
| `kaggle_generation_runbook_exists` | `pass` | docs/KAGGLE_T4X2_CIFAR10_GENERATION_R1A.md |
| `generation_adapter_exists_or_blocked_status_documented` | `pass` | {'google/ddpm-cifar10-32': {'adapter_status': 'ready_guarded_diffusers_ddpm_pipeline', 'pipeline_class': 'DDPMPipeline', 'expected_resolution': '32x32_rgb'}, 'FrankCCCCC/ddpm_ema_cifar10': {'adapter_status': 'ready_guarded_diffusers_ddpm_pipeline', 'pipeline_class': 'DDPMPipeline', 'expected_resolution': '32x32_rgb'}, 'FrankCCCCC/cfm-cifar10-32': {'adapter_status': 'ready_guarded_diffusers_ddpm_pipeline_per_model_card', 'pipeline_class': 'DDPMPipeline', 'expected_resolution': '32x32_rgb', 'note': 'Flow-matching checkpoint uses DDPMPipeline per model card; execute mode remains a real-run validation gate.'}} |
| `manifest_merge_tool_exists` | `pass` | python -m certgen.generation.merge_sample_manifests |
| `runtime_estimates_exist_and_are_planning_only` | `pass` | docs/R1A_CIFAR10_GENERATION_RUNTIME_ESTIMATES.md |
| `r1_readiness_report_has_updated_blocker_taxonomy` | `pass` | BLOCKED_MISSING_REFERENCE_SAMPLES |
| `no_claim_allowed_true` | `pass` | no claim_allowed=true JSON artifacts |
| `no_fake_empirical_results` | `pass` | planning-only language present |
| `no_certificate_run_performed_for_r1a` | `pass` | no R1A certificate artifacts |
| `no_feature_extraction_claimed_if_samples_missing` | `pass` | {'samples_missing': True, 'kaggle_feature_extraction_ready': False} |

## R1 Status

- Status code: `BLOCKED_MISSING_REFERENCE_SAMPLES`
- Kaggle generation ready: `True`
- Kaggle feature extraction ready: `False`
- No certificate run was performed.
