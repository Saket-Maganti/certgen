# CertGen Kaggle T4x2 execution handbook

Current Phase 1 boundary: `kaggle_diagnostic`. All GPU notebooks require **GPU T4 x2**; zero-, one-, or ambiguous-GPU visibility fails before work.

1. Validate the input ZIP locally with `python3 -m certgen kaggle validate-input <zip>`.
2. Attach the ZIP and, for preflight or later, the private assets described in `KAGGLE_ASSET_SETUP.md`.
3. Select the dependency mode frozen in the configuration. Keep model loading offline.
4. Run the matching canonical notebook top-to-bottom. Preserve status/log/shard files on failure.
5. Download the single final ZIP (or every hash-manifested multipart member) without unpacking or renaming.
6. Place it in the launchboard copy-back directory and run `CUDA_VISIBLE_DEVICES="" CERTGEN_CPU_ONLY=1 python3 scripts/run_all_available_cpu_stages.py --resume --explain`.

Never mix run IDs, configuration hashes, study hashes, asset revisions, seed partitions, or feature rows. Resume reuses only validated completion markers. No notebook may set `claim_allowed=true`.

Exact next action: `Upload artifacts/cvpr/kaggle_inputs/diagnostic/certgen_kaggle_environment_diagnostic_input.zip and run notebooks/kaggle/certgen_kaggle_environment_diagnostic_t4x2.ipynb on GPU T4 x2`.
