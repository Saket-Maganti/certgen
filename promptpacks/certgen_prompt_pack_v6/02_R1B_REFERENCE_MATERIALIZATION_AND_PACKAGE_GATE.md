# 02 — R1B Reference Materialization and Package Gate

Implement or execute `CERTGEN_R1B_REFERENCE_MATERIALIZATION_AND_PACKAGE_GATE`.

Goal:

> Materialize CIFAR-10 reference samples locally and update the readiness state. Do not run certificates. Do not run feature extraction yet.

## Current blocker

`BLOCKED_MISSING_REFERENCE_SAMPLES`

No local CIFAR-10 image tree or official Python-batch archive exists under `data/sources`.

## Allowed reference materialization paths

Use one explicit source:

1. User-provided CIFAR root;
2. manually downloaded official CIFAR-10 Python archive;
3. explicit `torchvision.datasets.CIFAR10(download=True)` command only when user intentionally runs it, never in tests.

Do not download CIFAR in tests.

## Tasks

### 1. Provide explicit commands

Create/update:

- `commands/r1b_cpu/00_materialize_cifar10_reference_from_local_root.sh`
- `commands/r1b_cpu/00b_materialize_cifar10_reference_from_official_archive.sh`
- optional documented `torchvision` command with explicit `--download` guard.

### 2. Build reference manifest

Use:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.data.build_cifar10_reference_manifest \
  --cifar-root <CIFAR_ROOT> \
  --split test \
  --out-manifest registry/manifests/cifar10_r1_reference.jsonl \
  --out-summary data/results/r1b_cifar10_reference_summary.json \
  --license-status license_unknown_reference_only \
  --source-url https://www.cs.toronto.edu/~kriz/cifar.html \
  --claim-allowed false
```

Expected test count: 10,000 images.
Expected resolution: 32x32 RGB.

### 3. Validate reference

Add CPU command:

`commands/r1b_cpu/00c_validate_reference_manifest.sh`

It checks:

- expected count;
- image paths exist;
- dimensions correct;
- hashes present if feasible;
- split labels present;
- source_id correct;
- license status explicit;
- `claim_allowed=false`.

### 4. Update readiness

If reference exists but generated samples do not:

`BLOCKED_GENERATION_NOT_RUN`

If reference still missing:

`BLOCKED_MISSING_REFERENCE_SAMPLES`

Do not emit feature-extraction-ready status yet.

## Tests

Use tiny fake CIFAR fixtures only.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m pytest -q
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.cli.run_cifar10_real_pilot \
  --provenance-ledger registry/provenance/cifar10_r1_ledger.csv \
  --sample-manifest registry/manifests/cifar10_r1_samples.jsonl \
  --preprocessing-lock configs/preprocessing_locks/cifar10_inception_bilinear_299.json \
  --feature-cache-dir data/features/cifar10_r1 \
  --metric-reproduction-audit data/results/cifar10_r1_metric_reproduction.json \
  --out-json data/results/r1_cifar10_status.json \
  --report docs/R1_CIFAR10_REAL_PILOT_READINESS.md
```

Final response:

- reference status;
- exact path used;
- count;
- whether ready for Kaggle generation;
- no claim promotion.
