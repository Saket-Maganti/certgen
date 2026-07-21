# Legacy Compatibility Next-Action Mirror

`LEGACY_COMPATIBILITY_ONLY` · `NOT_CANONICAL_GUIDANCE`

Canonical source: `CERTGEN_CVPR_FINAL_100_PERCENT_PRE_RUN_HANDBOOK.md`.

Status: `KAGGLE_DIAGNOSTIC_REQUIRED`
Action: `RUN_KAGGLE_ENVIRONMENT_DIAGNOSTIC`
Reason: The reference, frozen study, and registered draw are ready; the two-GPU environment diagnostic is the first unresolved external boundary.
Exact command: `Upload artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip and run notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb on GPU T4 x2`
Notebook: `notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb`
Expected output: `certgen_kaggle_environment_diagnostic_output.zip`
Success validator: `CUDA_VISIBLE_DEVICES="" CERTGEN_CPU_ONLY=1 python3 scripts/run_all_available_cpu_stages.py --resume --explain`
Claim allowed: `false`
