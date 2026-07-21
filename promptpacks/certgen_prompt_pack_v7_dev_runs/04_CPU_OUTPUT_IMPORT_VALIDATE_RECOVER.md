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

# V7 Prompt 04 — CPU Output Import, Validation, and Recovery

Build robust local import/recovery commands for copied-back Kaggle outputs.

Create/update:

- `certgen/packaging/import_kaggle_generation_outputs.py`
- `certgen/packaging/import_kaggle_feature_outputs.py`
- `commands/v7_cpu_execution/04_import_generation_output_zip.sh`
- `commands/v7_cpu_execution/05_import_feature_output_zip.sh`
- `docs/V7_KAGGLE_COPYBACK_AND_RECOVERY.md`

Generation import must handle:

- missing ZIP;
- corrupt ZIP;
- partial output;
- failed checkpoint status JSON;
- duplicate seeds;
- duplicate paths;
- missing image hashes;
- incorrect image dimensions;
- wrong per-model counts;
- safe resume/import idempotence.

Feature import must handle:

- missing ZIP;
- corrupt ZIP;
- missing role caches;
- missing sidecars;
- dimension mismatch;
- NaN/inf features;
- sample ID mismatch;
- extractor metadata mismatch;
- role split needed;
- safe re-import.

Statuses:

- `BLOCKED_GENERATION_OUTPUT_ZIP_MISSING`;
- `BLOCKED_GENERATION_OUTPUT_CORRUPT`;
- `BLOCKED_GENERATED_MANIFEST_INVALID`;
- `BLOCKED_FEATURE_OUTPUT_ZIP_MISSING`;
- `BLOCKED_FEATURE_OUTPUT_CORRUPT`;
- `BLOCKED_FEATURE_CACHE_INVALID`;
- `READY_FOR_FEATURE_INPUT_PACKAGE`;
- `READY_FOR_METRIC_SANITY_GATES`.

Write:

- `data/results/v7_generation_import_summary.json`;
- `data/results/v7_feature_import_summary.json`;
- `docs/V7_IMPORT_RECOVERY_REPORT.md`.

Tests must use fake ZIPs only.
