You are working on CertGen in `/Users/saketmaganti/Projects/certGen` after V6.

Global non-negotiables:
- Do not fabricate results.
- Do not create `claim_allowed=true` unless a specific real-evidence gate later permits it; for V7, keep `claim_allowed=false`.
- Do not use smoke/template/synthetic outputs as real evidence.
- Do not run certificates unless real feature caches and metric/sanity gates pass.
- Do not claim rigorous FID certification. FID remains descriptive-only.
- Polynomial KID remains descriptive/non-certified by default unless a separate valid bounded/nonasymptotic justification is implemented and audited.
- Rigorous certificate path remains bounded RBF-MMD / bounded CMMD / valid bounded streams.
- Kaggle T4×2 is for sample generation and feature extraction only. CPU/local is for validation, packaging, metric reproduction, certificates, reports, and audits.
- Every output must clearly label whether it is `NO_REAL_EVIDENCE`, `pilot_only`, `not_paper_evidence`, or `run_log_only`.
- Do not build generic V7 fluff. Build execution leverage: commands, notebooks, validators, packaging, recovery, and run lanes that get the first real pilot unstuck and scalable.

# V7 Prompt 11 — Kaggle Dataset Packaging Automation

Make local-to-Kaggle handoff less error-prone.

Create:

- `certgen/packaging/kaggle_dataset_manifest.py`;
- `python -m certgen.packaging.prepare_kaggle_dataset_folder`;
- `commands/v7_cpu_execution/09_prepare_kaggle_generation_dataset_folder.sh`;
- `commands/v7_cpu_execution/10_prepare_kaggle_feature_dataset_folder.sh`;
- `docs/V7_KAGGLE_DATASET_UPLOAD_GUIDE.md`.

The command should create folders like:

- `data/kaggle_uploads/certgen-generation/`;
- `data/kaggle_uploads/certgen-features/`;

Each folder includes:

- ZIP(s);
- README;
- manifest JSON;
- checksum file;
- expected Kaggle dataset name;
- upload instructions;
- no secrets;
- no local absolute private paths unless deliberately flagged.

If Kaggle CLI is unavailable, provide manual UI steps. Do not require Kaggle CLI for tests.
