#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

CACHE_DIR="${CERTGEN_R1_FEATURE_CACHE_DIR:-data/features/cifar10_r1}"
REPRO_AUDIT="${CERTGEN_R1_METRIC_REPRO_AUDIT:-data/results/r0_cpu/metric_reproduction.json}"
COMPARISON_ID="${CERTGEN_R1_COMPARISON_ID:-cifar10_r1_pair_001}"
mkdir -p data/results/r0_cpu/certificates

python3 -m certgen.cli.certify_clean_metric \
  --features-a "$CACHE_DIR/model_a_inception.npz" \
  --features-b "$CACHE_DIR/model_b_inception.npz" \
  --features-r "$CACHE_DIR/reference_inception.npz" \
  --metric mmd_rbf \
  --comparison-id "$COMPARISON_ID" \
  --alpha "${CERTGEN_ALPHA:-0.05}" \
  --budget-units "${CERTGEN_BUDGET_UNITS:-1000}" \
  --method betting \
  --block-size "${CERTGEN_BLOCK_SIZE:-16}" \
  --metric-reproduction-audit "$REPRO_AUDIT" \
  --out "data/results/r0_cpu/certificates/${COMPARISON_ID}_mmd_rbf.json" \
  --evidence-status real_pilot_non_claim

python3 -m certgen.cli.certify_clean_metric \
  --features-a "$CACHE_DIR/model_a_clip.npz" \
  --features-b "$CACHE_DIR/model_b_clip.npz" \
  --features-r "$CACHE_DIR/reference_clip.npz" \
  --metric cmmd_clip_mmd \
  --comparison-id "$COMPARISON_ID" \
  --alpha "${CERTGEN_ALPHA:-0.05}" \
  --budget-units "${CERTGEN_BUDGET_UNITS:-1000}" \
  --method betting \
  --block-size "${CERTGEN_BLOCK_SIZE:-16}" \
  --metric-reproduction-audit "$REPRO_AUDIT" \
  --out "data/results/r0_cpu/certificates/${COMPARISON_ID}_cmmd_clip_mmd.json" \
  --evidence-status real_pilot_non_claim
