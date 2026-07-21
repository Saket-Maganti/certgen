#!/usr/bin/env bash
set -euo pipefail
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES="" python3 - <<'PY2'
import json, pathlib, sys
p=pathlib.Path("data/results/v7_metric_sanity_gates.json")
if not p.exists(): sys.exit("BLOCKED_1K_METRIC_SANITY_GATES_MISSING")
print("10k preparation requires validated 1k gates; no automatic scale run performed")
PY2
