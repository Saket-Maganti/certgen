# 08 — Scale to 10k and 50k Only If Gates Pass

Implement `CERTGEN_R2_SCALE_PLAN_10K_50K_IF_GATES_PASS`.

Goal:

> Scale from 1k/model pilot to 10k/model and then 50k/model only if R1E gates pass.

Do not scale if the 1k pilot has not run or if null/obvious-gap sanity fails.

## Gate requirements

Before 10k:

- R1E audit passed;
- null calibration does not falsely decide;
- obvious-gap sanity behaves correctly;
- feature extraction pipeline works;
- generated manifests validate;
- no `claim_allowed=true`;
- runtime acceptable.

Before 50k:

- 10k manifests validate;
- feature extraction succeeds;
- metric reproduction/sanity stable;
- certificate results are meaningful;
- no severe block-size instability;
- no provenance/license blocker.

## Tasks

### 1. Create scaling command bundles

- `commands/r2_kaggle_generation/00_generate_10000_per_model_t4x2.sh`
- `commands/r2_kaggle_generation/01_generate_50000_per_model_t4x2.sh`
- `commands/r2_kaggle_feature_extraction/00_extract_10k_inception_clip_t4x2.sh`
- `commands/r2_kaggle_feature_extraction/01_extract_50k_inception_clip_t4x2.sh`
- `commands/r2_cpu/00_validate_10k_package.sh`
- `commands/r2_cpu/01_run_10k_certificates.sh`
- `commands/r2_cpu/02_validate_50k_package.sh`
- `commands/r2_cpu/03_run_50k_certificates.sh`

### 2. Runtime tables

Update estimates with measured R1 values if available.

Label clearly:

- measured runtimes;
- extrapolated runtimes;
- planning estimates.

### 3. Scaling report

Create:

- `docs/R2_SCALE_GO_NOGO_REPORT.md`

Statuses:

- `READY_FOR_10K`
- `BLOCKED_R1_SANITY_FAILED`
- `BLOCKED_RUNTIME_TOO_HIGH`
- `BLOCKED_PROVENANCE`
- `READY_FOR_50K`
- `STOP_AT_10K`

### 4. Evidence policy

Even 10k/50k results remain not paper claims until final multi-comparison gates and result contracts pass.

## No automatic full mode

Do not run 50k automatically. Generate commands and gates. Execute only when asked.
