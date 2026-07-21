#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

CONFIG="${CERTGEN_R1_METRIC_REPRO_CONFIG:-configs/r0_cpu/cifar10_metric_reproduction.yaml}"
mkdir -p data/results/r0_cpu docs

python3 -m certgen.cli.audit_metric_reproduction \
  --config "$CONFIG" \
  --out docs/R0_CPU_METRIC_REPRODUCTION.md \
  --json-out data/results/r0_cpu/metric_reproduction.json
