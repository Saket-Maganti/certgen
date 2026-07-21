#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

: "${CIFAR_ROOT:?Set CIFAR_ROOT to a local CIFAR-10 image tree before running this command.}"

python3 -m certgen.data.build_cifar10_reference_manifest \
  --cifar-root "$CIFAR_ROOT" \
  --split "${CERTGEN_CIFAR10_SPLIT:-test}" \
  --out-manifest registry/manifests/cifar10_r1_reference.jsonl \
  --out-summary data/results/r1b_cifar10_reference_summary.json \
  --license-status license_unknown_reference_only \
  --source-url https://www.cs.toronto.edu/~kriz/cifar.html \
  --claim-allowed false
