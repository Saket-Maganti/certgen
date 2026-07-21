# Kaggle CIFAR-10 Generation T4x2 Notebook Guide

`NO_FAKE_RESULTS`
`NO_REAL_EVIDENCE`
`not paper evidence`

Notebook: `notebooks/kaggle/certgen_cifar10_generation_t4x2_1k.ipynb`

This notebook generates sample-package artifacts only. It does not run feature extraction, metric reproduction, certificates, or paper evidence.

## Local CPU Package

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" \
  python3 -m certgen.packaging.build_kaggle_generation_input_zip \
  --provenance-ledger registry/provenance/cifar10_r1_ledger.csv \
  --out-zip data/kaggle_inputs/certgen_cifar10_generation_1k_input.zip \
  --manifest-out data/results/v6_generation_input_zip_manifest.json \
  --sample-count-per-model 1000
```

Upload `data/kaggle_inputs/certgen_cifar10_generation_1k_input.zip` as a Kaggle dataset named `certgen-generation`.

## Kaggle Steps

1. Enable T4 x2.
2. Attach the `certgen-generation` dataset.
3. Open `certgen_cifar10_generation_t4x2_1k.ipynb`.
4. Run cells in order.
5. Confirm GPU 0 and GPU 1 are both visible.
6. Confirm the notebook writes `/kaggle/working/certgen_cifar10_generated_1k_outputs.zip`.

Parallel seed sharding:

```text
GPU 0: seeds 0-499
GPU 1: seeds 500-999
```

Models:

```text
google/ddpm-cifar10-32
FrankCCCCC/ddpm_ema_cifar10
FrankCCCCC/cfm-cifar10-32
```

## Copy Back

Download:

```text
/kaggle/working/certgen_cifar10_generated_1k_outputs.zip
```

Place locally:

```text
data/kaggle_outputs/certgen_cifar10_generated_1k_outputs.zip
```

Validate locally:

```bash
commands/v6_cpu_execution/04_validate_copied_back_generation_outputs.sh
```

If a checkpoint fails, the notebook writes `generation_blocked_status.json` and stops. Do not continue to feature extraction for failed or partial outputs.
