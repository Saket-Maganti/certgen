#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

mkdir -p data/results/r0_cpu

python3 - <<'PY'
import json
import os
import platform
import sys
from pathlib import Path

import certgen

payload = {
    "check": "r0_cpu_environment",
    "python": sys.version,
    "platform": platform.platform(),
    "certgen_version": certgen.__version__,
    "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", None),
    "cpu_default": os.environ.get("CUDA_VISIBLE_DEVICES", None) == "",
    "claim_allowed": False,
}
Path("data/results/r0_cpu").mkdir(parents=True, exist_ok=True)
Path("data/results/r0_cpu/environment_cpu.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
if not payload["cpu_default"]:
    raise SystemExit("CUDA_VISIBLE_DEVICES must be empty for CPU-side CertGen runs")
print("CPU environment validation passed")
PY
