#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1

WORK_ROOT="${CERTGEN_KAGGLE_WORK_ROOT:-/kaggle/working}"
SAMPLE_ROOT="$WORK_ROOT/samples"
MANIFEST_ROOT="$WORK_ROOT/manifests"
BATCH_SIZE="${CERTGEN_R1B_GENERATION_BATCH_SIZE:-32}"

mkdir -p "$SAMPLE_ROOT" "$MANIFEST_ROOT"

run_model() {
  local checkpoint_id="$1"
  local slug="$2"
  mkdir -p "$SAMPLE_ROOT/$slug/gpu0" "$SAMPLE_ROOT/$slug/gpu1"

  CUDA_VISIBLE_DEVICES=0 python -m certgen.generation.generate_cifar10_diffusers \
    --checkpoint-id "$checkpoint_id" \
    --seed-start 0 \
    --seed-end 500 \
    --num-samples 500 \
    --out-dir "$SAMPLE_ROOT/$slug/gpu0" \
    --manifest-out "$MANIFEST_ROOT/${slug}_gpu0.jsonl" \
    --device cuda \
    --batch-size "$BATCH_SIZE" \
    --resume \
    --execute &

  CUDA_VISIBLE_DEVICES=1 python -m certgen.generation.generate_cifar10_diffusers \
    --checkpoint-id "$checkpoint_id" \
    --seed-start 500 \
    --seed-end 1000 \
    --num-samples 500 \
    --out-dir "$SAMPLE_ROOT/$slug/gpu1" \
    --manifest-out "$MANIFEST_ROOT/${slug}_gpu1.jsonl" \
    --device cuda \
    --batch-size "$BATCH_SIZE" \
    --resume \
    --execute &

  wait
}

run_model "google/ddpm-cifar10-32" "google_ddpm"
run_model "FrankCCCCC/ddpm_ema_cifar10" "frank_ddpm_ema"
run_model "FrankCCCCC/cfm-cifar10-32" "frank_cfm"

python -m certgen.generation.merge_sample_manifests \
  --manifest "$MANIFEST_ROOT/google_ddpm_gpu0.jsonl" \
  --manifest "$MANIFEST_ROOT/google_ddpm_gpu1.jsonl" \
  --manifest "$MANIFEST_ROOT/frank_ddpm_ema_gpu0.jsonl" \
  --manifest "$MANIFEST_ROOT/frank_ddpm_ema_gpu1.jsonl" \
  --manifest "$MANIFEST_ROOT/frank_cfm_gpu0.jsonl" \
  --manifest "$MANIFEST_ROOT/frank_cfm_gpu1.jsonl" \
  --out-manifest "$MANIFEST_ROOT/cifar10_r1_generated_pilot_1000.jsonl" \
  --out-summary "$MANIFEST_ROOT/cifar10_r1_generated_pilot_1000_summary.json" \
  --check-image-hashes
