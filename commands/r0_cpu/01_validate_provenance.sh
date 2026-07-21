#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

LEDGER="${CERTGEN_R1_PROVENANCE_LEDGER:-registry/provenance/cifar10_r1_ledger.csv}"
mkdir -p data/results/r0_cpu docs

python3 -m certgen.cli.validate_provenance_ledger \
  --ledger "$LEDGER" \
  --out docs/R0_CPU_PROVENANCE_VALIDATION.md \
  --json-out data/results/r0_cpu/provenance_validation.json \
  --require-real-pilot
