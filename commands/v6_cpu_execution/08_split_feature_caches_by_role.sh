#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

FEATURE_ROOT="${CERTGEN_FEATURE_ROOT:-data/features/cifar10_r1}"
SAMPLE_MANIFEST="${CERTGEN_FEATURE_SAMPLE_MANIFEST:-registry/manifests/cifar10_r1_feature_extraction_samples.jsonl}"

python3 -m certgen.features.split_by_role \
  --features-npz "$FEATURE_ROOT/cifar10_r1_inception.npz" \
  --sidecar "$FEATURE_ROOT/cifar10_r1_inception.sidecar.json" \
  --sample-manifest "$SAMPLE_MANIFEST" \
  --extractor-label inception \
  --out-dir "$FEATURE_ROOT/split" \
  --summary-out "$FEATURE_ROOT/split/inception_split_summary.json" \
  --force

python3 -m certgen.features.split_by_role \
  --features-npz "$FEATURE_ROOT/cifar10_r1_clip.npz" \
  --sidecar "$FEATURE_ROOT/cifar10_r1_clip.sidecar.json" \
  --sample-manifest "$SAMPLE_MANIFEST" \
  --extractor-label clip \
  --out-dir "$FEATURE_ROOT/split" \
  --summary-out "$FEATURE_ROOT/split/clip_split_summary.json" \
  --force
