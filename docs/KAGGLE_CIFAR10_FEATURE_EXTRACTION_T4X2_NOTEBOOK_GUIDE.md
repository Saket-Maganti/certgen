# Kaggle CIFAR-10 Feature Extraction T4x2 Notebook Guide

`NO_FAKE_RESULTS`
`NO_REAL_EVIDENCE`
`not paper evidence`

Notebook: `notebooks/kaggle/certgen_cifar10_feature_extraction_t4x2_1k.ipynb`

This notebook creates feature-cache artifacts only. It does not run certificates, metric reproduction claims, pilot undecided fraction, or paper evidence generation.

## Local CPU Package

```bash
commands/v6_cpu_execution/05_build_feature_extraction_sample_package.sh

PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" \
  python3 -m certgen.packaging.build_kaggle_feature_input_zip \
  --reference-manifest registry/manifests/cifar10_r1_reference.jsonl \
  --generated-manifest registry/manifests/cifar10_r1_generated_pilot_1000.jsonl \
  --sample-manifest registry/manifests/cifar10_r1_feature_extraction_samples.jsonl \
  --provenance-ledger registry/provenance/cifar10_r1_ledger.csv \
  --preprocessing-lock configs/preprocessing_locks/cifar10_inception_bilinear_299.json \
  --out-zip data/kaggle_inputs/certgen_cifar10_feature_extraction_1k_input.zip \
  --manifest-out data/results/v6_feature_input_zip_manifest.json
```

Upload `data/kaggle_inputs/certgen_cifar10_feature_extraction_1k_input.zip` as a Kaggle dataset named `certgen-features`.

## Kaggle Steps

1. Enable T4 x2.
2. Attach the `certgen-features` dataset.
3. Open `certgen_cifar10_feature_extraction_t4x2_1k.ipynb`.
4. Run cells in order.
5. Confirm reference/generated samples and manifests are present.
6. Extract Inception with two shards.
7. Extract CLIP with two shards.
8. Merge shards and split caches by role.
9. Confirm `/kaggle/working/certgen_cifar10_features_1k_outputs.zip` exists.

Parallel sharding:

```text
GPU 0: shard 0 of 2
GPU 1: shard 1 of 2
```

## Copy Back

Download:

```text
/kaggle/working/certgen_cifar10_features_1k_outputs.zip
```

Place locally:

```text
data/kaggle_outputs/certgen_cifar10_features_1k_outputs.zip
```

Validate locally:

```bash
commands/v6_cpu_execution/07_validate_copied_back_feature_caches.sh
commands/v6_cpu_execution/09_run_metric_reproduction_and_sanity_gates.sh
```

Do not run `commands/v6_cpu_execution/10_run_first_certificate_pilot_if_ready.sh` unless R1D reports ready.
