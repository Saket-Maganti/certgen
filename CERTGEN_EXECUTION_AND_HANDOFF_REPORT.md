# CertGen execution and handoff report

`EXECUTION_STATUS=WAITING_FOR_KAGGLE_DIAGNOSTIC`
`GITHUB_PUBLICATION_STATUS=GITHUB_CLI_REQUIRED`

Completed locally: official CIFAR validation, canonical 10,000-image reference materialization, corrected prospective study/draw/scale/sensitivity freeze, deterministic notebooks and static Kaggle inputs, full local tests, audits, paper build, privacy/restricted-asset checks, and clean release verification.

Next handoff:

- Notebook: `notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb`
- Input ZIP: `artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip`
- SHA-256: `6e5b22cd6ddce4155e762b6d2afa8fc3299fecd524cc10ac3c3de678c1ff8057`
- Accelerator: `GPU T4 x2`
- Internet: ON for dependency installation; model-asset network access OFF
- Private assets: none
- Planning estimate: 5–20 minutes (not measured)
- Expected output: `certgen_kaggle_environment_diagnostic_output.zip`
- Copy back to: `data/kaggle_returns/diagnostic/`
- Resume: `CUDA_VISIBLE_DEVICES="" CERTGEN_CPU_ONLY=1 python3 scripts/run_all_available_cpu_stages.py --resume --explain`

No returned Kaggle ZIP was present. No empirical metric, gate, certificate, ranking, or cross-feature result has been claimed. `claim_allowed=false`.
