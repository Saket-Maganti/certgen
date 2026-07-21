#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

mkdir -p data/results/r0_cpu docs

status=0
python3 -m certgen.cli.run_cifar10_real_pilot \
  --provenance-ledger "${CERTGEN_R1_PROVENANCE_LEDGER:-registry/provenance/cifar10_r1_ledger.csv}" \
  --sample-manifest "${CERTGEN_R1_SAMPLE_MANIFEST:-registry/manifests/cifar10_r1_samples.jsonl}" \
  --preprocessing-lock "${CERTGEN_R1_PREPROCESSING_LOCK:-configs/preprocessing_locks/cifar10_inception_bilinear_299.json}" \
  --feature-cache-dir "${CERTGEN_R1_FEATURE_CACHE_DIR:-data/features/cifar10_r1}" \
  --metric-reproduction-audit "${CERTGEN_R1_METRIC_REPRO_AUDIT:-data/results/cifar10_r1_metric_reproduction.json}" \
  --out-json data/results/r0_cpu/r1_cifar10_status.json \
  --report docs/R1_CIFAR10_REAL_PILOT_READINESS.md || status=$?

if [[ "$status" != "0" && "$status" != "2" ]]; then
  exit "$status"
fi
