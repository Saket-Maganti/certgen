# CertGen Phase 1 pre-GPU completion report

Status: `PHASE1_COMPLETE_WAITING_FOR_KAGGLE_DIAGNOSTIC`

1. CIFAR found: `yes` at `data/sources/cifar-10-python.tar.gz`.
2. Validated and materialized: `yes`.
3. Profile/study frozen: `yes`.
4. Reference draw built: `yes`.
5. Upload ZIPs present: diagnostic and preflight; both validate locally.
6. Stage-dependent ZIPs: generation 1k and features 1k; only complete blocked plans exist.
7. Next notebook: `notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb`.
8. T4x2 required: `yes` for every real Kaggle stage.
9. Internet mode: `KAGGLE_INTERNET_ON_INSTALL` for diagnostic/preflight dependency installation; model loading and later stages use Internet off.
10. Private assets: none for diagnostic; validated DDPM, Inception, and CLIP mounts for preflight/later. CLIP is never in a public archive.
11. Estimated runtime: diagnostic 5-20 min; preflight 20-60 min; first 1k pilot 5-10 hr total. All are `PLANNING_ESTIMATE_NOT_MEASURED`.
12. Output ZIP: after diagnostic, `certgen_kaggle_environment_diagnostic_output.zip`.
13. Place it at: `data/kaggle_returns/diagnostic/`.
14. Resume: `CUDA_VISIBLE_DEVICES="" CERTGEN_CPU_ONLY=1 python3 scripts/run_all_available_cpu_stages.py --resume --explain`.
15. Local defect remaining: `no`.

Exact next action: `Upload artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip and run notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb on GPU T4 x2`.

No empirical claim is authorized. `claim_allowed=false`.
