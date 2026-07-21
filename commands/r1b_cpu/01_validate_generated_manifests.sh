#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

MANIFEST_DIR="${CERTGEN_R1B_GENERATED_MANIFEST_DIR:-data/sources/cifar10_r1/kaggle_manifests}"
OUT_MANIFEST="${CERTGEN_R1B_GENERATED_MANIFEST:-registry/manifests/cifar10_r1_generated_pilot_1000.jsonl}"
OUT_SUMMARY="${CERTGEN_R1B_GENERATED_SUMMARY:-data/results/r1b_generated_manifest_summary.json}"

python3 -m certgen.generation.validate_cifar10_generated_pilot \
  --manifest-dir "$MANIFEST_DIR" \
  --out-manifest "$OUT_MANIFEST" \
  --out-summary "$OUT_SUMMARY" \
  --expected-count-per-model 1000 \
  --check-image-hashes
