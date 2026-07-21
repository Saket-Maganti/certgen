#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

: "${CIFAR_ARCHIVE_ROOT:?Set CIFAR_ARCHIVE_ROOT to a local extracted cifar-10-batches-py directory or its parent.}"

python3 -m certgen.data.build_cifar10_reference_manifest \
  --cifar-root "$CIFAR_ARCHIVE_ROOT" \
  --split "${CERTGEN_CIFAR10_SPLIT:-test}" \
  --out-manifest registry/manifests/cifar10_r1_reference.jsonl \
  --out-summary data/results/r1b_cifar10_reference_summary.json \
  --license-status license_unknown_reference_only \
  --source-url https://www.cs.toronto.edu/~kriz/cifar.html \
  --claim-allowed false
