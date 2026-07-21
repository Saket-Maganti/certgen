#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

python3 -m certgen.packaging.v9_import_repair \
  --kind generation \
  --zip "${CERTGEN_GENERATION_V9_ZIP:-data/kaggle_outputs/certgen_cifar10_generation_outputs_v9_1k.zip}" \
  --out-dir "${CERTGEN_GENERATION_IMPORT_DIR:-data/imported/v9_generation}" \
  --out-json data/results/v9_import_repair_status.json \
  --out-report docs/V9_IMPORT_REPAIR_REPORT.md \
  ${CERTGEN_IMPORT_FORCE:+--force}
