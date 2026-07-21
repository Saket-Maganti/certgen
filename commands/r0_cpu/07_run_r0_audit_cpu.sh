#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

mkdir -p data/results/r0_cpu docs

python3 -m certgen.audit.r0_cpu_gpu_audit \
  --out docs/R0_CPU_GPU_AUDIT.md \
  --json-out data/results/r0_cpu_gpu_audit.json
