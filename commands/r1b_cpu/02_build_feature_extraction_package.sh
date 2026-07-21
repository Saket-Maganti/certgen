#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

python3 -m certgen.data.build_cifar10_r1_sample_package \
  --reference-manifest registry/manifests/cifar10_r1_reference.jsonl \
  --generated-manifest registry/manifests/cifar10_r1_generated_pilot_1000.jsonl \
  --provenance-ledger registry/provenance/cifar10_r1_ledger.csv \
  --preprocessing-lock configs/preprocessing_locks/cifar10_inception_bilinear_299.json \
  --out-manifest registry/manifests/cifar10_r1_feature_extraction_samples.jsonl \
  --out-summary data/results/r1b_feature_extraction_package_summary.json
