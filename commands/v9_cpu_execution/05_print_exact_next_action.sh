#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

python3 -m certgen.pipeline.v9_next_action \
  --out-json data/results/v9_exact_next_action.json \
  --out-report docs/V9_EXACT_NEXT_ACTION.md
