# V6 CPU and Kaggle Master Execution Runbook

> **LEGACY_COMPATIBILITY_ONLY — NOT CANONICAL GUIDANCE.** Use `CERTGEN_CVPR_FINAL_RUN_READY_EXECUTION_HANDBOOK.md`.

`NO_FAKE_RESULTS`
`NO_REAL_EVIDENCE until gates pass`
`not paper evidence`
`claim_allowed=false`

This is the execution bridge for the first real CIFAR-10 pilot. Do not create V7. Do not run certificates until R1D passes.

## 1. Local CPU Setup

```bash
commands/v6_cpu_execution/00_check_local_prereqs.sh
```

## 2. CIFAR Reference Materialization

Use one source.

```bash
CIFAR_ROOT=/path/to/local/cifar10 \
  commands/v6_cpu_execution/01_materialize_reference_from_local_root.sh
```

or:

```bash
CIFAR_ARCHIVE_ROOT=/path/to/archive \
  commands/v6_cpu_execution/01b_materialize_reference_from_official_archive.sh
```

Validate:

```bash
commands/v6_cpu_execution/02_validate_reference_manifest.sh
```

## 3. Generation Input ZIP

```bash
commands/v6_cpu_execution/03_create_kaggle_generation_input_zip.sh
```

Upload `data/kaggle_inputs/certgen_cifar10_generation_1k_input.zip` to Kaggle as `certgen-generation`.

## 4. Kaggle Generation Notebook

Run `notebooks/kaggle/certgen_cifar10_generation_t4x2_1k.ipynb` on T4 x2.

Download:

```text
/kaggle/working/certgen_cifar10_generated_1k_outputs.zip
```

Place:

```text
data/kaggle_outputs/certgen_cifar10_generated_1k_outputs.zip
```

## 5. Local Generation Output Validation

```bash
commands/v6_cpu_execution/04_validate_copied_back_generation_outputs.sh
```

## 6. Feature Input ZIP

```bash
commands/v6_cpu_execution/05_build_feature_extraction_sample_package.sh
commands/v6_cpu_execution/06_create_kaggle_feature_extraction_input_zip.sh
```

Upload `data/kaggle_inputs/certgen_cifar10_feature_extraction_1k_input.zip` to Kaggle as `certgen-features`.

If the ZIP is too large, use the split policy documented in `data/results/v6_feature_input_zip_manifest.json`: `reference.zip`, `generated_google_ddpm.zip`, `generated_frank_ddpm_ema.zip`, `generated_frank_cfm.zip`, and `configs_and_manifests.zip`.

## 7. Kaggle Feature Extraction Notebook

Run `notebooks/kaggle/certgen_cifar10_feature_extraction_t4x2_1k.ipynb` on T4 x2.

Download:

```text
/kaggle/working/certgen_cifar10_features_1k_outputs.zip
```

Place:

```text
data/kaggle_outputs/certgen_cifar10_features_1k_outputs.zip
```

## 8. Local Feature Output Validation

```bash
commands/v6_cpu_execution/07_validate_copied_back_feature_caches.sh
```

If merged caches are copied back manually instead of through the output ZIP:

```bash
commands/v6_cpu_execution/08_split_feature_caches_by_role.sh
```

## 9. Metric/Sanity Gates

```bash
commands/v6_cpu_execution/09_run_metric_reproduction_and_sanity_gates.sh
```

Expected non-published label for 1k pilot-only sanity:

```text
PILOT_SANITY_ONLY_NO_PUBLISHED_METRIC_REPRODUCTION
```

## 10. First Certificate Pilot

Only after R1D passes:

```bash
commands/v6_cpu_execution/10_run_first_certificate_pilot_if_ready.sh
```

Outputs remain:

```text
pilot_only
not_paper_evidence
single_benchmark_only
not_generalized
claim_allowed=false
```

## 11. Final Audit

```bash
commands/v6_cpu_execution/11_run_final_execution_audit.sh
```

## 12. Scale

Scale to 10k/50k only after the first pilot sanity gates pass and the final audit reports `FIRST_PILOT_COMPLETED_NO_CLAIM`.

## 13. Runtime Estimates

Generation 1k/model for three models on T4x2: ~30 min-3 hr.

Feature extraction for 1k/model plus reference test split: Inception ~5-30 min, CLIP ~10-45 min, merge/validation minutes.

CPU validation: seconds to minutes for manifests/ZIPs, longer if hashing many files.

First certificate pilot from cached features: seconds to minutes for 1k-scale arrays.

All estimates are planning estimates only, not empirical project results.

## 14. Troubleshooting

- `BLOCKED_MISSING_REFERENCE_SAMPLES`: run step 2.
- `BLOCKED_GENERATION_OUTPUT_ZIP_MISSING`: run the generation notebook and copy back the output ZIP.
- `BLOCKED_GENERATED_MANIFEST_INVALID`: inspect `data/results/v6_generation_output_validation_summary.json`.
- `BLOCKED_FEATURE_INPUT_PACKAGE_MISSING`: run steps 5-6.
- `BLOCKED_FEATURE_OUTPUT_ZIP_MISSING`: run the feature notebook and copy back the output ZIP.
- `BLOCKED_FEATURE_CACHE_INVALID`: inspect `data/results/v6_feature_output_validation_summary.json`.
- `BLOCKED_METRIC_REPRODUCTION_OR_SANITY`: inspect `docs/R1D_METRIC_REPRODUCTION_REPORT.md`.

## 15. What Not To Do

- Do not use Kaggle for certificates/statistics/reports.
- Do not fabricate missing samples or features.
- Do not use smoke data as evidence.
- Do not create `claim_allowed=true`.
- Do not run FID certificates.
- Do not certify polynomial KID by default.
- Do not put pilot-only numbers into the paper.
