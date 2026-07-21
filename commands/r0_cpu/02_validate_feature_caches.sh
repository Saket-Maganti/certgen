#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

CACHE_DIR="${CERTGEN_R1_FEATURE_CACHE_DIR:-data/features/cifar10_r1}"
mkdir -p data/results/r0_cpu docs

validate_cache () {
  local name="$1"
  local metric="$2"
  python3 -m certgen.cli.validate_feature_cache \
    --features "$CACHE_DIR/${name}.npz" \
    --sidecar "$CACHE_DIR/${name}.sidecar.json" \
    --metric "$metric" \
    --out "docs/R0_CPU_${name}_FEATURE_CACHE.md" \
    --json-out "data/results/r0_cpu/${name}_feature_cache_validation.json"
}

validate_cache reference_inception mmd_rbf
validate_cache model_a_inception mmd_rbf
validate_cache model_b_inception mmd_rbf
validate_cache reference_clip cmmd_clip_mmd
validate_cache model_a_clip cmmd_clip_mmd
validate_cache model_b_clip cmmd_clip_mmd
