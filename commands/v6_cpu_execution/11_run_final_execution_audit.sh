#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

python3 -m certgen.audit.final_execution_audit \
  --out docs/FINAL_EXECUTION_AUDIT.md \
  --json-out data/results/final_execution_audit.json
