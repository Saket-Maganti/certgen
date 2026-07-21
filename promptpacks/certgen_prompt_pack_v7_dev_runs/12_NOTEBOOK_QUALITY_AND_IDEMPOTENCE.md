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

# V7 Prompt 12 — Notebook Quality and Idempotence

Harden notebooks so they are not fragile one-off scripts.

Add notebook quality checks:

- required markdown warning cells;
- no hidden `claim_allowed=true`;
- no certificate imports/calls;
- no paper result generation;
- output ZIP creation;
- status JSON writing;
- copy-back instructions;
- resume flag support;
- cell timing logs as `run_log_only`;
- deterministic seeds;
- clear failure stop.

Create:

- `python -m certgen.notebooks.validate_kaggle_notebooks`;
- `docs/V7_NOTEBOOK_QUALITY_REPORT.md`;
- tests for notebook JSON inspection.

Notebook validation should run locally on CPU and not require Kaggle.
