#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

python3 - <<'PY'
import importlib.util
import sys
print(f"python={sys.version.split()[0]}")
for module in ["numpy", "yaml"]:
    print(f"{module}={'ok' if importlib.util.find_spec(module) else 'missing'}")
PY

python3 -m certgen.audit.final_execution_audit \
  --out docs/FINAL_EXECUTION_AUDIT.md \
  --json-out data/results/final_execution_audit.json
