# CIFAR-10 Reference Materialization R1A

`NO_REAL_EVIDENCE`

Claim allowed: `False`

## Source

Official source URL: https://www.cs.toronto.edu/~kriz/cifar.html

Expected counts:

- train: 50,000
- test: 10,000
- total: 60,000

Expected resolution: 32x32 RGB.

The official CIFAR-10 page describes the Python archive layout as five training batches plus one test batch, each with 10,000 images.

## License Status Handling

If the CIFAR-10 license remains unresolved, use `license_unknown_reference_only`.

Internal no-claim pilot use is allowed only if the project policy permits that status. Paper-evidence promotion remains blocked until license status is resolved. Do not convert `license_unknown_reference_only` into a public claim or paper evidence state.

## Accepted Local Inputs

Use one explicit local source. Do not download CIFAR-10 inside tests.

- `torchvision.datasets.CIFAR10`: allowed only in an explicit real-run command where the user controls the local root and download choice.
- Official CIFAR-10 Python tarball: download manually from the official page, extract it, then point the builder at the extracted root or parent root.
- Local user-provided image root: use a tree such as `data/sources/cifar10_r1/reference/test/<class_name>/*.png`.

Recommended local path conventions:

- Raw/manual archive root: `data/sources/cifar10_raw/`
- Materialized reference images: `data/sources/cifar10_r1/reference/`
- Reference manifest: `registry/manifests/cifar10_r1_reference.jsonl`
- Reference summary: `data/results/r1a_cifar10_reference_summary.json`

## Manifest Creation Command

For already-materialized local images:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.data.build_cifar10_reference_manifest \
  --cifar-root data/sources/cifar10_r1/reference \
  --split test \
  --out-manifest registry/manifests/cifar10_r1_reference.jsonl \
  --out-summary data/results/r1a_cifar10_reference_summary.json \
  --license-status license_unknown_reference_only \
  --source-url https://www.cs.toronto.edu/~kriz/cifar.html \
  --claim-allowed false
```

For the manually downloaded official Python archive:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.data.build_cifar10_reference_manifest \
  --cifar-root data/sources/cifar10_raw \
  --split test \
  --out-manifest registry/manifests/cifar10_r1_reference.jsonl \
  --out-summary data/results/r1a_cifar10_reference_summary.json \
  --license-status license_unknown_reference_only \
  --source-url https://www.cs.toronto.edu/~kriz/cifar.html \
  --claim-allowed false
```

If the root contains `cifar-10-batches-py`, the builder exports PPM images under `data/sources/cifar10_raw/certgen_materialized_images/` and writes stable hashes into the manifest.

## Validation Command

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 -m certgen.cli.run_cifar10_real_pilot \
  --provenance-ledger registry/provenance/cifar10_r1_ledger.csv \
  --sample-manifest registry/manifests/cifar10_r1_samples.jsonl \
  --preprocessing-lock configs/preprocessing_locks/cifar10_inception_bilinear_299.json \
  --feature-cache-dir data/features/cifar10_r1 \
  --metric-reproduction-audit data/results/cifar10_r1_metric_reproduction.json \
  --out-json data/results/r1_cifar10_status.json \
  --report docs/R1_CIFAR10_REAL_PILOT_READINESS.md
```
