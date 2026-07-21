#!/usr/bin/env bash
set -euo pipefail

: "${CERTGEN_R2_ENABLE_10K:?Set CERTGEN_R2_ENABLE_10K=1 only after R1E audit passes and scale is approved.}"

export PYTHONDONTWRITEBYTECODE=1

WORK_ROOT="${CERTGEN_KAGGLE_WORK_ROOT:-/kaggle/working}"
SAMPLE_ROOT="$WORK_ROOT/samples_r2_10k"
MANIFEST_ROOT="$WORK_ROOT/manifests_r2_10k"
BATCH_SIZE="${CERTGEN_R2_GENERATION_BATCH_SIZE:-32}"

mkdir -p "$SAMPLE_ROOT" "$MANIFEST_ROOT" "$WORK_ROOT/logs_r2_10k"

run_model() {
  local checkpoint_id="$1"
  local slug="$2"
  local count="${CERTGEN_R2_COUNT_PER_MODEL:-10000}"
  local split=$((count / 2))
  CUDA_VISIBLE_DEVICES=0 python -m certgen.generation.generate_cifar10_diffusers \
    --checkpoint-id "$checkpoint_id" --seed-start 0 --seed-end "$split" --num-samples "$split" \
    --out-dir "$SAMPLE_ROOT/$slug/gpu0" --manifest-out "$MANIFEST_ROOT/${slug}_gpu0.jsonl" \
    --device cuda --batch-size "$BATCH_SIZE" --resume --execute > "$WORK_ROOT/logs_r2_10k/${slug}_gpu0.log" 2>&1 &
  CUDA_VISIBLE_DEVICES=1 python -m certgen.generation.generate_cifar10_diffusers \
    --checkpoint-id "$checkpoint_id" --seed-start "$split" --seed-end "$count" --num-samples "$((count - split))" \
    --out-dir "$SAMPLE_ROOT/$slug/gpu1" --manifest-out "$MANIFEST_ROOT/${slug}_gpu1.jsonl" \
    --device cuda --batch-size "$BATCH_SIZE" --resume --execute > "$WORK_ROOT/logs_r2_10k/${slug}_gpu1.log" 2>&1 &
  wait
}

run_model "google/ddpm-cifar10-32" "google_ddpm"
run_model "FrankCCCCC/ddpm_ema_cifar10" "frank_ddpm_ema"
run_model "FrankCCCCC/cfm-cifar10-32" "frank_cfm"
