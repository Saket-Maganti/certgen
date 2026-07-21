#!/usr/bin/env bash
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
export CUDA_VISIBLE_DEVICES=""

python3 -m certgen.packaging.v9_import_repair \
  --kind preflight \
  --zip "${CERTGEN_PREFLIGHT_ZIP:-data/kaggle_outputs/certgen_checkpoint_preflight_outputs.zip}" \
  --out-dir "${CERTGEN_PREFLIGHT_IMPORT_DIR:-data/imported/v9_preflight}" \
  --out-json data/results/v9_checkpoint_preflight_import_status.json \
  --out-report docs/V9_IMPORT_REPAIR_REPORT.md \
  ${CERTGEN_IMPORT_FORCE:+--force}
