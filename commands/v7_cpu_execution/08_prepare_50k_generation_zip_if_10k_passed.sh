#!/usr/bin/env bash
set -euo pipefail
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 - <<'PY2'
import pathlib, sys
p=pathlib.Path("data/results/v7_10k_validation_summary.json")
if not p.exists(): sys.exit("BLOCKED_10K_VALIDATION_MISSING")
print("50k preparation requires validated 10k gates; no automatic scale run performed")
PY2
