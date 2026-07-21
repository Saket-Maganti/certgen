# 04 — CPU Validate Generated Manifests and Build Feature-Extraction Package

Implement/execute `CERTGEN_R1B_VALIDATE_GENERATED_MANIFESTS_AND_BUILD_PACKAGE`.

Goal:

> After Kaggle generation outputs are copied back, validate manifests, merge generated samples, and build a feature-extraction-ready sample package.

All of this is CPU-side.

## Inputs

Expected copied-back generated manifests:

- `google_ddpm_gpu0.jsonl`
- `google_ddpm_gpu1.jsonl`
- `frank_ddpm_ema_gpu0.jsonl`
- `frank_ddpm_ema_gpu1.jsonl`
- `frank_cfm_gpu0.jsonl`
- `frank_cfm_gpu1.jsonl`

Expected reference manifest:

- `registry/manifests/cifar10_r1_reference.jsonl`

## Tasks

### 1. Validate generated manifests

Run or create:

`commands/r1b_cpu/01_validate_generated_manifests.sh`

Checks:

- each manifest exists;
- per checkpoint count = 1000 total after merge;
- seeds are unique per checkpoint;
- paths exist;
- image hashes exist;
- width/height/channels = 32x32x3;
- generation_status success;
- `claim_allowed=false`;
- no duplicate paths;
- optional duplicate hash detection.

### 2. Merge generated manifests

Use:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.generation.merge_sample_manifests \
  --manifest <MANIFEST_1> \
  --manifest <MANIFEST_2> \
  --out-manifest registry/manifests/cifar10_r1_generated_pilot_1000.jsonl \
  --out-summary data/results/r1b_generated_manifest_summary.json \
  --check-image-hashes
```

### 3. Build feature-extraction package

Use:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.data.build_cifar10_r1_sample_package \
  --reference-manifest registry/manifests/cifar10_r1_reference.jsonl \
  --generated-manifest registry/manifests/cifar10_r1_generated_pilot_1000.jsonl \
  --provenance-ledger registry/provenance/cifar10_r1_ledger.csv \
  --preprocessing-lock configs/preprocessing_locks/cifar10_inception_bilinear_299.json \
  --out-manifest registry/manifests/cifar10_r1_feature_extraction_samples.jsonl \
  --out-summary data/results/r1b_feature_extraction_package_summary.json
```

### 4. Update readiness

If package validates:

`READY_FOR_KAGGLE_FEATURE_EXTRACTION`

If not:

- `BLOCKED_GENERATION_NOT_RUN`
- `BLOCKED_GENERATION_INCOMPLETE`
- `BLOCKED_GENERATION_MANIFEST_INVALID`
- `BLOCKED_MISSING_REFERENCE_SAMPLES`

## Outputs

- `registry/manifests/cifar10_r1_generated_pilot_1000.jsonl`
- `data/results/r1b_generated_manifest_summary.json`
- `registry/manifests/cifar10_r1_feature_extraction_samples.jsonl`
- `data/results/r1b_feature_extraction_package_summary.json`
- updated readiness report.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m pytest -q
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.audit.r1b_generation_package_audit \
  --out docs/R1B_GENERATION_PACKAGE_AUDIT.md \
  --json-out data/results/r1b_generation_package_audit.json
```

Final response:

- generated package status;
- ready/not ready for feature extraction;
- exact blocker if blocked;
- no certificate run.
