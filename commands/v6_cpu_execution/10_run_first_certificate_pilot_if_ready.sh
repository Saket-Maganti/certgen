#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

python3 -m certgen.audit.r1e_first_pilot_audit \
  --feature-dir "${CERTGEN_FEATURE_ROOT:-data/features/cifar10_r1}" \
  --out docs/R1E_FIRST_PILOT_AUDIT.md \
  --json-out data/results/r1e_first_pilot_audit.json
