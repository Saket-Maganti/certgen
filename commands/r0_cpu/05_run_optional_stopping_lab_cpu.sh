#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

mkdir -p data/results/r0_cpu docs

python3 -m certgen.cli.run_optional_stopping_lab \
  --config configs/optional_stopping_lab_v3.yaml \
  --out docs/R0_CPU_OPTIONAL_STOPPING_LAB.md \
  --json-out data/results/r0_cpu/optional_stopping_lab.json
