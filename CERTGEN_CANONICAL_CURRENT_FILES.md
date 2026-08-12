# CertGen canonical current files

- Deep-repair state: `reports/icml2027/deep_repair/CERTGEN_DEEP_REPAIR_CURRENT_STATE.json`
- ICML state v2: `reports/icml2027/CERTGEN_ICML2027_CURRENT_STATE_V2.json`
- Launchboard: `CERTGEN_ICML2027_KAGGLE_LAUNCHBOARD.md`
- Diagnostic ZIP: `artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip`
- Diagnostic SHA-256: `d9b056f220fdd3ef87d5a0c2b41df0d8012452f0f912cb2e378bbc8f764e718d`
- Preflight ZIP: `artifacts/cvpr/kaggle_inputs/preflight/certgen_cvpr_preflight_input.zip`
- Preflight SHA-256: `d3a5b585383e12cfad82d94694fa1d8e2701de399617e8e515bafae57f33e93f`

Next action: upload the immutable diagnostic ZIP, run
`notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb` on Kaggle
T4 x2, download its output, and resume locally with:

`CUDA_VISIBLE_DEVICES="" CERTGEN_CPU_ONLY=1 python3 scripts/run_all_available_cpu_stages.py --resume --explain --search-root /path/to/downloads`

No real GPU/model/paper evidence exists. `claim_allowed=false`.
